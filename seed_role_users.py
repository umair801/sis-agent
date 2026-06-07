"""
Seed test users for all roles via Supabase REST API.
Reads credentials from backend/.env — no secrets hardcoded.
Run from project root with venv active:
  python seed_role_users.py
"""
import requests
import uuid
import sys
import os
import time

# Load from backend/.env — never hardcode secrets
env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
env_vars = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip()

SUPABASE_URL     = env_vars.get("SUPABASE_URL", "")
SERVICE_ROLE_KEY = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")
TENANT_ID        = "a0000000-0000-0000-0000-000000000001"

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing from backend/.env")
    sys.exit(1)

REST = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey":        SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_pw(pw): return pwd_context.hash(pw)
except ImportError:
    print("ERROR: passlib not installed. Run: pip install passlib bcrypt")
    sys.exit(1)

def api_get(path, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(f"{REST}/{path}", headers=headers, timeout=30)
            return r
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1} after error: {e}")
                time.sleep(2)
            else:
                raise

def api_post(path, payload, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"{REST}/{path}", json=payload, headers=headers, timeout=30)
            return r
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1} after error: {e}")
                time.sleep(2)
            else:
                raise

# Step 1: Fetch roles
print("Fetching roles...")
r = api_get(f"sis_role?tenant_id=eq.{TENANT_ID}&select=id,name")
if r.status_code != 200:
    print(f"Failed to fetch roles: {r.status_code} {r.text}")
    sys.exit(1)
role_map = {role["name"]: role["id"] for role in r.json()}
print(f"Found roles: {list(role_map.keys())}\n")

# Step 2: Users to create
TEST_USERS = [
    {"email": "teacher@westlake.edu",   "password": "teacher123",   "first_name": "Jane",   "last_name": "Smith",   "role": "Teacher"},
    {"email": "principal@westlake.edu", "password": "principal123", "first_name": "Robert", "last_name": "Johnson", "role": "Principal"},
    {"email": "sped@westlake.edu",      "password": "sped123",      "first_name": "Maria",  "last_name": "Garcia",  "role": "SpEdCoordinator"},
    {"email": "parent@westlake.edu",    "password": "parent123",    "first_name": "David",  "last_name": "Lee",     "role": "Parent"},
    {"email": "district@westlake.edu",  "password": "district123",  "first_name": "Carol",  "last_name": "White",   "role": "DistrictAdmin"},
]

# Step 3: Check existing
print("Checking existing users...")
existing_r = api_get(f"sis_user?tenant_id=eq.{TENANT_ID}&select=email")
existing_emails = {u["email"] for u in (existing_r.json() if existing_r.status_code == 200 else [])}

# Step 4: Insert
created = 0
skipped = 0

for u in TEST_USERS:
    if u["email"] in existing_emails:
        print(f"  SKIP   {u['email']} (already exists)")
        skipped += 1
        continue

    role_id = role_map.get(u["role"])
    if not role_id:
        print(f"  ERROR  {u['email']} — role '{u['role']}' not found")
        continue

    payload = {
        "id":              str(uuid.uuid4()),
        "tenant_id":       TENANT_ID,
        "role_id":         role_id,
        "email":           u["email"],
        "hashed_password": hash_pw(u["password"]),
        "first_name":      u["first_name"],
        "last_name":       u["last_name"],
        "is_active":       True,
    }

    ins = api_post("sis_user", payload)
    if ins.status_code in (200, 201):
        print(f"  CREATE {u['email']} ({u['role']})")
        created += 1
    else:
        print(f"  FAIL   {u['email']} => {ins.status_code}: {ins.text[:150]}")

print(f"\nDone: {created} created, {skipped} skipped.")
