from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
import re

from backend.app.core.security import get_current_user, require_roles, UserPayload
from backend.app.db.database import db

router = APIRouter(tags=["Knowledge Base"])

# --- Models ---
class FactCreate(BaseModel):
    id: Optional[str] = None
    label: str
    value: str
    source: str
    owner: str
    expires_on: Optional[str] = None

class FactUpdate(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None
    expires_on: Optional[str] = None

class TermCreate(BaseModel):
    id: Optional[str] = None
    bad_term: str
    preferred_term: str
    note: Optional[str] = None

class TermUpdate(BaseModel):
    bad_term: Optional[str] = None
    preferred_term: Optional[str] = None
    note: Optional[str] = None

class AssetCreate(BaseModel):
    name: str
    type: str  # 'palette' | 'logo' | 'badge'
    storage_path: Optional[str] = None
    palette: Optional[List[str]] = None

class RedactionTermCreate(BaseModel):
    term: str
    replacement: Optional[str] = None

class GuidelineImportText(BaseModel):
    title: str = "Imported Brand Guidelines"
    version: str = "1.0"
    description: Optional[str] = None
    content: str  # Plain text with numbered clauses or bullet points

# --- Guidelines & Clauses Endpoints ---
@router.get("/guidelines")
def get_guidelines(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM guidelines WHERE org_id = ?", (current_user.org_id,))
    guidelines = cur.fetchall()

    result = []
    for g in guidelines:
        cur.execute("SELECT * FROM clauses WHERE guideline_id = ?", (g["id"],))
        g_clauses = cur.fetchall()
        result.append({**g, "clauses": g_clauses})
    conn.close()
    return {"guidelines": result}

@router.get("/clauses")
def get_clauses(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, g.title as guideline_title 
        FROM clauses c
        JOIN guidelines g ON g.id = c.guideline_id
        WHERE g.org_id = ?
        ORDER BY c.id ASC
    """, (current_user.org_id,))
    clauses = cur.fetchall()
    conn.close()
    return {"clauses": clauses}

@router.post("/guidelines/import")
def import_guidelines(
    payload: GuidelineImportText,
    current_user: UserPayload = Depends(require_roles(["admin", "manager"]))
):
    conn = db.get_connection()
    cur = conn.cursor()

    guide_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO guidelines (id, org_id, title, version, description) VALUES (?, ?, ?, ?, ?)",
        (guide_id, current_user.org_id, payload.title, payload.version, payload.description)
    )

    # Split lines into distinct clauses
    lines = [line.strip() for line in payload.content.split("\n") if line.strip()]
    inserted_clauses = []
    idx = 1

    for line in lines:
        # Detect category and ID prefix if present
        clause_id = f"C-{idx:02d}"
        category = "Claims"

        # Check for explicit ID in line, e.g. "C-05:", "Tone 2.1:"
        match_id = re.match(r"^([A-Z]+-\d+)\s*[:.-]\s*(.+)", line)
        if match_id:
            clause_id = match_id.group(1)
            text = match_id.group(2)
        else:
            text = line

        if "voice" in text.lower() or "tone" in text.lower():
            category = "Tone"
        elif "access" in text.lower() or "contrast" in text.lower() or "alt" in text.lower():
            category = "Accessibility"
        elif "visual" in text.lower() or "color" in text.lower() or "palette" in text.lower():
            category = "Visual"

        cur.execute(
            "INSERT INTO clauses (id, guideline_id, category, title, text) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET text = excluded.text, category = excluded.category",
            (clause_id, guide_id, category, f"{category} Clause {clause_id}", text)
        )
        inserted_clauses.append({"id": clause_id, "category": category, "text": text})
        idx += 1

    conn.commit()
    conn.close()
    return {
        "status": "success",
        "guideline_id": guide_id,
        "imported_clauses_count": len(inserted_clauses),
        "clauses": inserted_clauses
    }

# --- Approved Facts Endpoints ---
@router.get("/facts")
def list_facts(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM facts WHERE org_id = ? ORDER BY id ASC", (current_user.org_id,))
    facts = cur.fetchall()
    conn.close()
    return {"facts": facts}

@router.post("/facts")
def create_fact(fact: FactCreate, current_user: UserPayload = Depends(require_roles(["admin", "manager"]))):
    conn = db.get_connection()
    cur = conn.cursor()

    fact_id = fact.id
    if not fact_id:
        cur.execute("SELECT COUNT(*) as c FROM facts WHERE org_id = ?", (current_user.org_id,))
        count = cur.fetchone()["c"] + 1
        fact_id = f"F-{count:03d}"

    cur.execute(
        "INSERT INTO facts (id, org_id, label, value, source, owner, expires_on) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fact_id, current_user.org_id, fact.label, fact.value, fact.source, fact.owner, fact.expires_on)
    )
    conn.commit()
    conn.close()
    return {"status": "created", "fact_id": fact_id}

@router.put("/facts/{fact_id}")
def update_fact(fact_id: str, fact: FactUpdate, current_user: UserPayload = Depends(require_roles(["admin", "manager"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM facts WHERE id = ? AND org_id = ?", (fact_id, current_user.org_id))
    existing = cur.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Fact not found")

    new_label = fact.label if fact.label is not None else existing["label"]
    new_value = fact.value if fact.value is not None else existing["value"]
    new_source = fact.source if fact.source is not None else existing["source"]
    new_owner = fact.owner if fact.owner is not None else existing["owner"]
    new_expires = fact.expires_on if fact.expires_on is not None else existing["expires_on"]

    cur.execute(
        "UPDATE facts SET label = ?, value = ?, source = ?, owner = ?, expires_on = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND org_id = ?",
        (new_label, new_value, new_source, new_owner, new_expires, fact_id, current_user.org_id)
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "fact_id": fact_id}

@router.delete("/facts/{fact_id}")
def delete_fact(fact_id: str, current_user: UserPayload = Depends(require_roles(["admin"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM facts WHERE id = ? AND org_id = ?", (fact_id, current_user.org_id))
    conn.commit()
    conn.close()
    return {"status": "deleted", "fact_id": fact_id}

# --- Approved Terms Endpoints ---
@router.get("/terms")
def list_terms(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM terms WHERE org_id = ? ORDER BY id ASC", (current_user.org_id,))
    terms = cur.fetchall()
    conn.close()
    return {"terms": terms}

@router.post("/terms")
def create_term(term: TermCreate, current_user: UserPayload = Depends(require_roles(["admin", "manager"]))):
    conn = db.get_connection()
    cur = conn.cursor()

    term_id = term.id
    if not term_id:
        cur.execute("SELECT COUNT(*) as c FROM terms WHERE org_id = ?", (current_user.org_id,))
        count = cur.fetchone()["c"] + 1
        term_id = f"T-{count:02d}"

    cur.execute(
        "INSERT INTO terms (id, org_id, bad_term, preferred_term, note) VALUES (?, ?, ?, ?, ?)",
        (term_id, current_user.org_id, term.bad_term, term.preferred_term, term.note or "")
    )
    conn.commit()
    conn.close()
    return {"status": "created", "term_id": term_id}

@router.delete("/terms/{term_id}")
def delete_term(term_id: str, current_user: UserPayload = Depends(require_roles(["admin"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM terms WHERE id = ? AND org_id = ?", (term_id, current_user.org_id))
    conn.commit()
    conn.close()
    return {"status": "deleted", "term_id": term_id}

# --- Assets Endpoints ---
@router.get("/assets")
def list_assets(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM assets WHERE org_id = ? ORDER BY name ASC", (current_user.org_id,))
    raw_assets = cur.fetchall()
    assets = []
    for a in raw_assets:
        palette = json.loads(a["palette_json"]) if a.get("palette_json") else []
        assets.append({**a, "palette": palette})
    conn.close()
    return {"assets": assets}

@router.post("/assets")
def create_asset(asset: AssetCreate, current_user: UserPayload = Depends(require_roles(["admin"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    asset_id = str(uuid.uuid4())
    palette_json = json.dumps(asset.palette) if asset.palette else json.dumps([])

    cur.execute(
        "INSERT INTO assets (id, org_id, name, type, storage_path, palette_json) VALUES (?, ?, ?, ?, ?, ?)",
        (asset_id, current_user.org_id, asset.name, asset.type, asset.storage_path, palette_json)
    )
    conn.commit()
    conn.close()
    return {"status": "created", "asset_id": asset_id}

# --- Redaction Terms Endpoints ---
@router.get("/redaction-terms")
def list_redaction_terms(current_user: UserPayload = Depends(get_current_user)):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM redaction_terms WHERE org_id = ? ORDER BY created_at ASC", (current_user.org_id,))
    terms = cur.fetchall()
    conn.close()
    return {"redaction_terms": terms}

@router.post("/redaction-terms")
def create_redaction_term(term: RedactionTermCreate, current_user: UserPayload = Depends(require_roles(["admin"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    term_id = str(uuid.uuid4())
    replacement = term.replacement or f"[CONFIDENTIAL_{uuid.uuid4().hex[:6].upper()}]"

    cur.execute(
        "INSERT INTO redaction_terms (id, org_id, term, replacement) VALUES (?, ?, ?, ?)",
        (term_id, current_user.org_id, term.term, replacement)
    )
    conn.commit()
    conn.close()
    return {"status": "created", "term_id": term_id, "replacement": replacement}

@router.delete("/redaction-terms/{term_id}")
def delete_redaction_term(term_id: str, current_user: UserPayload = Depends(require_roles(["admin"]))):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM redaction_terms WHERE id = ? AND org_id = ?", (term_id, current_user.org_id))
    conn.commit()
    conn.close()
    return {"status": "deleted", "term_id": term_id}
