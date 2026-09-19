import json
import logging
from pathlib import Path
from app.services.supabase_db import (
    sb_upsert_campaign,
    sb_upsert_prospect,
    sb_upsert_execution,
    sb_insert_agent_result,
    sb_insert_outreach_message,
)
from app.models.campaign import get_all_campaigns
from app.models.prospect import get_all_prospects

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

VALID_PROSPECT_STATUSES = {
    'FIT', 'NO_FIT', 'REVIEW', 'CONTACTED', 'REPLIED',
    'MEETING_READY', 'FOLLOW_UP_REQUIRED', 'FAILED'
}

VALID_EXEC_STATUSES = {
    'PENDING', 'RUNNING', 'NO_FIT', 'READY_TO_SEND', 'SENT',
    'INITIATING', 'RINGING', 'IN_PROGRESS', 'COMPLETED',
    'PENDING_MANUAL', 'FAILED', 'BLOCKED'
}


def normalize_prospect_status(status: str) -> str:
    s = (status or "FIT").strip().upper()
    if s == "SENT":
        return "CONTACTED"
    if s == "IN_PROGRESS":
        return "REVIEW"
    if s in VALID_PROSPECT_STATUSES:
        return s
    return "FIT"


def normalize_exec_status(status: str) -> str:
    s = (status or "PENDING").strip().upper()
    if s in ["BUSY", "NO_ANSWER", "CANCELED"]:
        return "FAILED"
    if s in VALID_EXEC_STATUSES:
        return s
    return "PENDING"


def migrate_all():
    logger.info("Starting migration to Supabase...")

    # 1. Migrate Campaigns
    for c in get_all_campaigns():
        res = sb_upsert_campaign(c.model_dump())
        logger.info(f"Migrated campaign: {c.name} -> {res is not None}")

    # 2. Migrate Prospects
    for p in get_all_prospects():
        payload = {
            "id": p.id,
            "campaign_id": p.campaign_id or p.campaignId,
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "linkedin_url": p.linkedin_url or p.linkedinUrl,
            "title": p.title,
            "company": p.company,
            "domain": p.domain,
            "location": p.location,
            "company_size": p.company_size or p.companySize,
            "status": normalize_prospect_status(p.status or "FIT"),
            "channel": p.channel or "EMAIL",
            "icp_score": p.icpScore or 0,
            "notes": p.notes,
        }
        res = sb_upsert_prospect(payload)
        logger.info(f"Migrated prospect: {p.name} ({p.id}) -> {res is not None}")

    # Also check prospects.json directly for any other prospect IDs
    pros_file = DATA_DIR / "prospects.json"
    if pros_file.exists():
        with open(pros_file, "r", encoding="utf-8") as f:
            for p in json.load(f):
                payload = {
                    "id": p.get("id"),
                    "campaign_id": p.get("campaign_id") or p.get("campaignId"),
                    "name": p.get("name"),
                    "email": p.get("email"),
                    "phone": p.get("phone"),
                    "linkedin_url": p.get("linkedin_url") or p.get("linkedinUrl"),
                    "title": p.get("title"),
                    "company": p.get("company"),
                    "domain": p.get("domain"),
                    "location": p.get("location"),
                    "company_size": p.get("company_size") or p.get("companySize"),
                    "status": normalize_prospect_status(p.get("status", "FIT")),
                    "channel": p.get("channel", "EMAIL"),
                    "icp_score": p.get("icpScore") or p.get("icp_score") or 0,
                    "notes": p.get("notes"),
                }
                sb_upsert_prospect(payload)

    # 3. Migrate Executions and their Agent Results
    exec_file = DATA_DIR / "executions.json"
    if exec_file.exists():
        with open(exec_file, "r", encoding="utf-8") as f:
            executions = json.load(f)
            for e in executions:
                exec_id = e.get("execution_id") or e.get("id")
                pros_id = e.get("prospect_id")
                camp_id = e.get("campaign_id")

                payload = {
                    "id": exec_id,
                    "campaign_id": camp_id,
                    "prospect_id": pros_id,
                    "status": normalize_exec_status(e.get("status", "PENDING")),
                    "current_agent": e.get("current_agent", "ORCHESTRATOR"),
                    "recommended_channel": e.get("recommended_channel"),
                    "actual_channel": e.get("actual_channel"),
                    "action_type": e.get("action_type", "NEW_OUTREACH"),
                    "provider_call_id": e.get("provider_call_id"),
                    "started_at": e.get("started_at"),
                    "answered_at": e.get("answered_at"),
                    "ended_at": e.get("ended_at"),
                    "duration": e.get("duration"),
                    "call_outcome": e.get("call_outcome"),
                    "completed_at": e.get("completed_at"),
                    "error": e.get("error"),
                }
                res = sb_upsert_execution(payload)
                logger.info(f"Migrated execution: {exec_id} -> {res is not None}")

                # Populate agent_results from execution
                if e.get("research_result") and pros_id and res is not None:
                    sb_insert_agent_result(
                        execution_id=exec_id,
                        prospect_id=pros_id,
                        agent_type="LEAD_RESEARCH",
                        raw_output=e["research_result"],
                        summary=e["research_result"].get("prospect_summary"),
                    )
                if e.get("icp_result") and pros_id and res is not None:
                    sb_insert_agent_result(
                        execution_id=exec_id,
                        prospect_id=pros_id,
                        agent_type="ICP_FITMENT",
                        raw_output=e["icp_result"],
                        score=e["icp_result"].get("score"),
                        summary=e["icp_result"].get("reasoning"),
                    )
                if e.get("strategy_result") and pros_id and res is not None:
                    sb_insert_agent_result(
                        execution_id=exec_id,
                        prospect_id=pros_id,
                        agent_type="OUTREACH_STRATEGY",
                        raw_output=e["strategy_result"],
                        summary=e["strategy_result"].get("angle"),
                    )
                if e.get("personalisation_result") and pros_id and res is not None:
                    sb_insert_agent_result(
                        execution_id=exec_id,
                        prospect_id=pros_id,
                        agent_type="PERSONALISATION",
                        raw_output=e["personalisation_result"],
                        summary=e["personalisation_result"].get("content"),
                        sources_cited=e["personalisation_result"].get("rag_sources_cited", []),
                    )

                # Populate outreach_messages from channel_result
                cr = e.get("channel_result")
                if cr and cr.get("recipient") and pros_id and res is not None:
                    raw_st = cr.get("status", "SENT")
                    valid_st = "SENT" if raw_st == "SENT" else ("FAILED" if raw_st == "FAILED" else ("PENDING_MANUAL" if raw_st == "PENDING_MANUAL" else "PENDING"))
                    sb_insert_outreach_message(
                        execution_id=exec_id,
                        prospect_id=pros_id,
                        campaign_id=camp_id,
                        channel=cr.get("channel") or e.get("actual_channel") or "EMAIL",
                        recipient=cr.get("recipient"),
                        subject=cr.get("subject"),
                        content=cr.get("content") or (e.get("personalisation_result", {}) or {}).get("content", ""),
                        status=valid_st,
                        provider=cr.get("provider") or "SYSTEM",
                        provider_message_id=cr.get("provider_message_id"),
                        error=cr.get("error"),
                    )

    logger.info("Migration to Supabase finished successfully!")


if __name__ == "__main__":
    migrate_all()
