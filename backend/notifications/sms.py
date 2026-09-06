"""
SMS notification service.
Sends OTP and alert SMS messages.
"""
import structlog
from backend.utils.config import settings

log = structlog.get_logger()


async def send_otp_sms(mobile_number: str, otp: str) -> bool:
    """
    Send OTP via SMS.
    In draft mode, logs the OTP instead of sending.
    In production, integrates with configured SMS provider.
    """
    if not settings.NOTIFICATION_SMS_ENABLED or settings.ENVIRONMENT != "production":
        # log.info("SMS (draft mode — not sent)", mobile=mobile_number[-4:], otp=otp)
        print(f"DRAFT OTP for {mobile_number}: {otp}")
        return True

    # Production SMS send — integrate with provider
    try:
        import httpx
        # Example: integrate with MSG91, Twilio, or similar
        # Replace this section with your SMS provider's API
        log.warning("SMS provider integration not yet configured for production")
        return False
    except Exception as e:
        log.error("SMS send failed", error=str(e))
        return False


async def send_alert_sms(mobile_number: str, message: str) -> bool:
    """Send an alert SMS to admin/officer."""
    if not settings.NOTIFICATION_SMS_ENABLED:
        log.info("Alert SMS (disabled)", mobile=mobile_number[-4:], message=message[:50])
        return True

    try:
        log.info("Sending alert SMS", mobile=mobile_number[-4:])
        # TODO: Integrate with production SMS provider
        return True
    except Exception as e:
        log.error("Alert SMS failed", error=str(e))
        return False
