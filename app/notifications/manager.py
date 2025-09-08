from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.notification import NotificationChannel, NotificationStatus
from app.schemas.notification import NotificationRequest, NotificationLogCreate, NotificationLogUpdate
from app.notifications.base import NotificationProvider
from app.notifications.email_provider import EmailProvider
from app.notifications.sms_provider import SMSProvider, WhatsAppProvider
from app.notifications.push_provider import PushNotificationProvider, WebPushProvider
from app.notifications.templates import TemplateManager
from app.services.notification_service import NotificationLogService

logger = logging.getLogger(__name__)


class NotificationManager:
    """Central notification manager that coordinates all notification providers."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.template_manager = TemplateManager()
        self.notification_service = NotificationLogService(db)
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all notification providers."""
        try:
            self.providers[NotificationChannel.EMAIL] = EmailProvider()
            self.providers[NotificationChannel.SMS] = SMSProvider()
            self.providers[NotificationChannel.WHATSAPP] = WhatsAppProvider()
            self.providers[NotificationChannel.PUSH] = PushNotificationProvider()
            self.providers[NotificationChannel.WEBPUSH] = WebPushProvider()
            
            logger.info("Notification providers initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing notification providers: {str(e)}")
    
    async def send_notification(self, request: NotificationRequest) -> List[Dict[str, Any]]:
        """Send notification through multiple channels."""
        results = []
        
        for channel in request.channels:
            try:
                result = await self._send_single_notification(request, channel)
                results.append(result)
            except Exception as e:
                logger.error(f"Error sending {channel} notification: {str(e)}")
                results.append({
                    'channel': channel,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    async def _send_single_notification(
        self, 
        request: NotificationRequest, 
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """Send notification through a single channel."""
        
        # Get provider
        provider = self.providers.get(channel)
        if not provider:
            raise ValueError(f"No provider configured for channel: {channel}")
        
        # Get recipient details based on channel
        recipient_info = await self._get_recipient_info(
            request.recipient_id, 
            request.recipient_type, 
            channel
        )
        
        if not recipient_info:
            raise ValueError(f"No recipient info found for {channel}")
        
        # Render content based on channel
        content_data = self._render_content(request.template_name, channel, request.context_data or {})
        
        # Create notification log entry
        log_entry = NotificationLogCreate(
            recipient_id=request.recipient_id,
            recipient_type=request.recipient_type,
            channel=channel,
            template_name=request.template_name,
            subject=content_data.get('subject'),
            content=content_data.get('content', ''),
            recipient_email=recipient_info.get('email'),
            recipient_phone=recipient_info.get('phone'),
            recipient_device_token=recipient_info.get('device_token'),
            context_data=request.context_data
        )
        
        notification_log = await self.notification_service.create_log(log_entry)
        
        try:
            # Send notification
            result = await provider.send(
                recipient=recipient_info['address'],
                subject=content_data.get('subject', ''),
                content=content_data.get('content', ''),
                context=request.context_data
            )
            
            # Update log with result
            if result['success']:
                await self.notification_service.update_log(
                    notification_log.id,
                    NotificationLogUpdate(
                        status=NotificationStatus.SENT,
                        provider_name=provider.get_provider_name(),
                        provider_message_id=result.get('provider_message_id'),
                        provider_response=result.get('provider_response')
                    )
                )
            else:
                await self.notification_service.update_log(
                    notification_log.id,
                    NotificationLogUpdate(
                        status=NotificationStatus.FAILED,
                        provider_name=provider.get_provider_name(),
                        error_message=result.get('error'),
                        provider_response=result.get('provider_response')
                    )
                )
            
            return {
                'channel': channel,
                'success': result['success'],
                'log_id': notification_log.id,
                'provider_message_id': result.get('provider_message_id'),
                'error': result.get('error')
            }
            
        except Exception as e:
            # Update log with error
            await self.notification_service.update_log(
                notification_log.id,
                NotificationLogUpdate(
                    status=NotificationStatus.FAILED,
                    error_message=str(e)
                )
            )
            raise
    
    async def _get_recipient_info(
        self, 
        recipient_id: int, 
        recipient_type: str, 
        channel: NotificationChannel
    ) -> Optional[Dict[str, Any]]:
        """Get recipient contact information for the specified channel."""
        
        # This would typically query the database for user/candidate contact info
        # For now, return placeholder data
        
        if recipient_type == "candidate":
            # Query candidate and user data
            # candidate = await candidate_service.get_by_id(recipient_id)
            # user = candidate.user
            
            # Placeholder data
            return {
                'address': 'candidate@example.com' if channel == NotificationChannel.EMAIL else '+1234567890',
                'email': 'candidate@example.com',
                'phone': '+1234567890',
                'device_token': 'device_token_placeholder'
            }
        
        elif recipient_type == "employer":
            # Query employer and user data
            return {
                'address': 'employer@example.com' if channel == NotificationChannel.EMAIL else '+1234567890',
                'email': 'employer@example.com', 
                'phone': '+1234567890',
                'device_token': 'device_token_placeholder'
            }
        
        return None
    
    def _render_content(
        self, 
        template_name: str, 
        channel: NotificationChannel, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render notification content for the specified channel."""
        
        if channel == NotificationChannel.EMAIL:
            content = self.template_manager.render_email(template_name, context)
            return {
                'subject': context.get('subject', f"JobPay Notification"),
                'content': content
            }
        
        elif channel == NotificationChannel.SMS:
            content = self.template_manager.render_sms(template_name, context)
            return {
                'content': content
            }
        
        elif channel == NotificationChannel.WHATSAPP:
            content = self.template_manager.render_whatsapp(template_name, context)
            return {
                'content': content
            }
        
        elif channel in [NotificationChannel.PUSH, NotificationChannel.WEBPUSH]:
            push_content = self.template_manager.render_push(template_name, context)
            return {
                'subject': push_content.get('title', ''),
                'content': push_content.get('body', '')
            }
        
        else:
            return {
                'content': f"Notification: {template_name}"
            }
    
    async def send_job_match_notification(
        self, 
        candidate_id: int, 
        job_data: Dict[str, Any],
        match_data: Dict[str, Any],
        channels: List[NotificationChannel]
    ) -> List[Dict[str, Any]]:
        """Send job match notification to candidate."""
        
        context = {
            'candidate_name': match_data.get('candidate_name', 'Candidate'),
            'job_title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', 'Remote'),
            'salary_range': self._format_salary_range(job_data),
            'job_type': job_data.get('job_type', ''),
            'match_score': int(match_data.get('overall_score', 0) * 100),
            'match_strengths': match_data.get('match_reasons', {}).get('strengths', []),
            'match_summary': match_data.get('match_reasons', {}).get('summary', ''),
            'matching_skills': match_data.get('matching_skills', []),
            'application_url': job_data.get('application_url', '#'),
            'subject': f"New Job Match: {job_data.get('title', 'Job')} at {job_data.get('company', 'Company')}"
        }
        
        request = NotificationRequest(
            recipient_id=candidate_id,
            recipient_type="candidate",
            template_name="job_match",
            channels=channels,
            context_data=context
        )
        
        return await self.send_notification(request)
    
    async def send_welcome_notification(
        self, 
        candidate_id: int, 
        candidate_name: str,
        channels: List[NotificationChannel]
    ) -> List[Dict[str, Any]]:
        """Send welcome notification to new candidate."""
        
        context = {
            'candidate_name': candidate_name,
            'subject': f"Welcome to JobPay, {candidate_name}!"
        }
        
        request = NotificationRequest(
            recipient_id=candidate_id,
            recipient_type="candidate",
            template_name="welcome_candidate",
            channels=channels,
            context_data=context
        )
        
        return await self.send_notification(request)
    
    async def send_job_posted_notification(
        self, 
        employer_id: int, 
        employer_name: str,
        job_title: str,
        channels: List[NotificationChannel]
    ) -> List[Dict[str, Any]]:
        """Send job posted notification to employer."""
        
        context = {
            'employer_name': employer_name,
            'job_title': job_title,
            'subject': f"Job Posted: {job_title}"
        }
        
        request = NotificationRequest(
            recipient_id=employer_id,
            recipient_type="employer",
            template_name="job_posted",
            channels=channels,
            context_data=context
        )
        
        return await self.send_notification(request)
    
    def _format_salary_range(self, job_data: Dict[str, Any]) -> str:
        """Format salary range for display."""
        salary_min = job_data.get('salary_min')
        salary_max = job_data.get('salary_max')
        currency = job_data.get('currency', 'USD')
        
        if salary_min and salary_max:
            return f"{currency} {salary_min:,.0f} - {salary_max:,.0f}"
        elif salary_min:
            return f"{currency} {salary_min:,.0f}+"
        elif salary_max:
            return f"Up to {currency} {salary_max:,.0f}"
        else:
            return "Salary not specified"
