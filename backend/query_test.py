import urllib.request
import json

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

query_data = json.dumps({
    "query": "What happens when a student has more than 3 unexcused absences?",
    "k": 3
}).encode()

req2 = urllib.request.Request(
    "http://localhost:8000/api/v1/rag/query",
    data=query_data,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
)
print(urllib.request.urlopen(req2).read().decode())
