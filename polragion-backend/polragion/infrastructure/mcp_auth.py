"""MCP authentication with user-bound local bearer credentials."""

from fastmcp.server.auth import AccessToken, TokenVerifier

from polragion.application.access_policy import AccessDenied, AccessPolicy, PolicyUnavailable

READ_SCOPE = "work-items:read"


class BackendTokenVerifier(TokenVerifier):
    def __init__(self, state):
        super().__init__(required_scopes=[READ_SCOPE])
        self.state = state

    async def verify_token(self, raw: str) -> AccessToken | None:
        token = await self.state.mcp_token_service.resolve_token(raw)
        if token is None:
            return None
        user = await self.state.user_repository.get_by_id(token.user_id)
        if user is None:
            return None
        try:
            AccessPolicy(self.state.settings).require_allowed(user.username)
        except (AccessDenied, PolicyUnavailable):
            return None
        return AccessToken(
            token=raw,
            client_id=str(token.id),
            subject=str(user.id),
            scopes=[READ_SCOPE],
            expires_at=int(token.expires_at.timestamp()),
        )
