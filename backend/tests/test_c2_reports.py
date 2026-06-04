"""Test C2 -- Automated Report Generator"""
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


def test_report(token: str, report_type: str):
    r = requests.post(
        f"{BASE}/reports/generate",
        json={"report_type": report_type},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\n[{report_type}]")
    print(f"  Status : {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Title  : {data.get('title')}")
        print(f"  Rows   : {data.get('row_count')}")
        print(f"  Stats  : {json.dumps(data.get('summary_stats'), indent=4)}")
        print(f"  Narrative: {data.get('narrative')}")
        print(f"  ms     : {data.get('duration_ms')}")
    else:
        print(f"  Error  : {r.text[:300]}")


if __name__ == "__main__":
    token = get_token()
    print("Token obtained.")

    r = requests.get(f"{BASE}/reports/types", headers={"Authorization": f"Bearer {token}"})
    print(f"\n[Report Types] {r.json()['report_types']}")

    for rt in ["attendance_weekly", "attendance_monthly", "grade_distribution",
               "student_gpa_summary", "iep_compliance", "enrollment_summary"]:
        test_report(token, rt)