# Project Overview

FastAPI Base is a reusable modular-monolith backend. It intentionally keeps
only auth, users, OpenRouter access, Opik tracing, database infrastructure,
common repository primitives, common schemas, and migrations.

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
APP_NAME=FastAPI Base
PROJECT_NAME=fastapi-base
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/fastapi_base
SECRET_KEY=...
FRONTEND_URL=http://localhost:3000
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPIK_PROJECT_NAME=fastapi_base
```

## API Surface

- Email signup, signin, and JWT refresh under `/api/v1/auth`.
- Current-user profile under `/api/v1/users`.

## Local Development

Docker path:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Local app process:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000 --reload-dir app --reload-dir migrations
```

Opik tracing:

```bash
uv run opik endpoint --project "fastapi_base" -- uv run uvicorn app.main:app --port 8000 --reload --reload-dir app --reload-dir migrations
```
