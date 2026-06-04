"""Test C3 -- Conflict Detection Agent"""
import requests
import json

BASE = "http://localhost:8000/api/v1"


def get_token():
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "admin@westlake.edu",
        "password": "admin123",
        "tenant_slug": "westlake"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


if __name__ == "__main__":
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("Token obtained.")

    # Full scan
    r = requests.post(
        f"{BASE}/conflicts/scan",
        json={"check_scheduling": True, "check_iep": True},
        headers=headers
    )
    print(f"\n[Full Scan] Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Overall status : {data['overall_status']}")
        print(f"  Total critical : {data['total_critical']}")
        print(f"  Total warning  : {data['total_warning']}")
        print(f"  Duration       : {data['duration_ms']}ms")
        print(f"\n  Findings:")
        for f in data["findings"]:
            print(f"    [{f['severity'].upper()}] {f['title']}: {f['count']} item(s)")
            if f["count"] > 0:
                print(f"      Suggestions: {f['suggestions'][:200]}...")
    else:
        print(f"  Error: {r.text[:300]}")

    # Scheduling only
    r2 = requests.post(
        f"{BASE}/conflicts/scan",
        json={"check_scheduling": True, "check_iep": False},
        headers=headers
    )
    print(f"\n[Scheduling Only] Status: {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        print(f"  Overall: {data2['overall_status']} | Findings: {len(data2['findings'])}")

    # IEP only
    r3 = requests.post(
        f"{BASE}/conflicts/scan",
        json={"check_scheduling": False, "check_iep": True},
        headers=headers
    )
    print(f"\n[IEP Only] Status: {r3.status_code}")
    if r3.status_code == 200:
        data3 = r3.json()
        print(f"  Overall: {data3['overall_status']} | Findings: {len(data3['findings'])}")