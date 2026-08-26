from __future__ import annotations

import base64

import httpx


class FixtureSigner:
    async def create_signature_draft(self, pdf_bytes: bytes, first: str, last: str, email: str) -> dict:
        return {
            "provider": "fixture",
            "status": "draft",
            "folder_id": "fixture-folder",
            "send_now": False,
            "note": "No email sent. Live demo must use Foxit eSign after explicit human approval.",
        }


class FoxitESignProvider:
    def __init__(self, url: str, client_id: str, client_secret: str, client: httpx.AsyncClient | None = None):
        if not (client_id and client_secret):
            raise ValueError("FOXIT_CLIENT_ID and FOXIT_CLIENT_SECRET are required in live mode")
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = client or httpx.AsyncClient(timeout=30)

    async def create_signature_draft(self, pdf_bytes: bytes, first: str, last: str, email: str) -> dict:
        payload = {
            "folderName": "TrustFlow approved vendor agreement",
            "inputType": "base64",
            "base64FileString": [base64.b64encode(pdf_bytes).decode("ascii")],
            "fileNames": ["trustflow-approved-agreement.pdf"],
            "parties": [{
                "firstName": first,
                "lastName": last,
                "emailId": email,
                "permission": "FILL_FIELDS_AND_SIGN",
                "sequence": 1,
            }],
            "fields": [{
                "type": "signature", "x": 108, "y": 565, "width": 120, "height": 40,
                "documentNumber": 1, "pageNumber": 1, "party": 1, "required": True,
            }],
            "processTextTags": False,
            "processAcroFields": False,
            "createEmbeddedSigningSession": False,
            # Hard safety boundary: draft only. A separate human action in Foxit dispatches it.
            "sendNow": False,
        }
        r = await self.client.post(
            self.url,
            headers={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        folder = data.get("folder", {}) if isinstance(data, dict) else {}
        return {
            "provider": "foxit",
            "status": folder.get("folderStatus", "draft"),
            "folder_id": folder.get("folderId"),
            "send_now": False,
        }
