"""
Twilio SMS Inbound Webhook
============================
POST /api/inbound/twilio/sms

Twilio calls this endpoint automatically when someone texts your Twilio number.
Accepts Twilio's native form-encoded webhook payload, looks up the prospect
by phone number, and routes the reply through the Conversation Agent pipeline.

Setup in Twilio Console:
  Phone Numbers → Your Number → Messaging → Webhook URL:
  https://your-ngrok-url.ngrok.io/api/inbound/twilio/sms
  Method: HTTP POST
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Form, Response
from fastapi.responses import PlainTextResponse

from app.services.supabase_db import _request

logger = logging.getLogger("sdr.routes.inbound_twilio")

router = APIRouter(prefix="/api/inbound/twilio", tags=["Inbound - Twilio"])

# Twilio expects a TwiML XML response — even an empty one
_TWIML_EMPTY = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
_TWIML_CT = "application/xml"


def _find_prospect_by_phone(phone: str):
    """
    Look up a prospect by their phone number.
    Tries exact match first, then strips leading '+' as fallback.
    """
    # Normalise: strip whitespace
    phone = (phone or "").strip()

    # Try exact match
    res = _request(f"prospects?phone=eq.{phone}&select=*&limit=1")
    if isinstance(res, list) and len(res) > 0:
        return res[0]

    # Try without leading '+'
    if phone.startswith("+"):
        phone_no_plus = phone[1:]
        res = _request(f"prospects?phone=eq.{phone_no_plus}&select=*&limit=1")
        if isinstance(res, list) and len(res) > 0:
            return res[0]

    return None


def _find_campaign_for_prospect(prospect_id: str) -> Optional[str]:
    """Find the most recent campaign this prospect was contacted in."""
    res = _request(
        f"outreach_messages?prospect_id=eq.{prospect_id}"
        f"&select=campaign_id&order=created_at.desc&limit=1"
    )
    if isinstance(res, list) and len(res) > 0:
        return res[0].get("campaign_id")
    return None


@router.post(
    "/sms",
    response_class=PlainTextResponse,
    summary="Twilio inbound SMS webhook",
    description=(
        "Twilio calls this endpoint when a prospect texts your number back. "
        "Configure this URL in Twilio Console → Phone Numbers → Messaging → Webhook URL. "
        "Returns empty TwiML so Twilio doesn't auto-reply."
    ),
)
async def twilio_sms_inbound(
    From: str = Form(..., description="Sender's phone number (E.164 format, e.g. +15551234567)"),
    Body: str = Form(..., description="Text content of the SMS"),
    MessageSid: str = Form(..., description="Twilio message SID (used as idempotency key)"),
    To: Optional[str] = Form(default=None, description="Your Twilio phone number"),
    NumMedia: Optional[str] = Form(default="0"),
):
    """
    Handle inbound SMS reply from Twilio.

    Twilio sends form-encoded POST with fields: From, Body, MessageSid, To, etc.
    We look up the prospect, route to the Conversation Agent, and return empty TwiML.
    """
    from_phone = (From or "").strip()
    message_body = (Body or "").strip()
    message_sid = (MessageSid or "").strip()

    logger.info(
        f"[TWILIO SMS INBOUND] From={from_phone} | SID={message_sid} | "
        f"Body='{message_body[:80]}{'...' if len(message_body) > 80 else ''}'"
    )

    if not from_phone or not message_body:
        logger.warning("[TWILIO SMS INBOUND] Empty From or Body — ignoring.")
        return PlainTextResponse(_TWIML_EMPTY, media_type=_TWIML_CT)

    # Look up prospect by phone
    prospect = _find_prospect_by_phone(from_phone)
    if not prospect:
        logger.warning(
            f"[TWILIO SMS INBOUND] No prospect found for phone {from_phone}. "
            f"Message ignored (not a known SDR contact)."
        )
        return PlainTextResponse(_TWIML_EMPTY, media_type=_TWIML_CT)

    prospect_id = prospect.get("id", "")
    campaign_id = _find_campaign_for_prospect(prospect_id) or ""

    logger.info(
        f"[TWILIO SMS INBOUND] Matched prospect {prospect_id} "
        f"(campaign: {campaign_id or 'unknown'}) — routing to Conversation Agent."
    )

    try:
        from app.services.conversation import handle_inbound_message

        result = await handle_inbound_message(
            message_id=message_sid,          # Twilio SID = idempotency key
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            channel="SMS",
            prospect_message=message_body,
            to_address=from_phone,           # Reply back to this number
            prospect_info={
                "name": prospect.get("name"),
                "company": prospect.get("company"),
                "phone": from_phone,
            },
        )

        action = result.get("action", "UNKNOWN")
        logger.info(
            f"[TWILIO SMS INBOUND] Conversation Agent action for prospect "
            f"{prospect_id}: {action}"
        )

    except Exception as e:
        logger.error(
            f"[TWILIO SMS INBOUND] Error processing reply from {from_phone}: {str(e)}"
        )

    # Always return empty TwiML — we handle replies ourselves via Conversation Agent
    return PlainTextResponse(_TWIML_EMPTY, media_type=_TWIML_CT)


@router.get(
    "/status",
    summary="Twilio inbound webhook status",
)
def twilio_inbound_status():
    """Returns the webhook URL to configure in Twilio Console."""
    from app.config import BACKEND_BASE_URL, TWILIO_PHONE_NUMBER
    webhook_url = f"{BACKEND_BASE_URL}/api/inbound/twilio/sms"
    return {
        "status": "ok",
        "twilio_phone_number": TWILIO_PHONE_NUMBER or "not configured",
        "webhook_url_to_configure_in_twilio": webhook_url,
        "instructions": (
            "In Twilio Console → Phone Numbers → Your Number → "
            "Messaging → Webhook URL, paste the webhook_url above. "
            "Use HTTP POST. If running locally, use ngrok to expose the backend first."
        ),
    }
