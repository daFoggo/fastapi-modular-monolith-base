from contextlib import AbstractContextManager, nullcontext

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.users.repositories.users import UserRepository
from app.modules.users.services.users import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    def session_factory() -> AbstractContextManager[Session]:
        return nullcontext(db)

    return UserService(user_repository=UserRepository(session_factory))
