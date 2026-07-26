"""Interactive HTML visualization via pyvis."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
from pyvis.network import Network

from config import GRAPH_DIR, ensure_data_dirs

COLOR_MAP = {
    "passage": "#1f4e79",
    "person": "#b35c00",
    "deity": "#7a1f1f",
    "place": "#2f6f3e",
    "concept": "#5b2c6f",
    "text": "#334155",
    "practice": "#0f766e",
    "community": "#854d0e",
    "entity": "#475569",
}


def graph_to_html(graph: nx.DiGraph, tradition: str, ref: str) -> Path:
    ensure_data_dirs()
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(ref)).strip("_").lower()
    out = GRAPH_DIR / tradition / f"{slug}.html"

    net = Network(height="720px", width="100%", directed=True, bgcolor="#f7f4ef", font_color="#1c1917")
    net.barnes_hut(gravity=-8000, spring_length=140)

    for node, attrs in graph.nodes(data=True):
        ntype = attrs.get("node_type") or "entity"
        label = attrs.get("label") or node
        title = f"{label}\\ntype={ntype}\\n{attrs.get('note') or attrs.get('gloss') or attrs.get('summary') or ''}"
        net.add_node(
            node,
            label=label[:40],
            title=title,
            color=COLOR_MAP.get(ntype, "#64748b"),
        )

    for u, v, attrs in graph.edges(data=True):
        net.add_edge(u, v, label=attrs.get("relation") or "", title=attrs.get("evidence") or "")

    out.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(out), open_browser=False, notebook=False)
    return out
