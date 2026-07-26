"""Multi-provider LLM client: ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from config import Settings, get_settings


@dataclass
class LLMResponse:
    content: str
    reasoning_content: str
    raw: Any


class LLMClient:
    """Unified chat client selected by LLM_PROVIDER."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = (self.settings.llm_provider or "openai").lower()
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise RuntimeError("LLM_PROVIDER must be one of: openai, anthropic, gemini")

    def _init_openai(self) -> None:
        from openai import OpenAI

        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Copy .env.example to .env and set ChatGPT credentials.")
        self.model = self.settings.openai_model
        self._openai = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
            timeout=self.settings.request_timeout,
        )
        self._mode = "openai"

    def _init_gemini(self) -> None:
        from openai import OpenAI

        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Copy .env.example to .env and set Gemini credentials.")
        self.model = self.settings.gemini_model
        self._openai = OpenAI(
            api_key=self.settings.gemini_api_key,
            base_url=self.settings.gemini_base_url,
            timeout=self.settings.request_timeout,
        )
        self._mode = "openai"

    def _init_anthropic(self) -> None:
        from anthropic import Anthropic

        if not self.settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is missing. Copy .env.example to .env and set Claude credentials."
            )
        self.model = self.settings.anthropic_model
        self._anthropic = Anthropic(
            api_key=self.settings.anthropic_api_key,
            base_url=self.settings.anthropic_base_url or None,
            timeout=self.settings.request_timeout,
        )
        self._mode = "anthropic"

    @retry(wait=wait_exponential(multiplier=1, min=2, max=20), stop=stop_after_attempt(3), reraise=True)
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        enable_thinking: bool = True,
    ) -> LLMResponse:
        if self._mode == "anthropic":
            return self._chat_anthropic(messages, temperature=temperature)
        return self._chat_openai_compatible(messages, temperature=temperature, enable_thinking=enable_thinking)

    def _chat_openai_compatible(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        enable_thinking: bool,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        # Best-effort for models that expose reasoning fields; ignored by others.
        if enable_thinking and self.provider == "openai":
            kwargs["extra_body"] = {"reasoning_effort": "medium"}

        response = self._openai.chat.completions.create(**kwargs)
        message = response.choices[0].message
        content = message.content or ""
        reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None) or ""
        if isinstance(reasoning, dict):
            reasoning = str(reasoning.get("content") or reasoning)
        return LLMResponse(content=content, reasoning_content=str(reasoning or ""), raw=response)

    def _chat_anthropic(self, messages: list[dict[str, str]], *, temperature: float) -> LLMResponse:
        system = ""
        converted: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "system":
                system = f"{system}\n{text}".strip() if system else text
                continue
            if role not in {"user", "assistant"}:
                role = "user"
            converted.append({"role": role, "content": text})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": converted or [{"role": "user", "content": "Hello"}],
            "temperature": temperature,
            "max_tokens": 8192,
        }
        if system:
            kwargs["system"] = system

        response = self._anthropic.messages.create(**kwargs)
        parts = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        content = "\n".join(parts)
        return LLMResponse(content=content, reasoning_content="", raw=response)


# Backward-compatible alias used by existing modules.
DeepSeekClient = LLMClient
