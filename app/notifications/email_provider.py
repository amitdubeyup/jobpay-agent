import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging

from app.core.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailProvider(NotificationProvider):
    """Email notification provider using SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send(
        self,
        recipient: str,
        subject: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email notification."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient
            
            # Add HTML content
            html_part = MIMEText(content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            
            return {
                'success': True,
                'provider_message_id': None,  # SMTP doesn't provide message ID
                'provider_response': {'status': 'sent'}
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'provider_response': {'error': str(e)}
            }
    
    def get_provider_name(self) -> str:
        return "smtp_email"
