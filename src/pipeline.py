"""End-to-end pipeline: crawl -> CoT interpret -> KG -> compare commentaries."""

from __future__ import annotations

import json
from typing import Any, Literal

from rich.console import Console
from rich.progress import track

from config import PROCESSED_DIR, ensure_data_dirs
from src.comparison.compare import compare_with_commentaries
from src.crawlers import crawl_buddhism, crawl_christianity, crawl_islam, load_commentaries
from src.knowledge_graph.builder import build_graph_from_interpretation, export_graph, merge_graphs
from src.knowledge_graph.visualizer import graph_to_html
from src.llm.chain_of_thought import interpret_passage
from src.llm.deepseek_client import DeepSeekClient

Tradition = Literal["buddhism", "christianity", "islam", "all"]
console = Console()


def crawl_all(tradition: Tradition = "all") -> dict[str, list[dict[str, Any]]]:
    ensure_data_dirs()
    load_commentaries()
    out: dict[str, list[dict[str, Any]]] = {}
    if tradition in ("buddhism", "all"):
        console.print("[bold]Crawling Buddhist suttas (SuttaCentral)...[/bold]")
        out["buddhism"] = crawl_buddhism()
    if tradition in ("christianity", "all"):
        console.print("[bold]Crawling Christian passages (bible-api)...[/bold]")
        out["christianity"] = crawl_christianity()
    if tradition in ("islam", "all"):
        console.print("[bold]Crawling Qur'anic units (AlQuran Cloud)...[/bold]")
        out["islam"] = crawl_islam()
    return out


def run_interpretation(
    scriptures: dict[str, list[dict[str, Any]]],
    *,
    limit_per_tradition: int | None = 1,
    do_compare: bool = True,
    do_graph: bool = True,
) -> dict[str, Any]:
    client = DeepSeekClient()
    report: dict[str, Any] = {"items": [], "graphs": []}
    graphs = []

    for tradition, records in scriptures.items():
        selected = records[:limit_per_tradition] if limit_per_tradition else records
        for record in track(selected, description=f"Interpreting {tradition}"):
            console.print(f"  -> CoT interpret: {tradition}")
            interp = interpret_passage(record, tradition=tradition, client=client)
            item: dict[str, Any] = {"interpretation": interp}

            if do_graph:
                g = build_graph_from_interpretation(interp)
                gpath = export_graph(g, tradition, interp["ref"])
                hpath = graph_to_html(g, tradition, interp["ref"])
                item["graph_json"] = str(gpath)
                item["graph_html"] = str(hpath)
                graphs.append(g)
                report["graphs"].append({"tradition": tradition, "ref": interp["ref"], "html": str(hpath)})

            if do_compare:
                console.print(f"  -> Compare commentaries: {tradition}/{interp['ref']}")
                comps = compare_with_commentaries(interp, client=client)
                item["comparisons"] = comps

            report["items"].append(item)

    if graphs:
        merged = merge_graphs(graphs)
        mpath = export_graph(merged, "all", "merged")
        mhtml = graph_to_html(merged, "all", "merged")
        report["merged_graph_json"] = str(mpath)
        report["merged_graph_html"] = str(mhtml)

    out = PROCESSED_DIR / "last_run_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(out)
    return report


def run_pipeline(
    tradition: Tradition = "all",
    *,
    limit_per_tradition: int | None = 1,
    skip_crawl: bool = False,
    do_compare: bool = True,
) -> dict[str, Any]:
    if skip_crawl:
        # Load previously crawled raw JSON indexes lightly by re-crawling is safer for demo;
        # here we just crawl again unless user passes skip with existing files.
        from pathlib import Path

        scriptures: dict[str, list[dict[str, Any]]] = {}
        base = Path(__file__).resolve().parents[1] / "data" / "raw"
        for trad in ("buddhism", "christianity", "islam"):
            if tradition not in ("all", trad):
                continue
            files = sorted(p for p in (base / trad).glob("*.json") if p.name not in {"index.json", "commentaries.json"})
            scriptures[trad] = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    else:
        scriptures = crawl_all(tradition)

    return run_interpretation(
        scriptures,
        limit_per_tradition=limit_per_tradition,
        do_compare=do_compare,
    )
