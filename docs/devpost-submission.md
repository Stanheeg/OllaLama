# Devpost submission draft — TrustFlow

## Project name
TrustFlow

## One-line pitch
**Evidence before signature:** an agent that researches a vendor, extracts contract obligations, scores review risk, creates an auditable approval packet, and stops at an explicit human boundary before e-signature.

## Problem
Vendor and contract approvals are fragmented. Procurement or operations teams search the web in one tab, read agreements in another, copy conclusions into workflow tools, generate approval documents elsewhere, and finally hand the result to an e-signature product. AI can speed up that work, but giving an agent authority to approve or dispatch a legal agreement creates a new class of risk.

## Solution
TrustFlow turns the process into one traceable agentic workflow while keeping authority with a person.

1. **SerpApi** supplies fresh vendor evidence as provenance-bearing review signals.
2. **Nutrient DWS** extracts schema-constrained agreement facts, confidence, and citations from the source document.
3. A deterministic policy engine scores review risk; optional **Gemini** synthesizes the evidence but has no approval authority.
4. **Xano** is designed as the resumable workflow and append-only audit system of record.
5. After explicit human approval, **Doctavian** generates the structured approval/document packet.
6. A second explicit human-intent gate allows **Foxit eSign** to create a draft. TrustFlow hardcodes `sendNow=false`, so the agent cannot autonomously dispatch the agreement.

Every workflow transition is chained with SHA-256 audit hashes so a reviewer can detect missing or reordered events.

## What software does it replace?
TrustFlow replaces the fragmented combination of vendor research spreadsheets, manual contract review notes, procurement approval tickets, document-generation steps, and unsafe agent-to-signature glue. It does not replace the human who is accountable for approval.

## Technical implementation
- Python 3.11+
- FastAPI + Pydantic
- SQLite local durable state
- SHA-256 chained audit events
- SerpApi provider adapter
- Nutrient DWS extraction adapter
- Xano workflow/audit mirror adapter
- Doctavian generation adapter
- Foxit eSign draft-only adapter
- Optional Gemini evidence synthesizer
- Responsive browser UI
- Pytest negative-gate and provider-contract tests

## Validation already completed
- 9/9 local tests passed before publication.
- Full HTTP flow exercised end-to-end in fixture mode.
- Document generation is rejected before approval (HTTP 409).
- Rejected workflows stay blocked.
- Signature draft creation requires a second explicit human confirmation.
- Foxit request contract is tested to keep `sendNow=false`.
- Five chained audit events persisted in the end-to-end run.

Fixture-mode validation proves the orchestration and safety controls only. It is **not** presented as live sponsor-API evidence. Live sponsor evidence will be added only after authenticated event/free credentials are configured and real calls succeed.

## Why the integrations are substantive
Each sponsor technology owns a necessary stage of one causal workflow; none is included only to satisfy a badge requirement. Removing any of the five core sponsor stages changes the product behavior: evidence collection, document understanding, workflow persistence, packet generation, or the signature boundary disappears.

## Build story
TrustFlow was built during the DevNetwork API + Cloud + AI Hackathon 2026 window. AI-assisted development accelerated provider-contract research, implementation, test generation, and documentation, while the final safety policy is deterministic and testable rather than delegated to a model.

## Public source
https://github.com/Stanheeg/OllaLama/tree/trustflow-entry

## Demo structure
See `docs/demo-script.md` for the 2–4 minute judge walkthrough and `docs/submission-matrix.md` for sponsor-specific evidence gates.
