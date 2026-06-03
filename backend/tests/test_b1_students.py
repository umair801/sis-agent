"""
B1 Student CRUD test suite.
Run with: python backend/tests/test_b1_students.py
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def login(email: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password, "tenant_slug": "westlake"})
    if resp.status_code != 200:
        print(f"[FAIL] Login failed: {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"[PASS] Login successful for {email}")
    return token


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def check(label: str, resp, expected_status: int):
    if resp.status_code == expected_status:
        print(f"[PASS] {label} => {resp.status_code}")
        return resp.json() if resp.content else {}
    else:
        print(f"[FAIL] {label} => expected {expected_status}, got {resp.status_code}")
        print(f"       Response: {resp.text[:300]}")
        return None


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #

def test_lookups(token: str):
    print("\n--- Lookups ---")
    h = headers(token)
    check("GET schools", requests.get(f"{BASE_URL}/students/lookups/schools", headers=h), 200)
    check("GET academic years", requests.get(f"{BASE_URL}/students/lookups/academic-years", headers=h), 200)
    gl = check("GET grade levels", requests.get(f"{BASE_URL}/students/lookups/grade-levels", headers=h), 200)
    return gl


def test_student_crud(token: str) -> dict:
    print("\n--- Student CRUD ---")
    h = headers(token)

    # Create
    payload = {
        "student_number": "WHS-2025-001",
        "first_name": "Alice",
        "middle_name": "Marie",
        "last_name": "Johnson",
        "date_of_birth": "2009-03-15",
        "gender": "Female",
        "ethnicity": "Hispanic",
        "address_line1": "42 Oak Street",
        "city": "Westlake",
        "state": "CA",
        "zip_code": "90001",
        "phone": "(310) 555-1234",
        "email": "alice.johnson@student.westlake.edu",
        "guardians": [
            {
                "first_name": "Maria",
                "last_name": "Johnson",
                "relationship": "Mother",
                "phone_primary": "(310) 555-5678",
                "email": "maria.johnson@email.com",
                "is_emergency_contact": True,
                "is_authorized_pickup": True
            }
        ]
    }
    result = check("POST create student", requests.post(f"{BASE_URL}/students", json=payload, headers=h), 201)
    if not result:
        sys.exit(1)
    student_id = result["id"]
    print(f"       Student ID: {student_id}")
    print(f"       Guardians: {len(result.get('guardians', []))}")

    # Duplicate student number
    check(
        "POST duplicate student_number (expect 409)",
        requests.post(f"{BASE_URL}/students", json=payload, headers=h),
        409
    )

    # List
    list_result = check("GET list students", requests.get(f"{BASE_URL}/students", headers=h), 200)
    if list_result:
        print(f"       Total students: {list_result['total']}")

    # Get by ID
    check("GET student by ID", requests.get(f"{BASE_URL}/students/{student_id}", headers=h), 200)

    # Search
    search_result = check(
        "GET search by name",
        requests.get(f"{BASE_URL}/students?search=Alice", headers=h),
        200
    )
    if search_result:
        print(f"       Search results: {search_result['total']}")

    # Update
    update_payload = {"city": "Los Angeles", "zip_code": "90002"}
    updated = check("PATCH update student", requests.patch(f"{BASE_URL}/students/{student_id}", json=update_payload, headers=h), 200)
    if updated:
        print(f"       Updated city: {updated['city']}")

    return result


def test_enrollment(token: str, student_id: str):
    print("\n--- Enrollment ---")
    h = headers(token)

    schools = requests.get(f"{BASE_URL}/students/lookups/schools", headers=h).json()
    years = requests.get(f"{BASE_URL}/students/lookups/academic-years", headers=h).json()
    levels = requests.get(f"{BASE_URL}/students/lookups/grade-levels", headers=h).json()

    if not schools or not years or not levels:
        print("[SKIP] Missing lookup data for enrollment test")
        return

    payload = {
        "student_id": student_id,
        "school_id": schools[0]["id"],
        "academic_year_id": years[0]["id"],
        "grade_level_id": levels[0]["id"],
        "enrollment_date": "2024-08-26"
    }
    result = check("POST enroll student", requests.post(f"{BASE_URL}/students/enrollments", json=payload, headers=h), 201)
    if result:
        enrollment_id = result["id"]
        print(f"       Enrollment ID: {enrollment_id}")

        check(
            "POST duplicate enrollment (expect 409)",
            requests.post(f"{BASE_URL}/students/enrollments", json=payload, headers=h),
            409
        )

        update_payload = {"status": "active", "grade_level_id": levels[1]["id"] if len(levels) > 1 else levels[0]["id"]}
        check("PATCH update enrollment", requests.patch(f"{BASE_URL}/students/enrollments/{enrollment_id}", json=update_payload, headers=h), 200)


def test_guardian_crud(token: str, student_id: str):
    print("\n--- Guardian CRUD ---")
    h = headers(token)

    payload = {
        "first_name": "Robert",
        "last_name": "Johnson",
        "relationship": "Father",
        "phone_primary": "(310) 555-9999",
        "is_emergency_contact": True,
        "is_authorized_pickup": False
    }
    result = check("POST add guardian", requests.post(f"{BASE_URL}/students/{student_id}/guardians", json=payload, headers=h), 201)
    if result:
        guardian_id = result["id"]
        check("DELETE guardian", requests.delete(f"{BASE_URL}/students/{student_id}/guardians/{guardian_id}", headers=h), 204)


def test_soft_delete(token: str, student_id: str):
    print("\n--- Soft Delete ---")
    h = headers(token)
    check("DELETE student (soft)", requests.delete(f"{BASE_URL}/students/{student_id}", headers=h), 204)
    check("GET deleted student (expect 404)", requests.get(f"{BASE_URL}/students/{student_id}", headers=h), 404)


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    print("=" * 55)
    print("B1 Student Profiles and Enrollment CRUD Tests")
    print("=" * 55)

    token = login("admin@westlake.edu", "admin123")

    test_lookups(token)
    student = test_student_crud(token)
    student_id = student["id"]
    test_enrollment(token, student_id)
    test_guardian_crud(token, student_id)
    test_soft_delete(token, student_id)

    print("\n" + "=" * 55)
    print("B1 Tests complete.")
    print("=" * 55)