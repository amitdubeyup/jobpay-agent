"""
Error handling middleware for consistent error responses.
"""

import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.exceptions.base import JobPayException

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions and provide consistent error responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle exceptions and return appropriate error responses.
        """
        try:
            response = await call_next(request)
            return response
        except JobPayException as e:
            # Handle custom application exceptions
            logger.warning(f"Application error: {e.message}", exc_info=True)
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            logger.warning(f"HTTP error: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "HTTP_ERROR",
                    "message": e.detail,
                    "details": None
                }
            )
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": None
                }
            )
