from __future__ import annotations

from .models import ContractFacts, EvidenceItem, RiskAssessment


POLICY_VERSION = "trustflow-policy-v1"


def assess_risk(evidence: list[EvidenceItem], facts: ContractFacts) -> RiskAssessment:
    score = 10
    reasons: list[str] = []
    triggers: list[str] = []

    # Search snippets are signals, not adjudicated facts. They can trigger review, never auto-reject.
    joined = " ".join(f"{e.title} {e.snippet}" for e in evidence).lower()
    adverse_terms = {
        "sanction": 25,
        "fraud": 20,
        "data breach": 15,
        "lawsuit": 8,
        "investigation": 12,
        "bankruptcy": 18,
    }
    for term, weight in adverse_terms.items():
        if term in joined:
            score += weight
            triggers.append(f"Search evidence contains '{term}'; source must be manually verified.")

    if len(evidence) < 3:
        score += 15
        reasons.append("Insufficient independent web evidence.")
        triggers.append("Collect at least three independent evidence sources.")
    else:
        reasons.append(f"Collected {len(evidence)} web evidence items.")

    if facts.auto_renewal is True:
        score += 10
        reasons.append("Contract contains an automatic-renewal term.")
        triggers.append("Confirm renewal notice/cancellation owner.")
    if not facts.liability_cap:
        score += 12
        reasons.append("No liability cap was extracted with sufficient confidence.")
        triggers.append("Legal reviewer should confirm liability allocation.")
    if not facts.governing_law:
        score += 8
        reasons.append("Governing law was not extracted with sufficient confidence.")
        triggers.append("Confirm governing law before signature.")
    if facts.data_processing:
        score += 8
        reasons.append("Document appears to involve data processing.")
        triggers.append("Verify privacy/DPA obligations and subprocessors.")
    if facts.confidence < 0.75:
        score += 15
        reasons.append(f"Document extraction confidence is only {facts.confidence:.0%}.")
        triggers.append("Review source document against extracted fields.")

    score = min(100, score)
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    # Signing is always human-gated regardless of score.
    triggers.append("Explicit human approval is mandatory before any signature request.")
    return RiskAssessment(
        score=score,
        level=level,
        reasons=reasons,
        review_triggers=triggers,
        source_count=len(evidence),
        policy_version=POLICY_VERSION,
    )
