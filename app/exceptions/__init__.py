"""
Exception module initialization.
"""

from .base import JobPayException
from .auth import AuthenticationError, AuthorizationError, TokenError, InvalidCredentialsError
from .validation import (
    ValidationError, RequiredFieldError, InvalidFormatError, 
    DuplicateValueError, InvalidLengthError
)
from .business import (
    BusinessLogicError, NotFoundError, JobMatchingError, 
    NotificationError, InsufficientPermissionsError
)

__all__ = [
    # Base exception
    "JobPayException",
    
    # Authentication exceptions
    "AuthenticationError",
    "AuthorizationError", 
    "TokenError",
    "InvalidCredentialsError",
    
    # Validation exceptions
    "ValidationError",
    "RequiredFieldError",
    "InvalidFormatError",
    "DuplicateValueError",
    "InvalidLengthError",
    
    # Business logic exceptions
    "BusinessLogicError",
    "NotFoundError",
    "JobMatchingError",
    "NotificationError",
    "InsufficientPermissionsError"
]
