# 机小智 MechaBrain AI

**面向机械类专业学生的 AI 学习与工程图纸助手。**

上传一张零件图，它按「视图结构 → 尺寸与公差 → 表面粗糙度 → 材料推断 → 加工工艺」五个维度讲清楚；翻教材卡住时，它从《机械原理》《工程材料》的章节切片里找依据再回答，并标注出处；题目不会做，它按「审题 → 考点 → 分步解答 → 易错点」讲完，再给一道同考点变式。

- 参赛：传智杯 · 全国高校 AI Web 开发挑战赛
- 作者：张照、黄赤宇　绵阳城市学院 · 智能制造与工程学院 · 机械设计制造及其自动化 2025 级
- 形态：前后端分离的完整工程（Vue3 + TypeScript + Vite 前端，FastAPI 后端，SSE 流式输出）

---

## 在线演示

演示环境地址见比赛提交页；本地按下面的「快速开始」三条命令即可跑起来，**未配置 API Key 时服务照常启动**，AI 接口会返回明确的「未配置密钥」提示，不会伪造答案。

---

## 功能

| 功能 | 入口 | 说明 |
| --- | --- | --- |
| 图纸识读 | `/drawing` | 上传 JPG / PNG / WEBP 零件图，多模态模型一次性识读后按五个维度结构化返回，每维度自带置信度 |
| 教材问答 | `/rag` | 左侧章节树由 `/api/textbooks` 按实际入库内容动态生成，章节过滤 + BM25 词法检索 Top-5，答案末尾回标教材·章节（PDF 教材带页码） |
| AI 讲题 | `/chat` | 拍照 OCR 或直接输入题目，四步讲题，附同考点变式 |
| 变式出题 | `/chat` | 指定知识点，生成三道由易到难的变式题，附参考答案与解析 |
| 学习记录 | `/records` | 按日期分组、按模式筛选、可展开查看与删除，存在浏览器本地 |

五个页面共用一套「工程图纸」视觉体系：24px 方格纸底、墨色正文、图纸蓝标注、强调红只用于关键标注。

## 技术栈

**前端**：Vue 3 · TypeScript · Vite 5 · Vue Router 4 · Pinia · TailwindCSS 3 · markdown-it
**后端**：FastAPI · Uvicorn · pydantic-settings · httpx
**AI**：DeepSeek V4.1 Flash（对话，模型 ID `deepseek-flash`）、qwen3-vl-plus（多模态识图 / OCR）、bge-m3（向量化，可选）
**检索**：内置 BM25（零依赖，默认）＋ Chroma（可选，配置 embedding 后启用）
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
│  CORS · 限流 60 次/分 · 输入过滤 · 统一 SSE 事件协议     │
└───────┬───────────────┬───────────────┬──────────────┘
        │               │               │
   DeepSeek API    qwen3-vl-plus     Retriever
   （讲题/问答）    （识图/OCR）    ┌──────┴──────┐
                                  Chroma      BM25
                                  （可选）    （默认）
```

密钥全部在服务端 `.env`，前端构建产物中不含任何 key。

## 团队信息

| 项目 | 内容 |
| --- | --- |
| 参赛形式 | 团队参赛（2 人） |
| 姓名 | 张照、黄赤宇 |
| 学号 | 2025500650（张照）/ 2025500620（黄赤宇） |
| 学校 | 绵阳城市学院 |
| 学院 | 智能制造与工程学院 |
| 专业 | 机械设计制造及其自动化 |
| 年级 | 2025 级 |
| 承担工作 | 张照：需求分析与功能设计、前端五个页面与设计体系、后端接口与 SSE 协议、检索与提示词工程、部署与测试；黄赤宇：后台维护与推广 |
| 技术工具 | SolidWorks、AutoCAD、Python、Vue 3、TypeScript、FastAPI |
| 联系方式 | 见比赛提交表（不在公开仓库中暴露手机号） |

如后续组队参赛，在本表下方追加成员与分工即可，其余章节无需改动。

## 代码规范

- **目录约定**：`web/src` 按 `views`（页面）/ `stores`（状态）/ `lib`（工具）/ `api.ts`（接口）分层；`backend/app` 按 `api`（路由）/ `core`（协议与安全）/ `services`（模型与检索）分层，新增功能落到对应层，不在页面里直接写请求逻辑。
- **命名**：前端组件文件用 PascalCase，工具函数用 camelCase，接口类型以 `Req` / `Res` 结尾；后端模块与函数用 snake_case，路由函数与文件同名。
- **类型**：前端开启 TypeScript `strict`，`any` 仅用于 SSE 解析后的原始帧；后端所有请求与响应经 `schemas.py` 的 pydantic 模型校验，不直接读裸 dict。
- **注释**：每个 Python 模块首行写职责说明；模型调用、SSE 封装、检索打分三处保留关键参数注释（如 BM25 的 k1、b 取值理由），不写“给变量赋值”这类无信息注释。
- **提交信息**：采用 Conventional Commits 前缀（`feat` / `fix` / `chore` / `docs`），一次提交只做一件事，提交体说明“为什么改”。
- **校验命令**：前端 `npm run build`（等价于类型检查 + 构建），后端 `python -m pytest -q`。两项通过才算一次可提交的改动。

## 目录结构

```
机小智-MechaBrain/
├─ web/                      前端工程
│  ├─ src/
│  │  ├─ api.ts              SSE 解析与四条能力接口
│  │  ├─ router.ts           5 个路由 + 404 兜底
│  │  ├─ stores/app.ts       记录与图纸上下文（localStorage）
│  │  ├─ lib/markdown.ts     回答渲染
│  │  ├─ views/              Home / Drawing / Rag / Chat / Records
│  │  ├─ App.vue             导航、能力状态条与提示
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
│  ├─ tests/test_api.py      接口与检索回归测试（10 条）
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
| `DEEPSEEK_MODEL` | 否 | 填模型 ID `deepseek-flash`，背后版本为 DeepSeek-V4.1-Flash-1017（不要填版本名） |
| `VISION_MODEL` | 否 | 默认 `qwen3-vl-plus` |
| `CHROMA_ENABLED` | 否 | 默认 `false`，走内置 BM25 |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` | 否 | 启用 Chroma 时填 bge-m3 的 OpenAI 兼容 `/embeddings` 地址 |
| `CORS_ORIGINS` | 否 | 允许的前端来源，逗号分隔 |
| `MAX_UPLOAD_MB` | 否 | 上传图片上限，默认 10 |
| `RATE_LIMIT_PER_MIN` | 否 | 单 IP 每分钟请求上限，默认 60 |

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
| GET | `/api/textbooks` | 实际入库的教材与章节目录，前端章节树据此渲染 |
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

覆盖：健康检查、meta 不泄露密钥、空输入与超长输入拦截、非图片上传拒绝，以及检索链路的四条回归测试——教材目录接口、章节限定仍能召回、错误章节不召回、引用去重、逐维度置信度解析。

## Docker

```bash
copy backend\.env.example backend\.env    # 填写密钥
docker compose up --build
```

访问 http://127.0.0.1:8000 。镜像为多阶段构建：Node 阶段打包前端，Python 阶段安装后端依赖、**在构建期跑一次 `python scripts/ingest.py` 把示例教材入库**，再托管 `web/dist`。因此容器一起来教材问答就是可用的，不需要额外手工入库。

## 提交物说明

| 比赛要求 | 状态 |
| --- | --- |
| Git 代码仓库（Public） | 本仓库，含 README、`.env.example`、真实提交历史 |
| 公网在线演示地址 | 已部署（见提交页） |
| 演示视频 | 见提交材料目录，因体积原因不纳入 git 仓库 |
| 技术文档 | 见提交材料目录，因体积原因不纳入 git 仓库 |

把仓库推到 Gitee / GitHub 后，在仓库设置里将可见性改为 Public 即可：

```bash
git remote add origin https://gitee.com/<你的账号>/mechabrain.git
git branch -M main
git push -u origin main
```

## 已知限制

- 目录与索引保持一致：前端章节树完全由 `/api/textbooks` 读取实际入库内容渲染，索引里没有的章节不会出现在界面上。示例数据只有《机械原理》两章，替换成真实教材 PDF 后重新入库即可扩展。
- 页码只对 PDF 教材有效：`scripts/ingest.py` 按页提取时记录每个切片的起始页，标注为 `p.N`；TXT 教材没有页的概念，引用只到章节，界面不会显示一个空的页码位。
- 图纸识读依赖 qwen3-vl-plus 的识别能力，手绘草图与低分辨率照片的置信度会下降，每个维度单独标注置信度（高 / 中 / 低），并在「识别备注」里写出看不清的地方。
- 学习记录存在浏览器 `localStorage`，换设备或换浏览器不同步。
- 限流为内存滑动窗口（默认 60 次/分），已支持 `X-Forwarded-For` 取真实客户端 IP；多副本部署时仍需换成 Redis 之类的共享计数。

## License

MIT © 2026 张照、黄赤宇

> 以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
