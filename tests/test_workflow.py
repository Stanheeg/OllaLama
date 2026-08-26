import asyncio
from pathlib import Path

import pytest

from trustflow.config import Settings
from trustflow.models import CreateWorkflowRequest, WorkflowState
from trustflow.service import TrustFlowService


def settings(tmp_path: Path) -> Settings:
    return Settings(mode="fixture", db_path=str(tmp_path / "db.sqlite"))


def create(service: TrustFlowService):
    return asyncio.run(service.create(CreateWorkflowRequest(
        vendor_name="Northwind Systems",
        vendor_domain="northwind.example",
        contract_text=(
            "SERVICE AGREEMENT. This agreement is governed by Dutch law. "
            "It automatically renews annually unless either party gives 30 days prior notice. "
            "Liability is limited to fees paid in the preceding 12 months. "
            "The supplier processes customer data under GDPR. Both parties must sign."
        ),
    )))


def test_creation_requires_human_review_and_hash_chains_audit(tmp_path):
    svc = TrustFlowService(settings(tmp_path))
    wf = create(svc)
    assert wf.state == WorkflowState.NEEDS_HUMAN_REVIEW
    assert len(wf.evidence) == 3
    assert wf.audit[0].event_hash
    assert wf.audit[1].prev_hash == wf.audit[0].event_hash
    assert any("human approval" in x.lower() for x in wf.risk.review_triggers)


def test_cannot_generate_without_human_approval(tmp_path):
    svc = TrustFlowService(settings(tmp_path))
    wf = create(svc)
    with pytest.raises(PermissionError):
        asyncio.run(svc.generate_document(wf.id, "Packet"))


def test_rejection_blocks_workflow(tmp_path):
    svc = TrustFlowService(settings(tmp_path))
    wf = create(svc)
    wf = asyncio.run(svc.approve(wf.id, False, "Reviewer", "Risk not acceptable"))
    assert wf.state == WorkflowState.BLOCKED
    with pytest.raises(PermissionError):
        asyncio.run(svc.generate_document(wf.id, "Packet"))


def test_approved_flow_creates_signature_draft_but_never_sends(tmp_path):
    svc = TrustFlowService(settings(tmp_path))
    wf = create(svc)
    wf = asyncio.run(svc.approve(wf.id, True, "Reviewer", "Verified"))
    wf = asyncio.run(svc.generate_document(wf.id, "Packet"))
    wf = asyncio.run(svc.create_signature_draft(wf.id, "Jane", "Doe", "jane@example.com", True))
    assert wf.state == WorkflowState.SIGNATURE_DRAFT_CREATED
    assert wf.signature["send_now"] is False
    assert wf.audit[-1].event == "signature_draft_created"


def test_signature_requires_explicit_second_human_intent(tmp_path):
    svc = TrustFlowService(settings(tmp_path))
    wf = create(svc)
    wf = asyncio.run(svc.approve(wf.id, True, "Reviewer", "Verified"))
    wf = asyncio.run(svc.generate_document(wf.id, "Packet"))
    with pytest.raises(PermissionError):
        asyncio.run(svc.create_signature_draft(wf.id, "Jane", "Doe", "jane@example.com", False))
