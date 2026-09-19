import base64
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    VOICE_PROVIDER,
    VOICE_AGENT_ENDPOINT,
    VOICE_PROVIDER_API_KEY,
    DRONAHQ_VOICE_AGENT_URL,
    DRONAHQ_VOICE_AGENT_KEY,
    BACKEND_BASE_URL,
)
from app.models.execution import (
    ExecutionRecord,
    get_execution,
    get_execution_by_provider_call_id,
    save_execution,
)
from app.models.prospect import update_prospect_status

logger = logging.getLogger("sdr.voice")


# ---------------------------------------------------------------------------
# Provider Interface & SDR Voice Script Agent Connection
# ---------------------------------------------------------------------------

async def send_context_to_voice_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Connects to the existing DronaHQ 'SDR Voice Script Agent'.
    Passes full context (Prospect, Campaign, Strategy, Research, ICP Qualification).
    
    DO NOT run a second LLM/TTS/STT agent in the backend. The SDR Voice Script Agent
    is the sole entity responsible for the conversation.
    """
    url = (VOICE_AGENT_ENDPOINT or DRONAHQ_VOICE_AGENT_URL or "").strip()
    api_key = (VOICE_PROVIDER_API_KEY or DRONAHQ_VOICE_AGENT_KEY or "").strip()

    if not url:
        logger.info(
            "[VOICE AGENT CONTEXT] No external SDR Voice Script Agent webhook URL configured. "
            "Using bundled agent context payload."
        )
        return {
            "status": "READY",
            "context": context,
            "greeting": f"Hello {context['prospect'].get('name', '')}, this is an outreach call regarding {context['campaign'].get('campaign_name', 'our developer acceleration platform')}.",
        }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Autonomous-SDR-Backend/1.0",
    }
    if api_key:
        headers["api-key"] = api_key

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(context).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else {}
            logger.info(f"[VOICE AGENT CONTEXT] Transmitted context to SDR Voice Script Agent: {url}")
            return data
    except Exception as exc:
        logger.warning(f"[VOICE AGENT CONTEXT] Unable to reach voice agent webhook: {exc}. Proceeding with default context.")
        return {
            "status": "FALLBACK",
            "context": context,
            "error": str(exc),
            "greeting": f"Hello {context['prospect'].get('name', '')}, this is an outreach call regarding {context['campaign'].get('campaign_name', 'our developer velocity solution')}.",
        }


async def create_outbound_call(
    to_phone: str,
    from_phone: str,
    voice_agent_context: Dict[str, Any],
    execution_id: str,
    agent_response: Optional[Dict[str, Any]] = None,
    callback_url: Optional[str] = None,
    twiml_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Isolated Voice Telephony Provider Interface.
    
    Supports:
    - 'twilio' (default): Native Twilio Voice REST API
    - 'dronahq' / 'webhook': Direct webhook telephony trigger
    - Fallback: Graceful pending state when credentials are unconfigured
    """
    provider = (VOICE_PROVIDER or "twilio").strip().lower()

    # 1. Twilio Voice Provider
    if provider == "twilio":
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            logger.warning("[VOICE CALL PENDING] Twilio credentials not configured in environment.")
            return {
                "success": False,
                "status": "PENDING",
                "provider": "twilio",
                "provider_call_id": None,
                "error": "Twilio Voice credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) are missing.",
            }

        endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
        auth_bytes = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode("utf-8")
        basic_auth = base64.b64encode(auth_bytes).decode("utf-8")

        # Determine TwiML URL connecting call to SDR Voice Script Agent
        # Twilio Trial accounts require 'Url' parameter (inline 'Twiml' is rejected with error 400).
        is_local = "localhost" in BACKEND_BASE_URL.lower() or "127.0.0.1" in BACKEND_BASE_URL
        effective_twiml_url = twiml_url
        if not effective_twiml_url:
            if not is_local:
                effective_twiml_url = f"{BACKEND_BASE_URL}/api/voice/twiml?execution_id={execution_id}"
            else:
                # Publicly reachable fallback for local developer testing
                effective_twiml_url = "http://demo.twilio.com/docs/voice.xml"

        params: Dict[str, str] = {
            "To": to_phone,
            "From": from_phone or TWILIO_PHONE_NUMBER,
            "Url": effective_twiml_url,
        }

        if not is_local:
            params["StatusCallback"] = callback_url or f"{BACKEND_BASE_URL}/api/voice/callback?execution_id={execution_id}"
            params["StatusCallbackEvent"] = "initiated"
            params["StatusCallbackMethod"] = "POST"

        encoded_data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=encoded_data,
            headers={
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                call_sid = resp_data.get("sid")
                logger.info(f"[VOICE CALL INITIATED] Outbound call placed via Twilio SID={call_sid} to={to_phone}")
                return {
                    "success": True,
                    "provider": "twilio",
                    "provider_call_id": call_sid,
                    "status": "INITIATING",
                    "raw_response": resp_data,
                }
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            logger.error(f"[VOICE CALL FAILED] Twilio API HTTP {err.code}: {err_body}")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("message") or err_body
            except Exception:
                err_msg = err_body
            return {
                "success": False,
                "provider": "twilio",
                "provider_call_id": None,
                "status": "FAILED",
                "error": f"Twilio Voice API error: {err_msg}",
            }
        except Exception as exc:
            logger.error(f"[VOICE CALL FAILED] Unexpected error initiating outbound call: {exc}")
            return {
                "success": False,
                "provider": "twilio",
                "provider_call_id": None,
                "status": "FAILED",
                "error": str(exc),
            }

    # 2. DronaHQ / Custom Webhook Telephony Provider
    elif provider in ["dronahq", "webhook"]:
        url = (VOICE_AGENT_ENDPOINT or DRONAHQ_VOICE_AGENT_URL or "").strip()
        if not url:
            return {
                "success": False,
                "provider": provider,
                "provider_call_id": None,
                "status": "PENDING",
                "error": f"Voice provider '{provider}' selected but VOICE_AGENT_ENDPOINT is empty.",
            }
        
        call_payload = {
            "action": "INITIATE_CALL",
            "to_phone": to_phone,
            "execution_id": execution_id,
            "voice_agent_context": voice_agent_context,
            "callback_url": f"{BACKEND_BASE_URL}/api/voice/callback?execution_id={execution_id}",
        }
        headers = {"Content-Type": "application/json"}
        if VOICE_PROVIDER_API_KEY:
            headers["api-key"] = VOICE_PROVIDER_API_KEY

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(call_payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                call_id = resp_data.get("provider_call_id") or resp_data.get("call_id") or f"dronahq_call_{execution_id[:8]}"
                return {
                    "success": True,
                    "provider": provider,
                    "provider_call_id": call_id,
                    "status": "INITIATING",
                    "raw_response": resp_data,
                }
        except Exception as exc:
            return {
                "success": False,
                "provider": provider,
                "provider_call_id": None,
                "status": "FAILED",
                "error": f"Failed to initiate call via {provider}: {exc}",
            }

    else:
        return {
            "success": False,
            "provider": provider,
            "provider_call_id": None,
            "status": "FAILED",
            "error": f"Unknown VOICE_PROVIDER '{provider}'. Supported: 'twilio', 'dronahq', 'webhook'.",
        }


# ---------------------------------------------------------------------------
# Main Entry Point: initiate_voice_call
# ---------------------------------------------------------------------------

async def initiate_voice_call(
    phone: str,
    prospect: dict,
    campaign: dict,
    strategy: dict,
    execution_id: str,
    research: Optional[dict] = None,
    icp_result: Optional[dict] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Main Voice SDR service entry point.
    
    The backend only bridges:
    DronaHQ Strategy Agent (PHONE decision)
      ↓
    Initiate Outbound Call (Twilio / Telephony Provider)
      ↓
    Pass Context to SDR Voice Script Agent
      ↓
    Track Call Lifecycle (PENDING -> INITIATING -> RINGING -> IN_PROGRESS -> COMPLETED)
    
    1. Validate that phone exists.
    2. Validate that the campaign is allowed to use PHONE.
    3. Create the outbound phone call using the configured voice provider.
    4. Connect the call to the existing SDR Voice Script Agent.
    5. Pass the prospect and campaign context required by that agent.
    6. Return the provider's call ID.
    7. Never claim that the call was completed until the provider confirms it.
    """
    clean_phone = (phone or "").strip()
    prospect_id = prospect.get("id") or prospect.get("prospect_id") or ""
    campaign_id = campaign.get("id") or campaign.get("campaign_id") or ""

    # 1. Validate that phone exists
    if not clean_phone:
        logger.error(f"[VOICE VALIDATION FAILED] Missing phone number for prospect {prospect_id}")
        return {
            "channel": "PHONE",
            "status": "FAILED",
            "recipient": None,
            "provider_call_id": None,
            "error": "Prospect phone number is missing for Voice SDR call",
        }

    # 2. Validate that the campaign is allowed to use PHONE
    enabled_channels = campaign.get("enabled_channels") or ["EMAIL", "SMS", "LINKEDIN", "PHONE"]
    allowed_upper = [str(ch).strip().upper() for ch in enabled_channels]
    if "PHONE" not in allowed_upper and "VOICE" not in allowed_upper:
        c_name = campaign.get("name", campaign_id)
        logger.warning(f"[VOICE VALIDATION BLOCKED] Campaign '{c_name}' does not allow PHONE outreach.")
        return {
            "channel": "PHONE",
            "status": "BLOCKED",
            "recipient": clean_phone,
            "provider_call_id": None,
            "error": f"Campaign '{c_name}' is not configured to allow PHONE outreach",
        }

    # 4 & 5. Build context and connect to SDR Voice Script Agent
    voice_agent_context: Dict[str, Any] = {
        "execution_id": execution_id,
        "prospect": {
            "prospect_id": prospect_id,
            "name": prospect.get("name"),
            "title": prospect.get("title"),
            "company": prospect.get("company"),
            "phone": clean_phone,
            "email": prospect.get("email"),
            "location": prospect.get("location"),
            "company_size": prospect.get("company_size") or prospect.get("companySize"),
            "domain": prospect.get("domain"),
            "linkedin_url": prospect.get("linkedin_url") or prospect.get("linkedinUrl"),
            "notes": prospect.get("notes"),
        },
        "campaign": {
            "campaign_id": campaign_id,
            "campaign_name": campaign.get("name") or campaign.get("campaignName"),
            "icp": campaign.get("icp"),
            "product": campaign.get("product") or campaign.get("description"),
        },
        "strategy": {
            "recommended_channel": strategy.get("recommended_channel", "PHONE"),
            "action_type": strategy.get("action_type", "NEW_OUTREACH"),
            "angle": strategy.get("angle"),
            "tone": strategy.get("tone"),
            "instructions_for_copywriter": strategy.get("instructions_for_copywriter"),
            "reasoning": strategy.get("reasoning"),
        },
    }

    # Include research and qualification if available (do not invent missing data)
    if research:
        voice_agent_context["research"] = research
    if icp_result:
        voice_agent_context["icp_qualification"] = icp_result

    # Transmit context to SDR Voice Script Agent
    agent_res = await send_context_to_voice_agent(voice_agent_context)

    # 3. Create outbound phone call using the configured voice provider
    call_outcome = await create_outbound_call(
        to_phone=clean_phone,
        from_phone=TWILIO_PHONE_NUMBER,
        voice_agent_context=voice_agent_context,
        execution_id=execution_id,
        agent_response=agent_res,
        callback_url=f"{BACKEND_BASE_URL}/api/voice/callback?execution_id={execution_id}",
    )

    provider_call_id = call_outcome.get("provider_call_id")
    initial_status = call_outcome.get("status", "FAILED")

    # 7. Never claim that the call was completed until provider confirms it.
    # Initial status must be INITIATING, RINGING, or PENDING.
    rec = get_execution(execution_id)
    if rec:
        rec.channel = "PHONE"
        rec.provider_call_id = provider_call_id
        rec.status = initial_status
        rec.started_at = datetime.now(timezone.utc).isoformat()
        if call_outcome.get("error"):
            rec.error = call_outcome.get("error")
        save_execution(rec)

    return {
        "channel": "PHONE",
        "status": initial_status,
        "recipient": clean_phone,
        "provider_call_id": provider_call_id,
        "provider": call_outcome.get("provider"),
        "error": call_outcome.get("error"),
        "voice_agent_connected": bool(agent_res.get("status") in ["READY", "OK"]),
        "agent_response": agent_res,
    }


# ---------------------------------------------------------------------------
# Call Lifecycle & Status Callback Handlers
# ---------------------------------------------------------------------------

async def handle_call_status_update(
    call_id: str,
    raw_status: str,
    duration: Optional[int] = None,
    error: Optional[str] = None,
    execution_id: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> Optional[ExecutionRecord]:
    """
    Updates the ExecutionRecord lifecycle based on provider callback events.
    Maps provider events to: INITIATING, RINGING, IN_PROGRESS, COMPLETED, NO_ANSWER, BUSY, FAILED.
    """
    rec: Optional[ExecutionRecord] = None
    if execution_id:
        rec = get_execution(execution_id)
    if not rec and call_id:
        rec = get_execution_by_provider_call_id(call_id)

    if not rec:
        logger.warning(f"[VOICE CALLBACK] No execution record matched for call_id='{call_id}' exec_id='{execution_id}'")
        return None

    if call_id and not rec.provider_call_id:
        rec.provider_call_id = call_id

    norm_status = (raw_status or "").strip().lower()
    now_iso = datetime.now(timezone.utc).isoformat()

    status_map = {
        "queued": "INITIATING",
        "initiated": "INITIATING",
        "ringing": "RINGING",
        "in-progress": "IN_PROGRESS",
        "in_progress": "IN_PROGRESS",
        "answered": "IN_PROGRESS",
        "completed": "COMPLETED",
        "busy": "BUSY",
        "no-answer": "NO_ANSWER",
        "no_answer": "NO_ANSWER",
        "failed": "FAILED",
        "canceled": "FAILED",
    }

    mapped_status = status_map.get(norm_status, norm_status.upper())
    rec.status = mapped_status

    if mapped_status == "IN_PROGRESS" and not rec.answered_at:
        rec.answered_at = now_iso

    if mapped_status in ["COMPLETED", "BUSY", "NO_ANSWER", "FAILED"]:
        rec.ended_at = now_iso
        rec.completed_at = now_iso
        rec.call_outcome = mapped_status
        if duration is not None:
            rec.duration = duration
        if error:
            rec.error = error

        # Update prospect pipeline status
        if mapped_status == "COMPLETED":
            update_prospect_status(rec.prospect_id, "CONTACTED")
        elif mapped_status in ["BUSY", "NO_ANSWER"]:
            update_prospect_status(rec.prospect_id, "FOLLOW_UP_REQUIRED")
        elif mapped_status == "FAILED":
            update_prospect_status(rec.prospect_id, "FAILED")

    save_execution(rec)
    logger.info(f"[VOICE CALLBACK APPLIED] execution={rec.execution_id} provider_call_id={call_id} status={rec.status}")
    return rec


async def handle_voice_agent_result(
    call_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    result_data: Optional[Dict[str, Any]] = None,
) -> Optional[ExecutionRecord]:
    """
    Stores structured conversation results returned by the SDR Voice Script Agent:
    - conversation_summary
    - call_outcome
    - interested
    - objections
    - follow_up_required
    - next_action
    
    Never fabricates values.
    """
    if not result_data:
        return None

    rec: Optional[ExecutionRecord] = None
    if execution_id:
        rec = get_execution(execution_id)
    if not rec and call_id:
        rec = get_execution_by_provider_call_id(call_id)

    if not rec:
        logger.warning(f"[VOICE AGENT RESULT] No execution found for call_id='{call_id}' execution_id='{execution_id}'")
        return None

    agent_result = {
        "conversation_summary": result_data.get("conversation_summary"),
        "call_outcome": result_data.get("call_outcome"),
        "interested": result_data.get("interested"),
        "objections": result_data.get("objections"),
        "follow_up_required": result_data.get("follow_up_required"),
        "next_action": result_data.get("next_action"),
    }
    # Filter out None keys if preferred, or keep exact payload
    rec.voice_agent_result = {k: v for k, v in agent_result.items() if v is not None}

    if result_data.get("call_outcome"):
        rec.call_outcome = result_data.get("call_outcome")

    if result_data.get("interested") is True:
        update_prospect_status(rec.prospect_id, "MEETING_READY")

    save_execution(rec)

    # Sync to Supabase conversations and follow_ups
    try:
        from app.services.supabase_db import sb_upsert_conversation, sb_create_follow_up
        from datetime import timedelta

        conv_status = "INTERESTED" if result_data.get("interested") is True else "CLOSED"
        sb_upsert_conversation({
            "prospect_id": rec.prospect_id,
            "channel": "PHONE",
            "status": conv_status,
            "outcome": rec.call_outcome,
            "summary": result_data.get("conversation_summary"),
            "objections": result_data.get("objections") or [],
            "next_step": result_data.get("next_action"),
        })

        if result_data.get("follow_up_required"):
            sb_create_follow_up({
                "prospect_id": rec.prospect_id,
                "campaign_id": rec.campaign_id,
                "channel": "PHONE",
                "step_number": 2,
                "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                "status": "SCHEDULED",
                "notes": f"Follow-up required from Voice call. Next action: {result_data.get('next_action', 'Call back')}",
            })
    except Exception as exc:
        logger.warning(f"Failed to sync voice outcome to Supabase: {exc}")

    logger.info(f"[VOICE AGENT RESULT SAVED] execution={rec.execution_id} outcome={rec.call_outcome}")
    return rec
