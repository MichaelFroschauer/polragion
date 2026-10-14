"""Website-session authenticated management of personal MCP credentials."""

from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field

from polragion.api.auth import get_current_user
from polragion.api.dependencies import get_mcp_token_service, get_settings
from polragion.application.mcp_token_service import McpTokenService
from polragion.models.mcp_token import McpTokenInfo
from polragion.models.user import User
from polragion.settings import Settings
from polragion.utils.general import StrictModel

router = APIRouter(prefix="/auth/mcp-tokens", tags=["MCP credentials"])


def require_management_header(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> None:
    # CSRF protection for cookie-authenticated token creation/revocation:
    # cross-site HTML forms cannot set this header; cross-origin JavaScript
    # requires a CORS preflight. Also reject unexpected browser origins.
    if request.headers.get("x-mcp-token-management") != "true":
        raise HTTPException(403, "X-MCP-Token-Management: true is required")
    origin = request.headers.get("origin")
    frontend = urlsplit(settings.frontend_url)
    backend = urlsplit(str(request.base_url))
    allowed = {f"{frontend.scheme}://{frontend.netloc}", f"{backend.scheme}://{backend.netloc}"}
    if origin is not None and origin not in allowed:
        raise HTTPException(403, "Origin is not allowed")

class CreateToken(StrictModel):
    name: str = Field(
        default="PolRAGion MCP Server", min_length=1, max_length=100, pattern=r".*\S.*"
    )

class IssuedToken(StrictModel):
    token: str
    info: McpTokenInfo

class TokenOverview(StrictModel):
    enabled: bool
    lifetime_days: int
    server_url: str | None
    tokens: list[McpTokenInfo]

def metadata(token) -> McpTokenInfo:
    return McpTokenInfo.model_validate(token.model_dump(exclude={"token_hash"}))

@router.get("", response_model=TokenOverview)
async def list_mcp_tokens(
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[McpTokenService, Depends(get_mcp_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenOverview:
    response.headers["Cache-Control"] = "no-store"
    return TokenOverview(
        enabled=settings.mcp_enabled,
        lifetime_days=settings.mcp_token_lifetime_days,
        server_url=settings.mcp_public_url.rstrip("/") + "/mcp/"
        if settings.mcp_public_url
        else None,
        tokens=[metadata(t) for t in await service.list_tokens(user.id)],
    )


@router.post(
    "",
    response_model=IssuedToken,
    status_code=201,
    dependencies=[Depends(require_management_header)],
)
async def create_mcp_token(
    body: CreateToken,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[McpTokenService, Depends(get_mcp_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IssuedToken:
    if not settings.mcp_enabled:
        raise HTTPException(503, "MCP server is disabled")
    raw, token = await service.create_token(user.id, body.name.strip())
    response.headers["Cache-Control"] = "no-store"
    return IssuedToken(token=raw, info=metadata(token))


@router.delete("/{token_id}", status_code=204, dependencies=[Depends(require_management_header)])
async def revoke_mcp_token(
    token_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[McpTokenService, Depends(get_mcp_token_service)],
) -> Response:
    if not await service.revoke_token(token_id, user.id):
        raise HTTPException(404, "Token not found")
    return Response(status_code=204)
