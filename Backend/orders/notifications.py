import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(to_number, message):
    try:
        # Initialize Africa's Talking SDK
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        sms = africastalking.SMS
        response = sms.send(message, [to_number])
        logger.info(f"SMS sent successfully to {to_number}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
        raise