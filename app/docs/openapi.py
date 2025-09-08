"""
Enhanced OpenAPI documentation configuration.
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def create_openapi_schema(app: FastAPI):
    """
    Create enhanced OpenAPI schema with detailed documentation.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="JobPay Agent API",
        version="1.0.0",
        description="""
        ## AI-Powered Job Matching Platform

        The JobPay Agent API provides intelligent job matching capabilities powered by AI.
        This RESTful API enables seamless integration between job seekers and employers
        through advanced matching algorithms and comprehensive notification systems.

        ### Key Features
        
        * **🤖 AI-Powered Matching**: Advanced algorithms to match candidates with relevant positions
        * **🔐 Secure Authentication**: JWT-based authentication with role-based access control
        * **📊 Real-time Analytics**: Performance metrics and matching insights
        * **📧 Multi-channel Notifications**: Email, SMS, WhatsApp, and push notifications
        * **🚀 High Performance**: Redis caching and async operations for optimal speed
        * **📈 Monitoring**: Comprehensive health checks and performance monitoring

        ### Authentication

        Most endpoints require authentication using JWT tokens:

        1. Register or login to get an access token
        2. Include the token in the Authorization header: `Bearer <token>`
        3. Refresh tokens when needed using the refresh endpoint

        ### Rate Limiting

        API requests are rate-limited to ensure fair usage:
        - **60 requests per minute** for most endpoints
        - **1000 requests per hour** for authenticated users
        - **10000 requests per day** for premium accounts

        ### Error Handling

        The API uses standard HTTP status codes and returns detailed error information:

        ```json
        {
            "error": true,
            "error_code": "VALIDATION_ERROR",
            "message": "Field validation failed",
            "details": {
                "field": "email",
                "expected_format": "Valid email address"
            },
            "path": "/api/v1/users",
            "timestamp": 1640995200.0
        }
        ```

        ### Versioning

        The API is versioned using URL prefixes:
        - **v1**: Current stable version (`/api/v1/`)
        - Future versions will be available at `/api/v2/`, etc.

        ### Support

        For technical support or questions:
        - 📧 Email: support@jobpay.in
        - 🌐 Website: https://jobpay.in
        - 📚 Documentation: https://docs.jobpay.in
        """,
        routes=app.routes,
        contact={
            "name": "JobPay India Support",
            "url": "https://jobpay.in/support",
            "email": "support@jobpay.in"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "https://api.jobpay.in",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.jobpay.in", 
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ]
    )
    
    # Add custom extensions
    openapi_schema["x-logo"] = {
        "url": "https://jobpay.in/logo.png",
        "altText": "JobPay Logo"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Add response examples
    openapi_schema["components"]["examples"] = {
        "ValidationError": {
            "summary": "Validation Error Example",
            "value": {
                "error": True,
                "error_code": "VALIDATION_ERROR",
                "message": "Field validation failed",
                "details": {
                    "field": "email",
                    "expected_format": "Valid email address"
                }
            }
        },
        "AuthenticationError": {
            "summary": "Authentication Error Example", 
            "value": {
                "error": True,
                "error_code": "AUTHENTICATION_ERROR",
                "message": "Invalid or expired token"
            }
        },
        "NotFoundError": {
            "summary": "Not Found Error Example",
            "value": {
                "error": True,
                "error_code": "NOT_FOUND", 
                "message": "Resource not found"
            }
        },
        "RateLimitError": {
            "summary": "Rate Limit Error Example",
            "value": {
                "error": True,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please try again later.",
                "details": {
                    "retry_after": 60
                }
            }
        }
    }
    
    # Add common response schemas
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {"type": "boolean"},
            "error_code": {"type": "string"},
            "message": {"type": "string"},
            "details": {"type": "object"},
            "path": {"type": "string"},
            "timestamp": {"type": "number"}
        },
        "required": ["error", "error_code", "message"]
    }
    
    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object", 
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "object"}
        },
        "required": ["success"]
    }
    
    # Add tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.jobpay.in/auth"
            }
        },
        {
            "name": "Users",
            "description": "User profile management for job seekers and employers",
            "externalDocs": {
                "description": "User Management Guide", 
                "url": "https://docs.jobpay.in/users"
            }
        },
        {
            "name": "Jobs",
            "description": "Job posting and search functionality",
            "externalDocs": {
                "description": "Job Management Guide",
                "url": "https://docs.jobpay.in/jobs"
            }
        },
        {
            "name": "Matching",
            "description": "AI-powered job matching algorithms",
            "externalDocs": {
                "description": "Matching Algorithm Guide",
                "url": "https://docs.jobpay.in/matching"
            }
        },
        {
            "name": "Notifications",
            "description": "Multi-channel notification system",
            "externalDocs": {
                "description": "Notification Guide",
                "url": "https://docs.jobpay.in/notifications"
            }
        },
        {
            "name": "Analytics",
            "description": "Performance metrics and analytics",
            "externalDocs": {
                "description": "Analytics Guide",
                "url": "https://docs.jobpay.in/analytics"
            }
        },
        {
            "name": "Health",
            "description": "System health and monitoring endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
