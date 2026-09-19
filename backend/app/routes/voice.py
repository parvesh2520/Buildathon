import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel

from app.services.voice import (
    initiate_voice_call,
    handle_call_status_update,
    handle_voice_agent_result,
)
from app.models.execution import (
    ExecutionRecord,
    get_execution,
    get_execution_by_provider_call_id,
)
from app.models.prospect import get_prospect
from app.models.campaign import get_campaign

logger = logging.getLogger("routes.voice")

router = APIRouter(prefix="/api/voice", tags=["Voice SDR"])


class VoiceCallRequest(BaseModel):
    execution_id: str
    phone: Optional[str] = None


class VoiceAgentResultPayload(BaseModel):
    execution_id: Optional[str] = None
    provider_call_id: Optional[str] = None
    conversation_summary: Optional[str] = None
    call_outcome: Optional[str] = None
    interested: Optional[bool] = None
    objections: Optional[List[str]] = None
    follow_up_required: Optional[bool] = None
    next_action: Optional[str] = None


@router.post("/callback", status_code=200)
async def voice_provider_callback(request: Request) -> Dict[str, Any]:
    """
    Receives telephony call-status updates from Twilio or configured voice provider.
    
    Associates the event via CallSid or execution_id and updates:
    - RINGING
    - IN_PROGRESS (answered)
    - COMPLETED
    - NO_ANSWER
    - BUSY
    - FAILED
    """
    content_type = request.headers.get("content-type", "").lower()
    payload: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        payload = dict(form_data)
    else:
        # Fallback to query params
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
        or "IN_PROGRESS"
    )
    duration_str = payload.get("CallDuration") or payload.get("duration")
    duration = int(duration_str) if duration_str and str(duration_str).isdigit() else None
    exec_id = (
        request.query_params.get("execution_id")
        or payload.get("execution_id")
    )
    error = payload.get("ErrorMessage") or payload.get("error")

    logger.info(
        f"[VOICE CALLBACK RECEIVED] call_sid={call_sid} status={raw_status} exec_id={exec_id}"
    )

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


@router.post("/result", status_code=200)
async def receive_voice_agent_result(payload: VoiceAgentResultPayload) -> Dict[str, Any]:
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
    data = payload.model_dump(exclude_none=True)
    rec = await handle_voice_agent_result(
        call_id=payload.provider_call_id,
        execution_id=payload.execution_id,
        result_data=data,
    )

    if not rec:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found for execution_id='{payload.execution_id}' call_id='{payload.provider_call_id}'",
        )

    return {
        "status": "ok",
        "execution_id": rec.execution_id,
        "call_outcome": rec.call_outcome,
        "voice_agent_result": rec.voice_agent_result,
    }


@router.api_route("/twiml", methods=["GET", "POST"])
async def voice_twiml_endpoint(request: Request):
    """
    Renders TwiML XML instructions when an outbound phone call connects.
    Connects the caller to the SDR Voice Script Agent.
    """
    exec_id = request.query_params.get("execution_id")
    rec = get_execution(exec_id) if exec_id else None

    prospect_name = "there"
    campaign_name = "our engineering solution"

    if rec:
        p = get_prospect(rec.prospect_id)
        if p:
            prospect_name = p.name
        c = get_campaign(rec.campaign_id)
        if c:
            campaign_name = c.name

    twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Response>\n'
        f'  <Say voice="Polly.Joanna">Hello {prospect_name}, this is your AI sales representative calling regarding {campaign_name}.</Say>\n'
        f'  <Pause length="1"/>\n'
        f'  <Say voice="Polly.Joanna">Connecting you to our SDR voice script agent.</Say>\n'
        f'</Response>'
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/call", response_model=Dict[str, Any], status_code=200)
async def manual_voice_call_trigger(payload: VoiceCallRequest) -> Dict[str, Any]:
    """
    Direct endpoint to initiate a voice call for an existing execution.
    """
    rec = get_execution(payload.execution_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Execution '{payload.execution_id}' not found")

    prospect = get_prospect(rec.prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail=f"Prospect '{rec.prospect_id}' not found")

    campaign = get_campaign(rec.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{rec.campaign_id}' not found")

    phone_to_call = payload.phone or prospect.phone or ""

    outcome = await initiate_voice_call(
        phone=phone_to_call,
        prospect=prospect.model_dump(),
        campaign=campaign.model_dump(),
        strategy=rec.strategy_result or {"recommended_channel": "PHONE"},
        execution_id=rec.execution_id,
        research=rec.research_result,
        icp_result=rec.icp_result,
    )

    return outcome
