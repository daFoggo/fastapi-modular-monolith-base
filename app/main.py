from collections.abc import Iterable
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.routes import router as v1_router
from app.core.config import settings
from app.core.dependencies import get_database


def _build_cors_origins(origins: Iterable[str]) -> list[str]:
    return [origin for origin in origins if origin and origin != "*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    database = get_database()

    def check_database() -> None:
        with database.session() as session:
            session.execute(text("SELECT 1"))

    await anyio.to_thread.run_sync(check_database)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    # Enable these in production when the public schema should be hidden:
    # docs_url=None if settings.is_production else "/docs",
    # redoc_url=None if settings.is_production else "/redoc",
    # openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(settings.BACKEND_CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
