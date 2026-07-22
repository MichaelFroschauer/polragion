from datetime import datetime
from uuid import uuid4, UUID

from pydantic import SecretStr, Field

from polragion.utils.general import StrictModel, utc_now


class OAuthToken(StrictModel):
    value: SecretStr
    expires_at: datetime


class User(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    github_user_id: str # Stable extern GitHub id
    username: str
    created_at: datetime = Field(default_factory=utc_now)


class GitHubCredentials(StrictModel):
    user_id: UUID

    access_token_encrypted: str
    access_token_expires_at: datetime

    refresh_token_encrypted: str
    refresh_token_expires_at: datetime

    updated_at: datetime = Field(default_factory=utc_now)


class UserSession(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID

    token_hash: str # Only the SHA-256-Hash is saved on the server

    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = None
