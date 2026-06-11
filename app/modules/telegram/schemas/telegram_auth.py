from pydantic import BaseModel, ConfigDict, Field, model_validator


class TelegramLoginRequest(BaseModel):
    id: str | None = None
    auth_date: str | None = None
    hash: str | None = None
    id_token: str | None = None
    code: str | None = None
    redirect_uri: str | None = Field(default=None, max_length=2048)
    code_verifier: str | None = Field(default=None, max_length=256)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=512)
    phone_number: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_login_mode(self) -> "TelegramLoginRequest":
        has_code = self.code is not None
        has_id_token = self.id_token is not None
        has_widget = any(
            value is not None for value in (self.id, self.auth_date, self.hash)
        )
        if sum((has_code, has_id_token, has_widget)) != 1:
            raise ValueError("Provide exactly one Telegram login mode.")
        if has_code and (not self.redirect_uri or not self.code_verifier):
            raise ValueError(
                "Authorization code login requires redirect_uri and code_verifier."
            )
        if has_widget and not all((self.id, self.auth_date, self.hash)):
            raise ValueError("Telegram widget payload is incomplete.")
        return self


class TelegramLinkStartResponse(BaseModel):
    link_url: str
    expires_at: str


class TelegramWebhookResponse(BaseModel):
    ok: bool
    message: str


class TelegramUser(BaseModel):
    id: int | str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(extra="allow")


class TelegramChat(BaseModel):
    id: int | str

    model_config = ConfigDict(extra="allow")


class TelegramMessage(BaseModel):
    text: str | None = None
    chat: TelegramChat | None = None
    from_user: TelegramUser | None = Field(default=None, alias="from")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TelegramCallbackQuery(BaseModel):
    id: str
    data: str | None = None

    model_config = ConfigDict(extra="allow")


class TelegramUpdate(BaseModel):
    update_id: int | None = None
    message: TelegramMessage | None = None
    callback_query: TelegramCallbackQuery | None = None

    model_config = ConfigDict(extra="allow")
