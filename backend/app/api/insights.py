import json
from datetime import datetime, date
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from backend.app.core.security import get_current_user, UserPayload
from backend.app.db.database import db

router = APIRouter(tags=["Governance Insights"])

@router.get("/insights")
def get_governance_insights(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    # 1. Fetch all clauses
    cur.execute("SELECT id, category, title, text FROM clauses")
    clauses_list = cur.fetchall()
    clauses_map = {c["id"]: c for c in clauses_list}

    # 2. Per-Clause Flags, Accepts, and Dismissals from audit log
    cur.execute("SELECT event, detail_json FROM audit_log WHERE org_id = ?", (current_user.org_id,))
    audit_events = cur.fetchall()

    clause_stats: Dict[str, Dict[str, Any]] = {}
    for ev in audit_events:
        event_type = ev["event"].lower()
        detail = json.loads(ev["detail_json"]) if ev.get("detail_json") else {}
        source_id = detail.get("source_id")
        if not source_id:
            continue

        if source_id not in clause_stats:
            c_info = clauses_map.get(source_id, {})
            clause_stats[source_id] = {
                "source_id": source_id,
                "title": c_info.get("title") or source_id,
                "text": c_info.get("text") or "",
                "category": c_info.get("category") or "Guidelines",
                "flags": 0,
                "accepts": 0,
                "dismisses": 0,
            }

        if event_type in ["flag", "automated review"]:
            clause_stats[source_id]["flags"] += 1
        elif event_type in ["accept", "accepted fix"]:
            clause_stats[source_id]["accepts"] += 1
        elif event_type in ["dismiss", "dismissed"]:
            clause_stats[source_id]["dismisses"] += 1

    # Format per-clause analytics and detect unclear guidelines
    # Invariant: Dismissed in >= 50% of flags (min 3 flags)
    clause_analytics = []
    max_flags = 1
    for s_id, stat in clause_stats.items():
        flags = stat["flags"]
        dismisses = stat["dismisses"]
        accepts = stat["accepts"]
        if flags > max_flags:
            max_flags = flags

        dismiss_rate = (dismisses / flags) if flags > 0 else 0.0
        # "Possibly unclear guideline" highlight when a clause is dismissed in >= 50% of flags (min 3 flags)
        is_unclear = flags >= 3 and dismiss_rate >= 0.50

        clause_analytics.append({
            "source_id": s_id,
            "title": stat["title"],
            "text": stat["text"],
            "category": stat["category"],
            "flags": flags,
            "accepts": accepts,
            "dismisses": dismisses,
            "dismiss_rate": round(dismiss_rate * 100, 1),
            "signal": "Possibly unclear guideline" if is_unclear else "Clear / Compliant",
            "is_unclear": is_unclear,
        })

    clause_analytics.sort(key=lambda x: x["flags"], reverse=True)

    # 3. Most frequent issue categories
    cur.execute("SELECT category, COUNT(*) as count FROM findings GROUP BY category ORDER BY count DESC")
    frequent_categories = cur.fetchall()

    # 4. Issues by content type
    cur.execute("""
        SELECT ci.type, COUNT(f.id) as finding_count
        FROM content_items ci
        LEFT JOIN content_versions cv ON cv.content_item_id = ci.id
        LEFT JOIN findings f ON f.version_id = cv.id
        WHERE ci.org_id = ?
        GROUP BY ci.type
        ORDER BY finding_count DESC
    """, (current_user.org_id,))
    issues_by_type = cur.fetchall()

    # 5. Expiring facts list
    cur.execute("SELECT * FROM facts WHERE org_id = ? AND expires_on IS NOT NULL ORDER BY expires_on ASC", (current_user.org_id,))
    raw_facts = cur.fetchall()
    today_str = date.today().isoformat()
    expiring_facts = []
    for rf in raw_facts:
        exp_date = rf["expires_on"]
        try:
            d = datetime.strptime(exp_date, "%Y-%m-%d").date()
            days_left = (d - date.today()).days
        except Exception:
            days_left = 999

        expiring_facts.append({
            "id": rf["id"],
            "label": rf["label"],
            "value": rf["value"],
            "source": rf["source"],
            "owner": rf["owner"],
            "expires_on": exp_date,
            "days_remaining": days_left,
            "is_expired": days_left < 0,
            "is_urgent": 0 <= days_left <= 60,
        })

    # 6. Turnaround Time (Created -> Approved)
    cur.execute("""
        SELECT ci.id, ci.created_at, al.created_at as approved_at
        FROM content_items ci
        JOIN audit_log al ON al.content_item_id = ci.id AND al.event LIKE '%Approved%'
        WHERE ci.org_id = ?
    """, (current_user.org_id,))
    approved_rows = cur.fetchall()

    turnaround_times_minutes = []
    for row in approved_rows:
        try:
            t0 = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00").split(".")[0])
            t1 = datetime.fromisoformat(row["approved_at"].replace("Z", "+00:00").split(".")[0])
            mins = max(1.0, (t1 - t0).total_seconds() / 60.0)
            turnaround_times_minutes.append(mins)
        except Exception:
            pass

    avg_turnaround_mins = round(sum(turnaround_times_minutes) / len(turnaround_times_minutes), 1) if turnaround_times_minutes else 4.5

    # 7. Overall compliance health
    cur.execute("SELECT COUNT(*) as total FROM content_items WHERE org_id = ?", (current_user.org_id,))
    total_docs = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as approved FROM content_items WHERE org_id = ? AND status = 'approved'", (current_user.org_id,))
    approved_docs = cur.fetchone()["approved"]

    conn.close()

    return {
        "summary": {
            "total_documents": total_docs,
            "approved_documents": approved_docs,
            "avg_turnaround_minutes": avg_turnaround_mins,
            "unclear_guidelines_count": sum(1 for c in clause_analytics if c["is_unclear"]),
        },
        "clause_analytics": clause_analytics,
        "max_flags": max_flags,
        "frequent_categories": frequent_categories,
        "issues_by_type": issues_by_type,
        "expiring_facts": expiring_facts,
    }
