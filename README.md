# FastAPI Auth + Telegram Base

Reusable FastAPI modular monolith containing email/JWT authentication, user
profiles, Telegram login and linking, webhook management, OpenRouter strategy,
and an Opik tracing wrapper.

## Setup

```bash
cp .env.example .env
docker compose up -d --build
docker exec anno-bot-be-api alembic upgrade head
```

The API runs at `http://localhost:8000`; OpenAPI is available at `/docs`.

This cleanup replaces the old migration history. Reset any existing development
database before applying the new baseline:

```bash
docker compose down -v
docker compose up -d --build
docker exec anno-bot-be-api alembic upgrade head
```

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Repository rules and architecture are documented in [`docs/handbook`](docs/handbook).
