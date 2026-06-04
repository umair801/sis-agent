"""Test C4 -- Scenario Forecasting Agent"""
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


def test_forecast(token: str, forecast_type: str):
    r = requests.post(
        f"{BASE}/forecasts/run",
        json={"forecast_type": forecast_type},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\n[{forecast_type}]")
    print(f"  Status  : {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Success : {data.get('success')}")
        print(f"  Title   : {data.get('title')}")
        print(f"  Trend   : {data.get('trend')}")
        print(f"  Narrative: {data.get('narrative', '')[:300]}")
        print(f"  ms      : {data.get('duration_ms')}")
    else:
        print(f"  Error   : {r.text[:300]}")


if __name__ == "__main__":
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("Token obtained.")

    r = requests.get(f"{BASE}/forecasts/types", headers=headers)
    print(f"\n[Forecast Types] {r.json()['forecast_types']}")

    test_forecast(token, "enrollment")
    test_forecast(token, "budget")
    test_forecast(token, "attendance_trend")

    # Invalid type test
    r_bad = requests.post(
        f"{BASE}/forecasts/run",
        json={"forecast_type": "invalid_type"},
        headers=headers
    )
    print(f"\n[Invalid Type] Status: {r_bad.status_code} | success: {r_bad.json().get('success')}")