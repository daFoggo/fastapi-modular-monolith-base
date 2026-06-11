from contextlib import contextmanager, nullcontext

import pytest

from app.common import UnitOfWork
from app.modules.users.repositories import UserRepository


def test_user_repository_crud(database) -> None:
    database.create_database()
    with database.session() as session:
        repository = UserRepository(lambda: nullcontext(session))
        user = repository.create(
            {
                "email": "repo@example.com",
                "name": "Repo",
                "hashed_password": "hash",
                "user_token": "repo-token",
                "is_active": True,
                "profile_completed": True,
            }
        )
        assert repository.read_by_email("repo@example.com").id == user.id
        assert repository.update(user.id, {"name": "Updated"}).name == "Updated"


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


@contextmanager
def fake_session_factory():
    yield FakeSession()


def test_unit_of_work_commits_and_rolls_back() -> None:
    with UnitOfWork(fake_session_factory) as successful:
        success_session = successful.session
    assert success_session.committed is True

    with pytest.raises(ValueError), UnitOfWork(fake_session_factory) as failed:
        failed_session = failed.session
        raise ValueError("failure")
    assert failed_session.rolled_back is True
