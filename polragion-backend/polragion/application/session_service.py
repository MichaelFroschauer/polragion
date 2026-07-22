import hashlib
import secrets

from datetime import timedelta
from uuid import UUID

from polragion.database.repository import SessionRepository
from polragion.models.user import UserSession
from polragion.utils.general import utc_now


class SessionService:

    def __init__(self, repository: SessionRepository, session_lifetime: timedelta = timedelta(days=7)) -> None:
        self._repository = repository
        self._session_lifetime = session_lifetime

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create_session(self, user_id: UUID) -> str:
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)

        session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=utc_now() + self._session_lifetime,
        )

        await self._repository.create(session)

        return raw_token

    async def resolve_session(self, raw_token: str) -> UserSession | None:
        token_hash = self._hash_token(raw_token)
        session = await self._repository.get_by_token_hash(token_hash)

        if session is None:
            return None

        if session.revoked_at is not None:
            return None

        if session.expires_at <= utc_now():
            return None

        return session

    async def revoke_session(self, raw_token: str) -> None:
        token_hash = self._hash_token(raw_token)
        session = await self._repository.get_by_token_hash(token_hash)

        if session is not None:
            await self._repository.revoke(session.id)