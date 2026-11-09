"""多模态图纸识读：qwen3-vl-plus（DashScope 兼容模式）。"""
import base64
import json

import httpx

from ..config import get_settings
from .prompts import VISION_SCHEMA_PROMPT

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


class VisionNotConfigured(RuntimeError):
    pass


class VisionResult(dict):
    """view / size / roughness / material / process / confidence / notes"""


async def recognize(image_bytes: bytes, mime: str) -> VisionResult:
    settings = get_settings()
    if not settings.dashscope_api_key:
        raise VisionNotConfigured(
            "服务端未配置 DASHSCOPE_API_KEY，图纸识读暂不可用。请在 backend/.env 填入密钥后重启。"
        )
    if mime not in ALLOWED_MIME:
        raise ValueError("仅支持 JPG / PNG / WEBP 图片")

    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": settings.vision_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": VISION_SCHEMA_PROMPT},
                ],
            }
        ],
        "temperature": 0.1,
    }
    headers = {"Authorization": f"Bearer {settings.dashscope_api_key}"}
    url = settings.vision_base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"多模态模型调用失败（HTTP {resp.status_code}）：{resp.text[:300]}")

    content = resp.json()["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content)
    return normalize(content)


async def recognize_text(image_bytes: bytes, mime: str, prompt: str) -> str:
    """把题目照片转成文字，供讲题链路复用。"""
    settings = get_settings()
    if not settings.dashscope_api_key:
        raise VisionNotConfigured("服务端未配置 DASHSCOPE_API_KEY，OCR 暂不可用。")
    if mime not in ALLOWED_MIME:
        raise ValueError("仅支持 JPG / PNG / WEBP 图片")

    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": settings.vision_model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        "temperature": 0.0,
    }
    headers = {"Authorization": f"Bearer {settings.dashscope_api_key}"}
    url = settings.vision_base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"OCR 调用失败（HTTP {resp.status_code}）：{resp.text[:200]}")
    content = resp.json()["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content)
    return str(content).strip()


def normalize(raw: str) -> VisionResult:
    """模型偶尔会带 ```json 包裹，这里做容错解析。"""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    start, end = text.find("{"), text.rfind("}")
    data: dict = {}
    if start != -1 and end != -1:
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            data = {}
    result = VisionResult(
        view=str(data.get("view", "")).strip(),
        size=str(data.get("size", "")).strip(),
        roughness=str(data.get("roughness", "")).strip(),
        material=str(data.get("material", "")).strip(),
        process=str(data.get("process", "")).strip(),
        confidence=str(data.get("confidence", "medium")).strip(),
        notes=str(data.get("notes", "")).strip(),
    )
    if not result["view"]:
        result["view"] = "模型未返回结构化结果，请重新上传更清晰的图纸照片。"
    return result
