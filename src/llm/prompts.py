"""Prompt templates for scripture interpretation, KG extraction, and comparison."""

SYSTEM_INTERPRETER = """You are a careful scholar of comparative religion and textual exegesis.
Your task is to produce auditable chain-of-thought interpretations of the given near-primary scripture unit — not preaching or apologetics.
Requirements:
1. Distinguish: literal/grammatical sense / historical-literary context / doctrinal structure / possible misreadings.
2. Mark uncertainty; do not invent historical facts.
3. Output valid JSON only (no Markdown fences).
4. Write in English; keep key terms in the original language where helpful (Pali / Greek / Hebrew / Arabic with optional transliteration).
"""

INTERPRET_USER = """Interpret the following scripture unit.

Tradition: {tradition}
Corpus note: {corpus_note}
Reference: {ref}
Title / name: {title}

[Primary text]
{primary_text}

[Secondary translation, if any]
{secondary_text}

Return JSON with this schema:
{{
  "ref": "...",
  "tradition": "...",
  "literal_reading": "literal / grammatical reading",
  "historical_context": "likely historical and genre context (label inferences)",
  "doctrinal_structure": "doctrinal structure: claims, conditions, addressees, practical directives",
  "key_concepts": [{{"term": "...", "gloss": "...", "role": "..."}}],
  "entities": [{{"name": "...", "type": "person|deity|place|concept|text|practice|community", "note": "..."}}],
  "relations": [{{"source": "...", "relation": "...", "target": "...", "evidence": "..."}}],
  "possible_misreadings": ["..."],
  "open_questions": ["..."],
  "summary": "summary in <= 120 English words"
}}
"""

COMPARE_SYSTEM = """You are a scholar of comparative exegesis. Compare the model's reading of the primary text with a later commentary, noting continuity, divergence, systematization, and possible chronological retrojection.
Output valid JSON only (no Markdown fences).
"""

COMPARE_USER = """Tradition: {tradition}
Reference: {ref}

[Model interpretation of the primary text (selected fields)]
{model_interpretation}

[Later commentary]
Author: {author}
Work: {work}
Era: {era}
Stance label: {stance}
Commentary text:
{commentary_text}

Return:
{{
  "ref": "...",
  "commentary_id": "...",
  "continuities": ["where model and commentary agree"],
  "divergences": ["shifts or rewritings"],
  "systematization": "how later tradition systemizes / doctrinalizes the primary fragment",
  "anachronism_risks": ["possible anachronisms"],
  "kg_delta": {{
    "added_concepts": ["..."],
    "dropped_concepts": ["..."],
    "relation_shifts": ["..."]
  }},
  "verdict": "one-sentence verdict on the commentary's main movement relative to the primary layer"
}}
"""

KG_NORMALIZE_SYSTEM = """You are a knowledge-graph normalization assistant. Convert entities and relations into a compact node/edge list. Output valid JSON only."""
