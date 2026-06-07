import requests

BASE = "http://localhost:8000/api/v1"

print("Testing login endpoint directly...")
payload = {
    "email": "admin@westlake.edu",
    "password": "admin123",
    "tenant_slug": "westlake"
}

try:
    r = requests.post(f"{BASE}/auth/login", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
