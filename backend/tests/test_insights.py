import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_governance_insights():
    resp = client.get("/insights")
    assert resp.status_code == 200
    data = resp.json()

    # 1. Summary structure
    assert "summary" in data
    assert "total_documents" in data["summary"]

    # 2. Per-clause analytics
    clauses = data["clause_analytics"]
    assert len(clauses) > 0

    # 3. Major Improvement 1: "Possibly unclear guideline" detection
    # In seed data, R-02 has >= 3 flags and >= 50% dismiss rate
    r02 = next((c for c in clauses if c["source_id"] == "R-02"), None)
    assert r02 is not None
    assert r02["flags"] >= 3
    assert r02["dismiss_rate"] >= 50.0
    assert r02["is_unclear"] is True
    assert r02["signal"] == "Possibly unclear guideline"

    # 4. Expiring facts
    facts = data["expiring_facts"]
    assert any(f["id"] == "F-014" for f in facts)
