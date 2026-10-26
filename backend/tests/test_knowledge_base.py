import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_facts_and_terms():
    # Public / creator read access
    resp = client.get("/facts")
    assert resp.status_code == 200
    facts = resp.json()["facts"]
    assert any(f["id"] == "F-014" for f in facts)

    resp_terms = client.get("/terms")
    assert resp_terms.status_code == 200
    terms = resp_terms.json()["terms"]
    assert any(t["id"] == "T-01" for t in terms)

def test_role_enforcement_on_kb():
    # Creator role should be blocked from creating facts (403 Forbidden)
    headers = {"X-User-Role": "creator"}
    resp = client.post("/facts", json={
        "label": "Test Fact",
        "value": "100",
        "source": "Manual",
        "owner": "Tester"
    }, headers=headers)
    assert resp.status_code == 403

    # Admin role should succeed
    admin_headers = {"X-User-Role": "admin"}
    resp_admin = client.post("/facts", json={
        "id": "F-999",
        "label": "Test Fact Admin",
        "value": "100",
        "source": "Manual",
        "owner": "Admin"
    }, headers=admin_headers)
    assert resp_admin.status_code == 200

def test_import_guidelines():
    admin_headers = {"X-User-Role": "admin"}
    guideline_text = (
        "C-10: Claims must always cite published peer-reviewed journals.\n"
        "Voice 2.4: Keep an upbeat and encouraging brand tone across all social channels.\n"
        "A-05: Ensure videos contain closed captions."
    )
    resp = client.post("/guidelines/import", json={
        "title": "Social Guidelines Addendum",
        "version": "1.1",
        "description": "Imported policy rules",
        "content": guideline_text
    }, headers=admin_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["imported_clauses_count"] == 3
    clauses = data["clauses"]
    ids = [c["id"] for c in clauses]
    assert "C-10" in ids
