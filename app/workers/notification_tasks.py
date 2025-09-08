import asyncio
from typing import Dict, Any, List
import logging
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.notifications.manager import NotificationManager
from app.services.notification_service import NotificationLogService
from app.models.notification import NotificationChannel
from app.schemas.notification import NotificationRequest

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="send_notification_task")
def send_notification_task(self, notification_data: Dict[str, Any]):
    """
    Background task to send notifications.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_send_notification_async(notification_data))
        loop.close()
        
        logger.info(f"Notification sent successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _send_notification_async(notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Async function to send notification."""
    async with AsyncSessionLocal() as db:
        try:
            notification_manager = NotificationManager(db)
            
            # Convert channels from strings to enum values
            channels = [NotificationChannel(ch) for ch in notification_data['channels']]
            
            request = NotificationRequest(
                recipient_id=notification_data['recipient_id'],
                recipient_type=notification_data['recipient_type'],
                template_name=notification_data['template_name'],
                channels=channels,
                context_data=notification_data.get('context_data', {}),
                priority=notification_data.get('priority', 'normal')
            )
            
            results = await notification_manager.send_notification(request)
            
            return {
                "success": True,
                "results": results,
                "channels_attempted": len(channels)
            }
            
        except Exception as e:
            logger.error(f"Error in _send_notification_async: {str(e)}")
            raise


@celery_app.task(bind=True, name="send_welcome_notification_task")
def send_welcome_notification_task(self, candidate_id: int, candidate_name: str):
    """
    Background task to send welcome notification to new candidates.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_send_welcome_notification_async(candidate_id, candidate_name))
        loop.close()
        
        logger.info(f"Welcome notification sent to candidate {candidate_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending welcome notification to candidate {candidate_id}: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)


async def _send_welcome_notification_async(candidate_id: int, candidate_name: str) -> Dict[str, Any]:
    """Async function to send welcome notification."""
    async with AsyncSessionLocal() as db:
        try:
            notification_manager = NotificationManager(db)
            
            # Use default channels for welcome notification
            channels = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
            
            results = await notification_manager.send_welcome_notification(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                channels=channels
            )
            
            return {
                "success": True,
                "results": results,
                "candidate_id": candidate_id
            }
            
        except Exception as e:
            logger.error(f"Error in _send_welcome_notification_async: {str(e)}")
            raise


@celery_app.task(bind=True, name="send_job_posted_notification_task")
def send_job_posted_notification_task(self, employer_id: int, employer_name: str, job_title: str):
    """
    Background task to send job posted confirmation to employers.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_send_job_posted_notification_async(employer_id, employer_name, job_title))
        loop.close()
        
        logger.info(f"Job posted notification sent to employer {employer_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending job posted notification to employer {employer_id}: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)


async def _send_job_posted_notification_async(employer_id: int, employer_name: str, job_title: str) -> Dict[str, Any]:
    """Async function to send job posted notification."""
    async with AsyncSessionLocal() as db:
        try:
            notification_manager = NotificationManager(db)
            
            # Use email for employer notifications
            channels = [NotificationChannel.EMAIL]
            
            results = await notification_manager.send_job_posted_notification(
                employer_id=employer_id,
                employer_name=employer_name,
                job_title=job_title,
                channels=channels
            )
            
            return {
                "success": True,
                "results": results,
                "employer_id": employer_id
            }
            
        except Exception as e:
            logger.error(f"Error in _send_job_posted_notification_async: {str(e)}")
            raise


@celery_app.task(bind=True, name="retry_failed_notifications")
def retry_failed_notifications(self):
    """
    Periodic task to retry failed notifications.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_retry_failed_notifications_async())
        loop.close()
        
        logger.info(f"Retried {result['retried']} failed notifications")
        return result
        
    except Exception as e:
        logger.error(f"Error retrying failed notifications: {str(e)}")
        raise


async def _retry_failed_notifications_async() -> Dict[str, Any]:
    """Async function to retry failed notifications."""
    async with AsyncSessionLocal() as db:
        try:
            notification_service = NotificationLogService(db)
            
            # Get failed notifications
            failed_notifications = await notification_service.get_failed_notifications(limit=50)
            
            retried = 0
            for notification in failed_notifications:
                try:
                    # Prepare notification data
                    notification_data = {
                        'recipient_id': notification.recipient_id,
                        'recipient_type': notification.recipient_type,
                        'template_name': notification.template_name,
                        'channels': [notification.channel.value],
                        'context_data': notification.context_data or {},
                        'priority': 'normal'
                    }
                    
                    # Queue retry task
                    send_notification_task.delay(notification_data)
                    
                    # Increment retry count
                    from app.schemas.notification import NotificationLogUpdate
                    await notification_service.update_log(
                        notification.id,
                        NotificationLogUpdate(retry_count=notification.retry_count + 1)
                    )
                    
                    retried += 1
                    
                except Exception as e:
                    logger.error(f"Error retrying notification {notification.id}: {str(e)}")
            
            return {"retried": retried}
            
        except Exception as e:
            logger.error(f"Error in _retry_failed_notifications_async: {str(e)}")
            raise


@celery_app.task(bind=True, name="send_bulk_notifications")
def send_bulk_notifications(self, notifications_data: List[Dict[str, Any]]):
    """
    Background task to send multiple notifications in bulk.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_send_bulk_notifications_async(notifications_data))
        loop.close()
        
        logger.info(f"Bulk notifications processed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {str(e)}")
        raise


async def _send_bulk_notifications_async(notifications_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Async function to send bulk notifications."""
    async with AsyncSessionLocal() as db:
        try:
            notification_manager = NotificationManager(db)
            
            total_sent = 0
            total_failed = 0
            
            for notification_data in notifications_data:
                try:
                    channels = [NotificationChannel(ch) for ch in notification_data['channels']]
                    
                    request = NotificationRequest(
                        recipient_id=notification_data['recipient_id'],
                        recipient_type=notification_data['recipient_type'],
                        template_name=notification_data['template_name'],
                        channels=channels,
                        context_data=notification_data.get('context_data', {}),
                        priority=notification_data.get('priority', 'normal')
                    )
                    
                    results = await notification_manager.send_notification(request)
                    
                    # Count successful sends
                    for result in results:
                        if result.get('success'):
                            total_sent += 1
                        else:
                            total_failed += 1
                            
                except Exception as e:
                    logger.error(f"Error processing bulk notification: {str(e)}")
                    total_failed += len(notification_data.get('channels', []))
            
            return {
                "total_processed": len(notifications_data),
                "total_sent": total_sent,
                "total_failed": total_failed
            }
            
        except Exception as e:
            logger.error(f"Error in _send_bulk_notifications_async: {str(e)}")
            raise
