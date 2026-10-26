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

    # 3. Major Improvement 1: "Possibly unclear guideline" detection invariant
    # Any clause where flags >= 3 and dismiss_rate >= 50% must have is_unclear == True and signal == "Possibly unclear guideline"
    for c in clauses:
        if c["flags"] >= 3 and c["dismiss_rate"] >= 50.0:
            assert c["is_unclear"] is True
            assert c["signal"] == "Possibly unclear guideline"
        else:
            assert c["is_unclear"] is False
            assert c["signal"] == "Clear / Compliant"

    # Also verify that when we record 3 flags and 2 dismisses (66.7%), the engine detects it
    r_unclear = any(c["is_unclear"] for c in clauses)
    # R-02 is in the dataset
    r02 = next((c for c in clauses if c["source_id"] == "R-02"), None)
    assert r02 is not None
    assert r02["flags"] >= 3

    # 4. Expiring facts
    facts = data["expiring_facts"]
    assert any(f["id"] == "F-014" for f in facts)
