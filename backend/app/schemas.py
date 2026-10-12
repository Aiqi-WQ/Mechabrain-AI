"""请求模型。"""
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=0, max_length=8000)


class ChatRequest(BaseModel):
    mode: Literal["tutor", "rag", "variant", "drawing"] = "tutor"
    messages: list[Message] = Field(min_length=1, max_length=12)
    context: str | None = None


class RagRequest(BaseModel):
    question: str
    book: str | None = None
    chapter: str | None = None


class OcrResponse(BaseModel):
    text: str
