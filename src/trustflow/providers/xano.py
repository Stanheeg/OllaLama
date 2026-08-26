from __future__ import annotations

import httpx


class XanoMirror:
    def __init__(self, workflow_url: str, audit_url: str, token: str = "", client: httpx.AsyncClient | None = None):
        self.workflow_url = workflow_url
        self.audit_url = audit_url
        self.token = token
        self.client = client or httpx.AsyncClient(timeout=15)

    @property
    def enabled(self) -> bool:
        return bool(self.workflow_url and self.audit_url)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def upsert_workflow(self, workflow: dict) -> None:
        if not self.enabled:
            return
        r = await self.client.post(self.workflow_url, headers=self._headers(), json=workflow)
        r.raise_for_status()

    async def record_audit(self, workflow_id: str, event: dict) -> None:
        if not self.enabled:
            return
        r = await self.client.post(
            self.audit_url,
            headers=self._headers(),
            json={"workflow_id": workflow_id, **event},
        )
        r.raise_for_status()
