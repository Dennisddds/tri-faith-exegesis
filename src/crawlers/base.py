"""Shared HTTP helpers for respectful scripture crawling."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=12),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    reraise=True,
)
def http_get_json(url: str, *, params: dict[str, Any] | None = None, timeout: int | None = None) -> Any:
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    with httpx.Client(timeout=timeout or max(settings.request_timeout, 90), headers=headers, follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=12),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    reraise=True,
)
def http_get_text(url: str, *, params: dict[str, Any] | None = None, timeout: int | None = None) -> str:
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent, "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(timeout=timeout or max(settings.request_timeout, 90), headers=headers, follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.text


def save_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def polite_pause(seconds: float = 0.35) -> None:
    time.sleep(seconds)
