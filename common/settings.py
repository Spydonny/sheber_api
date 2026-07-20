"""Конфиг из окружения. Каждый ключ опционален — сервис деградирует, но не падает."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# .env живёт локально в своём слое (bot/.env или api/.env), а не в корне репо —
# грузим явно по пути, не полагаясь на upward-поиск от текущей рабочей директории.
LAYER_DIR = Path(__file__).resolve().parent.parent
load_dotenv(LAYER_DIR / ".env")


class Settings:
    # Mongo (общая БД bot/ и api/)
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip()
    DB_NAME: str = os.getenv("DB_NAME", "sheber").strip()

    # DeepSeek v4 flash — диалог (NLU) + enrichment
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()

    # Groq — vision (фото) и ASR (голосовые). У DeepSeek нет ни того, ни другого.
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct").strip()
    ASR_MODEL: str = os.getenv("ASR_MODEL", "whisper-large-v3-turbo").strip()

    # Websearch для "додумывания" цены/характеристик
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()

    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

    # WhatsApp (Green API) — отдельный инстанс под Шебер
    GREEN_API_ID_INSTANCE: str = os.getenv("GREEN_API_ID_INSTANCE", "").strip()
    GREEN_API_TOKEN: str = os.getenv("GREEN_API_TOKEN", "").strip()
    GREEN_API_BASE_URL: str = os.getenv("GREEN_API_BASE_URL", "https://api.green-api.com").rstrip("/")

    # Публичные URL
    PUBLIC_MARKET_URL: str = os.getenv("PUBLIC_MARKET_URL", "http://localhost:5173").rstrip("/")
    # Медиа хранится в GridFS и раздаётся сервисом api/ — базовый URL до него, из
    # которого бот собирает ссылки на фото ({PUBLIC_MEDIA_URL}/media/{id}).
    PUBLIC_MEDIA_URL: str = os.getenv("PUBLIC_MEDIA_URL", "http://localhost:8000").rstrip("/")

    PORT: int = int(os.getenv("PORT", "8001"))
    # API_PORT — для локальной разработки. На Railway/PaaS PORT задаётся платформой.
    API_PORT: int = int(os.getenv("API_PORT", os.getenv("PORT", "8000")))

    # CORS для api/ (список через запятую). "*" по умолчанию.
    # На Railway/Vercel — задать CORS_ORIGINS=https://sheber-nine.vercel.app
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*").strip()

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def deepseek_enabled(self) -> bool:
        return bool(self.DEEPSEEK_API_KEY)

    @property
    def vision_enabled(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def asr_enabled(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def search_enabled(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.BOT_TOKEN)

    @property
    def whatsapp_enabled(self) -> bool:
        return bool(self.GREEN_API_ID_INSTANCE and self.GREEN_API_TOKEN)


settings = Settings()
