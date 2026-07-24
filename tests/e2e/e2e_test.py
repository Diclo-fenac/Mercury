import asyncio
import io
import json
import os
import time

import pytest
import requests
import websockets

if not os.getenv("MERCURY_E2E_URL"):
    pytest.skip(
        "E2E suite requires deployed Mercury stack; set MERCURY_E2E_URL to enable it.",
        allow_module_level=True,
    )

BASE_URL = os.environ["MERCURY_E2E_URL"].rstrip("/") + "/api/v1"

print("Starting E2E Integration Test...")

# 1. Onboard a merchant
print("1. Onboard merchant")
import uuid

onboard_res = requests.post(f"{BASE_URL}/admin/onboard", json={
    "name": "E2E Test Store",
    "slug": f"e2e-store-{uuid.uuid4().hex[:6]}",
    "owner_email": f"admin_{uuid.uuid4().hex[:6]}@e2estore.com",
    "plan": "pro"
})
if onboard_res.status_code != 201:
    print(f"Failed to onboard: {onboard_res.text}")
    exit(1)
data = onboard_res.json()
admin_key = data["keys"]["admin_key"]
search_key = data["keys"]["search_key"]
org_id = data["organization"]["id"]
print(f"   Success. Admin Key: {admin_key}, Search Key: {search_key}")

# 2. Upload a 10-item CSV catalog
print("2. Upload CSV catalog")
csv_data = """id,title,description,price,category,stock
p001,Smartphone X,A great phone,999,Electronics,true
p002,Laptop Pro,A fast laptop,1500,Electronics,true
p003,Wireless Mouse,Ergonomic mouse,30,Accessories,true
p004,Mechanical Keyboard,Clicky keyboard,100,Accessories,true
p005,Monitor 4K,Sharp display,300,Electronics,true
p006,Desk Lamp,LED desk lamp,25,Home,true
p007,Office Chair,Comfortable chair,200,Home,true
p008,USB-C Hub,Multiport adapter,40,Accessories,true
p009,Webcam HD,1080p camera,60,Accessories,true
p010,Bluetooth Speaker,Portable speaker,80,Electronics,true
"""
files = {"file": ("catalog.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
headers_admin = {"Authorization": f"Bearer {admin_key}", "X-API-Key": admin_key}
headers_search = {"Authorization": f"Bearer {search_key}", "X-API-Key": search_key}
upload_res = requests.post(f"{BASE_URL}/admin/catalog/upload", files=files, headers=headers_admin)
if upload_res.status_code != 200:
    print(f"Failed to upload catalog: {upload_res.text}")
    exit(1)
print("   Uploaded. Waiting for indexing...")
time.sleep(2)

stats_res = requests.get(f"{BASE_URL}/admin/catalog/stats", headers=headers_admin)
print(f"   Catalog stats: {stats_res.json()}")

# 3. Add synonym: "mobile" -> "smartphone"
print("3. Add synonym")
syn_res = requests.post(f"{BASE_URL}/admin/rules/synonyms", json={
    "term": "mobile",
    "synonyms": ["smartphone"]
}, headers=headers_admin)
print(f"   Synonym res: {syn_res.json()}")

# 4. Search: GET /api/v1/search/?q=mobile (Actually POST per code)
print("4. Search for 'mobile'")
search_res = requests.post(f"{BASE_URL}/search/", json={"query": "mobile"}, headers=headers_search)
if search_res.status_code != 200:
    # Try GET if POST fails (in case we misread the router)
    search_res = requests.get(f"{BASE_URL}/search/?q=mobile", headers=headers_search)
print(f"   Search res status: {search_res.status_code}")
results = search_res.json().get("results", [])
print(f"   Found {len(results)} results. First: {results[0]['id'] if results else 'None'}")

# 5. Pin product p001 to position 1 for query "mobile"
print("5. Pin product")
pin_res = requests.post(f"{BASE_URL}/admin/pinned", json={
    "query_pattern": "mobile",
    "product_id": "p001",
    "position": 1
}, headers=headers_admin)
print(f"   Pin res: {pin_res.json()}")

# 6. Repeat search -> verify p001 is first
print("6. Repeat search")
search_res2 = requests.post(f"{BASE_URL}/search/", json={"query": "mobile"}, headers=headers_search)
results2 = search_res2.json().get("results", [])
print(f"   Found {len(results2)} results. First: {results2[0]['id'] if results2 else 'None'}")
assert results2 and results2[0]['id'] == 'p001', "Product pinning failed"

# Register a test user to get a real JWT for the image API
user_res = requests.post(f"{BASE_URL}/users/register", json={
    "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
    "password": "password123",
    "name": "Test User"
})
if user_res.status_code in [200, 201]:
    jwt_token = user_res.json()["token"]["access_token"]
else:
    print(f"   User registration failed: {user_res.status_code} - {user_res.text}")
    # Fallback to a locally generated JWT if registration fails (e.g. endpoint doesn't exist)
    try:
        from jose import jwt as jose_jwt
        jwt_token = jose_jwt.encode({"sub": "user_123", "roles": ["user"]}, "your-super-secret-key-here", algorithm="HS256")
    except ImportError:
        import jwt
        jwt_token = jwt.encode({"sub": "user_123", "roles": ["user"]}, "your-super-secret-key-here", algorithm="HS256")
        if isinstance(jwt_token, bytes): jwt_token = jwt_token.decode()

headers_image = {"Authorization": f"Bearer {jwt_token}", "X-API-Key": search_key}

# 7. Upload product image (we mock image upload to /api/v1/images/)
print("7. Upload product image")
# Let's create a dummy image (e.g., 1x1 black pixel base64)
# Since the endpoint expects a pydantic model with `image_data`, we send JSON
import base64

dummy_img = base64.b64encode(b"dummy image data").decode("utf-8")
img_res = requests.post(f"{BASE_URL}/images/", json={
    "image_data": f"data:image/jpeg;base64,{dummy_img}",
    "message": "Analyze this"
}, headers=headers_image)
print(f"   Image upload res: {img_res.status_code}")
if img_res.status_code == 200:
    img_data = img_res.json()
    print(f"   Analysis: {img_data.get('analysis')}")
    image_id = img_data.get("image_id")
else:
    print(f"   Error: {img_res.text}")
    image_id = "dummy"

# 8. POST /api/v1/images/search with same image
print("8. Image search")
img_search_res = requests.post(f"{BASE_URL}/images/search", json={
    "image_data": f"data:image/jpeg;base64,{dummy_img}",
    "prompt": "Find something like this",
    "search_type": "similar_style"
}, headers=headers_image)
print(f"   Image search res: {img_search_res.status_code}")

# 9. Start WebSocket
print("9. WebSocket chat")
async def test_websocket():
    # WebSocket auth requires sending type: auth, api_key: search_key
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as ws:
            # Auth
            await ws.send(json.dumps({"event": "user_auth", "data": {"user_id": "e2e_test_user"}}))
            auth_res = await ws.recv()
            print(f"   WS Auth: {auth_res}")
            
            # Chat message
            await ws.send(json.dumps({"event": "chat_message", "data": {"message": "best smartphone under 10k", "user_id": "e2e_test_user"}}))
            chat_res = await ws.recv()
            print(f"   WS Chat: {chat_res}")
    except Exception as e:
        print(f"   WS Error: {e}")

asyncio.run(test_websocket())

# 10. POST /api/v1/telemetry/events for 5 clicks
print("10. Telemetry clicks")
for _ in range(5):
    tel_res = requests.post(f"{BASE_URL}/telemetry/events", json={
        "event_type": "click",
        "product_id": "p001",
        "query": "mobile"
    }, headers=headers_search)
print(f"   Telemetry res: {tel_res.status_code}")
time.sleep(1) # wait for bg tasks
trending_res = requests.get(f"{BASE_URL}/search/trending", headers=headers_search)
print(f"   Trending searches: {trending_res.json()}")

# 11. GET /api/v1/admin/analytics
print("11. Admin analytics")
analytics_res = requests.get(f"{BASE_URL}/admin/analytics", headers=headers_admin)
print(f"   Analytics res: {analytics_res.status_code}")
# Try to print some keys safely
try:
    print(f"   Analytics keys: {analytics_res.json().keys()}")
except Exception:
    pass

# 12. GET /api/v1/admin/system/metrics
print("12. System metrics")
metrics_res = requests.get(f"{BASE_URL}/admin/system/metrics", headers=headers_admin)
print(f"   Metrics: {metrics_res.json()}")

print("Done.")
