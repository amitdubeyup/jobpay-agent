"""
Application constants and configuration values.
"""

from enum import Enum
from typing import Dict, List


# Job-related constants
class JobStatus(str, Enum):
    """Job status enumeration."""
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"
    PAUSED = "paused"


class JobType(str, Enum):
    """Job type enumeration."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class ApplicationStatus(str, Enum):
    """Application status enumeration."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# User-related constants
class UserRole(str, Enum):
    """User role enumeration."""
    JOB_SEEKER = "job_seeker"
    EMPLOYER = "employer"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# Notification constants
class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"


class NotificationType(str, Enum):
    """Notification type enumeration."""
    JOB_MATCH = "job_match"
    APPLICATION_UPDATE = "application_update"
    MESSAGE = "message"
    SYSTEM_ALERT = "system_alert"
    PAYMENT_UPDATE = "payment_update"


# Validation constants
EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
COMPANY_NAME_MAX_LENGTH = 100
JOB_TITLE_MAX_LENGTH = 100
JOB_DESCRIPTION_MAX_LENGTH = 5000
SKILL_NAME_MAX_LENGTH = 50
MAX_SKILLS_PER_USER = 50
MAX_SKILLS_PER_JOB = 25

# File upload constants
MAX_FILE_SIZE_MB = 10
ALLOWED_RESUME_EXTENSIONS = {'.pdf', '.doc', '.docx'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}

# Rate limiting constants
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_REQUESTS_PER_HOUR = 1000
RATE_LIMIT_REQUESTS_PER_DAY = 10000

# Pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# Matching algorithm constants
MIN_MATCH_SCORE = 0.1
DEFAULT_MATCH_THRESHOLD = 0.3
HIGH_MATCH_THRESHOLD = 0.7

# Cache constants (in seconds)
CACHE_TTL_SHORT = 300      # 5 minutes
CACHE_TTL_MEDIUM = 1800    # 30 minutes
CACHE_TTL_LONG = 3600      # 1 hour
CACHE_TTL_DAILY = 86400    # 24 hours

# Error messages
ERROR_MESSAGES = {
    "invalid_email": "Invalid email format",
    "password_too_short": f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
    "password_too_long": f"Password cannot exceed {PASSWORD_MAX_LENGTH} characters",
    "username_too_short": f"Username must be at least {USERNAME_MIN_LENGTH} characters",
    "username_too_long": f"Username cannot exceed {USERNAME_MAX_LENGTH} characters",
    "email_required": "Email address is required",
    "password_required": "Password is required",
    "invalid_credentials": "Invalid email or password",
    "account_suspended": "Account has been suspended",
    "account_not_verified": "Account requires email verification",
    "insufficient_permissions": "Insufficient permissions for this operation",
    "resource_not_found": "Requested resource not found",
    "duplicate_email": "Email address already registered",
    "file_too_large": f"File size cannot exceed {MAX_FILE_SIZE_MB}MB",
    "invalid_file_type": "Invalid file type",
    "rate_limit_exceeded": "Rate limit exceeded. Please try again later",
    "invalid_job_status": "Invalid job status",
    "invalid_application_status": "Invalid application status",
    "job_not_active": "Job is not currently active",
    "already_applied": "You have already applied to this job",
    "cannot_apply_own_job": "Cannot apply to your own job posting"
}

# Success messages
SUCCESS_MESSAGES = {
    "user_created": "User account created successfully",
    "user_updated": "User profile updated successfully",
    "job_created": "Job posting created successfully",
    "job_updated": "Job posting updated successfully",
    "application_submitted": "Application submitted successfully",
    "notification_sent": "Notification sent successfully",
    "password_updated": "Password updated successfully",
    "email_verified": "Email address verified successfully"
}

# External service timeouts (in seconds)
EXTERNAL_SERVICE_TIMEOUTS = {
    "openai_api": 30,
    "email_service": 10,
    "sms_service": 15,
    "push_service": 10,
    "redis": 5
}

# Skill categories for better organization
SKILL_CATEGORIES = {
    "programming": [
        "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP", "Go", 
        "Rust", "Swift", "Kotlin", "TypeScript"
    ],
    "web_development": [
        "HTML", "CSS", "React", "Vue.js", "Angular", "Node.js", "Django", 
        "Flask", "Express.js", "Laravel"
    ],
    "mobile_development": [
        "iOS Development", "Android Development", "React Native", "Flutter", 
        "Xamarin", "Ionic"
    ],
    "data_science": [
        "Machine Learning", "Data Analysis", "Statistics", "SQL", "Python", 
        "R", "Tableau", "Power BI", "Pandas", "NumPy"
    ],
    "cloud_platforms": [
        "AWS", "Google Cloud", "Azure", "Docker", "Kubernetes", "Terraform", 
        "Jenkins", "CI/CD"
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", 
        "Cassandra", "Oracle"
    ]
}

# Common job titles by category
JOB_TITLE_CATEGORIES = {
    "engineering": [
        "Software Engineer", "Frontend Developer", "Backend Developer", 
        "Full Stack Developer", "DevOps Engineer", "Site Reliability Engineer",
        "Data Engineer", "Machine Learning Engineer"
    ],
    "product": [
        "Product Manager", "Product Owner", "Product Designer", "UX Designer", 
        "UI Designer", "Business Analyst"
    ],
    "marketing": [
        "Marketing Manager", "Digital Marketing Specialist", "Content Marketing Manager",
        "SEO Specialist", "Social Media Manager", "Marketing Analyst"
    ],
    "sales": [
        "Sales Representative", "Account Manager", "Sales Manager", 
        "Business Development Representative", "Customer Success Manager"
    ]
}
