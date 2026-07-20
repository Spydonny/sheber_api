"""REST для React-витрины маркетплейса. Бот пишет товары напрямую в Mongo — этот
сервис только читает каталог и пишет события учёта (просмотры/лиды/продажи)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .common import media, repo
from .common.mongo import ensure_indexes
from .common.settings import settings
from .core.storyboard import build_storyboard

CATEGORIES = {
    "jewelry": "Украшения",
    "clothing": "Одежда",
    "food": "Еда",
    "decor": "Декор",
    "other": "Другое",
}


def _contact_link(user: Optional[dict[str, Any]]) -> Optional[str]:
    if not user:
        return None
    channel = user.get("channel")
    channel_id = user.get("channel_id", "")
    if channel == "wa":
        phone = channel_id.split("@")[0]
        return f"https://wa.me/{phone}" if phone else None
    if channel == "tg":
        username = user.get("tg_username")
        return f"https://t.me/{username}" if username else None
    return None


async def _seller_of(product: dict[str, Any]) -> Optional[dict[str, Any]]:
    ref = product.get("seller_ref", "")
    channel, _, channel_id = ref.partition(":")
    if not channel or not channel_id:
        return None
    return await repo.get_user(channel, channel_id)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await ensure_indexes()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Шебер — маркетплейс API", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/categories")
    async def categories() -> dict[str, str]:
        return CATEGORIES

    @app.get("/api/products")
    async def products(
        category: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(default=60, ge=1, le=100),
    ):
        return await repo.list_products(status="published", category=category, q=q, limit=limit)

    @app.get("/api/products/{pid}")
    async def product(pid: str):
        p = await repo.get_product(pid)
        if not p or p.get("status") != "published":
            raise HTTPException(status_code=404, detail="not found")
        await repo.record_event(pid, "view")
        p["views"] = p.get("views", 0) + 1
        # Обогащаем контактами продавца
        seller = await _seller_of(p)
        p["seller_contact"] = {
            "phone": p.get("seller_phone") or (seller.get("phone") if seller else None),
            "link": _contact_link(seller),
        }
        return p

    @app.post("/api/products/{pid}/lead")
    async def lead(pid: str):
        p = await repo.get_product(pid)
        if not p or p.get("status") != "published":
            raise HTTPException(status_code=404, detail="not found")
        seller = await _seller_of(p)
        link = _contact_link(seller)
        phone = p.get("seller_phone") or (seller.get("phone") if seller else None)
        await repo.record_event(pid, "lead")
        return {"contact_url": link, "phone": phone}

    @app.post("/api/products/{pid}/sale")
    async def sale(pid: str):
        p = await repo.get_product(pid)
        if not p:
            raise HTTPException(status_code=404, detail="not found")
        await repo.record_event(pid, "sale")
        return {"ok": True}

    @app.get("/api/sellers/{ref}/stats")
    async def seller_stats(ref: str):
        return await repo.stats(seller_ref=ref)

    @app.get("/api/products/{pid}/storyboard")
    async def product_storyboard(pid: str):
        """Сториборд товара (генерируется ботом по /cards)."""
        p = await repo.get_product(pid)
        if not p or p.get("status") != "published":
            raise HTTPException(status_code=404, detail="not found")
        sb = p.get("storyboard")
        if not sb:
            raise HTTPException(status_code=404, detail="storyboard not yet generated — use /cards in bot")
        return sb

    @app.post("/api/products/{pid}/storyboard")
    async def generate_storyboard(pid: str):
        """Генерирует сториборд через DeepSeek и сохраняет в товар.

        Возвращает сгенерированный JSON или ошибку если DeepSeek недоступен.
        Промпт — storyboard_prompt_draft.md в корне репозитория."""
        p = await repo.get_product(pid)
        if not p:
            raise HTTPException(status_code=404, detail="product not found")

        # Если уже есть — отдаём кешированный
        existing = p.get("storyboard")
        if existing:
            return {"source": "cache", "storyboard": existing}

        facts = p.get("facts") or {}
        vision_facts = p.get("vision_facts") or {}
        photos = p.get("photos") or []

        sb = await build_storyboard(p, facts, vision_facts, photos)
        if sb is None:
            raise HTTPException(
                status_code=503,
                detail="storyboard generation failed — DeepSeek unavailable or returned invalid JSON",
            )

        await repo.update_product(pid, {"storyboard": sb})
        return {"source": "generated", "storyboard": sb}

    @app.get("/api/stats")
    async def public_stats():
        """Общая витринная статистика: изделий, мастеров, просмотров."""
        return await repo.stats()

    @app.get("/media/{media_id}")
    async def get_media(media_id: str):
        """Отдаёт фото товара прямо из GridFS (медиа хранится в Mongo, не на диске)."""
        found = await media.get_media(media_id)
        if found is None:
            raise HTTPException(status_code=404, detail="not found")
        data, content_type = found
        return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})

    return app


app = create_app()
