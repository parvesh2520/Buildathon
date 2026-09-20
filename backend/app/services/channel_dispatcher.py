import logging
from typing import Any, Dict, Optional
from app.services.email import send_email
from app.services.sms import send_sms
from app.services.linkedin import send_linkedin
from app.services.voice import initiate_voice_call

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
    - PHONE    -> initiate_voice_call (bridges to SDR Voice Script Agent)
    """
    channel_norm = (recommended_channel or "").strip().upper()
    prospect_id = getattr(prospect, "id", None) or (prospect.get("id") if isinstance(prospect, dict) else "")
    campaign_id = getattr(campaign, "id", None) or (campaign.get("id") if isinstance(campaign, dict) else "")

    p_email = getattr(prospect, "email", None) or (prospect.get("email") if isinstance(prospect, dict) else "")
    p_phone = getattr(prospect, "phone", None) or (prospect.get("phone") if isinstance(prospect, dict) else "")
    p_linkedin = getattr(prospect, "linkedin_url", None) or getattr(prospect, "linkedinUrl", None) or (
        prospect.get("linkedin_url") or prospect.get("linkedinUrl") if isinstance(prospect, dict) else ""
    )

    content = personalisation.get("content", "")
    subject_line = personalisation.get("subject_line") or personalisation.get("subject") or "Introduction"

    logger.info(
        f"[CHANNEL DISPATCHER] Dispatching outreach via '{channel_norm}' for prospect {prospect_id} (campaign: {campaign_id})"
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
        p_dict = prospect.model_dump() if hasattr(prospect, "model_dump") else (prospect if isinstance(prospect, dict) else {})
        c_dict = campaign.model_dump() if hasattr(campaign, "model_dump") else (campaign if isinstance(campaign, dict) else {})
        return await initiate_voice_call(
            phone=p_phone or "",
            prospect=p_dict,
            campaign=c_dict,
            strategy=strategy or {},
            execution_id=execution_id or "",
            research=research,
            icp_result=icp_result,
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
