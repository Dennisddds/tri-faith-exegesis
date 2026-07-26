"""
Crawl Qur'anic text via AlQuran Cloud API, with CDN / offline fallbacks.
"""

from __future__ import annotations

from typing import Any

from config import RAW_DIR, ensure_data_dirs
from src.crawlers.base import http_get_json, polite_pause, save_json
from src.crawlers.seed_data import ISLAM_SEEDS

DEFAULT_UNITS = [
    {"surah": 1, "from_ayah": 1, "to_ayah": 7, "name": "Al-Fatihah"},
    {"surah": 2, "from_ayah": 1, "to_ayah": 5, "name": "Al-Baqarah (opening)"},
    {"surah": 2, "from_ayah": 255, "to_ayah": 255, "name": "Ayat al-Kursi"},
    {"surah": 24, "from_ayah": 35, "to_ayah": 35, "name": "An-Nur (Light Verse)"},
    {"surah": 36, "from_ayah": 1, "to_ayah": 12, "name": "Ya-Sin (opening)"},
    {"surah": 112, "from_ayah": 1, "to_ayah": 4, "name": "Al-Ikhlas"},
]


def _fetch_ayah_alquran(surah: int, ayah: int) -> dict[str, Any]:
    url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/editions/quran-uthmani,en.sahih"
    data = http_get_json(url, timeout=90)
    polite_pause()
    editions = data.get("data") or []
    arabic = next((e for e in editions if e.get("edition", {}).get("identifier") == "quran-uthmani"), None)
    english = next((e for e in editions if e.get("edition", {}).get("identifier") == "en.sahih"), None)
    return {
        "surah": surah,
        "ayah": ayah,
        "arabic": (arabic or {}).get("text", ""),
        "english": (english or {}).get("text", ""),
        "source": f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}",
    }


def _fetch_ayah_cdn(surah: int, ayah: int) -> dict[str, Any]:
    # fawazahmed0 quran-api on jsDelivr (often more reachable)
    ar = http_get_json(
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/ara-quranuthmanihaf/{surah}/{ayah}.json",
        timeout=60,
    )
    polite_pause(0.2)
    en = http_get_json(
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-sahih/{surah}/{ayah}.json",
        timeout=60,
    )
    polite_pause(0.2)
    return {
        "surah": surah,
        "ayah": ayah,
        "arabic": ar.get("text") or "",
        "english": en.get("text") or "",
        "source": f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/.../{surah}/{ayah}.json",
    }


def _fetch_ayah(surah: int, ayah: int) -> dict[str, Any]:
    try:
        return _fetch_ayah_alquran(surah, ayah)
    except Exception:
        return _fetch_ayah_cdn(surah, ayah)


def _fetch_unit(unit: dict[str, Any]) -> dict[str, Any]:
    ayahs = []
    for n in range(unit["from_ayah"], unit["to_ayah"] + 1):
        ayahs.append(_fetch_ayah(unit["surah"], n))
    arabic_text = "\n".join(f"{a['ayah']}. {a['arabic']}" for a in ayahs if a["arabic"])
    english_text = "\n".join(f"{a['ayah']}. {a['english']}" for a in ayahs if a["english"])
    ref = f"{unit['surah']}:{unit['from_ayah']}-{unit['to_ayah']}"
    return {
        "tradition": "islam",
        "corpus": "Qur'an (Arabic Uthmani; remote API or CDN)",
        "ref": ref,
        "name": unit["name"],
        "surah": unit["surah"],
        "from_ayah": unit["from_ayah"],
        "to_ayah": unit["to_ayah"],
        "ayahs": ayahs,
        "text_arabic": arabic_text,
        "text_english": english_text,
        "primary_language": "ar",
        "note": "Arabic Uthmani text is treated as the primary scriptural layer; English is gloss only.",
    }


def _save_seed_corpus() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for record in ISLAM_SEEDS:
        slug = f"surah_{record['surah']}_{record['from_ayah']}_{record['to_ayah']}"
        out = RAW_DIR / "islam" / f"{slug}.json"
        save_json(out, record)
        item = dict(record)
        item["path"] = str(out)
        results.append(item)
    return results


def crawl_islam(units: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    ensure_data_dirs()
    units = units or DEFAULT_UNITS
    results: list[dict[str, Any]] = []
    try:
        # Probe first ayah; if unreachable, fall back to seeds for whole tradition.
        _fetch_ayah(1, 1)
        for unit in units:
            record = _fetch_unit(unit)
            slug = f"surah_{unit['surah']}_{unit['from_ayah']}_{unit['to_ayah']}"
            out = RAW_DIR / "islam" / f"{slug}.json"
            save_json(out, record)
            record["path"] = str(out)
            results.append(record)
    except Exception as exc:  # noqa: BLE001
        results = _save_seed_corpus()
        for r in results:
            r["fallback_reason"] = str(exc)

    index = {
        "tradition": "islam",
        "count": len(results),
        "items": [r["ref"] for r in results],
        "fallback": any(r.get("fallback_reason") for r in results),
    }
    save_json(RAW_DIR / "islam" / "index.json", index)
    return results
