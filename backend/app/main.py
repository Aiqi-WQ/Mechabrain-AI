"""机小智 MechaBrain AI —— FastAPI 入口。

启动：uvicorn app.main:app --reload --port 8000
接口：/api/chat /api/rag /api/vision /api/ocr /api/meta /api/health
"""
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import chat, rag, vision
from .config import get_settings
from .services import retriever

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="面向机械类专业学生的 AI 学习与工程图纸助手",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _hits[ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_min:
            return JSONResponse({"detail": "请求过于频繁，请稍后再试"}, status_code=429)
        bucket.append(now)
    return await call_next(request)


app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(vision.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": settings.deepseek_model,
        "vision_model": settings.vision_model,
        "rag_backend": retriever.backend_name(),
    }


@app.get("/api/meta")
def meta():
    """暴露能力开关，前端据此提示用户，不含任何密钥。"""
    backend = retriever.backend_name()
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "capabilities": {
            "chat": bool(settings.deepseek_api_key),
            "vision": bool(settings.dashscope_api_key),
            "rag": backend != "none",
        },
        "rag_backend": backend,
        "limits": {"max_upload_mb": settings.max_upload_mb},
        "disclaimer": "以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。",
    }


# 生产环境把前端构建产物挂到根路径（web/dist）
dist = Path(__file__).resolve().parents[2] / "web" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")
