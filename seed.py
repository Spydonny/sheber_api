"""Демо-товары для витрины (жюри/разработка). Запуск: python -m api.seed"""
from __future__ import annotations

import asyncio
import contextlib
import sys
import time

from .common import repo
from .common.mongo import ensure_indexes, get_db

with contextlib.suppress(Exception):
    sys.stdout.reconfigure(encoding="utf-8")

DEMO_SELLER_TG = ("tg", "999000001")
DEMO_SELLER_WA = ("wa", "77011234567@c.us")

DEMO_PRODUCTS = [
    {
        "seller": DEMO_SELLER_TG,
        "sku": "SHB-JEW-A1B2C3",
        "brand": "Мастерская Айгуль",
        "title": "Серьги «Айгуль»",
        "short_description": "Серебряные серьги ручной работы с натуральной бирюзой.",
        "description": (
            "Серебряные серьги ручной работы с натуральной бирюзой в национальном стиле. "
            "Каждая пара уникальна — лёгкие, идут и на каждый день, и на подарок."
        ),
        "category": "jewelry",
        "characteristics": {"Материал": "серебро 925°, натуральная бирюза", "Размер": "~3.5 см", "Стиль": "этно"},
        "options": [{"name": "Цвет камня", "values": ["бирюза", "оникс"]}],
        "availability": "под заказ",
        "weight_grams": 8,
        "dimensions": "3.5×1.5 см",
        "price": 13500,
        "hashtags": ["ручнаяработа", "серьги", "серебро925", "бирюза", "handmadekz"],
        "keywords": ["серьги ручной работы", "серебряные серьги", "бирюза", "этно украшения", "подарок женщине"],
    },
    {
        "seller": DEMO_SELLER_WA,
        "sku": "SHB-CLO-D4E5F6",
        "brand": "Дала Войлок",
        "title": "Войлочный шарф «Дала»",
        "short_description": "Тёплый шарф из натурального войлока с орнаментом.",
        "description": (
            "Тёплый шарф из натурального войлока ручной валяния с орнаментом. "
            "Мягкий, лёгкий, согревает в любые морозы."
        ),
        "category": "clothing",
        "characteristics": {"Материал": "войлок, шерсть мериноса", "Размер": "180×30 см", "Цвет": "серо-бежевый"},
        "options": [{"name": "Цвет", "values": ["серо-бежевый", "терракотовый"]}],
        "availability": "в наличии",
        "weight_grams": 220,
        "dimensions": "180×30 см",
        "price": 24000,
        "hashtags": ["войлок", "шарф", "handmadekz", "казахскийорнамент"],
        "keywords": ["войлочный шарф", "шарф ручной работы", "мериносовая шерсть", "тёплый шарф", "казахский орнамент"],
    },
    {
        "seller": DEMO_SELLER_TG,
        "sku": "SHB-DEC-G7H8I9",
        "brand": "Глина и Свет",
        "title": "Керамическая ваза «Шар»",
        "short_description": "Ваза ручной лепки минималистичного дизайна.",
        "description": "Ваза ручной лепки из глины с минималистичным дизайном — украсит любой интерьер.",
        "category": "decor",
        "characteristics": {"Материал": "керамика, глазурь", "Высота": "22 см", "Цвет": "молочный"},
        "options": [],
        "availability": "в наличии",
        "weight_grams": 900,
        "dimensions": "22×18×18 см",
        "price": 9500,
        "hashtags": ["керамика", "декор", "handmadekz"],
        "keywords": ["керамическая ваза", "ваза ручной работы", "декор интерьера", "керамика", "минимализм"],
    },
]


async def seed() -> None:
    await ensure_indexes()
    db = get_db()
    await db.products.delete_many({"_demo": True})

    for item in DEMO_PRODUCTS:
        channel, channel_id = item["seller"]
        await repo.upsert_user(channel, channel_id, name="Демо-мастер", city="Алматы")
        seller_ref = f"{channel}:{channel_id}"
        doc = {
            "seller_ref": seller_ref,
            "channel": channel,
            "status": "published",
            "facts": {},
            "photos": [],
            "sku": item["sku"],
            "brand": item["brand"],
            "title": item["title"],
            "short_description": item["short_description"],
            "description": item["description"],
            "category": item["category"],
            "characteristics": item["characteristics"],
            "options": item["options"],
            "availability": item["availability"],
            "weight_grams": item["weight_grams"],
            "dimensions": item["dimensions"],
            "price": item["price"],
            "old_price": None,
            "discount_percent": None,
            "currency": "₸",
            "price_range": {"low": item["price"] - 2000, "high": item["price"] + 3000},
            "price_note": "демо-данные",
            "stock": None,
            "delivery": "Доставка по Казахстану (Kaspi Postomat / CDEK) · самовывоз: Алматы",
            "hashtags": item["hashtags"],
            "keywords": item["keywords"],
            "badges": ["ручная работа"],
            "rating": 0.0,
            "reviews_count": 0,
            "views": 12,
            "leads": 2,
            "sales": 0,
            "published_at": time.time(),
            "_demo": True,
        }
        await repo.save_product(doc)

    print(f"[seed] добавлено {len(DEMO_PRODUCTS)} демо-товаров")


if __name__ == "__main__":
    asyncio.run(seed())
