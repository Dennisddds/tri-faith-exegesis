"""Crawl Qur'anic tafsir as ground-truth commentaries (Ibn Kathir)."""

from __future__ import annotations

from rich.console import Console
from rich.progress import track

from src.corpus.inventory import (
    ensure_corpus_dirs,
    list_units,
    save_gt,
    save_gt_manifest,
)
from src.corpus.schema import GTUnit
from src.crawlers.base import http_get_json, polite_pause
from src.crawlers.commentaries import COMMENTARIES

console = Console()

TAFSIR_SLUGS = [
    "en-tafisr-ibn-kathir",  # common CDN slug (typo variant used by qurancdn)
    "en-tafsir-ibn-kathir",
]


def _strip_html(raw: str) -> str:
    try:
        from bs4 import BeautifulSoup

        return BeautifulSoup(raw, "lxml").get_text("\n", strip=True)
    except Exception:  # noqa: BLE001
        return raw


def _fetch_ibn_kathir(verse_key: str) -> str:
    last_err: Exception | None = None
    for slug in TAFSIR_SLUGS:
        url = f"https://api.qurancdn.com/api/qdc/tafsirs/{slug}/by_ayah/{verse_key}"
        try:
            data = http_get_json(url, timeout=90, params={"locale": "en"})
            polite_pause(0.12)
            tafsir = data.get("tafsir") or data
            text = tafsir.get("text") if isinstance(tafsir, dict) else ""
            if text:
                return _strip_html(text)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    # AlQuran cloud secondary attempt (edition id may vary)
    try:
        data = http_get_json(f"https://api.alquran.cloud/v1/ayah/{verse_key}/editions/en.ibn-kathir", timeout=60)
        polite_pause(0.12)
        payload = data.get("data") or {}
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        text = payload.get("text") or ""
        if text:
            return _strip_html(text)
    except Exception as exc:  # noqa: BLE001
        last_err = exc
    raise RuntimeError(f"No tafsir for {verse_key}: {last_err}")


def crawl_islam_gt(*, max_units: int | None = None, use_seed_fallback: bool = True) -> list[str]:
    """Fetch GT tafsir for each Qur'an unit_id in the corpus manifest."""
    ensure_corpus_dirs()
    unit_ids = list_units("islam")
    if not unit_ids:
        raise RuntimeError("Islam corpus empty. Run: python main.py crawl-full --tradition islam")
    if max_units:
        unit_ids = unit_ids[:max_units]

    gt_ids: list[str] = []
    console.print(f"[bold]Islam GT (Ibn Kathir): {len(unit_ids)} ayahs[/bold]")
    for unit_id in track(unit_ids, description="Tafsir GT"):
        gt_id = f"ibn_kathir::{unit_id}"
        try:
            text = _fetch_ibn_kathir(unit_id)
            gt = GTUnit(
                tradition="islam",
                gt_id=gt_id,
                aligns_to=unit_id,
                author="Ibn Kathir",
                work="Tafsir al-Qur'an al-Azim",
                era="14th century CE",
                stance="hadith-forward Sunni tafsir (GT)",
                text=text,
                source=f"https://api.qurancdn.com/api/qdc/tafsirs/en-tafisr-ibn-kathir/by_ayah/{unit_id}",
            )
        except Exception as exc:  # noqa: BLE001
            if not use_seed_fallback:
                console.print(f"[yellow]skip GT {unit_id}: {exc}[/yellow]")
                continue
            # fallback: reuse curated seed if aligns
            seed = next(
                (c for c in COMMENTARIES["islam"] if any(a in unit_id for a in [x.split(":")[0] + ":" for x in c.get("aligns_to", [])]) or unit_id in c.get("aligns_to", [])),
                COMMENTARIES["islam"][0],
            )
            gt = GTUnit(
                tradition="islam",
                gt_id=gt_id,
                aligns_to=unit_id,
                author=seed["author"],
                work=seed["work"],
                era=seed.get("era", ""),
                stance=seed.get("stance", "") + " (seed fallback GT)",
                text=seed["text"],
                source="seed://commentaries",
                meta={"fallback_reason": str(exc)},
            )
        save_gt(gt)
        gt_ids.append(gt.gt_id)

    save_gt_manifest("islam", gt_ids, extra={"primary_gt": "ibn_kathir", "role": "ground_truth"})
    return gt_ids
