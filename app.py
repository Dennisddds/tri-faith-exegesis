"""Streamlit UI: full corpus, GT commentaries, interpretations, alignments."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config import ALIGN_DIR, CORPUS_DIR, GT_DIR, GRAPH_DIR, INTERP_DIR, ensure_data_dirs
from src.alignment.evaluate import summarize_alignments
from src.corpus.inventory import list_gt_ids, list_units
from src.crawlers.full_buddhism import crawl_buddhism_full
from src.crawlers.full_christianity import crawl_christianity_full
from src.crawlers.full_islam import crawl_islam_full
from src.crawlers.gt_buddhism import crawl_buddhism_gt
from src.crawlers.gt_christianity import crawl_christianity_gt
from src.crawlers.gt_islam import crawl_islam_gt
from src.jobs.runner import BatchRunner

st.set_page_config(page_title="Clarification · Full Corpus + GT", layout="wide")
ensure_data_dirs()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700&family=Source+Sans+3:wght@400;600&display=swap');
    h1,h2,h3 { font-family:'Noto Serif SC', serif !important; }
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

st.title("Clarification")
st.caption("全量原典阐释 · 后人注疏作 GT · 对齐评估 · 知识图谱")

with st.sidebar:
    st.header("全量管道")
    tradition = st.selectbox("传统", ["all", "buddhism", "christianity", "islam"])
    debug = st.checkbox("调试限量", value=True)
    max_surah = st.number_input("Islam max surah", 1, 114, 1) if debug else None
    max_books = st.number_input("Bible max books", 1, 66, 1) if debug else None
    max_ch = st.number_input("Chapters/book", 1, 50, 1) if debug else None
    max_suttas = st.number_input("Max suttas", 1, 5000, 3) if debug else None
    batch_limit = st.number_input("Batch limit", 1, 100000, 1)
    use_judge = st.checkbox("LLM Judge（以注疏为 GT）", value=True)

    if st.button("1) 爬取全量原典", use_container_width=True):
        with st.spinner("爬取原典..."):
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

    if st.button("2) 爬取注疏 GT", use_container_width=True):
        with st.spinner("爬取 GT..."):
            out = {}
            lim = int(batch_limit) if debug else None
            if tradition in ("islam", "all"):
                out["islam"] = len(crawl_islam_gt(max_units=lim))
            if tradition in ("christianity", "all"):
                out["christianity"] = len(crawl_christianity_gt(max_units=lim))
            if tradition in ("buddhism", "all"):
                out["buddhism"] = len(crawl_buddhism_gt(max_units=lim))
        st.success(out)

    if st.button("3) 批处理阐释并对齐 GT", use_container_width=True):
        with st.spinner("LLM 批处理中..."):
            report = BatchRunner().run(
                tradition,  # type: ignore[arg-type]
                limit=int(batch_limit),
                do_align=True,
                use_llm_judge=use_judge,
            )
        st.session_state["batch_report"] = report
        st.success(report.get("stats"))

tabs = st.tabs(["原典语料", "GT 注疏", "模型阐释", "GT 对齐", "知识图谱", "进度"])

with tabs[0]:
    trad = st.selectbox("传统##corpus", ["islam", "christianity", "buddhism"], key="c1")
    ids = list_units(trad)  # type: ignore[arg-type]
    st.write(f"单元数：{len(ids)}")
    if ids:
        pick = st.selectbox("unit_id", ids[:5000], key="c2")
        path = CORPUS_DIR / trad / "units" / f"{pick.replace(':', '_').replace(' ', '_').lower()}.json"
        # robust open via inventory helper
        from src.corpus.inventory import unit_path

        p = unit_path(trad, pick)  # type: ignore[arg-type]
        if p.exists():
            st.json(json.loads(p.read_text(encoding="utf-8")))

with tabs[1]:
    trad = st.selectbox("传统##gt", ["islam", "christianity", "buddhism"], key="g1")
    ids = list_gt_ids(trad)  # type: ignore[arg-type]
    st.write(f"GT 数：{len(ids)}")
    if ids:
        pick = st.selectbox("gt_id", ids[:5000], key="g2")
        from src.corpus.inventory import gt_path

        p = gt_path(trad, pick)  # type: ignore[arg-type]
        if p.exists():
            st.json(json.loads(p.read_text(encoding="utf-8")))

with tabs[2]:
    trad = st.selectbox("传统##interp", ["islam", "christianity", "buddhism"], key="i1")
    files = sorted((INTERP_DIR / trad).glob("*.json")) if (INTERP_DIR / trad).exists() else []
    if not files:
        st.info("暂无阐释。请先批处理。")
    else:
        pick = st.selectbox("文件", [f.name for f in files], key="i2")
        data = json.loads((INTERP_DIR / trad / pick).read_text(encoding="utf-8"))
        with st.expander("reasoning_content"):
            st.write(data.get("reasoning_content") or "")
        st.json(data.get("interpretation") or data)

with tabs[3]:
    trad = st.selectbox("传统##align", ["islam", "christianity", "buddhism"], key="a1")
    if st.button("刷新对齐汇总"):
        st.json(summarize_alignments(trad))
    files = sorted((ALIGN_DIR / trad).glob("*.json")) if (ALIGN_DIR / trad).exists() else []
    if not files:
        st.info("暂无对齐结果。")
    else:
        pick = st.selectbox("对齐文件", [f.name for f in files], key="a2")
        st.json(json.loads((ALIGN_DIR / trad / pick).read_text(encoding="utf-8")))

with tabs[4]:
    trad = st.selectbox("传统##graph", ["islam", "christianity", "buddhism", "all"], key="gr1")
    html_files = sorted((GRAPH_DIR / trad).glob("*.html")) if (GRAPH_DIR / trad).exists() else []
    if html_files:
        pick = st.selectbox("图谱", [f.name for f in html_files], key="gr2")
        components.html((GRAPH_DIR / trad / pick).read_text(encoding="utf-8"), height=740, scrolling=True)
    else:
        st.info("暂无图谱。")

with tabs[5]:
    runner = BatchRunner()
    runner.register_corpus("all")
    st.json(runner.stats())
    if "batch_report" in st.session_state:
        st.subheader("最近批处理")
        st.json(st.session_state["batch_report"])
