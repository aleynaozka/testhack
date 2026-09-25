from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.config import settings


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EDU_ROLES = {"student", "academic"}


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email.strip().lower()))


def is_edu_tr_email(email: str) -> bool:
    normalized = email.strip().lower()
    if not is_valid_email(normalized):
        return False
    domain = normalized.rsplit("@", 1)[1]
    return domain.endswith(".edu.tr")


def validate_registration(email: str, role: str) -> dict[str, Any]:
    normalized = email.strip().lower()
    errors: list[str] = []
    if not is_valid_email(normalized):
        errors.append("Geçerli bir e-posta adresi girilmelidir.")
    if role in EDU_ROLES and not is_edu_tr_email(normalized):
        errors.append("Öğrenci ve akademisyen hesapları .edu.tr uzantılı e-posta kullanmalıdır.")
    return {
        "valid": not errors,
        "normalized_email": normalized,
        "role": role,
        "requires_email_confirmation": True,
        "requires_admin_approval": role == "academic",
        "errors": errors,
    }


INDUSTRY_METHODS = {
    "entrepreneur": {"google_oauth", "work_email", "manual_review"},
    "company_without_rd": {"google_oauth", "work_email", "manual_review"},
    "rd_center": {"work_email", "manual_review", "rd_center_document"},
}


def validate_industry_verification(
    industry_type: str,
    method: str,
    email: str,
    company_name: str | None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not is_valid_email(email):
        errors.append("Geçerli bir e-posta adresi girilmelidir.")
    if method not in INDUSTRY_METHODS[industry_type]:
        errors.append("Bu firma profili için seçilen doğrulama yöntemi kullanılamaz.")
    if industry_type != "entrepreneur" and not company_name:
        errors.append("Firma adı zorunludur.")
    return {
        "valid": not errors,
        "status": "pending" if not errors else "rejected",
        "industry_type": industry_type,
        "method": method,
        "allowed_methods": sorted(INDUSTRY_METHODS[industry_type]),
        "requires_admin_review": industry_type == "rd_center" or method in {"manual_review", "rd_center_document"},
        "errors": errors,
    }


def fetch_supabase_user(bearer_token: str) -> dict[str, Any]:
    """Validate a Supabase access token and return its confirmed user.

    The service-role key is deliberately not used. This endpoint only needs the
    public/publishable key plus the user's Bearer token.
    """
    if not settings.supabase_enabled:
        raise RuntimeError("Supabase environment variables are not configured.")
    request = urllib.request.Request(
        f"{settings.supabase_url}/auth/v1/user",
        headers={
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {bearer_token}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PermissionError("Supabase oturumu doğrulanamadı.") from exc
    return {
        "id": payload.get("id"),
        "email": payload.get("email"),
        "email_confirmed": bool(payload.get("email_confirmed_at")),
        "metadata": payload.get("user_metadata", {}),
    }

