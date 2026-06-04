"""Test C6 -- District Documents RAG"""
import requests

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

    # List categories
    r = requests.get(f"{BASE}/district-docs/categories", headers=headers)
    print(f"\n[Categories] Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Role: {data['your_role']}")
        print(f"  Accessible categories: {list(data['your_accessible_categories'].keys())}")

    # Query with no docs uploaded (expect graceful empty response)
    r2 = requests.post(
        f"{BASE}/district-docs/query",
        json={"question": "What is the district policy on excused absences?"},
        headers=headers
    )
    print(f"\n[Query - No Docs] Status: {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        print(f"  Success      : {data2['success']}")
        print(f"  Sources used : {data2['sources_used']}")
        print(f"  Answer       : {data2['answer'][:200]}")

    # Role-access test: invalid category
    r3 = requests.post(
        f"{BASE}/district-docs/query",
        json={
            "question": "What are the IEP procedures?",
            "doc_category": "invalid_cat"
        },
        headers=headers
    )
    print(f"\n[Invalid Category] Status: {r3.status_code}")
    if r3.status_code == 200:
        data3 = r3.json()
        print(f"  Success: {data3['success']} | Answer: {data3['answer'][:150]}")

    # Valid category query
    r4 = requests.post(
        f"{BASE}/district-docs/query",
        json={
            "question": "What are the IEP annual review requirements?",
            "doc_category": "compliance"
        },
        headers=headers
    )
    print(f"\n[Compliance Category Query] Status: {r4.status_code}")
    if r4.status_code == 200:
        data4 = r4.json()
        print(f"  Success      : {data4['success']}")
        print(f"  Sources used : {data4['sources_used']}")
        print(f"  Answer       : {data4['answer'][:200]}")

    print("\nC6 test complete.")