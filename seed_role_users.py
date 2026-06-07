"""
Seed test users for all roles via Supabase REST API.
Run from project root with venv active:
  python seed_role_users.py
"""
import requests
import uuid
import sys

SUPABASE_URL      = "https://oenvkdtfvoisyeeqbpqm.supabase.co"
SERVICE_ROLE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9lbnZrZHRmdm9pc3llZXFicHFtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDM3OTA3NSwiZXhwIjoyMDg5OTU1MDc1fQ.-7626TKqEqEvW_WSUZCHpSx_192mXjyJdSmF8C-Bbs8"
TENANT_ID         = "a0000000-0000-0000-0000-000000000001"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

REST = f"{SUPABASE_URL}/rest/v1"

# ── Hash passwords using bcrypt (same as backend) ──────────────────────────
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_pw(pw): return pwd_context.hash(pw)
except ImportError:
    print("ERROR: passlib not installed. Run: pip install passlib bcrypt")
    sys.exit(1)

# ── Step 1: Fetch roles for this tenant ───────────────────────────────────
print("Fetching roles...")
r = requests.get(
    f"{REST}/sis_role?tenant_id=eq.{TENANT_ID}&select=id,name",
    headers=headers
)
if r.status_code != 200:
    print(f"Failed to fetch roles: {r.status_code} {r.text}")
    sys.exit(1)

roles = r.json()
role_map = {role["name"]: role["id"] for role in roles}
print(f"Found roles: {list(role_map.keys())}\n")

# ── Step 2: Users to create ───────────────────────────────────────────────
TEST_USERS = [
    {"email": "teacher@westlake.edu",   "password": "teacher123",   "first_name": "Jane",   "last_name": "Smith",   "role": "Teacher"},
    {"email": "principal@westlake.edu", "password": "principal123", "first_name": "Robert", "last_name": "Johnson", "role": "Principal"},
    {"email": "sped@westlake.edu",      "password": "sped123",      "first_name": "Maria",  "last_name": "Garcia",  "role": "SpEdCoordinator"},
    {"email": "parent@westlake.edu",    "password": "parent123",    "first_name": "David",  "last_name": "Lee",     "role": "Parent"},
    {"email": "district@westlake.edu",  "password": "district123",  "first_name": "Carol",  "last_name": "White",   "role": "DistrictAdmin"},
]

# ── Step 3: Check existing users ──────────────────────────────────────────
existing_r = requests.get(
    f"{REST}/sis_user?tenant_id=eq.{TENANT_ID}&select=email",
    headers=headers
)
existing_emails = {u["email"] for u in (existing_r.json() if existing_r.status_code == 200 else [])}

# ── Step 4: Insert each user ──────────────────────────────────────────────
created = 0
skipped = 0

for u in TEST_USERS:
    if u["email"] in existing_emails:
        print(f"  SKIP   {u['email']} (already exists)")
        skipped += 1
        continue

    role_id = role_map.get(u["role"])
    if not role_id:
        print(f"  ERROR  {u['email']} — role '{u['role']}' not in DB. Available: {list(role_map.keys())}")
        continue

    payload = {
        "id":               str(uuid.uuid4()),
        "tenant_id":        TENANT_ID,
        "role_id":          role_id,
        "email":            u["email"],
        "hashed_password":  hash_pw(u["password"]),
        "first_name":       u["first_name"],
        "last_name":        u["last_name"],
        "is_active":        True,
    }

    ins = requests.post(f"{REST}/sis_user", json=payload, headers=headers)
    if ins.status_code in (200, 201):
        print(f"  CREATE {u['email']} ({u['role']})")
        created += 1
    else:
        print(f"  FAIL   {u['email']} => {ins.status_code}: {ins.text[:150]}")

print(f"\nDone: {created} created, {skipped} skipped.")
