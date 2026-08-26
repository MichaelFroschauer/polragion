from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from polragion.app import app, logger
from polragion.infrastructure.copilot_service import (
    GitHubCredentialsMissingError,
    GitHubReauthenticationRequiredError,
    GitHubTokenRefreshError,
    CopilotRequestError,
)
from polragion.infrastructure.errors import VectorStoreUnavailableError


@app.exception_handler(VectorStoreUnavailableError)
async def handle_vector_store_unavailable(
        request: Request,
        exc: VectorStoreUnavailableError,
) -> JSONResponse:
    logger.warning(
        "Vector store unavailable during %s %s: %s",
        request.method,
        request.full_url,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Vector store is temporarily unavailable"},
    )


@app.exception_handler(GitHubCredentialsMissingError)
@app.exception_handler(GitHubReauthenticationRequiredError)
async def handle_github_auth_error(
        request: Request,
        exc: GitHubCredentialsMissingError | GitHubReauthenticationRequiredError,
) -> JSONResponse:
    logger.warning("GitHub authentication required during %s %s: %s", request.method, request.full_url, exc)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "GitHub reauthentication required", "code": "github_reauth_required"},
    )


@app.exception_handler(GitHubTokenRefreshError)
async def handle_github_token_refresh_error(
        request: Request,
        exc: GitHubTokenRefreshError,
) -> JSONResponse:
    logger.warning("GitHub token refresh failed during %s %s: %s", request.method, request.full_url, exc)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "GitHub token refresh failed", "code": "github_token_refresh_failed"},
    )


@app.exception_handler(CopilotRequestError)
async def handle_copilot_request_error(
        request: Request,
        exc: CopilotRequestError,
) -> JSONResponse:
    logger.error("Copilot request error during %s %s: %s", request.method, request.full_url, exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Copilot request failed", "code": "copilot_request_failed"},
    )

@app.exception_handler(Exception)
async def handle_unexpected_error(
        request: Request,
        exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled error during %s %s",
        request.method,
        request.full_url,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
