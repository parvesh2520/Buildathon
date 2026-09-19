from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
import uuid


class ProspectCreate(BaseModel):
    name: str
    email: str
    title: str
    company: str
    domain: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    companySize: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedinUrl: Optional[str] = None
    notes: Optional[str] = None
    campaign_id: Optional[str] = None
    campaignId: Optional[str] = None
    status: Optional[str] = "FIT"

    @model_validator(mode="before")
    @classmethod
    def sync_camel_snake(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "campaignId" in data and not data.get("campaign_id"):
                data["campaign_id"] = data["campaignId"]
            elif "campaign_id" in data and not data.get("campaignId"):
                data["campaignId"] = data["campaign_id"]

            if "companySize" in data and not data.get("company_size"):
                data["company_size"] = data["companySize"]
            elif "company_size" in data and not data.get("companySize"):
                data["companySize"] = data["company_size"]

            if "linkedinUrl" in data and not data.get("linkedin_url"):
                data["linkedin_url"] = data["linkedinUrl"]
            elif "linkedin_url" in data and not data.get("linkedinUrl"):
                data["linkedinUrl"] = data["linkedin_url"]
        return data


class Prospect(ProspectCreate):
    id: str
    campaignName: Optional[str] = None
    icpScore: Optional[int] = 85
    channel: Optional[str] = "EMAIL"
    lastActivity: Optional[str] = "Just now"


# ---------------------------------------------------------------------------
# Persistent store — backed by JSON file in backend/data/prospects.json
# ---------------------------------------------------------------------------
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PROSPECTS_FILE = DATA_DIR / "prospects.json"

_DEFAULT_PROSPECTS: dict[str, Prospect] = {
    "parvesh_email": Prospect(
        id="parvesh_email",
        name="Parvesh Kumar (Email Test)",
        email="parvesh2520@gmail.com",
        title="CTO",
        company="CloudScale Technologies",
        domain="cloudscale.io",
        location="San Francisco, CA",
        company_size="150 employees",
        companySize="150 employees",
        campaign_id="us_saas_cto",
        campaignId="us_saas_cto",
        campaignName="US SaaS CTOs",
        status="FIT",
        channel="EMAIL",
        notes="Evaluated by ICP agent. Interested in developer velocity. Reach out via Email.",
    ),
    "parvesh_sms": Prospect(
        id="parvesh_sms",
        name="Parvesh Kumar (SMS Test)",
        email="parvesh2520@gmail.com",
        phone="+917419045750",
        title="Chief Information Officer (CIO)",
        company="FinTech Wave Bank",
        domain="fintechwave.in",
        location="Mumbai, India",
        company_size="1,200 employees",
        companySize="1,200 employees",
        campaign_id="india_bfsi_cio",
        campaignId="india_bfsi_cio",
        campaignName="India BFSI CIOs",
        status="FIT",
        channel="SMS",
        notes="CIO at BFSI enterprise. Prefers mobile SMS communication. Fast follow-up via SMS text message.",
    ),
    "parvesh_voice": Prospect(
        id="parvesh_voice",
        name="Parvesh Kumar (Voice Call Test)",
        email="parvesh2520@gmail.com",
        phone="+917419045750",
        title="Chief Information Officer (CIO)",
        company="FinTech Wave Bank",
        domain="fintechwave.in",
        location="Mumbai, India",
        company_size="1,200 employees",
        companySize="1,200 employees",
        campaign_id="india_bfsi_cio",
        campaignId="india_bfsi_cio",
        campaignName="India BFSI CIOs",
        status="FIT",
        channel="PHONE",
        notes="CIO at BFSI enterprise. Outreach Strategy Agent selected PHONE call for executive briefing. Connects directly to SDR Voice Script Agent.",
    ),
    "p1": Prospect(
        id="p1",
        name="James Carter",
        email="james.carter@cloudpeak.io",
        title="CTO",
        company="CloudPeak",
        domain="cloudpeak.io",
        location="San Francisco, CA",
        company_size="120 employees",
        companySize="120 employees",
        campaign_id="us_saas_cto",
        campaignId="us_saas_cto",
        campaignName="US SaaS CTOs",
        status="FIT",
        notes="Evaluated by ICP agent. Interested in developer productivity automation.",
    ),
    "p2": Prospect(
        id="p2",
        name="Priya Nair",
        email="priya.nair@fintechwave.in",
        title="CIO",
        company="FinTech Wave",
        domain="fintechwave.in",
        location="Mumbai, India",
        company_size="2,400 employees",
        companySize="2,400 employees",
        campaign_id="india_bfsi_cio",
        campaignId="india_bfsi_cio",
        campaignName="India BFSI CIOs",
        status="FIT",
        notes="Interested in enterprise AI security and compliance.",
    ),
    "p3": Prospect(
        id="p3",
        name="Alex Reid",
        email="alex@voicenative.ai",
        title="CEO & Co-founder",
        company="VoiceNative",
        domain="voicenative.ai",
        location="London, UK",
        company_size="8 employees",
        companySize="8 employees",
        campaign_id="voice_ai_founder",
        campaignId="voice_ai_founder",
        campaignName="Voice AI Founders",
        status="FIT",
        notes="Voice AI startup founder looking for infrastructure solutions.",
    ),
    "p4": Prospect(
        id="p4",
        name="Sarah Kim",
        email="sarah.kim@growthspark.com",
        title="VP Engineering",
        company="GrowthSpark",
        domain="growthspark.com",
        location="Austin, TX",
        company_size="340 employees",
        companySize="340 employees",
        campaign_id="us_saas_cto",
        campaignId="us_saas_cto",
        campaignName="US SaaS CTOs",
        status="FIT",
        notes="Scaling engineering team, focused on pipeline velocity.",
    ),
    "p6": Prospect(
        id="p6",
        name="Michael Torres",
        email="mkt@datanest.io",
        title="Head of Engineering",
        company="DataNest",
        domain="datanest.io",
        location="New York, NY",
        company_size="85 employees",
        companySize="85 employees",
        campaign_id="us_saas_cto",
        campaignId="us_saas_cto",
        campaignName="US SaaS CTOs",
        status="NO_FIT",
        notes="ICP mismatch: Budget freeze, not evaluating new vendors.",
    ),
}


def _load_prospects() -> dict[str, Prospect]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    loaded: dict[str, Prospect] = {}
    if PROSPECTS_FILE.exists():
        try:
            with open(PROSPECTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        p = Prospect(**item)
                        loaded[p.id] = p
        except Exception:
            pass

    # Ensure all defaults are present
    for k, v in _DEFAULT_PROSPECTS.items():
        if k not in loaded:
            loaded[k] = v

    return loaded


def _save_prospects(store: dict[str, Prospect]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(PROSPECTS_FILE, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in store.values()], f, indent=2)
    except Exception:
        pass


_prospects: dict[str, Prospect] = _load_prospects()
_save_prospects(_prospects)


def get_all_prospects() -> list[Prospect]:
    from app.services.supabase_db import sb_get_prospects
    try:
        remote = sb_get_prospects()
        if remote is not None:
            new_store: dict[str, Prospect] = {}
            for item in remote:
                p_id = item.get("id")
                if p_id:
                    new_store[p_id] = Prospect(
                        id=p_id,
                        campaign_id=item.get("campaign_id"),
                        campaignId=item.get("campaign_id"),
                        name=item.get("name"),
                        email=item.get("email"),
                        phone=item.get("phone"),
                        linkedin_url=item.get("linkedin_url"),
                        linkedinUrl=item.get("linkedin_url"),
                        title=item.get("title"),
                        company=item.get("company"),
                        domain=item.get("domain"),
                        location=item.get("location"),
                        company_size=item.get("company_size"),
                        companySize=item.get("company_size"),
                        status=item.get("status", "FIT"),
                        channel=item.get("channel", "EMAIL"),
                        icpScore=item.get("icp_score", 85),
                        notes=item.get("notes"),
                    )
            _prospects.clear()
            _prospects.update(new_store)
            _save_prospects(_prospects)
            return list(_prospects.values())
    except Exception:
        pass
    return list(_prospects.values())


def get_prospect(prospect_id: str) -> Optional[Prospect]:
    from app.services.supabase_db import sb_get_prospect
    try:
        remote = sb_get_prospect(prospect_id)
        if remote:
            p = Prospect(
                id=remote["id"],
                campaign_id=remote.get("campaign_id"),
                campaignId=remote.get("campaign_id"),
                name=remote.get("name"),
                email=remote.get("email"),
                phone=remote.get("phone"),
                linkedin_url=remote.get("linkedin_url"),
                linkedinUrl=remote.get("linkedin_url"),
                title=remote.get("title"),
                company=remote.get("company"),
                domain=remote.get("domain"),
                location=remote.get("location"),
                company_size=remote.get("company_size"),
                companySize=remote.get("company_size"),
                status=remote.get("status", "FIT"),
                channel=remote.get("channel", "EMAIL"),
                icpScore=remote.get("icp_score", 85),
                notes=remote.get("notes"),
            )
            _prospects[p.id] = p
            return p
        elif remote is not None:
            if prospect_id in _prospects:
                _prospects.pop(prospect_id, None)
                _save_prospects(_prospects)
            return None
    except Exception:
        pass
    return _prospects.get(prospect_id)


def delete_prospect(prospect_id: str) -> bool:
    from app.services.supabase_db import sb_delete_prospect
    _prospects.pop(prospect_id, None)
    _save_prospects(_prospects)
    try:
        sb_delete_prospect(prospect_id)
    except Exception:
        pass
    return True


def create_prospect(data: ProspectCreate) -> Prospect:
    from app.models.campaign import get_campaign
    from app.services.supabase_db import sb_upsert_prospect
    c = get_campaign(data.campaign_id) if data.campaign_id else None
    c_name = c.name if c else None
    dumped = data.model_dump()
    dumped["campaignId"] = data.campaign_id
    dumped["campaignName"] = c_name
    dumped["companySize"] = data.company_size
    prospect = Prospect(id=str(uuid.uuid4()), **dumped)
    _prospects[prospect.id] = prospect
    _save_prospects(_prospects)

    try:
        db_payload = {
            "id": prospect.id,
            "campaign_id": prospect.campaign_id or prospect.campaignId,
            "name": prospect.name,
            "email": prospect.email,
            "phone": prospect.phone,
            "linkedin_url": prospect.linkedin_url or prospect.linkedinUrl,
            "title": prospect.title,
            "company": prospect.company,
            "domain": prospect.domain,
            "location": prospect.location,
            "company_size": prospect.company_size or prospect.companySize,
            "status": "FIT",
            "channel": prospect.channel or "EMAIL",
            "icp_score": prospect.icpScore or 0,
            "notes": prospect.notes,
        }
        sb_upsert_prospect(db_payload)
    except Exception:
        pass

    return prospect


def update_prospect_status(prospect_id: str, status: str) -> Optional[Prospect]:
    from app.services.supabase_db import sb_update_prospect_status
    prospect = _prospects.get(prospect_id)
    if prospect is None:
        return None
    updated = prospect.model_copy(update={"status": status})
    _prospects[prospect_id] = updated
    _save_prospects(_prospects)

    try:
        norm_st = "CONTACTED" if status == "SENT" else ("REVIEW" if status == "IN_PROGRESS" else status)
        sb_update_prospect_status(prospect_id, norm_st)
    except Exception:
        pass

    return updated
