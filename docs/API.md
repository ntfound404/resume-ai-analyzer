# HTTP API 说明

Base URL：本地默认 `http://127.0.0.1:8000`。所有业务接口前缀为 `/api`。

---

## 通用响应格式

### 成功

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 失败

```json
{
  "code": 1,
  "message": "错误原因（人类可读）",
  "data": null
}
```

HTTP 状态码一般为 **200**（错误也通过 `code: 1` 表达），便于前端统一处理；若发生未捕获异常，可能返回 5xx。

---

## 健康检查

### `GET /api/health`

**说明：** 探活，确认服务已启动。

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok"
  }
}
```

**curl：**

```bash
curl -s http://127.0.0.1:8000/api/health
```

---

## 简历分析（含可选 JD 匹配）

### `POST /api/resume/analyze`

**Content-Type：** `multipart/form-data`

| 字段 | 必填 | 说明 |
|------|------|------|
| `file` | 是 | PDF 文件；服务端校验扩展名 / MIME |
| `jd_text` | 否 | 岗位 JD 纯文本；仅空白或未传时**不**返回 `match_analysis` |

**限制：**

- 单文件大小默认不超过 `MAX_UPLOAD_FILE_MB`（见 `.env`，默认 10 MB）
- 非 PDF 或空文件会返回 `code: 1`
- 无法从 PDF 提取文本（如纯扫描件无文本层）会返回明确错误信息

**curl 示例（仅简历）：**

```bash
curl -s -X POST "http://127.0.0.1:8000/api/resume/analyze" \
  -F "file=@/path/to/resume.pdf"
```

**curl 示例（简历 + JD）：**

```bash
curl -s -X POST "http://127.0.0.1:8000/api/resume/analyze" \
  -F "file=@/path/to/resume.pdf" \
  -F "jd_text=岗位职责：后端开发，熟悉 Python、FastAPI、MySQL..."
```

---

## 成功响应 `data` 结构（简历部分）

以下为简历结构化主字段（与 Pydantic 模型一致）；数值与数组内容随模型或 Mock 变化。

```json
{
  "basic_info": {
    "name": "",
    "phone": "",
    "email": "",
    "location": "",
    "education_level": ""
  },
  "education": [
    {
      "school": "",
      "major": "",
      "degree": "",
      "start_date": "",
      "end_date": ""
    }
  ],
  "skills": [],
  "work_experience": [
    {
      "company": "",
      "position": "",
      "start_date": "",
      "end_date": "",
      "description": ""
    }
  ],
  "projects": [
    {
      "name": "",
      "role": "",
      "description": "",
      "technologies": [],
      "highlights": []
    }
  ],
  "analysis": {
    "summary": "",
    "strengths": [],
    "risks": [],
    "suggestions": [],
    "score": 0
  }
}
```

当请求中 **`jd_text` 有效（非空白）** 时，`data` 在以上字段之外追加：

```json
{
  "match_analysis": { }
}
```

若未传 JD 或 JD 仅空白，则 **不应** 出现 `match_analysis` 键。

---

## `match_analysis` 字段说明

仅在提供有效 `jd_text` 时返回。

| 字段 | 类型 | 说明 |
|------|------|------|
| `match_score` | int | 0–100，岗位匹配综合分 |
| `matched_skills` | string[] | 与 JD 要求匹配度较高的技能或关键词 |
| `missing_skills` | string[] | JD 侧重但简历侧体现不足的技能或关键词 |
| `job_keywords` | string[] | 从 JD 侧抽取的代表性关键词 |
| `candidate_keywords` | string[] | 从简历技能/经历等侧抽取的代表性关键词 |
| `summary` | string | 匹配总结（一段话） |
| `advantages` | string[] | 候选人相对该岗位的优势 |
| `gaps` | string[] | 差距与风险说明；**降级时首条常含原因说明** |
| `improvement_suggestions` | string[] | 可执行的改进建议 |

**示例片段：**

```json
"match_analysis": {
  "match_score": 72,
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["K8s"],
  "job_keywords": ["Python", "后端", "微服务"],
  "candidate_keywords": ["Python", "Vue", "API"],
  "summary": "整体技能栈与岗位部分重合……",
  "advantages": ["具备后端接口开发经验"],
  "gaps": ["云原生相关关键词在简历中体现较少"],
  "improvement_suggestions": ["在项目描述中补充高并发与部署相关实践"]
}
```

---

## 常见错误 `message` 示例

| 场景 | 典型 `message` |
|------|----------------|
| 非 PDF | `文件类型必须是 PDF` |
| 超限 | `文件过大，单文件不超过 N MB（可在环境变量 MAX_UPLOAD_FILE_MB 中配置）` |
| 空文件 | `上传文件为空` |
| 无文本层 | `未能从 PDF 中提取到文本，请确认是否为文本型 PDF` |
| 解析异常 | `PDF 解析失败：...` |

---

## 交互式文档

启动后端后访问：**http://127.0.0.1:8000/docs**
