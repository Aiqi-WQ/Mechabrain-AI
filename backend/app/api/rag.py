"""教材问答接口：检索 Top-K 切片，答案末尾回标出处。"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..core.security import InputRejected, check_question
from ..core.sse import SSE_HEADERS, delta, done, error, pack
from ..schemas import RagRequest
from ..services import prompts, retriever
from ..services.llm import ModelNotConfigured, stream_chat

router = APIRouter(prefix="/api", tags=["rag"])


@router.post("/rag")
async def rag(req: RagRequest):
    try:
        question = check_question(req.question)
    except InputRejected as exc:
        return StreamingResponse(_single(error(str(exc), "invalid_input")),
                                 headers=SSE_HEADERS, media_type="text/event-stream")

    backend = retriever.backend_name()
    if backend == "none":
        async def empty():
            yield error(
                "知识库尚未构建。请把教材 PDF 放入 backend/data/textbooks/，"
                "运行 `python scripts/ingest.py` 后重启服务。",
                "index_missing",
            )
        return StreamingResponse(empty(), headers=SSE_HEADERS, media_type="text/event-stream")

    hits = retriever.retrieve(question, book=req.book, chapter=req.chapter)
    if not hits:
        async def no_hit():
            yield delta(
                "资料中没有检索到与该问题相关的章节。可以换一种问法，"
                "或在左侧选择更接近的章节后重试。"
            )
            yield done()
        return StreamingResponse(no_hit(), headers=SSE_HEADERS, media_type="text/event-stream")

    messages = [
        {"role": "system", "content": prompts.RAG},
        {"role": "system", "content": "【资料】\n" + retriever.format_context(hits)},
        {"role": "user", "content": question},
    ]
    cites = [
        {"book": h.get("book", ""), "chapter": h.get("chapter", ""), "page": h.get("page", "")}
        for h in hits
    ]

    async def gen():
        try:
            async for piece in stream_chat(messages):
                yield delta(piece)
            yield pack({"type": "cites", "items": cites, "backend": backend})
            yield done()
        except ModelNotConfigured as exc:
            yield error(str(exc), "model_not_configured")
        except Exception as exc:  # noqa: BLE001
            yield error(f"生成失败：{exc}", "upstream_error")

    return StreamingResponse(gen(), headers=SSE_HEADERS, media_type="text/event-stream")


async def _single(event: str):
    yield event
