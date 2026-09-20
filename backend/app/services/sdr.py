import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.models.prospect import get_prospect, get_all_prospects, update_prospect_status, Prospect
from app.models.campaign import get_campaign, Campaign
from app.models.execution import (
    ExecutionRecord,
    create_execution,
    get_execution,
    get_campaign_executions,
    get_all_executions,
    update_execution,
    save_execution,
)
from app.services.dronahq import trigger_dronahq, parse_agent_results, run_dronahq_multi_agent_pipeline
from app.services.channel_dispatcher import dispatch_outreach

logger = logging.getLogger("sdr.orchestrator")


class SDRRunRequest(BaseModel):
    campaign_id: str
    prospect_id: str


def _log_structured(
    execution_id: str,
    campaign_id: str,
    prospect_id: str,
    agent: str,
    channel: Optional[str],
    status: str,
    detail: Optional[str] = None,
):
    """Structured logging per hackathon spec. Never logs secrets/tokens."""
    now_iso = datetime.now(timezone.utc).isoformat()
    msg = (
        f"[SDR AUDIT] time={now_iso} execution_id={execution_id} "
        f"campaign_id={campaign_id} prospect_id={prospect_id} agent={agent} "
        f"channel={channel or 'NONE'} status={status}"
    )
    if detail:
        msg += f" detail='{detail}'"
    logger.info(msg)


async def execute_sdr_pipeline(campaign_id: str, prospect_id: str) -> ExecutionRecord:
    """
    Autonomous SDR Orchestration Pipeline.
    
    1. Checks Campaign Lifecycle (LIVE vs PAUSED).
    2. Constructs structured payload and invokes DronaHQ Automation Webhook.
    3. Evaluates ICP Fitment (NO_FIT aborts outreach immediately).
    4. Extracts channel directive from Personalisation Agent.
    5. Validates channel-specific contact info and content length.
    6. Dispatches via Channel Dispatcher (Email, SMS, LinkedIn, Voice).
    7. Persists execution state and updates prospect status.
    """
    execution_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    campaign = get_campaign(campaign_id)
    prospect = get_prospect(prospect_id)

    # 1. Campaign Pause Check
    if not campaign:
        rec = ExecutionRecord(
            execution_id=execution_id,
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            status="FAILED",
            current_agent="ORCHESTRATOR",
            error=f"Campaign '{campaign_id}' not found",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        create_execution(rec)
        _log_structured(execution_id, campaign_id, prospect_id, "ORCHESTRATOR", None, "FAILED", "Campaign not found")
        return rec

    from app.routes.operational_controls import _controls_state
    if _controls_state.get("global_kill_switch"):
        rec = ExecutionRecord(
            execution_id=execution_id,
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            status="BLOCKED",
            current_agent="ORCHESTRATOR",
            error=f"Emergency Global Kill Switch is ENGAGED ({_controls_state.get('kill_switch_reason', 'Operator Stop')}). Autonomous activity halted.",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        create_execution(rec)
        _log_structured(execution_id, campaign_id, prospect_id, "ORCHESTRATOR", None, "BLOCKED", "Global Kill Switch active")
        return rec

    if campaign.status != "LIVE":
        rec = ExecutionRecord(
            execution_id=execution_id,
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            status="BLOCKED",
            current_agent="ORCHESTRATOR",
            error=f"Campaign '{campaign.name}' is PAUSED. Autonomous execution blocked.",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        create_execution(rec)
        _log_structured(execution_id, campaign_id, prospect_id, "ORCHESTRATOR", None, "BLOCKED", "Campaign is PAUSED")
        return rec

    if not prospect:
        rec = ExecutionRecord(
            execution_id=execution_id,
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            status="FAILED",
            current_agent="ORCHESTRATOR",
            error=f"Prospect '{prospect_id}' not found",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        create_execution(rec)
        _log_structured(execution_id, campaign_id, prospect_id, "ORCHESTRATOR", None, "FAILED", "Prospect not found")
        return rec

    # 2. Idempotency Check: Prevent duplicate sends if already successfully dispatched
    for past_exec in get_all_executions():
        if (
            past_exec.campaign_id == campaign_id
            and past_exec.prospect_id == prospect_id
            and past_exec.status in ["SENT", "COMPLETED"]
        ):
            logger.info(
                f"[IDEMPOTENCY] Outreach already sent for prospect '{prospect_id}' in campaign '{campaign_id}' "
                f"(execution_id: {past_exec.execution_id}, status: {past_exec.status}). Skipping duplicate send."
            )
            _log_structured(
                past_exec.execution_id,
                campaign_id,
                prospect_id,
                "ORCHESTRATOR",
                past_exec.actual_channel or past_exec.recommended_channel,
                "SKIPPED_DUPLICATE",
                "Idempotency guard: outreach already sent",
            )
            return past_exec

    # 3. Initialise RUNNING execution record
    rec = ExecutionRecord(
        execution_id=execution_id,
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        status="RUNNING",
        current_agent="LEAD_RESEARCH",
        started_at=started_at,
    )
    create_execution(rec)
    _log_structured(execution_id, campaign_id, prospect_id, "LEAD_RESEARCH", None, "RUNNING")

    # 3. Construct payload for DronaHQ Webhook
    p_phone = getattr(prospect, "phone", None) or ""
    p_linkedin = getattr(prospect, "linkedin_url", None) or getattr(prospect, "linkedinUrl", None) or ""

    dronahq_payload = {
        "prospect": {
            "prospect_id": prospect.id,
            "name": prospect.name,
            "email": prospect.email,
            "phone": p_phone,
            "linkedin_url": p_linkedin,
            "title": prospect.title,
            "company": prospect.company,
            "domain": prospect.domain or "",
            "location": prospect.location or "",
            "company_size": prospect.company_size or getattr(prospect, "companySize", "") or "",
            "notes": prospect.notes or "",
        },
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "icp": campaign.icp,
            "enabled_channels": getattr(campaign, "enabled_channels", ["EMAIL", "SMS", "LINKEDIN", "PHONE"]),
        },
    }

    # 4. Invoke DronaHQ Multi-Agent Pipeline
    research_res, icp_res, strat_res, pers_res = run_dronahq_multi_agent_pipeline(
        prospect=prospect,
        campaign=campaign,
    )

    rec.research_result = research_res
    rec.icp_result = icp_res
    rec.strategy_result = strat_res
    rec.personalisation_result = pers_res

    # Save to Supabase agent_results
    try:
        from app.services.supabase_db import sb_insert_agent_result
        if research_res:
            sb_insert_agent_result(
                execution_id=execution_id,
                prospect_id=prospect_id,
                agent_type="LEAD_RESEARCH",
                raw_output=research_res,
                summary=research_res.get("prospect_summary"),
            )
        if icp_res:
            sb_insert_agent_result(
                execution_id=execution_id,
                prospect_id=prospect_id,
                agent_type="ICP_FITMENT",
                raw_output=icp_res,
                score=icp_res.get("score"),
                summary=icp_res.get("reasoning"),
            )
        if strat_res:
            sb_insert_agent_result(
                execution_id=execution_id,
                prospect_id=prospect_id,
                agent_type="OUTREACH_STRATEGY",
                raw_output=strat_res,
                summary=strat_res.get("angle"),
            )
        if pers_res:
            sb_insert_agent_result(
                execution_id=execution_id,
                prospect_id=prospect_id,
                agent_type="PERSONALISATION",
                raw_output=pers_res,
                summary=pers_res.get("content"),
                sources_cited=pers_res.get("rag_sources_cited", []),
            )
    except Exception as exc:
        logger.warning(f"Failed to record agent_results in Supabase: {exc}")

    # 6. Check ICP Qualification
    if icp_res.get("status") == "NO_FIT":
        rec.status = "NO_FIT"
        rec.current_agent = "ICP_FITMENT"
        rec.completed_at = datetime.now(timezone.utc).isoformat()
        rec.error = icp_res.get("reasoning", "Prospect disqualified by ICP Agent.")
        save_execution(rec)
        update_prospect_status(prospect.id, "NO_FIT")
        _log_structured(execution_id, campaign_id, prospect_id, "ICP_FITMENT", None, "NO_FIT", rec.error)
        return rec

    # 7. Channel Decision from DronaHQ Outreach Strategy Agent
    # DronaHQ's Outreach Strategy Agent makes the definitive channel decision
    strategy_channel = (strat_res.get("recommended_channel") or "").strip().upper() if strat_res else None
    recommended_channel = strategy_channel or (pers_res.get("channel") if pers_res else None) or (prospect.channel or "EMAIL").strip().upper()
    if recommended_channel == "VOICE":
        recommended_channel = "PHONE"

    rec.channel = recommended_channel
    rec.recommended_channel = recommended_channel
    rec.actual_channel = recommended_channel
    rec.action_type = strat_res.get("action_type", "NEW_OUTREACH") if strat_res else "NEW_OUTREACH"
    rec.current_agent = "PERSONALISATION"
    _log_structured(execution_id, campaign_id, prospect_id, "OUTREACH_STRATEGY", recommended_channel, "DECIDED")

    # 8. Channel Requirements Validation
    validation_error = None
    if recommended_channel == "EMAIL":
        if not prospect.email:
            validation_error = "Prospect email address is missing for EMAIL outreach"
        elif not pers_res.get("content"):
            validation_error = "Email content is missing"
        elif not pers_res.get("subject_line"):
            validation_error = "Email subject line is missing"

    elif recommended_channel == "SMS":
        if not p_phone:
            validation_error = "Prospect phone number is missing for SMS outreach"
        elif not pers_res.get("content"):
            validation_error = "SMS content is missing"
        elif len(pers_res.get("content", "")) > 160:
            pers_res["content"] = pers_res["content"][:157].rstrip() + "..."
            logger.info(f"[SMS TRUNCATE] Truncated SMS content to 160 chars for prospect {prospect_id}")

    elif recommended_channel == "LINKEDIN":
        if not p_linkedin:
            validation_error = "Prospect LinkedIn URL is missing for LINKEDIN outreach"
        elif not pers_res.get("content"):
            validation_error = "LinkedIn content is missing"

    elif recommended_channel in ["PHONE", "VOICE"]:
        if not p_phone:
            validation_error = "Prospect phone number is missing for Voice SDR call"

    if not validation_error and recommended_channel in _controls_state.get("paused_channels", []):
        validation_error = f"Outreach via '{recommended_channel}' is temporarily PAUSED by operator channel policy"

    if validation_error:
        rec.status = "FAILED"
        rec.error = validation_error
        rec.completed_at = datetime.now(timezone.utc).isoformat()
        save_execution(rec)
        _log_structured(execution_id, campaign_id, prospect_id, "VALIDATOR", recommended_channel, "FAILED", validation_error)
        return rec

    # 9. Dispatch to Channel Service (Passes context to SDR Voice Script Agent if PHONE)
    rec.current_agent = "CHANNEL_EXECUTOR"
    rec.status = "READY_TO_SEND"

    channel_outcome = await dispatch_outreach(
        recommended_channel=recommended_channel,
        prospect=prospect,
        personalisation=pers_res,
        strategy=strat_res,
        campaign=campaign,
        execution_id=execution_id,
        research=research_res,
        icp_result=icp_res,
    )

    rec.channel_result = channel_outcome
    rec.completed_at = datetime.now(timezone.utc).isoformat()
    if channel_outcome.get("provider_call_id"):
        rec.provider_call_id = channel_outcome["provider_call_id"]

    final_status = channel_outcome.get("status", "FAILED")
    actual_channel = (
        channel_outcome.get("channel")
        or rec.actual_channel
        or rec.recommended_channel
        or recommended_channel
        or "EMAIL"
    ).strip().upper()
    icp_score_val = icp_res.get("score") if icp_res else None

    if final_status == "SENT":
        rec.status = "SENT"
        update_prospect_status(prospect.id, "SENT", channel=actual_channel, icp_score=icp_score_val)
    elif final_status in ["INITIATING", "RINGING", "IN_PROGRESS"]:
        # Phone call created; never mark COMPLETED until provider confirms
        rec.status = final_status
        update_prospect_status(prospect.id, "IN_PROGRESS", channel=actual_channel, icp_score=icp_score_val)
    elif final_status == "COMPLETED":
        rec.status = "COMPLETED"
        update_prospect_status(prospect.id, "CONTACTED", channel=actual_channel, icp_score=icp_score_val)
    elif final_status == "PENDING_MANUAL":
        rec.status = "PENDING_MANUAL"
        update_prospect_status(prospect.id, "READY_TO_SEND", channel=actual_channel, icp_score=icp_score_val)
    elif final_status == "PENDING":
        rec.status = "PENDING"
        update_prospect_status(prospect.id, "READY_TO_SEND", channel=actual_channel, icp_score=icp_score_val)
    elif final_status == "BLOCKED":
        rec.status = "BLOCKED"
        rec.error = channel_outcome.get("error", "Outreach channel blocked by campaign policy")
    else:
        rec.status = "FAILED"
        rec.error = channel_outcome.get("error", "Channel dispatch failed")
        update_prospect_status(prospect.id, "FAILED", channel=actual_channel, icp_score=icp_score_val)

    save_execution(rec)

    # Save outreach message to Supabase
    try:
        from app.services.supabase_db import sb_insert_outreach_message
        raw_st = channel_outcome.get("status", "SENT")
        valid_st = (
            raw_st
            if raw_st in ["PENDING", "PENDING_MANUAL", "SENT", "DELIVERED", "FAILED", "BOUNCED"]
            else ("SENT" if raw_st in ["COMPLETED", "INITIATING", "RINGING", "IN_PROGRESS"] else "FAILED")
        )
        msg_recipient = (
            channel_outcome.get("recipient")
            or (p_email if recommended_channel == "EMAIL" else (p_phone if recommended_channel in ["SMS", "PHONE", "VOICE"] else p_linkedin))
        )
        if msg_recipient:
            sb_insert_outreach_message(
                execution_id=execution_id,
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                channel=channel_outcome.get("channel") or recommended_channel,
                recipient=msg_recipient,
                subject=channel_outcome.get("subject") or (pers_res.get("subject_line") if pers_res else None),
                content=channel_outcome.get("content") or (pers_res.get("content", "") if pers_res else ""),
                status=valid_st,
                provider=channel_outcome.get("provider") or "SYSTEM",
                provider_message_id=channel_outcome.get("provider_message_id") or channel_outcome.get("provider_call_id"),
                error=channel_outcome.get("error"),
            )
    except Exception as exc:
        logger.warning(f"Failed to record outreach_message in Supabase: {exc}")

    _log_structured(
        execution_id,
        campaign_id,
        prospect_id,
        "CHANNEL_EXECUTOR",
        recommended_channel,
        rec.status,
        channel_outcome.get("error") or f"provider_msg_id={channel_outcome.get('provider_message_id')}",
    )

    return rec


# Synchronous helper wrapper for backward compatibility
def queue_sdr_run(campaign_id: str, prospect_id: str) -> ExecutionRecord:
    import asyncio
    return asyncio.run(execute_sdr_pipeline(campaign_id, prospect_id))


async def process_dronahq_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handles incoming DronaHQ webhook posts."""
    prospect_id = payload.get("prospect_id")
    campaign_id = payload.get("campaign_id") or "us_saas_cto"
    if prospect_id:
        record = await execute_sdr_pipeline(campaign_id, prospect_id)
        return record.model_dump()
    return {"status": "ACK", "message": "Webhook payload received", "data": payload}
