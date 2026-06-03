import urllib.request
import json
import uuid

# Login
login_data = json.dumps({
    "email": "admin@westlake.edu",
    "password": "admin123",
    "tenant_slug": "westlake"
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/api/v1/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
print("Token obtained")

# Build multipart upload
boundary = uuid.uuid4().hex
with open("test_policy.txt", "rb") as f:
    file_bytes = f.read()

body = (
    ("--" + boundary + "\r\n").encode() +
    ("Content-Disposition: form-data; name=\"file\"; filename=\"test_policy.txt\"\r\n").encode() +
    ("Content-Type: text/plain\r\n\r\n").encode() +
    file_bytes +
    ("\r\n--" + boundary + "\r\n").encode() +
    ("Content-Disposition: form-data; name=\"doc_type\"\r\n\r\n").encode() +
    ("policy\r\n").encode() +
    ("--" + boundary + "--\r\n").encode()
)

req2 = urllib.request.Request(
    "http://localhost:8000/api/v1/rag/upload",
    data=body,
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "multipart/form-data; boundary=" + boundary
    }
)
result = urllib.request.urlopen(req2).read()
print("Upload result:", result.decode())
