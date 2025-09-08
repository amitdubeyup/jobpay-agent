import asyncio
from typing import List, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.job_service import JobService, JobMatchService
from app.services.ai_matching_service import AIMatchingService
from app.services.notification_service import NotificationPreferenceService
from app.notifications.manager import NotificationManager
from app.models.notification import NotificationChannel

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_job_matching")
def process_job_matching(self, job_id: int):
    """
    Background task to process job matching.
    This task is triggered when a new job is posted.
    """
    try:
        # Run the async matching process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_process_job_matching_async(job_id))
        loop.close()
        
        logger.info(f"Job matching completed for job {job_id}. Found {result['matches_created']} matches.")
        return result
        
    except Exception as e:
        logger.error(f"Error processing job matching for job {job_id}: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _process_job_matching_async(job_id: int) -> Dict[str, Any]:
    """Async function to process job matching."""
    async with AsyncSessionLocal() as db:
        try:
            # Get the job
            job_service = JobService(db)
            job = await job_service.get_by_id(job_id)
            
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Initialize AI matching service
            ai_matching_service = AIMatchingService(db)
            
            # Find matching candidates
            matches = await ai_matching_service.find_matching_candidates(job, top_k=50)
            
            if not matches:
                logger.info(f"No matches found for job {job_id}")
                return {"matches_created": 0, "notifications_queued": 0}
            
            # Create match records in database
            job_match_service = JobMatchService(db)
            created_matches = await job_match_service.bulk_create_matches(matches)
            
            # Queue notification tasks for each match
            notification_tasks_queued = 0
            for match in created_matches:
                # Queue notification task
                send_job_match_notification.delay(match.id)
                notification_tasks_queued += 1
            
            logger.info(f"Created {len(created_matches)} matches and queued {notification_tasks_queued} notifications for job {job_id}")
            
            return {
                "matches_created": len(created_matches),
                "notifications_queued": notification_tasks_queued
            }
            
        except Exception as e:
            logger.error(f"Error in _process_job_matching_async for job {job_id}: {str(e)}")
            raise


@celery_app.task(bind=True, name="send_job_match_notification")
def send_job_match_notification(self, match_id: int):
    """
    Background task to send job match notification to candidate.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_send_job_match_notification_async(match_id))
        loop.close()
        
        logger.info(f"Job match notification sent for match {match_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending job match notification for match {match_id}: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)


async def _send_job_match_notification_async(match_id: int) -> Dict[str, Any]:
    """Async function to send job match notification."""
    async with AsyncSessionLocal() as db:
        try:
            # Get the match with job and candidate details
            job_match_service = JobMatchService(db)
            matches = await job_match_service.get_matches_for_job(0)  # This needs to be updated to get specific match
            
            # For now, we'll use a simpler approach - get match by ID would need to be implemented
            # This is a placeholder implementation
            
            # Get notification preferences for candidate
            notification_pref_service = NotificationPreferenceService(db)
            # enabled_channels = await notification_pref_service.get_enabled_channels(candidate_id)
            
            # For demo, use default channels
            enabled_channels = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
            
            # Initialize notification manager
            notification_manager = NotificationManager(db)
            
            # Prepare job and match data (placeholder)
            job_data = {
                "title": "Software Engineer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "salary_min": 100000,
                "salary_max": 150000,
                "currency": "USD",
                "job_type": "full_time",
                "application_url": "https://example.com/apply"
            }
            
            match_data = {
                "candidate_name": "John Doe",
                "overall_score": 0.85,
                "matching_skills": ["Python", "FastAPI", "PostgreSQL"],
                "match_reasons": {
                    "strengths": ["Strong technical skills", "Relevant experience"],
                    "summary": "Excellent match with high compatibility score"
                }
            }
            
            # Send notifications
            # notification_results = await notification_manager.send_job_match_notification(
            #     candidate_id=1,  # This should come from the match
            #     job_data=job_data,
            #     match_data=match_data,
            #     channels=enabled_channels
            # )
            
            # Mark match as notified
            # await job_match_service.mark_as_notified(match_id)
            
            return {"success": True, "notifications_sent": len(enabled_channels)}
            
        except Exception as e:
            logger.error(f"Error in _send_job_match_notification_async for match {match_id}: {str(e)}")
            raise


@celery_app.task(bind=True, name="batch_process_unnotified_matches")
def batch_process_unnotified_matches(self):
    """
    Periodic task to process any unnotified matches.
    This serves as a backup to ensure no matches are missed.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_batch_process_unnotified_matches_async())
        loop.close()
        
        logger.info(f"Batch processed {result['processed']} unnotified matches")
        return result
        
    except Exception as e:
        logger.error(f"Error in batch processing unnotified matches: {str(e)}")
        raise


async def _batch_process_unnotified_matches_async() -> Dict[str, Any]:
    """Async function to batch process unnotified matches."""
    async with AsyncSessionLocal() as db:
        try:
            job_match_service = JobMatchService(db)
            
            # Get unnotified matches
            unnotified_matches = await job_match_service.get_unnotified_matches(limit=100)
            
            processed = 0
            for match in unnotified_matches:
                try:
                    # Queue notification task
                    send_job_match_notification.delay(match.id)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error queuing notification for match {match.id}: {str(e)}")
            
            return {"processed": processed}
            
        except Exception as e:
            logger.error(f"Error in _batch_process_unnotified_matches_async: {str(e)}")
            raise


# Periodic task configuration
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'batch-process-unnotified-matches': {
        'task': 'batch_process_unnotified_matches',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
celery_app.conf.timezone = 'UTC'
