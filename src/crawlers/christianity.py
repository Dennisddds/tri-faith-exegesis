"""
Crawl Christian scripture texts.

Primary layer: public-domain English Bible (World English Bible) via bible-api.com.
Secondary note: for research rigor we also record book/chapter/verse anchors so
Hebrew OT / Greek NT critical editions can be attached later.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from config import RAW_DIR, ensure_data_dirs
from src.crawlers.base import http_get_json, polite_pause, save_json

# Representative passages spanning Torah, Prophets, Gospels, Epistles.
DEFAULT_PASSAGES = [
    {"ref": "Genesis 1:1-5", "book": "Genesis", "chapter": 1, "start": 1, "end": 5},
    {"ref": "Exodus 20:1-17", "book": "Exodus", "chapter": 20, "start": 1, "end": 17},
    {"ref": "Psalm 23", "book": "Psalms", "chapter": 23, "start": 1, "end": 6},
    {"ref": "Isaiah 53:1-12", "book": "Isaiah", "chapter": 53, "start": 1, "end": 12},
    {"ref": "Matthew 5:1-12", "book": "Matthew", "chapter": 5, "start": 1, "end": 12},
    {"ref": "John 1:1-18", "book": "John", "chapter": 1, "start": 1, "end": 18},
    {"ref": "Romans 3:21-26", "book": "Romans", "chapter": 3, "start": 21, "end": 26},
]


def _fetch_passage(passage: dict[str, Any]) -> dict[str, Any]:
    # bible-api.com uses human-readable refs and returns WEB by default (public domain).
    data = http_get_json(f"https://bible-api.com/{quote(passage['ref'])}")
    polite_pause()
    verses = [
        {
            "verse": v.get("verse"),
            "text": (v.get("text") or "").strip(),
        }
        for v in data.get("verses", [])
    ]
    full_text = "\n".join(f"{v['verse']}. {v['text']}" for v in verses if v["text"])
    return {
        "tradition": "christianity",
        "corpus": "Christian Bible (WEB public-domain English; verse-anchored)",
        "ref": passage["ref"],
        "book": passage["book"],
        "chapter": passage["chapter"],
        "translation": data.get("translation_name") or "World English Bible",
        "translation_id": data.get("translation_id") or "web",
        "verses": verses,
        "text": full_text or (data.get("text") or "").strip(),
        "source": f"https://bible-api.com/{passage['ref']}",
        "original_language_note": (
            "Hebrew (Tanakh) / Koine Greek (NT) are the critical original-language strata; "
            "this crawl stores a public-domain translation with stable verse IDs for alignment."
        ),
    }


def crawl_christianity(passages: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    ensure_data_dirs()
    passages = passages or DEFAULT_PASSAGES
    results: list[dict[str, Any]] = []
    for passage in passages:
        record = _fetch_passage(passage)
        slug = passage["ref"].lower().replace(" ", "_").replace(":", "-").replace(",", "")
        out = RAW_DIR / "christianity" / f"{slug}.json"
        save_json(out, record)
        record["path"] = str(out)
        results.append(record)
    index = {
        "tradition": "christianity",
        "count": len(results),
        "items": [r["ref"] for r in results],
    }
    save_json(RAW_DIR / "christianity" / "index.json", index)
    return results
