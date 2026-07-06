from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_uploadrejects_unsupported_type():
    r = client.post(
        "/upload",
        files={"file": ("x.docx", b"fake", "application/vnd.openxmlformats")},
        )
    assert r.status_code == 415
  

def test_search_rejects_empty_query():
    r = client.get("/search", params={"q": "   "})
    assert r.status_code == 422


    