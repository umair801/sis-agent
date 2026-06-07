"""
End-to-end test suite for AgAI_30 SIS backend.
Run from project root with venv active:
  python e2e_test.py
"""
import requests, sys
from datetime import date, timedelta

BASE      = "http://localhost:8000/api/v1"
TENANT    = "westlake"
SCHOOL_ID = "b0000000-0000-0000-0000-000000000001"
TODAY     = date.today().isoformat()
WEEK_AGO  = (date.today() - timedelta(days=7)).isoformat()

USERS = [
    ("admin@westlake.edu",     "admin123",     "SuperAdmin"),
    ("teacher@westlake.edu",   "Password123!", "Teacher"),
    ("principal@westlake.edu", "Password123!", "Principal"),
    ("sped@westlake.edu",      "Password123!", "SpEdCoordinator"),
    ("parent@westlake.edu",    "Password123!", "Parent"),
    ("district@westlake.edu",  "Password123!", "DistrictAdmin"),
]

results = []
tokens  = {}

def ok(label):
    results.append(("PASS", label))
    print(f"  PASS  {label}")

def fail(label, reason=""):
    results.append(("FAIL", label))
    print(f"  FAIL  {label}" + (f" -- {reason[:100]}" if reason else ""))

def check(label, r, expected=200):
    if r.status_code == expected:
        ok(label); return True
    fail(label, f"HTTP {r.status_code}: {r.text[:120]}"); return False

def h(role="SuperAdmin"):
    return {"Authorization": f"Bearer {tokens.get(role, '')}"}

# ── STEP 1 ────────────────────────────────────────────────────────────────
print("\n=== STEP 1: Authentication (all 6 roles) ===")
for email, password, role in USERS:
    r = requests.post(f"{BASE}/auth/login",
                      json={"email": email, "password": password, "tenant_slug": TENANT})
    if r.status_code == 200:
        tokens[role] = r.json()["access_token"]; ok(f"Login {role}")
    else:
        fail(f"Login {role}", f"HTTP {r.status_code}")

# ── STEP 2 ────────────────────────────────────────────────────────────────
print("\n=== STEP 2: Health Check ===")
check("GET /health", requests.get(f"{BASE}/health"))

# ── STEP 3: Students (B1) ─────────────────────────────────────────────────
print("\n=== STEP 3: Students (B1) ===")
r = requests.get(f"{BASE}/students", headers=h())
check("GET /students", r)
students = []
if r.status_code == 200:
    d = r.json()
    students = d if isinstance(d, list) else d.get("students", d.get("items", []))
    print(f"         {len(students)} students")
if students:
    check("GET /students/{id}", requests.get(f"{BASE}/students/{students[0]['id']}", headers=h()))

# ── STEP 4: Attendance (B2) ───────────────────────────────────────────────
print("\n=== STEP 4: Attendance (B2) ===")
check("GET /attendance/daily",
      requests.get(f"{BASE}/attendance/daily",
                   params={"school_id": SCHOOL_ID, "attendance_date": TODAY}, headers=h()))
check("GET /attendance/period",
      requests.get(f"{BASE}/attendance/period",
                   params={"school_id": SCHOOL_ID, "attendance_date": TODAY}, headers=h()))
check("GET /attendance/reports/student-summary",
      requests.get(f"{BASE}/attendance/reports/student-summary",
                   params={"date_from": WEEK_AGO, "date_to": TODAY}, headers=h()))
check("GET /attendance/reports/daily-summary",
      requests.get(f"{BASE}/attendance/reports/daily-summary",
                   params={"school_id": SCHOOL_ID, "date_from": WEEK_AGO, "date_to": TODAY}, headers=h()))

# ── STEP 5: Scheduling (B3) ───────────────────────────────────────────────
print("\n=== STEP 5: Scheduling (B3) ===")
r = requests.get(f"{BASE}/scheduling/sections", headers=h())
check("GET /scheduling/sections", r)
sections = []
if r.status_code == 200:
    d = r.json()
    sections = d if isinstance(d, list) else d.get("sections", d.get("items", []))
    print(f"         {len(sections)} sections")

# ── STEP 6: Gradebook (B4) ────────────────────────────────────────────────
print("\n=== STEP 6: Gradebook (B4) ===")
if sections:
    sid = sections[0]["id"]
    check("GET /gradebook/grades",
          requests.get(f"{BASE}/gradebook/grades", params={"section_id": sid}, headers=h()))
    check("GET /gradebook/assignments",
          requests.get(f"{BASE}/gradebook/assignments", params={"section_id": sid}, headers=h()))
else:
    fail("GET /gradebook/grades", "No sections"); fail("GET /gradebook/assignments", "No sections")

# ── STEP 7: SpEd/IEP (B5) ────────────────────────────────────────────────
print("\n=== STEP 7: SpEd/IEP (B5) ===")
check("GET /sped/ieps (SuperAdmin)",      requests.get(f"{BASE}/sped/ieps", headers=h()))
check("GET /sped/ieps (SpEdCoordinator)", requests.get(f"{BASE}/sped/ieps", headers=h("SpEdCoordinator")))

# ── STEP 8: Budget (B6) ───────────────────────────────────────────────────
print("\n=== STEP 8: Budget (B6) ===")
check("GET /budget/fiscal-years",         requests.get(f"{BASE}/budget/fiscal-years",         headers=h()))
check("GET /budget/fiscal-years/current", requests.get(f"{BASE}/budget/fiscal-years/current", headers=h()))
check("GET /budget/budgets",              requests.get(f"{BASE}/budget/budgets",              headers=h()))

# ── STEP 9: Communication (B7) ────────────────────────────────────────────
print("\n=== STEP 9: Communication (B7) ===")
check("GET /communication/announcements",
      requests.get(f"{BASE}/communication/announcements", headers=h()))
check("GET /communication/messages/inbox (Parent)",
      requests.get(f"{BASE}/communication/messages/inbox", headers=h("Parent")))
check("GET /communication/messages/sent (Parent)",
      requests.get(f"{BASE}/communication/messages/sent", headers=h("Parent")))

# ── STEP 10: NL Query (C1) ────────────────────────────────────────────────
print("\n=== STEP 10: NL Query (C1) ===")
r = requests.post(f"{BASE}/query/ask",
                  json={"question": "How many students are enrolled?"},
                  headers=h())
check("POST /query/ask", r)
if r.status_code == 200:
    print(f"         summary: {str(r.json().get('summary',''))[:80]}")

# ── STEP 11: Reports (C2) ─────────────────────────────────────────────────
print("\n=== STEP 11: Reports (C2) ===")
check("GET /reports/types",
      requests.get(f"{BASE}/reports/types", headers=h()))
check("POST /reports/generate (attendance_weekly)",
      requests.post(f"{BASE}/reports/generate",
                    json={"report_type": "attendance_weekly"}, headers=h()))

# ── STEP 12: Conflict Detection (C3) ─────────────────────────────────────
print("\n=== STEP 12: Conflict Detection (C3) ===")
check("GET  /conflicts/scan",
      requests.get(f"{BASE}/conflicts/scan", headers=h()))
check("POST /conflicts/scan",
      requests.post(f"{BASE}/conflicts/scan",
                    json={"check_scheduling": True, "check_iep": True}, headers=h()))

# ── STEP 13: Forecasting (C4) ─────────────────────────────────────────────
print("\n=== STEP 13: Forecasting (C4) ===")
check("GET  /forecasts/types",
      requests.get(f"{BASE}/forecasts/types", headers=h()))
check("POST /forecasts/run (enrollment)",
      requests.post(f"{BASE}/forecasts/run",
                    json={"forecast_type": "enrollment"}, headers=h()))

# ── STEP 14: Compliance (C5) ──────────────────────────────────────────────
print("\n=== STEP 14: Compliance (C5) ===")
check("GET /compliance/rules", requests.get(f"{BASE}/compliance/rules", headers=h()))
check("GET /compliance/check", requests.get(f"{BASE}/compliance/check", headers=h()))

# ── STEP 15: RAG District Docs (C6) ──────────────────────────────────────
print("\n=== STEP 15: RAG District Docs (C6) ===")
check("GET  /district-docs/categories",
      requests.get(f"{BASE}/district-docs/categories", headers=h()))
check("POST /district-docs/query",
      requests.post(f"{BASE}/district-docs/query",
                    json={"question": "What is the attendance policy?"}, headers=h()))

# ── STEP 16: RBAC ─────────────────────────────────────────────────────────
print("\n=== STEP 16: Role-Based Access Control ===")
check("Teacher   GET /students",                   requests.get(f"{BASE}/students",                            headers=h("Teacher")))
check("Parent    GET /communication/announcements", requests.get(f"{BASE}/communication/announcements",         headers=h("Parent")))
check("Parent    GET /communication/messages/inbox",requests.get(f"{BASE}/communication/messages/inbox",       headers=h("Parent")))
check("SpEd      GET /sped/ieps",                  requests.get(f"{BASE}/sped/ieps",                           headers=h("SpEdCoordinator")))
check("Principal GET /scheduling/sections",         requests.get(f"{BASE}/scheduling/sections",                headers=h("Principal")))
check("District  GET /budget/budgets",              requests.get(f"{BASE}/budget/budgets",                     headers=h("DistrictAdmin")))

# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "="*55)
passed = sum(1 for s, _ in results if s == "PASS")
failed = sum(1 for s, _ in results if s == "FAIL")
total  = len(results)
pct    = round(passed / total * 100) if total else 0
print(f"  TOTAL : {total}")
print(f"  PASSED: {passed} ({pct}%)")
print(f"  FAILED: {failed}")
print("="*55)
if failed:
    print("\nFailed tests:")
    for s, l in results:
        if s == "FAIL": print(f"  - {l}")
print()
sys.exit(0 if failed == 0 else 1)
