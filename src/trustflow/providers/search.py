from __future__ import annotations

import httpx

from ..models import EvidenceItem


class FixtureSearchProvider:
    async def search_vendor(self, name: str, domain: str) -> list[EvidenceItem]:
        return [
            EvidenceItem(
                title=f"{name} — official site",
                url=f"https://{domain}",
                snippet=f"Official company information for {name}.",
                provider="fixture",
            ),
            EvidenceItem(
                title=f"Independent profile: {name}",
                url=f"https://example.org/company/{domain}",
                snippet="Independent business profile; no adverse signal in this fixture.",
                provider="fixture",
            ),
            EvidenceItem(
                title=f"Security posture reference for {name}",
                url=f"https://example.net/security/{domain}",
                snippet="Public security and compliance reference used for demonstration.",
                provider="fixture",
            ),
        ]


class SerpApiSearchProvider:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        if not api_key:
            raise ValueError("SERPAPI_API_KEY is required in live mode")
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=20)

    async def search_vendor(self, name: str, domain: str) -> list[EvidenceItem]:
        query = f'"{name}" {domain} company security compliance news'
        response = await self.client.get(
            "https://serpapi.com/search.json",
            params={"engine": "google", "q": query, "api_key": self.api_key, "num": 8},
        )
        response.raise_for_status()
        data = response.json()
        items: list[EvidenceItem] = []
        for result in data.get("organic_results", [])[:8]:
            link = result.get("link")
            title = result.get("title")
            if link and title:
                items.append(
                    EvidenceItem(
                        title=title,
                        url=link,
                        snippet=result.get("snippet", ""),
                        provider="serpapi",
                    )
                )
        return items
