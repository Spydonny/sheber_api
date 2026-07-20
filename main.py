"""Точка входа API маркетплейса.

Запуск:  python -m api.main
"""
from __future__ import annotations

import contextlib
import sys

import uvicorn

from .common.settings import settings

with contextlib.suppress(Exception):
    sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    uvicorn.run("api.routes:app", host="localhost", port=settings.API_PORT, reload=False)
