-- Run this in Supabase SQL Editor
-- Go to: https://supabase.com/dashboard/project/oenvkdtfvoisyeeqbpqm/sql/new

DO $$
DECLARE
  v_tenant_id  UUID := 'a0000000-0000-0000-0000-000000000001';
  v_role_id    UUID;
BEGIN

  -- Teacher
  SELECT id INTO v_role_id FROM sis_role WHERE tenant_id = v_tenant_id AND name = 'Teacher';
  INSERT INTO sis_user (id, tenant_id, role_id, email, hashed_password, first_name, last_name, is_active)
  VALUES (gen_random_uuid(), v_tenant_id, v_role_id,
    'teacher@westlake.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uiom',
    'Jane', 'Smith', true)
  ON CONFLICT (email, tenant_id) DO NOTHING;

  -- Principal
  SELECT id INTO v_role_id FROM sis_role WHERE tenant_id = v_tenant_id AND name = 'Principal';
  INSERT INTO sis_user (id, tenant_id, role_id, email, hashed_password, first_name, last_name, is_active)
  VALUES (gen_random_uuid(), v_tenant_id, v_role_id,
    'principal@westlake.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uiom',
    'Robert', 'Johnson', true)
  ON CONFLICT (email, tenant_id) DO NOTHING;

  -- SpEdCoordinator
  SELECT id INTO v_role_id FROM sis_role WHERE tenant_id = v_tenant_id AND name = 'SpEdCoordinator';
  INSERT INTO sis_user (id, tenant_id, role_id, email, hashed_password, first_name, last_name, is_active)
  VALUES (gen_random_uuid(), v_tenant_id, v_role_id,
    'sped@westlake.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uiom',
    'Maria', 'Garcia', true)
  ON CONFLICT (email, tenant_id) DO NOTHING;

  -- Parent
  SELECT id INTO v_role_id FROM sis_role WHERE tenant_id = v_tenant_id AND name = 'Parent';
  INSERT INTO sis_user (id, tenant_id, role_id, email, hashed_password, first_name, last_name, is_active)
  VALUES (gen_random_uuid(), v_tenant_id, v_role_id,
    'parent@westlake.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uiom',
    'David', 'Lee', true)
  ON CONFLICT (email, tenant_id) DO NOTHING;

  -- DistrictAdmin
  SELECT id INTO v_role_id FROM sis_role WHERE tenant_id = v_tenant_id AND name = 'DistrictAdmin';
  INSERT INTO sis_user (id, tenant_id, role_id, email, hashed_password, first_name, last_name, is_active)
  VALUES (gen_random_uuid(), v_tenant_id, v_role_id,
    'district@westlake.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uiom',
    'Carol', 'White', true)
  ON CONFLICT (email, tenant_id) DO NOTHING;

  RAISE NOTICE 'Users seeded successfully.';
END $$;
