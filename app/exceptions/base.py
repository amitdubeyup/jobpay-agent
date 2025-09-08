"""
Base exception classes for the JobPay Agent application.
"""

from typing import Optional, Dict, Any


class JobPayException(Exception):
    """
    Base exception class for all JobPay application exceptions.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "JOBPAY_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
