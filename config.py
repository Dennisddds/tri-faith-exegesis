"""Central configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GRAPH_DIR = DATA_DIR / "graphs"
INTERP_DIR = DATA_DIR / "interpretations"
COMPARE_DIR = DATA_DIR / "comparisons"
CORPUS_DIR = DATA_DIR / "corpus"
GT_DIR = DATA_DIR / "gt"
ALIGN_DIR = DATA_DIR / "alignments"
JOBS_DIR = DATA_DIR / "jobs"
GT_SOURCES_DIR = DATA_DIR / "gt_sources"

Provider = Literal["openai", "anthropic", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Provider = "openai"

    # ChatGPT / OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1"

    # Claude / Anthropic
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-5"

    # Gemini / Google (OpenAI-compatible endpoint)
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-2.5-pro"

    request_timeout: int = 90
    user_agent: str = "ClarificationScriptureBot/1.0 (+research; full-corpus; respectful crawl)"


def get_settings() -> Settings:
    return Settings()


def ensure_data_dirs() -> None:
    for path in (
        RAW_DIR,
        PROCESSED_DIR,
        GRAPH_DIR,
        INTERP_DIR,
        COMPARE_DIR,
        CORPUS_DIR,
        GT_DIR,
        ALIGN_DIR,
        JOBS_DIR,
        GT_SOURCES_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
        for tradition in ("buddhism", "christianity", "islam"):
            (path / tradition).mkdir(parents=True, exist_ok=True)
