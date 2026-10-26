import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.core.security import get_current_user, require_roles, UserPayload
from backend.app.db.database import db
from backend.app.review.pipeline import run_pipeline, ReviewOptions

router = APIRouter(tags=["Content Workflow & Approval"])

# --- Models ---
class ContentCreate(BaseModel):
    title: str = "Untitled post"
    type: str = "Social post"  # 'Social post' | 'Press release' | 'Ad copy' | 'Blog'
    channel: Optional[str] = "Instagram"
    text: str
    has_image: bool = False
    alt_text: Optional[str] = ""
    fg_color: Optional[str] = "#9aa6b2"
    bg_color: Optional[str] = "#ffffff"

class ReviewRequest(BaseModel):
    rules_only: bool = False
    confidential_mode: bool = False
    has_image: bool = False
    alt_text: Optional[str] = ""
    fg_color: Optional[str] = "#9aa6b2"
    bg_color: Optional[str] = "#ffffff"

class DecisionRequest(BaseModel):
    reason: Optional[str] = None
    custom_fix: Optional[str] = None

class CommentCreate(BaseModel):
    finding_id: Optional[str] = None
    body: str

class VerdictRequest(BaseModel):
    reason: Optional[str] = "All brand checks reviewed."

# --- Helper to log audit events ---
def log_audit(conn, org_id: str, content_item_id: str, actor: str, event: str, detail: Optional[dict] = None):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_log (id, org_id, content_item_id, actor, event, detail_json) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), org_id, content_item_id, actor, event, json.dumps(detail or {}))
    )

# --- Endpoints ---
@router.post("/content")
def create_content(payload: ContentCreate, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    item_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    cur.execute(
        "INSERT INTO content_items (id, org_id, title, type, channel, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (item_id, current_user.org_id, payload.title, payload.type, payload.channel, "draft", current_user.full_name or current_user.role)
    )

    cur.execute(
        "INSERT INTO content_versions (id, content_item_id, n, text, created_by, note) VALUES (?, ?, ?, ?, ?, ?)",
        (version_id, item_id, 1, payload.text, current_user.full_name or current_user.role, "Initial draft")
    )

    log_audit(conn, current_user.org_id, item_id, current_user.full_name or current_user.role, "Created", {"title": payload.title})
    conn.commit()
    conn.close()

    return {"status": "created", "content_item_id": item_id, "version_id": version_id}

@router.get("/content")
def list_content(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_items WHERE org_id = ? ORDER BY created_at DESC", (current_user.org_id,))
    items = cur.fetchall()

    result = []
    for it in items:
        # Get open findings count for the latest version
        cur.execute("SELECT id FROM content_versions WHERE content_item_id = ? ORDER BY n DESC LIMIT 1", (it["id"],))
        v = cur.fetchone()
        open_count = 0
        high_count = 0
        if v:
            cur.execute("SELECT COUNT(*) as c FROM findings WHERE version_id = ? AND state = 'open'", (v["id"],))
            open_count = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM findings WHERE version_id = ? AND state = 'open' AND severity = 'high'", (v["id"],))
            high_count = cur.fetchone()["c"]

        result.append({
            **it,
            "open_findings": open_count,
            "high_findings": high_count,
        })

    conn.close()
    return {"content_items": result}

@router.get("/content/{content_id}")
def get_content(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")

    cur.execute("SELECT * FROM content_versions WHERE content_item_id = ? ORDER BY n DESC LIMIT 1", (content_id,))
    latest_version = cur.fetchone()

    findings = []
    if latest_version:
        cur.execute("SELECT * FROM findings WHERE version_id = ? ORDER BY span_start ASC", (latest_version["id"],))
        findings = cur.fetchall()

    cur.execute("SELECT * FROM comments WHERE content_item_id = ? ORDER BY created_at ASC", (content_id,))
    comments = cur.fetchall()

    cur.execute("SELECT * FROM audit_log WHERE content_item_id = ? ORDER BY created_at DESC LIMIT 25", (content_id,))
    raw_audit = cur.fetchall()
    audit = [{**a, "detail": json.loads(a["detail_json"]) if a.get("detail_json") else {}} for a in raw_audit]

    conn.close()
    return {
        "item": item,
        "latest_version": latest_version,
        "findings": findings,
        "comments": comments,
        "audit_log": audit,
    }

@router.post("/content/{content_id}/review")
def run_content_review(content_id: str, req: ReviewRequest, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")

    cur.execute("SELECT * FROM content_versions WHERE content_item_id = ? ORDER BY n DESC LIMIT 1", (content_id,))
    version = cur.fetchone()
    if not version:
        conn.close()
        raise HTTPException(status_code=400, detail="No content version available")

    # Run review pipeline
    opts = ReviewOptions(
        rules_only=req.rules_only,
        confidential_mode=req.confidential_mode,
        has_image=req.has_image,
        alt_text=req.alt_text or "",
        fg_color=req.fg_color or "#9aa6b2",
        bg_color=req.bg_color or "#ffffff",
    )
    result = run_pipeline(
        text=version["text"],
        options=opts,
        org_id=current_user.org_id,
        content_item_id=content_id,
    )

    # Persist findings for this version
    cur.execute("DELETE FROM findings WHERE version_id = ?", (version["id"],))
    for f in result.findings:
        f_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO findings (id, version_id, category, severity, confidence, span_start, span_end, quoted_text, "
            "message, source_type, source_id, suggested_fix, origin, state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f_id,
                version["id"],
                f["category"],
                f["severity"],
                f["confidence"],
                f["span_start"],
                f["span_end"],
                f["quoted_text"],
                f["message"],
                f["source_type"],
                f["source_id"],
                f.get("suggested_fix"),
                f["origin"],
                f.get("state", "open"),
            )
        )
        # Log clause/fact flag event for insights
        log_audit(conn, current_user.org_id, content_id, "System", "flag", {"source_id": f["source_id"], "finding_id": f_id})

    # Log review run
    log_audit(conn, current_user.org_id, content_id, "System", "Automated review", {
        "findings_count": len(result.findings),
        "ai_used": result.ai_used,
        "rules_only": req.rules_only,
        "confidential_mode": req.confidential_mode,
    })

    conn.commit()
    conn.close()

    return {
        "status": "reviewed",
        "result": result.model_dump(),
    }

@router.post("/findings/{finding_id}/accept")
def accept_finding(finding_id: str, req: DecisionRequest, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
    finding = cur.fetchone()
    if not finding:
        conn.close()
        raise HTTPException(status_code=404, detail="Finding not found")

    cur.execute("SELECT * FROM content_versions WHERE id = ?", (finding["version_id"],))
    version = cur.fetchone()
    cur.execute("SELECT * FROM content_items WHERE id = ?", (version["content_item_id"],))
    item = cur.fetchone()

    # Determine replacement text
    replacement = req.custom_fix if req.custom_fix is not None else finding["suggested_fix"]
    if replacement is None:
        replacement = ""

    # Apply diff
    current_text = version["text"]
    s = finding["span_start"]
    e = finding["span_end"]
    if s >= 0 and e <= len(current_text) and s <= e:
        new_text = current_text[:s] + replacement + current_text[e:]
    else:
        new_text = current_text.replace(finding["quoted_text"], replacement, 1)

    # Create new version
    cur.execute("SELECT COUNT(*) as c FROM content_versions WHERE content_item_id = ?", (item["id"],))
    next_n = cur.fetchone()["c"] + 1
    new_version_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO content_versions (id, content_item_id, n, text, created_by, note) VALUES (?, ?, ?, ?, ?, ?)",
        (new_version_id, item["id"], next_n, new_text, current_user.full_name or current_user.role, f"Accepted fix for [{finding['source_id']}]")
    )

    # Mark finding accepted
    cur.execute(
        "UPDATE findings SET state = 'accepted', decided_by = ?, decision_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (current_user.full_name or current_user.role, req.reason or "Accepted suggested fix", finding_id)
    )

    log_audit(conn, current_user.org_id, item["id"], current_user.full_name or current_user.role, "accept", {
        "source_id": finding["source_id"],
        "finding_id": finding_id,
        "quoted_text": finding["quoted_text"],
        "replacement": replacement
    })

    conn.commit()
    conn.close()
    return {"status": "accepted", "new_version_id": new_version_id, "new_text": new_text}

@router.post("/findings/{finding_id}/dismiss")
def dismiss_finding(finding_id: str, req: DecisionRequest, current_user: UserPayload = Depends(get_current_user)):
    if not req.reason or not req.reason.strip():
        raise HTTPException(status_code=400, detail="A reason is required to dismiss a brand finding.")

    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
    finding = cur.fetchone()
    if not finding:
        conn.close()
        raise HTTPException(status_code=404, detail="Finding not found")

    cur.execute("SELECT content_item_id FROM content_versions WHERE id = ?", (finding["version_id"],))
    v = cur.fetchone()

    cur.execute(
        "UPDATE findings SET state = 'dismissed', decided_by = ?, decision_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (current_user.full_name or current_user.role, req.reason.strip(), finding_id)
    )

    log_audit(conn, current_user.org_id, v["content_item_id"], current_user.full_name or current_user.role, "dismiss", {
        "source_id": finding["source_id"],
        "finding_id": finding_id,
        "quoted_text": finding["quoted_text"],
        "reason": req.reason.strip()
    })

    conn.commit()
    conn.close()
    return {"status": "dismissed", "finding_id": finding_id, "reason": req.reason.strip()}

@router.post("/content/{content_id}/submit")
def submit_for_review(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")

    cur.execute("UPDATE content_items SET status = 'in_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (content_id,))
    log_audit(conn, current_user.org_id, content_id, current_user.full_name or current_user.role, "Submitted for review")
    conn.commit()
    conn.close()
    return {"status": "in_review", "content_id": content_id}

@router.post("/content/{content_id}/comments")
def add_comment(content_id: str, req: CommentCreate, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    comment_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO comments (id, content_item_id, finding_id, user_id, user_name, user_role, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (comment_id, content_id, req.finding_id, current_user.user_id, current_user.full_name or current_user.role, current_user.role, req.body.strip())
    )
    log_audit(conn, current_user.org_id, content_id, current_user.full_name or current_user.role, "Comment added", {"comment_id": comment_id})
    conn.commit()
    conn.close()
    return {"status": "created", "comment_id": comment_id}

@router.post("/content/{content_id}/approve")
def approve_content(
    content_id: str,
    req: VerdictRequest,
    current_user: UserPayload = Depends(require_roles(["reviewer", "manager", "admin"]))
):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")

    # Approval Gating: Blocked while HIGH severity findings are open
    cur.execute("SELECT id FROM content_versions WHERE content_item_id = ? ORDER BY n DESC LIMIT 1", (content_id,))
    v = cur.fetchone()
    if v:
        cur.execute("SELECT COUNT(*) as c FROM findings WHERE version_id = ? AND severity = 'high' AND state = 'open'", (v["id"],))
        high_open_count = cur.fetchone()["c"]
        if high_open_count > 0:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Approval blocked: {high_open_count} high-severity finding(s) still open. A human must accept or dismiss each one with a reason."
            )

    cur.execute("UPDATE content_items SET status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (content_id,))
    log_audit(conn, current_user.org_id, content_id, current_user.full_name or current_user.role, "Approved (human sign-off)", {"reason": req.reason})
    conn.commit()
    conn.close()
    return {"status": "approved", "content_id": content_id, "signed_by": current_user.full_name or current_user.role}

@router.post("/content/{content_id}/request-changes")
def request_changes(
    content_id: str,
    req: VerdictRequest,
    current_user: UserPayload = Depends(require_roles(["reviewer", "manager", "admin"]))
):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE content_items SET status = 'changes_requested', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (content_id,))
    log_audit(conn, current_user.org_id, content_id, current_user.full_name or current_user.role, "Requested changes", {"reason": req.reason})
    conn.commit()
    conn.close()
    return {"status": "changes_requested", "content_id": content_id}

@router.get("/content/{content_id}/versions")
def get_versions(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_versions WHERE content_item_id = ? ORDER BY n ASC", (content_id,))
    versions = cur.fetchall()
    conn.close()
    return {"versions": versions}

@router.get("/content/{content_id}/audit")
def get_audit(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_log WHERE content_item_id = ? ORDER BY created_at ASC", (content_id,))
    raw_audit = cur.fetchall()
    audit = [{**a, "detail": json.loads(a["detail_json"]) if a.get("detail_json") else {}} for a in raw_audit]
    conn.close()
    return {"audit_log": audit}

@router.get("/export/{content_id}")
def export_approved_content(content_id: str, current_user: UserPayload = Depends(get_current_user)):
    """
    Exports approved content package with compliance & sign-off certificate.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_items WHERE id = ? AND org_id = ?", (content_id, current_user.org_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Content not found")

    cur.execute("SELECT * FROM content_versions WHERE content_item_id = ? ORDER BY n DESC LIMIT 1", (content_id,))
    latest_version = cur.fetchone()

    cur.execute("SELECT * FROM audit_log WHERE content_item_id = ? AND event LIKE '%Approved%' ORDER BY created_at DESC LIMIT 1", (content_id,))
    approval_event = cur.fetchone()

    cur.execute("SELECT * FROM findings WHERE version_id = ?", (latest_version["id"] if latest_version else "",))
    findings = cur.fetchall()

    conn.close()
    return {
        "brand": "Lumina Skincare",
        "content_id": content_id,
        "title": item["title"],
        "channel": item["channel"],
        "status": item["status"],
        "version_number": latest_version["n"] if latest_version else 1,
        "approved_text": latest_version["text"] if latest_version else "",
        "compliance_certificate": {
            "signed_by": approval_event["actor"] if approval_event else "Pending Approval",
            "signed_at": approval_event["created_at"] if approval_event else None,
            "findings_resolved": len([f for f in findings if f["state"] in ["accepted", "dismissed"]]),
            "governance_hash": str(uuid.uuid4().hex[:16]),
        }
    }
