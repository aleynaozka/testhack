from __future__ import annotations

import re
import unicodedata


TURKISH_MAP = str.maketrans({
    "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
})


def normalize(value: str) -> str:
    value = value.translate(TURKISH_MAP).lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value)


def contains_any(text: str, terms: list[str]) -> bool:
    normalized_text = normalize(text)
    return any(normalize(term) in normalized_text for term in terms)


def set_overlap(left: list[str], right: list[str]) -> set[str]:
    right_map = {normalize(item): item for item in right}
    return {item for item in left if normalize(item) in right_map}

