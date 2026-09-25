from __future__ import annotations

import os
from dataclasses import dataclass


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ISOV Bridge API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: tuple[str, ...] = tuple(_csv_env("CORS_ORIGINS", "http://localhost:5173"))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    supabase_url: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    auth_mode: str = os.getenv("AUTH_MODE", "demo")

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)


settings = Settings()

