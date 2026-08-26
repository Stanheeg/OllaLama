from __future__ import annotations

import httpx


class FixtureDocumentGenerator:
    async def generate(self, title: str, data: dict) -> dict:
        return {
            "provider": "fixture",
            "status": "generated",
            "document_id": f"fixture-{data['workflow_id']}",
            "title": title,
            "note": "Fixture output. Contest demo must switch to live Doctavian generation API.",
        }


class DoctavianDocumentGenerator:
    """Thin live adapter.

    Doctavian advertises an API-first REST workflow, but the event credentials/quickstart
    determine the exact generation endpoint and template identifier. We therefore require
    those values explicitly instead of inventing an undocumented route.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        auth_header: str,
        auth_prefix: str,
        template_id: str,
        client: httpx.AsyncClient | None = None,
    ):
        if not (url and api_key and template_id):
            raise ValueError("DOCTAVIAN_GENERATE_URL, DOCTAVIAN_API_KEY and DOCTAVIAN_TEMPLATE_ID are required")
        self.url = url
        self.api_key = api_key
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix
        self.template_id = template_id
        self.client = client or httpx.AsyncClient(timeout=30)

    async def generate(self, title: str, data: dict) -> dict:
        value = f"{self.auth_prefix} {self.api_key}".strip()
        r = await self.client.post(
            self.url,
            headers={self.auth_header: value, "Content-Type": "application/json"},
            json={"template_id": self.template_id, "title": title, "data": data},
        )
        r.raise_for_status()
        result = r.json()
        return {"provider": "doctavian", "status": "generated", "response": result}
