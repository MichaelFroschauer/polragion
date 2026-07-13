import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from typing import Union, Dict, Any

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self, request: Request, call_next
    ) -> Union[JSONResponse, Dict[str, Any]]:
        try:
            return await call_next(request)
        except Exception as e:
            error_info = {
                "error": str(e),
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
            logger.error(error_info)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
