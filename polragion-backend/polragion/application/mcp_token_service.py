"""Personal token lifecycle; persistence is supplied through a repository."""

import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from polragion.database.repository import McpTokenRepository
from polragion.models.mcp_token import McpToken
from polragion.utils.general import utc_now


class McpTokenService:
    def __init__(self, repository: McpTokenRepository, lifetime: timedelta):
        self._repository = repository
        self._lifetime = lifetime

    async def create_token(self, user_id: UUID, name: str) -> tuple[str, McpToken]:
        raw = "pmcp_" + secrets.token_urlsafe(32)
        token = McpToken(
            user_id=user_id,
            name=name,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=utc_now() + self._lifetime,
        )
        await self._repository.create(token)
        return raw, token

    async def resolve_token(self, raw: str) -> McpToken | None:
        if not raw.startswith("pmcp_") or len(raw) > 256:
            return None
        token = await self._repository.get_by_token_hash(hashlib.sha256(raw.encode()).hexdigest())
        if token is None or token.revoked_at is not None or token.expires_at <= utc_now():
            return None
        return token

    async def list_tokens(self, user_id: UUID) -> list[McpToken]:
        return await self._repository.list_for_user(user_id)

    async def revoke_token(self, token_id: UUID, user_id: UUID) -> bool:
        return await self._repository.revoke(token_id, user_id)
