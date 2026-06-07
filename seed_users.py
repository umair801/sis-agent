"""
Seed additional test users for all 6 roles.
Run from: D:\aaa_AI_Agents\AgAI_30_AI_Student_Information_System
"""
import requests

BASE        = "http://localhost:8000/api/v1"
TENANT_SLUG = "westlake"

# Step 1: Login as SuperAdmin to get token
login = requests.post(f"{BASE}/auth/login", json={
    "email": "admin@westlake.edu",
    "password": "admin123",
    "tenant_slug": TENANT_SLUG,
})
assert login.status_code == 200, f"Login failed: {login.text}"
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"Logged in as SuperAdmin. Token acquired.\n")

# Step 2: Check existing users
users_res = requests.get(f"{BASE}/auth/users", headers=headers)
print(f"GET /auth/users => {users_res.status_code}")
if users_res.status_code == 200:
    existing = users_res.json()
    print(f"Existing users: {[u.get('email') for u in (existing if isinstance(existing, list) else existing.get('users', []))]}")
else:
    print(f"Response: {users_res.text[:300]}")

# Step 3: Try registration endpoint
test_users = [
    {"email": "teacher@westlake.edu",    "password": "teacher123",  "first_name": "Jane",   "last_name": "Smith",   "role": "Teacher"},
    {"email": "principal@westlake.edu",  "password": "principal123","first_name": "Robert", "last_name": "Johnson", "role": "Principal"},
    {"email": "sped@westlake.edu",       "password": "sped123",     "first_name": "Maria",  "last_name": "Garcia",  "role": "SpEdCoordinator"},
    {"email": "parent@westlake.edu",     "password": "parent123",   "first_name": "David",  "last_name": "Lee",     "role": "Parent"},
    {"email": "district@westlake.edu",   "password": "district123", "first_name": "Carol",  "last_name": "White",   "role": "DistrictAdmin"},
]

for u in test_users:
    payload = {**u, "tenant_slug": TENANT_SLUG}
    r = requests.post(f"{BASE}/auth/register", json=payload, headers=headers)
    print(f"Register {u['email']} => {r.status_code}: {r.text[:120]}")
