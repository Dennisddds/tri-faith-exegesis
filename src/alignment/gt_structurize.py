"""Convert free-text GT commentary into the same structured schema as model interpretations."""

from __future__ import annotations

import json
import re
from typing import Any

from config import DATA_DIR
from src.corpus.schema import GTUnit
from src.llm.chain_of_thought import _extract_json
from src.llm.deepseek_client import DeepSeekClient

GT_STRUCT_DIR = DATA_DIR / "gt_structured"

SYSTEM = """You are a commentary structuring assistant. Rewrite later commentary text into the same JSON schema used for model interpretations.
This is ground-truth structuring: do not invent new doctrine; only compress / organize what the commentary already says.
If a field is not attested in the commentary, use an empty string or empty array. Output valid JSON only (no Markdown fences).
Write field values in English; keep original-language terms where they appear.
"""

USER = """Tradition: {tradition}
Aligned scripture unit: {aligns_to}
Commentary author: {author}
Commentary work: {work}

[Commentary text]
{text}

Return schema:
{{
  "ref": "{aligns_to}",
  "tradition": "{tradition}",
  "literal_reading": "...",
  "historical_context": "...",
  "doctrinal_structure": "...",
  "key_concepts": [{{"term": "...", "gloss": "...", "role": "..."}}],
  "entities": [{{"name": "...", "type": "person|deity|place|concept|text|practice|community", "note": "..."}}],
  "relations": [{{"source": "...", "relation": "...", "target": "...", "evidence": "..."}}],
  "possible_misreadings": [],
  "open_questions": [],
  "summary": "..."
}}
"""


def structurize_gt(gt: GTUnit, *, client: DeepSeekClient | None = None, force: bool = False) -> dict[str, Any]:
    GT_STRUCT_DIR.mkdir(parents=True, exist_ok=True)
    (GT_STRUCT_DIR / gt.tradition).mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", gt.gt_id).strip("_").lower()
    out = GT_STRUCT_DIR / gt.tradition / f"{slug}.json"
    if out.exists() and not force:
        return json.loads(out.read_text(encoding="utf-8"))

    client = client or DeepSeekClient()
    text = gt.text[:10000]
    resp = client.chat(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": USER.format(
                    tradition=gt.tradition,
                    aligns_to=gt.aligns_to,
                    author=gt.author,
                    work=gt.work,
                    text=text,
                ),
            },
        ],
        temperature=0.1,
        enable_thinking=True,
    )
    parsed = _extract_json(resp.content)
    payload = {
        "gt_id": gt.gt_id,
        "aligns_to": gt.aligns_to,
        "tradition": gt.tradition,
        "author": gt.author,
        "work": gt.work,
        "reasoning_content": resp.reasoning_content,
        "structured": parsed,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
