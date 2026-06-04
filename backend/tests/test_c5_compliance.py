"""Test C5 -- Compliance Alert Agent"""
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

    # List rules
    r = requests.get(f"{BASE}/compliance/rules", headers=headers)
    print(f"\n[Rules] Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total rules: {data['total_rules']}")
        for rule in data["rules"]:
            print(f"  {rule['code']} [{rule['severity'].upper()}]: {rule['title']}")

    # Run compliance check
    r2 = requests.get(f"{BASE}/compliance/check", headers=headers)
    print(f"\n[Compliance Check] Status: {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        print(f"  Overall status : {data2['overall_status']}")
        print(f"  Total critical : {data2['summary']['total_critical']}")
        print(f"  Total warning  : {data2['summary']['total_warning']}")
        print(f"  Rules checked  : {data2['summary']['rules_checked']}")
        print(f"  Rules triggered: {data2['summary']['rules_triggered']}")
        print(f"  Duration       : {data2['duration_ms']}ms")
        print(f"\n  Alerts:")
        for alert in data2["alerts"]:
            status = "TRIGGERED" if alert["count"] > 0 else "clear"
            print(f"    [{alert['severity'].upper()}] {alert['rule_code']}: "
                  f"{alert['title']} -- {status} ({alert['count']} affected)")
        print(f"\n  Compliance Memo (first 500 chars):")
        print(f"  {data2['compliance_memo'][:500]}")
    else:
        print(f"  Error: {r2.text[:300]}")