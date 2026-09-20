"""
app/services/voice.py
=====================
PHONE channel executor — Twilio Programmable Voice with Interactive AI Voice Agent.

Flow:
    Agent 3 → recommended_channel = PHONE
    → channel_dispatcher.py → initiate_voice_call()
    → Twilio client.calls.create(url=TWILIO_VOICE_URL)
    → Prospect answers phone
    → Twilio fetches TwiML from /api/voice/interactive
    → AI greets prospect, listens with <Gather input="speech">
    → Groq LLM generates conversational responses in real-time (~250ms)
    → Interactive 2-way phone conversation
"""

import json
import logging
import os
import re
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger("sdr.voice")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_usable_phone(phone: str) -> bool:
    """Returns True if phone looks like a real E.164 number (7–16 digits)."""
    if not phone:
        return False
    stripped = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
    return bool(re.fullmatch(r"\+?[0-9]{7,16}", stripped))


def _save_execution_result(
    execution_id: str,
    campaign_id: str,
    prospect_id: str,
    phone: str,
    status: str,
    call_sid: Optional[str],
    error: Optional[str],
) -> None:
    """Persists call outcome into the existing ExecutionRecord store."""
    try:
        from app.models.execution import get_execution, save_execution, ExecutionRecord, create_execution
        now_iso = datetime.now(timezone.utc).isoformat()

        rec = get_execution(execution_id) if execution_id else None
        if not rec:
            rec = ExecutionRecord(
                execution_id=execution_id or f"exec_voice_{uuid.uuid4().hex[:10]}",
                campaign_id=campaign_id or "",
                prospect_id=prospect_id or "",
            )

        rec.channel = "PHONE"
        rec.recommended_channel = "PHONE"
        rec.actual_channel = "PHONE"
        rec.status = status
        rec.completed_at = now_iso
        if call_sid:
            rec.provider_call_id = call_sid
        if error:
            rec.error = error
        rec.channel_result = {
            "channel": "PHONE",
            "status": status,
            "phone": phone,
            "external_call_id": call_sid,
            "provider_call_id": call_sid,
            "executed_at": now_iso,
        }
        save_execution(rec)
    except Exception as exc:
        logger.warning(f"[VOICE] Could not save execution record: {exc}")


# ---------------------------------------------------------------------------
# Interactive Voice AI Agent (Groq LLM ~200ms latency)
# ---------------------------------------------------------------------------

def generate_voice_response(
    prospect_name: str,
    company_name: str,
    job_title: str,
    user_speech: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[str, bool]:
    """
    Generates intelligent real-time conversational SDR voice response via Groq.
    Returns (assistant_reply, should_hangup).
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    clean_speech = (user_speech or "").strip()

    # Fast heuristic checks for early hangup
    lower = clean_speech.lower()
    if any(phrase in lower for phrase in ["not interested", "stop calling", "remove me", "do not call", "wrong number"]):
        return ("Understood. Thank you for your time, I will make sure we do not reach out again. Have a great day!", True)
    if any(phrase in lower for phrase in ["goodbye", "bye bye", "gotta go", "hang up"]):
        return ("Thank you so much for your time. Have a wonderful day!", True)

    if not groq_key:
        return ("Thank you for taking our call. I will follow up via email with more details. Have a wonderful day!", True)

    system_prompt = (
        f"You are Alex, an autonomous AI Sales Development Representative at Autonomous SDR having a LIVE telephone conversation.\n"
        f"You are on a live call with {prospect_name or 'the prospect'}, {job_title or 'an executive'} at {company_name or 'their company'}.\n"
        f"CRITICAL VOICE RULES:\n"
        f"1. Speak conversationally in 1 to 2 short sentences (maximum 28 words). This is spoken on a phone call.\n"
        f"2. ALWAYS end your turn with a direct, friendly question or call-to-action so the prospect clearly knows it is their turn to talk.\n"
        f"3. If they say 'hello' or 'can you hear me', say: 'Yes, I can hear you clearly! I was just calling to see if you have looked into automating outbound outreach with AI?'\n"
        f"4. If they ask who you are or what you do, explain you help companies automate sales outreach to book more meetings, then ask: 'Would you be open to hearing how that works?'\n"
        f"5. If they are interested, ask: 'Could we set up a quick 10-minute demo on Tuesday to show you?'\n"
        f"6. If they say they are busy or ask for an email, say: 'Totally understand, I will email the overview right away. What is the best email to send it to?'\n"
        f"7. If they say 'not interested' or 'remove me', politely say goodbye and thank them.\n"
        f"8. Never use bullet points, markdown, asterisks, emojis, or quotation marks."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for turn in conversation_history[-4:]:
            messages.append(turn)
    messages.append({"role": "user", "content": clean_speech})

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "qwen/qwen3.8-27b",
                "messages": messages,
                "max_tokens": 70,
                "temperature": 0.6,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            reply = data["choices"][0]["message"]["content"].strip()
            # Clean formatting
            reply = reply.replace('"', '').replace('*', '').replace('#', '').strip()

            lower_reply = reply.lower()
            should_hangup = any(w in lower_reply for w in ["have a great day", "goodbye", "take care", "wonderful day", "have a good one"])
            return (reply, should_hangup)

    except Exception as exc:
        logger.error(f"[VOICE LLM] Groq error: {exc}")
        return ("Thank you for your time. I will send you a brief email summary right away. Have a great day!", True)


# ---------------------------------------------------------------------------
# Core function — called by channel dispatcher (and test endpoint)
# ---------------------------------------------------------------------------

async def initiate_voice_call(
    prospect_phone: Optional[str] = None,
    phone: Optional[str] = None,
    prospect: Optional[Dict[str, Any]] = None,
    campaign: Optional[Dict[str, Any]] = None,
    strategy: Optional[Dict[str, Any]] = None,
    execution_id: Optional[str] = None,
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Place an outbound phone call through Twilio Programmable Voice.

    Required env vars:
        TWILIO_ACCOUNT_SID
        TWILIO_AUTH_TOKEN
        TWILIO_PHONE_NUMBER   — your Twilio caller-ID
        TWILIO_VOICE_URL      — TwiML / Interactive URL Twilio fetches when call connects

    Returns a dict with keys:
        success, channel, status, prospect_id, campaign_id, external_call_id
    """
    to_phone = (prospect_phone or phone or "").strip()
    if not to_phone and isinstance(prospect, dict):
        to_phone = str(prospect.get("phone") or "").strip()

    pid = (
        prospect_id
        or (prospect.get("id") or prospect.get("prospect_id") if isinstance(prospect, dict) else None)
        or "unknown"
    )
    cid = (
        campaign_id
        or (campaign.get("id") or campaign.get("campaign_id") if isinstance(campaign, dict) else None)
        or ""
    )
    exec_id = execution_id or f"exec_voice_{uuid.uuid4().hex[:10]}"

    # 1. Validate phone
    if not to_phone:
        logger.error(f"[VOICE] Missing phone number for prospect '{pid}'")
        return _fail(pid, cid, None, "Prospect phone number is missing")

    if not _is_usable_phone(to_phone):
        logger.error(f"[VOICE] Phone '{to_phone}' is not a valid E.164 number")
        return _fail(pid, cid, to_phone, f"Phone number '{to_phone}' is not a valid E.164 number")

    # 2. Read credentials from env (always reloaded so dynamic tunnels are current)
    from dotenv import load_dotenv
    load_dotenv(override=True)

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN",  "").strip()
    from_phone  = os.environ.get("TWILIO_PHONE_NUMBER","").strip()
    voice_url   = os.environ.get("TWILIO_VOICE_URL",   "").strip()

    if not account_sid:
        logger.error("[VOICE] TWILIO_ACCOUNT_SID is not set")
        return _fail(pid, cid, to_phone, "TWILIO_ACCOUNT_SID is not configured")

    if not auth_token:
        logger.error("[VOICE] TWILIO_AUTH_TOKEN is not set")
        return _fail(pid, cid, to_phone, "TWILIO_AUTH_TOKEN is not configured")

    if not from_phone:
        logger.error("[VOICE] TWILIO_PHONE_NUMBER is not set")
        return _fail(pid, cid, to_phone, "TWILIO_PHONE_NUMBER is not configured")

    if not voice_url:
        logger.error("[VOICE] TWILIO_VOICE_URL is not set")
        return _fail(pid, cid, to_phone, "TWILIO_VOICE_URL is not configured")

    # Attach execution_id to the voice_url so the TwiML webhook knows which prospect this is
    call_url = voice_url
    if "execution_id=" not in call_url:
        sep = "&" if "?" in call_url else "?"
        call_url = f"{call_url}{sep}execution_id={exec_id}"

    # 3. Place the call via Twilio SDK
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(account_sid, auth_token)

        logger.info(
            f"[VOICE] Placing Twilio call: to={to_phone}  from={from_phone}  "
            f"url={call_url}  prospect={pid}  campaign={cid}"
        )

        call = client.calls.create(
            to=to_phone,
            from_=from_phone,
            url=call_url,
        )

        call_sid = call.sid
        logger.info(f"[VOICE] Twilio accepted call — SID={call_sid}  status={call.status}")

        _save_execution_result(
            execution_id=exec_id,
            campaign_id=cid,
            prospect_id=pid,
            phone=to_phone,
            status="INITIATED",
            call_sid=call_sid,
            error=None,
        )

        return {
            "success": True,
            "channel": "PHONE",
            "status": "INITIATED",
            "prospect_id": pid,
            "campaign_id": cid,
            "external_call_id": call_sid,
            "provider_call_id": call_sid,
            "twilio_status": call.status,
            "recipient": to_phone,
        }

    except TwilioRestException as exc:
        safe_msg = str(exc).replace(auth_token, "[REDACTED]")
        logger.error(f"[VOICE] Twilio API error: {safe_msg}")
        _save_execution_result(
            execution_id=exec_id,
            campaign_id=cid,
            prospect_id=pid,
            phone=to_phone,
            status="FAILED",
            call_sid=None,
            error=safe_msg,
        )
        return _fail(pid, cid, to_phone, f"Twilio error: {safe_msg}")

    except ImportError:
        logger.error("[VOICE] twilio package is not installed — run: pip install twilio")
        return _fail(pid, cid, to_phone, "twilio SDK is not installed on this server")

    except Exception as exc:
        safe_msg = str(exc).replace(auth_token if auth_token else "__none__", "[REDACTED]")
        logger.error(f"[VOICE] Unexpected error: {safe_msg}")
        _save_execution_result(
            execution_id=exec_id,
            campaign_id=cid,
            prospect_id=pid,
            phone=to_phone,
            status="FAILED",
            call_sid=None,
            error=safe_msg,
        )
        return _fail(pid, cid, to_phone, f"Voice call could not be initiated: {safe_msg}")


def _fail(
    prospect_id: Optional[str],
    campaign_id: Optional[str],
    phone: Optional[str],
    reason: str,
) -> Dict[str, Any]:
    """Returns a standardised FAILED response dict."""
    return {
        "success": False,
        "channel": "PHONE",
        "status": "FAILED",
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "external_call_id": None,
        "provider_call_id": None,
        "recipient": phone,
        "reason": reason,
        "error": reason,
    }


# ---------------------------------------------------------------------------
# Call-lifecycle handlers (used by /api/voice/callback webhook)
# ---------------------------------------------------------------------------

async def handle_call_status_update(
    call_id: str,
    raw_status: str,
    duration: Optional[int] = None,
    error: Optional[str] = None,
    execution_id: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
):
    """Maps Twilio status-callback events onto ExecutionRecord lifecycle."""
    from app.models.execution import get_execution, get_execution_by_provider_call_id, save_execution
    from app.models.prospect import update_prospect_status

    rec = None
    if execution_id:
        rec = get_execution(execution_id)
    if not rec and call_id:
        rec = get_execution_by_provider_call_id(call_id)

    if not rec:
        logger.warning(
            f"[VOICE CALLBACK] No execution matched call_id='{call_id}' exec_id='{execution_id}'"
        )
        return None

    if call_id and not rec.provider_call_id:
        rec.provider_call_id = call_id

    STATUS_MAP = {
        "queued":      "INITIATED",
        "initiated":   "INITIATED",
        "ringing":     "RINGING",
        "in-progress": "IN_PROGRESS",
        "in_progress": "IN_PROGRESS",
        "answered":    "IN_PROGRESS",
        "completed":   "COMPLETED",
        "busy":        "BUSY",
        "no-answer":   "NO_ANSWER",
        "no_answer":   "NO_ANSWER",
        "failed":      "FAILED",
        "canceled":    "FAILED",
    }
    mapped = STATUS_MAP.get(raw_status.strip().lower(), raw_status.upper())
    rec.status = mapped

    now_iso = datetime.now(timezone.utc).isoformat()
    if mapped == "IN_PROGRESS" and not rec.answered_at:
        rec.answered_at = now_iso
    if mapped in ("COMPLETED", "BUSY", "NO_ANSWER", "FAILED"):
        rec.ended_at = now_iso
        rec.completed_at = now_iso
        rec.call_outcome = mapped
        if duration is not None:
            rec.duration = duration
        if error:
            rec.error = error
        prospect_status = {
            "COMPLETED": "CONTACTED",
            "BUSY": "FOLLOW_UP_REQUIRED",
            "NO_ANSWER": "FOLLOW_UP_REQUIRED",
            "FAILED": "FAILED",
        }.get(mapped, "FAILED")
        update_prospect_status(rec.prospect_id, prospect_status)

    save_execution(rec)
    logger.info(
        f"[VOICE CALLBACK] exec={rec.execution_id} sid={call_id} status={rec.status}"
    )
    return rec


async def handle_voice_agent_result(
    call_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    result_data: Optional[Dict[str, Any]] = None,
):
    """Stores post-call conversation results (interested, objections, etc.)."""
    if not result_data:
        return None

    from app.models.execution import get_execution, get_execution_by_provider_call_id, save_execution
    from app.models.prospect import update_prospect_status

    rec = None
    if execution_id:
        rec = get_execution(execution_id)
    if not rec and call_id:
        rec = get_execution_by_provider_call_id(call_id)
    if not rec:
        return None

    rec.voice_agent_result = {
        k: v for k, v in {
            "conversation_summary": result_data.get("conversation_summary"),
            "call_outcome":        result_data.get("call_outcome"),
            "interested":          result_data.get("interested"),
            "objections":          result_data.get("objections"),
            "follow_up_required":  result_data.get("follow_up_required"),
            "next_action":         result_data.get("next_action"),
        }.items() if v is not None
    }
    if result_data.get("call_outcome"):
        rec.call_outcome = result_data["call_outcome"]
    if result_data.get("interested") is True:
        update_prospect_status(rec.prospect_id, "MEETING_READY")

    save_execution(rec)
    logger.info(f"[VOICE RESULT] exec={rec.execution_id} outcome={rec.call_outcome}")
    return rec
