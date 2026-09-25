from __future__ import annotations

from typing import Any

from app.repository import get_candidates
from app.services.analyzer import detect_taxonomy
from app.services.text import normalize


WEIGHTS = {
    "fields": 30,
    "skills": 25,
    "methods": 15,
    "sectors": 10,
    "project_types": 10,
    "availability": 5,
    "location": 5,
}


def _overlap(required: list[str], offered: list[str]) -> list[str]:
    offered_normalized = {normalize(value) for value in offered}
    return [value for value in required if normalize(value) in offered_normalized]


def _ratio_score(required: list[str], offered: list[str], weight: int) -> tuple[float, list[str]]:
    if not required:
        return weight * 0.35, []
    matches = _overlap(required, offered)
    return weight * len(matches) / len(required), matches


def candidate_passes_filters(candidate: dict[str, Any], filters: dict[str, Any]) -> bool:
    if not candidate.get("verified") or not candidate.get("available"):
        return False
    if filters.get("city") and normalize(filters["city"]) != normalize(candidate.get("city", "")):
        if not (filters.get("remote_allowed") and candidate.get("remote")):
            return False
    if filters.get("university") and normalize(filters["university"]) not in normalize(candidate.get("university", "")):
        return False
    if filters.get("department") and normalize(filters["department"]) not in normalize(candidate.get("department", "")):
        return False
    if filters.get("minimum_year") and candidate.get("year", 0) < filters["minimum_year"]:
        return False
    required_skills = filters.get("skills") or []
    if required_skills and not _overlap(required_skills, candidate.get("skills", [])):
        return False
    return True


def score_candidate(
    candidate: dict[str, Any],
    analysis: dict[str, list[str]],
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = filters or {}
    breakdown: dict[str, float] = {}
    matched_terms: dict[str, list[str]] = {}
    for category in ("fields", "skills", "methods", "sectors", "project_types"):
        score, matches = _ratio_score(
            analysis.get(category, []),
            candidate.get(category, []),
            WEIGHTS[category],
        )
        breakdown[category] = round(score, 1)
        matched_terms[category] = matches

    breakdown["availability"] = WEIGHTS["availability"] if candidate.get("available") else 0
    wanted_city = filters.get("city")
    if not wanted_city:
        breakdown["location"] = WEIGHTS["location"] * 0.6
    elif normalize(wanted_city) == normalize(candidate.get("city", "")):
        breakdown["location"] = WEIGHTS["location"]
    elif filters.get("remote_allowed") and candidate.get("remote"):
        breakdown["location"] = WEIGHTS["location"] * 0.7
    else:
        breakdown["location"] = 0

    total = min(100, round(sum(breakdown.values())))
    reasons: list[str] = []
    labels = {
        "fields": "Alan",
        "skills": "Yetkinlik",
        "methods": "Yöntem",
        "sectors": "Sektör",
        "project_types": "Proje tipi",
    }
    for category, matches in matched_terms.items():
        if matches:
            reasons.append(f"{labels[category]} uyumu: {', '.join(matches)}")
    if not reasons:
        reasons.append("Genel profil yakınlığı; ayrıntılı insan değerlendirmesi önerilir.")

    return {
        "candidate": candidate,
        "score": total,
        "breakdown": breakdown,
        "matched_terms": matched_terms,
        "reasons": reasons,
    }


def match_candidates(
    problem_text: str,
    target_role: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
    analysis_override: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    filters = filters or {}
    analysis = analysis_override or detect_taxonomy(problem_text)
    candidates = [
        candidate
        for candidate in get_candidates(target_role)
        if candidate_passes_filters(candidate, filters)
    ]
    results = [score_candidate(candidate, analysis, filters) for candidate in candidates]
    results.sort(key=lambda item: (-item["score"], item["candidate"]["name"]))
    return {
        "analysis": analysis,
        "target_role": target_role,
        "total_candidates": len(candidates),
        "results": results[:top_k],
        "scoring_weights": WEIGHTS,
    }


def match_team(problem_text: str, student_count: int = 3) -> dict[str, Any]:
    academics = match_candidates(problem_text, "academic", top_k=3)
    students = match_candidates(problem_text, "student", top_k=student_count)
    return {
        "academic_matches": academics["results"],
        "student_matches": students["results"],
        "team_ready": bool(academics["results"] and students["results"]),
        "minimum_team_rule": "En az 1 sanayici + 1 akademisyen + 1 öğrenci",
    }
