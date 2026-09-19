import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("sdr.linkedin")


async def send_linkedin(
    linkedin_url: Optional[str],
    content: Optional[str],
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    LinkedIn Provider Abstraction.
    
    Adheres strictly to safety rules:
    - Zero browser automation, scraping, or credential harvesting.
    - If third-party LinkedIn API is not connected, safely queues as PENDING_MANUAL
      allowing sales reps to inspect and deliver the message manually from the UI.
    """
    clean_url = (linkedin_url or "").strip()
    clean_content = (content or "").strip()

    if not clean_url:
        logger.error(f"[LINKEDIN FAILED] Missing LinkedIn URL for prospect {prospect_id}")
        return {
            "channel": "LINKEDIN",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": None,
            "error": "Prospect LinkedIn URL is missing",
        }

    if not clean_content:
        logger.error(f"[LINKEDIN FAILED] Empty LinkedIn message content for prospect {prospect_id}")
        return {
            "channel": "LINKEDIN",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_url,
            "error": "LinkedIn outreach content is empty",
        }

    logger.info(
        f"[LINKEDIN PENDING_MANUAL] Outreach message generated and queued for human/manual delivery. "
        f"Recipient: {clean_url}"
    )

    # Return PENDING_MANUAL so the UI surfaces this message ready for the sales rep to copy/send
    return {
        "channel": "LINKEDIN",
        "status": "PENDING_MANUAL",
        "recipient": clean_url,
        "content": clean_content,
        "provider_message_id": None,
        "error": None,
    }
