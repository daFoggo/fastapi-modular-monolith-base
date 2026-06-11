from collections.abc import Callable
from importlib import import_module
from typing import Any, TypeVar, cast

from app.core.config import settings

try:
    track = import_module("opik").track
except (ImportError, AttributeError):
    track = None

F = TypeVar("F", bound=Callable[..., Any])


def trace(name: str | None = None, *, entrypoint: bool = False) -> Callable[[F], F]:
    if track is None:

        def passthrough(func: F) -> F:
            return func

        return passthrough

    return cast(
        Callable[[F], F],
        track(
            name=name,
            entrypoint=entrypoint,
            project_name=settings.OPIK_PROJECT_NAME,
        ),
    )
