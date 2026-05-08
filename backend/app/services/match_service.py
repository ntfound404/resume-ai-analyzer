"""
岗位 JD 与简历结构化数据的匹配分析：优先大模型，失败则本地规则降级。
"""
import json
import re
from typing import Any, Dict, List, Set

import requests

from app import config
from app.models.resume_schema import MatchAnalysis, empty_match_analysis_dict
from app.services.ai_service import _try_parse_json_blob

# 常见无信息词汇，过滤后减少噪声关键词
_STOP_WORDS: Set[str] = {
    "的",
    "了",
    "和",
    "与",
    "或",
    "及",
    "等",
    "为",
    "在",
    "有",
    "对",
    "将",
    "可",
    "能",
    "会",
    "进行",
    "相关",
    "工作",
    "岗位",
    "职责",
    "要求",
    "优先",
    "熟悉",
    "掌握",
    "了解",
    "具备",
    "负责",
    "参与",
    "协助",
    "完成",
    "以上",
    "以下",
    "经验",
    "学历",
    "本科",
    "大专",
    "硕士",
    "博士",
    "年",
    "the",
    "and",
    "or",
    "for",
    "with",
    "from",
    "this",
    "that",
    "you",
    "our",
    "are",
    "will",
    "have",
    "has",
}

MATCH_SYSTEM_PROMPT = """你是招聘与人才评估专家。根据【简历结构化 JSON】与【岗位 JD】输出岗位匹配分析。
只输出一个合法 JSON 对象，禁止 markdown、禁止代码块、禁止任何解释文字。
JSON 键名必须完全一致，结构如下：
{
  "match_score": 0,
  "matched_skills": [],
  "missing_skills": [],
  "job_keywords": [],
  "candidate_keywords": [],
  "summary": "",
  "advantages": [],
  "gaps": [],
  "improvement_suggestions": []
}
match_score 为 0-100 的整数。分析须覆盖：技能匹配、项目经验与 JD 相关性、岗位职责匹配、学习潜力、风险点、改进建议；并体现在 summary、advantages、gaps、improvement_suggestions 中。"""


def _normalize_token(t: str) -> str:
    t = t.strip()
    if not t:
        return ""
    return t.lower() if t.isascii() else t


def _extract_keywords(text: str, limit: int = 45) -> List[str]:
    """从文本抽取候选关键词（英文词、技术片段、中文连续片段）。"""
    if not text or not text.strip():
        return []

    # 英文与技术 token（含 C#、node.js 等常见形态）
    en_tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,}", text)
    # 中文：按非标点切分后保留长度>=2 的片段
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9+#.\s]", " ", text)
    chunks: List[str] = []
    for part in cleaned.split():
        if re.search(r"[\u4e00-\u9fff]", part):
            if len(part) >= 2:
                chunks.append(part)
        elif part in en_tokens or len(part) >= 2:
            chunks.append(part)

    raw = list(en_tokens) + chunks
    seen: Set[str] = set()
    out: List[str] = []
    for r in raw:
        r = r.strip()
        if len(r) < 2:
            continue
        nk = _normalize_token(r)
        if not nk or nk in _STOP_WORDS:
            continue
        if nk not in seen:
            seen.add(nk)
            out.append(r if not r.isascii() else r.lower())
        if len(out) >= limit:
            break
    return out


def _resume_to_search_blob(resume_data: Dict[str, Any]) -> str:
    """将简历结构化字段拼成用于子串匹配的文本（小写）。"""
    parts: List[str] = []
    for s in resume_data.get("skills") or []:
        parts.append(str(s))
    for w in resume_data.get("work_experience") or []:
        if isinstance(w, dict):
            parts.append(str(w.get("position", "")))
            parts.append(str(w.get("description", "")))
            parts.append(str(w.get("company", "")))
    for p in resume_data.get("projects") or []:
        if isinstance(p, dict):
            parts.append(str(p.get("name", "")))
            parts.append(str(p.get("role", "")))
            parts.append(str(p.get("description", "")))
            for t in p.get("technologies") or []:
                parts.append(str(t))
            for h in p.get("highlights") or []:
                parts.append(str(h))
    blob = " ".join(parts).lower()
    for edu in resume_data.get("education") or []:
        if isinstance(edu, dict):
            blob += " " + str(edu.get("major", "")).lower()
            blob += " " + str(edu.get("degree", "")).lower()
    return blob


def _keyword_in_blob(keyword: str, blob_lower: str) -> bool:
    """判断关键词是否在候选人文本中出现（英文不区分大小写）。"""
    if not keyword:
        return False
    if keyword.isascii():
        return keyword.lower() in blob_lower
    return keyword in blob_lower  # 中文 blob 已小写，中文不变


def fallback_jd_match(resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """
    本地规则：关键词抽取 + 与简历技能/经历文本对比，生成可展示的匹配结果。
    """
    jd_text = (jd_text or "").strip()
    blob = _resume_to_search_blob(resume_data)
    job_keywords = _extract_keywords(jd_text, limit=40)
    candidate_keywords = _extract_keywords(blob.replace("\n", " "), limit=40)
    if not job_keywords:
        job_keywords = _extract_keywords(jd_text[:2000], limit=40) or ["岗位描述较短"]

    matched: List[str] = []
    for kw in job_keywords:
        if _keyword_in_blob(kw, blob):
            matched.append(kw)

    matched_set = {_normalize_token(m) for m in matched}
    missing: List[str] = []
    for kw in job_keywords:
        if _normalize_token(kw) not in matched_set:
            missing.append(kw)
    missing = missing[:25]

    # 分数：按 JD 关键词覆盖率，并设上下限避免极端
    denom = max(len(job_keywords), 1)
    ratio = len(matched) / denom
    match_score = int(round(min(100, max(0, ratio * 100))))
    if match_score == 0 and job_keywords and matched:
        match_score = min(100, 15 + len(matched) * 5)
    if not matched and job_keywords:
        match_score = min(match_score, 35)
    elif len(matched) >= max(3, denom // 2):
        match_score = max(match_score, 55)

    summary = (
        f"基于关键词规则的快速评估：JD 抽取 {len(job_keywords)} 个关键词，"
        f"其中约 {len(matched)} 项在简历技能/项目/经历描述中有体现。"
    )
    advantages: List[str] = []
    if matched:
        advantages.append(f"与岗位描述存在交集的技能或技术点：{', '.join(matched[:8])}")
    if resume_data.get("projects"):
        advantages.append("简历中包含项目经历，可结合 JD 进一步突出与岗位相关的成果。")
    if not advantages:
        advantages.append("建议补充与 JD 对齐的技能关键词，便于简历筛选通过。")

    gaps: List[str] = []
    if missing:
        gaps.append(f"JD 中提及但简历侧未明显体现的关键词示例：{', '.join(missing[:8])}")
    gaps.append("规则匹配无法理解语义同义（如「后端」与「服务端」），仅供参考。")

    improvement_suggestions: List[str] = [
        "在简历「技能」与「项目描述」中显式写入 JD 中的核心技术栈与业务场景。",
        "为每个项目补充量化指标（性能、规模、收益）以支撑职责匹配度。",
    ]
    if missing:
        improvement_suggestions.append(
            f"针对缺失关键词中的 {missing[0]} 等，补充学习经历或相关项目说明。"
        )

    base = empty_match_analysis_dict()
    base.update(
        {
            "match_score": match_score,
            "matched_skills": matched[:30],
            "missing_skills": missing[:30],
            "job_keywords": job_keywords[:30],
            "candidate_keywords": candidate_keywords[:30],
            "summary": summary,
            "advantages": advantages,
            "gaps": gaps,
            "improvement_suggestions": improvement_suggestions,
        }
    )
    return base


def _merge_match_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """校验并补全 match_analysis 字段。"""
    base = empty_match_analysis_dict()
    if not isinstance(raw, dict):
        return base
    try:
        merged = {**base, **raw}
        model = MatchAnalysis.model_validate(merged)
        out = model.model_dump()
        # 分数边界
        s = int(out.get("match_score") or 0)
        out["match_score"] = min(100, max(0, s))
        return out
    except Exception:
        return base


def _is_weak_match_result(d: Dict[str, Any]) -> bool:
    """判断大模型返回是否几乎为空（需降级到本地规则）。"""
    return (
        int(d.get("match_score") or 0) == 0
        and not (d.get("summary") or "").strip()
        and not (d.get("matched_skills") or [])
        and not (d.get("job_keywords") or [])
    )


def _call_llm_jd_match(resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """调用 OpenAI 兼容接口生成匹配 JSON。"""
    api_base = config.AI_BASE_URL.rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    resume_json = json.dumps(resume_data, ensure_ascii=False)
    if len(resume_json) > 12000:
        resume_json = resume_json[:12000] + "...(truncated)"

    payload = {
        "model": config.AI_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": MATCH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"【简历结构化 JSON】\n{resume_json}\n\n【岗位 JD】\n{jd_text}",
            },
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    body = resp.json()
    choices = body.get("choices") or []
    if not choices:
        raise ValueError("模型响应无 choices")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    raw_dict = _try_parse_json_blob(content)
    return _merge_match_schema(raw_dict)


def analyze_jd_match(resume_data: Dict[str, Any], jd_text: str) -> dict:
    """
    基于简历结构化结果与 JD 文本做岗位匹配分析。
    有 API KEY 时优先调用大模型；失败或无 KEY 时使用本地规则，保证必有可展示结果。
    """
    jd_text = (jd_text or "").strip()
    if not jd_text:
        return empty_match_analysis_dict()

    if not config.AI_API_KEY:
        out = fallback_jd_match(resume_data, jd_text)
        # 与「调用失败」区分：未配置密钥时不算失败，明确提示未走大模型
        prefix = "未配置 AI_API_KEY，岗位匹配未调用大模型，以下为本地关键词规则估算。"
        out["gaps"] = list(dict.fromkeys([prefix] + (out.get("gaps") or [])))
        return out

    try:
        merged = _call_llm_jd_match(resume_data, jd_text)
        if _is_weak_match_result(merged):
            out = fallback_jd_match(resume_data, jd_text)
            out["gaps"] = list(
                dict.fromkeys(
                    ["大模型返回无效或几乎为空，已使用本地关键词规则降级结果。"]
                    + (out.get("gaps") or [])
                )
            )
            return out
        return merged
    except Exception:
        # API 失败：降级到本地规则（不打断主流程）
        out = fallback_jd_match(resume_data, jd_text)
        out["gaps"] = list(
            dict.fromkeys(
                ["大模型调用失败或返回非 JSON，已使用本地关键词规则降级结果。"]
                + (out.get("gaps") or [])
            )
        )
        return out
