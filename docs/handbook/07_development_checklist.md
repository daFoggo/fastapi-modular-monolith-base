# Development Checklist

Use this checklist before finishing backend work.

## Architecture

- Module routes import services and wire repository dependencies.
- Service owns business logic and permission checks.
- Service does not construct repositories or manage database sessions.
- Repository owns SQLAlchemy details.
- API schema owns validation and serialization.
- Core shared dependencies are in `app/core`.

## API

- Endpoint has `response_model`.
- Normal endpoint returns `ResponseSchema`.
- Authenticated routes use the right current-user dependency.
- Expected failures raise `AppError` subclasses.
- List endpoints use `FindResult` when returning searchable/paginated results.

## Persistence

- Schema changes have Alembic migrations.
- Migration was reviewed for accidental drops or unrelated changes.
- Soft-delete reads filter deleted records.
- Boolean filters use `.is_(True)` / `.is_(False)`.
- Multi-repository writes use `UnitOfWork` when atomicity matters.

## LLM And Observability

- Deterministic checks happen before LLM calls.
- LLM provider calls go through the strategy layer.
- Opik tracing goes through the observability wrapper.
- Provider and tracing code does not log secrets.

## Verification

Run the smallest useful checks for the change:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

For docs-only changes, `git diff --check` is usually enough.
