import pytest
from backend.app.review.rules import run_rule_engine, contrast_ratio, relative_luminance

def test_contrast_ratio():
    # Pure black (#000000) and pure white (#ffffff) ratio is 21:1
    ratio = contrast_ratio("#000000", "#ffffff")
    assert round(ratio, 1) == 21.0

    # Low contrast pair (#9aa6b2 on #ffffff) should fail 4.5:1
    bad_ratio = contrast_ratio("#9aa6b2", "#ffffff")
    assert bad_ratio < 4.5

def test_golden_sample_rule_engine():
    text = "Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!"
    terms = [
        {"id": "T-01", "bad_term": "cheap", "preferred_term": "affordable"},
        {"id": "T-02", "bad_term": "customers", "preferred_term": "members"},
    ]
    findings = run_rule_engine(
        text=text,
        terms=terms,
        approved_price="1,199",
        palette=["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"],
        has_image=True,
        alt_text="",
        fg_color="#9aa6b2",
        bg_color="#ffffff",
    )

    sources = [f.source_id for f in findings]
    categories = [f.category for f in findings]

    # Verify all expected rule triggers
    assert "C-01" in sources  # 100% guaranteed results
    assert "C-02" in sources  # #1
    assert "T-01" in sources  # cheap -> affordable
    assert "F-014" in sources # Rs 999 vs Rs 1,199
    assert "R-02" in sources  # Extra exclamation marks
    assert "R-03" in sources  # BUY NOW / LOVE in ALL CAPS
    assert "A-01" in sources  # Missing alt text
    assert "A-02" in sources  # Contrast < 4.5:1
    assert "V-01" in sources  # #9aa6b2 not in palette

    # Verify severity flags
    high_findings = [f for f in findings if f.severity == "high"]
    assert len(high_findings) >= 4  # C-01, C-02, F-014, A-01, A-02

def test_medical_cure_claim():
    text = "Our formula cures eczema in just 3 days."
    findings = run_rule_engine(text=text, terms=[])
    c03 = [f for f in findings if f.source_id == "C-03"]
    assert len(c03) == 1
    assert c03[0].suggested_fix == "helps care for"

def test_sentence_length_accessibility():
    long_sentence = (
        "This serum contains an exquisite combination of multi-molecular hyaluronic acid and organic botanical extracts "
        "formulated by world renowned European dermatologists over many decades to deliver moisture into every subcutaneous layer."
    )
    findings = run_rule_engine(text=long_sentence, terms=[])
    a03 = [f for f in findings if f.source_id == "A-03"]
    assert len(a03) == 1
    assert "Average sentence length" in a03[0].message
