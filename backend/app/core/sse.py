"""SSE 输出与统一事件格式。

统一事件：data: {"type": "delta" | "dimension" | "cites" | "done" | "error", ...}
"""
import json
from typing import Any


DISCLAIMER = "以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。"


def pack(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def delta(text: str) -> str:
    return pack({"type": "delta", "text": text})


def done(message_id: str | None = None) -> str:
    return pack({"type": "done", "message_id": message_id, "disclaimer": DISCLAIMER})


def error(message: str, code: str = "upstream_error") -> str:
    return pack({"type": "error", "code": code, "message": message})


SSE_HEADERS = {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}
