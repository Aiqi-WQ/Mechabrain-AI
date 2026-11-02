"""接口冒烟测试：先把不需要密钥的三条路径守住。

运行：cd backend && python -m pytest -q
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_meta_hides_secrets():
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert set(data["capabilities"]) == {"chat", "vision", "rag"}
    assert "api_key" not in response.text.lower()


def test_chat_rejects_blank_question():
    response = client.post(
        "/api/chat",
        json={"mode": "tutor", "messages": [{"role": "user", "content": "   "}]},
    )
    assert response.status_code == 200
    assert "invalid_input" in response.text


def test_chat_rejects_overlong_question():
    response = client.post(
        "/api/chat",
        json={"mode": "tutor", "messages": [{"role": "user", "content": "轴" * 2100}]},
    )
    assert response.status_code == 200
    assert "invalid_input" in response.text


def test_vision_rejects_non_image():
    response = client.post(
        "/api/vision",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
