from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationChannel, NotificationStatus


class NotificationPreferenceBase(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    whatsapp_enabled: bool = False
    webpush_enabled: bool = True
    instant_notifications: bool = True
    daily_digest: bool = False
    weekly_digest: bool = False
    job_matches: bool = True
    application_updates: bool = True
    profile_updates: bool = False
    marketing: bool = False


class NotificationPreferenceCreate(NotificationPreferenceBase):
    candidate_id: int


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    pass


class NotificationPreferenceInDB(NotificationPreferenceBase):
    id: int
    candidate_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationPreference(NotificationPreferenceInDB):
    pass


class NotificationLogBase(BaseModel):
    recipient_id: int
    recipient_type: str
    channel: NotificationChannel
    template_name: str
    subject: Optional[str] = None
    content: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_device_token: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class NotificationLogCreate(NotificationLogBase):
    pass


class NotificationLogUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    provider_name: Optional[str] = None
    provider_message_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None


class NotificationLogInDB(NotificationLogBase):
    id: int
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    provider_name: Optional[str] = None
    provider_message_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationLog(NotificationLogInDB):
    pass


class NotificationRequest(BaseModel):
    recipient_id: int
    recipient_type: str
    template_name: str
    channels: List[NotificationChannel]
    context_data: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high
    scheduled_at: Optional[datetime] = None


class NotificationStats(BaseModel):
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    failure_rate: float
    channel_stats: Dict[str, Dict[str, int]]
