"""图纸识读接口：五维度结构化输出（SSE 逐维度推送）。"""
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..config import get_settings
from ..core.sse import SSE_HEADERS, done, error, pack
from ..schemas import OcrResponse
from ..services import vision

router = APIRouter(prefix="/api", tags=["vision"])

DIMS = [
    ("view", "视图结构"),
    ("size", "尺寸与公差"),
    ("roughness", "表面粗糙度"),
    ("material", "材料推断"),
    ("process", "加工工艺建议"),
]

OCR_PROMPT = (
    "请把这张图片中的机械课程题目完整转录为文字，保留公式、数值与单位，"
    "不要解答，只输出题目原文。若图片不是题目，输出「无法识别为题目」。"
)


@router.post("/vision")
async def recognize(file: UploadFile = File(...)):
    settings = get_settings()
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="仅支持 JPG / PNG / WEBP 图片")

    blob = await file.read()
    if len(blob) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"图片超过 {settings.max_upload_mb}MB")

    async def gen():
        try:
            result = await vision.recognize(blob, file.content_type or "image/jpeg")
        except vision.VisionNotConfigured as exc:
            yield error(str(exc), "vision_not_configured")
            return
        except ValueError as exc:
            yield error(str(exc), "invalid_image")
            return
        except Exception as exc:  # noqa: BLE001
            yield error(f"图纸识读失败：{exc}", "vision_error")
            return

        for key, title in DIMS:
            yield pack({
                "type": "dimension",
                "key": key,
                "title": title,
                "content": result.get(key, ""),
                "confidence": result.get("confidence", "medium"),
            })
        yield pack({"type": "meta", "notes": result.get("notes", "")})
        yield done()

    return StreamingResponse(gen(), headers=SSE_HEADERS, media_type="text/event-stream")


@router.post("/ocr", response_model=OcrResponse)
async def ocr(file: UploadFile = File(...)):
    """把题目照片转成文字，供讲题链路复用。"""
    blob = await file.read()
    settings = get_settings()
    if len(blob) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="图片过大")
    try:
        result = await vision.recognize_text(blob, file.content_type or "image/jpeg", OCR_PROMPT)
    except vision.VisionNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"识别失败：{exc}")
    return OcrResponse(text=result)
