# API, Repository, And Service Patterns

## Response Envelope

Normal API endpoints return `ResponseSchema`.

```python
@router.get("/me", response_model=ResponseSchema[UserInfo])
def get_me(...):
    result = service.get_me(current_user)
    return ResponseSchema(data=result, message="User profile fetched successfully")
```

Use raw dictionaries only for health/system endpoints where the response is intentionally outside the application envelope.

## List Responses

Use `FindResult[T]` for paginated or searchable list responses when returning list pages.

## Dependency Wiring

Module route files own service factories and wire concrete repository adapters.

```python
def get_user_service(db=Depends(get_db)) -> UserService:
    user_repository = UserRepository(lambda: nullcontext(db))
    return UserService(user_repository=user_repository)
```

Do not instantiate request services at module import time. They depend on the request session.

## Error Pattern

Expected application failures use `AppError` subclasses:

- `DuplicatedError` -> 400
- `AuthError` -> 401
- `NotFoundError` -> 404
- `ValidationError` -> 422

## Base Repository

`app/common/repositories/base.py` provides common CRUD and list behavior. Module repositories should add only query methods that cannot be expressed clearly through the base behavior.

## Unit Of Work

Use `UnitOfWork` from `app/common/repositories/unit_of_work.py` when one action writes multiple repositories and must commit or rollback together. Do not manually commit inside a `UnitOfWork` block.
