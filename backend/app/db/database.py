import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.app.core.config import settings

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class LocalDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = dict_factory
        return conn

    def init_db(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # Tables
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS organisations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            org_id TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guidelines (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            title TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clauses (
            id TEXT PRIMARY KEY,
            guideline_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT,
            text TEXT NOT NULL,
            embedding_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            label TEXT NOT NULL,
            value TEXT NOT NULL,
            source TEXT NOT NULL,
            owner TEXT NOT NULL,
            expires_on TEXT,
            embedding_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS terms (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            bad_term TEXT NOT NULL,
            preferred_term TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            storage_path TEXT,
            palette_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS content_items (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            channel TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS content_versions (
            id TEXT PRIMARY KEY,
            content_item_id TEXT NOT NULL,
            n INTEGER NOT NULL,
            text TEXT NOT NULL,
            file_path TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            version_id TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence TEXT NOT NULL,
            span_start INTEGER NOT NULL DEFAULT 0,
            span_end INTEGER NOT NULL DEFAULT 0,
            quoted_text TEXT NOT NULL,
            message TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            suggested_fix TEXT,
            origin TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'open',
            decision_reason TEXT,
            decided_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            content_item_id TEXT NOT NULL,
            finding_id TEXT,
            user_id TEXT NOT NULL,
            user_name TEXT,
            user_role TEXT,
            body TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            content_item_id TEXT,
            actor TEXT NOT NULL,
            event TEXT NOT NULL,
            detail_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_calls (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            content_item_id TEXT,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            redacted INTEGER NOT NULL DEFAULT 0,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            duration_ms INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS redaction_terms (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            term TEXT NOT NULL,
            replacement TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

        # Check if seed data exists; if not, seed Lumina Skincare
        cur.execute("SELECT COUNT(*) as count FROM organisations")
        if cur.fetchone()["count"] == 0:
            self.seed_lumina_skincare(conn)
        conn.close()

    def seed_lumina_skincare(self, conn):
        cur = conn.cursor()
        org_id = "00000000-0000-0000-0000-000000000001"
        guide_id = "11111111-1111-1111-1111-111111111111"
        item_id = "22222222-2222-2222-2222-222222222222"
        ver_id = "33333333-3333-3333-3333-333333333333"

        # Organisation
        cur.execute(
            "INSERT INTO organisations (id, name, slug) VALUES (?, ?, ?)",
            (org_id, "Lumina Skincare", "lumina-skincare")
        )

        # Profiles
        profiles = [
            ("00000000-0000-0000-0000-000000000101", "00000000-0000-0000-0000-000000000101", org_id, "creator@luminaskincare.com", "Elena Vance (Creator)", "creator"),
            ("00000000-0000-0000-0000-000000000102", "00000000-0000-0000-0000-000000000102", org_id, "reviewer@luminaskincare.com", "Marcus Brody (Reviewer)", "reviewer"),
            ("00000000-0000-0000-0000-000000000103", "00000000-0000-0000-0000-000000000103", org_id, "manager@luminaskincare.com", "Sarah Chen (Manager)", "manager"),
            ("00000000-0000-0000-0000-000000000104", "00000000-0000-0000-0000-000000000104", org_id, "admin@luminaskincare.com", "Devin Archer (Admin)", "admin"),
        ]
        cur.executemany("INSERT INTO profiles (id, user_id, org_id, email, full_name, role) VALUES (?, ?, ?, ?, ?, ?)", profiles)

        # Guidelines & Clauses
        cur.execute(
            "INSERT INTO guidelines (id, org_id, title, version, description) VALUES (?, ?, ?, ?, ?)",
            (guide_id, org_id, "Lumina Skincare Brand & Governance Guidelines 2026", "2.4", "Official standards for claims, voice, visual identity, facts and accessibility.")
        )

        clauses = [
            ("C-01", guide_id, "Claims", "Claims Policy 3.2: Result Claims", "Claims Policy 3.2: result claims need approved evidence. Avoid guaranteed results unless substantiated by double-blind trials."),
            ("C-02", guide_id, "Claims", "Claims Policy 3.4: Superlatives", "Claims Policy 3.4: no superlatives (#1, best) without a cited ranking from a recognized industry source."),
            ("C-03", guide_id, "Claims", "Claims Policy 3.6: Medical Claims", "Claims Policy 3.6: no medical-cure language. Skincare products support, nourish, or care for skin, but do not cure dermatological conditions."),
            ("R-02", guide_id, "Tone", "Voice Guide 2.1: Exclamation Marks", "Voice Guide 2.1: at most one exclamation mark per post. Maintain an authoritative yet friendly tone."),
            ("R-03", guide_id, "Tone", "Voice Guide 2.3: Shouting / ALL CAPS", "Voice Guide 2.3: no shouting in ALL CAPS. Use title case or bold styling for emphasis instead."),
            ("A-01", guide_id, "Accessibility", "Accessibility 1.1: Alt Text", "Accessibility 1.1: images need descriptive alt text for assistive screen readers."),
            ("A-02", guide_id, "Accessibility", "Accessibility 1.4: Color Contrast", "Accessibility 1.4: text contrast against background must be at least 4.5:1 for WCAG AA compliance."),
            ("A-03", guide_id, "Accessibility", "Accessibility 2.2: Sentence Length", "Accessibility 2.2: keep sentences under 25 words to optimize readability for all users."),
            ("V-01", guide_id, "Visual", "Visual Guide 1.2: Brand Palette", "Visual Guide 1.2: use brand palette colours only (#1b2a49, #0f8b8d, #ffffff, #e8a33d)."),
        ]
        cur.executemany("INSERT INTO clauses (id, guideline_id, category, title, text) VALUES (?, ?, ?, ?, ?)", clauses)

        # Facts
        facts = [
            ("F-014", org_id, "Glow Serum Price", "1,199", "Q4 2026 Price Sheet v2", "Product Marketing", "2026-12-31"),
            ("F-015", org_id, "Lumina Glow Active Ingredients", "10% Niacinamide + 2% Hyaluronic Acid", "Lab Formulation Dossier v3.1", "R&D Lab", "2027-06-30"),
            ("F-016", org_id, "Cruelty Free Certification", "Leaping Bunny Certified 2025-2027", "Legal Reg #LB-9921", "Legal Affairs", "2027-01-01"),
        ]
        cur.executemany("INSERT INTO facts (id, org_id, label, value, source, owner, expires_on) VALUES (?, ?, ?, ?, ?, ?, ?)", facts)

        # Terms
        terms = [
            ("T-01", org_id, "cheap", "affordable", "Brand voice conveys premium accessibility rather than low cost."),
            ("T-02", org_id, "customers", "members", "Cultivate community feeling among our skincare club."),
            ("T-03", org_id, "miracle", "clinically proven", "Strictly avoid miraculous or pseudo-scientific claims."),
        ]
        cur.executemany("INSERT INTO terms (id, org_id, bad_term, preferred_term, note) VALUES (?, ?, ?, ?, ?)", terms)

        # Assets
        assets = [
            ("44444444-4444-4444-4444-444444444441", org_id, "Lumina Master Palette", "palette", None, json.dumps(["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"])),
            ("44444444-4444-4444-4444-444444444442", org_id, "Lumina Primary Wordmark", "logo", "/assets/lumina-logo.svg", json.dumps([])),
        ]
        cur.executemany("INSERT INTO assets (id, org_id, name, type, storage_path, palette_json) VALUES (?, ?, ?, ?, ?, ?)", assets)

        # Redaction Terms
        redaction = [
            ("55555555-5555-5555-5555-555555555551", org_id, "Project Radiance", "[CONFIDENTIAL_PROJECT_1]"),
            ("55555555-5555-5555-5555-555555555552", org_id, "Dr. Aris Thorne", "[CONFIDENTIAL_PARTNER_1]"),
            ("55555555-5555-5555-5555-555555555553", org_id, "$4.2M", "[CONFIDENTIAL_FIGURE_1]"),
        ]
        cur.executemany("INSERT INTO redaction_terms (id, org_id, term, replacement) VALUES (?, ?, ?, ?)", redaction)

        # Sample Item & Version
        cur.execute(
            "INSERT INTO content_items (id, org_id, title, type, channel, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item_id, org_id, "Lumina Glow Serum Launch Post", "Social post", "Instagram", "draft", "Elena Vance")
        )
        cur.execute(
            "INSERT INTO content_versions (id, content_item_id, n, text, created_by, note) VALUES (?, ?, ?, ?, ?, ?)",
            (ver_id, item_id, 1, "Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!", "Elena Vance", "Initial draft")
        )

        # Seed audit log events for governance insights
        audit_events = [
            ("66666666-6666-6666-6666-666666666001", org_id, item_id, "System", "flag", json.dumps({"source_id": "C-01"})),
            ("66666666-6666-6666-6666-666666666002", org_id, item_id, "System", "flag", json.dumps({"source_id": "C-01"})),
            ("66666666-6666-6666-6666-666666666003", org_id, item_id, "Elena Vance", "dismiss", json.dumps({"source_id": "C-01", "reason": "Authorized trial underway"})),
            ("66666666-6666-6666-6666-666666666004", org_id, item_id, "System", "flag", json.dumps({"source_id": "T-01"})),
            ("66666666-6666-6666-6666-666666666005", org_id, item_id, "Elena Vance", "accept", json.dumps({"source_id": "T-01"})),
            ("66666666-6666-6666-6666-666666666006", org_id, item_id, "System", "flag", json.dumps({"source_id": "R-02"})),
            ("66666666-6666-6666-6666-666666666007", org_id, item_id, "Elena Vance", "dismiss", json.dumps({"source_id": "R-02", "reason": "High enthusiasm campaign"})),
            ("66666666-6666-6666-6666-666666666008", org_id, item_id, "System", "flag", json.dumps({"source_id": "R-02"})),
            ("66666666-6666-6666-6666-666666666009", org_id, item_id, "Elena Vance", "dismiss", json.dumps({"source_id": "R-02", "reason": "Social media stylistic choice"})),
            ("66666666-6666-6666-6666-666666666010", org_id, item_id, "System", "flag", json.dumps({"source_id": "F-014"})),
            ("66666666-6666-6666-6666-666666666011", org_id, item_id, "Elena Vance", "accept", json.dumps({"source_id": "F-014"})),
            ("66666666-6666-6666-6666-666666666012", org_id, item_id, "System", "flag", json.dumps({"source_id": "A-01"})),
        ]
        cur.executemany("INSERT INTO audit_log (id, org_id, content_item_id, actor, event, detail_json) VALUES (?, ?, ?, ?, ?, ?)", audit_events)

        conn.commit()

# Global database instance
db = LocalDatabase()

def get_db():
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()
