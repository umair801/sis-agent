"""
B3 Scheduling Engine test suite.
Run with: python backend/tests/test_b3_scheduling.py
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"


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
    print(f"[FAIL] {label} => expected {expected}, got {resp.status_code}: {resp.text[:300]}")
    return None


if __name__ == "__main__":
    print("=" * 55)
    print("B3 Scheduling Engine Tests")
    print("=" * 55)

    token = login()

    # Get lookups
    schools = requests.get(f"{BASE_URL}/students/lookups/schools", headers=h(token)).json()
    years = requests.get(f"{BASE_URL}/students/lookups/academic-years", headers=h(token)).json()
    periods = requests.get(f"{BASE_URL}/attendance/periods?school_id={schools[0]['id']}", headers=h(token)).json()
    school_id = schools[0]["id"]
    year_id = years[0]["id"]
    period_1_id = periods[0]["id"]
    period_2_id = periods[1]["id"]
    print(f"\nSchool: {schools[0]['name']}")
    print(f"Year:   {years[0]['name']}")
    print(f"Using Period 1: {periods[0]['name']}, Period 2: {periods[1]['name']}")

    # Courses
    print("\n--- Courses ---")
    courses = check("GET courses", requests.get(f"{BASE_URL}/scheduling/courses", headers=h(token)), 200)
    if courses:
        print(f"       Courses found: {len(courses)}")
    course_id = courses[0]["id"] if courses else None
    course_id_2 = courses[1]["id"] if courses and len(courses) > 1 else course_id

    # Rooms
    print("\n--- Rooms ---")
    rooms = check("GET rooms", requests.get(f"{BASE_URL}/scheduling/rooms?school_id={school_id}", headers=h(token)), 200)
    if rooms:
        print(f"       Rooms found: {len(rooms)}")
    room_id = rooms[0]["id"] if rooms else None

    # Sections
    print("\n--- Sections ---")
    sec1_payload = {
        "school_id": school_id,
        "course_id": course_id,
        "academic_year_id": year_id,
        "period_id": period_1_id,
        "room_id": room_id,
        "section_number": "01",
        "max_enrollment": 30
    }
    sec1 = check("POST create section 1", requests.post(f"{BASE_URL}/scheduling/sections", json=sec1_payload, headers=h(token)), 201)
    if not sec1:
        sys.exit(1)
    section_1_id = sec1["id"]
    print(f"       Section 1 ID: {section_1_id}")

    sec2_payload = {
        "school_id": school_id,
        "course_id": course_id_2,
        "academic_year_id": year_id,
        "period_id": period_2_id,
        "room_id": room_id,
        "section_number": "01",
        "max_enrollment": 28
    }
    sec2 = check("POST create section 2", requests.post(f"{BASE_URL}/scheduling/sections", json=sec2_payload, headers=h(token)), 201)
    section_2_id = sec2["id"] if sec2 else None

    sections_list = check("GET list sections", requests.get(f"{BASE_URL}/scheduling/sections?academic_year_id={year_id}", headers=h(token)), 200)
    if sections_list:
        print(f"       Sections found: {len(sections_list)}")

    # Conflict detection: same room, same period (force a conflict)
    print("\n--- Conflict Detection ---")
    conflict_payload = {
        "school_id": school_id,
        "course_id": course_id_2,
        "academic_year_id": year_id,
        "period_id": period_1_id,
        "room_id": room_id,
        "section_number": "02",
        "max_enrollment": 35
    }
    conflict_sec = check(
        "POST section with room conflict (still creates)",
        requests.post(f"{BASE_URL}/scheduling/sections", json=conflict_payload, headers=h(token)),
        201
    )
    conflicts = check(
        "GET detect conflicts",
        requests.get(f"{BASE_URL}/scheduling/conflicts?academic_year_id={year_id}", headers=h(token)),
        200
    )
    if conflicts:
        print(f"       Conflicts found: {conflicts['conflict_count']}")
        for c in conflicts["conflicts"]:
            print(f"       [{c['severity'].upper()}] {c['conflict_type']}: {c['description']}")
            print(f"       Suggestion: {c['suggestion']}")

    # Student enrollment in section
    print("\n--- Student Section Enrollment ---")
    students = requests.get(f"{BASE_URL}/students?is_active=true", headers=h(token)).json()
    if students["total"] == 0:
        print("[SKIP] No active students found")
    else:
        student_id = students["items"][0]["id"]
        print(f"       Using student: {students['items'][0]['first_name']} {students['items'][0]['last_name']}")

        ss = check(
            "POST enroll student in section",
            requests.post(f"{BASE_URL}/scheduling/student-sections", json={
                "student_id": student_id,
                "section_id": section_1_id
            }, headers=h(token)),
            201
        )

        if ss:
            ss_id = ss["id"]
            check(
                "POST duplicate enrollment (expect 409)",
                requests.post(f"{BASE_URL}/scheduling/student-sections", json={
                    "student_id": student_id,
                    "section_id": section_1_id
                }, headers=h(token)),
                409
            )

            schedule = check(
                "GET student schedule",
                requests.get(f"{BASE_URL}/scheduling/student-sections/student/{student_id}?academic_year_id={year_id}", headers=h(token)),
                200
            )
            if schedule:
                print(f"       Courses in schedule: {len(schedule)}")
                for s in schedule:
                    print(f"       {s['period_name']}: {s['course_name']}")

            check(
                "DELETE drop student from section",
                requests.delete(f"{BASE_URL}/scheduling/student-sections/{ss_id}", headers=h(token)),
                204
            )

    print("\n" + "=" * 55)
    print("B3 Tests complete.")
    print("=" * 55)