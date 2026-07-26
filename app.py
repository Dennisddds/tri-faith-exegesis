"""Streamlit UI: full corpus, GT commentaries, interpretations, alignments."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from config import ALIGN_DIR, GRAPH_DIR, INTERP_DIR, ensure_data_dirs
from src.alignment.evaluate import summarize_alignments
from src.corpus.inventory import gt_path, list_gt_ids, list_units, unit_path
from src.crawlers.full_buddhism import crawl_buddhism_full
from src.crawlers.full_christianity import crawl_christianity_full
from src.crawlers.full_islam import crawl_islam_full
from src.crawlers.gt_buddhism import crawl_buddhism_gt
from src.crawlers.gt_christianity import crawl_christianity_gt
from src.crawlers.gt_islam import crawl_islam_gt
from src.jobs.runner import BatchRunner

st.set_page_config(page_title="Tri-Faith Exegesis", layout="wide")
ensure_data_dirs()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Source+Sans+3:wght@400;600&display=swap');
    h1,h2,h3 { font-family:'Libre Baskerville', serif !important; }
    .stApp {
      background:
        radial-gradient(1000px 420px at 8% -8%, #e7dcc8 0%, transparent 55%),
        radial-gradient(800px 360px at 100% 0%, #d5e2da 0%, transparent 50%),
        linear-gradient(180deg, #f3eee5 0%, #f7f4ef 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Tri-Faith Exegesis")
st.caption("Full-corpus scripture · commentary as GT · alignment · knowledge graphs")

with st.sidebar:
    st.header("Pipeline")
    tradition = st.selectbox("Tradition", ["all", "buddhism", "christianity", "islam"])
    debug = st.checkbox("Debug limits", value=True)
    max_surah = st.number_input("Islam max surah", 1, 114, 1) if debug else None
    max_books = st.number_input("Bible max books", 1, 66, 1) if debug else None
    max_ch = st.number_input("Chapters/book", 1, 50, 1) if debug else None
    max_suttas = st.number_input("Max suttas", 1, 5000, 3) if debug else None
    batch_limit = st.number_input("Batch limit", 1, 100000, 1)
    use_judge = st.checkbox("LLM judge (commentary as GT)", value=True)

    if st.button("1) Crawl full scripture", use_container_width=True):
        with st.spinner("Crawling scripture..."):
            out = {}
            if tradition in ("islam", "all"):
                out["islam"] = len(crawl_islam_full(max_surah=int(max_surah) if debug else None))
            if tradition in ("christianity", "all"):
                out["christianity"] = len(
                    crawl_christianity_full(
                        max_books=int(max_books) if debug else None,
                        max_chapters_per_book=int(max_ch) if debug else None,
                    )
                )
            if tradition in ("buddhism", "all"):
                out["buddhism"] = len(crawl_buddhism_full(max_suttas=int(max_suttas) if debug else None))
        st.success(out)

    if st.button("2) Crawl commentary GT", use_container_width=True):
        with st.spinner("Crawling GT..."):
            out = {}
            lim = int(batch_limit) if debug else None
            if tradition in ("islam", "all"):
                out["islam"] = len(crawl_islam_gt(max_units=lim))
            if tradition in ("christianity", "all"):
                out["christianity"] = len(crawl_christianity_gt(max_units=lim))
            if tradition in ("buddhism", "all"):
                out["buddhism"] = len(crawl_buddhism_gt(max_units=lim))
        st.success(out)

    if st.button("3) Batch interpret + align GT", use_container_width=True):
        with st.spinner("Running LLM batch..."):
            report = BatchRunner().run(
                tradition,  # type: ignore[arg-type]
                limit=int(batch_limit),
                do_align=True,
                use_llm_judge=use_judge,
            )
        st.session_state["batch_report"] = report
        st.success(report.get("stats"))

tabs = st.tabs(["Corpus", "GT commentaries", "Interpretations", "GT alignment", "Knowledge graphs", "Progress"])

with tabs[0]:
    trad = st.selectbox("Tradition##corpus", ["islam", "christianity", "buddhism"], key="c1")
    ids = list_units(trad)  # type: ignore[arg-type]
    st.write(f"Units: {len(ids)}")
    if ids:
        pick = st.selectbox("unit_id", ids[:5000], key="c2")
        p = unit_path(trad, pick)  # type: ignore[arg-type]
        if p.exists():
            st.json(json.loads(p.read_text(encoding="utf-8")))

with tabs[1]:
    trad = st.selectbox("Tradition##gt", ["islam", "christianity", "buddhism"], key="g1")
    ids = list_gt_ids(trad)  # type: ignore[arg-type]
    st.write(f"GT items: {len(ids)}")
    if ids:
        pick = st.selectbox("gt_id", ids[:5000], key="g2")
        p = gt_path(trad, pick)  # type: ignore[arg-type]
        if p.exists():
            st.json(json.loads(p.read_text(encoding="utf-8")))

with tabs[2]:
    trad = st.selectbox("Tradition##interp", ["islam", "christianity", "buddhism"], key="i1")
    files = sorted((INTERP_DIR / trad).glob("*.json")) if (INTERP_DIR / trad).exists() else []
    if not files:
        st.info("No interpretations yet. Run the batch pipeline first.")
    else:
        pick = st.selectbox("File", [f.name for f in files], key="i2")
        data = json.loads((INTERP_DIR / trad / pick).read_text(encoding="utf-8"))
        with st.expander("reasoning_content"):
            st.write(data.get("reasoning_content") or "")
        st.json(data.get("interpretation") or data)

with tabs[3]:
    trad = st.selectbox("Tradition##align", ["islam", "christianity", "buddhism"], key="a1")
    if st.button("Refresh alignment summary"):
        st.json(summarize_alignments(trad))
    files = sorted((ALIGN_DIR / trad).glob("*.json")) if (ALIGN_DIR / trad).exists() else []
    if not files:
        st.info("No alignment results yet.")
    else:
        pick = st.selectbox("Alignment file", [f.name for f in files], key="a2")
        st.json(json.loads((ALIGN_DIR / trad / pick).read_text(encoding="utf-8")))

with tabs[4]:
    trad = st.selectbox("Tradition##graph", ["islam", "christianity", "buddhism", "all"], key="gr1")
    html_files = sorted((GRAPH_DIR / trad).glob("*.html")) if (GRAPH_DIR / trad).exists() else []
    if html_files:
        pick = st.selectbox("Graph", [f.name for f in html_files], key="gr2")
        components.html((GRAPH_DIR / trad / pick).read_text(encoding="utf-8"), height=740, scrolling=True)
    else:
        st.info("No graphs yet.")

with tabs[5]:
    runner = BatchRunner()
    runner.register_corpus("all")
    st.json(runner.stats())
    if "batch_report" in st.session_state:
        st.subheader("Latest batch report")
        st.json(st.session_state["batch_report"])
