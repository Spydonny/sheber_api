"""Слой доступа к данным (Mongo). Вызовы по имени повторяют старый db.py —
save_product/get_product/list_products/stats — плюс новые: пользователи,
события учёта (views/leads/sales), лог сообщений (дедуп + отладка).

ВЕНДОРИТСЯ в bot/common и api/common — правка здесь = синхронизировать обе копии.
"""
from __future__ import annotations

import re
import time
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from .mongo import get_db


def oid(id_str: str) -> Optional[ObjectId]:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


def _serialize(doc: dict[str, Any]) -> dict[str, Any]:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


# ---- users ----

async def upsert_user(channel: str, channel_id: str, **fields: Any) -> dict[str, Any]:
    db = get_db()
    now = time.time()
    update: dict[str, Any] = {"$set": {k: v for k, v in fields.items() if v is not None},
                               "$setOnInsert": {"created_at": now}}
    await db.users.update_one(
        {"channel": channel, "channel_id": channel_id}, update, upsert=True
    )
    doc = await db.users.find_one({"channel": channel, "channel_id": channel_id})
    return _serialize(doc)


async def get_user(channel: str, channel_id: str) -> Optional[dict[str, Any]]:
    db = get_db()
    doc = await db.users.find_one({"channel": channel, "channel_id": channel_id})
    return _serialize(doc) if doc else None


# ---- products ----

async def save_product(data: dict[str, Any]) -> str:
    db = get_db()
    doc = dict(data)
    doc.setdefault("status", "draft")
    doc.setdefault("views", 0)
    doc.setdefault("sales", 0)
    doc.setdefault("leads", 0)
    doc.setdefault("created_at", time.time())
    res = await db.products.insert_one(doc)
    return str(res.inserted_id)


async def update_product(pid: str, fields: dict[str, Any]) -> bool:
    db = get_db()
    _id = oid(pid)
    if _id is None:
        return False
    res = await db.products.update_one({"_id": _id}, {"$set": fields})
    return res.matched_count > 0


async def publish_product(pid: str) -> bool:
    return await update_product(pid, {"status": "published", "published_at": time.time()})


async def get_product(pid: str) -> Optional[dict[str, Any]]:
    db = get_db()
    _id = oid(pid)
    if _id is None:
        return None
    doc = await db.products.find_one({"_id": _id})
    return _serialize(doc) if doc else None


async def list_products(
    seller_ref: Optional[str] = None,
    status: Optional[str] = "published",
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    db = get_db()
    query: dict[str, Any] = {}
    if seller_ref is not None:
        query["seller_ref"] = seller_ref
    if status is not None:
        query["status"] = status
    if category:
        query["category"] = category
    if q:
        pattern = re.escape(q)
        query["$or"] = [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]
    cursor = db.products.find(query).sort("_id", -1).limit(limit)
    return [_serialize(doc) async for doc in cursor]


async def stats(seller_ref: Optional[str] = None) -> dict[str, int]:
    db = get_db()
    query: dict[str, Any] = {"status": "published"}
    if seller_ref is not None:
        query["seller_ref"] = seller_ref
    products = await db.products.count_documents(query)
    agg = db.products.aggregate([
        {"$match": query},
        {"$group": {"_id": None, "views": {"$sum": "$views"}, "sales": {"$sum": "$sales"}, "leads": {"$sum": "$leads"}}},
    ])
    row = await agg.to_list(length=1)
    totals = row[0] if row else {"views": 0, "sales": 0, "leads": 0}
    sellers = len(await db.products.distinct("seller_ref", query)) if seller_ref is None else 1
    return {
        "products": int(products),
        "sellers": int(sellers),
        "views": int(totals.get("views", 0)),
        "leads": int(totals.get("leads", 0)),
        "sales": int(totals.get("sales", 0)),
    }


# ---- events / учёт ----

async def record_event(product_id: str, event_type: str, meta: Optional[dict[str, Any]] = None) -> None:
    """event_type: view | lead | sale. Инкрементит денормализованный счётчик + пишет events."""
    db = get_db()
    _id = oid(product_id)
    if _id is None:
        return
    field = {"view": "views", "lead": "leads", "sale": "sales"}.get(event_type)
    if field is None:
        return
    await db.products.update_one({"_id": _id}, {"$inc": {field: 1}})
    await db.events.insert_one(
        {"product_id": product_id, "type": event_type, "ts": time.time(), "meta": meta or {}}
    )


# ---- messages (лог + дедуп) ----

async def log_message(channel: str, channel_id: str, text: str, wa_id: Optional[str] = None) -> bool:
    """Возвращает True если сообщение новое (не дубликат). wa_id — idMessage Green API."""
    db = get_db()
    doc = {"channel": channel, "channel_id": channel_id, "text": text, "ts": time.time()}
    if wa_id:
        doc["wa_id"] = wa_id
        try:
            await db.messages.insert_one(doc)
        except DuplicateKeyError:
            return False
        return True
    await db.messages.insert_one(doc)
    return True
