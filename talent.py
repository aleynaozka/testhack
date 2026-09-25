from __future__ import annotations

import re
from typing import Any

from app.repository import get_candidates
from app.services.ai import AIUnavailable, TALENT_SYSTEM_PROMPT, generate_json
from app.services.text import normalize


UNIVERSITIES = [
    "İstanbul Teknik Üniversitesi", "Yıldız Teknik Üniversitesi", "Orta Doğu Teknik Üniversitesi",
    "Boğaziçi Üniversitesi", "Ege Üniversitesi", "Bursa Uludağ Üniversitesi",
]
DEPARTMENTS = [
    "Makine Mühendisliği", "Mekatronik Mühendisliği", "Bilgisayar Mühendisliği",
    "Kimya Mühendisliği", "Çevre Mühendisliği", "Endüstri Mühendisliği",
    "Gıda Mühendisliği", "Elektrik-Elektronik Mühendisliği",
]
SKILLS = [
    "Python", "SolidWorks", "Sonlu Elemanlar Analizi", "PLC ve Otomasyon",
    "Bilgisayarlı Görü", "Atık Su Arıtımı", "Membran Prosesleri", "Gıda Ambalajlama",
    "Üretim Planlama", "Gömülü Sistemler ve IoT", "Robotik ve Navigasyon",
]
CITIES = ["İstanbul", "Ankara", "İzmir", "Bursa"]


ALIASES = {
    "itu": "İstanbul Teknik Üniversitesi",
    "ytu": "Yıldız Teknik Üniversitesi",
    "odtu": "Orta Doğu Teknik Üniversitesi",
    "boun": "Boğaziçi Üniversitesi",
}


def parse_talent_query(query: str) -> dict[str, Any]:
    normalized = normalize(query)
    universities = [item for item in UNIVERSITIES if normalize(item) in normalized]
    for alias, full_name in ALIASES.items():
        if alias in normalized and full_name not in universities:
            universities.append(full_name)
    departments = [item for item in DEPARTMENTS if normalize(item) in normalized]
    skills = [item for item in SKILLS if normalize(item) in normalized]
    cities = [item for item in CITIES if normalize(item) in normalized]
    year_match = re.search(r"([1-6])\.?\s*sinif", normalized)
    request_type = None
    if "staj" in normalized:
        request_type = "internship"
    elif "aday muhendis" in normalized:
        request_type = "candidate_engineer"
    elif "proje" in normalized:
        request_type = "project"
    remote_allowed = True if "uzaktan" in normalized else None
    questions: list[str] = []
    if not skills:
        questions.append("Hangi teknik yetkinlikler zorunlu olmalı?")
    if not cities and remote_allowed is None:
        questions.append("Çalışma lokasyonu veya uzaktan çalışma tercihi nedir?")
    if request_type is None:
        questions.append("Stajyer, aday mühendis veya proje öğrencisi mi arıyorsunuz?")
    return {
        "universities": universities,
        "departments": departments,
        "skills": skills,
        "cities": cities,
        "minimum_year": int(year_match.group(1)) if year_match else None,
        "request_type": request_type,
        "remote_allowed": remote_allowed,
        "clarification_questions": questions,
    }


def parse_talent_query_with_ai(query: str, ai_mode: str = "auto") -> tuple[dict[str, Any], str, str | None]:
    local_filters = parse_talent_query(query)
    if ai_mode == "local":
        return local_filters, "local_rule_engine", None
    try:
        ai_filters = generate_json(TALENT_SYSTEM_PROMPT, {"query": query})
        safe_filters = {
            "universities": [item for item in ai_filters.get("universities", []) if item in UNIVERSITIES],
            "departments": [item for item in ai_filters.get("departments", []) if item in DEPARTMENTS],
            "skills": [item for item in ai_filters.get("skills", []) if item in SKILLS],
            "cities": [item for item in ai_filters.get("cities", []) if item in CITIES],
            "minimum_year": ai_filters.get("minimum_year"),
            "request_type": ai_filters.get("request_type"),
            "remote_allowed": ai_filters.get("remote_allowed"),
            "clarification_questions": ai_filters.get("clarification_questions", []),
        }
        for key in ("universities", "departments", "skills", "cities"):
            if not safe_filters[key]:
                safe_filters[key] = local_filters[key]
        return safe_filters, "gemini", None
    except AIUnavailable as exc:
        if ai_mode == "gemini":
            raise
        return local_filters, "local_rule_engine", str(exc)


def _contains_filter(value: str, accepted: list[str]) -> bool:
    return not accepted or any(normalize(item) in normalize(value) for item in accepted)


def search_students(filters: dict[str, Any], top_k: int = 5) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for student in get_candidates("student"):
        if not student.get("verified") or not student.get("available") or not student.get("searchable"):
            continue
        if not _contains_filter(student["university"], filters.get("universities", [])):
            continue
        if not _contains_filter(student["department"], filters.get("departments", [])):
            continue
        if filters.get("cities") and student.get("city") not in filters["cities"]:
            if not (filters.get("remote_allowed") and student.get("remote")):
                continue
        if filters.get("minimum_year") and student.get("year", 0) < filters["minimum_year"]:
            continue
        requested_skills = filters.get("skills", [])
        skill_matches = [skill for skill in requested_skills if normalize(skill) in {normalize(x) for x in student["skills"]}]
        if requested_skills and not skill_matches:
            continue
        score = 50
        score += min(30, len(skill_matches) * 12)
        score += 10 if filters.get("universities") else 0
        score += 5 if filters.get("departments") else 0
        score += 5 if filters.get("cities") and student.get("city") in filters["cities"] else 0
        results.append({
            "candidate": student,
            "score": min(score, 100),
            "matched_skills": skill_matches,
        })
    results.sort(key=lambda item: (-item["score"], item["candidate"]["name"]))
    return results[:top_k]
