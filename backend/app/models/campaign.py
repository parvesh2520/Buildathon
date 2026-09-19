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
