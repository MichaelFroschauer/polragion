import logging
from datetime import timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, Query, HTTPException, Depends

import secrets
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette import status

from polragion.api.dependencies import get_settings, get_user_repository, get_github_credentials_repository, \
    get_session_service
from polragion.application.session_service import SessionService
from polragion.database.repository import UserRepository, GitHubCredentialsRepository
from polragion.models.user import OAuthToken, GitHubCredentials, User, UserSession
from polragion.settings import Settings
from polragion.utils.token_cipher import TokenCipher
from polragion.utils.general import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/github", tags=["GitHub authentication"])


async def _exchange_code_for_token(code: str, settings: Settings) -> tuple[OAuthToken, OAuthToken]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )

        response.raise_for_status()
        data = response.json()

    if error := data.get("error"):
        description = data.get("error_description", "Unknown GitHub-OAuth-Error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error}: {description}")

    access_token = data.get("access_token")
    access_token_expires_in = data.get("expires_in")

    if not access_token or not access_token_expires_in:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub did not respond with an access token")

    expiration_seconds_buffer = 300 # 5 minutes
    access_token_expiration_time = utc_now() + timedelta(seconds=max(access_token_expires_in - expiration_seconds_buffer, 0))

    refresh_token = data.get("refresh_token")
    refresh_token_expires_in = data.get("refresh_token_expires_in")

    if not refresh_token or not refresh_token_expires_in:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub did not respond with an refresh token")

    refresh_token_expiration_time = utc_now() + timedelta(seconds=max(refresh_token_expires_in - expiration_seconds_buffer, 0))

    return (OAuthToken(value=access_token, expires_at=access_token_expiration_time),
            OAuthToken(value=refresh_token, expires_at=refresh_token_expiration_time))


async def get_current_user(
        request: Request,
        user_repository: Annotated[UserRepository, Depends(get_user_repository)],
        session_service: Annotated[SessionService, Depends(get_session_service)],
) -> User:

    raw_session_token = request.session.get("sid")

    if not isinstance(raw_session_token, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session: UserSession | None = await session_service.resolve_session(raw_session_token)

    if session is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user: User | None = await user_repository.get_by_id(session.user_id)

    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    return user


@router.get(
    "/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT
)
async def github_login(
        request: Request,
        settings: Annotated[Settings, Depends(get_settings)],
):
    state = secrets.token_urlsafe(32)

    request.session["github_oauth_state"] = state

    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "state": state,
        }
    )

    authorization_url = f"https://github.com/login/oauth/authorize?{query}"

    return RedirectResponse(url=authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get(
    "/callback",
    include_in_schema=False,
)
async def github_callback(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    credentials_repository: Annotated[GitHubCredentialsRepository, Depends(get_github_credentials_repository)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    expected_state = request.session.pop("github_oauth_state", None)

    if not state or not isinstance(expected_state, str) or not secrets.compare_digest(state, expected_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth-State")

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=error_description or error)

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub did not respond with an authorization code")

    access_token, refresh_token = await _exchange_code_for_token(code, settings)

    async with httpx.AsyncClient(timeout=15.0) as client:
        github_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token.value.get_secret_value()}",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "polragion",
            },
        )

    if github_response.status_code != status.HTTP_200_OK:
        logger.error("GitHub /user failed: status=%s body=%s", github_response.status_code, github_response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub user information could not be retrieved")

    github_data = github_response.json()
    user = await user_repository.upsert_from_github(
        github_user_id=str(github_data["id"]),
        username=github_data["login"],
    )

    token_cipher = TokenCipher(settings.encryption_secret)
    credentials = GitHubCredentials(
        user_id=user.id,
        access_token_encrypted=token_cipher.encrypt(access_token.value.get_secret_value()),
        access_token_expires_at=access_token.expires_at,
        refresh_token_encrypted=token_cipher.encrypt(refresh_token.value.get_secret_value()),
        refresh_token_expires_at=refresh_token.expires_at,
    )

    await credentials_repository.upsert(credentials)

    raw_session_token = await session_service.create_session(user.id)
    request.session.clear()
    request.session["sid"] = raw_session_token

    return RedirectResponse(url=settings.frontend_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout(
        request: Request,
        session_service: Annotated[SessionService, Depends(get_session_service)],
):
    raw_session_token = request.session.get("sid")

    if isinstance(raw_session_token, str):
        await session_service.revoke_session(raw_session_token)

    request.session.clear()
    return {"authenticated": False}


@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
async def me(
        current_user: Annotated[User, Depends(get_current_user)]
):
    return {
        "id": str(current_user.id),
        "github_user_id": current_user.github_user_id,
        "username": current_user.username,
    }