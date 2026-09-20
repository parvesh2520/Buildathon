"""
Inbound Message Route
========================
POST /api/inbound/message
GET  /api/inbound/threads
POST /api/inbound/manual-reply

Receives prospect replies from any channel, lists conversation threads,
and allows operators to send manual replies via email/SMS.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.conversation import handle_inbound_message

logger = logging.getLogger("sdr.routes.inbound")

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class InboundMessageRequest(BaseModel):
    """
    Payload sent to /api/inbound/message when a prospect replies.

    Fields:
        message_id: Stable unique ID for this reply (idempotency key).
                    If omitted, a UUID v4 is generated.
        prospect_id: Supabase UUID of the prospect.
        campaign_id: Supabase UUID of the campaign.
        channel: Reply channel — EMAIL | SMS | LINKEDIN | PHONE.
        prospect_message: The raw text of the prospect's reply.
        to_address: Phone / email / LinkedIn URL to reply back on.
        subject: Email subject line (only relevant for EMAIL channel).
        prospect_info: Optional extra metadata (name, company, title, etc.)
                       forwarded as-is to the Conversation Agent for context.
    """
    message_id: Optional[str] = Field(default=None, description="Idempotency key — omit to auto-generate")
    prospect_id: str = Field(..., description="Supabase UUID of the prospect")
    campaign_id: str = Field(..., description="Supabase UUID of the campaign")
    channel: str = Field(..., description="EMAIL | SMS | LINKEDIN | PHONE")
    prospect_message: str = Field(..., description="Raw text of the prospect's reply")
    to_address: str = Field(..., description="Reply-back address (email / phone / linkedin URL)")
    subject: Optional[str] = Field(default=None, description="Email subject (EMAIL channel only)")
    prospect_info: Optional[Dict[str, Any]] = Field(default=None, description="Extra prospect metadata")


class InboundMessageResponse(BaseModel):
    message_id: str
    prospect_id: str
    campaign_id: str
    action: str
    agent_decision: Dict[str, Any]
    execution_result: Dict[str, Any]
    processed_at: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/message",
    response_model=InboundMessageResponse,
    summary="Handle inbound prospect reply",
    description=(
        "Receives a prospect reply, calls the DronaHQ Conversation Agent, "
        "and executes the resulting action (REPLY, FOLLOW_UP, ESCALATE_HUMAN, UNSUBSCRIBE, CLOSE). "
        "Idempotent — submit the same message_id multiple times safely."
    ),
)
async def inbound_message(payload: InboundMessageRequest):
    """
    Main inbound handler. Called by:
    - Webhooks from email / SMS providers when a prospect replies.
    - DronaHQ automations that detect inbound activity.
    - Manual triggers during testing.
    """
    # Auto-generate message_id if not provided
    message_id = (payload.message_id or "").strip() or str(uuid.uuid4())

    # Validate channel
    channel_upper = (payload.channel or "").strip().upper()
    valid_channels = {"EMAIL", "SMS", "LINKEDIN", "PHONE"}
    if channel_upper not in valid_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel '{payload.channel}'. Must be one of: {sorted(valid_channels)}",
        )

    # Validate required fields
    if not payload.prospect_id or not payload.prospect_id.strip():
        raise HTTPException(status_code=400, detail="prospect_id is required")
    if not payload.campaign_id or not payload.campaign_id.strip():
        raise HTTPException(status_code=400, detail="campaign_id is required")
    if not payload.prospect_message or not payload.prospect_message.strip():
        raise HTTPException(status_code=400, detail="prospect_message cannot be empty")
    if not payload.to_address or not payload.to_address.strip():
        raise HTTPException(status_code=400, detail="to_address is required")

    logger.info(
        f"[INBOUND] Received {channel_upper} reply from prospect {payload.prospect_id} "
        f"(campaign: {payload.campaign_id}, message_id: {message_id})"
    )

    try:
        result = await handle_inbound_message(
            message_id=message_id,
            prospect_id=payload.prospect_id.strip(),
            campaign_id=payload.campaign_id.strip(),
            channel=channel_upper,
            prospect_message=payload.prospect_message.strip(),
            to_address=payload.to_address.strip(),
            subject=payload.subject,
            prospect_info=payload.prospect_info,
        )
    except Exception as e:
        logger.error(f"[INBOUND] Unhandled error processing message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error processing inbound message: {str(e)}")

    return InboundMessageResponse(**result)


# ---------------------------------------------------------------------------
# Health / info endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    summary="Inbound handler status",
    tags=["Inbound"],
)
def inbound_status():
    """Returns configuration status for the inbound conversation pipeline."""
    from app.config import (
        DRONAHQ_CONVERSATION_AGENT_URL,
        DRONAHQ_CONVERSATION_AGENT_ID,
        GMAIL_POLL_INTERVAL_SECONDS,
        SMTP_USERNAME,
    )
    return {
        "status": "ok",
        "conversation_agent_configured": bool(DRONAHQ_CONVERSATION_AGENT_URL),
        "conversation_agent_id": DRONAHQ_CONVERSATION_AGENT_ID or None,
        "supported_channels": ["EMAIL", "SMS", "LINKEDIN", "PHONE"],
        "supported_actions": ["REPLY", "FOLLOW_UP", "ESCALATE_HUMAN", "UNSUBSCRIBE", "CLOSE"],
        "gmail_poll_interval_seconds": GMAIL_POLL_INTERVAL_SECONDS,
        "gmail_poll_interval_hours": round(GMAIL_POLL_INTERVAL_SECONDS / 3600, 1) if GMAIL_POLL_INTERVAL_SECONDS else 0,
        "gmail_poller_active": GMAIL_POLL_INTERVAL_SECONDS > 0 and bool(SMTP_USERNAME),
        "gmail_account": SMTP_USERNAME or "not configured",
    }


# ---------------------------------------------------------------------------
# Gmail IMAP poll trigger (manual or called by scheduler)
# ---------------------------------------------------------------------------

@router.post(
    "/gmail/poll",
    summary="Trigger a Gmail IMAP poll for new reply emails",
    tags=["Inbound"],
    description=(
        "Connects to Gmail via IMAP, finds UNSEEN emails from known prospects, "
        "and routes each reply through the Conversation Agent. "
        "Safe to call multiple times — uses per-email idempotency via Message-ID header. "
        "The backend also calls this automatically every GMAIL_POLL_INTERVAL_SECONDS (currently 2h)."
    ),
)
async def trigger_gmail_poll():
    """
    Manually trigger a Gmail reply poll cycle.
    Returns a summary of how many replies were processed.
    """
    from app.services.gmail_poller import poll_gmail_replies
    result = await poll_gmail_replies()
    return result


# ---------------------------------------------------------------------------
# Conversation threads listing
# ---------------------------------------------------------------------------

@router.get(
    "/threads",
    summary="List all prospect conversation threads",
    tags=["Inbound"],
)
def get_conversation_threads():
    """
    Returns all prospects that have had outreach activity, along with their
    full message timeline (outbound AI messages + inbound prospect replies).
    Used by the Inbox UI.
    """
    from app.models.prospect import get_all_prospects
    from app.services.supabase_db import sb_get_outreach_messages, sb_get_conversations

    prospects = get_all_prospects()
    active_statuses = {"SENT", "CONTACTED", "REPLIED", "REVIEW", "MEETING", "COMPLETED", "FAILED"}

    threads = []
    for prospect in prospects:
        status_upper = (prospect.status or "DISCOVERED").upper()
        if status_upper not in active_statuses:
            continue

        # Outbound messages (sent by SDR / AI)
        outbound: List[Dict] = sb_get_outreach_messages(prospect_id=prospect.id) or []
        # Inbound conversations (prospect replies tracked in conversations table)
        inbound: List[Dict] = sb_get_conversations(prospect_id=prospect.id) or []

        messages: List[Dict[str, Any]] = []

        for msg in outbound:
            messages.append({
                "id": msg.get("id") or str(uuid.uuid4()),
                "direction": "outbound",
                "content": msg.get("content") or msg.get("message") or "",
                "subject": msg.get("subject"),
                "channel": (msg.get("channel") or prospect.channel or "EMAIL").upper(),
                "status": msg.get("status", "SENT"),
                "sender": "AI Agent",
                "created_at": msg.get("sent_at") or msg.get("created_at") or "",
            })

        for conv in inbound:
            summary = conv.get("summary") or ""
            # Strip leading "Inbound: " prefix if present
            if summary.startswith("Inbound: "):
                summary = summary[len("Inbound: "):]
            messages.append({
                "id": conv.get("id") or str(uuid.uuid4()),
                "direction": "inbound",
                "content": summary,
                "channel": (conv.get("channel") or prospect.channel or "EMAIL").upper(),
                "status": conv.get("status", "ACTIVE"),
                "sentiment": conv.get("sentiment"),
                "sender": prospect.name,
                "created_at": conv.get("last_message_at") or conv.get("created_at") or "",
            })

        # Sort chronologically
        messages.sort(key=lambda m: m.get("created_at") or "")

        last_at = messages[-1]["created_at"] if messages else None

        threads.append({
            "prospect_id": prospect.id,
            "prospect_name": prospect.name,
            "prospect_email": prospect.email,
            "prospect_phone": prospect.phone,
            "prospect_title": prospect.title,
            "prospect_company": prospect.company,
            "prospect_status": prospect.status,
            "prospect_channel": (prospect.channel or "EMAIL").upper(),
            "campaign_id": prospect.campaign_id or prospect.campaignId,
            "messages": messages,
            "message_count": len(messages),
            "last_message_at": last_at,
        })

    # Most recently active threads first
    threads.sort(key=lambda t: t.get("last_message_at") or "", reverse=True)
    return threads


# ---------------------------------------------------------------------------
# Manual reply — operator sends a message directly without AI agent
# ---------------------------------------------------------------------------

class ManualReplyRequest(BaseModel):
    prospect_id: str = Field(..., description="ID of the prospect to reply to")
    message: str = Field(..., description="Message body to send")
    subject: Optional[str] = Field(default=None, description="Subject line (EMAIL only)")
    channel: Optional[str] = Field(default=None, description="Override channel (EMAIL|SMS). Defaults to prospect's channel.")


@router.post(
    "/manual-reply",
    summary="Send a manual operator reply to a prospect",
    tags=["Inbound"],
)
async def manual_reply(payload: ManualReplyRequest):
    """
    Operator sends a reply directly to a prospect via their channel (email/SMS).
    Bypasses the AI Conversation Agent — sends immediately and logs to Supabase.
    """
    from app.models.prospect import get_prospect
    from app.services.email import send_email
    from app.services.sms import send_sms
    from app.services.supabase_db import sb_insert_outreach_message

    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message body cannot be empty")

    prospect = get_prospect(payload.prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    channel = (payload.channel or prospect.channel or "EMAIL").strip().upper()
    if channel not in ("EMAIL", "SMS", "LINKEDIN", "PHONE"):
        raise HTTPException(status_code=400, detail=f"Unsupported channel: {channel}")

    execution_id = str(uuid.uuid4())
    campaign_id = prospect.campaign_id or prospect.campaignId or ""

    logger.info(
        f"[MANUAL REPLY] Sending {channel} to prospect {prospect.id} ({prospect.name})"
    )

    if channel == "EMAIL":
        if not prospect.email:
            raise HTTPException(status_code=400, detail="Prospect has no email address on file")
        result = await send_email(
            to_email=prospect.email,
            subject=payload.subject or "Following up",
            content=payload.message.strip(),
            prospect_id=prospect.id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )
        recipient = prospect.email

    elif channel == "SMS":
        if not prospect.phone:
            raise HTTPException(status_code=400, detail="Prospect has no phone number on file")
        result = await send_sms(
            to_phone=prospect.phone,
            content=payload.message.strip(),
            prospect_id=prospect.id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )
        recipient = prospect.phone

    else:
        raise HTTPException(status_code=400, detail=f"Channel {channel} is not directly sendable — use email or SMS")

    # Persist outbound message to Supabase
    try:
        sb_insert_outreach_message(
            prospect_id=prospect.id,
            channel=channel,
            recipient=recipient,
            content=payload.message.strip(),
            subject=payload.subject,
            execution_id=execution_id,
            campaign_id=campaign_id,
            status=result.get("status", "SENT"),
            provider=result.get("provider"),
            provider_message_id=result.get("provider_message_id"),
            error=result.get("error"),
        )
    except Exception as e:
        logger.warning(f"[MANUAL REPLY] Supabase persist failed: {str(e)}")

    return {
        "status": result.get("status", "SENT"),
        "channel": channel,
        "recipient": recipient,
        "prospect_id": prospect.id,
        "prospect_name": prospect.name,
        "message_preview": payload.message.strip()[:120],
        "execution_id": execution_id,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "provider_result": result,
    }
