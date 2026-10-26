-- =====================================================================
-- BrandLens Seed Data: Fictional Brand "Lumina Skincare"
-- =====================================================================

DO $$
DECLARE
    org_uuid UUID := '00000000-0000-0000-0000-000000000001';
    guide_uuid UUID := '11111111-1111-1111-1111-111111111111';
    item_uuid UUID := '22222222-2222-2222-2222-222222222222';
    ver_uuid UUID := '33333333-3333-3333-3333-333333333333';
BEGIN
    -- 1. Organisation
    INSERT INTO organisations (id, name, slug)
    VALUES (org_uuid, 'Lumina Skincare', 'lumina-skincare')
    ON CONFLICT (id) DO NOTHING;

    -- 2. Profiles (All 4 roles)
    INSERT INTO profiles (id, user_id, org_id, email, full_name, role)
    VALUES 
        ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000101', org_uuid, 'creator@luminaskincare.com', 'Elena Vance (Creator)', 'creator'),
        ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000102', org_uuid, 'reviewer@luminaskincare.com', 'Marcus Brody (Reviewer)', 'reviewer'),
        ('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000103', org_uuid, 'manager@luminaskincare.com', 'Sarah Chen (Manager)', 'manager'),
        ('00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000104', org_uuid, 'admin@luminaskincare.com', 'Devin Archer (Admin)', 'admin')
    ON CONFLICT (id) DO NOTHING;

    -- 3. Guidelines
    INSERT INTO guidelines (id, org_id, title, version, description)
    VALUES (guide_uuid, org_uuid, 'Lumina Skincare Brand & Governance Guidelines 2026', '2.4', 'Official standards for claims, voice, visual identity, facts and accessibility.')
    ON CONFLICT (id) DO NOTHING;

    -- Clauses
    INSERT INTO clauses (id, guideline_id, category, title, text)
    VALUES
        ('C-01', guide_uuid, 'Claims', 'Claims Policy 3.2: Result Claims', 'Claims Policy 3.2: result claims need approved clinical evidence. Avoid guaranteed results unless substantiated by double-blind trials.'),
        ('C-02', guide_uuid, 'Claims', 'Claims Policy 3.4: Superlatives', 'Claims Policy 3.4: no superlatives (#1, best) without a cited ranking from a recognized industry source.'),
        ('C-03', guide_uuid, 'Claims', 'Claims Policy 3.6: Medical Claims', 'Claims Policy 3.6: no medical-cure language. Skincare products support, nourish, or care for skin, but do not cure dermatological conditions.'),
        ('R-02', guide_uuid, 'Tone', 'Voice Guide 2.1: Exclamation Marks', 'Voice Guide 2.1: at most one exclamation mark per post. Maintain an authoritative yet friendly tone.'),
        ('R-03', guide_uuid, 'Tone', 'Voice Guide 2.3: Shouting / ALL CAPS', 'Voice Guide 2.3: no shouting in ALL CAPS. Use title case or bold styling for emphasis instead.'),
        ('A-01', guide_uuid, 'Accessibility', 'Accessibility 1.1: Alt Text', 'Accessibility 1.1: images need descriptive alt text for assistive screen readers.'),
        ('A-02', guide_uuid, 'Accessibility', 'Accessibility 1.4: Color Contrast', 'Accessibility 1.4: text contrast against background must be at least 4.5:1 for WCAG AA compliance.'),
        ('A-03', guide_uuid, 'Accessibility', 'Accessibility 2.2: Sentence Length', 'Accessibility 2.2: keep sentences under 25 words to optimize readability for all users.'),
        ('V-01', guide_uuid, 'Visual', 'Visual Guide 1.2: Brand Palette', 'Visual Guide 1.2: use brand palette colours only (#1b2a49, #0f8b8d, #ffffff, #e8a33d).')
    ON CONFLICT (id) DO NOTHING;

    -- 4. Approved Facts
    INSERT INTO facts (id, org_id, label, value, source, owner, expires_on)
    VALUES
        ('F-014', org_uuid, 'Glow Serum Price', '1,199', 'Q4 2026 Price Sheet v2', 'Product Marketing', '2026-12-31'),
        ('F-015', org_uuid, 'Lumina Glow Active Ingredients', '10% Niacinamide + 2% Hyaluronic Acid', 'Lab Formulation Dossier v3.1', 'R&D Lab', '2027-06-30'),
        ('F-016', org_uuid, 'Cruelty Free Certification', 'Leaping Bunny Certified 2025-2027', 'Legal Reg #LB-9921', 'Legal Affairs', '2027-01-01')
    ON CONFLICT (id) DO NOTHING;

    -- 5. Approved Terms
    INSERT INTO terms (id, org_id, bad_term, preferred_term, note)
    VALUES
        ('T-01', org_uuid, 'cheap', 'affordable', 'Brand voice conveys premium accessibility rather than low cost.'),
        ('T-02', org_uuid, 'customers', 'members', 'Cultivate community feeling among our skincare club.'),
        ('T-03', org_uuid, 'miracle', 'clinically proven', 'Strictly avoid miraculous or pseudo-scientific claims.')
    ON CONFLICT (id) DO NOTHING;

    -- 6. Brand Assets
    INSERT INTO assets (id, org_id, name, type, palette)
    VALUES
        ('44444444-4444-4444-4444-444444444441', org_uuid, 'Lumina Master Palette', 'palette', '["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"]'::jsonb),
        ('44444444-4444-4444-4444-444444444442', org_uuid, 'Lumina Primary Wordmark', 'logo', '[]'::jsonb)
    ON CONFLICT (id) DO NOTHING;

    -- 7. Redaction Terms (Confidential Mode)
    INSERT INTO redaction_terms (org_id, term, replacement)
    VALUES
        (org_uuid, 'Project Radiance', '[CONFIDENTIAL_PROJECT_1]'),
        (org_uuid, 'Dr. Aris Thorne', '[CONFIDENTIAL_PARTNER_1]'),
        (org_uuid, '$4.2M', '[CONFIDENTIAL_FIGURE_1]')
    ON CONFLICT DO NOTHING;

    -- 8. Sample Content Item & Version (The Golden Sample)
    INSERT INTO content_items (id, org_id, title, type, channel, status, created_by)
    VALUES (item_uuid, org_uuid, 'Lumina Glow Serum Launch Post', 'Social post', 'Instagram', 'draft', 'Elena Vance')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO content_versions (id, content_item_id, n, text, created_by, note)
    VALUES (ver_uuid, item_uuid, 1, 'Get 100% guaranteed results with our #1 skincare serum! Cheap prices, only Rs 999 this week!! BUY NOW and LOVE it!', 'Elena Vance', 'Initial draft')
    ON CONFLICT (id) DO NOTHING;

    -- 9. Historical Audit Events (to seed the governance insights)
    INSERT INTO audit_log (org_id, content_item_id, actor, event, detail)
    VALUES
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "C-01"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "C-01"}'::jsonb),
        (org_uuid, item_uuid, 'Elena Vance', 'dismiss', '{"source_id": "C-01", "reason": "Authorized trial underway"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "T-01"}'::jsonb),
        (org_uuid, item_uuid, 'Elena Vance', 'accept', '{"source_id": "T-01"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "R-02"}'::jsonb),
        (org_uuid, item_uuid, 'Elena Vance', 'dismiss', '{"source_id": "R-02", "reason": "High enthusiasm campaign"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "R-02"}'::jsonb),
        (org_uuid, item_uuid, 'Elena Vance', 'dismiss', '{"source_id": "R-02", "reason": "Social media stylistic choice"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "F-014"}'::jsonb),
        (org_uuid, item_uuid, 'Elena Vance', 'accept', '{"source_id": "F-014"}'::jsonb),
        (org_uuid, item_uuid, 'System', 'flag', '{"source_id": "A-01"}'::jsonb);

END $$;
