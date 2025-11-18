import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, config):
        self.config = config
    
    def send_sms(self, message):
        """Send SMS notification to owner"""
        logger.info(f"📱 Sending SMS: {message}")
        
        try:
            from twilio.rest import Client
            client = Client(
                self.config.TWILIO_ACCOUNT_SID,
                self.config.TWILIO_AUTH_TOKEN
            )
            
            client.messages.create(
                body=message,
                from_=self.config.TWILIO_PHONE,
                to=self.config.OWNER_PHONE
            )
            
            logger.info("✅ SMS sent")
        except Exception as e:
            logger.error(f"❌ SMS failed: {e}")
    
    def send_email(self, subject, body):
        """Send email notification"""
        logger.info(f"📧 Sending email: {subject}")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = 'reservations@seahorseinn.com'
            msg['To'] = self.config.OWNER_EMAIL
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('YOUR_EMAIL@gmail.com', 'YOUR_APP_PASSWORD')
                server.send_message(msg)
            
            logger.info("✅ Email sent")
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")