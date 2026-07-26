"""Resume-able batch interpretation + GT alignment over the full corpus."""

from __future__ import annotations

import json
import sqlite3
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from rich.console import Console
from rich.progress import Progress

from src.alignment.evaluate import align_unit, summarize_alignments
from src.corpus.inventory import JOBS_DIR, ensure_corpus_dirs, iter_units, list_units, load_unit
from src.corpus.schema import ScriptureUnit
from src.knowledge_graph.builder import build_graph_from_interpretation, export_graph
from src.knowledge_graph.visualizer import graph_to_html
from src.llm.chain_of_thought import interpret_passage
from src.llm.deepseek_client import DeepSeekClient

Tradition = Literal["buddhism", "christianity", "islam", "all"]
console = Console()


def _unit_to_record(unit: ScriptureUnit) -> dict[str, Any]:
    """Adapt ScriptureUnit to the legacy interpret_passage record shape."""
    if unit.tradition == "buddhism":
        editions = []
        if unit.primary_text:
            editions.append(
                {
                    "language": unit.primary_language or "pli",
                    "text": unit.primary_text,
                    "source": unit.source,
                }
            )
        if unit.secondary_text:
            editions.append({"language": "en", "text": unit.secondary_text, "source": unit.source})
        return {
            "tradition": "buddhism",
            "uid": unit.unit_id,
            "title": unit.title,
            "corpus": unit.corpus,
            "editions": editions,
            "primary_language": unit.primary_language,
        }
    if unit.tradition == "christianity":
        return {
            "tradition": "christianity",
            "ref": unit.ref,
            "text": unit.primary_text,
            "corpus": unit.corpus,
        }
    return {
        "tradition": "islam",
        "ref": unit.ref,
        "name": unit.title,
        "text_arabic": unit.primary_text,
        "text_english": unit.secondary_text,
        "corpus": unit.corpus,
    }


class BatchRunner:
    def __init__(self, job_name: str = "full_corpus") -> None:
        ensure_corpus_dirs()
        self.db_path = JOBS_DIR / f"{job_name}.sqlite3"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                tradition TEXT NOT NULL,
                unit_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                updated_at TEXT,
                PRIMARY KEY (tradition, unit_id)
            )
            """
        )
        self.conn.commit()

    def register_corpus(self, tradition: Tradition = "all") -> int:
        trads = ["buddhism", "christianity", "islam"] if tradition == "all" else [tradition]
        n = 0
        for trad in trads:
            for unit_id in list_units(trad):  # type: ignore[arg-type]
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO tasks(tradition, unit_id, status, updated_at)
                    VALUES (?, ?, 'pending', ?)
                    """,
                    (trad, unit_id, datetime.now(timezone.utc).isoformat()),
                )
                n += 1
        self.conn.commit()
        return n

    def pending_tasks(self, tradition: Tradition = "all", limit: int | None = None) -> list[sqlite3.Row]:
        if tradition == "all":
            sql = "SELECT * FROM tasks WHERE status != 'done' ORDER BY tradition, unit_id"
            rows = list(self.conn.execute(sql))
        else:
            sql = "SELECT * FROM tasks WHERE tradition = ? AND status != 'done' ORDER BY unit_id"
            rows = list(self.conn.execute(sql, (tradition,)))
        return rows[:limit] if limit else rows

    def mark(self, tradition: str, unit_id: str, status: str, error: str | None = None) -> None:
        self.conn.execute(
            """
            UPDATE tasks
            SET status = ?, attempts = attempts + 1, last_error = ?, updated_at = ?
            WHERE tradition = ? AND unit_id = ?
            """,
            (status, error, datetime.now(timezone.utc).isoformat(), tradition, unit_id),
        )
        self.conn.commit()

    def stats(self) -> dict[str, Any]:
        rows = self.conn.execute(
            "SELECT tradition, status, COUNT(*) AS n FROM tasks GROUP BY tradition, status"
        ).fetchall()
        out: dict[str, Any] = {}
        for r in rows:
            out.setdefault(r["tradition"], {})[r["status"]] = r["n"]
        return out

    def run(
        self,
        tradition: Tradition = "all",
        *,
        limit: int | None = None,
        do_graph: bool = True,
        do_align: bool = True,
        use_llm_judge: bool = True,
    ) -> dict[str, Any]:
        self.register_corpus(tradition)
        tasks = self.pending_tasks(tradition, limit=limit)
        if not tasks:
            console.print("[green]No pending tasks.[/green]")
            return {"stats": self.stats(), "processed": 0}

        client = DeepSeekClient()
        processed = 0
        errors = 0

        with Progress() as progress:
            bar = progress.add_task("Batch interpret+align", total=len(tasks))
            for task in tasks:
                trad = task["tradition"]
                unit_id = task["unit_id"]
                try:
                    unit = load_unit(trad, unit_id)
                    record = _unit_to_record(unit)
                    console.print(f"-> interpret {trad}:{unit_id}")
                    interp = interpret_passage(record, tradition=trad, client=client, save=True)

                    if do_graph:
                        g = build_graph_from_interpretation(interp)
                        export_graph(g, trad, interp["ref"])
                        graph_to_html(g, trad, interp["ref"])

                    if do_align:
                        console.print(f"-> align GT {trad}:{unit_id}")
                        align_unit(
                            tradition=trad,
                            unit_id=unit_id,
                            model_interpretation=interp,
                            client=client,
                            use_llm_judge=use_llm_judge,
                        )

                    self.mark(trad, unit_id, "done")
                    processed += 1
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    err = f"{exc}\n{traceback.format_exc()[-800:]}"
                    self.mark(trad, unit_id, "error", error=err)
                    console.print(f"[red]error {trad}:{unit_id}[/red] {exc}")
                progress.advance(bar)

        summary = summarize_alignments(None if tradition == "all" else tradition)
        report = {
            "processed": processed,
            "errors": errors,
            "stats": self.stats(),
            "alignment_summary": summary,
            "db": str(self.db_path),
        }
        out = JOBS_DIR / "last_batch_report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
