"""
B7 Communication test suite.
Run with: python tests/test_b7_communication.py
"""

import sys
import requests

BASE_URL = "http://localhost:8000/api/v1"


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
    print("B7 Communication Tests")
    print("=" * 60)

    token = login()

    # 1. Create draft announcement
    ann = check("Create announcement (draft)", requests.post(
        f"{BASE_URL}/communication/announcements",
        json={
            "title": "Back to School Night - August 28",
            "body": "Join us for Back to School Night on August 28 at 6pm in the main gymnasium. Meet your teachers and learn about this year's curriculum.",
            "audience": "parents",
            "status": "draft",
            "is_urgent": False,
        },
        headers=h(token),
    ), 201)
    if not ann: sys.exit(1)
    ann_id = ann["id"]
    print(f"[INFO] Announcement id: {ann_id}")

    # 2. Create urgent announcement
    urgent_ann = check("Create urgent announcement", requests.post(
        f"{BASE_URL}/communication/announcements",
        json={
            "title": "School Closed Tomorrow - Weather Emergency",
            "body": "Due to severe weather conditions, school will be closed tomorrow. Remote learning is in effect. Check your email for class links.",
            "audience": "all",
            "status": "published",
            "is_urgent": True,
        },
        headers=h(token),
    ), 201)

    # 3. List announcements
    check("List all announcements", requests.get(
        f"{BASE_URL}/communication/announcements", headers=h(token)
    ), 200)

    # 4. List by status
    check("List published announcements", requests.get(
        f"{BASE_URL}/communication/announcements?status=published",
        headers=h(token),
    ), 200)

    # 5. Get single announcement
    check("Get announcement by ID", requests.get(
        f"{BASE_URL}/communication/announcements/{ann_id}", headers=h(token)
    ), 200)

    # 6. Update announcement to published
    check("Publish announcement", requests.patch(
        f"{BASE_URL}/communication/announcements/{ann_id}",
        json={"status": "published"},
        headers=h(token),
    ), 200)

    # 7. Dispatch notification (in_app channel)
    notify_result = check("Dispatch in-app notification", requests.post(
        f"{BASE_URL}/communication/announcements/{ann_id}/notify",
        json={"announcement_id": str(ann_id), "channels": ["in_app"]},
        headers=h(token),
    ), 200)
    if notify_result:
        print(f"[INFO] Notifications: {notify_result['total']} sent, {notify_result['failed']} failed")

    # 8. Dispatch email notification
    check("Dispatch email notification", requests.post(
        f"{BASE_URL}/communication/announcements/{ann_id}/notify",
        json={"announcement_id": str(ann_id), "channels": ["email"]},
        headers=h(token),
    ), 200)

    # 9. Get notification logs
    logs = check("Get notification logs", requests.get(
        f"{BASE_URL}/communication/notifications/logs?announcement_id={ann_id}",
        headers=h(token),
    ), 200)
    if logs:
        print(f"[INFO] Log entries: {len(logs)}")

    # 10. Send direct message
    msg = check("Send direct message", requests.post(
        f"{BASE_URL}/communication/messages",
        json={
            "recipient_id": str(ann["created_by"]),
            "subject": "Question about Back to School Night",
            "body": "Will there be parking available for the Back to School Night event?",
        },
        headers=h(token),
    ), 201)

    # 11. Get inbox
    inbox = check("Get inbox", requests.get(
        f"{BASE_URL}/communication/messages/inbox", headers=h(token)
    ), 200)

    # 12. Get sent messages
    check("Get sent messages", requests.get(
        f"{BASE_URL}/communication/messages/sent", headers=h(token)
    ), 200)

    # 13. Mark message read
    if msg:
        check("Mark message as read", requests.patch(
            f"{BASE_URL}/communication/messages/{msg['id']}/read",
            headers=h(token),
        ), 200)

    # 14. Reply to message
    if msg:
        check("Reply to message", requests.post(
            f"{BASE_URL}/communication/messages",
            json={
                "recipient_id": str(ann["created_by"]),
                "subject": "Re: Question about Back to School Night",
                "body": "Yes, the main parking lot will be open from 5:30pm.",
                "parent_message_id": str(msg["id"]),
            },
            headers=h(token),
        ), 201)

    # 15. Get message thread
    if msg:
        check("Get message thread", requests.get(
            f"{BASE_URL}/communication/messages/{msg['id']}/thread",
            headers=h(token),
        ), 200)

    # 16. Get notification preferences
    check("Get notification preferences", requests.get(
        f"{BASE_URL}/communication/preferences", headers=h(token)
    ), 200)

    # 17. Update notification preferences
    check("Update notification preferences", requests.patch(
        f"{BASE_URL}/communication/preferences",
        json={
            "sms_enabled": True,
            "phone_number": "+15551234567",
            "urgent_sms": True,
        },
        headers=h(token),
    ), 200)

    # 18. Archive announcement
    check("Archive announcement", requests.patch(
        f"{BASE_URL}/communication/announcements/{ann_id}",
        json={"status": "archived"},
        headers=h(token),
    ), 200)

    print()
    print("=" * 60)
    print("B7 Tests Complete")
    print("=" * 60)