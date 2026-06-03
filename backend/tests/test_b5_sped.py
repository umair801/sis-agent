"""
B5 SpEd/IEP test suite.
Requires: API running on localhost:8000, B5 SQL migration applied in Supabase,
          and at least one student in the database.
Run with: python tests/test_b5_sped.py
"""

import sys
import requests
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
TODAY = date.today()
FMT = "%Y-%m-%d"


def login() -> str:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@westlake.edu",
        "password": "admin123",
        "tenant_slug": "westlake",
    })
    if resp.status_code != 200:
        print(f"[FAIL] Login: {resp.text}")
        sys.exit(1)
    print("[PASS] Login")
    return resp.json()["access_token"]


def h(token):
    return {"Authorization": f"Bearer {token}"}


def check(label, resp, expected):
    if resp.status_code == expected:
        print(f"[PASS] {label} => {resp.status_code}")
        return resp.json() if resp.content else {}
    print(f"[FAIL] {label} => expected {expected}, got {resp.status_code}: {resp.text[:400]}")
    return None


def get_first_student(token) -> str:
    resp = requests.get(f"{BASE_URL}/students", headers=h(token), params={"limit": 1})
    if resp.status_code != 200 or not resp.json().get("data"):
        print("[SKIP] No students found — seed a student first via B1 endpoints")
        sys.exit(0)
    student_id = resp.json()["data"][0]["id"]
    print(f"[INFO] Using student_id: {student_id}")
    return student_id


if __name__ == "__main__":
    print("=" * 60)
    print("B5 SpEd / IEP Tests")
    print("=" * 60)

    token = login()
    student_id = get_first_student(token)

    # ------------------------------------------------------------------
    # 1. Create IEP (with nested service, goal, accommodation, team member)
    # ------------------------------------------------------------------
    iep_payload = {
        "student_id": student_id,
        "disability_category": "specific_learning_disability",
        "eligibility_date": (TODAY - timedelta(days=30)).strftime(FMT),
        "start_date": TODAY.strftime(FMT),
        "end_date": (TODAY + timedelta(days=365)).strftime(FMT),
        "next_review_date": (TODAY + timedelta(days=300)).strftime(FMT),
        "triennial_date": (TODAY + timedelta(days=1000)).strftime(FMT),
        "present_levels": "Student demonstrates grade-level math skills but reads 2 years below grade level.",
        "least_restrictive_environment": "General education with resource room support 40% of the day.",
        "placement_percentage_general_ed": "60.00",
        "extended_school_year": False,
        "status": "draft",
        "services": [
            {
                "service_type": "special_education",
                "provider_name": "Ms. Johnson",
                "minutes_per_session": 45,
                "sessions_per_frequency": 5,
                "frequency": "weekly",
                "start_date": TODAY.strftime(FMT),
                "end_date": (TODAY + timedelta(days=365)).strftime(FMT),
                "location": "Resource Room",
            }
        ],
        "goals": [
            {
                "domain": "academic",
                "goal_text": "By end of IEP, student will read grade-level passages with 80% accuracy.",
                "baseline": "Currently reads at 65% accuracy on grade-level passages.",
                "target_criteria": "80% accuracy on 3 of 4 consecutive probes",
                "measurement_method": "Weekly running records",
                "reporting_frequency": "monthly",
                "status": "not_started",
                "sequence": 1,
            }
        ],
        "accommodations": [
            {
                "accommodation_type": "timing_scheduling",
                "description": "Extended time (1.5x) on all tests and quizzes.",
                "applies_to_assessment": True,
                "applies_to_instruction": False,
            }
        ],
        "team_members": [
            {
                "role": "sped_coordinator",
                "name": "Dr. Patricia Lee",
                "email": "plee@westlake.edu",
                "signature_obtained": False,
            }
        ],
    }

    result = check("Create IEP", requests.post(
        f"{BASE_URL}/sped/ieps", json=iep_payload, headers=h(token)
    ), 201)
    if not result:
        sys.exit(1)

    iep_id     = result["id"]
    service_id = result["services"][0]["id"]
    goal_id    = result["goals"][0]["id"]
    acc_id     = result["accommodations"][0]["id"]
    member_id  = result["team_members"][0]["id"]
    print(f"[INFO] IEP id: {iep_id}")

    # ------------------------------------------------------------------
    # 2. Get IEP by ID
    # ------------------------------------------------------------------
    check("Get IEP by ID", requests.get(
        f"{BASE_URL}/sped/ieps/{iep_id}", headers=h(token)
    ), 200)

    # ------------------------------------------------------------------
    # 3. List IEPs (all)
    # ------------------------------------------------------------------
    check("List IEPs", requests.get(
        f"{BASE_URL}/sped/ieps", headers=h(token)
    ), 200)

    # ------------------------------------------------------------------
    # 4. List IEPs for student
    # ------------------------------------------------------------------
    check("List IEPs for student", requests.get(
        f"{BASE_URL}/sped/ieps/student/{student_id}", headers=h(token)
    ), 200)

    # ------------------------------------------------------------------
    # 5. Update IEP status to active
    # ------------------------------------------------------------------
    check("Activate IEP", requests.patch(
        f"{BASE_URL}/sped/ieps/{iep_id}",
        json={"status": "active", "notes": "IEP reviewed and approved by team."},
        headers=h(token),
    ), 200)

    # ------------------------------------------------------------------
    # 6. Add a second service
    # ------------------------------------------------------------------
    svc2 = check("Add speech service", requests.post(
        f"{BASE_URL}/sped/ieps/{iep_id}/services",
        json={
            "service_type": "speech_language",
            "provider_name": "Mr. Carter",
            "minutes_per_session": 30,
            "sessions_per_frequency": 2,
            "frequency": "weekly",
            "start_date": TODAY.strftime(FMT),
            "end_date": (TODAY + timedelta(days=365)).strftime(FMT),
            "location": "Speech Room",
        },
        headers=h(token),
    ), 201)

    # ------------------------------------------------------------------
    # 7. Update service
    # ------------------------------------------------------------------
    check("Update service minutes", requests.patch(
        f"{BASE_URL}/sped/services/{service_id}",
        json={"minutes_per_session": 60},
        headers=h(token),
    ), 200)

    # ------------------------------------------------------------------
    # 8. Add a second goal
    # ------------------------------------------------------------------
    goal2 = check("Add math goal", requests.post(
        f"{BASE_URL}/sped/ieps/{iep_id}/goals",
        json={
            "domain": "academic",
            "goal_text": "Student will solve multi-step word problems with 85% accuracy.",
            "baseline": "Currently at 55% accuracy.",
            "target_criteria": "85% on 3 consecutive weekly probes",
            "measurement_method": "Weekly math probe",
            "status": "not_started",
            "sequence": 2,
        },
        headers=h(token),
    ), 201)

    # ------------------------------------------------------------------
    # 9. Update goal status
    # ------------------------------------------------------------------
    check("Update goal to in_progress", requests.patch(
        f"{BASE_URL}/sped/goals/{goal_id}",
        json={"status": "in_progress"},
        headers=h(token),
    ), 200)

    # ------------------------------------------------------------------
    # 10. Add progress note to goal
    # ------------------------------------------------------------------
    check("Add progress note", requests.post(
        f"{BASE_URL}/sped/goals/{goal_id}/progress",
        json={
            "progress_date": TODAY.strftime(FMT),
            "progress_note": "Student read 3 passages. Accuracy at 70%, improving from 65% baseline.",
            "mastery_percentage": "70.00",
            "status": "in_progress",
        },
        headers=h(token),
    ), 201)

    # ------------------------------------------------------------------
    # 11. Update accommodation
    # ------------------------------------------------------------------
    check("Update accommodation", requests.patch(
        f"{BASE_URL}/sped/accommodations/{acc_id}",
        json={"description": "Extended time (2x) on all assessments.", "applies_to_assessment": True},
        headers=h(token),
    ), 200)

    # ------------------------------------------------------------------
    # 12. Add team member
    # ------------------------------------------------------------------
    tm2 = check("Add parent team member", requests.post(
        f"{BASE_URL}/sped/ieps/{iep_id}/team-members",
        json={
            "role": "parent_guardian",
            "name": "Maria Rodriguez",
            "email": "maria.r@email.com",
            "phone": "555-0101",
            "signature_obtained": True,
            "signature_date": TODAY.strftime(FMT),
        },
        headers=h(token),
    ), 201)

    # ------------------------------------------------------------------
    # 13. Schedule a meeting
    # ------------------------------------------------------------------
    meeting_dt = datetime.now() + timedelta(days=14)
    mtg = check("Schedule annual review meeting", requests.post(
        f"{BASE_URL}/sped/ieps/{iep_id}/meetings",
        json={
            "meeting_type": "annual",
            "scheduled_date": meeting_dt.isoformat(),
            "location": "Conference Room A",
            "attendees": "Dr. Patricia Lee, Maria Rodriguez, Ms. Johnson",
        },
        headers=h(token),
    ), 201)

    if mtg:
        meeting_id = mtg["id"]
        check("Update meeting with minutes", requests.patch(
            f"{BASE_URL}/sped/meetings/{meeting_id}",
            json={
                "actual_date": datetime.now().isoformat(),
                "minutes": "Team reviewed annual goals. Progress noted on reading goal.",
                "outcome": "IEP goals maintained. One accommodation updated.",
                "next_steps": "Schedule 6-week follow-up.",
            },
            headers=h(token),
        ), 200)

    # ------------------------------------------------------------------
    # 14. Compliance alerts
    # ------------------------------------------------------------------
    check("Get compliance alerts (60 days)", requests.get(
        f"{BASE_URL}/sped/compliance/alerts?within_days=60", headers=h(token)
    ), 200)

    check("Get compliance alerts (365 days)", requests.get(
        f"{BASE_URL}/sped/compliance/alerts?within_days=365", headers=h(token)
    ), 200)

    check("Get overdue IEPs", requests.get(
        f"{BASE_URL}/sped/compliance/overdue", headers=h(token)
    ), 200)

    # ------------------------------------------------------------------
    # 15. Delete service (cleanup test)
    # ------------------------------------------------------------------
    if svc2:
        check("Delete added speech service", requests.delete(
            f"{BASE_URL}/sped/services/{svc2['id']}", headers=h(token)
        ), 204)

    # ------------------------------------------------------------------
    # 16. Delete IEP (should fail — status is active, not draft)
    # ------------------------------------------------------------------
    resp = requests.delete(f"{BASE_URL}/sped/ieps/{iep_id}", headers=h(token))
    if resp.status_code == 409:
        print("[PASS] Delete active IEP correctly rejected => 409")
    else:
        print(f"[FAIL] Delete active IEP should be 409, got {resp.status_code}")

    print()
    print("=" * 60)
    print("B5 Tests Complete")
    print("=" * 60)
