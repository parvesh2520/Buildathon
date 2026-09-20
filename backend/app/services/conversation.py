"""
Conversation Orchestration Service
====================================
Handles inbound prospect replies by:
  1. Identifying campaign + prospect from the incoming message.
  2. Fetching conversation history from Supabase.
  3. Calling the DronaHQ Conversation Agent.
  4. Executing the agent's returned action (REPLY, FOLLOW_UP, ESCALATE_HUMAN, UNSUBSCRIBE, CLOSE).
  5. Persisting all state back to Supabase.

IMPORTANT: This module NEVER re-implements agent logic — it only orchestrates.
           The DronaHQ Conversation Agent decides everything; this code executes it.
"""

import json
import logging
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import (
    DRONAHQ_CONVERSATION_AGENT_URL,
    DRONAHQ_CONVERSATION_AGENT_KEY,
    DRONAHQ_CONVERSATION_AGENT_ID,
    DRONAHQ_API_KEY,
)
from app.services.dronahq import unwrap_dronahq_response
from app.services.supabase_db import (
    _request,
    sb_upsert_conversation,
    sb_get_conversations,
    sb_get_outreach_messages,
    sb_insert_outreach_message,
    sb_create_follow_up,
    sb_update_prospect_status,
)

logger = logging.getLogger("sdr.conversation")

# ---------------------------------------------------------------------------
# Valid action types returned by the Conversation Agent
# ---------------------------------------------------------------------------
VALID_ACTIONS = {"REPLY", "FOLLOW_UP", "ESCALATE_HUMAN", "UNSUBSCRIBE", "CLOSE", "NO_ACTION"}


# ---------------------------------------------------------------------------
# DronaHQ Conversation Agent call
# ---------------------------------------------------------------------------

def _call_conversation_agent(
    prospect_id: str,
    campaign_id: str,
    channel: str,
    prospect_message: str,
    conversation_history: List[Dict[str, Any]],
    last_outbound_message: Optional[str],
    last_outbound_channel: Optional[str],
    prospect_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call the DronaHQ Conversation Agent with full context.
    Returns the agent's decision dict (action + payload).
    Falls back to a ESCALATE_HUMAN action if the agent is unreachable.
    """
    if not DRONAHQ_CONVERSATION_AGENT_URL:
        logger.warning(
            "[CONV AGENT] DRONAHQ_CONVERSATION_AGENT_URL not configured — "
            "defaulting to ESCALATE_HUMAN"
        )
        return {
            "action": "ESCALATE_HUMAN",
            "reason": "Conversation Agent URL not configured",
            "reply_message": None,
            "follow_up_delay_hours": None,
        }

    payload = {
        "agent_id": DRONAHQ_CONVERSATION_AGENT_ID,
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "channel": channel,
        "prospect_message": prospect_message,
        "message": prospect_message,
        "last_outbound_message": last_outbound_message,
        "last_outbound_channel": last_outbound_channel,
        "conversation_history": conversation_history,
        "prospect_info": prospect_info or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    key = DRONAHQ_CONVERSATION_AGENT_KEY or DRONAHQ_API_KEY
    if key:
        headers["api-key"] = key
        headers["x-api-key"] = key

    req = urllib.request.Request(
        url=DRONAHQ_CONVERSATION_AGENT_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
            parsed = json.loads(raw)
            # Unwrap DronaHQ output (handles nested response, markdown json fences, etc.)
            unwrapped = unwrap_dronahq_response(parsed)
            if isinstance(unwrapped, dict) and unwrapped:
                parsed = unwrapped
            elif "result" in parsed and isinstance(parsed["result"], dict):
                parsed = parsed["result"]
            elif "response" in parsed and isinstance(parsed["response"], dict):
                parsed = parsed["response"]

            logger.info(
                f"[CONV AGENT] Agent response for prospect {prospect_id}: "
                f"action={parsed.get('action')}, intent={parsed.get('intent')}"
            )
            return parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error(f"[CONV AGENT] HTTP {e.code}: {err_body}")
    except Exception as e:
        logger.error(f"[CONV AGENT] Connection error: {str(e)}")

    # Graceful degradation
    return {
        "action": "ESCALATE_HUMAN",
        "reason": "Conversation Agent unreachable — manual review required",
        "reply_message": None,
        "follow_up_delay_hours": None,
    }


# ---------------------------------------------------------------------------
# Action executors
# ---------------------------------------------------------------------------

async def _execute_reply(
    prospect_id: str,
    campaign_id: str,
    execution_id: str,
    channel: str,
    reply_message: str,
    to_address: str,
    subject: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a reply on the same channel using the existing channel services."""
    from app.services.email import send_email
    from app.services.sms import send_sms
    from app.services.linkedin import send_linkedin

    channel_upper = channel.upper()

    if channel_upper == "EMAIL":
        result = await send_email(
            to_email=to_address,
            subject=subject or "Re: Following up",
            content=reply_message,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )
    elif channel_upper == "SMS":
        result = await send_sms(
            to_phone=to_address,
            content=reply_message,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            execution_id=execution_id,
        )
    elif channel_upper == "LINKEDIN":
        result = await send_linkedin(
            linkedin_url=to_address,
            content=reply_message,
            prospect_id=prospect_id,
            campaign_id=campaign_id,
        )
    else:
        logger.warning(f"[CONV REPLY] Unsupported reply channel: {channel_upper}")
        result = {
            "channel": channel_upper,
            "status": "INVALID_CHANNEL",
            "error": f"Unsupported reply channel: {channel_upper}",
        }

    logger.info(
        f"[CONV REPLY] Reply dispatched for prospect {prospect_id} "
        f"via {channel_upper}: status={result.get('status')}"
    )
    return result


async def _execute_follow_up(
    prospect_id: str,
    campaign_id: str,
    delay_hours: Optional[int],
    channel: str,
    message: Optional[str],
    to_address: str,
) -> Dict[str, Any]:
    """Schedule a follow-up (stored in Supabase follow_ups table)."""
    delay = delay_hours or 24
    scheduled_at = datetime.now(timezone.utc).isoformat()

    record = sb_create_follow_up({
        "id": str(uuid.uuid4()),
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "channel": channel.upper(),
        "message": message or "",
        "to_address": to_address,
        "delay_hours": delay,
        "scheduled_at": scheduled_at,
        "status": "PENDING",
    })
    logger.info(
        f"[CONV FOLLOW_UP] Scheduled follow-up for prospect {prospect_id} "
        f"in {delay}h (record: {record})"
    )
    return {"action": "FOLLOW_UP", "scheduled": True, "delay_hours": delay}


def _execute_unsubscribe(prospect_id: str, campaign_id: str) -> Dict[str, Any]:
    """Mark prospect as unsubscribed in Supabase."""
    try:
        _request(
            f"prospects?id=eq.{prospect_id}",
            method="PATCH",
            data={"unsubscribed": True, "status": "UNSUBSCRIBED"},
        )
        logger.info(f"[CONV UNSUBSCRIBE] Prospect {prospect_id} marked UNSUBSCRIBED")
    except Exception as e:
        logger.error(f"[CONV UNSUBSCRIBE] Failed to mark prospect: {str(e)}")
    return {"action": "UNSUBSCRIBE", "prospect_id": prospect_id}


def _execute_close(prospect_id: str, campaign_id: str) -> Dict[str, Any]:
    """Mark conversation as closed / won."""
    try:
        _request(
            f"conversations?prospect_id=eq.{prospect_id}&campaign_id=eq.{campaign_id}",
            method="PATCH",
            data={"status": "CLOSED", "last_message_at": datetime.now(timezone.utc).isoformat()},
        )
        logger.info(f"[CONV CLOSE] Conversation closed for prospect {prospect_id}")
    except Exception as e:
        logger.error(f"[CONV CLOSE] Failed to close conversation: {str(e)}")
    return {"action": "CLOSE", "prospect_id": prospect_id}


def _execute_escalate_human(
    prospect_id: str,
    campaign_id: str,
    reason: Optional[str],
) -> Dict[str, Any]:
    """Flag conversation for human review."""
    try:
        _request(
            f"conversations?prospect_id=eq.{prospect_id}&campaign_id=eq.{campaign_id}",
            method="PATCH",
            data={
                "status": "ESCALATED",
                "escalation_reason": reason or "Agent requested human review",
                "last_message_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.warning(
            f"[CONV ESCALATE] Conversation for prospect {prospect_id} escalated: {reason}"
        )
    except Exception as e:
        logger.error(f"[CONV ESCALATE] Failed to escalate conversation: {str(e)}")

    return {"action": "ESCALATE_HUMAN", "prospect_id": prospect_id, "reason": reason}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def handle_inbound_message(
    *,
    message_id: str,
    prospect_id: str,
    campaign_id: str,
    channel: str,
    prospect_message: str,
    to_address: str,
    subject: Optional[str] = None,
    prospect_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orchestrate a full inbound reply cycle:
      1. Fetch conversation history.
      2. Determine last outbound message/channel.
      3. Call DronaHQ Conversation Agent.
      4. Execute the returned action.
      5. Persist inbound + outbound messages.

    Args:
        message_id: Idempotency key — callers should pass a stable unique ID per reply.
        prospect_id: The prospect's Supabase UUID.
        campaign_id: The campaign's Supabase UUID.
        channel: Channel the prospect replied on (EMAIL, SMS, LINKEDIN, PHONE).
        prospect_message: Raw text of the prospect's reply.
        to_address: Phone/email/identifier to reply back to.
        subject: Email subject (only used for EMAIL channel replies).
        prospect_info: Optional dict of prospect metadata (name, company, etc.).

    Returns:
        dict with keys: action, message_id, execution_result
    """
    execution_id = str(uuid.uuid4())
    channel_upper = channel.upper()

    logger.info(
        f"[CONV INBOUND] Handling inbound {channel_upper} reply "
        f"(message_id={message_id}, prospect={prospect_id}, campaign={campaign_id})"
    )

    # --- Step 1: Fetch conversation history ---
    try:
        conversations = sb_get_conversations(prospect_id=prospect_id)
        conversation_history = conversations if isinstance(conversations, list) else []
    except Exception as e:
        logger.warning(f"[CONV HISTORY] Failed to fetch history: {str(e)}")
        conversation_history = []

    # --- Step 2: Find last outbound message / channel ---
    last_outbound_message: Optional[str] = None
    last_outbound_channel: Optional[str] = None
    try:
        outreach_messages = sb_get_outreach_messages(prospect_id=prospect_id)
        if outreach_messages:
            # Most recent outbound first
            outreach_messages_sorted = sorted(
                outreach_messages,
                key=lambda m: m.get("created_at", ""),
                reverse=True,
            )
            last_msg = outreach_messages_sorted[0]
            last_outbound_message = last_msg.get("content") or last_msg.get("message")
            last_outbound_channel = last_msg.get("channel", channel_upper)
    except Exception as e:
        logger.warning(f"[CONV LAST_MSG] Failed to fetch last outbound: {str(e)}")

    # --- Step 3: Persist the inbound conversation state ---
    try:
        sb_upsert_conversation({
            "id": message_id,
            "prospect_id": prospect_id,
            "campaign_id": campaign_id,
            "channel": channel_upper,
            "status": "ACTIVE",
            "summary": f"Inbound: {prospect_message[:180]}",
            "sentiment": "NEUTRAL",
        })
    except Exception as e:
        logger.warning(f"[CONV PERSIST INBOUND] Failed: {str(e)}")

    # --- Step 4: Call Conversation Agent ---
    agent_decision = _call_conversation_agent(
        prospect_id=prospect_id,
        campaign_id=campaign_id,
        channel=channel_upper,
        prospect_message=prospect_message,
        conversation_history=conversation_history,
        last_outbound_message=last_outbound_message,
        last_outbound_channel=last_outbound_channel,
        prospect_info=prospect_info,
    )

    action = (agent_decision.get("action") or "ESCALATE_HUMAN").upper()
    if action not in VALID_ACTIONS:
        logger.warning(f"[CONV AGENT] Unknown action '{action}' — defaulting to ESCALATE_HUMAN")
        action = "ESCALATE_HUMAN"

    # --- Step 5: Execute the action ---
    execution_result: Dict[str, Any] = {}

    if action == "REPLY":
        reply_message = agent_decision.get("reply_message") or ""
        if reply_message:
            execution_result = await _execute_reply(
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                execution_id=execution_id,
                channel=channel_upper,
                reply_message=reply_message,
                to_address=to_address,
                subject=subject,
            )
            # Persist outbound reply
            try:
                sb_insert_outreach_message(
                    prospect_id=prospect_id,
                    channel=channel_upper,
                    recipient=to_address,
                    content=reply_message,
                    execution_id=execution_id,
                    campaign_id=campaign_id,
                    status=execution_result.get("status", "SENT"),
                    provider=execution_result.get("provider"),
                    provider_message_id=execution_result.get("provider_message_id"),
                )
            except Exception as e:
                logger.warning(f"[CONV PERSIST REPLY] Failed: {str(e)}")
        else:
            logger.warning(f"[CONV REPLY] Agent returned REPLY action but no reply_message")
            execution_result = {"status": "SKIPPED", "reason": "No reply_message in agent response"}

    elif action == "FOLLOW_UP":
        execution_result = await _execute_follow_up(
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            delay_hours=agent_decision.get("follow_up_delay_hours"),
            channel=channel_upper,
            message=agent_decision.get("follow_up_message"),
            to_address=to_address,
        )

    elif action == "UNSUBSCRIBE":
        execution_result = _execute_unsubscribe(
            prospect_id=prospect_id,
            campaign_id=campaign_id,
        )

    elif action == "CLOSE":
        execution_result = _execute_close(
            prospect_id=prospect_id,
            campaign_id=campaign_id,
        )

    elif action == "ESCALATE_HUMAN":
        execution_result = _execute_escalate_human(
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            reason=agent_decision.get("reason"),
        )

    elif action == "NO_ACTION":
        execution_result = {
            "status": "SUCCESS",
            "action": "NO_ACTION",
            "reason": agent_decision.get("reason") or "No reply or escalation needed",
        }

    # --- Step 6: Update conversation status ---
    try:
        raw_sentiment = str(agent_decision.get("sentiment") or agent_decision.get("intent") or "").upper()
        if "POS" in raw_sentiment or "INTEREST" in raw_sentiment:
            clean_sentiment = "POSITIVE"
        elif "NEG" in raw_sentiment or "UNSUB" in raw_sentiment or "REJECT" in raw_sentiment:
            clean_sentiment = "NEGATIVE"
        else:
            clean_sentiment = "NEUTRAL"

        clean_status = "CLOSED" if action == "CLOSE" else ("ESCALATED" if action == "ESCALATE_HUMAN" else "ACTIVE")

        sb_upsert_conversation({
            "id": message_id,
            "prospect_id": prospect_id,
            "campaign_id": campaign_id,
            "channel": channel_upper,
            "status": clean_status,
            "summary": f"Inbound: {prospect_message[:180]}",
            "next_action": action,
            "sentiment": clean_sentiment,
        })
    except Exception as e:
        logger.warning(f"[CONV PERSIST STATUS] Failed: {str(e)}")

    return {
        "message_id": message_id,
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "action": action,
        "agent_decision": agent_decision,
        "execution_result": execution_result,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
