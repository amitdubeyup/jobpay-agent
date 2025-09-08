from twilio.rest import Client
from typing import Dict, Any, Optional
import logging

from app.core.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class SMSProvider(NotificationProvider):
    """SMS notification provider using Twilio."""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    async def send(
        self,
        recipient: str,
        subject: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS notification."""
        try:
            # For SMS, we combine subject and content
            message_body = f"{subject}\n\n{content}" if subject else content
            
            # Send SMS
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=recipient
            )
            
            logger.info(f"SMS sent successfully to {recipient}, SID: {message.sid}")
            
            return {
                'success': True,
                'provider_message_id': message.sid,
                'provider_response': {
                    'sid': message.sid,
                    'status': message.status,
                    'to': message.to,
                    'from': message.from_
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'provider_response': {'error': str(e)}
            }
    
    def get_provider_name(self) -> str:
        return "twilio_sms"


class WhatsAppProvider(NotificationProvider):
    """WhatsApp notification provider using Twilio."""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
    
    async def send(
        self,
        recipient: str,
        subject: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp notification."""
        try:
            # For WhatsApp, format recipient number
            if not recipient.startswith('whatsapp:'):
                recipient = f"whatsapp:{recipient}"
            
            message_body = f"{subject}\n\n{content}" if subject else content
            
            # Send WhatsApp message
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=recipient
            )
            
            logger.info(f"WhatsApp sent successfully to {recipient}, SID: {message.sid}")
            
            return {
                'success': True,
                'provider_message_id': message.sid,
                'provider_response': {
                    'sid': message.sid,
                    'status': message.status,
                    'to': message.to,
                    'from': message.from_
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {recipient}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'provider_response': {'error': str(e)}
            }
