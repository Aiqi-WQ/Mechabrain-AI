"""文本模型调用：DeepSeek（OpenAI 兼容协议），流式输出。"""
from collections.abc import AsyncIterator

import httpx

from ..config import get_settings


class ModelNotConfigured(RuntimeError):
    pass


async def stream_chat(messages: list[dict], temperature: float | None = None) -> AsyncIterator[str]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise ModelNotConfigured(
            "服务端未配置 DEEPSEEK_API_KEY。请在 backend/.env 填入密钥后重启服务。"
        )

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "stream": True,
        "temperature": settings.chat_temperature if temperature is None else temperature,
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    url = settings.deepseek_base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            if resp.status_code != 200:
                body = (await resp.aread()).decode("utf-8", "ignore")[:300]
                raise RuntimeError(f"文本模型调用失败（HTTP {resp.status_code}）：{body}")
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = eval_json(data)
                except ValueError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                piece = (choices[0].get("delta") or {}).get("content")
                if piece:
                    yield piece


def eval_json(raw: str) -> dict:
    import json

    return json.loads(raw)
