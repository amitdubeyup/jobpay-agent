"""
Business logic exceptions for domain-specific errors.
"""

from typing import Optional, Dict, Any
from .base import JobPayException


class BusinessLogicError(JobPayException):
    """
    Exception raised when business logic validation fails.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(JobPayException):
    """
    Exception raised when a requested resource is not found.
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str = None,
        message: str = None
    ):
        if message is None:
            if resource_id:
                message = f"{resource_type} with id '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"

        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class JobMatchingError(BusinessLogicError):
    """
    Exception raised when job matching process fails.
    """

    def __init__(self, message: str = "Job matching failed"):
        super().__init__(
            message=message,
            details={"error_type": "job_matching"}
        )


class NotificationError(BusinessLogicError):
    """
    Exception raised when notification sending fails.
    """

    def __init__(self, message: str, channel: str = None):
        details = {"error_type": "notification"}
        if channel:
            details["channel"] = channel
            
        super().__init__(
            message=message,
            details=details
        )


class InsufficientPermissionsError(BusinessLogicError):
    """
    Exception raised when user lacks permissions for an operation.
    """

    def __init__(self, operation: str, resource: str = None):
        message = f"Insufficient permissions for operation: {operation}"
        if resource:
            message += f" on resource: {resource}"

        super().__init__(
            message=message,
            details={
                "error_type": "insufficient_permissions",
                "operation": operation,
                "resource": resource
            }
        )
