"""Test C1 — NL Query Handler (debug version)"""
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


def test_nl_query(token: str, question: str, label: str):
    r = requests.post(
        f"{BASE}/query/ask",
        json={"question": question},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\n[{label}]")
    print(f"  Status : {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Intent : {data['intent']}  (confidence: {data.get('confidence', 'n/a')})")
        print(f"  Rows   : {data['row_count']}")
        print(f"  Summary: {data['summary']}")
        print(f"  SQL    : {data.get('sql', 'None')}")
        print(f"  Error  : {data.get('error', 'None')}")
        print(f"  ms     : {data['duration_ms']}")
    else:
        print(f"  Error  : {r.text[:300]}")


if __name__ == "__main__":
    token = get_token()
    print("Token obtained.")

    test_nl_query(token, "How many students are currently enrolled?", "Enrollment count")
    test_nl_query(token, "Show me students who were absent last week", "Absences last week")
    test_nl_query(token, "What is the total budget allocated this year?", "Budget total")