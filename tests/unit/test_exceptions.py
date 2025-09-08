"""
Unit tests for custom exception classes.
"""

import pytest
from app.exceptions import (
    JobPayException,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    InvalidCredentialsError,
    ValidationError,
    RequiredFieldError,
    InvalidFormatError,
    DuplicateValueError,
    InvalidLengthError,
    BusinessLogicError,
    NotFoundError,
    JobMatchingError,
    NotificationError,
    InsufficientPermissionsError
)


class TestJobPayException:
    """Test base JobPay exception."""
    
    def test_base_exception_creation(self):
        """Test basic exception creation."""
        exc = JobPayException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details is None
        assert str(exc) == "Test error"
    
    def test_base_exception_with_details(self):
        """Test exception creation with details."""
        details = {"field": "value", "extra": "info"}
        exc = JobPayException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details=details
        )
        
        assert exc.details == details


class TestAuthenticationExceptions:
    """Test authentication-related exceptions."""
    
    def test_authentication_error(self):
        """Test AuthenticationError creation."""
        exc = AuthenticationError("Invalid token")
        
        assert exc.message == "Invalid token"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
    
    def test_authorization_error(self):
        """Test AuthorizationError creation."""
        exc = AuthorizationError("Access denied")
        
        assert exc.message == "Access denied"
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.status_code == 403
    
    def test_token_error(self):
        """Test TokenError creation."""
        exc = TokenError("Token expired")
        
        assert exc.message == "Token expired"
        assert exc.error_code == "TOKEN_ERROR"
        assert exc.status_code == 401
    
    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError creation."""
        exc = InvalidCredentialsError()
        
        assert exc.message == "Invalid email or password"
        assert exc.error_code == "INVALID_CREDENTIALS"
        assert exc.status_code == 401
    
    def test_invalid_credentials_error_custom_message(self):
        """Test InvalidCredentialsError with custom message."""
        exc = InvalidCredentialsError("Custom credentials error")
        
        assert exc.message == "Custom credentials error"
        assert exc.error_code == "INVALID_CREDENTIALS"


class TestValidationExceptions:
    """Test validation-related exceptions."""
    
    def test_validation_error(self):
        """Test ValidationError creation."""
        exc = ValidationError("Validation failed")
        
        assert exc.message == "Validation failed"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 422
    
    def test_required_field_error(self):
        """Test RequiredFieldError creation."""
        exc = RequiredFieldError("email")
        
        assert exc.message == "Field 'email' is required"
        assert exc.error_code == "REQUIRED_FIELD"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
    
    def test_invalid_format_error(self):
        """Test InvalidFormatError creation."""
        exc = InvalidFormatError("email", "user@", "Valid email address")
        
        assert exc.message == "Field 'email' has invalid format"
        assert exc.error_code == "INVALID_FORMAT"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "user@"
        assert exc.details["expected_format"] == "Valid email address"
    
    def test_duplicate_value_error(self):
        """Test DuplicateValueError creation."""
        exc = DuplicateValueError("email", "test@example.com")
        
        assert exc.message == "Field 'email' already exists with value 'test@example.com'"
        assert exc.error_code == "DUPLICATE_VALUE"
        assert exc.status_code == 409
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "test@example.com"
    
    def test_invalid_length_error_too_short(self):
        """Test InvalidLengthError for too short value."""
        exc = InvalidLengthError("password", 5, min_length=8)
        
        assert exc.message == "Field 'password' must be at least 8 characters long"
        assert exc.error_code == "INVALID_LENGTH"
        assert exc.status_code == 422
        assert exc.details["field"] == "password"
        assert exc.details["actual_length"] == 5
        assert exc.details["min_length"] == 8
    
    def test_invalid_length_error_too_long(self):
        """Test InvalidLengthError for too long value."""
        exc = InvalidLengthError("description", 1000, max_length=500)
        
        assert exc.message == "Field 'description' cannot exceed 500 characters"
        assert exc.error_code == "INVALID_LENGTH"
        assert exc.status_code == 422
        assert exc.details["field"] == "description"
        assert exc.details["actual_length"] == 1000
        assert exc.details["max_length"] == 500
    
    def test_invalid_length_error_both_limits(self):
        """Test InvalidLengthError with both min and max limits."""
        exc = InvalidLengthError("username", 2, min_length=3, max_length=20)
        
        assert exc.message == "Field 'username' must be between 3 and 20 characters long"
        assert exc.error_code == "INVALID_LENGTH"
        assert exc.status_code == 422


class TestBusinessExceptions:
    """Test business logic exceptions."""
    
    def test_business_logic_error(self):
        """Test BusinessLogicError creation."""
        exc = BusinessLogicError("Business rule violated")
        
        assert exc.message == "Business rule violated"
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.status_code == 400
    
    def test_business_logic_error_with_details(self):
        """Test BusinessLogicError with details."""
        details = {"rule": "max_applications", "limit": 5}
        exc = BusinessLogicError("Too many applications", details)
        
        assert exc.details == details
    
    def test_not_found_error_with_id(self):
        """Test NotFoundError with resource ID."""
        exc = NotFoundError("User", "123")
        
        assert exc.message == "User with id '123' not found"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "123"
    
    def test_not_found_error_without_id(self):
        """Test NotFoundError without resource ID."""
        exc = NotFoundError("Job")
        
        assert exc.message == "Job not found"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "Job"
        assert exc.details["resource_id"] is None
    
    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message."""
        exc = NotFoundError("User", message="Custom not found message")
        
        assert exc.message == "Custom not found message"
    
    def test_job_matching_error(self):
        """Test JobMatchingError creation."""
        exc = JobMatchingError("AI matching service unavailable")
        
        assert exc.message == "AI matching service unavailable"
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.status_code == 400
        assert exc.details["error_type"] == "job_matching"
    
    def test_job_matching_error_default_message(self):
        """Test JobMatchingError with default message."""
        exc = JobMatchingError()
        
        assert exc.message == "Job matching failed"
    
    def test_notification_error(self):
        """Test NotificationError creation."""
        exc = NotificationError("Failed to send email", "email")
        
        assert exc.message == "Failed to send email"
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.details["error_type"] == "notification"
        assert exc.details["channel"] == "email"
    
    def test_notification_error_without_channel(self):
        """Test NotificationError without channel."""
        exc = NotificationError("Notification failed")
        
        assert exc.details["error_type"] == "notification"
        assert "channel" not in exc.details
    
    def test_insufficient_permissions_error(self):
        """Test InsufficientPermissionsError creation."""
        exc = InsufficientPermissionsError("delete_job", "Job #123")
        
        expected_msg = "Insufficient permissions for operation: delete_job on resource: Job #123"
        assert exc.message == expected_msg
        assert exc.error_code == "BUSINESS_LOGIC_ERROR"
        assert exc.details["operation"] == "delete_job"
        assert exc.details["resource"] == "Job #123"
    
    def test_insufficient_permissions_error_without_resource(self):
        """Test InsufficientPermissionsError without resource."""
        exc = InsufficientPermissionsError("admin_access")
        
        expected_msg = "Insufficient permissions for operation: admin_access"
        assert exc.message == expected_msg
        assert exc.details["operation"] == "admin_access"
        assert exc.details["resource"] is None
