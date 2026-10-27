import sys
import os
import json
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app.main import app

def run_3_minute_demo():
    client = TestClient(app)
    creator_headers = {"X-User-Role": "creator"}
    manager_headers = {"X-User-Role": "manager"}

    print("=" * 80)
    print(" BRANDLENS · 3-MINUTE HACKATHON JUDGE DEMONSTRATION ")
    print(" Team Double Trouble · Pre-Publication AI Brand Governance ")
    print("=" * 80)

    # 1. Post Creation
    print("\n[STEP 1] Creator drafts post with policy violations (The Golden Sample):")
    sample_text = "Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!"
    print(f"Content: \"{sample_text}\"")

    create_res = client.post("/content", json={
        "title": "Lumina Glow Serum Launch",
        "type": "Social post",
        "channel": "Instagram",
        "text": sample_text
    }, headers=creator_headers)
    doc_id = create_res.json()["content_item_id"]
    print(f"-> Document created in database (ID: {doc_id})")

    # 2. Automated Brand Review
    print("\n[STEP 2] Running Multi-Layer Brand Governance Pipeline (L1 Rules -> L2 Retrieval -> L3 AI -> L4 Verification)...")
    rev_res = client.post(f"/content/{doc_id}/review", json={
        "rules_only": False,
        "confidential_mode": False,
        "has_image": True,
        "alt_text": "",
        "fg_color": "#9aa6b2",
        "bg_color": "#ffffff"
    }, headers=creator_headers)
    findings = rev_res.json()["result"]["findings"]
    print(f"-> Automated Review complete: {len(findings)} findings raised!")
    for f in findings:
        sev_tag = f"[{f['severity'].upper()}]"
        print(f"   {sev_tag:<8} {f['source_id']:<6} | {f['category']:<20} | \"{f['quoted_text']}\" -> {f['message']}")

    # 3. Test Invariant: Human Gating / Approval Blocked
    print("\n[STEP 3] Testing Core Invariant 4: Human Approval Gating...")
    client.post(f"/content/{doc_id}/submit", headers=creator_headers)
    blocked_approval = client.post(f"/content/{doc_id}/approve", json={"reason": "Looks good to me"}, headers=manager_headers)
    print(f"Manager attempted approval with open HIGH findings -> Status: {blocked_approval.status_code}")
    print(f"Block Reason: {blocked_approval.json().get('detail')}")
    assert blocked_approval.status_code == 400

    # 4. Resolve Findings
    print("\n[STEP 4] Creator reviews diff suggestions, accepts fixes, and dismisses with mandatory reason:")
    active_findings = client.get(f"/content/{doc_id}", headers=creator_headers).json()["findings"]
    for f in active_findings:
        if f["suggested_fix"]:
            acc = client.post(f"/findings/{f['id']}/accept", json={"reason": "Accepting brand standard"}, headers=creator_headers)
            print(f"   Accepted fix for [{f['source_id']}]: \"{f['quoted_text']}\" -> \"{f['suggested_fix']}\"")
        else:
            client.post(f"/findings/{f['id']}/dismiss", json={"reason": "Legal clearance granted under promo license #992"}, headers=creator_headers)
            print(f"   Dismissed [{f['source_id']}] with recorded audit reason.")

    # 5. Sign-off and Compliance Export
    print("\n[STEP 5] All high-severity findings resolved -> Manager approves:")
    approved_res = client.post(f"/content/{doc_id}/approve", json={"reason": "Brand voice & clinical claims validated"}, headers=manager_headers)
    print(f"-> Approval Status: {approved_res.json()['status']} by {approved_res.json()['signed_by']}")

    export_res = client.get(f"/export/{doc_id}", headers=creator_headers).json()
    print("\n[COMPLIANCE CERTIFICATE EXPORT]:")
    print(f"   Signed By:           {export_res['compliance_certificate']['signed_by']}")
    print(f"   Governance Hash:     {export_res['compliance_certificate']['governance_hash']}")
    print(f"   Approved Clean Text: \"{export_res['approved_text']}\"")

    # 6. Confidential Mode & AI Disclosure
    print("\n[STEP 6] Major Improvement 3: Confidential Mode & AI Disclosure Ledger:")
    conf_doc = client.post("/content", json={
        "title": "Q3 Secret Roadmap",
        "type": "Press release",
        "text": "Project Radiance is launching with 100% guaranteed results and $4.2M pre-orders."
    }, headers=creator_headers).json()["content_item_id"]
    client.post(f"/content/{conf_doc}/review", json={"confidential_mode": True}, headers=creator_headers)
    disc = client.get(f"/ai-disclosure/{conf_doc}", headers=creator_headers).json()
    print(f"   Privacy Status:      {disc['privacy_status']}")
    print(f"   Total AI Calls:      {disc['total_ai_calls']} (Redacted: {disc['confidential_mode_used']})")

    # 7. Governance Insights
    print("\n[STEP 7] Major Improvement 1: Guideline Clarity Insights (Real Audit Data):")
    ins = client.get("/insights", headers=creator_headers).json()
    print(f"   Total Docs:          {ins['summary']['total_documents']}")
    print(f"   Avg Turnaround:      {ins['summary']['avg_turnaround_minutes']} minutes")
    print(f"   Unclear Rules Alert: {ins['summary']['unclear_guidelines_count']} detected (dismiss rate >= 50%)")
    for c in ins["clause_analytics"][:4]:
        print(f"   - [{c['source_id']}] Flags: {c['flags']} | Accepted: {c['accepts']} | Dismissed: {c['dismisses']} ({c['dismiss_rate']}%) -> {c['signal']}")

    print("\n" + "=" * 80)
    print(" DEMONSTRATION COMPLETED SUCCESSFULLY IN FULL COMPLIANCE ")
    print("=" * 80)

if __name__ == "__main__":
    run_3_minute_demo()
