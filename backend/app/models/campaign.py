from pydantic import BaseModel
from typing import Literal, Optional
import uuid

CampaignStatus = Literal["LIVE", "PAUSED"]


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icp: str
    status: CampaignStatus = "PAUSED"
    enabled_channels: list[str] = ["EMAIL", "SMS", "LINKEDIN", "PHONE"]


class Campaign(CampaignCreate):
    id: str


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


# ---------------------------------------------------------------------------
# Persistent store — backed by JSON file in backend/data/campaigns.json
# ---------------------------------------------------------------------------
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.json"

_DEFAULT_CAMPAIGNS: dict[str, Campaign] = {
    "us_saas_cto": Campaign(
        id="us_saas_cto",
        name="US SaaS CTOs",
        description="Targeting CTOs at US-based SaaS companies",
        icp="CTO / VP Engineering at SaaS companies, 50–500 employees, US-based",
        status="LIVE",
    ),
    "india_bfsi_cio": Campaign(
        id="india_bfsi_cio",
        name="India BFSI CIOs",
        description="Targeting CIOs at Indian BFSI enterprises",
        icp="CIO / IT Director at BFSI companies, 1000+ employees, India",
        status="LIVE",
    ),
    "voice_ai_founder": Campaign(
        id="voice_ai_founder",
        name="Voice AI Founders",
        description="Targeting founders building Voice AI products",
        icp="Founder / CEO at early-stage Voice AI startups",
        status="PAUSED",
    ),
}


def _load_campaigns() -> dict[str, Campaign]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    loaded: dict[str, Campaign] = {}
    if CAMPAIGNS_FILE.exists():
        try:
            with open(CAMPAIGNS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        c = Campaign(**item)
                        loaded[c.id] = c
        except Exception:
            pass
    for k, v in _DEFAULT_CAMPAIGNS.items():
        if k not in loaded:
            loaded[k] = v
    return loaded


def _save_campaigns(store: dict[str, Campaign]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CAMPAIGNS_FILE, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in store.values()], f, indent=2)
    except Exception:
        pass


_campaigns: dict[str, Campaign] = _load_campaigns()
_save_campaigns(_campaigns)


def get_all_campaigns() -> list[Campaign]:
    from app.services.supabase_db import sb_get_campaigns
    try:
        remote = sb_get_campaigns()
        if remote is not None and len(remote) > 0:
            new_store = {item["id"]: Campaign(**item) for item in remote}
            _campaigns.clear()
            _campaigns.update(new_store)
            _save_campaigns(_campaigns)
            return list(_campaigns.values())
    except Exception:
        pass
    return list(_campaigns.values())


def get_campaign(campaign_id: str) -> Optional[Campaign]:
    from app.services.supabase_db import sb_get_campaign
    try:
        remote = sb_get_campaign(campaign_id)
        if remote:
            c = Campaign(**remote)
            _campaigns[c.id] = c
            return c
        elif remote is not None:
            if campaign_id in _campaigns:
                _campaigns.pop(campaign_id, None)
                _save_campaigns(_campaigns)
            return None
    except Exception:
        pass
    return _campaigns.get(campaign_id)


def create_campaign(data: CampaignCreate) -> Campaign:
    from app.services.supabase_db import sb_upsert_campaign
    campaign = Campaign(id=str(uuid.uuid4()), **data.model_dump())
    _campaigns[campaign.id] = campaign
    _save_campaigns(_campaigns)
    try:
        sb_upsert_campaign(campaign.model_dump())
    except Exception:
        pass
    return campaign


def update_campaign_status(campaign_id: str, status: CampaignStatus) -> Optional[Campaign]:
    from app.services.supabase_db import sb_upsert_campaign
    campaign = _campaigns.get(campaign_id)
    if campaign is None:
        return None
    updated = campaign.model_copy(update={"status": status})
    _campaigns[campaign_id] = updated
    _save_campaigns(_campaigns)
    try:
        sb_upsert_campaign(updated.model_dump())
    except Exception:
        pass
    return updated


# ---------------------------------------------------------------------------
# Prompt / Harness Management & Versioning (Section 3 & 4)
# ---------------------------------------------------------------------------
_campaign_prompts: dict[str, list[dict]] = {}

_DEFAULT_PROMPTS = {
    "system_prompt": "You are an autonomous AI Sales Development Representative (SDR) orchestrating enterprise outreach for CloudPeak. Maintain strict professional tonality, address prospect pain points, never fabricate false case studies, and observe channel-specific constraints.",
    "agent_prompts": {
        "icp_fitment": "Evaluate the lead against the target ICP: CTO/VP Engineering at 50-500 employee SaaS companies. Score fit from 0 to 100 with clear justification.",
        "lead_research": "Analyze company website and detect tech stack, developer infrastructure pain points, and recent headcount growth.",
        "outreach_strategy": "Select the optimal communication channel (Email, LinkedIn, SMS, Voice AI) based on prospect title, availability of verified phone/LinkedIn, and urgency.",
        "personalisation": "Draft a personalized outreach message under 150 words referencing specific technical signals and offering a low-friction 10-minute executive briefing.",
        "conversation": "Analyze incoming prospect responses: categorize as Positive, Objection, or Unsubscribe. Generate objection handling response using RAG playbook.",
        "follow_up": "Determine next follow-up cadence (3-day or 7-day spacing). Cap outreach at 4 touchpoints maximum.",
        "voice_sdr": "Synthesize SDR phone conversation script for Twilio call. Open with developer productivity benchmark and handle gatekeeper objections.",
    },
    "version": "v1.0",
    "author": "System Admin",
    "updated_at": "2026-09-18T12:00:00Z",
}

def get_campaign_prompts(campaign_id: str) -> dict:
    if campaign_id not in _campaign_prompts or len(_campaign_prompts[campaign_id]) == 0:
        _campaign_prompts[campaign_id] = [dict(_DEFAULT_PROMPTS)]
    history = _campaign_prompts[campaign_id]
    current = history[-1]
    return {
        "campaign_id": campaign_id,
        "current": current,
        "history": history,
        "version_count": len(history),
    }

def save_campaign_prompts(campaign_id: str, system_prompt: str, agent_prompts: dict, author: str = "Campaign Manager") -> dict:
    from datetime import datetime, timezone
    if campaign_id not in _campaign_prompts:
        _campaign_prompts[campaign_id] = [dict(_DEFAULT_PROMPTS)]
    history = _campaign_prompts[campaign_id]
    next_ver = f"v{len(history) + 1}.0"
    new_entry = {
        "system_prompt": system_prompt,
        "agent_prompts": agent_prompts,
        "version": next_ver,
        "author": author,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    history.append(new_entry)
    return {
        "campaign_id": campaign_id,
        "current": new_entry,
        "history": history,
        "version_count": len(history),
    }

def rollback_campaign_prompts(campaign_id: str, target_version: str) -> dict:
    if campaign_id not in _campaign_prompts:
        _campaign_prompts[campaign_id] = [dict(_DEFAULT_PROMPTS)]
    history = _campaign_prompts[campaign_id]
    matched = next((h for h in history if h["version"] == target_version), None)
    if not matched:
        raise ValueError(f"Version {target_version} not found")
    # Duplicate matched as a new active version entry with rollback stamp
    from datetime import datetime, timezone
    rolled_back = {
        "system_prompt": matched["system_prompt"],
        "agent_prompts": matched["agent_prompts"],
        "version": f"v{len(history) + 1}.0 (Rollback to {target_version})",
        "author": "Rollback Action",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    history.append(rolled_back)
    return {
        "campaign_id": campaign_id,
        "current": rolled_back,
        "history": history,
    }


# ---------------------------------------------------------------------------
# Sales Representative Assignment & Offboarding (Section 3)
# ---------------------------------------------------------------------------
_campaign_reps: dict[str, list[dict]] = {
    "us_saas_cto": [
        {
            "id": "rep-1",
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@autonomous-sdr.ai",
            "role": "Senior Enterprise SDR",
            "channels": ["EMAIL", "LINKEDIN"],
            "daily_quota": 50,
            "working_hours": "09:00 - 18:00 EST",
            "status": "ACTIVE",
        },
        {
            "id": "rep-2",
            "name": "Alex Rivera",
            "email": "alex.rivera@autonomous-sdr.ai",
            "role": "Outbound Specialist",
            "channels": ["PHONE", "SMS"],
            "daily_quota": 40,
            "working_hours": "08:00 - 17:00 PST",
            "status": "ACTIVE",
        },
    ],
    "india_bfsi_cio": [
        {
            "id": "rep-3",
            "name": "Rahul Verma",
            "email": "rahul.verma@autonomous-sdr.ai",
            "role": "Enterprise Account Exec",
            "channels": ["EMAIL", "LINKEDIN", "PHONE"],
            "daily_quota": 45,
            "working_hours": "10:00 - 19:00 IST",
            "status": "ACTIVE",
        }
    ],
}

def get_campaign_reps(campaign_id: str) -> list[dict]:
    return _campaign_reps.get(campaign_id, [
        {
            "id": "rep-default",
            "name": "Taylor Smith",
            "email": "taylor.smith@autonomous-sdr.ai",
            "role": "Commercial SDR",
            "channels": ["EMAIL", "LINKEDIN"],
            "daily_quota": 50,
            "working_hours": "09:00 - 17:00 EST",
            "status": "ACTIVE",
        }
    ])

def assign_campaign_rep(campaign_id: str, rep_data: dict) -> dict:
    rep_id = rep_data.get("id") or f"rep-{uuid.uuid4().hex[:6]}"
    entry = {
        "id": rep_id,
        "name": rep_data.get("name", "Sales Rep"),
        "email": rep_data.get("email", ""),
        "role": rep_data.get("role", "SDR"),
        "channels": rep_data.get("channels", ["EMAIL", "LINKEDIN"]),
        "daily_quota": rep_data.get("daily_quota", 50),
        "working_hours": rep_data.get("working_hours", "09:00 - 17:00"),
        "status": "ACTIVE",
    }
    _campaign_reps.setdefault(campaign_id, []).append(entry)
    return entry

def offboard_campaign_rep(campaign_id: str, rep_id: str, reassign_to_id: Optional[str] = None) -> dict:
    reps = _campaign_reps.get(campaign_id, [])
    for r in reps:
        if r["id"] == rep_id:
            r["status"] = "OFFBOARDED"
    return {
        "offboarded_rep_id": rep_id,
        "reassigned_to_id": reassign_to_id,
        "campaign_id": campaign_id,
        "message": f"Rep {rep_id} offboarded and prospects safely reassigned.",
    }


# ---------------------------------------------------------------------------
# Campaign Duplication / A/B Testing Variant (Section 3 - Stretch)
# ---------------------------------------------------------------------------
def duplicate_campaign(campaign_id: str, variant_name: Optional[str] = None) -> Campaign:
    source = get_campaign(campaign_id)
    if not source:
        raise ValueError(f"Campaign {campaign_id} not found")
    
    new_id = f"{campaign_id}_var_{uuid.uuid4().hex[:4]}"
    new_name = variant_name or f"{source.name} (Variant B)"
    
    duplicated = Campaign(
        id=new_id,
        name=new_name,
        description=f"A/B Testing Variant cloned from {source.name}. Benchmarks alternative prompts and outreach mix.",
        icp=source.icp,
        status="PAUSED",
        enabled_channels=source.enabled_channels,
    )
    _campaigns[duplicated.id] = duplicated
    _save_campaigns(_campaigns)
    
    # Clone prompts
    prompts_data = get_campaign_prompts(campaign_id)
    _campaign_prompts[duplicated.id] = [dict(prompts_data["current"])]
    
    return duplicated
