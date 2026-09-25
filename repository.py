from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=4)
def load_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_candidates(role: str | None = None) -> list[dict[str, Any]]:
    candidates = load_json("candidates.json")
    if role is None:
        return [dict(candidate) for candidate in candidates]
    return [dict(candidate) for candidate in candidates if candidate["role"] == role]


def get_demo_problems() -> list[dict[str, Any]]:
    return [dict(problem) for problem in load_json("problems.json")]

