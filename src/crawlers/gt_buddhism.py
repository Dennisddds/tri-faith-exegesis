"""
Buddhism GT commentaries.

Attempts SuttaCentral accompanying materials; falls back to curated Atthakatha /
Madhyamaka anchors and local files under data/gt_sources/buddhism/.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.progress import track

from config import DATA_DIR
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
GT_SOURCES = DATA_DIR / "gt_sources" / "buddhism"


def _load_local() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    GT_SOURCES.mkdir(parents=True, exist_ok=True)
    for path in GT_SOURCES.rglob("*"):
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            for item in items:
                key = str(item.get("aligns_to") or item.get("uid") or path.stem)
                mapping[key.lower()] = item
        elif path.suffix.lower() in {".txt", ".md"}:
            mapping[path.stem.lower()] = {
                "author": "local",
                "work": path.name,
                "text": path.read_text(encoding="utf-8"),
                "aligns_to": path.stem,
            }
    return mapping


def _fetch_sc_blurb(uid: str) -> str:
    data = http_get_json(f"https://suttacentral.net/api/suttaplex/{uid}", timeout=60)
    polite_pause(0.1)
    if isinstance(data, list) and data:
        node = data[0]
    elif isinstance(data, dict):
        node = data
    else:
        return ""
    parts = [
        node.get("blurb") or "",
        node.get("difficulty") or "",
    ]
    # Some payloads include translation description
    for key in ("translated_title", "original_title"):
        if node.get(key):
            parts.append(str(node[key]))
    return "\n".join(p for p in parts if p).strip()


def crawl_buddhism_gt(*, max_units: int | None = None) -> list[str]:
    ensure_corpus_dirs()
    unit_ids = list_units("buddhism")
    if not unit_ids:
        raise RuntimeError("Buddhism corpus empty. Run: python main.py crawl-full --tradition buddhism")
    if max_units:
        unit_ids = unit_ids[:max_units]

    local = _load_local()
    gt_ids: list[str] = []
    console.print(f"[bold]Buddhism GT (Atthakatha/local/SC): {len(unit_ids)} suttas[/bold]")

    for uid in track(unit_ids, description="Commentary GT"):
        gt_id = f"commentarial::{uid}"
        local_item = local.get(uid.lower())
        meta = {}
        if local_item and local_item.get("text"):
            author = local_item.get("author") or "local commentary"
            work = local_item.get("work") or "local GT"
            era = local_item.get("era") or ""
            stance = local_item.get("stance") or "local GT"
            text = local_item["text"]
        else:
            blurb = ""
            try:
                blurb = _fetch_sc_blurb(uid)
            except Exception as exc:  # noqa: BLE001
                meta["sc_error"] = str(exc)
            seed = next(
                (c for c in COMMENTARIES["buddhism"] if any(a.lower() in uid.lower() for a in c.get("aligns_to", []))),
                COMMENTARIES["buddhism"][0],
            )
            author = seed["author"]
            work = seed["work"]
            era = seed.get("era", "")
            stance = seed.get("stance", "") + " (seed/GT hybrid)"
            text = (blurb + "\n\n" + seed["text"]).strip() if blurb else seed["text"]
            meta["hybrid"] = True

        gt = GTUnit(
            tradition="buddhism",
            gt_id=gt_id,
            aligns_to=uid,
            author=author,
            work=work,
            era=era,
            stance=stance,
            text=text,
            source="suttacentral_blurb+atthakatha_seed_or_local",
            meta=meta,
        )
        save_gt(gt)
        gt_ids.append(gt.gt_id)

    save_gt_manifest("buddhism", gt_ids, extra={"role": "ground_truth"})
    return gt_ids
