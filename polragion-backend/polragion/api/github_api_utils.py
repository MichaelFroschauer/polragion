import logging

import httpx
from fastapi import HTTPException
from starlette import status

from polragion.infrastructure.copilot_service import GitHubCredentialsMissingError
from polragion.models.user import OAuthToken, GitHubCredentials
from polragion.settings import Settings
from polragion.utils.general import utc_now
from polragion.utils.token_cipher import TokenCipher

logger = logging.getLogger(__name__)


async def get_github_user(access_token: OAuthToken):
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
    return github_data


async def get_github_access_token(
    code: str,
    settings: Settings,
):
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

    return data


async def get_github_available_models(settings: Settings, credentials: GitHubCredentials):

    if credentials is None or not credentials.access_token_encrypted:
        raise GitHubCredentialsMissingError(f"No GitHub credentials are stored for user {credentials.user_id}")

    token_cipher = TokenCipher(settings.encryption_secret)
    access_token: str = token_cipher.decrypt(credentials.access_token_encrypted)

    async with httpx.AsyncClient(timeout=15.0) as client:
        github_response = await client.get(
            "https://models.github.ai/catalog/models",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "polragion",
            },
        )

    if github_response.status_code != status.HTTP_200_OK:
        logger.error("GitHub /catalog/models failed: status=%s body=%s", github_response.status_code, github_response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub available models for user could not be retrieved")

    github_data = github_response.json()
    return github_data
