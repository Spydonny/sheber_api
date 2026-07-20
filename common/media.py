"""Хранение медиа (фото товаров) прямо в MongoDB через GridFS.

GridFS, а не байты в обычном документе: снимает лимит 16MB на документ и корректно
чанкует крупные файлы. Пишет бот (при приёме фото), отдаёт api/ (эндпоинт /media/{id}).

ВЕНДОРИТСЯ в bot/common и api/common — правка здесь = синхронизировать обе копии.
"""
from __future__ import annotations

from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from gridfs.errors import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from .mongo import get_db


def _bucket() -> AsyncIOMotorGridFSBucket:
    return AsyncIOMotorGridFSBucket(get_db(), bucket_name="media")


async def save_media(data: bytes, content_type: str = "image/jpeg", filename: str = "photo.jpg") -> str:
    """Кладёт байты в GridFS, возвращает строковый id для сборки URL."""
    file_id = await _bucket().upload_from_stream(
        filename, data, metadata={"content_type": content_type}
    )
    return str(file_id)


async def get_media(media_id: str) -> Optional[tuple[bytes, str]]:
    """Возвращает (bytes, content_type) или None, если id битый/файла нет.
    Никогда не бросает — вызывающий эндпоинт отдаёт 404."""
    try:
        oid = ObjectId(media_id)
    except (InvalidId, TypeError):
        return None
    try:
        stream = await _bucket().open_download_stream(oid)
        data = await stream.read()
        content_type = (stream.metadata or {}).get("content_type", "application/octet-stream")
        return data, content_type
    except NoFile:
        return None
