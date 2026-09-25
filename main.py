from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.repository import get_candidates, get_demo_problems
from app.schemas import (
    AssistantRequest,
    IndustryVerificationRequest,
    MatchRequest,
    ProblemAnalysisRequest,
    RegistrationValidationRequest,
    TalentSearchRequest,
    TeamMatchRequest,
)
from app.services.ai import AIUnavailable
from app.services.analyzer import analyze_problem
from app.services.auth import (
    fetch_supabase_user,
    validate_industry_verification,
    validate_registration,
)
from app.services.matching import match_candidates
from app.services.talent import parse_talent_query_with_ai, search_students


app = FastAPI(
    title=settings.app_name,
    version="1.0.0-demo",
    description="Lovable frontend için ISOV Bridge demo API'si",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.environment,
        "gemini_configured": settings.gemini_enabled,
        "supabase_configured": settings.supabase_enabled,
    }


@app.get("/api/demo/candidates")
def demo_candidates(role: str | None = None) -> dict:
    if role not in {None, "academic", "student"}:
        raise HTTPException(400, "role academic veya student olmalıdır.")
    return {"items": get_candidates(role), "demo_data": True}


@app.get("/api/demo/problems")
def demo_problems() -> dict:
    return {"items": get_demo_problems(), "demo_data": True}


@app.post("/api/auth/validate-registration")
def registration_validation(body: RegistrationValidationRequest) -> dict:
    return validate_registration(body.email, body.role.value)


@app.post("/api/auth/industry-verification")
def industry_verification(body: IndustryVerificationRequest) -> dict:
    return validate_industry_verification(
        body.industry_type.value,
        body.method,
        body.email,
        body.company_name,
    )


@app.get("/api/auth/me")
def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Bearer token gereklidir.")
    try:
        user = fetch_supabase_user(authorization.split(" ", 1)[1])
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc
    if not user["email_confirmed"]:
        raise HTTPException(403, "E-posta adresi henüz doğrulanmamış.")
    return user


@app.post("/api/ai/analyze-problem")
def problem_analysis(body: ProblemAnalysisRequest) -> dict:
    try:
        return analyze_problem(
            body.problem_text,
            body.industry_type.value,
            body.answers,
            body.skip_clarification,
            body.ai_mode.value,
            body.confidentiality,
        )
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.post("/api/match")
def match(body: MatchRequest) -> dict:
    try:
        analysis_result = analyze_problem(
            body.problem_text,
            body.industry_type.value,
            skip_clarification=True,
            ai_mode=body.ai_mode.value,
            confidentiality=body.confidentiality,
        )
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    result = match_candidates(
        body.problem_text,
        body.target_role,
        body.filters.model_dump(),
        body.top_k,
        analysis_override={
            key: analysis_result["structured_problem"][key]
            for key in ("fields", "skills", "methods", "sectors", "project_types")
        },
    )
    result["analysis_provider"] = analysis_result["provider"]
    result["warning"] = analysis_result.get("warning")
    return result


@app.post("/api/match/team")
def team_match(body: TeamMatchRequest) -> dict:
    try:
        analysis_result = analyze_problem(
            body.problem_text,
            body.industry_type.value,
            skip_clarification=True,
            ai_mode=body.ai_mode.value,
            confidentiality=body.confidentiality,
        )
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    analysis_override = {
        key: analysis_result["structured_problem"][key]
        for key in ("fields", "skills", "methods", "sectors", "project_types")
    }
    academics = match_candidates(
        body.problem_text, "academic", top_k=3, analysis_override=analysis_override
    )
    students = match_candidates(
        body.problem_text, "student", top_k=body.student_count, analysis_override=analysis_override
    )
    return {
        "academic_matches": academics["results"],
        "student_matches": students["results"],
        "team_ready": bool(academics["results"] and students["results"]),
        "minimum_team_rule": "En az 1 sanayici + 1 akademisyen + 1 öğrenci",
        "analysis_provider": analysis_result["provider"],
        "warning": analysis_result.get("warning"),
    }


@app.post("/api/ai/talent-search")
def talent_search(body: TalentSearchRequest) -> dict:
    try:
        filters, provider, warning = parse_talent_query_with_ai(body.query, body.ai_mode.value)
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    return {
        "provider": provider,
        "filters": filters,
        "results": search_students(filters, body.top_k),
        "suggestions": filters.get("clarification_questions", []),
        "warning": warning,
    }


@app.post("/api/assistant/message")
def assistant_message(body: AssistantRequest) -> dict:
    lowered = body.message.lower()
    talent_terms = ("öğrenci", "ogrenci", "staj", "aday mühendis", "aday muhendis", "öğrenci bul")
    if any(term in lowered for term in talent_terms):
        try:
            filters, provider, warning = parse_talent_query_with_ai(body.message, body.ai_mode.value)
        except AIUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        return {
            "intent": "talent_search",
            "provider": provider,
            "filters": filters,
            "results": search_students(filters, 5),
            "suggestions": filters.get("clarification_questions", []),
            "warning": warning,
        }
    try:
        analysis = analyze_problem(
            body.message,
            body.industry_type.value,
            body.context,
            False,
            body.ai_mode.value,
            "masked",
        )
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"intent": "problem_analysis", **analysis}
