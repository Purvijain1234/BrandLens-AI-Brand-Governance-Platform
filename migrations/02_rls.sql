-- =====================================================================
-- BrandLens Row Level Security (RLS) Policies
-- Ensures users can only access data belonging to their organisation
-- =====================================================================

-- Helper to retrieve current user's organisation ID
CREATE OR REPLACE FUNCTION current_user_org_id()
RETURNS UUID AS $$
  SELECT org_id FROM profiles WHERE user_id = auth.uid() LIMIT 1;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Enable RLS on all tables
ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE guidelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE clauses ENABLE ROW LEVEL SECURITY;
ALTER TABLE facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE redaction_terms ENABLE ROW LEVEL SECURITY;

-- 1. ORGANISATIONS POLICIES
CREATE POLICY org_access ON organisations
    FOR ALL
    USING (id = current_user_org_id());

-- 2. PROFILES POLICIES
CREATE POLICY profile_access ON profiles
    FOR ALL
    USING (org_id = current_user_org_id());

-- 3. GUIDELINES & CLAUSES POLICIES
CREATE POLICY guidelines_access ON guidelines
    FOR ALL
    USING (org_id = current_user_org_id());

CREATE POLICY clauses_access ON clauses
    FOR ALL
    USING (guideline_id IN (SELECT id FROM guidelines WHERE org_id = current_user_org_id()));

-- 4. FACTS POLICIES
CREATE POLICY facts_access ON facts
    FOR ALL
    USING (org_id = current_user_org_id());

-- 5. TERMS POLICIES
CREATE POLICY terms_access ON terms
    FOR ALL
    USING (org_id = current_user_org_id());

-- 6. ASSETS POLICIES
CREATE POLICY assets_access ON assets
    FOR ALL
    USING (org_id = current_user_org_id());

-- 7. CONTENT & VERSIONS POLICIES
CREATE POLICY content_access ON content_items
    FOR ALL
    USING (org_id = current_user_org_id());

CREATE POLICY versions_access ON content_versions
    FOR ALL
    USING (content_item_id IN (SELECT id FROM content_items WHERE org_id = current_user_org_id()));

-- 8. FINDINGS POLICIES
CREATE POLICY findings_access ON findings
    FOR ALL
    USING (version_id IN (
        SELECT cv.id FROM content_versions cv
        JOIN content_items ci ON ci.id = cv.content_item_id
        WHERE ci.org_id = current_user_org_id()
    ));

-- 9. COMMENTS POLICIES
CREATE POLICY comments_access ON comments
    FOR ALL
    USING (content_item_id IN (SELECT id FROM content_items WHERE org_id = current_user_org_id()));

-- 10. AUDIT LOG POLICIES (Read-only for org members, append-only)
CREATE POLICY audit_read ON audit_log
    FOR SELECT
    USING (org_id = current_user_org_id());

CREATE POLICY audit_insert ON audit_log
    FOR INSERT
    WITH CHECK (org_id = current_user_org_id());

-- 11. AI CALLS POLICIES
CREATE POLICY ai_calls_access ON ai_calls
    FOR ALL
    USING (org_id = current_user_org_id());

-- 12. REDACTION TERMS POLICIES
CREATE POLICY redaction_access ON redaction_terms
    FOR ALL
    USING (org_id = current_user_org_id());
