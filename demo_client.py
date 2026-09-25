"""Backend çalışırken örnek istekleri terminalden gönderen küçük demo istemcisi."""

from __future__ import annotations

import json
import urllib.request


BASE_URL = "http://localhost:8000"


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    result = post(
        "/api/match",
        {
            "problem_text": "Tekstil atık suyunda membran ve adsorpsiyonla renk giderimini artırmak istiyoruz.",
            "target_role": "academic",
            "industry_type": "company_without_rd",
            "top_k": 3,
            "ai_mode": "local"
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

