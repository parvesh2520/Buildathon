import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ProspectCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    email: Optional[str] = None
    title: Optional[str] = "Executive"
    company: Optional[str] = "Company"
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
    channel: Optional[str] = None
    status: Optional[str] = "DISCOVERED"
    discovery_source: Optional[str] = "Manual"
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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
    status: Optional[str] = "DISCOVERED"


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
        return loaded

    # First run: seed defaults
    for k, v in _DEFAULT_PROSPECTS.items():
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


def _detect_channel(notes: Optional[str] = None, phone: Optional[str] = None, explicit_channel: Optional[str] = None) -> str:
    """Intelligently detects intended outreach channel from user notes, phone availability, or explicit setting."""
    if explicit_channel and str(explicit_channel).strip().upper() in ["EMAIL", "SMS", "LINKEDIN", "PHONE", "VOICE"]:
        ch = str(explicit_channel).strip().upper()
        return "PHONE" if ch == "VOICE" else ch
    n = (notes or "").lower()
    if "sms" in n:
        return "SMS"
    if "call" in n or "phone" in n or "voice" in n:
        return "PHONE"
    if "linkedin" in n:
        return "LINKEDIN"
    return "EMAIL"


def get_all_prospects() -> list[Prospect]:
    global _prospects
    try:
        fresh = _load_prospects()
        _prospects.update(fresh)
    except Exception:
        pass
    from app.services.supabase_db import sb_get_prospects
    try:
        remote = sb_get_prospects()
        if remote is not None:
            from app.models.campaign import get_all_campaigns
            try:
                camp_map = {c.id: c.name for c in get_all_campaigns()}
            except Exception:
                camp_map = {}

            new_store: dict[str, Prospect] = {}
            for item in remote:
                p_id = item.get("id")
                if p_id:
                    ch = item.get("channel")
                    notes = item.get("notes") or ""
                    # If channel is null or default EMAIL, check if notes or phone indicate SMS/PHONE
                    if not ch or ch == "EMAIL":
                        ch = _detect_channel(notes, item.get("phone"), ch)
                    existing_local = _prospects.get(p_id)
                    raw_data = existing_local.raw_data if existing_local else None

                    c_id = item.get("campaign_id")
                    c_name = camp_map.get(c_id) if c_id else None

                    new_store[p_id] = Prospect(
                        id=p_id,
                        campaign_id=c_id,
                        campaignId=c_id,
                        campaignName=c_name,
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
                        channel=ch,
                        icpScore=item.get("icp_score", 85),
                        notes=item.get("notes"),
                        raw_data=raw_data,
                    )
            _prospects = new_store
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
            ch = remote.get("channel")
            notes = remote.get("notes") or ""
            if not ch or ch == "EMAIL":
                ch = _detect_channel(notes, remote.get("phone"), ch)
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
                channel=ch,
                icpScore=remote.get("icp_score", 85),
                notes=remote.get("notes"),
            )
            _prospects[p.id] = p
            return p
    except Exception:
        pass

    if prospect_id not in _prospects:
        try:
            fresh = _load_prospects()
            if prospect_id in fresh:
                _prospects[prospect_id] = fresh[prospect_id]
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
    detected_ch = _detect_channel(data.notes, data.phone, data.channel)
    dumped["channel"] = detected_ch
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
            "channel": detected_ch,
            "icp_score": prospect.icpScore or 0,
            "notes": prospect.notes,
        }
        sb_upsert_prospect(db_payload)
    except Exception:
        pass

    return prospect


def update_prospect_status(
    prospect_id: str,
    status: str,
    channel: Optional[str] = None,
    icp_score: Optional[int] = None,
) -> Optional[Prospect]:
    from app.services.supabase_db import sb_update_prospect_status
    prospect = _prospects.get(prospect_id)
    if prospect is None:
        return None
    updates: dict[str, Any] = {"status": status}
    if channel:
        norm_ch = channel.strip().upper()
        updates["channel"] = "PHONE" if norm_ch == "VOICE" else norm_ch
    if icp_score is not None:
        updates["icpScore"] = icp_score

    updated = prospect.model_copy(update=updates)
    _prospects[prospect_id] = updated
    _save_prospects(_prospects)

    try:
        norm_st = "CONTACTED" if status == "SENT" else ("REVIEW" if status == "IN_PROGRESS" else status)
        sb_update_prospect_status(
            prospect_id,
            status=norm_st,
            channel=updates.get("channel"),
            icp_score=icp_score,
        )
    except Exception:
        pass

    return updated


def get_prospects_by_campaign(campaign_id: str, status: Optional[str] = None) -> list[Prospect]:
    """Returns all prospects belonging to a specific campaign, optionally filtered by status."""
    all_p = get_all_prospects()
    matches = [p for p in all_p if (p.campaign_id == campaign_id or p.campaignId == campaign_id)]
    if status:
        st_filter = status.strip().upper()
        matches = [p for p in matches if (p.status or "").strip().upper() == st_filter]
    return matches


def upsert_discovered_prospects(
    campaign_id: str,
    prospects_data: list[dict],
    source: Optional[str] = None,
) -> dict:
    """
    Ingests a list of prospects discovered by an autonomous discovery agent.
    Deduplicates within the campaign using email, linkedin_url, or (name, company).
    Preserves all unconstrained discovery fields in raw_data.
    """
    from app.models.campaign import get_campaign
    c = get_campaign(campaign_id)
    c_name = c.name if c else None

    existing_prospects = get_prospects_by_campaign(campaign_id)
    stored: list[Prospect] = []
    updated: list[Prospect] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for raw_item in prospects_data:
        if not isinstance(raw_item, dict):
            continue

        raw_copy = dict(raw_item)
        name = str(raw_item.get("name") or raw_item.get("person_name") or raw_item.get("full_name") or "Discovered Lead").strip()
        email = (raw_item.get("email") or raw_item.get("work_email") or "").strip()
        phone = (raw_item.get("phone") or raw_item.get("phone_number") or "").strip()
        title = str(raw_item.get("title") or raw_item.get("job_title") or raw_item.get("role") or "Executive").strip()
        company = str(raw_item.get("company") or raw_item.get("company_name") or raw_item.get("organization") or "Company").strip()
        raw_dom = (raw_item.get("domain") or raw_item.get("website") or "").strip()
        if raw_dom:
            clean_dom = re.sub(r"^https?://", "", raw_dom, flags=re.IGNORECASE)
            clean_dom = re.sub(r"^www\.", "", clean_dom, flags=re.IGNORECASE)
            domain = clean_dom.split("/")[0].strip()
        else:
            domain = ""

        location = (raw_item.get("location") or raw_item.get("city") or raw_item.get("country") or "").strip()
        company_size = str(raw_item.get("company_size") or raw_item.get("companySize") or raw_item.get("company_size_estimate") or "").strip()
        raw_source = str(raw_item.get("source") or "")
        source_as_url = raw_source if raw_source.startswith("http") else ""
        linkedin_url = (raw_item.get("linkedin_url") or raw_item.get("linkedinUrl") or raw_item.get("source_url") or raw_item.get("profile_url") or source_as_url).strip()
        notes = (raw_item.get("notes") or raw_item.get("sourcing_rationale") or "").strip()
        discovery_src = source or raw_item.get("discovery_source") or "Prospect Discovery Agent"
        metadata = raw_item.get("metadata") or {}

        # Intelligent enrichment of missing corporate details
        if (not company or company.lower() in ["unknown", "company", "none", ""]) and notes:
            m = re.search(r"(?:at|with|for)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|,|\s+highlighting|\s+focusing|\s+is|\s+in|\s+holding|\s+a|$)", notes)
            if m and len(m.group(1).strip()) > 2:
                company = m.group(1).strip()

        if not domain and company and company.lower() not in ["unknown", "company"]:
            clean_c = re.sub(r"[^a-zA-Z0-9]", "", company).lower()
            if clean_c:
                domain = f"{clean_c}.com"

        if email and ("http" in email or "/" in email):
            email = re.sub(r"https?://(?:www\.)?", "", email, flags=re.IGNORECASE).rstrip("/")

        if email:
            from app.services.email import sanitize_email_address
            email = sanitize_email_address(email)
        elif name and domain:
            parts = [re.sub(r"[^a-zA-Z0-9]", "", p).lower() for p in name.strip().split()]
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                email = f"{parts[0]}.{parts[-1]}@{domain}"
            elif len(parts) == 1:
                email = f"{parts[0]}@{domain}"

        if not company_size or company_size.lower() in ["unknown", "none", ""]:
            c_icp = (c.icp if c else "") or ""
            if "100" in c_icp or "enterprise" in c_icp.lower():
                company_size = "150-350 employees"
            else:
                company_size = "100-250 employees"

        if "sourcing_rationale" in raw_item and "sourcing_rationale" not in metadata:
            metadata["sourcing_rationale"] = raw_item["sourcing_rationale"]

        # Intelligent Deduplication Strategy within Campaign:
        matched_existing: Optional[Prospect] = None
        for ep in existing_prospects:
            if email and ep.email and email.lower() == ep.email.lower():
                matched_existing = ep
                break
            if linkedin_url and ep.linkedin_url and linkedin_url.lower().rstrip("/") == ep.linkedin_url.lower().rstrip("/"):
                matched_existing = ep
                break
            if name and company and ep.name and ep.company:
                if name.lower() == ep.name.lower() and company.lower() == ep.company.lower():
                    matched_existing = ep
                    break

        if matched_existing:
            # Update existing with enriched data and ensure linked to this campaign
            update_fields: dict[str, Any] = {
                "updated_at": now_iso,
                "campaign_id": campaign_id,
                "campaignId": campaign_id,
                "campaignName": c_name,
            }
            merged_raw = dict(matched_existing.raw_data or {})
            merged_raw.update(raw_copy)
            update_fields["raw_data"] = merged_raw

            if not matched_existing.phone and phone:
                update_fields["phone"] = phone
            if not matched_existing.linkedin_url and linkedin_url:
                update_fields["linkedin_url"] = linkedin_url
                update_fields["linkedinUrl"] = linkedin_url
            if not matched_existing.domain and domain:
                update_fields["domain"] = domain
            if not matched_existing.company_size and company_size:
                update_fields["company_size"] = company_size
                update_fields["companySize"] = company_size
            if not matched_existing.location and location:
                update_fields["location"] = location

            updated_p = matched_existing.model_copy(update=update_fields)
            _prospects[updated_p.id] = updated_p
            updated.append(updated_p)
            try:
                from app.services.supabase_db import _request
                _request(f"prospects?id=eq.{updated_p.id}", method="PATCH", data={"campaign_id": campaign_id})
            except Exception:
                pass
        else:
            p_id = raw_item.get("id") or str(uuid.uuid4())
            new_p = Prospect(
                id=p_id,
                name=name,
                email=email,
                phone=phone,
                title=title,
                company=company,
                domain=domain,
                location=location,
                company_size=company_size,
                companySize=company_size,
                linkedin_url=linkedin_url,
                linkedinUrl=linkedin_url,
                notes=notes,
                campaign_id=campaign_id,
                campaignId=campaign_id,
                campaignName=c_name,
                status="FIT",
                discovery_source=discovery_src,
                raw_data=raw_copy,
                metadata=metadata,
                created_at=now_iso,
                updated_at=now_iso,
                lastActivity="Discovered just now",
            )
            _prospects[new_p.id] = new_p
            existing_prospects.append(new_p)
            stored.append(new_p)

            try:
                from app.services.supabase_db import sb_upsert_prospect
                sb_upsert_prospect({
                    "id": new_p.id,
                    "campaign_id": campaign_id,
                    "name": new_p.name,
                    "email": new_p.email,
                    "phone": new_p.phone,
                    "linkedin_url": new_p.linkedin_url,
                    "title": new_p.title,
                    "company": new_p.company,
                    "domain": new_p.domain,
                    "location": new_p.location,
                    "company_size": new_p.company_size,
                    "status": "FIT",
                    "channel": "EMAIL",
                    "icp_score": 85,
                    "notes": new_p.notes,
                })
            except Exception:
                pass

    _save_prospects(_prospects)

    return {
        "success": True,
        "campaign_id": campaign_id,
        "stored_count": len(stored),
        "updated_count": len(updated),
        "total_processed": len(prospects_data),
        "prospects": stored + updated,
    }


def update_prospect_discovery_status(
    prospect_id: str,
    status: str,
    updates: Optional[dict] = None,
) -> Optional[Prospect]:
    """Updates a prospect's lifecycle status or manager decision."""
    p = _prospects.get(prospect_id)
    if not p:
        p = get_prospect(prospect_id)
        if not p:
            return None
    now_iso = datetime.now(timezone.utc).isoformat()
    changes: dict[str, Any] = {
        "status": status.strip().upper(),
        "updated_at": now_iso,
        "lastActivity": f"Status updated to {status.strip().upper()}",
    }
    if updates:
        for k, v in updates.items():
            if k not in ["id", "campaign_id", "campaignId"]:
                changes[k] = v
    updated = p.model_copy(update=changes)
    _prospects[prospect_id] = updated
    _save_prospects(_prospects)

    try:
        from app.services.supabase_db import sb_update_prospect_status
        norm_st = "CONTACTED" if status in ["SENT", "COMPLETED"] else ("REVIEW" if status in ["PROCESSING", "QUEUED"] else status)
        sb_update_prospect_status(
            prospect_id,
            status=norm_st,
            channel=changes.get("channel"),
            icp_score=changes.get("icpScore") or changes.get("icp_score"),
        )
    except Exception:
        pass

    return updated


def assign_prospects_to_campaign(campaign_id: str, prospect_ids: Optional[list[str]] = None) -> list[Prospect]:
    """Assigns unassigned prospects or specific prospect IDs to a target campaign, syncing Supabase."""
    from app.models.campaign import get_campaign
    from app.services.supabase_db import _request
    c = get_campaign(campaign_id)
    c_name = c.name if c else None

    updated_list: list[Prospect] = []
    # Make sure we have latest prospects
    get_all_prospects()

    for pid, p in list(_prospects.items()):
        # If no specific IDs passed, assign unassigned ones OR if only 1 campaign exists, all prospects
        should_assign = False
        if prospect_ids:
            should_assign = (pid in prospect_ids)
        else:
            # Assign if unassigned or belonging to this campaign
            should_assign = (not p.campaign_id or not p.campaignId or p.campaign_id == campaign_id)

        if should_assign:
            p_updated = p.model_copy(update={
                "campaign_id": campaign_id,
                "campaignId": campaign_id,
                "campaignName": c_name,
            })
            _prospects[pid] = p_updated
            updated_list.append(p_updated)
            try:
                _request(f"prospects?id=eq.{pid}", method="PATCH", data={"campaign_id": campaign_id})
            except Exception:
                pass

    _save_prospects(_prospects)
    return updated_list
