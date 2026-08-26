from trustflow.models import ContractFacts, EvidenceItem
from trustflow.risk import assess_risk


def test_search_adverse_language_only_triggers_review_not_autonomous_rejection():
    evidence = [
        EvidenceItem(title="Investigation report", url="https://example.com/a", snippet="Company faces investigation"),
        EvidenceItem(title="Official", url="https://example.com/b", snippet="Official profile"),
        EvidenceItem(title="Registry", url="https://example.com/c", snippet="Registry record"),
    ]
    risk = assess_risk(evidence, ContractFacts(governing_law="NL", liability_cap="12 months fees", confidence=.9))
    assert risk.score > 10
    assert any("manually verified" in t for t in risk.review_triggers)
    assert any("human approval" in t.lower() for t in risk.review_triggers)
