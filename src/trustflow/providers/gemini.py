from __future__ import annotations

import json

import httpx

from ..models import ContractFacts, EvidenceItem, RiskAssessment


class GeminiReasoner:
    def __init__(self, api_key: str, model: str, client: httpx.AsyncClient | None = None):
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.AsyncClient(timeout=30)

    async def synthesize(self, evidence: list[EvidenceItem], facts: ContractFacts, risk: RiskAssessment) -> str | None:
        if not self.api_key:
            return None
        prompt = {
            "role": "You are an evidence synthesizer, not an approval authority.",
            "rules": [
                "Do not invent facts.",
                "Treat search snippets as unverified leads and say when source verification is needed.",
                "Do not recommend bypassing human approval.",
                "Return a concise 4-sentence due-diligence summary.",
            ],
            "evidence": [e.model_dump() for e in evidence],
            "contract_facts": facts.model_dump(),
            "deterministic_risk": risk.model_dump(),
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        resp = await self.client.post(
            url,
            params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": json.dumps(prompt)}]}]},
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            return None
