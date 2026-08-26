import asyncio
import httpx

from trustflow.providers.foxit import FoxitESignProvider


def test_foxit_adapter_hardcodes_draft_only():
    seen = {}
    def handler(request: httpx.Request):
        seen["json"] = request.content.decode()
        return httpx.Response(200, json={"folder": {"folderId": 123, "folderStatus": "DRAFT"}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = FoxitESignProvider("https://example.test/esign", "id", "secret", client)
    result = asyncio.run(provider.create_signature_draft(b"%PDF-1.4 demo", "Jane", "Doe", "jane@example.com"))
    assert '"sendNow":false' in seen["json"]
    assert result["folder_id"] == 123
    assert result["send_now"] is False
    asyncio.run(client.aclose())
