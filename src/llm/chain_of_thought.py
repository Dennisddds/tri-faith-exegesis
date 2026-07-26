"""Chain-of-thought scripture interpretation using DeepSeek V4 Pro thinking mode."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config import INTERP_DIR, ensure_data_dirs
from src.llm.deepseek_client import DeepSeekClient
from src.llm.prompts import INTERPRET_USER, SYSTEM_INTERPRETER


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Models occasionally emit literal control chars inside JSON strings.
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


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(p for p in parts if p)
    if isinstance(value, dict):
        if any(k in value for k in ("text", "content", "html")):
            return _as_text(value.get("text") or value.get("content") or value.get("html") or "")
        # Bilara-style segment map: { "mn10:1.1": "....", ... }
        parts = []
        for key in sorted(value.keys()):
            chunk = _as_text(value[key]).strip()
            if chunk and chunk not in {"{}", "{ }"}:
                parts.append(chunk)
        return "\n".join(parts)
    return str(value)


def _primary_and_secondary(record: dict[str, Any], tradition: str) -> tuple[str, str, str, str, str]:
    if tradition == "buddhism":
        editions = record.get("editions") or []
        pali = next((e for e in editions if e.get("language") == "pli" and e.get("text")), None)
        eng = next((e for e in editions if e.get("language") == "en" and e.get("text")), None)
        primary = _as_text((pali or eng or {}).get("text"))
        secondary = _as_text((eng or {}).get("text")) if pali else ""
        ref = record.get("uid") or ""
        title = record.get("title") or ref
        note = record.get("corpus") or ""
        return primary, secondary, ref, title, note

    if tradition == "christianity":
        return (
            _as_text(record.get("text")),
            "",
            record.get("ref") or "",
            record.get("ref") or "",
            record.get("corpus") or "",
        )

    # islam
    return (
        _as_text(record.get("text_arabic")),
        _as_text(record.get("text_english")),
        record.get("ref") or "",
        record.get("name") or record.get("ref") or "",
        record.get("corpus") or "",
    )


def interpret_passage(
    record: dict[str, Any],
    *,
    tradition: str,
    client: DeepSeekClient | None = None,
    save: bool = True,
) -> dict[str, Any]:
    ensure_data_dirs()
    client = client or DeepSeekClient()
    primary, secondary, ref, title, note = _primary_and_secondary(record, tradition)
    if not primary.strip():
        raise ValueError(f"No primary text available for {tradition}:{ref}")

    # Truncate extremely long texts to keep cost/latency reasonable for pilot runs.
    primary_use = primary[:8000]
    secondary_use = secondary[:8000]

    user = INTERPRET_USER.format(
        tradition=tradition,
        corpus_note=note,
        ref=ref,
        title=title,
        primary_text=primary_use,
        secondary_text=secondary_use or "(无)",
    )
    resp = client.chat(
        [
            {"role": "system", "content": SYSTEM_INTERPRETER},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        enable_thinking=True,
    )
    parsed = _extract_json(resp.content)
    result = {
        "tradition": tradition,
        "ref": ref,
        "title": title,
        "model": client.model,
        "reasoning_content": resp.reasoning_content,
        "interpretation": parsed,
        "primary_text_excerpt": primary_use[:1200],
        "secondary_text_excerpt": secondary_use[:1200],
    }
    if save:
        slug = re.sub(r"[^\w\-]+", "_", str(ref)).strip("_").lower()
        path = INTERP_DIR / tradition / f"{slug}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["path"] = str(path)
    return result
