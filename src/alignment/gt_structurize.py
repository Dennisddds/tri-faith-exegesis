"""Convert free-text GT commentary into the same structured schema as model interpretations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config import DATA_DIR
from src.corpus.schema import GTUnit
from src.llm.deepseek_client import DeepSeekClient
from src.llm.chain_of_thought import _extract_json

GT_STRUCT_DIR = DATA_DIR / "gt_structured"

SYSTEM = """你是注疏结构化助手。将后人注疏文本转写为与模型阐释相同的 JSON schema。
这是 ground-truth 结构化，不要掺入你自己的新教义发明；只能压缩/归纳注疏已有内容。
若注疏未提及某字段，用空字符串或空数组。输出合法 JSON，不要 Markdown 围栏。
"""

USER = """传统: {tradition}
对齐原典单元: {aligns_to}
注疏作者: {author}
注疏著作: {work}

【注疏文本】
{text}

输出 schema：
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
