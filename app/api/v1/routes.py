from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.telegram.routes import router as telegram_router
from app.modules.users.routes import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(telegram_router)
router.include_router(users_router)


@router.get("/ping", tags=["System"])
def ping_v1() -> dict[str, str]:
    return {"message": "pong", "version": "v1"}
