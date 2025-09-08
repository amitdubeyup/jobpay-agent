"""
Validation exceptions for input data validation.
"""

from typing import Optional, Dict, Any, List
from .base import JobPayException


class ValidationError(JobPayException):
    """
    Exception raised when input validation fails.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        
        if field_errors:
            details["field_errors"] = field_errors

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class RequiredFieldError(ValidationError):
    """
    Exception raised when a required field is missing.
    """

    def __init__(self, field_name: str):
        super().__init__(
            message=f"Field '{field_name}' is required",
            details={"field": field_name, "error_type": "required_field"}
        )
        self.error_code = "REQUIRED_FIELD"


class InvalidFormatError(ValidationError):
    """
    Exception raised when a field has an invalid format.
    """

    def __init__(self, field_name: str, value: str = None, expected_format: str = None):
        super().__init__(
            message=f"Field '{field_name}' has invalid format",
            details={
                "field": field_name,
                "value": value,
                "expected_format": expected_format,
                "error_type": "invalid_format"
            }
        )
        self.error_code = "INVALID_FORMAT"


class DuplicateValueError(ValidationError):
    """
    Exception raised when a unique field has a duplicate value.
    """

    def __init__(self, field_name: str, value: str):
        super().__init__(
            message=f"Field '{field_name}' already exists with value '{value}'",
            details={
                "field": field_name,
                "value": value,
                "error_type": "duplicate_value"
            }
        )
        self.error_code = "DUPLICATE_VALUE"
        self.status_code = 409


class InvalidLengthError(ValidationError):
    """
    Exception raised when a field's length is invalid.
    """

    def __init__(
        self, 
        field_name: str, 
        actual_length: int, 
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ):
        # Determine the specific error message
        if min_length is not None and max_length is not None:
            message = f"Field '{field_name}' must be between {min_length} and {max_length} characters long"
        elif min_length is not None:
            message = f"Field '{field_name}' must be at least {min_length} characters long"
        elif max_length is not None:
            message = f"Field '{field_name}' cannot exceed {max_length} characters"
        else:
            message = f"Field '{field_name}' has invalid length"

        details = {
            "field": field_name,
            "actual_length": actual_length,
            "error_type": "invalid_length"
        }
        
        if min_length is not None:
            details["min_length"] = min_length
        if max_length is not None:
            details["max_length"] = max_length

        super().__init__(
            message=message,
            details=details
        )
        self.error_code = "INVALID_LENGTH"
