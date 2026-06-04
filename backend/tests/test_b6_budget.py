"""
B6 Budget test suite.
Run with: python tests/test_b6_budget.py
"""

import sys
import requests
from datetime import date, timedelta
from decimal import Decimal

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


def h(token): return {"Authorization": f"Bearer {token}"}


def check(label, resp, expected):
    if resp.status_code == expected:
        print(f"[PASS] {label} => {resp.status_code}")
        return resp.json() if resp.content else {}
    print(f"[FAIL] {label} => expected {expected}, got {resp.status_code}: {resp.text[:300]}")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("B6 Budget Tests")
    print("=" * 60)

    token = login()

    # 1. Create fiscal year
    fy = check("Create fiscal year", requests.post(
        f"{BASE_URL}/budget/fiscal-years",
        json={
            "name": "2025-2026",
            "start_date": "2025-07-01",
            "end_date": "2026-06-30",
            "is_current": True,
        },
        headers=h(token),
    ), 201)
    if not fy: sys.exit(1)
    fy_id = fy["id"]
    print(f"[INFO] Fiscal year id: {fy_id}")

    # 2. List fiscal years
    check("List fiscal years", requests.get(
        f"{BASE_URL}/budget/fiscal-years", headers=h(token)
    ), 200)

    # 3. Get current fiscal year
    check("Get current fiscal year", requests.get(
        f"{BASE_URL}/budget/fiscal-years/current", headers=h(token)
    ), 200)

    # 4. Create budget with two line items
    budget = check("Create budget", requests.post(
        f"{BASE_URL}/budget/budgets",
        json={
            "fiscal_year_id": fy_id,
            "name": "Westlake High School 2025-2026",
            "description": "Annual operating budget",
            "status": "draft",
            "total_allocated": "1500000.00",
            "line_items": [
                {
                    "category": "personnel",
                    "name": "Teaching Staff Salaries",
                    "allocated_amount": "900000.00",
                },
                {
                    "category": "supplies",
                    "name": "Classroom Supplies",
                    "allocated_amount": "50000.00",
                },
                {
                    "category": "technology",
                    "name": "Technology Infrastructure",
                    "allocated_amount": "120000.00",
                },
            ],
        },
        headers=h(token),
    ), 201)
    if not budget: sys.exit(1)
    budget_id   = budget["id"]
    personnel_id = budget["line_items"][0]["id"]
    supplies_id  = budget["line_items"][1]["id"]
    tech_id      = budget["line_items"][2]["id"]
    print(f"[INFO] Budget id: {budget_id}")

    # 5. Get budget
    check("Get budget", requests.get(
        f"{BASE_URL}/budget/budgets/{budget_id}", headers=h(token)
    ), 200)

    # 6. List budgets
    check("List budgets", requests.get(
        f"{BASE_URL}/budget/budgets", headers=h(token)
    ), 200)

    # 7. Update budget status to active
    check("Activate budget", requests.patch(
        f"{BASE_URL}/budget/budgets/{budget_id}",
        json={"status": "active"},
        headers=h(token),
    ), 200)

    # 8. Add a line item
    new_item = check("Add SpEd line item", requests.post(
        f"{BASE_URL}/budget/budgets/{budget_id}/line-items",
        json={
            "category": "special_education",
            "name": "SpEd Support Services",
            "allocated_amount": "200000.00",
        },
        headers=h(token),
    ), 201)

    # 9. Update line item
    check("Update supplies allocation", requests.patch(
        f"{BASE_URL}/budget/line-items/{supplies_id}",
        json={"allocated_amount": "60000.00", "notes": "Increased for new curriculum."},
        headers=h(token),
    ), 200)

    # 10. Add transactions
    check("Add personnel expense", requests.post(
        f"{BASE_URL}/budget/line-items/{personnel_id}/transactions",
        json={
            "transaction_type": "expense",
            "amount": "75000.00",
            "transaction_date": TODAY.strftime(FMT),
            "vendor": "Westlake Payroll",
            "description": "Monthly payroll - July 2025",
            "reference_number": "PAY-2025-07",
        },
        headers=h(token),
    ), 201)

    check("Add supplies expense", requests.post(
        f"{BASE_URL}/budget/line-items/{supplies_id}/transactions",
        json={
            "transaction_type": "expense",
            "amount": "5200.00",
            "transaction_date": TODAY.strftime(FMT),
            "vendor": "School Specialty",
            "description": "Back to school supplies order",
            "reference_number": "PO-2025-001",
        },
        headers=h(token),
    ), 201)

    check("Add tech expense", requests.post(
        f"{BASE_URL}/budget/line-items/{tech_id}/transactions",
        json={
            "transaction_type": "expense",
            "amount": "12500.00",
            "transaction_date": TODAY.strftime(FMT),
            "vendor": "Dell Technologies",
            "description": "Chromebook purchase - 50 units",
            "reference_number": "PO-2025-002",
        },
        headers=h(token),
    ), 201)

    # 11. Add a refund
    check("Add supplies refund", requests.post(
        f"{BASE_URL}/budget/line-items/{supplies_id}/transactions",
        json={
            "transaction_type": "refund",
            "amount": "200.00",
            "transaction_date": TODAY.strftime(FMT),
            "vendor": "School Specialty",
            "description": "Returned damaged items",
        },
        headers=h(token),
    ), 201)

    # 12. Generate linear forecast
    forecasts = check("Generate linear forecast", requests.post(
        f"{BASE_URL}/budget/budgets/{budget_id}/forecasts/linear",
        headers=h(token),
    ), 201)
    if forecasts:
        print(f"[INFO] Generated {len(forecasts)} forecast(s)")

    # 13. List forecasts
    check("List forecasts", requests.get(
        f"{BASE_URL}/budget/budgets/{budget_id}/forecasts", headers=h(token)
    ), 200)

    # 14. Manual forecast for tech
    check("Create manual forecast", requests.post(
        f"{BASE_URL}/budget/budgets/{budget_id}/forecasts",
        json={
            "line_item_id": tech_id,
            "forecast_method": "ai_generated",
            "forecasted_amount": "115000.00",
            "confidence_pct": "85.00",
            "scenario_label": "Base Case",
            "rationale": "Based on planned Q2 infrastructure upgrade.",
        },
        headers=h(token),
    ), 201)

    # 15. Budget overview
    overview = check("Get budget overview", requests.get(
        f"{BASE_URL}/budget/budgets/overview",
        params={"fiscal_year_id": fy_id},
        headers=h(token),
    ), 200)
    if overview:
        print(f"[INFO] Total allocated: ${overview['total_allocated']}")
        print(f"[INFO] Total spent:     ${overview['total_spent']}")
        print(f"[INFO] Utilization:     {overview['utilization_pct']}%")

    # 16. Delete draft budget (should fail — status is active)
    resp = requests.delete(f"{BASE_URL}/budget/budgets/{budget_id}", headers=h(token))
    if resp.status_code == 409:
        print("[PASS] Delete active budget correctly rejected => 409")
    else:
        print(f"[FAIL] Expected 409, got {resp.status_code}")

    print()
    print("=" * 60)
    print("B6 Tests Complete")
    print("=" * 60)