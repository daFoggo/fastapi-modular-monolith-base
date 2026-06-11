# Backend Handbook

This handbook is the source of truth for FastAPI Base.

## Reading Order

1. [Project Overview](01_project_overview.md)
2. [Architecture](02_architecture.md)
3. [Feature Development](03_feature_development.md)
4. [API, Repository, And Service Patterns](04_api_repository_service.md)
5. [LLM And Observability](05_ai_agent_runtime.md)
6. [Quality Rules](06_quality_rules.md)
7. [Development Checklist](07_development_checklist.md)

## Core Decisions

- The backend is a modular monolith target deployed as one FastAPI service.
- The main dependency direction inside a module is routes -> services -> repositories -> models.
- FastAPI dependency injection wires request-scoped sessions and services.
- API responses use `ResponseSchema`.
- SQLAlchemy access is hidden behind repositories.
- Business orchestration lives in services.
- Multi-repository writes use `UnitOfWork`.
- LLM access goes through provider strategy classes.
- Opik access goes through `app/core/observability.py`.
- Alembic is required for schema changes.
