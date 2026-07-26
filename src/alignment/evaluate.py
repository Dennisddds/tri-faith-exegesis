"""Align model interpretation against GT commentary (ground truth)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config import DATA_DIR
from src.alignment.gt_structurize import structurize_gt
from src.corpus.inventory import ALIGN_DIR, gts_for_unit
from src.corpus.schema import GTUnit
from src.llm.chain_of_thought import _extract_json
from src.llm.deepseek_client import DeepSeekClient
from src.llm.prompts import COMPARE_SYSTEM

ALIGN_PROMPT = """You are evaluating alignment where later commentary is Ground Truth (GT).
The model interpretation is the prediction; the structured commentary is GT.
Score how well the prediction covers and stays faithful to the GT. Output valid JSON only (no Markdown fences).

Tradition: {tradition}
Unit: {ref}

[GT structured commentary]
{gt_structured}

[Model prediction]
{pred}

Return:
{{
  "ref": "{ref}",
  "gt_id": "{gt_id}",
  "scores": {{
    "concept_coverage": 0.0,
    "doctrinal_fidelity": 0.0,
    "entity_coverage": 0.0,
    "hallucination_penalty": 0.0,
    "overall": 0.0
  }},
  "matched_concepts": ["..."],
  "missing_concepts_vs_gt": ["present in GT but missing in model"],
  "extra_concepts_vs_gt": ["present in model but not in GT (possible hallucination or fair addition)"],
  "relation_matches": ["..."],
  "relation_mismatches": ["..."],
  "verdict": "one sentence on alignment quality relative to this GT"
}}
All scores are 0–1. Higher hallucination_penalty means more unsupported invention relative to GT.
"""


def _norm_term(s: str) -> str:
    s = (s or "").lower().strip()
    # Drop common script/punctuation noise for cross-lingual rough matching.
    s = re.sub(r"[\(\)\[\]（）【】/\\|]", " ", s)
    s = re.sub(r"[^\w\u0600-\u06ff\u4e00-\u9fff\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    aliases = {
        "allah": "allah",
        "الل ه": "allah",
        "الله": "allah",
        "yahweh": "yahweh",
        "jehovah": "yahweh",
        "buddha": "buddha",
        "bhagava": "buddha",
    }
    return aliases.get(s, s)


def _terms_from_interp(data: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for c in data.get("key_concepts") or []:
        if c.get("term"):
            terms.add(_norm_term(c["term"]))
    for e in data.get("entities") or []:
        if e.get("name"):
            terms.add(_norm_term(e["name"]))
    return {t for t in terms if t}


def _f1(pred: set[str], gold: set[str]) -> dict[str, float]:
    if not pred and not gold:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred or not gold:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    tp = len(pred & gold)
    precision = tp / len(pred)
    recall = tp / len(gold)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def _token_overlap(a: str, b: str) -> float:
    ta = set(re.findall(r"[\w\u4e00-\u9fff]+", (a or "").lower()))
    tb = set(re.findall(r"[\w\u4e00-\u9fff]+", (b or "").lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def lexical_align(pred: dict[str, Any], gt_struct: dict[str, Any]) -> dict[str, Any]:
    p_terms = _terms_from_interp(pred)
    g_terms = _terms_from_interp(gt_struct)
    concept_f1 = _f1(p_terms, g_terms)
    summary_overlap = _token_overlap(pred.get("summary", ""), gt_struct.get("summary", ""))
    doctrine_overlap = _token_overlap(
        pred.get("doctrinal_structure", ""),
        gt_struct.get("doctrinal_structure", ""),
    )
    return {
        "concept_term_f1": concept_f1,
        "summary_token_jaccard": summary_overlap,
        "doctrine_token_jaccard": doctrine_overlap,
        "pred_term_count": len(p_terms),
        "gt_term_count": len(g_terms),
        "matched_terms": sorted(p_terms & g_terms),
        "missing_terms": sorted(g_terms - p_terms),
        "extra_terms": sorted(p_terms - g_terms),
    }


def llm_align(
    *,
    tradition: str,
    ref: str,
    gt_id: str,
    pred: dict[str, Any],
    gt_struct: dict[str, Any],
    client: DeepSeekClient,
) -> dict[str, Any]:
    resp = client.chat(
        [
            {"role": "system", "content": COMPARE_SYSTEM + "\nFor this task, treat the commentary as Ground Truth."},
            {
                "role": "user",
                "content": ALIGN_PROMPT.format(
                    tradition=tradition,
                    ref=ref,
                    gt_id=gt_id,
                    gt_structured=json.dumps(gt_struct, ensure_ascii=False, indent=2)[:12000],
                    pred=json.dumps(pred, ensure_ascii=False, indent=2)[:12000],
                ),
            },
        ],
        temperature=0.0,
        enable_thinking=True,
    )
    parsed = _extract_json(resp.content)
    return {"reasoning_content": resp.reasoning_content, "judgment": parsed}


def align_unit(
    *,
    tradition: str,
    unit_id: str,
    model_interpretation: dict[str, Any],
    client: DeepSeekClient | None = None,
    use_llm_judge: bool = True,
) -> list[dict[str, Any]]:
    """Align one model interpretation to all GT commentaries for the unit."""
    client = client or DeepSeekClient()
    gts = gts_for_unit(tradition, unit_id)  # type: ignore[arg-type]
    pred = model_interpretation.get("interpretation") or model_interpretation
    results: list[dict[str, Any]] = []

    if not gts:
        results.append(
            {
                "tradition": tradition,
                "unit_id": unit_id,
                "error": "no_gt_found",
            }
        )
    for gt in gts:
        structured_payload = structurize_gt(gt, client=client)
        gt_struct = structured_payload.get("structured") or {}
        lex = lexical_align(pred, gt_struct)
        item: dict[str, Any] = {
            "tradition": tradition,
            "unit_id": unit_id,
            "gt_id": gt.gt_id,
            "gt_author": gt.author,
            "gt_work": gt.work,
            "lexical": lex,
            "role": "gt_alignment",
        }
        if use_llm_judge:
            item["llm_judge"] = llm_align(
                tradition=tradition,
                ref=unit_id,
                gt_id=gt.gt_id,
                pred=pred,
                gt_struct=gt_struct,
                client=client,
            )
        results.append(item)

    out_dir = ALIGN_DIR / tradition
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", unit_id).strip("_").lower()
    path = out_dir / f"{slug}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def summarize_alignments(tradition: str | None = None) -> dict[str, Any]:
    traditions = [tradition] if tradition else ["buddhism", "christianity", "islam"]
    summary: dict[str, Any] = {"traditions": {}}
    for trad in traditions:
        folder = ALIGN_DIR / trad
        if not folder.exists():
            continue
        files = list(folder.glob("*.json"))
        overall_scores = []
        f1s = []
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data:
                if item.get("error"):
                    continue
                f1s.append(((item.get("lexical") or {}).get("concept_term_f1") or {}).get("f1") or 0.0)
                judge = ((item.get("llm_judge") or {}).get("judgment") or {}).get("scores") or {}
                if "overall" in judge:
                    overall_scores.append(float(judge["overall"]))
        summary["traditions"][trad] = {
            "aligned_files": len(files),
            "mean_concept_f1": sum(f1s) / len(f1s) if f1s else None,
            "mean_llm_overall": sum(overall_scores) / len(overall_scores) if overall_scores else None,
        }
    out = DATA_DIR / "processed" / "alignment_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
