import pytest
from backend.app.review.retrieval import segment_text, retrieve_top_k_sources
from backend.app.review.llm_provider import AIJudgeFinding
from backend.app.review.verify import verify_and_ground_findings
from backend.app.review.pipeline import run_pipeline, ReviewOptions

def test_segment_text():
    text = "Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!"
    segments = segment_text(text)
    assert len(segments) >= 2
    assert any("guaranteed" in s for s in segments)

def test_retrieval_finds_relevant_clauses():
    clauses = [
        {"id": "C-01", "category": "Claims", "title": "Result Claims", "text": "result claims need approved clinical evidence"},
        {"id": "A-01", "category": "Accessibility", "title": "Alt Text", "text": "images need alt text"},
    ]
    facts = [
        {"id": "F-014", "label": "Glow Serum Price", "value": "1,199", "source": "Q4 Price Sheet"}
    ]
    top_sources = retrieve_top_k_sources("100% guaranteed results in 3 days", clauses, facts, k=2)
    ids = [s["id"] for s in top_sources]
    assert "C-01" in ids

def test_verification_discards_hallucinated_quotes():
    full_content = "This is our authentic Lumina Skincare serum."
    retrieved = [{"id": "C-01", "type": "clause", "text": "sample"}]
    facts = []

    # AI outputs a quote that DOES NOT exist in full_content
    fake_finding = [
        AIJudgeFinding(
            issue="Fabricated Quote",
            category="Claims",
            quoted_text="magical cure for wrinkles",  # NOT in content!
            source_id="C-01",
            explanation="Unsubstantiated magic claim"
        )
    ]

    verified = verify_and_ground_findings(fake_finding, full_content, retrieved, facts)
    # Must be discarded according to "evidence or silence"
    assert len(verified) == 0

def test_verification_handles_hallucinated_sources():
    full_content = "Special discount for our customers."
    retrieved = [{"id": "T-01", "type": "term", "text": "cheap -> affordable"}]
    facts = []

    # AI outputs a clause ID not in the retrieved set (e.g. C-99)
    hallucinated_source_finding = [
        AIJudgeFinding(
            issue="Unapproved term",
            category="Terminology",
            quoted_text="customers",
            source_id="C-99",  # NOT in retrieved set!
            explanation="Use members instead"
        )
    ]

    verified = verify_and_ground_findings(hallucinated_source_finding, full_content, retrieved, facts)
    # Must be downgraded to needs_human
    assert len(verified) == 1
    assert verified[0].state == "needs_human"
    assert verified[0].confidence == "low"

def test_pipeline_execution():
    text = "Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!"
    # Rules only execution
    opts_rules = ReviewOptions(rules_only=True, has_image=True, alt_text="")
    res_rules = run_pipeline(text, opts_rules)
    assert not res_rules.ai_used
    assert res_rules.open_count > 0
    assert res_rules.high_count >= 3

    # Full pipeline execution
    opts_full = ReviewOptions(rules_only=False, has_image=True, alt_text="")
    res_full = run_pipeline(text, opts_full)
    assert res_full.open_count > 0
    sources = [f["source_id"] for f in res_full.findings]
    assert "C-01" in sources
    assert "F-014" in sources
