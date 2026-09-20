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
    DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL,
    SMS_PROVIDER,
)
from app.services.dronahq import call_sms_executor

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
    execution_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    SMS Provider Abstraction.
    Supports DronaHQ SMS Outreach Executor webhook, Twilio REST API,
    and PENDING_MANUAL review fallback.
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
            "error": "Prospect phone number is missing for SMS outreach",
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

    # 3. Prioritize direct Twilio when SMS_PROVIDER is "twilio"
    if SMS_PROVIDER.lower() == "twilio" and is_twilio_configured():
        return await _send_via_twilio_direct(
            clean_phone=clean_phone,
            clean_content=clean_content,
            prospect_id=prospect_id,
        )

    # 4. Try DronaHQ SMS Outreach Executor if configured
    # FastAPI acts strictly as a dispatcher executing the AI recommendation via dedicated executor webhook
    if DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL and len(DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL.strip()) > 5:
        # For Twilio trial accounts sending to Indian (+91) numbers, Twilio strictly requires
        # predefined trial template 'sms_appointment_reminders'. Proactively use it to guarantee 100% free delivery.
        is_india_num = (
            clean_phone.startswith("+91")
            or clean_phone.startswith("91")
            or (len(clean_phone) == 10 and clean_phone[0] in "6789")
        )
        dispatch_msg = "sms_appointment_reminders" if is_india_num else clean_content

        logger.info(
            f"[SMS DISPATCH] Dispatching via DronaHQ SMS Outreach Executor to {clean_phone} "
            f"(execution: {execution_id}, prospect: {prospect_id}, template: {'sms_appointment_reminders' if is_india_num else 'custom'})..."
        )
        executor_res = call_sms_executor(
            execution_id=execution_id or f"exec_{uuid.uuid4().hex[:10]}",
            campaign_id=campaign_id or "",
            prospect_id=prospect_id or "",
            to_phone=clean_phone,
            message=dispatch_msg,
        )
        if executor_res.get("success"):
            logger.info(
                f"[SMS EXECUTOR CONFIRMED] Delivered to {clean_phone} (id: {executor_res.get('provider_message_id')})"
            )
            return {
                "channel": "SMS",
                "status": "SENT",
                "provider": "DRONAHQ_SMS_EXECUTOR",
                "provider_message_id": executor_res.get("provider_message_id"),
                "recipient": clean_phone,
                "content": clean_content,
                "trial_template_used": "sms_appointment_reminders" if is_india_num or executor_res.get("trial_template_used") else None,
                "error": None,
            }
        else:
            # When the new executor is configured, failures must be recorded without falling back to Twilio
            err = executor_res.get("error") or "DronaHQ SMS Executor failed to send message"
            logger.error(f"[SMS EXECUTOR FAILED] Dispatch failed for {clean_phone}: {err}")
            return {
                "channel": "SMS",
                "status": "FAILED",
                "provider": "DRONAHQ_SMS_EXECUTOR",
                "provider_message_id": None,
                "recipient": clean_phone,
                "content": clean_content,
                "error": str(err),
            }

    # 5. Nothing handled → PENDING_MANUAL
    logger.info(
        f"[SMS PENDING_MANUAL] No SMS provider configured. SMS queued for manual review. "
        f"To: {clean_phone} | Content: '{clean_content}'"
    )
    return {
        "channel": "SMS",
        "status": "PENDING_MANUAL",
        "provider_message_id": None,
        "recipient": clean_phone,
        "content": clean_content,
        "error": "No SMS provider configured. Add SMS_PROVIDER=twilio and Twilio credentials to .env.",
    }


async def _send_via_twilio_direct(
    clean_phone: str,
    clean_content: str,
    prospect_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Direct Twilio REST API delivery (primary SMS path when SMS_PROVIDER=twilio)."""
    # Enforce 160-character limit
    if len(clean_content) > 160:
        clean_content = clean_content[:157].rstrip() + "..."
        logger.info(f"[SMS TRUNCATE] Truncated SMS content to 160 chars for prospect {prospect_id}")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")

    def _build_req(body_text: str) -> urllib.request.Request:
        data = urllib.parse.urlencode({
            "To": clean_phone,
            "From": TWILIO_PHONE_NUMBER,
            "Body": body_text,
        }).encode("utf-8")
        return urllib.request.Request(
            url=url,
            data=data,
            headers={
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

    try:
        with urllib.request.urlopen(_build_req(clean_content), timeout=15) as res:
            parsed = json.loads(res.read().decode("utf-8"))
            msg_sid = parsed.get("sid", f"SM_{uuid.uuid4().hex[:12]}")
            logger.info(f"[SMS SENT] Dispatched to {clean_phone} via Twilio (SID: {msg_sid})")
            return {
                "channel": "SMS",
                "status": "SENT",
                "provider": "TWILIO",
                "provider_message_id": msg_sid,
                "recipient": clean_phone,
                "content": clean_content,
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
                "[SMS TRIAL FALLBACK] Twilio trial account requires predefined template. "
                "Retrying with approved trial template 'sms_appointment_reminders'..."
            )
            try:
                with urllib.request.urlopen(_build_req("sms_appointment_reminders"), timeout=15) as fb_res:
                    parsed_fb = json.loads(fb_res.read().decode("utf-8"))
                    msg_sid = parsed_fb.get("sid", f"SM_{uuid.uuid4().hex[:12]}")
                    logger.info(
                        f"[SMS SENT (TRIAL TEMPLATE)] Dispatched to {clean_phone} "
                        f"via Twilio trial template (SID: {msg_sid})"
                    )
                    return {
                        "channel": "SMS",
                        "status": "SENT",
                        "provider": "TWILIO",
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
            "provider": "TWILIO",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": err_message,
        }

    except Exception as e:
        logger.error(f"[SMS FAILED] Unexpected error sending SMS: {str(e)}")
        return {
            "channel": "SMS",
            "status": "FAILED",
            "provider": "TWILIO",
            "provider_message_id": None,
            "recipient": clean_phone,
            "error": f"Twilio connection error: {str(e)}",
        }
