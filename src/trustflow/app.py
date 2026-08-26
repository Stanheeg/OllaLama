from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .config import Settings
from .models import ApprovalRequest, CreateWorkflowRequest, GenerateDocumentRequest, SignatureRequest
from .service import TrustFlowService

app = FastAPI(title="TrustFlow", version="0.1.0")
service = TrustFlowService(Settings())
STATIC = Path(__file__).resolve().parents[2] / "static"


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "mode": service.settings.mode}


@app.get("/api/workflows")
def list_workflows():
    return service.list()


@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    try:
        return service.get(workflow_id)
    except KeyError:
        raise HTTPException(404, "workflow not found")


@app.post("/api/workflows")
async def create_workflow(req: CreateWorkflowRequest):
    try:
        return await service.create(req)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(503, str(e))


@app.post("/api/workflows/{workflow_id}/approval")
async def approve(workflow_id: str, req: ApprovalRequest):
    try:
        return await service.approve(workflow_id, req.approved, req.reviewer, req.note)
    except KeyError:
        raise HTTPException(404, "workflow not found")


@app.post("/api/workflows/{workflow_id}/document")
async def document(workflow_id: str, req: GenerateDocumentRequest):
    try:
        return await service.generate_document(workflow_id, req.document_title)
    except KeyError:
        raise HTTPException(404, "workflow not found")
    except PermissionError as e:
        raise HTTPException(409, str(e))


@app.post("/api/workflows/{workflow_id}/signature-draft")
async def signature_draft(workflow_id: str, req: SignatureRequest):
    try:
        return await service.create_signature_draft(
            workflow_id,
            req.signer_first_name,
            req.signer_last_name,
            req.signer_email,
            req.confirm_human_intent,
        )
    except KeyError:
        raise HTTPException(404, "workflow not found")
    except PermissionError as e:
        raise HTTPException(409, str(e))
