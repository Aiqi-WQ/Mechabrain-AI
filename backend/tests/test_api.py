"""接口冒烟测试 + 检索链路回归测试。

运行：cd backend && python -m pytest -q
"""
from fastapi.testclient import TestClient

from app.main import app
from app.services import retriever, vision

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


def test_textbooks_endpoint_lists_real_chapters():
    """目录接口返回的必须是实际入库的教材，前端章节树据此渲染。"""
    response = client.get("/api/textbooks")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] != "none"
    books = data["books"]
    assert books, "示例教材应当已入库，请先运行 python scripts/ingest.py"
    titles = [book["book"] for book in books]
    assert "机械原理" in titles, f"书名归一化失败：{titles}"
    chapters = books[0]["chapters"]
    assert chapters and all(chapter["chunks"] > 0 for chapter in chapters)


def test_chapter_filter_still_retrieves():
    """点章节限定后必须还能召回，这条锁住「一点章节就返回没检索到」的回归。"""
    hits = retriever.retrieve("自由度", book="机械原理", chapter="第1章")
    assert hits, "章节限定检索返回空，book/chapter 匹配逻辑有问题"
    hits_full = retriever.retrieve("自由度", book="机械原理", chapter="第1章 平面机构的自由度")
    assert hits_full, "章节标题全称也应能匹配"


def test_chapter_filter_rejects_wrong_chapter():
    hits = retriever.retrieve("自由度", book="机械原理", chapter="第9章")
    assert hits == [], "不存在的章节不应召回任何切片"


def test_cites_dedupe_by_chapter():
    hits = [
        {"book": "机械原理", "chapter": "第1章 平面机构的自由度", "page": "p.3", "text": "a"},
        {"book": "机械原理", "chapter": "第1章 平面机构的自由度", "page": "p.3", "text": "b"},
        {"book": "机械原理", "chapter": "第2章 齿轮机构与传动比", "page": "p.9", "text": "c"},
    ]
    cites = retriever.dedupe_cites(hits)
    assert len(cites) == 2


def test_vision_normalize_keeps_per_dimension_confidence():
    raw = """```json
    {
      "view": {"content": "两个视图", "confidence": "high"},
      "size": {"content": "φ35", "confidence": "medium"},
      "roughness": {"content": "Ra 3.2", "confidence": "low"},
      "material": {"content": "45 钢", "confidence": "low"},
      "process": {"content": "粗车-精车", "confidence": "medium"},
      "notes": "Ra 代号偏小"
    }
    ```"""
    result = vision.normalize(raw)
    confidences = {key: item["confidence"] for key, item in result["dims"].items()}
    assert confidences["view"] == "high"
    assert confidences["roughness"] == "low"
    assert len(set(confidences.values())) > 1, "各维度置信度不应是同一个全局值"
    assert result["notes"] == "Ra 代号偏小"

