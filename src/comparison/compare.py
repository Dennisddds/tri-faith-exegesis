"""Compare model CoT readings with later commentaries."""

from __future__ import annotations

import json
import re
from typing import Any

from config import COMPARE_DIR, ensure_data_dirs
from src.crawlers.commentaries import commentaries_for
from src.llm.deepseek_client import DeepSeekClient
from src.llm.prompts import COMPARE_SYSTEM, COMPARE_USER


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)

    def _load(raw: str) -> dict[str, Any]:
        return json.loads(raw, strict=False)

    try:
        return _load(sanitized)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", sanitized, flags=re.DOTALL)
        if not match:
            raise
        return _load(match.group(0))


def compare_with_commentaries(
    interp_payload: dict[str, Any],
    *,
    client: DeepSeekClient | None = None,
    max_commentaries: int = 2,
) -> list[dict[str, Any]]:
    ensure_data_dirs()
    client = client or DeepSeekClient()
    tradition = interp_payload["tradition"]
    ref = str(interp_payload.get("ref") or "")
    commentaries = commentaries_for(tradition, ref)[:max_commentaries]

    model_view = interp_payload.get("interpretation") or {}
    model_compact = {
        "summary": model_view.get("summary"),
        "literal_reading": model_view.get("literal_reading"),
        "doctrinal_structure": model_view.get("doctrinal_structure"),
        "key_concepts": model_view.get("key_concepts"),
        "possible_misreadings": model_view.get("possible_misreadings"),
    }

    results: list[dict[str, Any]] = []
    for commentary in commentaries:
        user = COMPARE_USER.format(
            tradition=tradition,
            ref=ref,
            model_interpretation=json.dumps(model_compact, ensure_ascii=False, indent=2),
            author=commentary.get("author"),
            work=commentary.get("work"),
            era=commentary.get("era"),
            stance=commentary.get("stance"),
            commentary_text=commentary.get("text"),
        )
        resp = client.chat(
            [
                {"role": "system", "content": COMPARE_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            enable_thinking=True,
        )
        parsed = _extract_json(resp.content)
        item = {
            "tradition": tradition,
            "ref": ref,
            "commentary": {
                "id": commentary.get("id"),
                "author": commentary.get("author"),
                "work": commentary.get("work"),
                "era": commentary.get("era"),
                "stance": commentary.get("stance"),
            },
            "reasoning_content": resp.reasoning_content,
            "comparison": parsed,
        }
        results.append(item)

    slug = re.sub(r"[^\w\-]+", "_", ref).strip("_").lower()
    out = COMPARE_DIR / tradition / f"{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results
