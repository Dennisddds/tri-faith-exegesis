"""Crawl the full Protestant Bible (WEB) chapter-by-chapter as scripture units."""

from __future__ import annotations

from urllib.parse import quote

from rich.console import Console
from rich.progress import track

from src.corpus.inventory import ensure_corpus_dirs, save_manifest, save_unit
from src.corpus.schema import ScriptureUnit
from src.crawlers.base import http_get_json, polite_pause

console = Console()

# Protestant canon book order + chapter counts (WEB / common English Bible).
BIBLE_BOOKS: list[tuple[str, int]] = [
    ("Genesis", 50), ("Exodus", 40), ("Leviticus", 27), ("Numbers", 36), ("Deuteronomy", 34),
    ("Joshua", 24), ("Judges", 21), ("Ruth", 4), ("1 Samuel", 31), ("2 Samuel", 24),
    ("1 Kings", 22), ("2 Kings", 25), ("1 Chronicles", 29), ("2 Chronicles", 36),
    ("Ezra", 10), ("Nehemiah", 13), ("Esther", 10), ("Job", 42), ("Psalms", 150),
    ("Proverbs", 31), ("Ecclesiastes", 12), ("Song of Solomon", 8), ("Isaiah", 66),
    ("Jeremiah", 52), ("Lamentations", 5), ("Ezekiel", 48), ("Daniel", 12),
    ("Hosea", 14), ("Joel", 3), ("Amos", 9), ("Obadiah", 1), ("Jonah", 4),
    ("Micah", 7), ("Nahum", 3), ("Habakkuk", 3), ("Zephaniah", 3), ("Haggai", 2),
    ("Zechariah", 14), ("Malachi", 4),
    ("Matthew", 28), ("Mark", 16), ("Luke", 24), ("John", 21), ("Acts", 28),
    ("Romans", 16), ("1 Corinthians", 16), ("2 Corinthians", 13), ("Galatians", 6),
    ("Ephesians", 6), ("Philippians", 4), ("Colossians", 4), ("1 Thessalonians", 5),
    ("2 Thessalonians", 3), ("1 Timothy", 6), ("2 Timothy", 4), ("Titus", 3),
    ("Philemon", 1), ("Hebrews", 13), ("James", 5), ("1 Peter", 5), ("2 Peter", 3),
    ("1 John", 5), ("2 John", 1), ("3 John", 1), ("Jude", 1), ("Revelation", 22),
]


def _fetch_chapter(book: str, chapter: int) -> ScriptureUnit | None:
    ref = f"{book} {chapter}"
    try:
        data = http_get_json(f"https://bible-api.com/{quote(ref)}", timeout=90)
    except Exception:
        return None
    verses = data.get("verses") or []
    lines = []
    for v in verses:
        text = (v.get("text") or "").strip()
        if text:
            lines.append(f"{v.get('verse')}. {text}")
    body = "\n".join(lines) or (data.get("text") or "").strip()
    if not body:
        return None
    unit_id = f"{book.replace(' ', '_')}.{chapter}"
    return ScriptureUnit(
        tradition="christianity",
        unit_id=unit_id,
        ref=ref,
        title=ref,
        corpus="Christian Bible WEB (full chapter units)",
        primary_language="en",
        primary_text=body,
        secondary_text="",
        source=f"https://bible-api.com/{quote(ref)}",
        meta={
            "book": book,
            "chapter": chapter,
            "translation": data.get("translation_id") or "web",
            "verse_count": len(verses),
            "original_language_note": "Hebrew OT / Greek NT critical editions are the ultimate source layer; WEB provides public-domain verse-anchored text.",
        },
    )


def crawl_christianity_full(
    *,
    max_books: int | None = None,
    max_chapters_per_book: int | None = None,
) -> list[str]:
    ensure_corpus_dirs()
    books = BIBLE_BOOKS[:max_books] if max_books else BIBLE_BOOKS
    unit_ids: list[str] = []
    console.print(f"[bold]Christianity full corpus: {len(books)} books[/bold]")
    jobs: list[tuple[str, int]] = []
    for book, nchap in books:
        limit = min(nchap, max_chapters_per_book) if max_chapters_per_book else nchap
        for ch in range(1, limit + 1):
            jobs.append((book, ch))
    for book, ch in track(jobs, description="Bible chapters"):
        unit = _fetch_chapter(book, ch)
        polite_pause(0.12)
        if unit is None:
            console.print(f"[yellow]skip[/yellow] {book} {ch}")
            continue
        save_unit(unit)
        unit_ids.append(unit.unit_id)
    save_manifest(
        "christianity",
        unit_ids,
        extra={"granularity": "chapter", "books": len(books), "note": "Full WEB Bible by chapter"},
    )
    return unit_ids
