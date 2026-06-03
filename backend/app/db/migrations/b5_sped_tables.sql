-- ============================================================
-- B5 Migration: SpEd / IEP Tables
-- Datawebify | sis.datawebify.com
-- Run this in Supabase SQL Editor
-- ============================================================

-- Enum types (PostgreSQL native enums)
DO $$ BEGIN
    CREATE TYPE sis_iep_status AS ENUM ('draft','active','expired','revoked');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_disability_category AS ENUM (
        'autism','deaf_blindness','deafness','developmental_delay',
        'emotional_disturbance','hearing_impairment','intellectual_disability',
        'multiple_disabilities','orthopedic_impairment','other_health_impairment',
        'specific_learning_disability','speech_language_impairment',
        'traumatic_brain_injury','visual_impairment'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_service_type AS ENUM (
        'special_education','speech_language','occupational_therapy',
        'physical_therapy','counseling','transportation',
        'assistive_technology','other'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_service_frequency AS ENUM (
        'daily','weekly','biweekly','monthly','as_needed'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_goal_status AS ENUM (
        'not_started','in_progress','achieved','not_achieved','discontinued'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_goal_domain AS ENUM (
        'academic','communication','social_emotional','behavioral',
        'adaptive','motor','transition','other'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_accommodation_type AS ENUM (
        'presentation','response','setting','timing_scheduling','other'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_team_member_role AS ENUM (
        'sped_coordinator','general_ed_teacher','special_ed_teacher',
        'parent_guardian','student','administrator','psychologist',
        'speech_therapist','ot','pt','counselor','other'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sis_meeting_type AS ENUM (
        'initial','annual','triennial','amendment','transition','other'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ============================================================
-- 1. sis_iep  (master IEP record)
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id                       UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    student_id                      UUID NOT NULL REFERENCES sis_student(id) ON DELETE CASCADE,
    iep_number                      VARCHAR(50),
    status                          sis_iep_status NOT NULL DEFAULT 'draft',
    disability_category             sis_disability_category NOT NULL,
    secondary_disability            sis_disability_category,
    eligibility_date                DATE NOT NULL,
    start_date                      DATE NOT NULL,
    end_date                        DATE NOT NULL,
    next_review_date                DATE NOT NULL,
    triennial_date                  DATE,
    least_restrictive_environment   TEXT,
    placement_percentage_general_ed NUMERIC(5,2),
    present_levels                  TEXT,
    transition_plan                 TEXT,
    extended_school_year            BOOLEAN NOT NULL DEFAULT FALSE,
    notes                           TEXT,
    created_by                      UUID REFERENCES sis_user(id),
    updated_by                      UUID REFERENCES sis_user(id),
    created_at                      TIMESTAMPTZ DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_tenant_student  ON sis_iep(tenant_id, student_id);
CREATE INDEX IF NOT EXISTS ix_sis_iep_status          ON sis_iep(status);
CREATE INDEX IF NOT EXISTS ix_sis_iep_next_review     ON sis_iep(next_review_date);


-- ============================================================
-- 2. sis_iep_service
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_service (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    iep_id                  UUID NOT NULL REFERENCES sis_iep(id) ON DELETE CASCADE,
    service_type            sis_service_type NOT NULL,
    provider_name           VARCHAR(200),
    minutes_per_session     INTEGER NOT NULL,
    sessions_per_frequency  INTEGER NOT NULL DEFAULT 1,
    frequency               sis_service_frequency NOT NULL,
    start_date              DATE NOT NULL,
    end_date                DATE NOT NULL,
    location                VARCHAR(200),
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_service_iep ON sis_iep_service(iep_id);


-- ============================================================
-- 3. sis_iep_goal
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_goal (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    iep_id              UUID NOT NULL REFERENCES sis_iep(id) ON DELETE CASCADE,
    domain              sis_goal_domain NOT NULL,
    goal_text           TEXT NOT NULL,
    baseline            TEXT,
    target_criteria     TEXT,
    measurement_method  TEXT,
    reporting_frequency sis_service_frequency,
    status              sis_goal_status NOT NULL DEFAULT 'not_started',
    sequence            INTEGER NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_goal_iep ON sis_iep_goal(iep_id);


-- ============================================================
-- 4. sis_iep_goal_progress
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_goal_progress (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    goal_id             UUID NOT NULL REFERENCES sis_iep_goal(id) ON DELETE CASCADE,
    recorded_by         UUID REFERENCES sis_user(id),
    progress_date       DATE NOT NULL,
    progress_note       TEXT NOT NULL,
    mastery_percentage  NUMERIC(5,2),
    status              sis_goal_status NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_goal_progress_goal ON sis_iep_goal_progress(goal_id);


-- ============================================================
-- 5. sis_iep_accommodation
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_accommodation (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    iep_id                  UUID NOT NULL REFERENCES sis_iep(id) ON DELETE CASCADE,
    accommodation_type      sis_accommodation_type NOT NULL,
    description             TEXT NOT NULL,
    applies_to_assessment   BOOLEAN NOT NULL DEFAULT FALSE,
    applies_to_instruction  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_accommodation_iep ON sis_iep_accommodation(iep_id);


-- ============================================================
-- 6. sis_iep_team_member
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_team_member (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    iep_id              UUID NOT NULL REFERENCES sis_iep(id) ON DELETE CASCADE,
    role                sis_team_member_role NOT NULL,
    name                VARCHAR(200) NOT NULL,
    email               VARCHAR(255),
    phone               VARCHAR(50),
    user_id             UUID REFERENCES sis_user(id),
    signature_obtained  BOOLEAN NOT NULL DEFAULT FALSE,
    signature_date      DATE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_sis_iep_team_user UNIQUE (iep_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_team_iep ON sis_iep_team_member(iep_id);


-- ============================================================
-- 7. sis_iep_meeting
-- ============================================================
CREATE TABLE IF NOT EXISTS sis_iep_meeting (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES sis_tenant(id) ON DELETE CASCADE,
    iep_id          UUID NOT NULL REFERENCES sis_iep(id) ON DELETE CASCADE,
    scheduled_by    UUID REFERENCES sis_user(id),
    meeting_type    sis_meeting_type NOT NULL,
    scheduled_date  TIMESTAMPTZ NOT NULL,
    actual_date     TIMESTAMPTZ,
    location        VARCHAR(200),
    attendees       TEXT,
    minutes         TEXT,
    outcome         TEXT,
    next_steps      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sis_iep_meeting_iep  ON sis_iep_meeting(iep_id);
CREATE INDEX IF NOT EXISTS ix_sis_iep_meeting_date ON sis_iep_meeting(scheduled_date);


-- ============================================================
-- Row Level Security
-- ============================================================
ALTER TABLE sis_iep               ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_service       ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_goal          ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_goal_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_accommodation ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_team_member   ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis_iep_meeting       ENABLE ROW LEVEL SECURITY;

-- Service role bypass (FastAPI backend uses service role key)
CREATE POLICY sis_iep_service_role               ON sis_iep               FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_service_service_role       ON sis_iep_service       FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_goal_service_role          ON sis_iep_goal          FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_goal_prog_service_role     ON sis_iep_goal_progress FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_accommodation_service_role ON sis_iep_accommodation FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_team_service_role          ON sis_iep_team_member   FOR ALL TO service_role USING (true);
CREATE POLICY sis_iep_meeting_service_role       ON sis_iep_meeting       FOR ALL TO service_role USING (true);
