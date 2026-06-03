-- ============================================================
-- SIS Multi-Tenant Schema
-- Datawebify | sis.datawebify.com
-- All tables prefixed with sis_
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. TENANTS
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_tenant (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    domain          TEXT,
    logo_url        TEXT,
    primary_color   TEXT DEFAULT '#1a56db',
    grading_scale   JSONB DEFAULT '{"A": 90, "B": 80, "C": 70, "D": 60}',
    timezone        TEXT DEFAULT 'America/Los_Angeles',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 2. ROLES
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_role (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    permissions JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

-- ============================================================
-- 3. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_user (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES sis_role(id),
    email           TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    phone           TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);

-- ============================================================
-- 4. REFRESH TOKENS
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_refresh_token (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES sis_user(id) ON DELETE CASCADE,
    tenant_id   UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    token       TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. AUDIT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES sis_user(id),
    action      TEXT NOT NULL,
    table_name  TEXT,
    record_id   UUID,
    old_data    JSONB,
    new_data    JSONB,
    ip_address  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_sis_user_tenant     ON sis_user(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sis_user_email      ON sis_user(email);
CREATE INDEX IF NOT EXISTS idx_sis_role_tenant     ON sis_role(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sis_audit_tenant    ON sis_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sis_audit_user      ON sis_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_sis_refresh_user    ON sis_refresh_token(user_id);

-- ============================================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sis_tenant_updated
    BEFORE UPDATE ON sis_tenant
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_sis_user_updated
    BEFORE UPDATE ON sis_user
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE sis_tenant          ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_role            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_user            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_refresh_token   ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_audit_log       ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS (used by backend)
CREATE POLICY "service_role_bypass_tenant"
    ON sis_tenant FOR ALL TO service_role USING (TRUE);

CREATE POLICY "service_role_bypass_role"
    ON sis_role FOR ALL TO service_role USING (TRUE);

CREATE POLICY "service_role_bypass_user"
    ON sis_user FOR ALL TO service_role USING (TRUE);

CREATE POLICY "service_role_bypass_refresh_token"
    ON sis_refresh_token FOR ALL TO service_role USING (TRUE);

CREATE POLICY "service_role_bypass_audit"
    ON sis_audit_log FOR ALL TO service_role USING (TRUE);

-- ============================================================
-- SEED: Default tenant + roles for Westlake Unified
-- ============================================================
INSERT INTO sis_tenant (id, name, slug, domain)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Westlake Unified School District',
    'westlake',
    'westlake.sis.datawebify.com'
) ON CONFLICT (slug) DO NOTHING;

INSERT INTO sis_role (tenant_id, name, permissions) VALUES
('a0000000-0000-0000-0000-000000000001', 'SuperAdmin',        '{"all": true}'),
('a0000000-0000-0000-0000-000000000001', 'DistrictAdmin',     '{"students": true, "reports": true, "budget": true, "scheduling": true}'),
('a0000000-0000-0000-0000-000000000001', 'Principal',         '{"students": true, "reports": true, "scheduling": true}'),
('a0000000-0000-0000-0000-000000000001', 'Teacher',           '{"attendance": true, "gradebook": true}'),
('a0000000-0000-0000-0000-000000000001', 'SpEdCoordinator',   '{"sped": true, "students": true}'),
('a0000000-0000-0000-0000-000000000001', 'Parent',            '{"own_children": true}')
ON CONFLICT (tenant_id, name) DO NOTHING;
