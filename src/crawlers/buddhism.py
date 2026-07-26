"""
Crawl early Buddhist texts via SuttaCentral public API, with offline seed fallback.
"""

from __future__ import annotations

from typing import Any

from config import RAW_DIR, ensure_data_dirs
from src.crawlers.base import http_get_json, polite_pause, save_json
from src.crawlers.seed_data import BUDDHISM_SEEDS

DEFAULT_SUTTAS = [
    "mn10",
    "sn56.11",
    "dn22",
    "an3.65",
    "snp1.8",
]


def _strip_html(raw: str) -> str:
    try:
        from bs4 import BeautifulSoup

        return BeautifulSoup(raw, "lxml").get_text("\n", strip=True)
    except Exception:  # noqa: BLE001
        return raw


def _join_segments(segments: Any) -> str:
    if isinstance(segments, str):
        return _strip_html(segments)
    if not isinstance(segments, dict):
        return ""
    parts: list[str] = []
    for key in sorted(segments.keys(), key=lambda k: [int(x) if x.isdigit() else x for x in str(k).replace(":", ".").split(".")]):
        val = segments[key]
        if isinstance(val, dict):
            val = val.get("value") or val.get("text") or ""
        text = _strip_html(str(val or "")).strip()
        # Skip empty Bilara HTML templates like "{}"
        if not text or text in {"{}", "{ }"}:
            continue
        parts.append(text)
    return "\n".join(parts)


def _fetch_bilara(uid: str, author: str = "sujato") -> dict[str, Any] | None:
    data = http_get_json(f"https://suttacentral.net/api/bilarasuttas/{uid}/{author}", timeout=90)
    polite_pause()
    root = _join_segments(data.get("root_text") or data.get("rootText") or {})
    translation = _join_segments(data.get("translation_text") or data.get("translationText") or {})
    # Some payloads nest under keys differently.
    if not translation:
        translation = _join_segments(data.get("html_text") or data.get("text") or {})
    if not root and not translation:
        return None
    editions: list[dict[str, Any]] = []
    if root:
        editions.append(
            {
                "language": "pli",
                "author_uid": "root",
                "title": uid,
                "text": root,
                "source": f"https://suttacentral.net/{uid}/pli/ms",
            }
        )
    if translation:
        editions.append(
            {
                "language": "en",
                "author_uid": author,
                "title": uid,
                "text": translation,
                "source": f"https://suttacentral.net/{uid}/en/{author}",
            }
        )
    return {
        "tradition": "buddhism",
        "corpus": "Pali Tipitaka (Bilara / SuttaCentral)",
        "uid": uid,
        "title": (data.get("msg") or {}).get("title") if isinstance(data.get("msg"), dict) else uid,
        "editions": editions,
        "primary_language": "pli" if root else "en",
        "note": "Pali root text treated as earliest widely accessible canonical form; translations are secondary.",
    }


def _fetch_legacy_html(uid: str, author: str = "sujato") -> dict[str, Any] | None:
    data = http_get_json(
        f"https://suttacentral.net/api/suttas/{uid}/{author}",
        params={"lang": "en"},
        timeout=90,
    )
    polite_pause()
    text_html = data.get("text") or data.get("content") or ""
    text = _join_segments(text_html) if isinstance(text_html, dict) else _strip_html(str(text_html))
    if not text or set(text.replace("\n", "")) <= {"{", "}", " "}:
        return None
    return {
        "tradition": "buddhism",
        "corpus": "Pali Tipitaka (SuttaCentral HTML)",
        "uid": uid,
        "title": data.get("translation", {}).get("title") or uid,
        "editions": [
            {
                "language": "en",
                "author_uid": author,
                "title": uid,
                "text": text,
                "source": f"https://suttacentral.net/{uid}/en/{author}",
            }
        ],
        "primary_language": "en",
        "note": "English translation used when Pali Bilara payload unavailable.",
    }


def _seed_for(uid: str) -> dict[str, Any] | None:
    for item in BUDDHISM_SEEDS:
        if item.get("uid") == uid:
            return dict(item)
    return None


def _fetch_sutta(uid: str) -> dict[str, Any]:
    for author in ("sujato", "thanissaro", "bodhi"):
        try:
            record = _fetch_bilara(uid, author=author)
            if record and any(e.get("text") for e in record.get("editions", [])):
                # Improve title via suttaplex when possible.
                try:
                    suttaplex = http_get_json(f"https://suttacentral.net/api/suttaplex/{uid}", timeout=60)
                    polite_pause(0.2)
                    if isinstance(suttaplex, list) and suttaplex:
                        record["title"] = (
                            suttaplex[0].get("original_title")
                            or suttaplex[0].get("translated_title")
                            or record["title"]
                        )
                    elif isinstance(suttaplex, dict):
                        record["title"] = (
                            suttaplex.get("original_title")
                            or suttaplex.get("translated_title")
                            or record["title"]
                        )
                except Exception:  # noqa: BLE001
                    pass
                return record
        except Exception:  # noqa: BLE001
            continue

    for author in ("sujato", "thanissaro"):
        try:
            record = _fetch_legacy_html(uid, author=author)
            if record:
                return record
        except Exception:  # noqa: BLE001
            continue

    seed = _seed_for(uid)
    if seed:
        seed["fallback_reason"] = "remote sutta text unavailable or empty templates"
        return seed

    raise RuntimeError(f"Unable to fetch usable text for sutta {uid}")


def crawl_buddhism(uids: list[str] | None = None) -> list[dict[str, Any]]:
    ensure_data_dirs()
    uids = uids or DEFAULT_SUTTAS
    results: list[dict[str, Any]] = []
    for uid in uids:
        try:
            record = _fetch_sutta(uid)
        except Exception as exc:  # noqa: BLE001
            record = _seed_for(uid) or {
                "tradition": "buddhism",
                "uid": uid,
                "title": uid,
                "editions": [],
                "error": str(exc),
            }
            if "fallback_reason" not in record:
                record["fallback_reason"] = str(exc)
        out = RAW_DIR / "buddhism" / f"{uid.replace('.', '_')}.json"
        save_json(out, record)
        record["path"] = str(out)
        results.append(record)

    # Ensure at least seed corpus exists if all remote failed empty.
    if not any(any(e.get("text") for e in (r.get("editions") or [])) for r in results):
        for seed in BUDDHISM_SEEDS:
            out = RAW_DIR / "buddhism" / f"{seed['uid'].replace('.', '_')}.json"
            save_json(out, seed)
            item = dict(seed)
            item["path"] = str(out)
            results.append(item)

    index = {
        "tradition": "buddhism",
        "count": len(results),
        "items": [r.get("uid") for r in results],
        "fallback": any(r.get("fallback_reason") for r in results),
    }
    save_json(RAW_DIR / "buddhism" / "index.json", index)
    return results
