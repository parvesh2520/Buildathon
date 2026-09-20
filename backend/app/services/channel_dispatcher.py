import logging
from typing import Any, Dict, Optional
from app.services.email import send_email
from app.services.sms import send_sms
from app.services.linkedin import send_linkedin
from app.services.voice import initiate_voice_call
from app.services.dronahq import clean_agent_text

logger = logging.getLogger("sdr.dispatcher")


async def dispatch_outreach(
    recommended_channel: str,
    prospect: Any,
    personalisation: Dict[str, Any],
    strategy: Optional[Dict[str, Any]] = None,
    campaign: Optional[Any] = None,
    execution_id: Optional[str] = None,
    research: Optional[Dict[str, Any]] = None,
    icp_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Central Modular Channel Dispatcher.

    The backend does NOT independently decide which channel is best.
    DronaHQ's Outreach Strategy Agent already made that decision (recommended_channel).

    Routes outreach execution to the appropriate service:
    - EMAIL    -> send_email
    - SMS      -> send_sms
    - LINKEDIN -> send_linkedin
    - PHONE    -> initiate_voice_call  (Twilio Programmable Voice)
    """
    channel_norm = (recommended_channel or "").strip().upper()

    prospect_id = (
        getattr(prospect, "id", None)
        or (prospect.get("id") if isinstance(prospect, dict) else "")
        or ""
    )
    campaign_id = (
        getattr(campaign, "id", None)
        or (campaign.get("id") if isinstance(campaign, dict) else "")
        or ""
    )

    p_email = (
        getattr(prospect, "email", None)
        or (prospect.get("email") if isinstance(prospect, dict) else "")
        or ""
    )
    p_phone = (
        getattr(prospect, "phone", None)
        or (prospect.get("phone") if isinstance(prospect, dict) else "")
        or ""
    )
    p_linkedin = (
        getattr(prospect, "linkedin_url", None)
        or getattr(prospect, "linkedinUrl", None)
        or (prospect.get("linkedin_url") or prospect.get("linkedinUrl") if isinstance(prospect, dict) else "")
        or ""
    )

    raw_content = personalisation.get("content") or personalisation.get("message") or personalisation.get("body") or ""
    raw_subject = (
        personalisation.get("subject_line")
        or personalisation.get("subject")
        or (strategy.get("angle") if strategy else None)
        or "Introduction"
    )
    content = clean_agent_text(raw_content, ["message", "content", "body", "email_body"])
    subject_line = clean_agent_text(raw_subject, ["subject_line", "subject"]) or "Introduction"

    logger.info(
        f"[CHANNEL DISPATCHER] Dispatching outreach via '{channel_norm}' "
        f"for prospect {prospect_id} (campaign: {campaign_id})"
    )

    if channel_norm == "EMAIL":
        return await send_email(
            to_email=p_email,
            subject=subject_line,
            content=content,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )

    elif channel_norm == "SMS":
        return await send_sms(
            to_phone=p_phone,
            content=content,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )

    elif channel_norm == "LINKEDIN":
        return await send_linkedin(
            linkedin_url=p_linkedin,
            content=content,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
        )

    elif channel_norm in ["PHONE", "VOICE"]:
        # Pass the ACTUAL prospect phone — never hardcode destination
        return await initiate_voice_call(
            prospect_phone=p_phone or "",
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            execution_id=execution_id or "",
        )

    else:
        logger.error(f"[CHANNEL DISPATCHER] Unsupported channel '{recommended_channel}'")
        return {
            "channel": recommended_channel,
            "status": "INVALID_CHANNEL",
            "provider_message_id": None,
            "recipient": None,
            "error": f"Unsupported outreach channel: '{recommended_channel}'",
        }
