"""
Follow-up Agent orchestration.

This service deliberately does not decide the next follow-up. It only checks
eligibility, sends context to the configured DronaHQ Follow-up Agent, validates
the returned action, and executes that action through the existing SDR pipeline.
"""

import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config import FOLLOWUP_SCHEDULER_INTERVAL_SECONDS
from app.models.campaign import get_all_campaigns, get_campaign
from app.models.execution import get_all_executions
from app.models.followup import (
    FollowUpRecord,
    create_followup,
    find_followup_touch,
    get_all_followups,
    max_recorded_touch,
    save_followup,
)
from app.models.prospect import Prospect, get_all_prospects, get_prospect, update_prospect_status
from app.services.dronahq import call_followup_agent
from app.services.supabase_db import sb_get_conversations, sb_get_outreach_messages

logger = logging.getLogger("sdr.followup")

VALID_ACTIONS = {"FOLLOW_UP", "WAIT", "STOP", "ESCALATE_HUMAN"}
VALID_CHANNELS = {"EMAIL", "LINKEDIN", "SMS", "PHONE"}
TERMINAL_PROSPECT_STATUSES = {"NO_FIT", "UNSUBSCRIBED", "STOPPED", "REJECTED", "FAILED"}
_scheduler_started = False
_scheduler_lock = threading.Lock()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        clean = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(clean)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _prospect_campaign_id(prospect: Prospect) -> Optional[str]:
    return prospect.campaign_id or prospect.campaignId


def _allowed_channels(campaign: Any, prospect: Optional[Prospect], override: Optional[List[str]] = None) -> List[str]:
    raw = override or getattr(campaign, "enabled_channels", None) or ["EMAIL", "SMS", "LINKEDIN", "PHONE"]
    channels = [str(ch).strip().upper() for ch in raw if str(ch).strip()]
    if prospect and prospect.channel:
        p_ch = prospect.channel.strip().upper()
        if p_ch in VALID_CHANNELS and p_ch not in channels:
            channels.append(p_ch)
    return channels


def _last_outbound(campaign_id: str, prospect_id: str) -> Optional[Dict[str, Any]]:
    messages = sb_get_outreach_messages(prospect_id=prospect_id) or []
    scoped = [m for m in messages if not m.get("campaign_id") or m.get("campaign_id") == campaign_id]
    if scoped:
        return sorted(scoped, key=lambda m: m.get("sent_at") or m.get("created_at") or "", reverse=True)[0]

    executions = [
        e
        for e in get_all_executions()
        if e.campaign_id == campaign_id and e.prospect_id == prospect_id and e.status in {"SENT", "COMPLETED", "PENDING_MANUAL"}
    ]
    if not executions:
        return None
    latest = sorted(executions, key=lambda e: e.completed_at or e.started_at, reverse=True)[0]
    return {
        "touch_number": latest.touch_number or 1,
        "channel": latest.actual_channel or latest.recommended_channel or latest.channel,
        "created_at": latest.completed_at or latest.started_at,
        "content": (latest.personalisation_result or {}).get("content"),
    }


def has_reply_since_last_outbound(campaign_id: str, prospect_id: str) -> bool:
    last = _last_outbound(campaign_id, prospect_id)
    if not last:
        return False
    last_at = _parse_dt(last.get("sent_at") or last.get("created_at"))
    if not last_at:
        return False

    conversations = sb_get_conversations(prospect_id=prospect_id) or []
    for convo in conversations:
        if convo.get("campaign_id") and convo.get("campaign_id") != campaign_id:
            continue
        summary = str(convo.get("summary") or convo.get("last_message") or "").lower()
        inbound_hint = summary.startswith("inbound:") or str(convo.get("direction") or "").upper() == "INBOUND"
        msg_at = _parse_dt(convo.get("last_message_at") or convo.get("created_at"))
        if inbound_hint and msg_at and msg_at > last_at:
            return True
    return False


def build_followup_agent_input(
    *,
    campaign_id: str,
    prospect_id: str,
    current_touch: Optional[int] = None,
    max_allowed_touches: int = 3,
    allowed_channels: Optional[List[str]] = None,
    prior_touches: Optional[List[Dict[str, Any]]] = None,
    icp_fit_score: Optional[int] = None,
    prospect_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    campaign = get_campaign(campaign_id)
    prospect = get_prospect(prospect_id)
    if not campaign:
        raise ValueError(f"Campaign '{campaign_id}' not found")

    touch_number = current_touch if current_touch is not None else max_recorded_touch(campaign_id, prospect_id)
    icp_score = icp_fit_score if icp_fit_score is not None else (getattr(prospect, "icpScore", None) or 0)
    prospect_status = (getattr(prospect, "status", None) or "FIT").upper()
    icp_label = "FIT" if icp_score >= 40 and prospect_status != "NO_FIT" else "NO_FIT"
    channels = _allowed_channels(campaign, prospect, allowed_channels)

    touches = prior_touches
    if touches is None:
        touches = []
        for rec in sorted(get_all_executions(), key=lambda e: e.started_at):
            if rec.campaign_id == campaign_id and rec.prospect_id == prospect_id and rec.status in {"SENT", "COMPLETED", "PENDING_MANUAL"}:
                touches.append({
                    "touch_number": rec.touch_number or len(touches) + 1,
                    "channel": rec.actual_channel or rec.recommended_channel or rec.channel,
                    "sent_at": rec.completed_at or rec.started_at,
                    "angle": (rec.strategy_result or {}).get("angle"),
                    "proof_point": (rec.research_result or {}).get("verified_domain"),
                    "reply_received": False,
                })

    prospect_payload = prospect.model_dump() if prospect else (prospect_context or {"id": prospect_id})

    return {
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "campaign": campaign.id,
        "campaign_name": campaign.name,
        "icp_fit_score": icp_score,
        "icp_status": icp_label,
        "touch_number": touch_number,
        "max_allowed_touches": max_allowed_touches,
        "allowed_channels": channels,
        "prior_touches": touches,
        "prospect": prospect_payload,
        "timestamp": _now().isoformat(),
    }


def normalize_decision(response: Dict[str, Any]) -> Dict[str, Any]:
    raw = response.get("decision") if isinstance(response.get("decision"), dict) else response
    if isinstance(raw.get("follow_up_decision"), dict):
        raw = raw["follow_up_decision"]
    action = str(raw.get("action") or "").strip().upper()
    channel = str(raw.get("next_channel") or raw.get("channel") or "").strip().upper()
    if channel == "VOICE":
        channel = "PHONE"
    decision = {
        "prospect_id": raw.get("prospect_id"),
        "action": action,
        "next_channel": channel or None,
        "next_touch_number": raw.get("next_touch_number") or raw.get("touch_number"),
        "wait_days": raw.get("wait_days") if raw.get("wait_days") is not None else raw.get("delay_days"),
        "angle": raw.get("angle"),
        "reason": raw.get("reason") or raw.get("reasoning"),
    }
    try:
        if decision["next_touch_number"] is not None:
            decision["next_touch_number"] = int(decision["next_touch_number"])
    except Exception:
        pass
    try:
        if decision["wait_days"] is not None:
            decision["wait_days"] = int(decision["wait_days"])
    except Exception:
        decision["wait_days"] = None
    return decision


def validate_decision(decision: Dict[str, Any], payload: Dict[str, Any]) -> Optional[str]:
    action = decision.get("action")
    if action not in VALID_ACTIONS:
        return f"Invalid follow-up action '{action}'"
    if decision.get("prospect_id") and decision["prospect_id"] != payload["prospect_id"]:
        return "Follow-up Agent returned a different prospect_id"

    current_touch = int(payload.get("touch_number") or 0)
    max_touch = int(payload.get("max_allowed_touches") or 0)
    expected_next = current_touch + 1

    if action == "FOLLOW_UP":
        next_touch = decision.get("next_touch_number")
        if not isinstance(next_touch, int):
            return "FOLLOW_UP decision must include integer next_touch_number"
        if next_touch != expected_next:
            return f"Invalid next_touch_number {next_touch}; expected {expected_next}"
        if next_touch > max_touch:
            return f"Touch limit exceeded: {next_touch} > {max_touch}"
        if decision.get("next_channel") not in payload.get("allowed_channels", []):
            return f"Channel '{decision.get('next_channel')}' is not in allowed_channels"
    return None


async def process_followup_payload(payload: Dict[str, Any], *, dry_run: bool = False) -> Dict[str, Any]:
    campaign_id = payload.get("campaign_id") or payload.get("campaign")
    prospect_id = payload.get("prospect_id")
    if not campaign_id or not prospect_id:
        raise ValueError("campaign_id/campaign and prospect_id are required")

    if has_reply_since_last_outbound(campaign_id, prospect_id):
        return {
            "status": "ROUTED_TO_CONVERSATION_AGENT",
            "prospect_id": prospect_id,
            "campaign_id": campaign_id,
            "reason": "Inbound reply exists after the last outbound touch",
        }

    current_touch = int(payload.get("touch_number") or max_recorded_touch(campaign_id, prospect_id) or 0)
    max_allowed = int(payload.get("max_allowed_touches") or 3)
    if current_touch >= max_allowed:
        rec = create_followup(FollowUpRecord(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            touch_number=current_touch,
            action="STOP",
            status="STOPPED",
            error="Touch limit already reached",
        ))
        return {"status": "STOPPED", "record": rec.model_dump(), "reason": "Touch limit already reached"}

    agent_payload = build_followup_agent_input(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        current_touch=current_touch,
        max_allowed_touches=max_allowed,
        allowed_channels=payload.get("allowed_channels"),
        prior_touches=payload.get("prior_touches"),
        icp_fit_score=payload.get("icp_fit_score"),
        prospect_context=payload.get("prospect"),
    )
    agent_response = call_followup_agent(agent_payload)
    decision = normalize_decision(agent_response)
    validation_error = validate_decision(decision, agent_payload)
    next_touch = decision.get("next_touch_number") or current_touch + 1

    if validation_error:
        rec = create_followup(FollowUpRecord(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            touch_number=next_touch,
            channel=decision.get("next_channel"),
            action=decision.get("action") or "INVALID",
            status="FAILED",
            agent_decision=decision,
            raw_response=agent_response,
            error=validation_error,
        ))
        return {"status": "FAILED", "error": validation_error, "payload": agent_payload, "record": rec.model_dump()}

    duplicate = find_followup_touch(campaign_id, prospect_id, next_touch)
    if duplicate:
        return {"status": "SKIPPED_DUPLICATE", "record": duplicate.model_dump(), "payload": agent_payload}

    action = decision["action"]
    now_iso = _now().isoformat()
    if action == "WAIT":
        wait_days = decision.get("wait_days") or 1
        scheduled_at = (_now() + timedelta(days=wait_days)).isoformat()
        rec = create_followup(FollowUpRecord(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            touch_number=next_touch,
            channel=decision.get("next_channel"),
            action=action,
            status="WAITING",
            scheduled_at=scheduled_at,
            agent_decision=decision,
            raw_response=agent_response,
        ))
        return {"status": "WAITING", "next_follow_up_at": scheduled_at, "payload": agent_payload, "record": rec.model_dump()}

    if action == "STOP":
        update_prospect_status(prospect_id, "STOPPED")
        rec = create_followup(FollowUpRecord(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            touch_number=next_touch,
            action=action,
            status="STOPPED",
            agent_decision=decision,
            raw_response=agent_response,
        ))
        return {"status": "STOPPED", "payload": agent_payload, "record": rec.model_dump()}

    if action == "ESCALATE_HUMAN":
        rec = create_followup(FollowUpRecord(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            touch_number=next_touch,
            channel=decision.get("next_channel"),
            action=action,
            status="HUMAN_REVIEW",
            scheduled_at=now_iso,
            agent_decision=decision,
            raw_response=agent_response,
        ))
        return {
            "status": "HUMAN_REVIEW",
            "human_review_item": {
                "campaign_id": campaign_id,
                "prospect_id": prospect_id,
                "reason": decision.get("reason"),
                "agent_decision": decision,
                "timestamp": now_iso,
            },
            "payload": agent_payload,
            "record": rec.model_dump(),
        }

    rec = create_followup(FollowUpRecord(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        touch_number=next_touch,
        channel=decision.get("next_channel"),
        action=action,
        status="SCHEDULED" if dry_run else "PROCESSING",
        scheduled_at=now_iso,
        agent_decision=decision,
        raw_response=agent_response,
    ))

    if dry_run:
        return {"status": "SCHEDULED", "dry_run": True, "payload": agent_payload, "decision": decision, "record": rec.model_dump()}

    from app.services.sdr import execute_sdr_pipeline

    execution = await execute_sdr_pipeline(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        followup_context={
            "followup_record_id": rec.id,
            "touch_number": current_touch,
            "next_touch_number": next_touch,
            "max_allowed_touches": max_allowed,
            "allowed_channels": agent_payload["allowed_channels"],
            "prior_touches": agent_payload["prior_touches"],
            "decision": decision,
        },
    )
    rec.execution_id = execution.execution_id
    rec.status = "SENT" if execution.status in {"SENT", "COMPLETED", "PENDING_MANUAL"} else "FAILED"
    rec.sent_at = execution.completed_at if rec.status == "SENT" else None
    rec.error = execution.error
    save_followup(rec)
    return {
        "status": rec.status,
        "payload": agent_payload,
        "decision": decision,
        "record": rec.model_dump(),
        "execution": execution.model_dump(),
    }


async def process_due_followups(limit: int = 25) -> Dict[str, Any]:
    processed: List[Dict[str, Any]] = []
    now = _now()
    campaigns = {c.id: c for c in get_all_campaigns() if c.status == "LIVE"}
    for prospect in get_all_prospects():
        campaign_id = _prospect_campaign_id(prospect)
        if not campaign_id or campaign_id not in campaigns:
            continue
        if (prospect.status or "").upper() in TERMINAL_PROSPECT_STATUSES:
            continue
        current_touch = max_recorded_touch(campaign_id, prospect.id)
        max_allowed = 3
        if current_touch >= max_allowed:
            continue
        if has_reply_since_last_outbound(campaign_id, prospect.id):
            processed.append({
                "prospect_id": prospect.id,
                "campaign_id": campaign_id,
                "status": "ROUTED_TO_CONVERSATION_AGENT",
            })
            continue

        due_waiting = [
            r for r in get_all_followups()
            if r.campaign_id == campaign_id
            and r.prospect_id == prospect.id
            and r.status == "WAITING"
            and (not r.scheduled_at or (_parse_dt(r.scheduled_at) or now) <= now)
        ]
        has_sent_history = current_touch > 0
        if not has_sent_history and not due_waiting:
            continue

        result = await process_followup_payload({
            "campaign_id": campaign_id,
            "prospect_id": prospect.id,
            "touch_number": current_touch,
            "max_allowed_touches": max_allowed,
            "allowed_channels": _allowed_channels(campaigns[campaign_id], prospect),
        })
        processed.append(result)
        if len(processed) >= limit:
            break
    return {"processed_count": len(processed), "processed": processed, "checked_at": now.isoformat()}


def _run_scheduler() -> None:
    interval = FOLLOWUP_SCHEDULER_INTERVAL_SECONDS
    logger.info(f"[FOLLOWUP SCHEDULER] Started with interval={interval}s")
    while interval > 0:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_due_followups())
            loop.close()
        except Exception as exc:
            logger.error(f"[FOLLOWUP SCHEDULER] Cycle failed: {exc}")
        time.sleep(interval)


def start_background_followup_scheduler() -> None:
    global _scheduler_started
    interval = FOLLOWUP_SCHEDULER_INTERVAL_SECONDS
    if interval <= 0:
        logger.info("[FOLLOWUP SCHEDULER] Disabled (FOLLOWUP_SCHEDULER_INTERVAL_SECONDS=0).")
        return
    with _scheduler_lock:
        if _scheduler_started:
            return
        thread = threading.Thread(target=_run_scheduler, daemon=True, name=f"followup-scheduler-{uuid.uuid4().hex[:6]}")
        thread.start()
        _scheduler_started = True
