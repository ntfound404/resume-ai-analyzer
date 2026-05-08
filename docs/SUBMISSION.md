# 提交说明（面试官 / 评审快速导读）

**项目名称：** AI 智能简历分析系统  

本文档用于笔试或技术评审时，帮助快速了解**完成度、选型与运行方式**。

---

## 1. 项目完成情况

- 已完成 **MVP + JD 岗位匹配** 两阶段能力，前后端可独立启动、联调通过。
- 文档：`README.md`（总览）、`docs/API.md`（接口）、`backend/README.md`、`frontend/README.md`。
- 前端生产构建：`cd frontend && npm run build` 可通过。
- 后端启动：`cd backend && uvicorn app.main:app --reload --port 8000`（与验收一致）。

---

## 2. 已实现功能列表

| 模块 | 功能 |
|------|------|
| 上传 | PDF 校验、大小限制、multipart 上传 |
| 解析 | PyMuPDF 文本提取、清洗、长度上限 |
| 简历 AI | OpenAI 兼容 Chat Completions → 严格 JSON → Pydantic 校验 |
| JD 匹配 | 可选 JD；大模型语义分析 + 本地关键词规则降级 |
| 降级 | 无密钥 Mock、请求失败 Mock、匹配失败规则兜底 |
| 前端 | 上传 + JD 文本域、简历结构化展示、匹配分与标签、状态区分（离线演示 / 调用失败） |

---

## 3. 技术选型说明

| 层次 | 选型 | 理由 |
|------|------|------|
| 后端框架 | FastAPI | 异步友好、自动 OpenAPI、与 Pydantic 天然结合 |
| 数据校验 | Pydantic v2 | 统一简历与 `match_analysis` 结构，防脏数据 |
| PDF | PyMuPDF | 成熟、易部署，适合文本型 PDF |
| HTTP 客户端 | requests | 调用大模型同步简单，MVP 足够 |
| 前端 | Vue 3 + Vite | 组合式 API、构建快 |
| UI | Element Plus | 表格表单与展示组件齐全，适合演示 |
| AI | OpenAI-compatible | 一套代码对接 DeepSeek、OpenAI 等多供应商 |

未引入 LangChain、向量库等，控制复杂度，符合笔试 MVP 边界。

---

## 4. AI 调用说明

- **简历分析**：`POST {AI_BASE_URL}/chat/completions`（完整路径一般为 `.../v1/chat/completions`），`Authorization: Bearer {AI_API_KEY}`。
- **岗位匹配**：同一兼容接口，独立 system prompt，用户消息携带「简历结构化 JSON + JD」。
- **模型与地址**：由 `.env` 中 `AI_MODEL`、`AI_BASE_URL` 配置；DeepSeek 示例见 `backend/README.md`。

---

## 5. 降级策略说明

1. **未配置 `AI_API_KEY`**：简历返回**离线演示**结构化数据；匹配走**本地规则**，`gaps` 说明未调大模型。
2. **已配置但简历调用失败**：回退演示数据，`analysis` 文案标明**大模型调用失败**类原因。
3. **已配置但匹配调用失败或返回过弱**：`fallback_jd_match`，`gaps` 标明降级原因。

目标：**评审环境可无密钥跑通**；**生产/真实评测可一键配置密钥**。

---

## 6. 本地运行方式

1. **后端**（Python 3.10+）  
   `cd backend` → `pip install -r requirements.txt` → 复制 `.env.example` 为 `.env` → `uvicorn app.main:app --reload --port 8000`

2. **前端**  
   `cd frontend` → `npm install` → `npm run dev`

3. 浏览器打开 Vite 提示的地址；确保后端已监听 8000 端口以便代理 `/api`。

---

## 7. 测试说明

- **健康检查**：`GET /api/health` → `code === 0`。
- **仅简历**：不传 `jd_text`，`data` 无 `match_analysis`。
- **简历 + JD**：传 `jd_text`，`data` 含完整 `match_analysis`。
- **无密钥**：全流程可演示；文案体现离线/规则路径。
- **错误路径**：错误 PDF、超大文件、空文本 PDF，应返回 `code: 1` 与明确 `message`。

详细 curl 与字段说明见 **docs/API.md**。

---

## 8. 亮点总结

- **工程化**：Router / Service / Model 分层清晰，匹配逻辑独立文件。
- **契约统一**：`code / message / data` 全项目一致。
- **可演示、可扩展**：Mock 与多供应商 AI 并存；后续可加持久化与异步任务。
- **安全基线**：类型与大小校验、`.env` 不入库、文档不嵌入真实密钥。

---

**仓库路径提示：** 根目录 `README.md` 为总入口；接口细节以 `docs/API.md` 为准。
