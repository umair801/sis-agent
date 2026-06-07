import requests

BASE = "http://localhost:8000/api/v1"

USERS = [
    ("admin@westlake.edu",    "admin123",    "SuperAdmin"),
    ("teacher@westlake.edu",  "teacher123",  "Teacher"),
    ("principal@westlake.edu","principal123","Principal"),
    ("sped@westlake.edu",     "sped123",     "SpEdCoordinator"),
    ("parent@westlake.edu",   "parent123",   "Parent"),
    ("district@westlake.edu", "district123", "DistrictAdmin"),
]

print("Testing all role logins...\n")
for email, password, expected_role in USERS:
    r = requests.post(f"{BASE}/auth/login", json={
        "email": email, "password": password, "tenant_slug": "westlake"
    })
    if r.status_code == 200:
        data = r.json()
        role = data.get("role", "?")
        name = data.get("full_name", "?")
        match = "OK" if role == expected_role else f"MISMATCH (expected {expected_role})"
        print(f"  {match:4}  {email:35} => {role} ({name})")
    else:
        print(f"  FAIL  {email:35} => {r.status_code}: {r.text[:80]}")
