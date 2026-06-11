# Project Overview

FastAPI Modular Monolith Base is a reusable backend base. It intentionally
keeps only auth, users, Telegram connection, OpenRouter access, Opik tracing,
database infrastructure, common repository primitives, common schemas, and
migrations.

## Runtime

- Python 3.12+
- FastAPI application in `app/main.py`
- API v1 router mounted at `/api/v1`
- PostgreSQL via SQLAlchemy
- Alembic migrations in `migrations/`
- OpenRouter access through `app/agents/llm_strategy.py`
- Opik tracing through `app/core/observability.py`

## Environment

Configuration lives in `app/core/config.py` and uses `pydantic-settings`.

Load order:

1. `.env`
2. `.env.{ENV}` when present

Important local values:

```env
ENV=dev
DATABASE_URL=postgresql://user:password@db:5432/fastapi_modular_monolith_base
SECRET_KEY=...
FRONTEND_URL=http://localhost:3000
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPIK_PROJECT_NAME=anno_bot
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=...
```

## API Surface

- Email signup, signin, and JWT refresh under `/api/v1/auth`.
- Telegram login at `/api/v1/auth/telegram`.
- Current-user profile under `/api/v1/users`.
- Telegram linking and webhook management under `/api/v1/telegram`.

## Local Development

Docker path:

```bash
docker compose up -d --build
docker exec anno-bot-be-api alembic upgrade head
```

Local app process:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000 --reload-dir app --reload-dir migrations
```

Opik tracing:

```bash
uv run opik endpoint --project "anno_bot" -- uv run uvicorn app.main:app --port 8000 --reload --reload-dir app --reload-dir migrations
```
