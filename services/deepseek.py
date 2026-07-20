"""DeepSeek v4 — OpenAI-совместимый клиент (API-слой).

ВЕНДОРИТСЯ из bot/services/deepseek.py — правка там = синхронизировать сюда.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from openai import AsyncOpenAI

from ..common.settings import settings

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)
    return _client


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def complete(
    system: str,
    user: str,
    *,
    temperature: float = 0.4,
    max_tokens: int = 1200,
    timeout: float = 45.0,
    response_format: Optional[dict[str, str]] = None,
) -> Optional[str]:
    if not settings.deepseek_enabled:
        return None
    try:
        kwargs: dict[str, Any] = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }
        if response_format:
            kwargs["response_format"] = response_format
        resp = await _get_client().chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        return content if content and content.strip() else None
    except Exception:
        return None


async def complete_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.4,
    max_tokens: int = 2200,
    timeout: float = 60.0,
    use_response_format: bool = True,
) -> Optional[dict[str, Any]]:
    rf = {"type": "json_object"} if use_response_format else None
    text = await complete(
        system, user,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        response_format=rf,
    )
    if not text:
        return None
    return _extract_json(text)
