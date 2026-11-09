# 机小智 MechaBrain AI · 后端

FastAPI 服务，提供四类能力：AI 讲题、教材问答（RAG）、变式出题、机械图纸识读。

## 目录

```
backend/
├─ app/
│  ├─ main.py            # 应用入口、CORS、限流、静态托管
│  ├─ config.py          # pydantic-settings 读 .env
│  ├─ schemas.py         # 请求 / 响应模型
│  ├─ api/
│  │  ├─ chat.py         # POST /api/chat      讲题 / 变式 / 图纸追问
│  │  ├─ rag.py          # POST /api/rag       教材问答
│  │  └─ vision.py       # POST /api/vision    五维度识读；POST /api/ocr 题目转录
│  ├─ core/
│  │  ├─ sse.py          # 统一事件协议 delta / dimension / cites / done / error
│  │  └─ security.py     # 输入过滤、限流常量、拒答兜底文案
│  └─ services/
│     ├─ llm.py          # DeepSeek 流式调用
│     ├─ vision.py       # qwen3-vl-plus 识读与 OCR
│     ├─ retriever.py    # Chroma / 内置 BM25 双后端
│     └─ prompts.py      # 四类任务的 system prompt
├─ scripts/ingest.py     # 教材 PDF → 章节 → 切片 → index.json
├─ data/                 # 教材与索引（不入库）
└─ tests/test_api.py     # 冒烟测试
```

## 起服务

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # 填入 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY
uvicorn app.main:app --reload --port 8000
```

打开 http://127.0.0.1:8000/docs 可直接在 Swagger 里试接口。

## 没有密钥时会发生什么

服务照常启动，`/api/health`、`/api/meta` 正常返回；调用 AI 的接口会返回一条

```json
{"type": "error", "code": "model_not_configured", "message": "服务端未配置 DEEPSEEK_API_KEY…"}
```

前端把这条消息原样显示为提示，不会假装已经答出来了。

## 教材入库

```bash
pip install -r requirements-ingest.txt
# 把 PDF 放进 data/textbooks/
python scripts/ingest.py
# 需要向量检索时：
python scripts/ingest.py --chroma
```

不装 `chromadb` 时 `retriever` 自动降级到内置 BM25（中文按二元切分），检索照样能用，只是召回质量弱于向量检索。

## 密钥从哪来

| 变量 | 用途 | 申请入口 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 讲题、问答、变式 | https://platform.deepseek.com/api_keys |
| `DASHSCOPE_API_KEY` | 图纸识读、题目 OCR | https://bailian.console.aliyun.com |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` | bge-m3 向量化（可选） | 任意 OpenAI 兼容的 embedding 服务 |

密钥只存在服务端 `.env`，前端构建产物里不含任何 key。
