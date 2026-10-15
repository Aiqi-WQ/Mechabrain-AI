"""对话接口：AI 讲题 / 变式出题 / 教材问答 / 图纸追问，统一 SSE 流式输出。"""
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..core.security import InputRejected, check_question
from ..core.sse import SSE_HEADERS, delta, done, error, pack
from ..schemas import ChatRequest
from ..services import prompts, retriever
from ..services.llm import ModelNotConfigured, stream_chat

router = APIRouter(prefix="/api", tags=["chat"])

SYSTEM_BY_MODE = {
    "tutor": prompts.TUTOR,
    "rag": prompts.RAG,
    "variant": prompts.VARIANT,
    "drawing": prompts.DRAWING_CHAT,
}


@router.post("/chat")
async def chat(req: ChatRequest):
    last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    try:
        question = check_question(last_user)
    except InputRejected as exc:
        return StreamingResponse(
            _single(error(str(exc), "invalid_input")), headers=SSE_HEADERS, media_type="text/event-stream"
        )

    system = SYSTEM_BY_MODE[req.mode]
    messages: list[dict] = [{"role": "system", "content": system}]

    if req.mode == "rag":
        hits = retriever.retrieve(question)
        if hits:
            messages.append({
                "role": "system",
                "content": "【资料】\n" + retriever.format_context(hits),
            })

    if req.context:
        messages.append({"role": "system", "content": "【图纸识读结果】\n" + req.context[:4000]})

    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    message_id = uuid.uuid4().hex[:12]

    async def gen():
        try:
            async for piece in stream_chat(messages):
                yield delta(piece)
            yield done(message_id)
        except ModelNotConfigured as exc:
            yield error(str(exc), "model_not_configured")
        except RuntimeError as exc:
            yield error(str(exc), "upstream_error")
        except Exception:  # noqa: BLE001 - 不允许把内部堆栈吐给前端
            yield error("生成失败，请稍后重试。", "internal_error")

    return StreamingResponse(gen(), headers=SSE_HEADERS, media_type="text/event-stream")


async def _single(event: str):
    yield event
