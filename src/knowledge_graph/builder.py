"""Build NetworkX knowledge graphs from CoT interpretation JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from config import GRAPH_DIR, ensure_data_dirs


def build_graph_from_interpretation(interp_payload: dict[str, Any]) -> nx.DiGraph:
    g = nx.DiGraph()
    tradition = interp_payload.get("tradition", "unknown")
    ref = interp_payload.get("ref", "unknown")
    data = interp_payload.get("interpretation") or {}

    root = f"{tradition}:{ref}"
    g.add_node(
        root,
        label=str(ref),
        node_type="passage",
        tradition=tradition,
        summary=data.get("summary", ""),
    )

    for ent in data.get("entities") or []:
        name = (ent.get("name") or "").strip()
        if not name:
            continue
        nid = f"entity:{name}"
        g.add_node(
            nid,
            label=name,
            node_type=ent.get("type") or "concept",
            note=ent.get("note") or "",
            tradition=tradition,
        )
        g.add_edge(root, nid, relation="mentions", evidence="interpretation.entities")

    for concept in data.get("key_concepts") or []:
        term = (concept.get("term") or "").strip()
        if not term:
            continue
        nid = f"concept:{term}"
        g.add_node(
            nid,
            label=term,
            node_type="concept",
            gloss=concept.get("gloss") or "",
            role=concept.get("role") or "",
            tradition=tradition,
        )
        g.add_edge(root, nid, relation="has_concept", evidence="interpretation.key_concepts")

    for rel in data.get("relations") or []:
        src = (rel.get("source") or "").strip()
        tgt = (rel.get("target") or "").strip()
        relation = (rel.get("relation") or "related_to").strip()
        if not src or not tgt:
            continue
        sid = src if src.startswith(("entity:", "concept:", f"{tradition}:")) else f"entity:{src}"
        tid = tgt if tgt.startswith(("entity:", "concept:", f"{tradition}:")) else f"entity:{tgt}"
        if sid not in g:
            g.add_node(sid, label=src, node_type="entity", tradition=tradition)
        if tid not in g:
            g.add_node(tid, label=tgt, node_type="entity", tradition=tradition)
        g.add_edge(sid, tid, relation=relation, evidence=rel.get("evidence") or "")

    return g


def export_graph(graph: nx.DiGraph, tradition: str, ref: str) -> Path:
    ensure_data_dirs()
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(ref)).strip("_").lower()
    path = GRAPH_DIR / tradition / f"{slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": [{"id": n, **graph.nodes[n]} for n in graph.nodes],
        "edges": [
            {"source": u, "target": v, **graph.edges[u, v]}
            for u, v in graph.edges
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # also GraphML for Gephi etc.
    graphml = path.with_suffix(".graphml")
    nx.write_graphml(graph, graphml)
    return path


def merge_graphs(graphs: list[nx.DiGraph]) -> nx.DiGraph:
    merged = nx.DiGraph()
    for g in graphs:
        merged.add_nodes_from(g.nodes(data=True))
        merged.add_edges_from(g.edges(data=True))
    return merged
