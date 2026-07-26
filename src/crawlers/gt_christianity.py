"""
Christianity GT commentaries.

Primary remote attempt: Matthew Henry via public mirrors.
Also loads any manually dropped files under data/gt_sources/christianity/.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.progress import track

from config import DATA_DIR
from src.corpus.inventory import (
    ensure_corpus_dirs,
    iter_units,
    list_units,
    save_gt,
    save_gt_manifest,
)
from src.corpus.schema import GTUnit
from src.crawlers.base import http_get_text, polite_pause
from src.crawlers.commentaries import COMMENTARIES

console = Console()
GT_SOURCES = DATA_DIR / "gt_sources" / "christianity"

# Common slug map for Matthew Henry mirrors
BOOK_SLUGS = {
    "Genesis": "genesis", "Exodus": "exodus", "Leviticus": "leviticus", "Numbers": "numbers",
    "Deuteronomy": "deuteronomy", "Joshua": "joshua", "Judges": "judges", "Ruth": "ruth",
    "1 Samuel": "1_samuel", "2 Samuel": "2_samuel", "1 Kings": "1_kings", "2 Kings": "2_kings",
    "Psalms": "psalms", "Proverbs": "proverbs", "Isaiah": "isaiah", "Jeremiah": "jeremiah",
    "Matthew": "matthew", "Mark": "mark", "Luke": "luke", "John": "john", "Acts": "acts",
    "Romans": "romans", "1 Corinthians": "1_corinthians", "2 Corinthians": "2_corinthians",
    "Galatians": "galatians", "Ephesians": "ephesians", "Philippians": "philippians",
    "Colossians": "colossians", "Hebrews": "hebrews", "James": "james", "Revelation": "revelation",
}


def _load_local_gt_files() -> dict[str, str]:
    """Map unit_id/ref -> commentary text from dropped local files."""
    mapping: dict[str, str] = {}
    if not GT_SOURCES.exists():
        GT_SOURCES.mkdir(parents=True, exist_ok=True)
        return mapping
    for path in GT_SOURCES.rglob("*"):
        if path.suffix.lower() not in {".txt", ".md", ".json"}:
            continue
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "text" in data:
                key = str(data.get("aligns_to") or data.get("unit_id") or path.stem)
                mapping[key] = str(data["text"])
            elif isinstance(data, list):
                for item in data:
                    key = str(item.get("aligns_to") or item.get("unit_id") or "")
                    if key and item.get("text"):
                        mapping[key] = str(item["text"])
        else:
            mapping[path.stem] = path.read_text(encoding="utf-8")
    return mapping


def _fetch_matthew_henry(book: str, chapter: int) -> str:
    slug = BOOK_SLUGS.get(book) or book.lower().replace(" ", "_")
    candidates = [
        f"https://cdn.jsdelivr.net/gh/aruljohn/Matthew-Henry-Commentary@master/{slug}/{chapter}.txt",
        f"https://raw.githubusercontent.com/aruljohn/Matthew-Henry-Commentary/master/{slug}/{chapter}.txt",
    ]
    last_err: Exception | None = None
    for url in candidates:
        try:
            text = http_get_text(url, timeout=60)
            polite_pause(0.1)
            if text and "<html" not in text.lower()[:40] and len(text.strip()) > 40:
                return text.strip()
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise RuntimeError(f"Matthew Henry unavailable for {book} {chapter}: {last_err}")


def crawl_christianity_gt(*, max_units: int | None = None) -> list[str]:
    ensure_corpus_dirs()
    unit_ids = list_units("christianity")
    if not unit_ids:
        raise RuntimeError("Christianity corpus empty. Run: python main.py crawl-full --tradition christianity")
    if max_units:
        unit_ids = unit_ids[:max_units]

    local = _load_local_gt_files()
    gt_ids: list[str] = []
    console.print(f"[bold]Christianity GT (Matthew Henry / local): {len(unit_ids)} chapters[/bold]")

    units = {u.unit_id: u for u in iter_units("christianity")}
    for unit_id in track(unit_ids, description="Commentary GT"):
        unit = units.get(unit_id)
        if not unit:
            continue
        book = unit.meta.get("book") or unit.ref.rsplit(" ", 1)[0]
        chapter = int(unit.meta.get("chapter") or unit.ref.rsplit(" ", 1)[-1])
        gt_id = f"matthew_henry::{unit_id}"
        text = local.get(unit_id) or local.get(unit.ref) or local.get(f"{book}_{chapter}")
        meta = {}
        if not text:
            try:
                text = _fetch_matthew_henry(str(book), chapter)
            except Exception as exc:  # noqa: BLE001
                seed = next(
                    (c for c in COMMENTARIES["christianity"] if any(a.lower() in unit.ref.lower() for a in c.get("aligns_to", []))),
                    COMMENTARIES["christianity"][0],
                )
                text = seed["text"]
                meta = {"fallback_reason": str(exc), "seed_author": seed["author"]}
        gt = GTUnit(
            tradition="christianity",
            gt_id=gt_id,
            aligns_to=unit_id,
            author="Matthew Henry" if "seed_author" not in meta else meta["seed_author"],
            work="Commentary on the Whole Bible (public-domain tradition / mirror)",
            era="17th–18th century CE",
            stance="Protestant pastoral-exegetical commentary (GT)",
            text=text,
            source="matthew_henry_mirror_or_local",
            meta=meta,
        )
        save_gt(gt)
        gt_ids.append(gt.gt_id)

    save_gt_manifest("christianity", gt_ids, extra={"primary_gt": "matthew_henry", "role": "ground_truth"})
    return gt_ids
