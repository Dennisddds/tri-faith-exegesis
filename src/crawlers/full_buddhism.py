"""Crawl the full early Nikaya corpus (DN/MN/SN/AN + selected KN) from SuttaCentral."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.progress import track

from src.corpus.inventory import ensure_corpus_dirs, save_manifest, save_unit
from src.corpus.schema import ScriptureUnit
from src.crawlers.base import http_get_json, polite_pause
from src.crawlers.buddhism import _fetch_sutta, _join_segments, _strip_html

console = Console()

NIKAYA_ROOTS = ["dn", "mn", "sn", "an", "kp", "dhp", "ud", "iti", "snp", "thag", "thig"]


def _collect_uids_from_suttaplex(node: Any, out: list[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_uids_from_suttaplex(item, out)
        return
    if not isinstance(node, dict):
        return
    uid = node.get("uid") or node.get("id")
    ntype = str(node.get("type") or "").lower()
    children = node.get("children")
    # SuttaCentral flat lists mark real discourses as type=leaf.
    if uid and ntype == "leaf" and uid not in out:
        out.append(uid)
    elif uid and ntype not in {"branch", "text"} and children:
        _collect_uids_from_suttaplex(children, out)
    elif uid and ntype not in {"branch", "text"} and any(ch.isdigit() for ch in str(uid)) and uid not in out:
        # Fallback for APIs that omit type but use numbered sutta ids.
        out.append(uid)
    if children:
        _collect_uids_from_suttaplex(children, out)


def list_nikaya_uids(*, roots: list[str] | None = None) -> list[str]:
    roots = roots or NIKAYA_ROOTS
    uids: list[str] = []
    for root in roots:
        try:
            data = http_get_json(f"https://suttacentral.net/api/suttaplex/{root}", timeout=120)
            polite_pause(0.2)
            _collect_uids_from_suttaplex(data, uids)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[yellow]suttaplex {root} failed: {exc}[/yellow]")
    # de-dup preserve order
    seen = set()
    ordered = []
    for u in uids:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


def _unit_from_sutta_record(record: dict[str, Any]) -> ScriptureUnit | None:
    editions = record.get("editions") or []
    pali = next((e for e in editions if e.get("language") == "pli" and e.get("text")), None)
    eng = next((e for e in editions if e.get("language") == "en" and e.get("text")), None)
    primary = (pali or eng or {}).get("text") or ""
    if isinstance(primary, dict):
        primary = _join_segments(primary)
    primary = _strip_html(str(primary)).strip()
    secondary = ""
    if pali and eng:
        secondary = _strip_html(str(eng.get("text") or ""))
        if isinstance(eng.get("text"), dict):
            secondary = _join_segments(eng.get("text"))
    if not primary:
        return None
    uid = record.get("uid") or ""
    return ScriptureUnit(
        tradition="buddhism",
        unit_id=uid,
        ref=uid,
        title=record.get("title") or uid,
        corpus=record.get("corpus") or "Pali Tipitaka / early Nikaya (SuttaCentral)",
        primary_language=record.get("primary_language") or ("pli" if pali else "en"),
        primary_text=primary,
        secondary_text=secondary,
        source=(pali or eng or {}).get("source") or f"https://suttacentral.net/{uid}",
        meta={"editions": [{"language": e.get("language"), "author_uid": e.get("author_uid")} for e in editions if e.get("text")]},
    )


def crawl_buddhism_full(
    *,
    max_suttas: int | None = None,
    roots: list[str] | None = None,
) -> list[str]:
    ensure_corpus_dirs()
    console.print("[bold]Buddhism full corpus: listing Nikaya suttas...[/bold]")
    uids = list_nikaya_uids(roots=roots)
    if max_suttas:
        uids = uids[:max_suttas]
    console.print(f"Found {len(uids)} sutta uids; fetching texts...")
    unit_ids: list[str] = []
    for uid in track(uids, description="Suttas"):
        try:
            record = _fetch_sutta(uid)
            unit = _unit_from_sutta_record(record)
            polite_pause(0.15)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[yellow]skip {uid}: {exc}[/yellow]")
            continue
        if unit is None:
            continue
        save_unit(unit)
        unit_ids.append(unit.unit_id)
    save_manifest(
        "buddhism",
        unit_ids,
        extra={
            "granularity": "sutta",
            "listed_uids": len(uids),
            "note": "Early Nikaya + selected KN via SuttaCentral Bilara",
        },
    )
    return unit_ids
