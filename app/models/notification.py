from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"
    WEBPUSH = "webpush"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=False)
    webpush_enabled = Column(Boolean, default=True)
    
    # Frequency preferences
    instant_notifications = Column(Boolean, default=True)
    daily_digest = Column(Boolean, default=False)
    weekly_digest = Column(Boolean, default=False)
    
    # Content preferences
    job_matches = Column(Boolean, default=True)
    application_updates = Column(Boolean, default=True)
    profile_updates = Column(Boolean, default=False)
    marketing = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="notification_preferences")


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, nullable=False)  # user or candidate id
    recipient_type = Column(String, nullable=False)  # user, candidate
    
    # Notification details
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    template_name = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    content = Column(String, nullable=False)
    
    # Recipient details
    recipient_email = Column(String, nullable=True)
    recipient_phone = Column(String, nullable=True)
    recipient_device_token = Column(String, nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Provider details
    provider_name = Column(String, nullable=True)
    provider_message_id = Column(String, nullable=True)
    provider_response = Column(JSON, nullable=True)
    
    # Error details
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Context
    context_data = Column(JSON, nullable=True)  # job_id, match_id, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
