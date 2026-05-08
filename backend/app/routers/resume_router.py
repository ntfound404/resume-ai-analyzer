"""
简历分析与健康检查路由。
"""
from typing import Any, Dict

from fastapi import APIRouter, File, Form, UploadFile

from app import config
from app.services.ai_service import analyze_resume_text
from app.services.match_service import analyze_jd_match
from app.services.pdf_service import extract_text_from_pdf

router = APIRouter(prefix="/api", tags=["resume"])


def success_response(data: Any) -> Dict[str, Any]:
    return {"code": 0, "message": "success", "data": data}


def error_response(message: str) -> Dict[str, Any]:
    return {"code": 1, "message": message, "data": None}


def _is_pdf_file(filename: str | None, content_type: str | None) -> bool:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return True
    ct = (content_type or "").lower()
    return ct in ("application/pdf", "application/x-pdf")


@router.get("/health")
async def health() -> Dict[str, Any]:
    """服务健康检查。"""
    return success_response({"status": "ok"})


@router.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    jd_text: str | None = Form(default=None),
) -> Dict[str, Any]:
    """
    上传 PDF 简历，解析文本并调用 AI（或 mock）返回结构化结果。
    可选表单字段 jd_text：非空时额外返回 match_analysis（岗位匹配分析）。
    单文件大小上限由环境变量 MAX_UPLOAD_FILE_MB（默认 10）控制，防止超大文件占用内存。
    """
    if not _is_pdf_file(file.filename, file.content_type):
        return error_response("文件类型必须是 PDF")

    try:
        file_bytes = await file.read()
    except Exception as e:  # noqa: BLE001
        return error_response(f"读取上传文件失败：{e!s}")

    if not file_bytes:
        return error_response("上传文件为空")

    max_bytes = config.MAX_UPLOAD_FILE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        return error_response(
            f"文件过大，单文件不超过 {config.MAX_UPLOAD_FILE_MB} MB"
            f"（可通过环境变量 MAX_UPLOAD_FILE_MB 调整）"
        )

    try:
        text = extract_text_from_pdf(file_bytes)
    except Exception as e:  # noqa: BLE001
        return error_response(f"PDF 解析失败：{e!s}")

    if not text or not text.strip():
        return error_response("未能从 PDF 中提取到文本，请确认是否为文本型 PDF")

    try:
        result = analyze_resume_text(text)
    except Exception as e:  # noqa: BLE001
        return error_response(f"简历分析失败：{e!s}")

    jd = (jd_text or "").strip()
    if jd:
        try:
            result = {**result, "match_analysis": analyze_jd_match(result, jd)}
        except Exception as e:  # noqa: BLE001
            return error_response(f"岗位匹配分析失败：{e!s}")

    return success_response(result)
