import hashlib
import time
import uuid
from typing import List, Dict, Any, Optional
from backend.app.review.llm_provider import get_llm_provider, AIJudgeFinding
from backend.app.db.database import db

# In-memory AI judgment cache by SHA-256 content hash
AI_CACHE: Dict[str, List[AIJudgeFinding]] = {}

def get_hash(text: str, sources_ids: List[str]) -> str:
    key = text.strip() + "|" + ",".join(sorted(sources_ids))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def run_ai_judge(
    segment: str,
    retrieved_sources: List[Dict[str, str]],
    content_item_id: Optional[str] = None,
    org_id: Optional[str] = "00000000-0000-0000-0000-000000000001",
    confidential_mode: bool = False,
    redaction_map: Optional[Dict[str, str]] = None,
) -> List[AIJudgeFinding]:
    """
    L3 AI Judge Layer.
    Dispatches segmented text + retrieved sources to LLM provider with caching and AI audit logging.
    """
    if not retrieved_sources:
        return []

    sources_ids = [s["id"] for s in retrieved_sources]
    cache_key = get_hash(segment, sources_ids)
    if cache_key in AI_CACHE:
        return AI_CACHE[cache_key]

    # Confidential Mode: Pre-redaction of sensitive terms
    processed_segment = segment
    if confidential_mode and redaction_map:
        for term, placeholder in redaction_map.items():
            processed_segment = processed_segment.replace(term, placeholder)

    provider = get_llm_provider()
    start_time = time.time()
    
    try:
        findings = provider.generate_judge_findings(processed_segment, retrieved_sources)
        duration_ms = int((time.time() - start_time) * 1000)

        # Confidential Mode: Post-restoration of placeholders
        if confidential_mode and redaction_map:
            reverse_map = {placeholder: term for term, placeholder in redaction_map.items()}
            restored_findings = []
            for f in findings:
                quoted = f.quoted_text
                expl = f.explanation
                fix = f.suggested_fix or ""
                for placeholder, term in reverse_map.items():
                    quoted = quoted.replace(placeholder, term)
                    expl = expl.replace(placeholder, term)
                    fix = fix.replace(placeholder, term)
                restored_findings.append(AIJudgeFinding(
                    issue=f.issue,
                    category=f.category,
                    quoted_text=quoted,
                    source_id=f.source_id,
                    explanation=expl,
                    suggested_fix=fix if fix else None,
                    confidence=f.confidence
                ))
            findings = restored_findings

        # Record into AI calls ledger
        if content_item_id:
            try:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO ai_calls (id, org_id, content_item_id, provider, model, redacted, duration_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        org_id,
                        content_item_id,
                        provider.__class__.__name__,
                        "gemini-2.5-flash" if "Gemini" in provider.__class__.__name__ else "mock-judge",
                        1 if confidential_mode else 0,
                        duration_ms,
                    )
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI Ledger] Failed to log AI call: {e}")

        # Store in cache
        AI_CACHE[cache_key] = findings
        return findings

    except Exception as e:
        print(f"[AI Judge Error]: {e}")
        return []
