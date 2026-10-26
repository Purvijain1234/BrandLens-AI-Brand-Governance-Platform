import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_confidential_mode_and_ai_ledger():
    creator_headers = {"X-User-Role": "creator"}

    # 1. Create content containing confidential terms
    create_resp = client.post("/content", json={
        "title": "Secret Q3 Launch",
        "type": "Press release",
        "channel": "PR Newswire",
        "text": "Project Radiance is launching with 100% guaranteed results and generated $4.2M in pre-orders!"
    }, headers=creator_headers)
    assert create_resp.status_code == 200
    content_id = create_resp.json()["content_item_id"]

    # 2. Run review with Confidential Mode ON
    rev_resp = client.post(f"/content/{content_id}/review", json={
        "rules_only": False,
        "confidential_mode": True,
        "has_image": False
    }, headers=creator_headers)
    assert rev_resp.status_code == 200

    # 3. Query AI disclosure panel
    disc_resp = client.get(f"/ai-disclosure/{content_id}", headers=creator_headers)
    assert disc_resp.status_code == 200
    data = disc_resp.json()
    assert data["confidential_mode_used"] is True
    assert "Confidential Mode ACTIVE" in data["privacy_status"]
    assert len(data["ai_calls_log"]) > 0
    assert data["ai_calls_log"][0]["redacted"] is True

    # 4. Test Rules-Only Mode
    create_rules_resp = client.post("/content", json={
        "title": "Offline Review Post",
        "type": "Ad copy",
        "text": "Cheap prices this week!!"
    }, headers=creator_headers)
    c_rules_id = create_rules_resp.json()["content_item_id"]

    client.post(f"/content/{c_rules_id}/review", json={
        "rules_only": True
    }, headers=creator_headers)

    rules_disc = client.get(f"/ai-disclosure/{c_rules_id}", headers=creator_headers)
    assert rules_disc.status_code == 200
    r_data = rules_disc.json()
    assert r_data["rules_only"] is True
    assert r_data["total_ai_calls"] == 0
    assert "Rules-only mode" in r_data["privacy_status"]
