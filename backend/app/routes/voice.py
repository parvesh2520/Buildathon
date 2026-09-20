import logging
import os
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.services.voice import (
    initiate_voice_call,
    handle_call_status_update,
    handle_voice_agent_result,
    generate_voice_response,
)
from app.models.execution import (
    get_execution,
    save_execution,
    get_execution_by_provider_call_id,
)
from app.models.prospect import get_prospect
from app.models.campaign import get_campaign

logger = logging.getLogger("routes.voice")

router = APIRouter(prefix="/api/voice", tags=["Voice SDR"])


# ──────────────────────────────────────────────────────────────────────────────
# Twilio status-callback webhook
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/callback", status_code=200)
async def voice_provider_callback(request: Request) -> Dict[str, Any]:
    """
    Receives Twilio call-status events (initiated / ringing / in-progress /
    completed / busy / no-answer / failed).
    """
    content_type = request.headers.get("content-type", "").lower()
    payload: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
    elif "application/x-www-form-urlencoded" in content_type or "multipart" in content_type:
        form_data = await request.form()
        payload = dict(form_data)
    else:
        payload = dict(request.query_params)

    call_sid = (
        payload.get("CallSid")
        or payload.get("provider_call_id")
        or payload.get("call_id")
        or request.query_params.get("CallSid")
    )
    raw_status = (
        payload.get("CallStatus")
        or payload.get("status")
        or request.query_params.get("CallStatus")
        or "in-progress"
    )
    duration_str = payload.get("CallDuration") or payload.get("duration")
    duration = int(duration_str) if duration_str and str(duration_str).isdigit() else None
    exec_id = request.query_params.get("execution_id") or payload.get("execution_id")
    error = payload.get("ErrorMessage") or payload.get("error")

    logger.info(f"[VOICE CALLBACK] sid={call_sid} status={raw_status} exec_id={exec_id}")

    rec = await handle_call_status_update(
        call_id=str(call_sid) if call_sid else "",
        raw_status=str(raw_status),
        duration=duration,
        error=str(error) if error else None,
        execution_id=str(exec_id) if exec_id else None,
        raw_payload=payload,
    )

    if not rec:
        return {
            "status": "received",
            "matched": False,
            "call_sid": call_sid,
            "message": "Callback received but no matching execution was found.",
        }

    return {
        "status": "ok",
        "matched": True,
        "execution_id": rec.execution_id,
        "call_status": rec.status,
        "prospect_id": rec.prospect_id,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Interactive 2-Way Conversational Voice AI Endpoints (OPTION C)
# ──────────────────────────────────────────────────────────────────────────────

@router.api_route("/interactive", methods=["GET", "POST"])
async def voice_interactive_entry(request: Request):
    """
    Twilio voice entrypoint for interactive AI phone conversation.
    Twilio fetches this TwiML when the outbound call is answered.
    """
    exec_id = request.query_params.get("execution_id")
    rec = get_execution(exec_id) if exec_id else None

    prospect_name = "there"
    if rec:
        p = get_prospect(rec.prospect_id)
        if p and p.name:
            prospect_name = p.name.split()[0]

    base_url = str(request.base_url).rstrip("/")
    respond_url = f"{base_url}/api/voice/interactive/respond"
    if exec_id:
        respond_url += f"?execution_id={exec_id}"

    vr = VoiceResponse()
    greeting = f"Hello {prospect_name}! This is Alex from Autonomous SDR. Am I speaking with {prospect_name}?"

    gather = Gather(
        input="speech",
        action=respond_url,
        method="POST",
        speech_timeout=2,
        timeout=6,
        speech_model="phone_call",
    )
    gather.say(greeting, voice="Polly.Joanna")
    vr.append(gather)

    # Fallback if initial silence
    fallback_gather = Gather(
        input="speech",
        action=respond_url,
        method="POST",
        speech_timeout=2,
        timeout=5,
        speech_model="phone_call",
    )
    fallback_gather.say(f"Are you still there, {prospect_name}?", voice="Polly.Joanna")
    vr.append(fallback_gather)

    vr.say("I didn't catch that. I will send you a follow-up email. Have a great day!", voice="Polly.Joanna")
    vr.hangup()

    return Response(content=str(vr), media_type="application/xml")


@router.post("/interactive/respond")
async def voice_interactive_respond(request: Request):
    """
    Receives spoken speech transcribed by Twilio <Gather>,
    invokes Groq AI in ~200ms to produce a responsive SDR reply ending with a question,
    and returns TwiML with the spoken reply + next <Gather>.
    """
    form_data = await request.form()
    payload = dict(form_data)

    speech_result = (payload.get("SpeechResult") or "").strip()
    exec_id = request.query_params.get("execution_id") or payload.get("execution_id")

    rec = get_execution(exec_id) if exec_id else None
    prospect_name = "there"
    company_name = "your company"
    job_title = "executive"

    if rec:
        p = get_prospect(rec.prospect_id)
        if p:
            prospect_name = p.name.split()[0] if p.name else "there"
            company_name = p.company or company_name
            job_title = p.title or job_title

    vr = VoiceResponse()

    base_url = str(request.base_url).rstrip("/")
    respond_url = f"{base_url}/api/voice/interactive/respond"
    if exec_id:
        respond_url += f"?execution_id={exec_id}"

    # If user was silent on this turn
    if not speech_result:
        fallback = Gather(
            input="speech",
            action=respond_url,
            method="POST",
            speech_timeout=2,
            timeout=5,
            speech_model="phone_call",
        )
        fallback.say("Sorry, I could not hear you. Could you repeat that please?", voice="Polly.Joanna")
        vr.append(fallback)
        vr.say("No worries, I will send you an email. Have a wonderful day!", voice="Polly.Joanna")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    # History of previous turns in this call
    history = []
    if rec and isinstance(rec.voice_agent_result, dict):
        history = list(rec.voice_agent_result.get("turns") or [])

    ai_reply, should_hangup = generate_voice_response(
        prospect_name=prospect_name,
        company_name=company_name,
        job_title=job_title,
        user_speech=speech_result,
        conversation_history=history,
    )

    # Save turn to record
    history.append({"role": "user", "content": speech_result})
    history.append({"role": "assistant", "content": ai_reply})

    if rec:
        if not isinstance(rec.voice_agent_result, dict):
            rec.voice_agent_result = {}
        rec.voice_agent_result["turns"] = history
        rec.voice_agent_result["last_user_speech"] = speech_result
        rec.voice_agent_result["last_ai_speech"] = ai_reply
        if should_hangup:
            rec.call_outcome = "COMPLETED"
            rec.status = "COMPLETED"
        save_execution(rec)

    if should_hangup:
        vr.say(ai_reply, voice="Polly.Joanna")
        vr.hangup()
    else:
        gather = Gather(
            input="speech",
            action=respond_url,
            method="POST",
            speech_timeout=2,
            timeout=6,
            speech_model="phone_call",
        )
        gather.say(ai_reply, voice="Polly.Joanna")
        vr.append(gather)

        fallback = Gather(
            input="speech",
            action=respond_url,
            method="POST",
            speech_timeout=2,
            timeout=5,
            speech_model="phone_call",
        )
        fallback.say("I didn't quite catch that. Could you repeat please?", voice="Polly.Joanna")
        vr.append(fallback)

        vr.say("Thank you so much for your time. Have a wonderful day!", voice="Polly.Joanna")
        vr.hangup()

    return Response(content=str(vr), media_type="application/xml")


# ──────────────────────────────────────────────────────────────────────────────
# Transcript & Recording Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/transcript/{identifier}", response_model=Dict[str, Any])
async def get_call_transcript(identifier: str) -> Dict[str, Any]:
    """
    Returns full multi-turn call transcript, audio recording URL, and outcome.
    Can be retrieved by execution_id or provider_call_id (Call SID).
    """
    rec = get_execution(identifier)
    if not rec:
        rec = get_execution_by_provider_call_id(identifier)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Execution record '{identifier}' not found")

    result = rec.voice_agent_result or {}
    turns = result.get("turns", [])

    formatted_transcript = []
    for turn in turns:
        speaker = "Prospect" if turn.get("role") == "user" else "Alex (AI SDR)"
        formatted_transcript.append({
            "speaker": speaker,
            "text": turn.get("content", "")
        })

    # Fetch Twilio recording URL if call_sid exists and recording_url not yet cached
    recording_url = result.get("recording_url")
    if not recording_url and rec.provider_call_id:
        try:
            from twilio.rest import Client
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
            if account_sid and auth_token:
                client = Client(account_sid, auth_token)
                recordings = client.calls(rec.provider_call_id).recordings.list(limit=1)
                if recordings:
                    rec_sid = recordings[0].sid
                    recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Recordings/{rec_sid}.mp3"
                    result["recording_url"] = recording_url
                    result["recording_sid"] = rec_sid
                    rec.voice_agent_result = result
                    save_execution(rec)
        except Exception as e:
            logger.warning(f"Could not fetch Twilio recording: {e}")

    return {
        "execution_id": rec.execution_id,
        "call_sid": rec.provider_call_id,
        "prospect_id": rec.prospect_id,
        "status": rec.status,
        "call_outcome": rec.call_outcome or ("COMPLETED" if len(turns) > 0 else "IN_PROGRESS"),
        "recording_url": recording_url,
        "turns_count": len(turns),
        "transcript": formatted_transcript,
        "last_user_speech": result.get("last_user_speech"),
        "last_ai_speech": result.get("last_ai_speech"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Static fallback TwiML endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.api_route("/twiml", methods=["GET", "POST"])
async def voice_twiml_endpoint(request: Request):
    """Fallback static pitch endpoint if interactive mode is not used."""
    exec_id = request.query_params.get("execution_id")
    rec = get_execution(exec_id) if exec_id else None

    prospect_name = "there"
    campaign_name = "our solution"

    if rec:
        p = get_prospect(rec.prospect_id)
        if p and p.name:
            prospect_name = p.name.split()[0]
        c = get_campaign(rec.campaign_id)
        if c:
            campaign_name = c.name

    vr = VoiceResponse()
    vr.say(f"Hello {prospect_name}, this is an outreach call regarding {campaign_name}. We would love to connect with you.", voice="Polly.Joanna")
    vr.pause(length=1)
    vr.say("Thank you for your time. Have a great day.", voice="Polly.Joanna")
    vr.hangup()
    return Response(content=str(vr), media_type="application/xml")


# ──────────────────────────────────────────────────────────────────────────────
# Post-call conversation result storage
# ──────────────────────────────────────────────────────────────────────────────

class VoiceAgentResultPayload(BaseModel):
    execution_id: Optional[str] = None
    provider_call_id: Optional[str] = None
    conversation_summary: Optional[str] = None
    call_outcome: Optional[str] = None
    interested: Optional[bool] = None
    objections: Optional[List[str]] = None
    follow_up_required: Optional[bool] = None
    next_action: Optional[str] = None


@router.post("/result", status_code=200)
async def receive_voice_agent_result(payload: VoiceAgentResultPayload) -> Dict[str, Any]:
    """Stores structured conversation results from a post-call agent."""
    data = payload.model_dump(exclude_none=True)
    rec = await handle_voice_agent_result(
        call_id=payload.provider_call_id,
        execution_id=payload.execution_id,
        result_data=data,
    )
    if not rec:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found for execution_id='{payload.execution_id}'",
        )
    return {
        "status": "ok",
        "execution_id": rec.execution_id,
        "call_outcome": rec.call_outcome,
        "voice_agent_result": rec.voice_agent_result,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Manual trigger for an existing execution
# ──────────────────────────────────────────────────────────────────────────────

class VoiceCallRequest(BaseModel):
    execution_id: str
    phone: Optional[str] = None


@router.post("/call", response_model=Dict[str, Any], status_code=200)
async def manual_voice_call_trigger(payload: VoiceCallRequest) -> Dict[str, Any]:
    """Trigger a Twilio call for an existing execution record."""
    rec = get_execution(payload.execution_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Execution '{payload.execution_id}' not found")

    prospect = get_prospect(rec.prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail=f"Prospect '{rec.prospect_id}' not found")

    campaign = get_campaign(rec.campaign_id)

    phone_to_call = payload.phone or (prospect.phone if prospect else "") or ""

    return await initiate_voice_call(
        prospect_phone=phone_to_call,
        prospect_id=rec.prospect_id,
        campaign_id=rec.campaign_id,
        execution_id=rec.execution_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Development test endpoint  POST /api/voice/test
# ──────────────────────────────────────────────────────────────────────────────

class VoiceTestRequest(BaseModel):
    phone: str                          # Must be Twilio-verified on trial accounts
    prospect_id: Optional[str] = None


@router.post("/test", response_model=Dict[str, Any], status_code=200)
async def test_voice_call_endpoint(payload: VoiceTestRequest) -> Dict[str, Any]:
    """
    Development test endpoint for Interactive Conversational AI Call (Option C).

    POST /api/voice/test
    {
        "phone": "+YOUR_VERIFIED_TEST_NUMBER"
    }

    Places a real Twilio call with interactive 2-way speech conversation + audio recording enabled.
    """
    outcome = await initiate_voice_call(
        prospect_phone=payload.phone,
        prospect_id=payload.prospect_id or "parvesh_user",
    )

    return {
        "success": outcome.get("success", False),
        "channel": "PHONE",
        "status": outcome.get("status", "FAILED"),
        "prospect_id": outcome.get("prospect_id"),
        "recipient": outcome.get("recipient") or payload.phone,
        "external_call_id": outcome.get("external_call_id"),
        "twilio_call_sid": outcome.get("external_call_id"),
        "twilio_status": outcome.get("twilio_status"),
        "error": outcome.get("error"),
        "reason": outcome.get("reason"),
    }
