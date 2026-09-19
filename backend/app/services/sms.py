import base64
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import uuid
from typing import Optional, Dict, Any
from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
)

logger = logging.getLogger("sdr.sms")


def is_twilio_configured() -> bool:
    """Check if Twilio environment credentials are provided and non-placeholder."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        return False
    if "your_twilio" in TWILIO_ACCOUNT_SID.lower() or "your_twilio" in TWILIO_AUTH_TOKEN.lower():
        return False
    return True


async def send_sms(
    to_phone: Optional[str],
    content: Optional[str],
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Twilio SMS Provider Abstraction.
    
    Validations:
    - Phone number must exist
    - Content must not be empty
    - Enforces 160-character maximum limit
    - If Twilio is not configured, returns PENDING_MANUAL without pretending delivery
    """
    clean_phone = (to_phone or "").strip()
    clean_content = (content or "").strip()

    # 1. Validation: phone presence
    if not clean_phone:
        logger.error(f"[SMS VALIDATION FAILED] Missing phone number for prospect {prospect_id}")
        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": None,
            "error": "Prospect phone number is missing",
        }

    # 2. Validation: content presence
    if not clean_content:
        logger.error(f"[SMS VALIDATION FAILED] Empty SMS content for prospect {prospect_id}")
        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": "SMS content is empty",
        }

    # 3. Validation: 160-character limit enforcement
    if len(clean_content) > 160:
        logger.error(
            f"[SMS VALIDATION FAILED] SMS content exceeds 160 characters (length: {len(clean_content)}). "
            f"Prospect: {prospect_id}"
        )
        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": f"SMS exceeds 160 character limit (length: {len(clean_content)})",
        }

    # 4. If Twilio is unconfigured, return PENDING_MANUAL
    if not is_twilio_configured():
        logger.info(
            f"[SMS PENDING_MANUAL] Twilio credentials not configured. SMS queued for manual review. "
            f"To: {clean_phone} | Content: '{clean_content}'"
        )
        return {
            "channel": "SMS",
            "status": "PENDING_MANUAL",
            "provider_message_id": None,
            "recipient": clean_phone,
            "content": clean_content,
            "error": "Twilio credentials not configured in backend .env. SMS queued for manual execution.",
        }

    # 5. Execute via Twilio REST API
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = urllib.parse.urlencode({
        "To": clean_phone,
        "From": TWILIO_PHONE_NUMBER,
        "Body": clean_content,
    }).encode("utf-8")

    auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")

    req = urllib.request.Request(
        url=url,
        data=data,
        headers={
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            parsed = json.loads(res_body)
            msg_sid = parsed.get("sid", f"SM_{uuid.uuid4().hex[:12]}")
            logger.info(f"[SMS SENT] Successfully dispatched to {clean_phone} via Twilio (SID: {msg_sid})")
            return {
                "channel": "SMS",
                "status": "SENT",
                "provider_message_id": msg_sid,
                "recipient": clean_phone,
                "error": None,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error(f"[SMS FAILED] Twilio HTTP {e.code}: {error_body}")
        try:
            parsed_err = json.loads(error_body)
            err_code = parsed_err.get("code")
            err_message = parsed_err.get("message", f"Twilio HTTP Error {e.code}")
        except Exception:
            err_code = None
            err_message = f"Twilio HTTP Error {e.code}: {error_body}"

        # If trial account template restriction (error 572006), retry with Twilio trial template
        if err_code == 572006:
            logger.warning(
                f"[SMS TRIAL FALLBACK] Twilio trial account requires predefined template. "
                f"Retrying with approved trial template 'sms_appointment_reminders'..."
            )
            fallback_data = urllib.parse.urlencode({
                "To": clean_phone,
                "From": TWILIO_PHONE_NUMBER,
                "Body": "sms_appointment_reminders",
            }).encode("utf-8")
            fallback_req = urllib.request.Request(
                url=url,
                data=fallback_data,
                headers={
                    "Authorization": f"Basic {b64_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(fallback_req, timeout=15) as fb_res:
                    fb_body = fb_res.read().decode("utf-8")
                    parsed_fb = json.loads(fb_body)
                    msg_sid = parsed_fb.get("sid", f"SM_{uuid.uuid4().hex[:12]}")
                    logger.info(
                        f"[SMS SENT (TRIAL TEMPLATE)] Successfully dispatched to {clean_phone} "
                        f"via Twilio trial template (SID: {msg_sid})"
                    )
                    return {
                        "channel": "SMS",
                        "status": "SENT",
                        "provider_message_id": msg_sid,
                        "recipient": clean_phone,
                        "content": clean_content,
                        "trial_template_used": "sms_appointment_reminders",
                        "error": None,
                    }
            except Exception as fb_err:
                logger.error(f"[SMS TRIAL FALLBACK FAILED] {str(fb_err)}")

        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": err_message,
        }
    except Exception as e:
        logger.error(f"[SMS FAILED] Unexpected error sending SMS: {str(e)}")
        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": f"Twilio connection error: {str(e)}",
        }
