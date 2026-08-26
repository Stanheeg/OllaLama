from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowState(StrEnum):
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"
    DOCUMENT_GENERATED = "document_generated"
    SIGNATURE_DRAFT_CREATED = "signature_draft_created"
    BLOCKED = "blocked"


class EvidenceItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    provider: str = "serpapi"


class ContractFacts(BaseModel):
    parties: list[str] = Field(default_factory=list)
    governing_law: str | None = None
    auto_renewal: bool | None = None
    termination_notice_days: int | None = None
    liability_cap: str | None = None
    data_processing: bool | None = None
    signature_required: bool = True
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str
    reasons: list[str]
    review_triggers: list[str]
    source_count: int
    policy_version: str = "trustflow-policy-v1"
    ai_summary: str | None = None


class AuditEvent(BaseModel):
    event: str
    at: str = Field(default_factory=utcnow_iso)
    actor: str
    details: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str | None = None
    event_hash: str | None = None


class Workflow(BaseModel):
    id: str
    vendor_name: str
    vendor_domain: str
    contract_text: str
    state: WorkflowState
    created_at: str = Field(default_factory=utcnow_iso)
    evidence: list[EvidenceItem]
    facts: ContractFacts
    risk: RiskAssessment
    human_approval: dict[str, Any] | None = None
    generated_document: dict[str, Any] | None = None
    signature: dict[str, Any] | None = None
    audit: list[AuditEvent] = Field(default_factory=list)


class CreateWorkflowRequest(BaseModel):
    vendor_name: str = Field(min_length=2, max_length=120)
    vendor_domain: str = Field(min_length=3, max_length=180)
    contract_text: str = Field(min_length=20, max_length=50_000)


class ApprovalRequest(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=2, max_length=120)
    note: str = Field(default="", max_length=1000)


class GenerateDocumentRequest(BaseModel):
    document_title: str = Field(default="Vendor Approval Packet", max_length=160)


class SignatureRequest(BaseModel):
    signer_first_name: str = Field(min_length=1, max_length=80)
    signer_last_name: str = Field(min_length=1, max_length=80)
    signer_email: str = Field(min_length=5, max_length=200)
    confirm_human_intent: bool
