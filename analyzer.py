from __future__ import annotations

import re
from typing import Any

from app.services.ai import AIUnavailable, PROBLEM_SYSTEM_PROMPT, generate_json
from app.services.taxonomy import TAXONOMY
from app.services.text import contains_any


QUESTION_BANK = {
    "success_metric": "Projenin başarılı olduğunu hangi ölçülebilir sonuç gösterecek?",
    "available_data": "Elinizde ölçüm verisi, numune, çizim veya geçmiş kayıt bulunuyor mu?",
    "attempted_solutions": "Daha önce hangi çözümleri denediniz ve sonuçları ne oldu?",
    "timeline": "Çalışmanın tamamlanmasını istediğiniz yaklaşık süre nedir?",
    "work_location": "Çalışma sahada mı, uzaktan mı yoksa hibrit mi yürütülecek?",
    "confidentiality": "Problem için açık, maskelenmiş veya yüksek gizlilik seviyelerinden hangisini istiyorsunuz?",
}


def detect_taxonomy(text: str) -> dict[str, list[str]]:
    detected: dict[str, list[str]] = {}
    for category, items in TAXONOMY.items():
        detected[category] = [label for label, keywords in items.items() if contains_any(text, keywords)]
    return detected


def clarification_questions(
    industry_type: str,
    answers: dict[str, str] | None = None,
    skip: bool = False,
) -> list[dict[str, str]]:
    if skip:
        return []
    answers = answers or {}
    keys_by_type = {
        "entrepreneur": [
            "success_metric", "available_data", "attempted_solutions", "timeline",
            "work_location", "confidentiality",
        ],
        "company_without_rd": [
            "success_metric", "available_data", "attempted_solutions", "timeline", "confidentiality",
        ],
        "rd_center": ["confidentiality"],
    }
    return [
        {"key": key, "question": QUESTION_BANK[key]}
        for key in keys_by_type[industry_type]
        if not answers.get(key, "").strip()
    ]


def build_safe_summary(detected: dict[str, list[str]]) -> str:
    fields = detected.get("fields") or ["mühendislik"]
    skills = detected.get("skills") or ["teknik analiz"]
    methods = detected.get("methods") or ["uygun yöntemlerin belirlenmesi"]
    return (
        f"{', '.join(fields[:2])} alanında; {', '.join(skills[:3])} yetkinlikleri kullanılarak "
        f"{', '.join(methods[:2])} yürütülecek sanayi problemi için araştırma ekibi aranmaktadır."
    )


def estimate_duration(detected: dict[str, list[str]]) -> str:
    project_types = set(detected.get("project_types", []))
    if "Deneysel Ar-Ge" in project_types:
        return "6-9 ay"
    if "Modelleme ve Simülasyon" in project_types:
        return "4-7 ay"
    if "Yazılım Geliştirme" in project_types:
        return "3-6 ay"
    return "3-6 ay"


def local_problem_analysis(
    problem_text: str,
    industry_type: str,
    answers: dict[str, str] | None = None,
    skip_clarification: bool = False,
) -> dict[str, Any]:
    detected = detect_taxonomy(problem_text)
    questions = clarification_questions(industry_type, answers, skip_clarification)
    return {
        "provider": "local_rule_engine",
        "structured_problem": {
            "fields": detected["fields"],
            "skills": detected["skills"],
            "methods": detected["methods"],
            "sectors": detected["sectors"],
            "project_types": detected["project_types"],
            "estimated_duration": estimate_duration(detected),
            "safe_public_summary": build_safe_summary(detected),
        },
        "needs_clarification": bool(questions),
        "questions": questions,
        "assistant_mode": {
            "entrepreneur": "guided",
            "company_without_rd": "assisted",
            "rd_center": "expert",
        }[industry_type],
    }


def _controlled_ai_analysis(ai_payload: dict[str, Any], local_result: dict[str, Any]) -> dict[str, Any]:
    controlled: dict[str, list[str]] = {}
    for category in ("fields", "skills", "methods", "sectors", "project_types"):
        allowed = set(TAXONOMY[category])
        ai_values = ai_payload.get(category, [])
        controlled[category] = [value for value in ai_values if value in allowed]
        if not controlled[category]:
            controlled[category] = local_result["structured_problem"][category]
    questions = ai_payload.get("questions", local_result["questions"])
    questions = [item for item in questions if isinstance(item, dict) and item.get("question")][:6]
    return {
        **local_result,
        "provider": "gemini",
        "structured_problem": {
            **controlled,
            "estimated_duration": str(
                ai_payload.get("estimated_duration")
                or local_result["structured_problem"]["estimated_duration"]
            ),
            "safe_public_summary": str(
                ai_payload.get("safe_public_summary")
                or local_result["structured_problem"]["safe_public_summary"]
            ),
        },
        "needs_clarification": bool(questions),
        "questions": questions,
    }


def analyze_problem(
    problem_text: str,
    industry_type: str,
    answers: dict[str, str] | None = None,
    skip_clarification: bool = False,
    ai_mode: str = "auto",
    confidentiality: str = "masked",
) -> dict[str, Any]:
    local_result = local_problem_analysis(
        problem_text,
        industry_type,
        answers,
        skip_clarification,
    )
    if ai_mode == "local" or confidentiality == "strict":
        if confidentiality == "strict" and ai_mode != "local":
            local_result["warning"] = "Yüksek gizlilik nedeniyle problem harici AI servisine gönderilmedi."
        return local_result
    ai_problem_text = mask_sensitive_numbers(problem_text) if confidentiality == "masked" else problem_text
    payload = {
        "problem_text": ai_problem_text,
        "industry_type": industry_type,
        "answers": answers or {},
        "allowed_taxonomy": {key: list(values) for key, values in TAXONOMY.items()},
        "confidentiality": confidentiality,
    }
    try:
        ai_payload = generate_json(PROBLEM_SYSTEM_PROMPT, payload)
        return _controlled_ai_analysis(ai_payload, local_result)
    except AIUnavailable:
        if ai_mode == "gemini":
            raise
        local_result["warning"] = "AI kullanılamadığı için yerel kural motoru çalıştı."
        return local_result


def mask_sensitive_numbers(text: str) -> str:
    """Optional UI helper; not a substitute for a human confidentiality review."""
    text = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|kg|ton|bar|°c|c|rpm)\b", "[TEKNİK DEĞER]", text, flags=re.I)
    return re.sub(r"\b(?:hat|makine|ürün)\s*[-#:]*\s*[a-z0-9-]+", "[GİZLİ EKİPMAN]", text, flags=re.I)
