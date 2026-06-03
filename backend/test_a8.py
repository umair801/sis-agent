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
    "query": "Which students are at risk of chronic absenteeism this semester?",
    "module": "attendance"
}).encode()

req2 = urllib.request.Request(
    "http://localhost:8000/api/v1/ai/query",
    data=query_data,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
)
result = json.loads(urllib.request.urlopen(req2).read().decode())
print("Response:", result["response"][:300])
print("Intent:", result["intent"])
print("Target Agent:", result["target_agent"])
print("Module:", result["module"])
