# Backend — AI 智能简历分析系统

Python **FastAPI** 服务：PDF 解析、大模型结构化简历、可选 JD 岗位匹配（大模型 + 本地规则降级）。

---

## 后端功能说明

- **健康检查** `GET /api/health`
- **简历分析** `POST /api/resume/analyze`：接收 PDF 与可选 `jd_text`，返回统一信封 JSON
- **PDF**：PyMuPDF 提文本，清洗与 `MAX_RESUME_TEXT_LENGTH` 截断
- **简历 AI**：OpenAI-compatible `chat/completions`；无密钥或失败时 Mock / 降级
- **岗位匹配**：有密钥优先调用模型；无密钥、请求失败、返回过弱时走 `match_service.fallback_jd_match`

---

## 环境要求

- Python **3.10+**
- 建议使用虚拟环境：`python -m venv .venv`

---

## 依赖安装

```bash
cd backend
pip install -r requirements.txt
```

---

## .env 配置

```bash
copy .env.example .env
```

编辑 `.env`，至少了解以下项（完整列表见根目录 `README.md`）：

| 变量 | 说明 |
|------|------|
| `AI_API_KEY` | 可为空；空则简历为离线演示数据 |
| `AI_BASE_URL` | 须指向兼容 OpenAI 的 **v1 根路径**（见下 DeepSeek 示例） |
| `AI_MODEL` | 与供应商文档一致 |
| `MAX_RESUME_TEXT_LENGTH` | 提取文本最大长度 |
| `MAX_UPLOAD_FILE_MB` | 上传 PDF 最大 MB |

---

## 启动命令

```bash
uvicorn app.main:app --reload --port 8000
```

启动后：

- 服务根路径：`http://127.0.0.1:8000/`
- Swagger：`http://127.0.0.1:8000/docs`

（启动命令与端口保持与项目验收一致。）

---

## API 说明

| 接口 | 说明 |
|------|------|
| `GET /api/health` | 返回 `data.status: ok` |
| `POST /api/resume/analyze` | `multipart/form-data`：`file`（必填 PDF），`jd_text`（选填） |

成功：`code: 0`；失败：`code: 1`，`data: null`。

详细请求/响应示例见仓库根目录 **[../docs/API.md](../docs/API.md)**。

---

## DeepSeek 配置示例

DeepSeek 使用 OpenAI 兼容接口，**`AI_BASE_URL` 需包含 `/v1`**，例如：

```env
AI_API_KEY=你的_deepseek_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
```

具体以 [DeepSeek 官方文档](https://api-docs.deepseek.com/) 为准。

---

## Mock / fallback 说明

1. **无 `AI_API_KEY`**  
   - 简历：`ai_service` 返回内置**离线演示**结构化数据（非真实模型抽取）。  
   - 岗位匹配：不请求大模型，使用 **本地关键词规则**；`match_analysis.gaps` 首条会说明未配置密钥。

2. **有密钥但简历接口异常**（网络、4xx/5xx、非 JSON 等）  
   - 简历：降级为演示数据，`analysis` 中强调**大模型调用失败**类文案。

3. **有密钥但匹配接口异常或返回过弱**  
   - 匹配：降级为本地规则，并在 `gaps` 中说明原因（调用失败 / 返回无效等）。

以上策略保证**演示与评审不断链**，同时日志与文案可区分「未配置」与「调用失败」。
