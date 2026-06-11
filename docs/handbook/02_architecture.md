# Architecture

The backend is a modular monolith. It deploys as one FastAPI service, while code is separated into bounded-context modules with clear dependency boundaries.

## Dependency Direction

```text
app/api/v1/routes.py
  -> app/modules/<module>/routes/
    -> app/modules/<module>/services/
    -> app/modules/<module>/repositories/
      -> app/modules/<module>/models/
```

Route code wires concrete repositories into services. Services may type-hint concrete repositories in this base project, but they must not construct repositories or manage database sessions.

## Layer Responsibilities

### Module Routes

- Define routes, path/query/body parameters, and `response_model`.
- Select auth dependencies such as `get_current_active_user`.
- Wire services and repositories with FastAPI `Depends`.
- Wrap output in `ResponseSchema`.
- Avoid direct SQLAlchemy query logic.

### Module Services

- Own business rules.
- Check domain permissions after loading required data.
- Coordinate repositories.
- Decide when a workflow needs `UnitOfWork`.
- Call LLM, email, or observability helpers when part of a use case.
- Raise `AppError` subclasses for expected failures.

### Module Models

- Own SQLAlchemy models and stable entity-level concepts for the bounded context.
- Stay free of HTTP concepts.
- Avoid importing routes or repository code.

### Module Repositories

- Own SQLAlchemy query details.
- Inherit `BaseRepository` when possible.
- Return models or query result structures for services.
- Do not know about HTTP status codes, response envelopes, or FastAPI dependencies.

### Module Schemas

- `schemas/` owns Pydantic request and response schemas.

### Common

- `app/common` contains cross-module primitives such as `ResponseSchema`, `FindResult`, `BaseRepository`, `UnitOfWork`, base models, and utilities.
- Common code must not contain bounded-context business rules.

### Core

- Configuration, database setup, shared dependencies, auth/security helpers, exceptions, and observability wrappers.

## Clean Architecture Principles & Rationale

While this project does not use deeply nested directories (such as `domain/`, `application/`, `infrastructure/` subfolders within each module) to avoid over-engineering and boilerplate code, it strictly adheres to **Clean Architecture principles**:

1. **Separation of Concerns**:
    - **Routes (API/Presentation)**: Own HTTP concerns, FastAPI dependencies, serialization, and input validation.
    - **Services (Application/Business Logic)**: Contain core business logic, orchestrate use cases, and control transaction boundaries. They are completely decoupled from HTTP frameworks.
    - **Repositories (Data Access/Infrastructure)**: Handle raw database queries and persistence details.
    - **Models (Domain Entities)**: Define core data structures and database models.

2. **Strict Dependency Direction**:
    - Code always imports inward: `routes` -> `services` -> `repositories` -> `models`.
    - Inner layers (like `services` or `models`) have absolutely no knowledge of outer layers (like `routes` or HTTP concepts).

3. **Dependency Inversion & Injection**:
    - Services do not instantiate repositories or manage database sessions directly.
    - Instead, concrete repositories and database sessions are wired and injected at the `routes` level (using FastAPI's `Depends`). This keeps business logic highly testable and decoupled from database infrastructure.

This pragmatically achieves the benefits of Clean Architecture (testability, flexibility, clear boundaries) without the directory nesting overhead.

## Module Contract (Public API)

Each module declares its public API in its `__init__.py`. Only the symbols
listed in `__all__` are considered stable and safe for other modules to use.

```python
# app/modules/users/__init__.py
from app.modules.users.services.users import UserService
from app.modules.users.services.dto import CurrentUser, UserProfile
from app.modules.users.schemas.users import UserInfo

__all__ = ["CurrentUser", "UserService", "UserProfile", "UserInfo"]
```

### Rules

1. **Cross-module imports must go through the package root only.**

   ```python
   # Correct – importing from the module's public API
   from app.modules.users import UserService, UserProfile

   # Forbidden – reaching into internal sub-packages
   from app.modules.users.repositories import UserRepository  # ❌
   from app.modules.users.models import User                  # ❌
   ```

2. **Services communicate with other modules through Services, not Repositories.**

   If module A needs data owned by module B, module A calls module B's
   `Service`, not module B's `Repository`. This keeps internal persistence
   details private to each module.

3. **Dependency direction between modules is one-way and acyclic.**

   `auth` may depend on `users`. `users` must never depend on `auth`.
   Circular dependencies between modules are forbidden.

4. **Dependency wiring happens at the route layer.**

   Route `dependencies.py` files are allowed to instantiate concrete
   repositories and wire them into services, including repositories from
   other modules when building a cross-module service graph.

## Included Modules

- `auth` owns password authentication, JWT issuance, refresh, and auth
  dependencies.
- `users` owns the user model and profile persistence.
