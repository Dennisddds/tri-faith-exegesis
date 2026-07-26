"""Manifest and unit I/O for the full corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Literal

from config import ALIGN_DIR, CORPUS_DIR, DATA_DIR, GT_DIR, JOBS_DIR, ensure_data_dirs
from src.corpus.schema import GTUnit, ScriptureUnit

Tradition = Literal["buddhism", "christianity", "islam"]


def ensure_corpus_dirs() -> None:
    ensure_data_dirs()
    for tradition in ("buddhism", "christianity", "islam"):
        (CORPUS_DIR / tradition / "units").mkdir(parents=True, exist_ok=True)
        (GT_DIR / tradition).mkdir(parents=True, exist_ok=True)
        (ALIGN_DIR / tradition).mkdir(parents=True, exist_ok=True)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def manifest_path(tradition: Tradition) -> Path:
    return CORPUS_DIR / tradition / "manifest.json"


def gt_manifest_path(tradition: Tradition) -> Path:
    return GT_DIR / tradition / "manifest.json"


def unit_path(tradition: Tradition, unit_id: str) -> Path:
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in unit_id).strip("_").lower()
    return CORPUS_DIR / tradition / "units" / f"{slug}.json"


def gt_path(tradition: Tradition, gt_id: str) -> Path:
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in gt_id).strip("_").lower()
    return GT_DIR / tradition / f"{slug}.json"


def save_unit(unit: ScriptureUnit) -> Path:
    ensure_corpus_dirs()
    path = unit_path(unit.tradition, unit.unit_id)
    path.write_text(unit.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_unit(tradition: Tradition, unit_id: str) -> ScriptureUnit:
    return ScriptureUnit.model_validate_json(unit_path(tradition, unit_id).read_text(encoding="utf-8"))


def save_gt(gt: GTUnit) -> Path:
    ensure_corpus_dirs()
    path = gt_path(gt.tradition, gt.gt_id)
    path.write_text(gt.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_gt(tradition: Tradition, gt_id: str) -> GTUnit:
    return GTUnit.model_validate_json(gt_path(tradition, gt_id).read_text(encoding="utf-8"))


def save_manifest(tradition: Tradition, unit_ids: Iterable[str], *, extra: dict[str, Any] | None = None) -> Path:
    ensure_corpus_dirs()
    ids = list(unit_ids)
    payload = {
        "tradition": tradition,
        "count": len(ids),
        "unit_ids": ids,
        **(extra or {}),
    }
    path = manifest_path(tradition)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_gt_manifest(tradition: Tradition, gt_ids: Iterable[str], *, extra: dict[str, Any] | None = None) -> Path:
    ensure_corpus_dirs()
    ids = list(gt_ids)
    payload = {
        "tradition": tradition,
        "count": len(ids),
        "gt_ids": ids,
        **(extra or {}),
    }
    path = gt_manifest_path(tradition)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_units(tradition: Tradition) -> list[str]:
    path = manifest_path(tradition)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("unit_ids") or [])


def list_gt_ids(tradition: Tradition) -> list[str]:
    path = gt_manifest_path(tradition)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("gt_ids") or [])


def iter_units(tradition: Tradition):
    for unit_id in list_units(tradition):
        path = unit_path(tradition, unit_id)
        if path.exists():
            yield ScriptureUnit.model_validate_json(path.read_text(encoding="utf-8"))


def gts_for_unit(tradition: Tradition, unit_id: str) -> list[GTUnit]:
    """Return GT commentaries whose aligns_to matches unit_id / ref prefix."""
    exact: list[GTUnit] = []
    fuzzy: list[GTUnit] = []
    key = unit_id.lower()
    for gt_id in list_gt_ids(tradition):
        path = gt_path(tradition, gt_id)
        if not path.exists():
            continue
        gt = GTUnit.model_validate_json(path.read_text(encoding="utf-8"))
        align = (gt.aligns_to or "").lower()
        if align == key:
            exact.append(gt)
        elif align in key or key in align or key.startswith(align + ".") or align.startswith(key + "."):
            fuzzy.append(gt)
    return exact or fuzzy
