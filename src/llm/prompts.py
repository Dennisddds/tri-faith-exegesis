"""Prompt templates for scripture interpretation, KG extraction, and comparison."""

SYSTEM_INTERPRETER = """你是一位严谨的比较宗教学与文本阐释助手。
你的任务是基于所给「最接近原典层」的经文，进行可审查的思维链阐释，而不是宣教或护教。
要求：
1. 区分：字面义 / 历史语境义 / 教义结构义 / 可能的误读。
2. 明确不确定之处，不要编造史料。
3. 输出必须是合法 JSON（不要 Markdown 围栏）。
4. 语言：中文为主，关键术语保留原文（巴利文/希腊文/希伯来文/阿拉伯文音译可附注）。
"""

INTERPRET_USER = """请阐释以下经文单元。

传统: {tradition}
文本层说明: {corpus_note}
文献标识: {ref}
标题/名称: {title}

【原典优先文本】
{primary_text}

【辅助译文（若有）】
{secondary_text}

请按以下 JSON schema 输出：
{{
  "ref": "...",
  "tradition": "...",
  "literal_reading": "字面/语法层阅读",
  "historical_context": "可能的历史与文体语境（标明推断）",
  "doctrinal_structure": "教义结构：核心主张、条件、对象、实践指令",
  "key_concepts": [{{"term": "...", "gloss": "...", "role": "..."}}],
  "entities": [{{"name": "...", "type": "person|deity|place|concept|text|practice|community", "note": "..."}}],
  "relations": [{{"source": "...", "relation": "...", "target": "...", "evidence": "..."}}],
  "possible_misreadings": ["..."],
  "open_questions": ["..."],
  "summary": "120字内总结"
}}
"""

COMPARE_SYSTEM = """你是比较阐释学者。请对比「模型对原典的阐释」与「后人注疏」，指出延续、偏移、系统化与可能的时代 retrojection。
输出合法 JSON，不要 Markdown 围栏。
"""

COMPARE_USER = """传统: {tradition}
经文标识: {ref}

【模型原典阐释（摘要字段）】
{model_interpretation}

【后人注疏】
作者: {author}
著作: {work}
时代: {era}
立场标签: {stance}
注疏文本:
{commentary_text}

请输出：
{{
  "ref": "...",
  "commentary_id": "...",
  "continuities": ["模型与注疏一致之处"],
  "divergences": ["偏移或重写之处"],
  "systematization": "后人如何把原典片段系统化/教义化",
  "anachronism_risks": ["可能的时代错置"],
  "kg_delta": {{
    "added_concepts": ["..."],
    "dropped_concepts": ["..."],
    "relation_shifts": ["..."]
  }},
  "verdict": "一句话评价注疏相对原典层的主要运动方向"
}}
"""

KG_NORMALIZE_SYSTEM = """你是知识图谱规范化助手。将实体与关系规范为简洁节点边列表。输出合法 JSON。"""
