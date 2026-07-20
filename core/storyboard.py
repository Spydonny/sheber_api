"""Генератор сториборда для API-слоя.

ВЕНДОРИТСЯ из bot/core/storyboard.py — правка там = синхронизировать сюда.
API-версия не включает generate_and_store_images (изображения генерирует бот).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..services import deepseek

_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "storyboard_prompt_draft.md"

_SYSTEM_PROMPT: Optional[str] = None


def _load_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        if _PROMPT_PATH.exists():
            _SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
        else:
            _SYSTEM_PROMPT = ""
    return _SYSTEM_PROMPT


CARD_TYPES = {
    "hero", "main_benefit", "features", "specifications",
    "usage", "advantages", "package_delivery", "cta",
}


def _normalize_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(card.get("id", 0)),
        "type": str(card.get("type", "hero")).strip().lower(),
        "title": str(card.get("title", "")).strip(),
        "subtitle": str(card.get("subtitle", "")).strip(),
        "bullets": _clean_bullets(card.get("bullets")),
        "visual_concept": str(card.get("visual_concept", "")).strip(),
        "composition": str(card.get("composition", "")).strip(),
        "camera": str(card.get("camera", "")).strip(),
        "lighting": str(card.get("lighting", "")).strip(),
        "background": str(card.get("background", "")).strip(),
        "palette": _clean_list(card.get("palette"), limit=5),
        "icons": _clean_list(card.get("icons"), limit=6),
        "image_prompt": str(card.get("image_prompt", "")).strip(),
        "source_fields": _clean_list(card.get("source_fields"), limit=20),
    }


def _clean_bullets(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(b).strip() for b in value if str(b).strip()][:5]
    return []


def _clean_list(value: Any, limit: int = 12) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(v).strip() for v in value if str(v).strip()][:limit]


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    analysis = data.get("product_analysis") or {}
    cards_raw = data.get("cards") or []

    return {
        "product_analysis": {
            "category": str(analysis.get("category", "")).strip(),
            "category_label": str(analysis.get("category_label", "")).strip(),
            "style": str(analysis.get("style", "")).strip(),
            "target_audience": str(analysis.get("target_audience", "")).strip(),
            "main_color": str(analysis.get("main_color", "")).strip(),
            "visible_material": str(analysis.get("visible_material", "")).strip(),
            "visible_details": _clean_list(analysis.get("visible_details"), limit=20),
            "visual_notes": _clean_list(analysis.get("visual_notes"), limit=10),
        },
        "cards": [
            _normalize_card(c) for c in cards_raw
            if isinstance(c, dict) and c.get("type", "").strip().lower() in CARD_TYPES
        ],
        "_generated_by": "deepseek",
    }


async def build_storyboard(
    card: dict[str, Any],
    facts: dict[str, Any],
    vision_facts: dict[str, Any],
    photos: list[str],
) -> Optional[dict[str, Any]]:
    prompt = _load_prompt()
    if not prompt:
        return None

    payload = {
        "card": {
            "title": card.get("title"),
            "brand": card.get("brand"),
            "short_description": card.get("short_description"),
            "description": card.get("description"),
            "characteristics": card.get("characteristics"),
            "options": card.get("options"),
            "availability": card.get("availability"),
            "weight_grams": card.get("weight_grams"),
            "dimensions": card.get("dimensions"),
            "price": card.get("price"),
            "old_price": card.get("old_price"),
            "discount_percent": card.get("discount_percent"),
            "currency": card.get("currency"),
            "delivery": card.get("delivery"),
            "badges": card.get("badges"),
            "rating": card.get("rating"),
            "reviews_count": card.get("reviews_count"),
            "sku": card.get("sku"),
            "category": card.get("category"),
            "category_label": card.get("category_label"),
            "photos": photos,
        },
        "facts": {
            "what": facts.get("what"),
            "materials": facts.get("materials"),
            "size": facts.get("size"),
            "highlight": facts.get("highlight"),
            "city": facts.get("city"),
        },
        "vision_facts": vision_facts,
        "photos": photos,
    }

    parsed = await deepseek.complete_json(
        prompt,
        json.dumps(payload, ensure_ascii=False),
        temperature=0.4,
        max_tokens=8000,
        timeout=90.0,
    )
    return _normalize(parsed) if parsed else None
