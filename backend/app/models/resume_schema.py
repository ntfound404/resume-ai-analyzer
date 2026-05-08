"""
简历结构化数据 Pydantic 模型，与 AI 返回 JSON 字段对齐。
"""
from typing import List

from pydantic import BaseModel, Field


class BasicInfo(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    education_level: str = ""


class EducationItem(BaseModel):
    school: str = ""
    major: str = ""
    degree: str = ""
    start_date: str = ""
    end_date: str = ""


class WorkExperienceItem(BaseModel):
    company: str = ""
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class ProjectItem(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class AnalysisSection(BaseModel):
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: int = 0


class ResumeAnalysisResult(BaseModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    education: List[EducationItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    work_experience: List[WorkExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    analysis: AnalysisSection = Field(default_factory=AnalysisSection)

    class Config:
        # 允许从 dict 宽松合并缺省字段
        extra = "ignore"


def empty_resume_dict() -> dict:
    """返回与 schema 一致的空结构，用于校验或占位。"""
    return ResumeAnalysisResult().model_dump()


class MatchAnalysis(BaseModel):
    """岗位 JD 与简历结构化结果的匹配分析。"""

    match_score: int = 0
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    job_keywords: List[str] = Field(default_factory=list)
    candidate_keywords: List[str] = Field(default_factory=list)
    summary: str = ""
    advantages: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"


def empty_match_analysis_dict() -> dict:
    return MatchAnalysis().model_dump()
