# Import all models here for Alembic
from app.models.user import User, Candidate, Employer
from app.models.job import Job, JobMatch
from app.models.notification import NotificationPreference, NotificationLog
from app.db.session import Base

__all__ = [
    "User",
    "Candidate", 
    "Employer",
    "Job",
    "JobMatch",
    "NotificationPreference",
    "NotificationLog",
    "Base"
]
