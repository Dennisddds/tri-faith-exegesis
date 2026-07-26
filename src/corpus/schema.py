"""Canonical unit schemas for scriptures and ground-truth commentaries."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Tradition = Literal["buddhism", "christianity", "islam"]


class ScriptureUnit(BaseModel):
    """One interpretable atomic unit (chapter / sutta / ayah-group)."""

    tradition: Tradition
    unit_id: str
    ref: str
    title: str = ""
    corpus: str = ""
    primary_language: str = ""
    primary_text: str
    secondary_text: str = ""
    source: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)

    def slug(self) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in self.unit_id).strip("_").lower()


class GTUnit(BaseModel):
    """Later interpretive text treated as ground truth for alignment."""

    tradition: Tradition
    gt_id: str
    aligns_to: str
    author: str
    work: str
    era: str = ""
    stance: str = ""
    text: str
    source: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)
