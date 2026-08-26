import asyncio
import json
import httpx

from trustflow.providers.search import SerpApiSearchProvider
from trustflow.providers.xano import XanoMirror


def test_serpapi_uses_official_search_endpoint_and_parses_evidence():
    seen = {}
    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"organic_results":[{"title":"Acme","link":"https://acme.test","snippet":"Profile"}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    p = SerpApiSearchProvider("key", client)
    items = asyncio.run(p.search_vendor("Acme", "acme.test"))
    assert "serpapi.com/search.json" in seen["url"]
    assert items[0].url == "https://acme.test"
    asyncio.run(client.aclose())


def test_xano_mirror_posts_workflow_and_audit_to_configured_backend():
    paths=[]
    def handler(request: httpx.Request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"ok":True})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    x=XanoMirror("https://xano.test/workflow","https://xano.test/audit","token",client)
    asyncio.run(x.upsert_workflow({"id":"w1"}))
    asyncio.run(x.record_audit("w1", {"event":"created"}))
    assert paths == ["/workflow","/audit"]
    asyncio.run(client.aclose())
