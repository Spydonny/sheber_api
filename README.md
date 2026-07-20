# API — REST-маркетплейс Шебер

REST API для витрины покупателя. Читает каталог товаров из MongoDB, отдаёт фото
через GridFS, пишет события учёта (просмотры/лиды/продажи). **Бизнес-логика
(создание карточек, сториборд) живёт в `bot/` — API только обслуживает фронт.**

## Стек

| Слой | Технология |
|---|---|
| Рантайм | Python 3.11 |
| Фреймворк | FastAPI + Uvicorn |
| База данных | MongoDB (Motor async) |
| Медиа | GridFS (фото в Mongo, не на диске) |
| LLM (сториборд) | DeepSeek v4 (OpenAI-совместимый SDK) |
| Валидация | Pydantic v2 |
| Деплой | Docker, Railway |

## Архитектура

```
api/
├── main.py              # Точка входа: uvicorn api.routes:app
├── routes.py            # REST-эндпоинты (create_app → FastAPI)
├── requirements.txt     # Зависимости
├── Dockerfile           # Независимая сборка (cd api && docker build)
├── storyboard_prompt_draft.md  # Промпт для генерации сториборда
├── common/              # Вендорнутый слой (копия bot/common/)
│   ├── settings.py      # Конфиг из api/.env
│   ├── mongo.py         # Motor-клиент (ленивый singleton)
│   ├── repo.py          # Доступ к данным (CRUD товаров, пользователей, событий)
│   └── media.py         # GridFS: сохранение/чтение фото
├── core/
│   └── storyboard.py    # Генерация JSON-сториборда через DeepSeek (POST endpoint)
└── services/
    └── deepseek.py      # OpenAI-совместимый клиент к DeepSeek
```

## Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/categories` | Список категорий |
| GET | `/api/products` | Каталог (фильтры: `?category=&q=&limit=`) |
| GET | `/api/products/{id}` | Карточка товара (+ seller_contact) |
| POST | `/api/products/{id}/lead` | Обращение покупателя (→ контакт продавца) |
| POST | `/api/products/{id}/sale` | Отметка о продаже |
| GET | `/api/products/{id}/storyboard` | Готовый сториборд (если сгенерирован) |
| POST | `/api/products/{id}/storyboard` | Генерация сториборда через DeepSeek |
| GET | `/api/stats` | Общая статистика витрины |
| GET | `/media/{id}` | Фото из GridFS (Cache-Control: 1 день) |

## Локальный запуск

```bash
cd api
cp .env.example .env          # заполнить MONGODB_URI, DEEPSEEK_API_KEY (опционально)
pip install -r requirements.txt
python -m api.main             # http://localhost:8000
```

## Переменные окружения (api/.env)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017` | Подключение к Mongo |
| `DB_NAME` | `sheber` | Имя базы |
| `DEEPSEEK_API_KEY` | — | Для POST /storyboard (опционально) |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | Модель DeepSeek |
| `CORS_ORIGINS` | `*` | Домены фронта через запятую |
| `API_PORT` | `8000` | Порт (на Railway — `$PORT`) |

## Docker

```bash
cd api
docker build -t sheber-api .
docker run -p 8000:8000 --env-file .env sheber-api
```
