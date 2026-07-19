import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Query, HTTPException, Depends

import secrets
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse

from polragion.api.dependencies import get_settings
from polragion.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/github", tags=["GitHub authentication"])

@router.get("/login")
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

    return RedirectResponse(authorization_url)


@router.get("/callback")
async def github_callback(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=error_description or error,
        )

    expected_state = request.session.pop("github_oauth_state", None)

    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth-State",
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="GitHub did not respond with an authorization code",
        )

    access_token = await exchange_code_for_token(code, settings)

    # Hier:
    # 1. Benutzer mit GET https://api.github.com/user identifizieren
    # 2. Token verschlüsselt serverseitig speichern
    # 3. Eigene Login-Session erstellen


    # Create a copilot client for a single user
    # client = CopilotClient(
    #     github_token=access_token,
    #     use_logged_in_user=False,
    # )
    #
    # user_id = "test_user"
    # session = await client.create_session(
    #     on_permission_request=PermissionHandler.approve_all,
    #     model="gpt-5.4",
    #     session_id=f"user-{user_id}-session"
    # )
    #
    # response = await session.send_and_wait("Hello!")
    # print("The response is: ", response)

    return {
        "authenticated": True,
        # Never respond with the authorization code
    }


async def exchange_code_for_token(code: str, settings: Settings) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )

        response.raise_for_status()
        data = response.json()

    if error := data.get("error"):
        description = data.get(
            "error_description",
            "Unknown GitHub-OAuth-Error",
        )
        raise HTTPException(
            status_code=400,
            detail=f"{error}: {description}",
        )

    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=502,
            detail="GitHub did not respond with an access token",
        )

    return access_token