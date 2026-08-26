from __future__ import annotations

import json
import re

import httpx

from ..models import ContractFacts


SCHEMA = {
    "type": "object",
    "properties": {
        "parties": {"type": "array", "items": {"type": "string"}, "description": "Named contracting parties"},
        "governing_law": {"type": ["string", "null"], "description": "Governing law or jurisdiction"},
        "auto_renewal": {"type": ["boolean", "null"], "description": "Whether the agreement automatically renews"},
        "termination_notice_days": {"type": ["integer", "null"], "description": "Notice days required to terminate"},
        "liability_cap": {"type": ["string", "null"], "description": "Liability limitation or cap"},
        "data_processing": {"type": ["boolean", "null"], "description": "Whether personal or customer data processing is contemplated"},
        "signature_required": {"type": "boolean", "description": "Whether execution/signature is required"},
    },
    "required": ["parties", "signature_required"],
}


class FixtureNutrientProvider:
    async def extract_contract(self, pdf_bytes: bytes, original_text: str) -> ContractFacts:
        text = original_text.lower()
        notice = None
        m = re.search(r"(\d{1,3})\s+days?\s+(?:prior|notice)", text)
        if m:
            notice = int(m.group(1))
        law = None
        if "netherlands" in text or "dutch law" in text:
            law = "Netherlands"
        elif "delaware" in text:
            law = "Delaware"
        liability = None
        if "liability" in text and ("cap" in text or "limited" in text):
            liability = "Liability limitation detected; verify source clause."
        return ContractFacts(
            parties=[],
            governing_law=law,
            auto_renewal=("auto-renew" in text or "automatically renew" in text),
            termination_notice_days=notice,
            liability_cap=liability,
            data_processing=("personal data" in text or "customer data" in text or "gdpr" in text),
            signature_required=True,
            confidence=0.82,
            citations=[],
        )


class NutrientExtractionProvider:
    def __init__(self, api_key: str, url: str, client: httpx.AsyncClient | None = None):
        if not api_key:
            raise ValueError("NUTRIENT_API_KEY is required in live mode")
        self.api_key = api_key
        self.url = url
        self.client = client or httpx.AsyncClient(timeout=45)

    async def extract_contract(self, pdf_bytes: bytes, original_text: str) -> ContractFacts:
        instructions = {
            "schema": SCHEMA,
            "parseConfig": {"mode": "understand"},
            "options": {"includeCitations": True},
            "instructions": "Extract only facts explicitly supported by the agreement. Use null if uncertain.",
        }
        response = await self.client.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            files={"file": ("agreement.pdf", pdf_bytes, "application/pdf")},
            data={"instructions": json.dumps(instructions)},
        )
        response.raise_for_status()
        data = response.json()
        # DWS extraction responses can wrap the schema-shaped result. Be strict but tolerant to documented wrappers.
        extracted = data.get("data") or data.get("output") or data.get("result") or data
        if isinstance(extracted, dict) and "data" in extracted and isinstance(extracted["data"], dict):
            extracted = extracted["data"]
        known = {k: extracted.get(k) for k in SCHEMA["properties"] if k in extracted}
        citations = data.get("citations") or extracted.get("citations", []) if isinstance(extracted, dict) else []
        confidences = []
        def scan_conf(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == "confidence" and isinstance(v, (float, int)):
                        confidences.append(float(v) / 100 if v > 1 else float(v))
                    else:
                        scan_conf(v)
            elif isinstance(obj, list):
                for v in obj: scan_conf(v)
        scan_conf(data)
        confidence = min(confidences) if confidences else 0.8
        known["confidence"] = max(0.0, min(1.0, confidence))
        known["citations"] = citations if isinstance(citations, list) else []
        return ContractFacts.model_validate(known)
