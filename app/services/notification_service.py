from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from app.models.notification import NotificationLog, NotificationPreference, NotificationStatus, NotificationChannel
from app.schemas.notification import (
    NotificationLogCreate, 
    NotificationLogUpdate,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate
)


class NotificationLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(self, log_data: NotificationLogCreate) -> NotificationLog:
        """Create a notification log entry."""
        log = NotificationLog(**log_data.dict())
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def update_log(self, log_id: int, update_data: NotificationLogUpdate) -> Optional[NotificationLog]:
        """Update notification log."""
        result = await self.db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(log, field, value)
        
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_logs_by_recipient(
        self, 
        recipient_id: int,
        recipient_type: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[NotificationLog]:
        """Get notification logs for a recipient."""
        result = await self.db.execute(
            select(NotificationLog)
            .where(
                and_(
                    NotificationLog.recipient_id == recipient_id,
                    NotificationLog.recipient_type == recipient_type
                )
            )
            .order_by(desc(NotificationLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_failed_notifications(self, limit: int = 100) -> List[NotificationLog]:
        """Get failed notifications for retry."""
        result = await self.db.execute(
            select(NotificationLog)
            .where(
                and_(
                    NotificationLog.status == NotificationStatus.FAILED,
                    NotificationLog.retry_count < 3  # Max retries
                )
            )
            .order_by(NotificationLog.created_at)
            .limit(limit)
        )
        return result.scalars().all()


class NotificationPreferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_candidate_id(self, candidate_id: int) -> Optional[NotificationPreference]:
        """Get notification preferences for a candidate."""
        result = await self.db.execute(
            select(NotificationPreference)
            .where(NotificationPreference.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()
    
    async def create_preferences(self, pref_data: NotificationPreferenceCreate) -> NotificationPreference:
        """Create notification preferences."""
        preferences = NotificationPreference(**pref_data.dict())
        
        self.db.add(preferences)
        await self.db.commit()
        await self.db.refresh(preferences)
        return preferences
    
    async def update_preferences(
        self, 
        candidate_id: int, 
        update_data: NotificationPreferenceUpdate
    ) -> Optional[NotificationPreference]:
        """Update notification preferences."""
        preferences = await self.get_by_candidate_id(candidate_id)
        
        if not preferences:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(preferences, field, value)
        
        await self.db.commit()
        await self.db.refresh(preferences)
        return preferences
    
    async def get_enabled_channels(self, candidate_id: int) -> List[NotificationChannel]:
        """Get enabled notification channels for a candidate."""
        preferences = await self.get_by_candidate_id(candidate_id)
        
        if not preferences:
            # Return default channels if no preferences set
            return [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        
        enabled_channels = []
        
        if preferences.email_enabled:
            enabled_channels.append(NotificationChannel.EMAIL)
        if preferences.sms_enabled:
            enabled_channels.append(NotificationChannel.SMS)
        if preferences.push_enabled:
            enabled_channels.append(NotificationChannel.PUSH)
        if preferences.whatsapp_enabled:
            enabled_channels.append(NotificationChannel.WHATSAPP)
        if preferences.webpush_enabled:
            enabled_channels.append(NotificationChannel.WEBPUSH)
        
        return enabled_channels
