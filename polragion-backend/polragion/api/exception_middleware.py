from urllib.request import Request

from starlette import status
from starlette.responses import JSONResponse

from polragion.app import app, logger
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
