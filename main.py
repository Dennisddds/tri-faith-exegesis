#!/usr/bin/env python
"""CLI: full-corpus crawl, GT commentary crawl, batch interpret, GT alignment."""

from __future__ import annotations

import argparse
import json

from rich.console import Console

from config import ensure_data_dirs
from src.crawlers.full_buddhism import crawl_buddhism_full
from src.crawlers.full_christianity import crawl_christianity_full
from src.crawlers.full_islam import crawl_islam_full
from src.crawlers.gt_buddhism import crawl_buddhism_gt
from src.crawlers.gt_christianity import crawl_christianity_gt
from src.crawlers.gt_islam import crawl_islam_gt
from src.alignment.evaluate import summarize_alignments
from src.jobs.runner import BatchRunner
from src.pipeline import crawl_all, run_pipeline

console = Console()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Full-corpus scripture interpretation with later commentaries as GT.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # legacy sample crawl
    crawl = sub.add_parser("crawl", help="[legacy] small sample crawl")
    crawl.add_argument("--tradition", choices=["buddhism", "christianity", "islam", "all"], default="all")

    # full corpus
    full = sub.add_parser("crawl-full", help="Crawl ALL primary scripture units into data/corpus")
    full.add_argument("--tradition", choices=["buddhism", "christianity", "islam", "all"], default="all")
    full.add_argument("--max-surah", type=int, default=None, help="Islam: limit surahs (debug)")
    full.add_argument("--max-books", type=int, default=None, help="Christianity: limit books (debug)")
    full.add_argument("--max-chapters-per-book", type=int, default=None, help="Christianity debug limit")
    full.add_argument("--max-suttas", type=int, default=None, help="Buddhism: limit suttas (debug)")

    gt = sub.add_parser("crawl-gt", help="Crawl later commentaries as Ground Truth aligned to corpus units")
    gt.add_argument("--tradition", choices=["buddhism", "christianity", "islam", "all"], default="all")
    gt.add_argument("--max-units", type=int, default=None, help="Debug limit")

    batch = sub.add_parser("batch", help="Resume-able full interpret + GT alignment")
    batch.add_argument("--tradition", choices=["buddhism", "christianity", "islam", "all"], default="all")
    batch.add_argument("--limit", type=int, default=None, help="Process N pending units then stop")
    batch.add_argument("--no-graph", action="store_true")
    batch.add_argument("--no-align", action="store_true")
    batch.add_argument("--no-llm-judge", action="store_true", help="Only lexical F1 against GT")
    batch.add_argument("--job-name", default="full_corpus")

    status = sub.add_parser("status", help="Show batch job progress")
    status.add_argument("--job-name", default="full_corpus")

    sub.add_parser("align-summary", help="Aggregate GT alignment scores")

    run = sub.add_parser("run", help="[legacy] small sample pipeline")
    run.add_argument("--tradition", choices=["buddhism", "christianity", "islam", "all"], default="all")
    run.add_argument("--limit", type=int, default=1)
    run.add_argument("--skip-crawl", action="store_true")
    run.add_argument("--no-compare", action="store_true")

    sub.add_parser("ui", help="Print Streamlit launch command")
    return p


def _crawl_full(args: argparse.Namespace) -> dict[str, int]:
    out: dict[str, int] = {}
    if args.tradition in ("islam", "all"):
        ids = crawl_islam_full(max_surah=args.max_surah)
        out["islam"] = len(ids)
    if args.tradition in ("christianity", "all"):
        ids = crawl_christianity_full(
            max_books=args.max_books,
            max_chapters_per_book=args.max_chapters_per_book,
        )
        out["christianity"] = len(ids)
    if args.tradition in ("buddhism", "all"):
        ids = crawl_buddhism_full(max_suttas=args.max_suttas)
        out["buddhism"] = len(ids)
    return out


def _crawl_gt(args: argparse.Namespace) -> dict[str, int]:
    out: dict[str, int] = {}
    if args.tradition in ("islam", "all"):
        out["islam"] = len(crawl_islam_gt(max_units=args.max_units))
    if args.tradition in ("christianity", "all"):
        out["christianity"] = len(crawl_christianity_gt(max_units=args.max_units))
    if args.tradition in ("buddhism", "all"):
        out["buddhism"] = len(crawl_buddhism_gt(max_units=args.max_units))
    return out


def main() -> None:
    ensure_data_dirs()
    args = build_parser().parse_args()

    if args.command == "crawl":
        data = crawl_all(args.tradition)
        console.print("[green]Crawl complete[/green]", {k: len(v) for k, v in data.items()})
        return

    if args.command == "crawl-full":
        summary = _crawl_full(args)
        console.print("[green]Full corpus crawl complete[/green]", summary)
        return

    if args.command == "crawl-gt":
        summary = _crawl_gt(args)
        console.print("[green]GT commentary crawl complete[/green]", summary)
        return

    if args.command == "batch":
        runner = BatchRunner(job_name=args.job_name)
        report = runner.run(
            args.tradition,
            limit=args.limit,
            do_graph=not args.no_graph,
            do_align=not args.no_align,
            use_llm_judge=not args.no_llm_judge,
        )
        console.print("[green]Batch step complete[/green]")
        console.print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "status":
        runner = BatchRunner(job_name=args.job_name)
        runner.register_corpus("all")
        console.print(json.dumps(runner.stats(), ensure_ascii=False, indent=2))
        return

    if args.command == "align-summary":
        summary = summarize_alignments()
        console.print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "run":
        report = run_pipeline(
            args.tradition,
            limit_per_tradition=args.limit,
            skip_crawl=args.skip_crawl,
            do_compare=not args.no_compare,
        )
        console.print("[green]Pipeline complete[/green]")
        console.print(json.dumps({
            "items": len(report.get("items", [])),
            "report_path": report.get("report_path"),
        }, ensure_ascii=False, indent=2))
        return

    if args.command == "ui":
        console.print("streamlit run app.py")
        return


if __name__ == "__main__":
    main()
