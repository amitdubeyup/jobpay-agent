"""
Authentication and authorization exceptions.
"""

from typing import Optional, Dict, Any
from .base import JobPayException


class AuthenticationError(JobPayException):
    """
    Exception raised when authentication fails.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(JobPayException):
    """
    Exception raised when authorization fails (insufficient permissions).
    """

    def __init__(
        self,
        message: str = "Access denied: insufficient permissions",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class TokenError(AuthenticationError):
    """
    Exception raised when there's a JWT token related error.
    """

    def __init__(
        self,
        message: str = "Token error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.error_code = "TOKEN_ERROR"


class InvalidCredentialsError(AuthenticationError):
    """
    Exception raised when login credentials are invalid.
    """

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)
        self.error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(TokenError):
    """
    Exception raised when JWT token has expired.
    """

    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            details={"error_type": "token_expired"}
        )


class InvalidTokenError(TokenError):
    """
    Exception raised when JWT token is invalid.
    """

    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            message=message,
            details={"error_type": "invalid_token"}
        )
