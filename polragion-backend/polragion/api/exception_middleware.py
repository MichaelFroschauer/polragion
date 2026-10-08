import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from polragion.infrastructure.copilot_service import (
    GitHubCredentialsMissingError,
    GitHubReauthenticationRequiredError,
    GitHubTokenRefreshError,
    CopilotRequestError,
)
from polragion.infrastructure.errors import VectorStoreUnavailableError, PolarionDataFetcherError

logger = logging.getLogger(__name__)


def _validation_message(exc: RequestValidationError) -> str:
    query_fields = {
        "prompt": "Prompt",
        "limit": "Result limit",
        "project_id": "Project ID",
        "score_threshold": "Score threshold",
        "limit_work_item_search": "Work item limit",
        "limit_ai_model_work_items": "AI work item limit",
        "project_ids": "Project IDs",
        "project_contexts": "Project contexts",
        "document_categories": "Document categories",
        "do_reranking": "Reranking",
        "answer_detail": "Answer detail",
        "model_id": "Model ID",
        "reasoning_effort": "Reasoning effort",
    }

    for error in exc.errors():
        location = error.get("loc", ())
        if len(location) < 2 or location[0] != "query":
            continue
        label = query_fields.get(location[1])
        if label is None:
            continue

        context = error.get("ctx") or {}
        error_type = error.get("type")
        if error_type == "missing":
            return f"{label} is required."
        for kind, key, description in (
            ("string_too_long", "max_length", "at most {value} characters"),
            ("string_too_short", "min_length", "at least {value} characters"),
            ("less_than_equal", "le", "at most {value}"),
            ("greater_than_equal", "ge", "at least {value}"),
        ):
            value = context.get(key)
            if error_type == kind and isinstance(value, (int, float)):
                requirement = description.format(value=f"{value:,}")
                return f"{label} must have {requirement}." if "characters" in requirement else f"{label} must be {requirement}."

        if error_type in ("int_parsing", "float_parsing", "int_type", "float_type"):
            return f"{label} must be a number."
        return f"Invalid {label.lower()}. Please check your input and try again."

    return "Invalid request parameters. Please check your input and try again."


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": _validation_message(exc)},
        )

    @app.exception_handler(VectorStoreUnavailableError)
    async def handle_vector_store_unavailable(
            request: Request,
            exc: VectorStoreUnavailableError,
    ) -> JSONResponse:
        logger.warning("Vector store unavailable during %s %s: %s", request.method, request.url, exc)
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
        logger.warning("GitHub authentication required during %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "GitHub reauthentication required", "code": "github_reauth_required"},
        )


    @app.exception_handler(GitHubTokenRefreshError)
    async def handle_github_token_refresh_error(
            request: Request,
            exc: GitHubTokenRefreshError,
    ) -> JSONResponse:
        logger.warning("GitHub token refresh failed during %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "GitHub token refresh failed", "code": "github_token_refresh_failed"},
        )


    @app.exception_handler(CopilotRequestError)
    async def handle_copilot_request_error(
            request: Request,
            exc: CopilotRequestError,
    ) -> JSONResponse:
        logger.error("Copilot request error during %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "Copilot request failed", "code": "copilot_request_failed"},
        )


    @app.exception_handler(PolarionDataFetcherError)
    async def handle_polarion_data_fetcher_request_error(
            request: Request,
            exc: PolarionDataFetcherError,
    ) -> JSONResponse:
        logger.error("PolarionDataFetcher request error during %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "PolarionDataFetcher request failed", "code": "polarion_data_ingest_request_failed"},
        )


    @app.exception_handler(Exception)
    async def handle_unexpected_error(
            request: Request,
            exc: Exception,
    ) -> JSONResponse:
        logger.error("Unhandled error during %s %s", request.method, request.url,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
