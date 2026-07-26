"""Crawl the full Qur'an (all ayahs) with resilient mirrors + local cache."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.progress import track

from config import DATA_DIR, get_settings
from src.corpus.inventory import ensure_corpus_dirs, save_manifest, save_unit
from src.corpus.schema import ScriptureUnit
from src.crawlers.base import polite_pause

console = Console()
CACHE_PATH = DATA_DIR / "cache" / "quran_ar_en.json"

# ayah counts per surah 1..114
AYAH_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53,
    89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12,
    12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26,
    30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]


def _client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(
        timeout=45,
        headers={"User-Agent": settings.user_agent, "Accept": "application/json"},
        follow_redirects=True,
    )


def _get_json(url: str) -> Any:
    with _client() as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()


def _load_cache() -> dict[str, dict[str, str]] | None:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return None


def _save_cache(cache: dict[str, dict[str, str]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def _build_cache_from_cdn(max_surah: int | None = None) -> dict[str, dict[str, str]]:
    """Build ayah cache via per-ayah jsDelivr endpoints (usually reachable)."""
    cache = _load_cache() or {}
    last = max_surah or 114
    console.print(f"[bold]Building Qur'an cache via CDN (surah 1..{last})[/bold]")
    for surah in track(range(1, last + 1), description="Cache surahs"):
        n_ayah = AYAH_COUNTS[surah - 1]
        for ayah in range(1, n_ayah + 1):
            key = f"{surah}:{ayah}"
            if key in cache and cache[key].get("ar"):
                continue
            ar_url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/ara-quranuthmanihaf/{surah}/{ayah}.json"
            # English edition slug on this repo is often eng-saheeh or eng-clearquran
            en_urls = [
                f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-saheeh/{surah}/{ayah}.json",
                f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-clearquran/{surah}/{ayah}.json",
                f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-sahih/{surah}/{ayah}.json",
            ]
            ar_text = ""
            en_text = ""
            try:
                ar_text = str((_get_json(ar_url) or {}).get("text") or "").strip()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]AR fail {key}: {exc}[/yellow]")
            for eu in en_urls:
                try:
                    en_text = str((_get_json(eu) or {}).get("text") or "").strip()
                    if en_text:
                        break
                except Exception:
                    continue
            cache[key] = {"ar": ar_text, "en": en_text}
            polite_pause(0.05)
        _save_cache(cache)
    return cache


def _try_alquran_surah(surah: int) -> list[ScriptureUnit]:
    url = f"https://api.alquran.cloud/v1/surah/{surah}/editions/quran-uthmani,en.sahih"
    data = _get_json(url)
    editions = data.get("data") or []
    arabic = next((e for e in editions if e.get("edition", {}).get("identifier") == "quran-uthmani"), None)
    english = next((e for e in editions if e.get("edition", {}).get("identifier") == "en.sahih"), None)
    if not arabic:
        return []
    name = arabic.get("englishName") or f"Surah {surah}"
    en_map = {a.get("numberInSurah"): a.get("text", "") for a in (english or {}).get("ayahs") or []}
    units: list[ScriptureUnit] = []
    for ayah in arabic.get("ayahs") or []:
        n = ayah.get("numberInSurah")
        ref = f"{surah}:{n}"
        units.append(
            ScriptureUnit(
                tradition="islam",
                unit_id=ref,
                ref=ref,
                title=f"{name} {ref}",
                corpus="Qur'an Arabic Uthmani (full)",
                primary_language="ar",
                primary_text=(ayah.get("text") or "").strip(),
                secondary_text=(en_map.get(n) or "").strip(),
                source=f"https://api.alquran.cloud/v1/ayah/{ref}",
                meta={"surah": surah, "ayah": n, "surah_name": name},
            )
        )
    return units


def crawl_islam_full(*, max_surah: int | None = None) -> list[str]:
    ensure_corpus_dirs()
    unit_ids: list[str] = []
    last = max_surah or 114

    # Fast path: complete from cache / CDN builder
    cache = _load_cache()
    need_build = False
    if not cache:
        need_build = True
    else:
        for s in range(1, last + 1):
            for a in range(1, AYAH_COUNTS[s - 1] + 1):
                if f"{s}:{a}" not in cache:
                    need_build = True
                    break
            if need_build:
                break

    # Try AlQuran Cloud surah API first (few requests); on failure use CDN cache builder.
    used_source = "alquran.cloud"
    for surah in track(range(1, last + 1), description="Qur'an surahs"):
        units: list[ScriptureUnit] = []
        try:
            units = _try_alquran_surah(surah)
            polite_pause(0.1)
        except Exception:
            units = []

        if not units:
            used_source = "jsdelivr-cdn-cache"
            if need_build or not cache:
                cache = _build_cache_from_cdn(max_surah=last)
                need_build = False
            assert cache is not None
            for ayah in range(1, AYAH_COUNTS[surah - 1] + 1):
                key = f"{surah}:{ayah}"
                item = cache.get(key) or {}
                if not item.get("ar"):
                    continue
                units.append(
                    ScriptureUnit(
                        tradition="islam",
                        unit_id=key,
                        ref=key,
                        title=key,
                        corpus="Qur'an Arabic Uthmani (full, CDN cache)",
                        primary_language="ar",
                        primary_text=item.get("ar") or "",
                        secondary_text=item.get("en") or "",
                        source=f"cdn.jsdelivr.net/.../ara-quranuthmanihaf/{surah}/{ayah}.json",
                        meta={"surah": surah, "ayah": ayah},
                    )
                )

        for unit in units:
            save_unit(unit)
            unit_ids.append(unit.unit_id)

    save_manifest(
        "islam",
        unit_ids,
        extra={
            "granularity": "ayah",
            "surahs": last,
            "source": used_source,
            "expected_ayahs": sum(AYAH_COUNTS[:last]),
            "note": "Full Qur'an primary Arabic + English gloss; GT alignment uses tafsir",
        },
    )
    console.print(f"[green]Islam units: {len(unit_ids)} / expected {sum(AYAH_COUNTS[:last])}[/green]")
    return unit_ids
