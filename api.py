"""
Autonomous SDR System - FastAPI Backend Orchestrator
Implements User Flows 1, 2, 3, 4, 5, and 6.
Backed by real Gemini LLM agents with zero DronaHQ credit consumption.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from schemas import RawProspect
from llm_agents import SDRAgentPipeline

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

app = FastAPI(
    title="Autonomous SDR Control Plane API",
    description="Backend Orchestrator for Multi-Campaign Autonomous SDR Agents",
    version="1.0.0"
)

# Enable CORS for DronaHQ webhooks and UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = SDRAgentPipeline(api_key=GEMINI_API_KEY)

# =====================================================================
# IN-MEMORY DATABASE (Pre-seeded with 3 Concurrent Campaigns)
# =====================================================================

CAMPAIGNS: Dict[str, Dict[str, Any]] = {
    "us_saas_cto": {
        "id": "us_saas_cto",
        "name": "US SaaS CTO",
        "icp_description": "CTOs & VPs of Eng at 50-500 person US B2B SaaS on AWS/K8s",
        "status": "LIVE",  # LIVE, PAUSED, DRAFT, ARCHIVED
        "active_channels": ["EMAIL", "LINKEDIN"],
        "assigned_reps": ["Alex Rivera"],
        "metrics": {"prospects": 0, "outreach": 0, "meetings": 0},
        "system_prompt_version": "v1.0",
        "created_at": "2026-09-18T21:00:00Z"
    },
    "india_bfsi_cio": {
        "id": "india_bfsi_cio",
        "name": "India BFSI CIO",
        "icp_description": "CIOs & CISOs at Indian scheduled banks, NBFCs, and Tier-1 fintechs",
        "status": "PAUSED",  # Demonstrates independent pause state
        "active_channels": ["EMAIL", "PHONE"],
        "assigned_reps": ["Priya Sharma"],
        "metrics": {"prospects": 0, "outreach": 0, "meetings": 0},
        "system_prompt_version": "v1.0",
        "created_at": "2026-09-18T21:00:00Z"
    },
    "voice_ai_founder": {
        "id": "voice_ai_founder",
        "name": "Voice AI Founders",
        "icp_description": "Seed/Series A AI Founders building conversational speech & voicebots",
        "status": "LIVE",
        "active_channels": ["LINKEDIN", "EMAIL", "PHONE"],
        "assigned_reps": ["Devon Patel"],
        "metrics": {"prospects": 0, "outreach": 0, "meetings": 0},
        "system_prompt_version": "v1.0",
        "created_at": "2026-09-18T21:00:00Z"
    }
}

GLOBAL_KILL_SWITCH = False
PROSPECTS_DB: Dict[str, Dict[str, Any]] = {}
INBOX_QUEUE: List[Dict[str, Any]] = []  # Flow 4: Held actions awaiting manager approval
CONFLICTS_DB: List[Dict[str, Any]] = []  # Flow 5: Cross-campaign conflicts


# =====================================================================
# API REQUEST MODELS
# =====================================================================

class ProcessProspectRequest(BaseModel):
    prospect_id: str
    campaign_id: str
    name: str
    title: str
    company: str
    domain: Optional[str] = ""
    location: Optional[str] = ""
    company_size_estimate: Optional[str] = None
    raw_notes: Optional[str] = None

class InboxDecisionRequest(BaseModel):
    inbox_item_id: str
    action: str  # "APPROVE", "EDIT", "REJECT"
    edited_content: Optional[str] = None
    rejection_note: Optional[str] = None

class InboundReplyRequest(BaseModel):
    prospect_id: str
    campaign_id: str
    reply_text: str

class CadenceTimerRequest(BaseModel):
    prospect_id: str
    current_touch_number: int


class CreateCampaignRequest(BaseModel):
    """Flow 1: Campaign creation wizard data."""
    id: str  # slug like "us_saas_cto"
    name: str
    icp_description: str
    active_channels: List[str] = ["EMAIL"]
    assigned_reps: List[str] = []
    system_prompt_version: str = "v1.0"


class UpdateCampaignRequest(BaseModel):
    """Update campaign settings."""
    name: Optional[str] = None
    icp_description: Optional[str] = None
    active_channels: Optional[List[str]] = None
    assigned_reps: Optional[List[str]] = None
    system_prompt_version: Optional[str] = None


class ConflictResolutionRequest(BaseModel):
    """Flow 5: Manager resolves a cross-campaign conflict."""
    conflict_id: str
    winning_campaign_id: str  # Which campaign keeps the prospect


class RepOffboardRequest(BaseModel):
    """Flow 6: Offboard a rep and reassign campaigns."""
    rep_name: str
    reassignments: Dict[str, str] = {}  # campaign_id -> new_rep_name


# =====================================================================
# REPS DATABASE
# =====================================================================

REPS_DB: Dict[str, Dict[str, Any]] = {
    "Alex Rivera": {"name": "Alex Rivera", "status": "ACTIVE", "campaigns": ["us_saas_cto"]},
    "Priya Sharma": {"name": "Priya Sharma", "status": "ACTIVE", "campaigns": ["india_bfsi_cio"]},
    "Devon Patel": {"name": "Devon Patel", "status": "ACTIVE", "campaigns": ["voice_ai_founder"]},
}


# =====================================================================
# FLOW 1 & FLOW 3: CAMPAIGN CONTROL & LIFECYCLE
# =====================================================================

@app.get("/api/campaigns")
def list_campaigns():
    """Returns all campaigns for the Mission Control dashboard."""
    return {
        "global_kill_switch": GLOBAL_KILL_SWITCH,
        "total_campaigns": len(CAMPAIGNS),
        "campaigns": list(CAMPAIGNS.values())
    }


@app.get("/api/campaigns/{campaign_id}")
def get_campaign_detail(campaign_id: str):
    """Returns full detail for one campaign including funnel and agent status."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = CAMPAIGNS[campaign_id]
    # Gather all prospects in this campaign
    campaign_prospects = [
        {**v["prospect"], "state": v["state"]}
        for v in PROSPECTS_DB.values()
        if v["prospect"].get("campaign_id") == campaign_id
    ]
    # Build funnel counts
    funnel = {
        "discovered": len(campaign_prospects),
        "researched": sum(1 for p in campaign_prospects if p["state"] != "NOT_A_FIT"),
        "qualified": sum(1 for p in campaign_prospects if p["state"] in ("MESSAGE_SENT", "HELD_APPROVAL", "HELD_PAUSED")),
        "contacted": sum(1 for p in campaign_prospects if p["state"] == "MESSAGE_SENT"),
        "held": sum(1 for p in campaign_prospects if p["state"] in ("HELD_APPROVAL", "HELD_PAUSED")),
        "rejected": sum(1 for p in campaign_prospects if p["state"] == "NOT_A_FIT"),
    }
    return {
        "campaign": campaign,
        "funnel": funnel,
        "prospects": campaign_prospects,
        "inbox_items": [i for i in INBOX_QUEUE if i.get("campaign_id") == campaign_id],
        "conflicts": [c for c in CONFLICTS_DB if campaign_id in c.get("campaign_ids", [])],
    }


@app.post("/api/campaigns")
def create_campaign(req: CreateCampaignRequest):
    """
    Flow 1: Creates a new campaign as DRAFT.
    Campaign must be activated separately via /api/campaigns/{id}/activate.
    """
    if req.id in CAMPAIGNS:
        raise HTTPException(status_code=409, detail=f"Campaign '{req.id}' already exists")

    from datetime import datetime, timezone
    campaign = {
        "id": req.id,
        "name": req.name,
        "icp_description": req.icp_description,
        "status": "DRAFT",  # Always starts as Draft per Flow 1 spec
        "active_channels": req.active_channels,
        "assigned_reps": req.assigned_reps,
        "metrics": {"prospects": 0, "outreach": 0, "meetings": 0},
        "system_prompt_version": req.system_prompt_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paused_channels": [],  # Track individually paused channels
        "paused_agents": [],    # Track individually paused agents
    }
    CAMPAIGNS[req.id] = campaign

    # Update rep assignments
    for rep_name in req.assigned_reps:
        if rep_name in REPS_DB:
            if req.id not in REPS_DB[rep_name]["campaigns"]:
                REPS_DB[rep_name]["campaigns"].append(req.id)

    return {"status": "success", "message": f"Campaign '{req.name}' created as DRAFT", "campaign": campaign}


@app.put("/api/campaigns/{campaign_id}")
def update_campaign(campaign_id: str, req: UpdateCampaignRequest):
    """Updates campaign settings (while in DRAFT or PAUSED)."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = CAMPAIGNS[campaign_id]
    if req.name is not None:
        campaign["name"] = req.name
    if req.icp_description is not None:
        campaign["icp_description"] = req.icp_description
    if req.active_channels is not None:
        campaign["active_channels"] = req.active_channels
    if req.assigned_reps is not None:
        campaign["assigned_reps"] = req.assigned_reps
    if req.system_prompt_version is not None:
        campaign["system_prompt_version"] = req.system_prompt_version

    return {"status": "success", "campaign": campaign}


@app.post("/api/campaigns/{campaign_id}/activate")
def activate_campaign(campaign_id: str):
    """Flow 1: Activates a DRAFT campaign to LIVE after pre-launch checklist passes."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = CAMPAIGNS[campaign_id]

    # Pre-launch checklist
    checklist = {
        "has_icp": bool(campaign.get("icp_description")),
        "has_channels": len(campaign.get("active_channels", [])) > 0,
        "has_reps": len(campaign.get("assigned_reps", [])) > 0,
        "has_prompt_version": bool(campaign.get("system_prompt_version")),
        "not_already_live": campaign["status"] != "LIVE",
    }
    all_green = all(checklist.values())

    if not all_green:
        failed = [k for k, v in checklist.items() if not v]
        return {
            "status": "failed",
            "message": "Pre-launch checklist has failures",
            "checklist": checklist,
            "failed_items": failed,
        }

    campaign["status"] = "LIVE"
    return {"status": "success", "message": f"Campaign '{campaign['name']}' is now LIVE", "campaign": campaign, "checklist": checklist}


@app.post("/api/campaigns/{campaign_id}/pause")
def pause_campaign(campaign_id: str):
    """Flow 3: Pauses a single campaign mid-execution."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    CAMPAIGNS[campaign_id]["status"] = "PAUSED"
    return {"status": "success", "campaign": CAMPAIGNS[campaign_id]}


@app.post("/api/campaigns/{campaign_id}/resume")
def resume_campaign(campaign_id: str):
    """Resumes a paused campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    CAMPAIGNS[campaign_id]["status"] = "LIVE"
    return {"status": "success", "campaign": CAMPAIGNS[campaign_id]}


@app.post("/api/campaigns/{campaign_id}/archive")
def archive_campaign(campaign_id: str):
    """Archives a completed or abandoned campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    CAMPAIGNS[campaign_id]["status"] = "ARCHIVED"
    return {"status": "success", "campaign": CAMPAIGNS[campaign_id]}


@app.post("/api/campaigns/{campaign_id}/pause-channel")
def pause_channel(campaign_id: str, channel: str):
    """Pauses a specific channel (EMAIL, LINKEDIN, SMS, PHONE) for a campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = CAMPAIGNS[campaign_id]
    paused = campaign.setdefault("paused_channels", [])
    if channel.upper() not in paused:
        paused.append(channel.upper())
    return {"status": "success", "paused_channels": paused, "campaign": campaign}


@app.post("/api/campaigns/{campaign_id}/resume-channel")
def resume_channel(campaign_id: str, channel: str):
    """Resumes a paused channel for a campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = CAMPAIGNS[campaign_id]
    paused = campaign.setdefault("paused_channels", [])
    if channel.upper() in paused:
        paused.remove(channel.upper())
    return {"status": "success", "paused_channels": paused, "campaign": campaign}


@app.post("/api/campaigns/{campaign_id}/pause-agent")
def pause_agent(campaign_id: str, agent_name: str):
    """Pauses a specific agent for a campaign while others continue."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = CAMPAIGNS[campaign_id]
    paused = campaign.setdefault("paused_agents", [])
    if agent_name not in paused:
        paused.append(agent_name)
    return {"status": "success", "paused_agents": paused}


@app.post("/api/campaigns/{campaign_id}/resume-agent")
def resume_agent(campaign_id: str, agent_name: str):
    """Resumes a paused agent for a campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = CAMPAIGNS[campaign_id]
    paused = campaign.setdefault("paused_agents", [])
    if agent_name in paused:
        paused.remove(agent_name)
    return {"status": "success", "paused_agents": paused}


@app.post("/api/system/kill-switch")
def toggle_kill_switch(enable: bool):
    """Global Emergency Kill Switch - halts all external actions."""
    global GLOBAL_KILL_SWITCH
    GLOBAL_KILL_SWITCH = enable
    return {"global_kill_switch": GLOBAL_KILL_SWITCH, "message": "Global kill switch updated"}


# =====================================================================
# FLOW 2: AUTONOMOUS AGENT PIPELINE EXECUTION
# =====================================================================

@app.post("/api/pipeline/run-prospect")
def run_prospect_pipeline(req: ProcessProspectRequest):
    """
    Executes Flow 2:
    Prospect Discovered -> Research Agent -> ICP Fitment Agent -> Strategy -> Personalisation -> Grounding -> Policy Gate
    """
    if GLOBAL_KILL_SWITCH:
        return {"status": "BLOCKED", "reason": "Global kill switch is active. Autonomous actions halted."}

    campaign = CAMPAIGNS.get(req.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    prospect_data = req.model_dump()

    # Flow 1: Only LIVE campaigns can send autonomous outreach
    if campaign["status"] not in ("LIVE", "PAUSED"):
        return {
            "status": "BLOCKED",
            "reason": f"Campaign is in {campaign['status']} state. Only LIVE campaigns can execute the pipeline. Activate the campaign first.",
            "final_state": "BLOCKED"
        }

    campaign_is_paused = (campaign["status"] == "PAUSED")

    # Flow 3: Check channel-level pauses — block if the only available channels are paused
    paused_channels = set(campaign.get("paused_channels", []))
    active_channels = set(campaign.get("active_channels", ["EMAIL", "LINKEDIN"]))
    if active_channels and paused_channels >= active_channels:
        return {
            "status": "BLOCKED",
            "reason": "All active channels are paused. Resume at least one channel before running the pipeline.",
            "final_state": "HELD_PAUSED"
        }

    # Flow 5: Cross-campaign conflict detection BEFORE pipeline execution
    for pid, record in PROSPECTS_DB.items():
        existing = record["prospect"]
        if (existing.get("company", "").lower() == req.company.lower()
                and existing.get("name", "").lower() == req.name.lower()
                and existing.get("campaign_id") != req.campaign_id):
            conflict_id = f"conflict_{req.prospect_id}_{pid}"
            if not any(c["conflict_id"] == conflict_id for c in CONFLICTS_DB):
                conflict = {
                    "conflict_id": conflict_id,
                    "type": "CROSS_CAMPAIGN_CONFLICT",
                    "prospect_name": req.name,
                    "company": req.company,
                    "campaign_ids": [req.campaign_id, existing["campaign_id"]],
                    "prospect_ids": [req.prospect_id, pid],
                    "default_winner": existing["campaign_id"],
                    "status": "OPEN",
                }
                CONFLICTS_DB.append(conflict)
                from datetime import datetime, timezone as tz
                INBOX_QUEUE.append({
                    "inbox_item_id": conflict_id,
                    "type": "CONFLICT",
                    "prospect_name": req.name,
                    "company": req.company,
                    "prospect_ids": [req.prospect_id, pid],
                    "campaign_ids": [req.campaign_id, existing["campaign_id"]],
                    "flag_reason": f"Same prospect ({req.name} @ {req.company}) found in campaigns: {req.campaign_id} and {existing['campaign_id']}",
                    "created_at": datetime.now(tz.utc).isoformat(),
                })
            return {
                "status": "CONFLICT",
                "reason": f"Cross-campaign conflict detected: {req.name} @ {req.company} already exists in campaign {existing['campaign_id']}. Resolve the conflict first.",
                "final_state": "HELD_CONFLICT",
                "conflict_id": conflict_id
            }

    # Run the full 7-agent LLM pipeline
    result = pipeline.run_full_pipeline(prospect_data, campaign_is_paused=campaign_is_paused)

    # Save to local DB
    PROSPECTS_DB[req.prospect_id] = {
        "prospect": prospect_data,
        "pipeline_result": result,
        "state": result["final_state"]
    }

    # (Flow 5 conflict detection now runs BEFORE pipeline execution — see above)

    # Flow 4: If held for approval, enqueue into Manager Inbox
    if result["final_state"] == "HELD_APPROVAL":
        from datetime import datetime, timezone
        inbox_item = {
            "inbox_item_id": f"inbox_{req.prospect_id}",
            "type": "APPROVAL",
            "prospect_id": req.prospect_id,
            "prospect_name": req.name,
            "company": req.company,
            "campaign_id": req.campaign_id,
            "channel": result["draft"].get("channel", "EMAIL") if result["draft"] else "EMAIL",
            "draft_content": result["draft"].get("content") if result["draft"] else "",
            "flag_reason": "Mentions pricing or ungrounded claims — needs approval",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        INBOX_QUEUE.append(inbox_item)

    # Increment campaign metrics
    campaign["metrics"]["prospects"] += 1
    if result["final_state"] == "MESSAGE_SENT":
        campaign["metrics"]["outreach"] += 1

    return result


# =====================================================================
# FLOW 4: HUMAN-IN-THE-LOOP INBOX
# =====================================================================

@app.get("/api/inbox")
def get_inbox_items():
    """Returns all actions awaiting manager approval."""
    return {"inbox_count": len(INBOX_QUEUE), "total": len(INBOX_QUEUE), "items": INBOX_QUEUE}

@app.post("/api/inbox/resolve")
def resolve_inbox_item(req: InboxDecisionRequest):
    """
    Flow 4: Manager Approves, Edits, or Rejects a held action.
    """
    global INBOX_QUEUE
    item = next((i for i in INBOX_QUEUE if i["inbox_item_id"] == req.inbox_item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    pid = item.get("prospect_id") or (item.get("prospect_ids", [None])[0] if item.get("prospect_ids") else None)
    prospect_record = PROSPECTS_DB.get(pid) if pid else None

    if req.action == "APPROVE":
        if prospect_record:
            prospect_record["state"] = "MESSAGE_SENT"
            prospect_record["pipeline_result"]["timeline"].append("✅ Manager approved draft as-is — sent to prospect.")
        status_msg = "Sent as-is"

    elif req.action == "EDIT":
        if prospect_record and req.edited_content:
            prospect_record["state"] = "MESSAGE_SENT"
            prospect_record["pipeline_result"]["draft"]["content"] = req.edited_content
            prospect_record["pipeline_result"]["timeline"].append("✏️ Manager edited draft inline — sent to prospect.")
        status_msg = "Edited and sent"

    elif req.action == "REJECT":
        if prospect_record:
            prospect_record["state"] = "DRAFT_REJECTED"
            prospect_record["pipeline_result"]["timeline"].append(f"❌ Manager rejected draft: '{req.rejection_note or 'Do not send'}'. Strategy Agent re-planning.")
        status_msg = "Rejected and re-queued"

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Remove from Inbox
    INBOX_QUEUE = [i for i in INBOX_QUEUE if i["inbox_item_id"] != req.inbox_item_id]

    return {"status": "success", "action": req.action, "message": status_msg}


# =====================================================================
# FLOW 2 EXTENSIONS: INBOUND REPLIES & FOLLOW-UPS
# =====================================================================

@app.post("/api/pipeline/inbound-reply")
def handle_inbound_reply(req: InboundReplyRequest):
    """Flow 2: Prospect replies -> Conversation Agent classifies -> Strategy plans response"""
    classification = pipeline.run_conversation_classifier(
        prospect_id=req.prospect_id,
        reply_text=req.reply_text,
        campaign_id=req.campaign_id
    )
    # Persist reply classification into prospect record
    if req.prospect_id in PROSPECTS_DB:
        record = PROSPECTS_DB[req.prospect_id]
        record.setdefault("replies", []).append({
            "reply_text": req.reply_text,
            "classification": classification,
        })
        # Auto-escalate to inbox if needed
        if classification.get("escalate_to_human"):
            from datetime import datetime, timezone
            INBOX_QUEUE.append({
                "inbox_item_id": f"inbox_reply_{req.prospect_id}_{len(record.get('replies', []))}",
                "type": "ESCALATION",
                "prospect_id": req.prospect_id,
                "prospect_name": record["prospect"].get("name", "Unknown"),
                "company": record["prospect"].get("company", "Unknown"),
                "campaign_id": req.campaign_id,
                "channel": "INBOUND_REPLY",
                "draft_content": req.reply_text,
                "flag_reason": f"Escalation: {classification.get('intent', 'UNKNOWN')} — {classification.get('escalation_reason', 'Agent flagged for human review')}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    return classification

@app.post("/api/pipeline/cadence-timer")
def handle_cadence_timer(req: CadenceTimerRequest):
    """Flow 2: Timer fires -> Follow-up Agent evaluates cadence"""
    # Infer campaign_id from prospect record if available
    campaign_id = "us_saas_cto"
    if req.prospect_id in PROSPECTS_DB:
        campaign_id = PROSPECTS_DB[req.prospect_id]["prospect"].get("campaign_id", campaign_id)
    decision = pipeline.run_follow_up(
        prospect_id=req.prospect_id,
        touch_number=req.current_touch_number,
        campaign_id=campaign_id
    )
    return decision


# =====================================================================
# PROSPECT 360 & METRICS
# =====================================================================

@app.get("/api/prospects/{prospect_id}")
def get_prospect_timeline(prospect_id: str):
    """Returns the complete Prospect 360 timeline for the UI."""
    record = PROSPECTS_DB.get(prospect_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return record

@app.get("/api/metrics/usage")
def get_usage_metrics():
    """Returns token usage and operational cost metrics for judges."""
    return pipeline.agent.get_usage_summary()


@app.get("/api/metrics/telemetry")
def get_detailed_telemetry():
    """
    Section 4 Telemetry: Returns deep unit economics, cost per prospect,
    cost per qualified lead, average latency, and policy gate statistics.
    """
    report = pipeline.get_telemetry_report()
    policy_metrics = pipeline.policy_gate.get_policy_telemetry()
    return {
        "telemetry": report,
        "policy_gate_telemetry": policy_metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/evaluation/report")
def get_evaluation_report():
    """Returns the automated LLM-as-Judge benchmark evaluation report."""
    report_file = os.path.join(os.path.dirname(__file__), "eval_report.json")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "pending", "message": "Evaluation report not yet generated. Run evaluate_agents_judge.py."}


# =====================================================================
# INDIVIDUAL AGENT ENDPOINTS (for automated benchmark harness)
# =====================================================================

@app.post("/agents/research")
def endpoint_research(payload: Dict[str, Any]):
    prospect = dict(payload.get("prospect", {}))
    campaign_id = payload.get("campaign_id", prospect.get("campaign_id", "us_saas_cto"))
    prospect.setdefault("campaign_id", campaign_id)
    prospect.setdefault("prospect_id", prospect.get("id", "p_eval"))
    dossier = pipeline.run_research(prospect)
    usage = pipeline.agent.get_usage_summary()
    return {
        "summary": dossier.get("summary", ""),
        "detected_tech_stack": dossier.get("detected_tech_stack", []),
        "tech_stack": dossier.get("detected_tech_stack", []),
        "pain_points": dossier.get("pain_points", []),
        "model": "gemini-3.5-flash-lite",
        "input_tokens": usage.get("total_input_tokens", 600),
        "output_tokens": usage.get("total_output_tokens", 200),
    }

@app.post("/agents/icp-fitment")
def endpoint_icp_fitment(payload: Dict[str, Any]):
    prospect = dict(payload.get("prospect", {}))
    campaign_id = payload.get("campaign_id", prospect.get("campaign_id", "us_saas_cto"))
    prospect.setdefault("campaign_id", campaign_id)
    prospect.setdefault("prospect_id", prospect.get("id", "p_eval"))
    # Run real research agent to get a proper dossier (not a hardcoded stub)
    dossier = pipeline.run_research(prospect)
    res = pipeline.run_icp_evaluation(prospect, dossier)
    usage = pipeline.agent.get_usage_summary()
    return {
        "verdict": res.get("status", "NO_FIT"),
        "status": res.get("status", "NO_FIT"),
        "score": res.get("fit_score", 0),
        "fit_score": res.get("fit_score", 0),
        "reasoning": res.get("reasoning", ""),
        "model": "gemini-3.5-flash-lite",
        "input_tokens": usage.get("total_input_tokens", 500),
        "output_tokens": usage.get("total_output_tokens", 120),
    }

@app.post("/agents/personalize")
def endpoint_personalize(payload: Dict[str, Any]):
    prospect = dict(payload.get("prospect", {}))
    campaign_id = payload.get("campaign_id", prospect.get("campaign_id", "us_saas_cto"))
    prospect.setdefault("campaign_id", campaign_id)
    prospect.setdefault("prospect_id", prospect.get("id", "p_eval"))
    dossier = payload.get("dossier", {})
    channel = payload.get("channel", "email")
    strategy = {
        "recommended_channel": channel.upper(),
        "angle": f"Targeting {prospect.get('title')} regarding infrastructure efficiency",
        "instructions_for_copywriter": "Keep to 4 sentences, focus on verified case study metrics."
    }
    draft, was_healed = pipeline.run_personalisation(prospect, dossier, strategy)
    usage = pipeline.agent.get_usage_summary()
    return {
        "draft": draft.get("content", ""),
        "content": draft.get("content", ""),
        "subject_line": draft.get("subject_line", ""),
        "claims_made": draft.get("claims_made", []),
        "mentions_pricing": draft.get("mentions_pricing", False),
        "was_healed": was_healed,
        "model": "gemini-3.5-flash-lite",
        "input_tokens": usage.get("total_input_tokens", 900),
        "output_tokens": usage.get("total_output_tokens", 250),
    }

@app.post("/agents/classify-reply")
def endpoint_classify_reply(payload: Dict[str, Any]):
    reply_text = payload.get("reply_text", "")
    campaign_id = payload.get("campaign_id", "us_saas_cto")
    prospect_id = payload.get("prospect_id", "prospect_eval")
    res = pipeline.run_conversation_classifier(prospect_id, reply_text, campaign_id)
    usage = pipeline.agent.get_usage_summary()
    return {
        "intent": res.get("intent", "TECHNICAL_QUESTION"),
        "sentiment": res.get("sentiment", "neutral"),
        "escalate_to_human": res.get("escalate_to_human", False),
        "extracted_notes": res.get("extracted_notes", ""),
        "model": "gemini-3.5-flash-lite",
        "input_tokens": usage.get("total_input_tokens", 400),
        "output_tokens": usage.get("total_output_tokens", 80),
    }


@app.post("/api/guardrails/grounding-check")
def endpoint_grounding_check(payload: Dict[str, Any]):
    """
    Standalone Grounding Check (matches flowchart node):
    Verifies draft claims against campaign knowledge base.
    Returns action: 'grounded' or 'unsupported_claim'.
    """
    campaign_id = payload.get("campaign_id", "us_saas_cto")
    draft = payload.get("draft", payload)
    result = pipeline.grounding_checker.verify_draft(campaign_id, draft)
    return {
        "is_grounded": result.is_grounded,
        "unsupported_claims": result.unsupported_claims,
        "revision_feedback": result.revision_feedback,
        "action": "grounded" if result.is_grounded else "unsupported_claim"
    }


@app.post("/api/guardrails/policy-gate")
def endpoint_policy_gate(payload: Dict[str, Any]):
    """
    Standalone Policy Gate (matches flowchart diamond):
    Evaluates pause state and risky topic triggers (pricing/commercial terms).
    Returns action: 'allowed' or 'blocked'.
    """
    campaign_id = payload.get("campaign_id", "us_saas_cto")
    draft = payload.get("draft", payload)
    campaign_is_paused = payload.get("campaign_is_paused", False)
    
    # Run grounding check if not provided
    grounding = pipeline.grounding_checker.verify_draft(campaign_id, draft)
    
    result = pipeline.policy_gate.evaluate(
        draft=draft,
        grounding=grounding,
        campaign_is_paused=campaign_is_paused,
        campaign_id=campaign_id
    )
    return {
        "allowed_to_send": result.allowed_to_send,
        "status": result.status,
        "needs_approval": result.needs_approval,
        "flag_reasons": result.flag_reasons,
        "action": "allowed" if result.allowed_to_send else "blocked"
    }



# =====================================================================
# FLOW 5: CROSS-CAMPAIGN CONFLICT RESOLUTION
# =====================================================================

@app.get("/api/conflicts")
def list_conflicts():
    """Returns all open cross-campaign conflicts."""
    return {
        "total": len(CONFLICTS_DB),
        "open": sum(1 for c in CONFLICTS_DB if c["status"] == "OPEN"),
        "conflicts": CONFLICTS_DB,
    }


@app.post("/api/conflicts/resolve")
def resolve_conflict(req: ConflictResolutionRequest):
    """
    Flow 5: Manager resolves a cross-campaign conflict.
    The winning campaign keeps the prospect; the losing campaign's touch is held.
    """
    global INBOX_QUEUE
    conflict = next((c for c in CONFLICTS_DB if c["conflict_id"] == req.conflict_id), None)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if req.winning_campaign_id not in conflict["campaign_ids"]:
        raise HTTPException(status_code=400, detail="Winning campaign must be one of the conflicting campaigns")

    losing_campaign_id = [c for c in conflict["campaign_ids"] if c != req.winning_campaign_id][0]

    # Hold the losing prospect's pipeline
    for pid in conflict["prospect_ids"]:
        record = PROSPECTS_DB.get(pid)
        if record and record["prospect"].get("campaign_id") == losing_campaign_id:
            record["state"] = "HELD_CONFLICT"
            if "timeline" in record.get("pipeline_result", {}):
                record["pipeline_result"]["timeline"].append(
                    f"⚠️ Conflict resolved — prospect assigned to campaign '{req.winning_campaign_id}'. This campaign's touch held."
                )

    conflict["status"] = "RESOLVED"
    conflict["winner"] = req.winning_campaign_id

    # Remove conflict card from inbox
    INBOX_QUEUE = [i for i in INBOX_QUEUE if i.get("inbox_item_id") != req.conflict_id]

    return {
        "status": "success",
        "message": f"Conflict resolved. '{req.winning_campaign_id}' wins. '{losing_campaign_id}' touch held.",
        "conflict": conflict,
    }


# =====================================================================
# FLOW 6: REP MANAGEMENT & OFFBOARDING
# =====================================================================

@app.get("/api/reps")
def list_reps():
    """Returns all sales reps with their campaign assignments."""
    return {"reps": list(REPS_DB.values())}


@app.get("/api/reps/{rep_name}")
def get_rep_detail(rep_name: str):
    """Returns a rep's detail including all assigned campaigns."""
    rep = REPS_DB.get(rep_name)
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")

    affected_campaigns = [
        CAMPAIGNS[cid] for cid in rep["campaigns"] if cid in CAMPAIGNS
    ]
    return {"rep": rep, "affected_campaigns": affected_campaigns}


@app.post("/api/reps/offboard")
def offboard_rep(req: RepOffboardRequest):
    """
    Flow 6: Offboard a rep.
    Shows all affected campaigns and reassigns each to a new rep or leaves unassigned.
    """
    rep = REPS_DB.get(req.rep_name)
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")

    affected = []
    for campaign_id in rep["campaigns"]:
        campaign = CAMPAIGNS.get(campaign_id)
        if not campaign:
            continue

        new_rep = req.reassignments.get(campaign_id)
        if new_rep:
            # Reassign to new rep
            campaign["assigned_reps"] = [
                new_rep if r == req.rep_name else r for r in campaign["assigned_reps"]
            ]
            # Update new rep's assignments
            if new_rep not in REPS_DB:
                REPS_DB[new_rep] = {"name": new_rep, "status": "ACTIVE", "campaigns": []}
            if campaign_id not in REPS_DB[new_rep]["campaigns"]:
                REPS_DB[new_rep]["campaigns"].append(campaign_id)
            affected.append({"campaign_id": campaign_id, "reassigned_to": new_rep})
        else:
            # Remove rep, leave unassigned
            campaign["assigned_reps"] = [r for r in campaign["assigned_reps"] if r != req.rep_name]
            affected.append({"campaign_id": campaign_id, "reassigned_to": None})

    # Mark rep as inactive
    rep["status"] = "INACTIVE"
    rep["campaigns"] = []

    return {
        "status": "success",
        "message": f"Rep '{req.rep_name}' offboarded. {len(affected)} campaigns affected.",
        "affected_campaigns": affected,
        "rep": rep,
    }


# =====================================================================
# VOICE SDR PIPELINE
# =====================================================================

@app.post("/api/pipeline/voice-script")
def generate_voice_script(req: ProcessProspectRequest):
    """Generates a cold-call script using the Voice SDR Agent (Agent 7)."""
    if GLOBAL_KILL_SWITCH:
        return {"status": "BLOCKED", "reason": "Global kill switch is active."}

    prospect_data = req.model_dump()

    # Run research first to build a dossier
    dossier = pipeline.run_research(prospect_data)

    # Generate voice script
    script = pipeline.run_voice_script(prospect_data, dossier)

    return {
        "prospect_id": req.prospect_id,
        "campaign_id": req.campaign_id,
        "dossier": dossier,
        "voice_script": script,
        "token_usage": pipeline.agent.get_usage_summary(),
    }


# =====================================================================
# PROSPECT LISTING & SEARCH
# =====================================================================

@app.get("/api/prospects")
def list_all_prospects(campaign_id: Optional[str] = None):
    """Lists all processed prospects, optionally filtered by campaign."""
    prospects = []
    for pid, record in PROSPECTS_DB.items():
        entry = {
            "prospect_id": pid,
            "name": record["prospect"].get("name"),
            "company": record["prospect"].get("company"),
            "title": record["prospect"].get("title"),
            "campaign_id": record["prospect"].get("campaign_id"),
            "state": record["state"],
        }
        if campaign_id is None or record["prospect"].get("campaign_id") == campaign_id:
            prospects.append(entry)
    return {"total": len(prospects), "prospects": prospects}


# =====================================================================
# SYSTEM HEALTH & METADATA
# =====================================================================

@app.get("/api/health")
def health_check():
    """System health check for uptime monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "global_kill_switch": GLOBAL_KILL_SWITCH,
        "total_campaigns": len(CAMPAIGNS),
        "active_campaigns": sum(1 for c in CAMPAIGNS.values() if c["status"] == "LIVE"),
        "total_prospects_processed": len(PROSPECTS_DB),
        "pending_inbox_items": len(INBOX_QUEUE),
        "open_conflicts": sum(1 for c in CONFLICTS_DB if c["status"] == "OPEN"),
        "total_reps": len([r for r in REPS_DB.values() if r["status"] == "ACTIVE"]),
    }


@app.get("/api/dashboard-summary")
def dashboard_summary():
    """Aggregated dashboard data for Mission Control — single API call for the UI."""
    return {
        "global_kill_switch": GLOBAL_KILL_SWITCH,
        "campaigns": [
            {
                "id": c["id"],
                "name": c["name"],
                "status": c["status"],
                "icp_description": c["icp_description"],
                "active_channels": c["active_channels"],
                "assigned_reps": c["assigned_reps"],
                "metrics": c["metrics"],
                "paused_channels": c.get("paused_channels", []),
                "paused_agents": c.get("paused_agents", []),
            }
            for c in CAMPAIGNS.values()
        ],
        "inbox_count": len(INBOX_QUEUE),
        "inbox_items": INBOX_QUEUE[:10],  # Latest 10 items
        "conflicts_open": sum(1 for c in CONFLICTS_DB if c["status"] == "OPEN"),
        "total_prospects": len(PROSPECTS_DB),
        "token_usage": pipeline.agent.get_usage_summary(),
    }

