from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .config import Settings
from .models import AuditEvent, CreateWorkflowRequest, Workflow, WorkflowState
from .pdfutil import text_to_pdf_bytes
from .risk import assess_risk
from .storage import WorkflowStore
from .providers import (
    DoctavianDocumentGenerator,
    FixtureDocumentGenerator,
    FixtureNutrientProvider,
    FixtureSearchProvider,
    FixtureSigner,
    FoxitESignProvider,
    GeminiReasoner,
    NutrientExtractionProvider,
    SerpApiSearchProvider,
    XanoMirror,
)


class TrustFlowService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.store = WorkflowStore(self.settings.db_path)
        self.search = (
            SerpApiSearchProvider(self.settings.serpapi_api_key)
            if self.settings.live else FixtureSearchProvider()
        )
        self.extractor = (
            NutrientExtractionProvider(self.settings.nutrient_api_key, self.settings.nutrient_extract_url)
            if self.settings.live else FixtureNutrientProvider()
        )
        self.reasoner = GeminiReasoner(self.settings.gemini_api_key, self.settings.gemini_model)
        self.xano = XanoMirror(
            self.settings.xano_workflow_upsert_url,
            self.settings.xano_audit_event_url,
            self.settings.xano_api_token,
        )
        self.generator = (
            DoctavianDocumentGenerator(
                self.settings.doctavian_generate_url,
                self.settings.doctavian_api_key,
                self.settings.doctavian_auth_header,
                self.settings.doctavian_auth_prefix,
                self.settings.doctavian_template_id,
            ) if self.settings.live else FixtureDocumentGenerator()
        )
        self.signer = (
            FoxitESignProvider(
                self.settings.foxit_esign_create_url,
                self.settings.foxit_client_id,
                self.settings.foxit_client_secret,
            ) if self.settings.live else FixtureSigner()
        )

    async def _audit(self, wf: Workflow, event: str, actor: str, details: dict[str, Any]) -> None:
        prev = wf.audit[-1].event_hash if wf.audit else None
        material = json.dumps(
            {"workflow_id": wf.id, "event": event, "actor": actor, "details": details, "prev": prev},
            sort_keys=True,
            separators=(",", ":"),
        )
        ev = AuditEvent(
            event=event,
            actor=actor,
            details=details,
            prev_hash=prev,
            event_hash=hashlib.sha256(material.encode()).hexdigest(),
        )
        wf.audit.append(ev)
        await self.xano.record_audit(wf.id, ev.model_dump())

    async def _persist(self, wf: Workflow) -> Workflow:
        self.store.save(wf)
        await self.xano.upsert_workflow(wf.model_dump(mode="json"))
        return wf

    async def create(self, req: CreateWorkflowRequest) -> Workflow:
        evidence = await self.search.search_vendor(req.vendor_name, req.vendor_domain)
        pdf = text_to_pdf_bytes(f"Agreement — {req.vendor_name}", req.contract_text)
        facts = await self.extractor.extract_contract(pdf, req.contract_text)
        risk = assess_risk(evidence, facts)
        risk.ai_summary = await self.reasoner.synthesize(evidence, facts, risk)
        wf = Workflow(
            id=str(uuid.uuid4()),
            vendor_name=req.vendor_name,
            vendor_domain=req.vendor_domain,
            contract_text=req.contract_text,
            state=WorkflowState.NEEDS_HUMAN_REVIEW,
            evidence=evidence,
            facts=facts,
            risk=risk,
        )
        await self._audit(wf, "evidence_collected", "trustflow-agent", {
            "evidence_count": len(evidence), "risk_score": risk.score, "mode": self.settings.mode,
        })
        await self._audit(wf, "human_review_required", "policy-engine", {
            "reason": "TrustFlow never permits autonomous signature authorization."
        })
        return await self._persist(wf)

    def get(self, workflow_id: str) -> Workflow:
        wf = self.store.get(workflow_id)
        if not wf:
            raise KeyError(workflow_id)
        return wf

    def list(self) -> list[Workflow]:
        return self.store.list()

    async def approve(self, workflow_id: str, approved: bool, reviewer: str, note: str) -> Workflow:
        wf = self.get(workflow_id)
        wf.human_approval = {"approved": approved, "reviewer": reviewer, "note": note}
        if approved:
            wf.state = WorkflowState.APPROVED
            await self._audit(wf, "human_approved", reviewer, {"note": note, "risk_score": wf.risk.score})
        else:
            wf.state = WorkflowState.BLOCKED
            await self._audit(wf, "human_rejected", reviewer, {"note": note})
        return await self._persist(wf)

    async def generate_document(self, workflow_id: str, title: str) -> Workflow:
        wf = self.get(workflow_id)
        if wf.state != WorkflowState.APPROVED or not (wf.human_approval or {}).get("approved"):
            raise PermissionError("Explicit human approval is required before document generation")
        packet = {
            "workflow_id": wf.id,
            "vendor": {"name": wf.vendor_name, "domain": wf.vendor_domain},
            "risk": wf.risk.model_dump(),
            "contract_facts": wf.facts.model_dump(),
            "evidence": [e.model_dump() for e in wf.evidence],
            "approval": wf.human_approval,
            "audit_head": wf.audit[-1].event_hash if wf.audit else None,
        }
        wf.generated_document = await self.generator.generate(title, packet)
        wf.state = WorkflowState.DOCUMENT_GENERATED
        await self._audit(wf, "document_generated", "trustflow-agent", {
            "provider": wf.generated_document.get("provider")
        })
        return await self._persist(wf)

    async def create_signature_draft(
        self, workflow_id: str, first: str, last: str, email: str, confirm_human_intent: bool
    ) -> Workflow:
        wf = self.get(workflow_id)
        if wf.state != WorkflowState.DOCUMENT_GENERATED:
            raise PermissionError("Generate an approved document before creating a signature draft")
        if not confirm_human_intent or not (wf.human_approval or {}).get("approved"):
            raise PermissionError("A human must explicitly confirm signature intent")
        # The sample PDF represents the approved packet for demo purposes; live Doctavian output can replace it.
        pdf = text_to_pdf_bytes(
            "TrustFlow Approved Vendor Packet",
            f"Vendor: {wf.vendor_name}\nDomain: {wf.vendor_domain}\nRisk: {wf.risk.level} ({wf.risk.score}/100)\n"
            f"Human reviewer: {wf.human_approval['reviewer']}\n\n{wf.contract_text}",
        )
        wf.signature = await self.signer.create_signature_draft(pdf, first, last, email)
        if wf.signature.get("send_now") is not False:
            raise RuntimeError("Safety invariant violated: TrustFlow only creates Foxit drafts")
        wf.state = WorkflowState.SIGNATURE_DRAFT_CREATED
        await self._audit(wf, "signature_draft_created", wf.human_approval["reviewer"], {
            "provider": wf.signature.get("provider"), "send_now": False,
        })
        return await self._persist(wf)
