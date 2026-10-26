from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.review.llm_provider import AIJudgeFinding

class VerifiedFinding(BaseModel):
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
    origin: str  # 'rule' | 'ai'
    state: str = "open"  # 'open' | 'accepted' | 'dismissed' | 'needs_human'

def verify_and_ground_findings(
    ai_findings: List[AIJudgeFinding],
    full_content: str,
    retrieved_sources: List[Dict[str, str]],
    approved_facts: List[Dict[str, Any]],
) -> List[VerifiedFinding]:
    """
    L4 Verification & Evidence-Grounded Reliability Layer.
    Enforces 'evidence or silence' and fact verification invariants.
    """
    verified: List[VerifiedFinding] = []
    retrieved_map = {s["id"]: s for s in retrieved_sources}
    facts_map = {f["id"]: f for f in approved_facts}

    for f in ai_findings:
        quoted = f.quoted_text.strip()
        source_id = f.source_id.strip()

        # Invariant 1: Quoted text must exist verbatim in content
        if quoted not in full_content:
            # Check for case-insensitive match
            lower_idx = full_content.lower().find(quoted.lower())
            if lower_idx != -1:
                # Correct quoted text to exact casing from content
                quoted = full_content[lower_idx : lower_idx + len(quoted)]
                span_start = lower_idx
                span_end = lower_idx + len(quoted)
            else:
                # Fabricated quote - discard immediately (evidence or silence)
                continue
        else:
            span_start = full_content.find(quoted)
            span_end = span_start + len(quoted)

        # Invariant 2: Source ID must be in the retrieved set
        if source_id not in retrieved_map:
            # Model hallucinated a non-retrieved clause - downgrade to needs_human
            verified.append(VerifiedFinding(
                category=f.category,
                severity="med",
                confidence="low",
                span_start=span_start,
                span_end=span_end,
                quoted_text=quoted,
                message=f"[Unverified Source {source_id}] {f.explanation}",
                source_type="clause",
                source_id=source_id,
                suggested_fix=f.suggested_fix,
                origin="ai",
                state="needs_human",
            ))
            continue

        # Invariant 3: Fact verification rules
        # "A fact is marked 'incorrect' only if an approved fact contradicts it, otherwise 'unverified'."
        source_item = retrieved_map[source_id]
        source_type = source_item.get("type", "clause")
        severity = "med"
        state = "open"
        confidence = f.confidence or "medium"

        if source_type == "fact":
            fact_record = facts_map.get(source_id)
            if fact_record and fact_record.get("value") and fact_record.get("value") not in quoted:
                severity = "high"
                message = f"Contradicts approved fact {source_id} ({fact_record.get('label')}: {fact_record.get('value')}). {f.explanation}"
            else:
                # No contradiction proven -> unverified
                severity = "low"
                state = "needs_human"
                message = f"Unverified claim against fact {source_id}. Requires human fact-checker verification."
        else:
            # Guideline clause
            if any(term in f.category.lower() for term in ["claim", "unsupported", "guarantee"]):
                severity = "high"
            elif any(term in f.category.lower() for term in ["tone", "voice"]):
                severity = "low"
            message = f"[{source_id}] {f.explanation}"

        verified.append(VerifiedFinding(
            category=f.category,
            severity=severity,
            confidence=confidence,
            span_start=span_start,
            span_end=span_end,
            quoted_text=quoted,
            message=message,
            source_type=source_type,
            source_id=source_id,
            suggested_fix=f.suggested_fix,
            origin="ai",
            state=state,
        ))

    return verified
