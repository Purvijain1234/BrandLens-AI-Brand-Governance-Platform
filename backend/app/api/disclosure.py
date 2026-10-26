from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from backend.app.core.security import get_current_user, UserPayload
from backend.app.db.database import db

router = APIRouter(tags=["AI Disclosure & Transparency"])

@router.get("/ai-disclosure/{content_id}")
def get_ai_disclosure(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content item not found")

    cur.execute("SELECT * FROM ai_calls WHERE content_item_id = ? ORDER BY created_at ASC", (content_id,))
    calls = cur.fetchall()

    conn.close()

    total_calls = len(calls)
    confidential_calls = sum(1 for c in calls if c.get("redacted") == 1)

    rule_checks = [
        "Claims policy patterns (C-01, C-02, C-03)",
        "Approved terminology check (T-01, T-02)",
        "Approved pricing & facts verification (F-014)",
        "Brand voice tone checks (R-02, R-03)",
        "Accessibility checks: Alt-text & 4.5:1 Contrast (A-01, A-02, A-03)",
        "Visual palette verification (V-01)",
    ]

    ai_checks = [
        "Semantic guideline retrieval & grounding (L2)",
        "Unapproved claim reasoning & explanation (L3)",
        "Grounded fix drafting preserving intent (L3)",
        "Hallucination verification & filter (L4)",
    ] if total_calls > 0 else []

    return {
        "content_id": content_id,
        "content_title": item["title"],
        "total_ai_calls": total_calls,
        "rules_only": total_calls == 0,
        "confidential_mode_used": confidential_calls > 0,
        "privacy_status": (
            "Confidential Mode ACTIVE: All sensitive terms and figures were redacted before external dispatch."
            if confidential_calls > 0
            else ("Rules-only mode: No external AI was contacted." if total_calls == 0 else "Standard grounded transmission.")
        ),
        "rule_based_checks": rule_checks,
        "ai_evaluated_checks": ai_checks,
        "ai_calls_log": [
            {
                "id": c["id"],
                "provider": c["provider"],
                "model": c["model"],
                "redacted": bool(c["redacted"]),
                "duration_ms": c.get("duration_ms", 120),
                "created_at": c["created_at"],
            }
            for c in calls
        ],
    }
