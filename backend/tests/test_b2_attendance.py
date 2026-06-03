"""
B2 Attendance Tracking test suite.
Run with: python backend/tests/test_b2_attendance.py
"""
import requests
import sys
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"
TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


def login() -> str:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@westlake.edu",
        "password": "admin123",
        "tenant_slug": "westlake"
    })
    if resp.status_code != 200:
        print(f"[FAIL] Login: {resp.text}")
        sys.exit(1)
    print("[PASS] Login")
    return resp.json()["access_token"]


def h(token): return {"Authorization": f"Bearer {token}"}


def check(label, resp, expected):
    if resp.status_code == expected:
        print(f"[PASS] {label} => {resp.status_code}")
        return resp.json() if resp.content else {}
    print(f"[FAIL] {label} => expected {expected}, got {resp.status_code}: {resp.text[:200]}")
    return None


if __name__ == "__main__":
    print("=" * 55)
    print("B2 Attendance Tracking Tests")
    print("=" * 55)

    token = login()

    # Get school and student IDs from existing data
    schools = requests.get(f"{BASE_URL}/students/lookups/schools", headers=h(token)).json()
    students = requests.get(f"{BASE_URL}/students", headers=h(token)).json()

    if not schools:
        print("[FAIL] No schools found. Run B1 first.")
        sys.exit(1)

    school_id = schools[0]["id"]
    print(f"\nUsing school: {schools[0]['name']} ({school_id})")

    # Create a fresh test student for attendance tests
    print("\n--- Setup: create test student ---")
    student_payload = {
        "student_number": "WHS-ATT-001",
        "first_name": "Bob",
        "last_name": "Smith",
        "date_of_birth": "2008-05-20"
    }
    s_resp = requests.post(f"{BASE_URL}/students", json=student_payload, headers=h(token))
    if s_resp.status_code not in (201, 409):
        print(f"[FAIL] Could not create test student: {s_resp.text}")
        sys.exit(1)
    if s_resp.status_code == 201:
        student_id = s_resp.json()["id"]
    else:
        # Already exists, look it up
        found = requests.get(f"{BASE_URL}/students?search=WHS-ATT-001", headers=h(token)).json()
        student_id = found["items"][0]["id"]
    print(f"[PASS] Test student ID: {student_id}")

    # Periods
    print("\n--- Periods ---")
    periods_resp = check(
        "GET periods",
        requests.get(f"{BASE_URL}/attendance/periods?school_id={school_id}", headers=h(token)),
        200
    )
    if not periods_resp:
        print("[FAIL] No periods returned. Check seed data.")
        sys.exit(1)
    print(f"       Periods found: {len(periods_resp)}")
    period_id = periods_resp[0]["id"]

    # Single daily attendance
    print("\n--- Daily Attendance ---")
    daily_payload = {
        "student_id": student_id,
        "school_id": school_id,
        "attendance_date": TODAY,
        "status": "present"
    }
    daily = check("POST daily attendance", requests.post(f"{BASE_URL}/attendance/daily", json=daily_payload, headers=h(token)), 201)
    if not daily:
        sys.exit(1)
    record_id = daily["id"]

    # Upsert same record (update)
    daily_payload["status"] = "tardy"
    updated = check("POST daily upsert (update to tardy)", requests.post(f"{BASE_URL}/attendance/daily", json=daily_payload, headers=h(token)), 201)
    if updated:
        print(f"       Status after upsert: {updated['status']}")

    # Patch
    patched = check("PATCH daily attendance", requests.patch(f"{BASE_URL}/attendance/daily/{record_id}", json={"status": "present", "notes": "Arrived late but present"}, headers=h(token)), 200)
    if patched:
        print(f"       Status after patch: {patched['status']}")

    # GET by date
    daily_list = check("GET daily by date", requests.get(f"{BASE_URL}/attendance/daily?school_id={school_id}&attendance_date={TODAY}", headers=h(token)), 200)
    if daily_list is not None:
        print(f"       Records for today: {len(daily_list)}")

    # GET student history
    check("GET student daily history", requests.get(f"{BASE_URL}/attendance/daily/student/{student_id}?date_from={YESTERDAY}&date_to={TODAY}", headers=h(token)), 200)

    # Bulk daily
    print("\n--- Bulk Daily Attendance ---")
    bulk_payload = {
        "school_id": school_id,
        "attendance_date": YESTERDAY,
        "entries": [
            {"student_id": student_id, "status": "absent", "excuse_reason": "Sick"},
        ]
    }
    bulk = check("POST bulk daily", requests.post(f"{BASE_URL}/attendance/daily/bulk", json=bulk_payload, headers=h(token)), 200)
    if bulk:
        print(f"       Created: {bulk['created']}, Updated: {bulk['updated']}")

    # Period attendance
    print("\n--- Period Attendance ---")
    period_payload = {
        "student_id": student_id,
        "school_id": school_id,
        "period_id": period_id,
        "attendance_date": TODAY,
        "status": "present"
    }
    p_record = check("POST period attendance", requests.post(f"{BASE_URL}/attendance/period", json=period_payload, headers=h(token)), 201)

    # GET period attendance
    check("GET period attendance by date", requests.get(f"{BASE_URL}/attendance/period?school_id={school_id}&attendance_date={TODAY}", headers=h(token)), 200)

    # Bulk period
    print("\n--- Bulk Period Attendance ---")
    bulk_period = {
        "school_id": school_id,
        "attendance_date": TODAY,
        "entries": [
            {"student_id": student_id, "period_id": period_id, "status": "tardy"},
        ]
    }
    bulk_p = check("POST bulk period", requests.post(f"{BASE_URL}/attendance/period/bulk", json=bulk_period, headers=h(token)), 200)
    if bulk_p:
        print(f"       Created: {bulk_p['created']}, Updated: {bulk_p['updated']}")

    # Reports
    print("\n--- Reports ---")
    summary = check(
        "GET student attendance summary",
        requests.get(f"{BASE_URL}/attendance/reports/student-summary?date_from={YESTERDAY}&date_to={TODAY}&school_id={school_id}", headers=h(token)),
        200
    )
    if summary:
        print(f"       Students in report: {len(summary)}")
        if summary:
            s = summary[0]
            print(f"       {s['first_name']} {s['last_name']}: {s['attendance_rate']}% attendance")

    daily_summary = check(
        "GET daily attendance summary",
        requests.get(f"{BASE_URL}/attendance/reports/daily-summary?school_id={school_id}&date_from={YESTERDAY}&date_to={TODAY}", headers=h(token)),
        200
    )
    if daily_summary:
        print(f"       Days in report: {len(daily_summary)}")

    print("\n" + "=" * 55)
    print("B2 Tests complete.")
    print("=" * 55)