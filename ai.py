from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.config import settings


class AIUnavailable(RuntimeError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def generate_json(system_instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not settings.gemini_enabled:
        raise AIUnavailable("GEMINI_API_KEY tanımlı değil.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(payload, ensure_ascii=False)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise AIUnavailable(f"Gemini yanıtı alınamadı: {exc}") from exc


PROBLEM_SYSTEM_PROMPT = """
Sen Türkçe sanayi problemlerini akademik Ar-Ge çağrısına dönüştüren bir asistansın.
Sadece JSON döndür. Asla kişi veya kurum uydurma. Gizli firma/makine/ölçü bilgisini
safe_public_summary alanına yazma. Şu anahtarları üret:
fields, skills, methods, sectors, project_types (hepsi string listesi),
estimated_duration (string), safe_public_summary (string), questions
(key ve question alanlı nesne listesi). Eksik olmayan bilgi için soru sorma.
""".strip()


TALENT_SYSTEM_PROMPT = """
Sen sanayicinin doğal dildeki öğrenci arama isteğini yalnızca filtre JSON'una çevirirsin.
Asla öğrenci veya sonuç uydurma. Şu anahtarları üret: universities, departments,
skills, cities (string listeleri), minimum_year (integer veya null),
request_type (internship, candidate_engineer, project veya null), remote_allowed
(boolean veya null), clarification_questions (string listesi).
""".strip()

