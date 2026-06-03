"""
B4 Gradebook test suite.
Run with: python backend/tests/test_b4_gradebook.py
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
    print("B4 Gradebook Tests")
    print("=" * 55)

    token = login()

    years = requests.get(f"{BASE_URL}/students/lookups/academic-years", headers=h(token)).json()
    year_id = years[0]["id"]

    sections = requests.get(f"{BASE_URL}/scheduling/sections?academic_year_id={year_id}", headers=h(token)).json()
    if not sections:
        print("[FAIL] No sections found. Run B3 first.")
        sys.exit(1)
    section_id = sections[0]["id"]
    print(f"\nUsing section: {sections[0].get('course_name','?')} ({section_id})")

    students = requests.get(f"{BASE_URL}/students?is_active=true", headers=h(token)).json()
    if students["total"] == 0:
        print("[FAIL] No students found. Run B1 first.")
        sys.exit(1)
    student_id = students["items"][0]["id"]
    print(f"Using student: {students['items'][0]['first_name']} {students['items'][0]['last_name']}")

    # Grading scale
    print("\n--- Grading Scale ---")
    scale = check("GET grading scale", requests.get(f"{BASE_URL}/gradebook/grading-scale", headers=h(token)), 200)
    if scale:
        print(f"       Scale entries: {len(scale)}")

    # Categories
    print("\n--- Assignment Categories ---")
    cat_resp = requests.post(f"{BASE_URL}/gradebook/categories", json={
        "section_id": section_id,
        "name": "Tests",
        "weight": 60.0,
        "drop_lowest": 0
    }, headers=h(token))
    cat = cat_resp.json() if cat_resp.status_code in (201, 409) else None
    print(f"[{'PASS' if cat_resp.status_code in (201, 409) else 'FAIL'}] POST create category => {cat_resp.status_code}")

    cat2_resp = requests.post(f"{BASE_URL}/gradebook/categories", json={
        "section_id": section_id,
        "name": "Homework",
        "weight": 40.0,
        "drop_lowest": 1
    }, headers=h(token))
    print(f"[{'PASS' if cat2_resp.status_code in (201, 409) else 'FAIL'}] POST create category 2 => {cat2_resp.status_code}")
    cats = check("GET categories", requests.get(f"{BASE_URL}/gradebook/categories?section_id={section_id}", headers=h(token)), 200)
    if cats:
        print(f"       Categories: {len(cats)}")

    # Get cat_id from the categories list since creation may return 409 on re-run
    cats_list = requests.get(f"{BASE_URL}/gradebook/categories?section_id={section_id}", headers=h(token)).json()
    cat_id = cats_list[0]["id"] if cats_list else None

    # Assignments
    print("\n--- Assignments ---")
    a1 = check("POST create assignment 1", requests.post(f"{BASE_URL}/gradebook/assignments", json={
        "section_id": section_id,
        "category_id": cat_id,
        "name": "Midterm Exam",
        "max_points": 100.0,
        "due_date": "2024-10-15",
        "is_published": True
    }, headers=h(token)), 201)

    a2 = check("POST create assignment 2", requests.post(f"{BASE_URL}/gradebook/assignments", json={
        "section_id": section_id,
        "category_id": cat_id,
        "name": "Final Exam",
        "max_points": 100.0,
        "due_date": "2024-12-10",
        "is_published": True
    }, headers=h(token)), 201)

    assignments = check("GET assignments", requests.get(f"{BASE_URL}/gradebook/assignments?section_id={section_id}", headers=h(token)), 200)
    if assignments:
        print(f"       Assignments: {len(assignments)}")

    if not a1 or not a2:
        print("[FAIL] Could not create assignments")
        sys.exit(1)

    # Enroll student in section first
    requests.post(f"{BASE_URL}/scheduling/student-sections", json={
        "student_id": student_id,
        "section_id": section_id
    }, headers=h(token))

    # Grade entry
    print("\n--- Grade Entry ---")
    g1 = check("POST enter grade (85/100)", requests.post(f"{BASE_URL}/gradebook/grades", json={
        "student_id": student_id,
        "assignment_id": a1["id"],
        "points_earned": 85.0
    }, headers=h(token)), 201)
    if g1:
        print(f"       Grade: {g1['points_earned']} pts, {g1['percentage']}%, {g1['letter_grade']}")

    g2 = check("POST enter grade (92/100)", requests.post(f"{BASE_URL}/gradebook/grades", json={
        "student_id": student_id,
        "assignment_id": a2["id"],
        "points_earned": 92.0
    }, headers=h(token)), 201)
    if g2:
        print(f"       Grade: {g2['points_earned']} pts, {g2['percentage']}%, {g2['letter_grade']}")

    # Upsert (update existing grade)
    updated = check("POST upsert grade (update to 90)", requests.post(f"{BASE_URL}/gradebook/grades", json={
        "student_id": student_id,
        "assignment_id": a1["id"],
        "points_earned": 90.0
    }, headers=h(token)), 201)
    if updated:
        print(f"       Updated grade: {updated['percentage']}% => {updated['letter_grade']}")

    # Bulk grades
    print("\n--- Bulk Grade Entry ---")
    bulk = check("POST bulk grades", requests.post(f"{BASE_URL}/gradebook/grades/bulk", json={
        "entries": [
            {"student_id": student_id, "assignment_id": a1["id"], "points_earned": 88.0},
            {"student_id": student_id, "assignment_id": a2["id"], "points_earned": 94.0},
        ]
    }, headers=h(token)), 200)
    if bulk:
        print(f"       Grades entered: {len(bulk)}")

    # GET grades
    grades = check("GET grades for section", requests.get(f"{BASE_URL}/gradebook/grades?section_id={section_id}", headers=h(token)), 200)
    if grades:
        print(f"       Grade records: {len(grades)}")

    # Compute final grade
    print("\n--- GPA Computation ---")
    fg = check("POST compute final grade", requests.post(
        f"{BASE_URL}/gradebook/final-grades/compute?student_id={student_id}&section_id={section_id}&academic_year_id={year_id}",
        headers=h(token)
    ), 200)
    if fg:
        print(f"       Final: {fg['final_percentage']}% => {fg['letter_grade']} ({fg['gpa_points']} GPA pts)")
        print(f"       Passing: {fg['is_passing']}, Credits earned: {fg['credits_earned']}")

    # Section gradebook
    gradebook = check("GET section gradebook", requests.get(
        f"{BASE_URL}/gradebook/final-grades?section_id={section_id}&academic_year_id={year_id}",
        headers=h(token)
    ), 200)
    if gradebook:
        print(f"       Students in gradebook: {len(gradebook)}")

    # Transcript
    print("\n--- Transcript ---")
    transcript = check("GET transcript", requests.get(f"{BASE_URL}/gradebook/transcript/{student_id}", headers=h(token)), 200)
    if transcript:
        print(f"       Student: {transcript['first_name']} {transcript['last_name']}")
        print(f"       Cumulative GPA: {transcript['cumulative_gpa']}")
        print(f"       Total credits earned: {transcript['total_credits_earned']}")
        for yr in transcript["years"]:
            print(f"       {yr['academic_year']}: GPA {yr['year_gpa']}, {len(yr['courses'])} course(s)")

    print("\n" + "=" * 55)
    print("B4 Tests complete.")
    print("=" * 55)