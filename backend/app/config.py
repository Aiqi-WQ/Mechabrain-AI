"""全局配置：所有密钥从环境变量读取，禁止写入前端代码。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "机小智 MechaBrain AI"
    app_version: str = "1.0.0"
    debug: bool = False

    # 文本模型（DeepSeek，OpenAI 兼容协议）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    chat_temperature: float = 0.3

    # 多模态模型（通义 qwen-vl-max，DashScope 兼容模式）
    dashscope_api_key: str = ""
    vision_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    vision_model: str = "qwen-vl-max"

    # 向量检索
    chroma_enabled: bool = False
    chroma_dir: str = "./data/chroma"
    index_file: str = "./data/index.json"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "bge-m3"
    retrieve_top_k: int = 5

    # 服务
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_mb: int = 10
    rate_limit_per_min: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
