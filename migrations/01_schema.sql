-- =====================================================================
-- BrandLens Database Schema Migration
-- Compatible with PostgreSQL + pgvector (Supabase)
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. ORGANISATIONS
CREATE TABLE IF NOT EXISTS organisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. USER PROFILES
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- references auth.users(id) in Supabase
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('creator', 'reviewer', 'manager', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_profiles_org ON profiles(org_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);

-- 3. GUIDELINES & CLAUSES
CREATE TABLE IF NOT EXISTS guidelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_guidelines_org ON guidelines(org_id);

CREATE TABLE IF NOT EXISTS clauses (
    id TEXT PRIMARY KEY, -- e.g. "C-01", "C-02", "R-02", "A-01", "V-01"
    guideline_id UUID NOT NULL REFERENCES guidelines(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- e.g. 'Claims', 'Tone', 'Accessibility', 'Visual'
    title TEXT,
    text TEXT NOT NULL,
    embedding vector(768), -- Embedding vector for semantic retrieval
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_clauses_guideline ON clauses(guideline_id);

-- 4. APPROVED FACTS
CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY, -- e.g. "F-014"
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT NOT NULL,
    owner TEXT NOT NULL,
    expires_on DATE,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_facts_org ON facts(org_id);

-- 5. APPROVED TERMINOLOGY
CREATE TABLE IF NOT EXISTS terms (
    id TEXT PRIMARY KEY, -- e.g. "T-01"
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    bad_term TEXT NOT NULL,
    preferred_term TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_terms_org ON terms(org_id);

-- 6. BRAND ASSETS
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'palette', 'logo', 'badge'
    storage_path TEXT,
    palette JSONB, -- Array of hex colours e.g. ["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_assets_org ON assets(org_id);

-- 7. CONTENT ITEMS & VERSIONS
CREATE TABLE IF NOT EXISTS content_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    type TEXT NOT NULL, -- 'Social post', 'Press release', 'Ad copy', 'Blog'
    channel TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_review', 'changes_requested', 'approved')),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_org ON content_items(org_id);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_items(status);

CREATE TABLE IF NOT EXISTS content_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    n INT NOT NULL,
    text TEXT NOT NULL,
    file_path TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_versions_content ON content_versions(content_item_id);

-- 8. FINDINGS
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES content_versions(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'med', 'low')),
    confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
    span_start INT NOT NULL DEFAULT 0,
    span_end INT NOT NULL DEFAULT 0,
    quoted_text TEXT NOT NULL,
    message TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('clause', 'fact', 'term', 'asset')),
    source_id TEXT NOT NULL,
    suggested_fix TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('rule', 'ai')),
    state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'accepted', 'dismissed', 'needs_human')),
    decision_reason TEXT,
    decided_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_findings_version ON findings(version_id);
CREATE INDEX IF NOT EXISTS idx_findings_state ON findings(state);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);

-- 9. COMMENTS
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
    user_id TEXT NOT NULL,
    user_name TEXT,
    user_role TEXT,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_comments_content ON comments(content_item_id);

-- 10. AUDIT LOG (Immutable)
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    actor TEXT NOT NULL,
    event TEXT NOT NULL,
    detail JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org_id);
CREATE INDEX IF NOT EXISTS idx_audit_content ON audit_log(content_item_id);

-- 11. AI DISCLOSURE CALLS LEDGER
CREATE TABLE IF NOT EXISTS ai_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    redacted BOOLEAN NOT NULL DEFAULT FALSE,
    prompt_tokens INT,
    completion_tokens INT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_calls_org ON ai_calls(org_id);
CREATE INDEX IF NOT EXISTS idx_ai_calls_content ON ai_calls(content_item_id);

-- 12. REDACTION TERMS (Confidential Mode)
CREATE TABLE IF NOT EXISTS redaction_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    term TEXT NOT NULL,
    replacement TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_redaction_org ON redaction_terms(org_id);
