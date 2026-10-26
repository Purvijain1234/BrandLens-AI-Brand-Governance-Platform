import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class FindingItem(BaseModel):
    category: str
    severity: str  # 'high' | 'med' | 'low'
    confidence: str  # 'high' | 'medium' | 'low'
    span_start: int
    span_end: int
    quoted_text: str
    message: str
    source_type: str  # 'clause' | 'fact' | 'term' | 'asset'
    source_id: str
    suggested_fix: Optional[str] = None
    origin: str = "rule"

# WCAG Luminance and Contrast Calculation
def hex_to_rgb(hex_code: str):
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c*2 for c in hex_code])
    if len(hex_code) != 6:
        return (0, 0, 0)
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def channel_luminance(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def relative_luminance(hex_code: str) -> float:
    try:
        r, g, b = hex_to_rgb(hex_code)
        return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)
    except Exception:
        return 0.0

def contrast_ratio(hex1: str, hex2: str) -> float:
    lum1 = relative_luminance(hex1)
    lum2 = relative_luminance(hex2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

# Unsupported Claims Patterns (C-01, C-02, C-03)
CLAIMS_PATTERNS = [
    (
        re.compile(r"(?:100%\s*)?guaranteed\s+results", re.IGNORECASE),
        "C-01",
        "high",
        "noticeable results with regular use",
        "\"{}\" is a promotional claim with no approved supporting evidence."
    ),
    (
        re.compile(r"#1|number one|\bno\.\s?1\b", re.IGNORECASE),
        "C-02",
        "high",
        "a trusted",
        "\"{}\" is an unverified superlative claim without a cited ranking."
    ),
    (
        re.compile(r"\bbest\b", re.IGNORECASE),
        "C-02",
        "med",
        "a favourite",
        "\"{}\" is a superlative claim; brand guidelines prefer neutral or cited phrasing."
    ),
    (
        re.compile(r"\bcures?\b", re.IGNORECASE),
        "C-03",
        "high",
        "helps care for",
        "\"{}\" is medical-cure language. Skincare products nourish and care for skin, but do not cure conditions."
    ),
]

def run_rule_engine(
    text: str,
    terms: List[Dict[str, Any]],
    approved_price: Optional[str] = "1,199",
    palette: Optional[List[str]] = None,
    has_image: bool = False,
    alt_text: str = "",
    fg_color: str = "#9aa6b2",
    bg_color: str = "#ffffff",
) -> List[FindingItem]:
    """
    L1 Deterministic BrandLens Rule Engine.
    Executes all deterministic checks without external AI.
    """
    findings: List[FindingItem] = []
    palette = [c.lower() for c in (palette or ["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"])]

    # 1. Claims Patterns
    for pattern, clause_id, sev, fix, msg_tmpl in CLAIMS_PATTERNS:
        for m in pattern.finditer(text):
            quoted = m.group(0)
            findings.append(FindingItem(
                category="Unsupported claim",
                severity=sev,
                confidence="high",
                span_start=m.start(),
                span_end=m.end(),
                quoted_text=quoted,
                message=msg_tmpl.format(quoted),
                source_type="clause",
                source_id=clause_id,
                suggested_fix=fix,
                origin="rule",
            ))

    # 2. Terminology Checks
    for term in terms:
        bad_word = term.get("bad_term", "")
        preferred = term.get("preferred_term", "")
        term_id = term.get("id", "term")
        if not bad_word:
            continue
        term_pattern = re.compile(rf"\b{re.escape(bad_word)}\b", re.IGNORECASE)
        for m in term_pattern.finditer(text):
            quoted = m.group(0)
            findings.append(FindingItem(
                category="Terminology",
                severity="med",
                confidence="high",
                span_start=m.start(),
                span_end=m.end(),
                quoted_text=quoted,
                message=f'"{quoted}" is not approved wording; preferred term is "{preferred}".',
                source_type="term",
                source_id=term_id,
                suggested_fix=preferred,
                origin="rule",
            ))

    # 3. Price / Fact Check (F-014)
    price_pattern = re.compile(r"(?:rs\.?|₹|inr)\s*([\d,]+)", re.IGNORECASE)
    cleaned_approved = approved_price.replace(",", "") if approved_price else "1199"
    for m in price_pattern.finditer(text):
        stated_raw = m.group(1).replace(",", "")
        quoted = m.group(0)
        if stated_raw != cleaned_approved:
            findings.append(FindingItem(
                category="Outdated / wrong fact",
                severity="high",
                confidence="high",
                span_start=m.start(),
                span_end=m.end(),
                quoted_text=quoted,
                message=f"Price stated as {quoted} but the approved price is Rs {approved_price}.",
                source_type="fact",
                source_id="F-014",
                suggested_fix=f"Rs {approved_price}",
                origin="rule",
            ))

    # 4. Tone - Exclamation marks limit (R-02)
    exclamations = list(re.finditer(r"!", text))
    if len(exclamations) > 1:
        # Flag subsequent exclamation marks
        for m in exclamations[1:]:
            findings.append(FindingItem(
                category="Tone",
                severity="low",
                confidence="medium",
                span_start=m.start(),
                span_end=m.end(),
                quoted_text="!",
                message="Extra exclamation mark; brand voice allows at most one exclamation mark per post.",
                source_type="clause",
                source_id="R-02",
                suggested_fix=".",
                origin="rule",
            ))

    # 5. Tone - ALL CAPS shouting (R-03)
    caps_pattern = re.compile(r"\b[A-Z]{4,}\b")
    for m in caps_pattern.finditer(text):
        quoted = m.group(0)
        # Fix into title/sentence case
        fix = quoted[0] + quoted[1:].lower()
        findings.append(FindingItem(
            category="Tone",
            severity="low",
            confidence="medium",
            span_start=m.start(),
            span_end=m.end(),
            quoted_text=quoted,
            message=f'"{quoted}" is in ALL CAPS, which reads as shouting.',
            source_type="clause",
            source_id="R-03",
            suggested_fix=fix,
            origin="rule",
        ))

    # 6. Readability - Average sentence length (A-03)
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if sentences:
        total_words = len(text.split())
        avg_words = total_words / len(sentences)
        if avg_words > 25:
            findings.append(FindingItem(
                category="Accessibility",
                severity="med",
                confidence="medium",
                span_start=0,
                span_end=min(len(text), 30),
                quoted_text=text[:30] + "...",
                message=f"Average sentence length is {avg_words:.1f} words (limit: 25 words); shorten for readability.",
                source_type="clause",
                source_id="A-03",
                suggested_fix=None,
                origin="rule",
            ))

    # 7. Accessibility - Alt Text (A-01)
    if has_image and not (alt_text and alt_text.strip()):
        findings.append(FindingItem(
            category="Accessibility",
            severity="high",
            confidence="high",
            span_start=0,
            span_end=0,
            quoted_text="[Image Missing Alt Text]",
            message="The post includes an image but no descriptive alt text was provided.",
            source_type="clause",
            source_id="A-01",
            suggested_fix="Provide descriptive alt text summarizing visual elements.",
            origin="rule",
        ))

    # 8. Accessibility - Text / Background Contrast (A-02)
    if has_image and fg_color and bg_color:
        ratio = contrast_ratio(fg_color, bg_color)
        if ratio < 4.5:
            findings.append(FindingItem(
                category="Accessibility",
                severity="high",
                confidence="high",
                span_start=0,
                span_end=0,
                quoted_text=f"Contrast {ratio:.2f}:1",
                message=f"Text/background contrast is {ratio:.2f}:1 (WCAG AA requirement: at least 4.5:1).",
                source_type="clause",
                source_id="A-02",
                suggested_fix="Increase color contrast between text and background.",
                origin="rule",
            ))

    # 9. Visual Consistency - Brand Palette Check (V-01)
    if has_image:
        for c, name in [(fg_color, "Text"), (bg_color, "Background")]:
            if c and c.lower() not in palette:
                findings.append(FindingItem(
                    category="Visual consistency",
                    severity="med",
                    confidence="medium",
                    span_start=0,
                    span_end=0,
                    quoted_text=c,
                    message=f"{name} colour {c} is not in the approved brand palette ({', '.join(palette)}).",
                    source_type="clause",
                    source_id="V-01",
                    suggested_fix=palette[0],
                    origin="rule",
                ))

    # Sort findings by span_start
    findings.sort(key=lambda x: (x.span_start, x.span_end))
    return findings
