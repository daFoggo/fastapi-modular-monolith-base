from app.core.exceptions import DuplicatedError
from app.modules.users.models.user import User
from app.modules.users.repositories.users import UserRepository
from app.modules.users.services.dto import CurrentUser, UserCredentials, UserProfile


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @staticmethod
    def to_user_profile(user: User) -> UserProfile:
        return UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            profile_completed=user.profile_completed,
        )

    @staticmethod
    def to_current_user(user: User) -> CurrentUser:
        return CurrentUser(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
        )

    @staticmethod
    def to_credentials(user: User) -> UserCredentials:
        return UserCredentials(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
        )

    def get_credentials_by_email(self, email: str) -> UserCredentials | None:
        user = self._user_repository.read_by_email(email)
        return self.to_credentials(user) if user else None

    def get_credentials_by_id(self, user_id: str) -> UserCredentials | None:
        user = self._user_repository.read_optional_by_id(user_id)
        return self.to_credentials(user) if user else None

    def get_current_user(self, user_id: str) -> CurrentUser | None:
        user = self._user_repository.read_optional_by_id(user_id)
        return self.to_current_user(user) if user else None

    def get_profile_by_id(self, user_id: str) -> UserProfile | None:
        user = self._user_repository.read_optional_by_id(user_id)
        return self.to_user_profile(user) if user else None

    def create_user(
        self,
        email: str | None,
        hashed_password: str | None,
        name: str,
        user_token: str,
        avatar_url: str | None = None,
        profile_completed: bool = True,
        auto_commit: bool = True,
    ) -> UserProfile:
        user = self._user_repository.create(
            {
                "email": email,
                "name": name,
                "avatar_url": avatar_url,
                "hashed_password": hashed_password,
                "is_active": True,
                "user_token": user_token,
                "profile_completed": profile_completed,
            },
            auto_commit=auto_commit,
        )
        return self.to_user_profile(user)

    def complete_profile(
        self,
        user_id: str,
        name: str | None = None,
        email: str | None = None,
        hashed_password: str | None = None,
    ) -> UserProfile:
        values: dict[str, object] = {"profile_completed": True}
        if name is not None:
            values["name"] = name
        if email is not None:
            existing_user = self._user_repository.read_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise DuplicatedError(
                    detail="Email already belongs to another account."
                )
            values["email"] = email
        if hashed_password is not None:
            values["hashed_password"] = hashed_password

        updated_user = self._user_repository.update(user_id, values)
        return self.to_user_profile(updated_user)
