import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_workflow_and_approval_gating():
    creator_headers = {"X-User-Role": "creator"}
    reviewer_headers = {"X-User-Role": "reviewer"}
    manager_headers = {"X-User-Role": "manager"}

    # 1. Creator creates a draft post with policy violations
    post_resp = client.post("/content", json={
        "title": "Serum Launch Campaign",
        "type": "Social post",
        "channel": "Instagram",
        "text": "Get 100% guaranteed results with our #1 serum! Cheap prices, only Rs 999 this week!!"
    }, headers=creator_headers)
    assert post_resp.status_code == 200
    content_id = post_resp.json()["content_item_id"]

    # 2. Run automated brand review
    review_resp = client.post(f"/content/{content_id}/review", json={
        "rules_only": True,
        "has_image": False
    }, headers=creator_headers)
    assert review_resp.status_code == 200
    findings = review_resp.json()["result"]["findings"]
    assert len(findings) > 0
    high_findings = [f for f in findings if f["severity"] == "high"]
    assert len(high_findings) >= 2  # C-01, C-02, F-014

    # 3. Creator submits for review
    sub_resp = client.post(f"/content/{content_id}/submit", headers=creator_headers)
    assert sub_resp.status_code == 200

    # 4. CRITICAL INVARIANT: Reviewer/Manager tries to approve while HIGH findings are unresolved
    # Must be strictly BLOCKED!
    approve_blocked = client.post(f"/content/{content_id}/approve", json={"reason": "Looks good"}, headers=manager_headers)
    assert approve_blocked.status_code == 400
    assert "Approval blocked" in approve_blocked.json()["detail"]

    # 5. Dismissing without reason must be rejected
    get_doc = client.get(f"/content/{content_id}", headers=creator_headers)
    active_findings = get_doc.json()["findings"]
    first_high = next(f for f in active_findings if f["severity"] == "high")

    dismiss_no_reason = client.post(f"/findings/{first_high['id']}/dismiss", json={"reason": ""}, headers=creator_headers)
    assert dismiss_no_reason.status_code == 400

    # 6. Resolve all open findings (Accept fixes or Dismiss with recorded reason)
    for f in active_findings:
        if f["suggested_fix"]:
            client.post(f"/findings/{f['id']}/accept", json={"reason": "Approved suggested correction"}, headers=creator_headers)
        else:
            client.post(f"/findings/{f['id']}/dismiss", json={"reason": "Authorized exception with legal clearance"}, headers=creator_headers)

    # 7. Check versions: Accepting fixes generated new versions
    v_resp = client.get(f"/content/{content_id}/versions", headers=creator_headers)
    assert v_resp.status_code == 200
    versions = v_resp.json()["versions"]
    assert len(versions) > 1

    # 8. Add collaboration comment
    comment_resp = client.post(f"/content/{content_id}/comments", json={
        "body": "All high severity claims fixed. Ready for manager sign-off."
    }, headers=reviewer_headers)
    assert comment_resp.status_code == 200

    # 9. Now that all high severity findings are resolved, Manager can approve!
    approve_success = client.post(f"/content/{content_id}/approve", json={
        "reason": "Brand voice and claims verified."
    }, headers=manager_headers)
    assert approve_success.status_code == 200
    assert approve_success.json()["status"] == "approved"

    # 10. Verify audit log contains full chronological trail
    audit_resp = client.get(f"/content/{content_id}/audit", headers=creator_headers)
    assert audit_resp.status_code == 200
    trail = audit_resp.json()["audit_log"]
    events = [a["event"] for a in trail]
    assert "Created" in events
    assert "Submitted for review" in events
    assert "Approved (human sign-off)" in events

    # 11. Verify export certificate
    export_resp = client.get(f"/export/{content_id}", headers=creator_headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["status"] == "approved"
    assert export_data["compliance_certificate"]["signed_by"] is not None
