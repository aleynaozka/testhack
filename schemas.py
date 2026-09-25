from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    student = "student"
    academic = "academic"
    industry = "industry"


class IndustryType(str, Enum):
    entrepreneur = "entrepreneur"
    company_without_rd = "company_without_rd"
    rd_center = "rd_center"


class AIMode(str, Enum):
    auto = "auto"
    local = "local"
    gemini = "gemini"


class RegistrationValidationRequest(BaseModel):
    email: str
    role: UserRole


class IndustryVerificationRequest(BaseModel):
    industry_type: IndustryType
    method: Literal["google_oauth", "work_email", "manual_review", "rd_center_document"]
    email: str
    company_name: str | None = None


class ProblemAnalysisRequest(BaseModel):
    problem_text: str = Field(min_length=15, max_length=8000)
    industry_type: IndustryType = IndustryType.company_without_rd
    answers: dict[str, str] = Field(default_factory=dict)
    skip_clarification: bool = False
    confidentiality: Literal["open", "masked", "strict"] = "masked"
    ai_mode: AIMode = AIMode.auto


class MatchFilters(BaseModel):
    city: str | None = None
    remote_allowed: bool | None = None
    university: str | None = None
    department: str | None = None
    minimum_year: int | None = Field(default=None, ge=1, le=6)
    skills: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    problem_text: str = Field(min_length=15, max_length=8000)
    target_role: Literal["academic", "student"] = "academic"
    industry_type: IndustryType = IndustryType.company_without_rd
    filters: MatchFilters = Field(default_factory=MatchFilters)
    top_k: int = Field(default=5, ge=1, le=10)
    confidentiality: Literal["open", "masked", "strict"] = "masked"
    ai_mode: AIMode = AIMode.auto


class TeamMatchRequest(BaseModel):
    problem_text: str = Field(min_length=15, max_length=8000)
    industry_type: IndustryType = IndustryType.company_without_rd
    student_count: int = Field(default=3, ge=1, le=5)
    confidentiality: Literal["open", "masked", "strict"] = "masked"
    ai_mode: AIMode = AIMode.auto


class TalentSearchRequest(BaseModel):
    query: str = Field(min_length=5, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    ai_mode: AIMode = AIMode.auto


class AssistantRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    industry_type: IndustryType = IndustryType.company_without_rd
    context: dict[str, Any] = Field(default_factory=dict)
    ai_mode: AIMode = AIMode.auto
