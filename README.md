# 机小智 MechaBrain AI

**面向机械类专业学生的 AI 学习与工程图纸助手。**

上传一张零件图，它按「视图结构 → 尺寸与公差 → 表面粗糙度 → 材料推断 → 加工工艺」五个维度讲清楚；翻教材卡住时，它从《机械原理》《工程材料》的章节切片里找依据再回答，并标注出处；题目不会做，它按「审题 → 考点 → 分步解答 → 易错点」讲完，再给一道同考点变式。

- 参赛：传智杯 · 全国高校 AI Web 开发挑战赛
- 作者：张照　绵阳城市学院 · 智能制造与工程学院 · 机械设计制造及其自动化 2025 级
- 形态：前后端分离的完整工程（Vue3 + TypeScript + Vite 前端，FastAPI 后端，SSE 流式输出）

---

## 在线演示

演示环境地址见比赛提交页；本地按下面的「快速开始」三条命令即可跑起来，**未配置 API Key 时服务照常启动**，AI 接口会返回明确的「未配置密钥」提示，不会伪造答案。

---

## 功能

| 功能 | 入口 | 说明 |
| --- | --- | --- |
| 图纸识读 | `/drawing` | 上传 JPG / PNG / WEBP 零件图，多模态模型按五个维度输出，逐维度流式返回 |
| 教材问答 | `/rag` | 左侧章节树限定检索范围，语义召回 Top-5 切片，答案末尾回标教材·章节·页码 |
| AI 讲题 | `/chat` | 拍照 OCR 或直接输入题目，四步讲题，附同考点变式 |
| 变式出题 | `/chat` | 指定知识点，生成三道由易到难的变式题，附参考答案与解析 |
| 学习记录 | `/records` | 按日期分组、按模式筛选、可展开查看与删除，存在浏览器本地 |

五个页面共用一套「工程图纸」视觉体系：24px 方格纸底、墨色正文、图纸蓝标注、强调红只用于关键标注。

## 技术栈

**前端**：Vue 3 · TypeScript · Vite 5 · Vue Router 4 · Pinia · TailwindCSS 3 · markdown-it
**后端**：FastAPI · Uvicorn · pydantic-settings · httpx
**AI**：DeepSeek-V3（对话）、qwen-vl-max（多模态识图 / OCR）、bge-m3（向量化，可选）
**检索**：Chroma（可选）＋ 内置 BM25（零依赖降级方案）
**传输**：SSE（`fetch` + `ReadableStream` 手动解析，支持 POST body 与中断）

## 架构

```
┌──────────────────────────────────────────────────────┐
│  浏览器                                                │
│  5 个页面 · Pinia（记录 / 图纸上下文）· SSE 逐字渲染      │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼──────────────────────────────┐
│  FastAPI（backend/app）                               │
│  /api/chat  /api/rag  /api/vision  /api/ocr           │
│  CORS · 限流 30 次/分 · 输入过滤 · 统一 SSE 事件协议     │
└───────┬───────────────┬───────────────┬──────────────┘
        │               │               │
   DeepSeek API    qwen-vl-max     Retriever
   （讲题/问答）    （识图/OCR）    ┌──────┴──────┐
                                  Chroma      BM25
                                  （可选）    （默认）
```

密钥全部在服务端 `.env`，前端构建产物中不含任何 key。

## 目录结构

```
机小智-MechaBrain/
├─ web/                      前端工程
│  ├─ src/
│  │  ├─ api.ts              SSE 解析与四条能力接口
│  │  ├─ router.ts           5 个路由
│  │  ├─ stores/app.ts       记录与图纸上下文（localStorage）
│  │  ├─ lib/markdown.ts     回答渲染
│  │  ├─ views/              Home / Drawing / Rag / Chat / Records
│  │  ├─ App.vue             导航与提示条
│  │  └─ style.css           设计令牌与方格纸底、Markdown 排版
│  ├─ tailwind.config.js     纸底 / 墨色 / 图纸蓝 / 强调红
│  └─ vite.config.ts         开发期把 /api 代理到 8000
├─ backend/                  FastAPI 服务
│  ├─ app/
│  │  ├─ main.py             入口、CORS、限流、静态托管
│  │  ├─ config.py           .env 配置
│  │  ├─ api/                chat / rag / vision 路由
│  │  ├─ core/               SSE 协议、输入过滤
│  │  └─ services/           llm / vision / retriever / prompts
│  ├─ scripts/ingest.py      教材 PDF → 章节 → 切片 → 索引
│  ├─ tests/test_api.py      冒烟测试（5 条）
│  ├─ requirements.txt
│  └─ .env.example
├─ Dockerfile                多阶段构建：前端打包 → 后端托管
├─ docker-compose.yml
└─ README.md
```

## 快速开始

前置：Node.js ≥ 18、Python ≥ 3.10。

### 1. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS / Linux：source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS / Linux：cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 与 DASHSCOPE_API_KEY
uvicorn app.main:app --reload --port 8000
```

接口文档：http://127.0.0.1:8000/docs

### 2. 前端

```bash
cd web
npm install
npm run dev
```

打开 http://localhost:5173 。开发期 `/api/*` 由 Vite 代理到 `127.0.0.1:8000`，不需要额外配 CORS。

### 3. 生产形态（单端口）

```bash
cd web && npm run build          # 产物在 web/dist
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`main.py` 检测到 `web/dist` 存在时，会把前端挂到根路径，8000 一个端口同时提供页面与接口。

## 配置

复制 `backend/.env.example` 为 `backend/.env`，按下表填写。**`.env` 已在 `.gitignore` 里，不会被提交。**

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 是 | 讲题、教材问答、变式出题；申请：https://platform.deepseek.com/api_keys |
| `DASHSCOPE_API_KEY` | 是 | 图纸识读与题目 OCR；申请：https://bailian.console.aliyun.com |
| `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat` |
| `VISION_MODEL` | 否 | 默认 `qwen-vl-max` |
| `CHROMA_ENABLED` | 否 | 默认 `false`，走内置 BM25 |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` | 否 | 启用 Chroma 时填 bge-m3 的 OpenAI 兼容 `/embeddings` 地址 |
| `CORS_ORIGINS` | 否 | 允许的前端来源，逗号分隔 |
| `MAX_UPLOAD_MB` | 否 | 上传图片上限，默认 10 |
| `RATE_LIMIT_PER_MIN` | 否 | 单 IP 每分钟请求上限，默认 30 |

### 没有密钥时的表现

这是刻意设计的降级路径，方便评委在没有 key 的机器上验证工程完整性：

- 服务正常启动，`/api/health`、`/api/meta`、`/docs` 都可用；
- 调用 `/api/chat`、`/api/rag`、`/api/vision` 会返回一条 SSE `error` 事件，`code=model_not_configured`，`message` 直接说明「服务端未配置 DEEPSEEK_API_KEY，请在 backend/.env 填入」；
- 前端把这条消息原样显示，不会假装已经生成答案；
- `/api/meta` 的 `capabilities` 会如实告诉你 chat / vision / rag 哪几项可用。

## 教材入库

```bash
cd backend
pip install -r requirements-ingest.txt     # PyMuPDF
# 把教材 PDF 放进 backend/data/textbooks/
python scripts/ingest.py                   # 产出 data/index.json
python scripts/ingest.py --chroma          # 同时写入 Chroma（需另装 chromadb 并配 embedding）
```

仓库里自带一份 `backend/data/textbooks/示例教材_机械原理节选.txt`，直接跑 `python scripts/ingest.py` 就能得到可检索的索引，用于验证链路是否通；换成真实教材 PDF 再跑一次即可替换。

切片策略：按「第 X 章」标题切章 → 段落聚合成 500~800 字切片 → 相邻切片重叠 100 字。

## 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 存活检查，返回当前模型与检索后端 |
| GET | `/api/meta` | 能力开关、上传上限、统一免责声明（不含密钥） |
| POST | `/api/chat` | 讲题 / 变式 / 教材 / 图纸追问，SSE |
| POST | `/api/rag` | 教材问答，SSE，末尾附 `cites` |
| POST | `/api/vision` | 图纸五维度识读，SSE |
| POST | `/api/ocr` | 题目照片转文字，JSON |

统一 SSE 事件协议：

```json
{"type":"delta","text":"..."}          // 逐字内容
{"type":"dimension","key":"view","title":"视图结构","content":"...","confidence":"medium"}
{"type":"cites","items":[{"book":"机械原理","chapter":"第5章 齿轮机构","page":"p.93"}],"backend":"lexical"}
{"type":"done","message_id":"...","disclaimer":"以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。"}
{"type":"error","code":"model_not_configured","message":"..."}
```

## 测试

```bash
cd backend
python -m pytest -q
```

覆盖：健康检查、meta 不泄露密钥、空输入与超长输入拦截、非图片上传拒绝。

## Docker

```bash
copy backend\.env.example backend\.env    # 填写密钥
docker compose up --build
```

访问 http://127.0.0.1:8000 。镜像为多阶段构建：Node 阶段打包前端，Python 阶段安装后端依赖并托管 `web/dist`。

## 提交物说明

| 比赛要求 | 状态 |
| --- | --- |
| Git 代码仓库（Public） | 本仓库，含 README、`.env.example`、真实提交历史 |
| 公网在线演示地址 | 已部署（见提交页） |
| 演示视频 | 不属于本仓库范围 |
| 技术文档 | 不属于本仓库范围 |

把仓库推到 Gitee / GitHub 后，在仓库设置里将可见性改为 Public 即可：

```bash
git remote add origin https://gitee.com/<你的账号>/mechabrain.git
git branch -M main
git push -u origin main
```

## 已知限制

- 教材切片只入库了两本教材的重点章节，检索质量取决于入库范围；未构建索引时教材问答会直接提示「知识库尚未构建」。
- 图纸识读依赖 qwen-vl-max 的识别能力，手绘草图与低分辨率照片的置信度会下降，界面上会标出「低置信」。
- 学习记录存在浏览器 `localStorage`，换设备或换浏览器不同步。
- 单机限流为内存滑动窗口，多副本部署时需要换成 Redis 之类的共享计数。

## License

MIT © 2026 张照

> 以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
