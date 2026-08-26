# TrustFlow

**Evidence before signature.** TrustFlow is a vendor and contract approval agent that collects live evidence, extracts agreement facts, evaluates risk, creates an auditable approval packet, and stops at an explicit human boundary before e-signature.

It is deliberately not a chatbot and not an autonomous contract signer.

## Why this is a strong hackathon entry

The integrations each own a necessary stage instead of being badgeware:

| Stage | Live integration | What it contributes |
|---|---|---|
| Vendor evidence | **SerpApi** | Fresh, structured web evidence used by the risk workflow |
| Contract understanding | **Nutrient DWS** | Schema-constrained extraction with citations/confidence from a real PDF |
| Workflow system of record | **Xano** | Resumable workflow state plus append-only audit-event storage |
| Evidence synthesis | **Gemini (optional)** | Concise synthesis; explicitly has no approval authority |
| Approval packet | **Doctavian** | Template-driven document generation from structured evidence and approval data |
| Human signature boundary | **Foxit eSign** | Creates a draft envelope only after human approval; `sendNow=false` is a code invariant |

The project can therefore be entered into several DevNetwork sponsor challenges without inventing unrelated features. The same architecture can also be adapted to the All Things Agentic hackathon by deploying the orchestration on Google Cloud and using Gemini as the live reasoner.

## Proof gates already implemented

- Web evidence is treated as **unverified signals**, not truth.
- Deterministic policy controls workflow state; an LLM cannot approve anything.
- Explicit human approval is required before document generation.
- A **second** explicit human-intent confirmation is required before eSign draft creation.
- Foxit request hardcodes `sendNow=false`; TrustFlow cannot dispatch a signature request autonomously.
- Every state transition is chained with SHA-256 audit hashes.
- SQLite is the local durable store; live mode mirrors workflow/audit state to Xano.
- Provider integrations are isolated and contract-tested.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[test]'
pytest
uvicorn trustflow.app:app --reload
```

Open `http://127.0.0.1:8000`.

Fixture mode is the default and makes **zero external calls**. It proves the orchestration and safety gates; it is not evidence of sponsor API use.

## Live mode

Copy `.env.example`, export the values, then set:

```text
TRUSTFLOW_MODE=live
```

Required for the multi-sponsor contest build:

- `SERPAPI_API_KEY`
- `NUTRIENT_API_KEY`
- Xano workflow/audit endpoint URLs
- Doctavian event credentials, generation endpoint and template ID
- `FOXIT_CLIENT_ID` / `FOXIT_CLIENT_SECRET`

Optional but recommended for the AI/agent story:

- `GEMINI_API_KEY`

### Important Doctavian integration note

Doctavian publicly describes an API-first/headless REST platform but the public marketing page does not expose the contest account's exact generation route. `DoctavianDocumentGenerator` therefore requires the exact event quickstart URL/template ID at configuration time rather than fabricating an endpoint. This is intentional and should be replaced with the sponsor-provided values before the contest demo.

## Official provider routes encoded in this build

- SerpApi: `GET https://serpapi.com/search.json`
- Nutrient DWS: `POST https://api.nutrient.io/extraction/extract`
- Foxit eSign: `POST https://na1.fusion.foxit.com/esign/api/v1/folders/createfolder`
- Xano and Doctavian: workspace/account-specific URLs supplied through environment variables

## Tests

The suite proves the important negative cases, not just the happy path:

```bash
pytest -q
```

- creation always lands in human review;
- audit hash continuity;
- generation rejected before approval;
- rejected workflow remains blocked;
- signature draft rejected without second human confirmation;
- Foxit live payload always uses `sendNow=false`;
- SerpApi endpoint/parsing contract;
- Xano workflow/audit mirroring contract.

## Submission work still required

The artifact is **PARTIAL, not contest-ready**, until these gates are passed with real event accounts:

1. Register the Devpost entry.
2. Obtain the free/event sponsor credentials.
3. Configure Xano schema/endpoints from `docs/xano-schema.md`.
4. Create a Doctavian template and wire its exact quickstart endpoint.
5. Run at least one real end-to-end workflow and preserve API/dashboard evidence.
6. Record the demo from `docs/demo-script.md`.
7. Publish/share the repository and submit it to the applicable sponsor challenges.

Do not claim sponsor integration from fixture-mode screenshots.
