"""
大模型简历分析：OpenAI 兼容 Chat Completions，无 KEY 时返回 mock。
"""
import json
import re
from typing import Any, Dict

import requests

from app import config
from app.models.resume_schema import ResumeAnalysisResult, empty_resume_dict

SYSTEM_PROMPT = """你是一个专业的简历分析助手。用户会提供从 PDF 提取的纯文本简历。
你必须只输出一个合法的 JSON 对象，不要 markdown 代码块，不要任何解释文字。
JSON 必须严格符合以下结构（字段键名固定，缺失内容用空字符串或空数组）：
{
  "basic_info": {
    "name": "",
    "phone": "",
    "email": "",
    "location": "",
    "education_level": ""
  },
  "education": [{"school":"","major":"","degree":"","start_date":"","end_date":""}],
  "skills": [],
  "work_experience": [{"company":"","position":"","start_date":"","end_date":"","description":""}],
  "projects": [{"name":"","role":"","description":"","technologies":[],"highlights":[]}],
  "analysis": {
    "summary": "",
    "strengths": [],
    "risks": [],
    "suggestions": [],
    "score": 0
  }
}
score 为 0-100 的整数。根据简历内容合理推断；信息不足时保守打分并说明风险。"""


def _mock_analysis(resume_text: str) -> Dict[str, Any]:
    """未配置 API KEY 时的本地演示数据。"""
    preview = (resume_text or "")[:200].replace("\n", " ")
    return {
        "basic_info": {
            "name": "演示候选人",
            "phone": "",
            "email": "demo@example.com",
            "location": "未识别",
            "education_level": "本科（演示）",
        },
        "education": [
            {
                "school": "演示大学",
                "major": "计算机科学与技术",
                "degree": "学士",
                "start_date": "",
                "end_date": "",
            }
        ],
        "skills": ["Python", "FastAPI", "Vue 3", "沟通协作"],
        "work_experience": [
            {
                "company": "演示科技有限公司",
                "position": "后端开发工程师",
                "start_date": "2022-01",
                "end_date": "至今",
                "description": "负责 API 开发与维护（此为未配置 AI_API_KEY 时的模拟数据）。",
            }
        ],
        "projects": [
            {
                "name": "AI 简历分析 MVP",
                "role": "全栈开发",
                "description": "上传 PDF 简历并生成结构化分析（演示项目）。",
                "technologies": ["Python", "Vue", "Element Plus"],
                "highlights": ["OpenAI 兼容接口", "无 KEY 时自动 mock"],
            }
        ],
        "analysis": {
            # 避免使用「Mock」字样，便于前端区分「未配置密钥」与「调用失败降级」
            "summary": f"当前为离线演示：已读取简历原文约 {len(resume_text or '')} 字，"
            f"结构化字段为本地模板。片段预览：{preview}...",
            "strengths": ["项目可本地运行", "接口格式统一", "容错与降级完善"],
            "risks": [
                "未配置 AI_API_KEY，未调用大模型，以下为演示用结构化数据",
                "配置 .env 中 AI_API_KEY / AI_BASE_URL / AI_MODEL 后可获得真实解析",
            ],
            "suggestions": ["配置 AI_API_KEY / AI_BASE_URL / AI_MODEL 后重新上传以获得真实解析"],
            "score": 72,
        },
    }


def _try_parse_json_blob(text: str) -> Dict[str, Any]:
    """从模型原始输出中尽量解析 JSON。"""
    if not text or not text.strip():
        raise ValueError("模型返回为空")

    stripped = text.strip()
    # 去掉 ```json ... ``` 包裹
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", stripped, re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()

    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 尝试截取第一个 { 到最后一个 }
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        chunk = stripped[start : end + 1]
        data = json.loads(chunk)
        if isinstance(data, dict):
            return data

    raise ValueError("无法从模型输出中解析 JSON")


def _merge_into_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """将解析结果合并到标准 schema，缺省补全；异常时返回空结构避免中断。"""
    base = empty_resume_dict()
    if not isinstance(raw, dict):
        return base
    try:
        merged = {**base, **raw}
        if isinstance(raw.get("basic_info"), dict):
            merged["basic_info"] = {**base["basic_info"], **raw["basic_info"]}
        if isinstance(raw.get("analysis"), dict):
            merged["analysis"] = {**base["analysis"], **raw["analysis"]}
        model = ResumeAnalysisResult.model_validate(merged)
        return model.model_dump()
    except Exception:
        return base


def analyze_resume_text(resume_text: str) -> dict:
    """
    调用大模型分析简历文本，返回结构化 dict。
    无 API KEY 时返回 mock，不抛异常。
    """
    if not config.AI_API_KEY:
        return _mock_analysis(resume_text)

    api_base = config.AI_BASE_URL.rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.AI_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"以下是从 PDF 提取的简历文本：\n\n{resume_text}",
            },
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        body = resp.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError("模型响应无 choices")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        raw_dict = _try_parse_json_blob(content)
        return _merge_into_schema(raw_dict)
    except Exception:
        # 容错：解析失败或网络错误时回退 mock，保证演示可用
        mock = _mock_analysis(resume_text)
        mock["analysis"]["summary"] = (
            f"大模型调用失败或响应无法解析为合法 JSON，简历解析已降级为离线演示数据。"
            f" 已读取简历原文约 {len(resume_text or '')} 字。"
        )
        # 覆盖 risks：避免仍带「未配置密钥」文案，防止前端与「无 KEY 离线演示」混淆
        mock["analysis"]["risks"] = [
            "大模型调用失败或 JSON 解析失败，已回退为演示数据（已配置密钥但请求/解析未成功）",
            "请检查 AI_API_KEY、AI_BASE_URL、网络、模型名及账户额度",
            "以下为演示用结构化字段，非模型真实抽取结果",
        ]
        mock["analysis"]["suggestions"] = [
            "核对 .env 中 AI_BASE_URL 是否为兼容接口根路径（如 DeepSeek 需使用官方文档地址）",
            "确认模型名与供应商一致，并查看服务端返回的错误信息（/docs 可试调）",
        ]
        return mock
