"""Backward-compatible import path. Prefer `src.llm.client.LLMClient`. """

from src.llm.client import LLMClient, LLMResponse

DeepSeekClient = LLMClient

__all__ = ["DeepSeekClient", "LLMClient", "LLMResponse"]
