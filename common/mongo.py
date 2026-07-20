"""Ленивый singleton motor-клиента. Общая Mongo для bot/ и api/."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .settings import settings

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client[settings.DB_NAME]


async def ensure_indexes() -> None:
    db = get_db()
    await db.products.create_index("seller_ref")
    await db.products.create_index("status")
    await db.events.create_index("product_id")
    await db.events.create_index("type")
    await db.users.create_index([("channel", 1), ("channel_id", 1)], unique=True)
    await db.messages.create_index("channel_id")
    await db.messages.create_index("wa_id", unique=True, sparse=True)
