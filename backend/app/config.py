"""
应用配置：从环境变量加载大模型与运行相关参数。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 从 backend 目录加载 .env（工作目录可能为 backend）
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _get_str(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


AI_API_KEY: str = _get_str("AI_API_KEY")
AI_BASE_URL: str = _get_str("AI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL: str = _get_str("AI_MODEL", "gpt-4o-mini")

# PDF 提取文本最大字符数，防止请求体过大
MAX_RESUME_TEXT_LENGTH: int = int(_get_str("MAX_RESUME_TEXT_LENGTH", "15000") or "15000")

# 上传 PDF 单文件大小上限（MB），防止过大文件占用内存
MAX_UPLOAD_FILE_MB: int = max(1, int(_get_str("MAX_UPLOAD_FILE_MB", "10") or "10"))
