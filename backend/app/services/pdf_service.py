"""
PDF 文本提取：PyMuPDF，清洗与长度限制。
"""
import re

import fitz  # PyMuPDF

from app import config


def _normalize_whitespace(text: str) -> str:
    """合并多余空格与空行，保留段落间单行换行。"""
    if not text:
        return ""
    # 行内多空格变单空格
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    从 PDF 二进制内容提取纯文本。
    空文档或扫描件无文本层时可能得到空字符串。
    """
    if not file_bytes:
        return ""

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text") or "")
        raw = "\n".join(parts)
    finally:
        doc.close()

    normalized = _normalize_whitespace(raw)
    max_len = max(1000, config.MAX_RESUME_TEXT_LENGTH)
    if len(normalized) > max_len:
        normalized = normalized[:max_len]
    return normalized
