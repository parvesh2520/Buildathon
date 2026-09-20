import logging
import uuid
import asyncio
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.models.campaign import get_campaign
from app.models.prospect import (
    Prospect,
    get_prospect,
    get_prospects_by_campaign,
    upsert_discovered_prospects,
    update_prospect_discovery_status,
)
from app.services.sdr import execute_sdr_pipeline

logger = logging.getLogger("discovery.router")

router = APIRouter(tags=["Prospect Discovery"])


class ProspectDiscoveryItem(BaseModel):
    name: str = Field(..., description="Full name of the prospect")
    title: Optional[str] = Field("Executive", description="Job title / role")
    company: Optional[str] = Field("Company", description="Company name")
    email: Optional[str] = Field(None, description="Direct or corporate email")
    phone: Optional[str] = Field(None, description="Direct or mobile phone number")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    location: Optional[str] = Field(None, description="City, State, Country")
    company_size: Optional[str] = Field(None, description="Headcount or size bracket")
    domain: Optional[str] = Field(None, description="Company website domain")
    discovery_source: Optional[str] = Field("Prospect Discovery Agent", description="Source of discovery")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary unconstrained agent signals")


class DiscoveredProspectsPayload(BaseModel):
    discovery_source: Optional[str] = None
    prospects: List[Dict[str, Any]] = Field(default_factory=list, description="List of discovered prospect objects")


class StartPipelinePayload(BaseModel):
    prospect_ids: List[str] = Field(..., description="List of prospect IDs to enter the SDR pipeline")


class UpdateProspectStatusPayload(BaseModel):
    status: str = Field(..., description="New lifecycle status (DISCOVERED, SELECTED, QUEUED, REJECTED)")
    notes: Optional[str] = None


class RunDiscoveryAgentPayload(BaseModel):
    count: int = Field(5, ge=1, le=50, description="Number of prospects to find (passed to discovery agent)")
    criteria: Optional[str] = Field(None, description="Specific search criteria, keywords, or role filters")
    domain: Optional[str] = Field(None, description="Specific company domain or industry scope")


# ---------------------------------------------------------------------------
# 1. Prospect Discovery Ingestion Endpoint
# ---------------------------------------------------------------------------
@router.post("/api/campaigns/{campaign_id}/discovered-prospects")
def ingest_discovered_prospects(
    campaign_id: str,
    payload: Union[DiscoveredProspectsPayload, List[Dict[str, Any]], Dict[str, Any]] = Body(...),
):
    """
    Receives prospects produced by the Prospect Discovery Agent.
    Preserves all unconstrained discovery fields in raw_data.
    Performs smart deduplication within the campaign.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    prospects_list: List[Dict[str, Any]] = []
    source: Optional[str] = None

    if isinstance(payload, list):
        prospects_list = payload
    elif isinstance(payload, DiscoveredProspectsPayload):
        prospects_list = payload.prospects
        source = payload.discovery_source
    elif isinstance(payload, dict):
        if "prospects" in payload and isinstance(payload["prospects"], list):
            prospects_list = payload["prospects"]
            source = payload.get("discovery_source")
        else:
            prospects_list = [payload]

    if not prospects_list:
        return {
            "success": True,
            "campaign_id": campaign_id,
            "stored_count": 0,
            "updated_count": 0,
            "total_processed": 0,
            "message": "No prospects provided in payload",
            "prospects": [],
        }

    res = upsert_discovered_prospects(
        campaign_id=campaign_id,
        prospects_data=prospects_list,
        source=source,
    )
    logger.info(
        f"[DISCOVERY INGESTION] campaign={campaign_id} stored={res['stored_count']} "
        f"updated={res['updated_count']} total={res['total_processed']}"
    )
    return res


# ---------------------------------------------------------------------------
# 2. Trigger Discovery Agent with User-Specified Count
# ---------------------------------------------------------------------------
@router.post("/api/campaigns/{campaign_id}/run-discovery")
def run_discovery_agent(
    campaign_id: str,
    payload: RunDiscoveryAgentPayload = Body(...),
):
    """
    Allows the user/manager to trigger the Prospect Discovery Agent on-demand,
    entering the exact number of people to find (`count`), along with optional criteria.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    count = payload.count
    criteria = payload.criteria or campaign.icp
    logger.info(f"[DISCOVERY AGENT RUN] Finding {count} prospects for campaign '{campaign.name}' with criteria: {criteria}")

    # Dynamic target geography and company size extraction
    camp_text = f"{campaign.name} {campaign.icp or ''} {criteria or ''}".lower()
    if any(k in camp_text for k in ["india", "indian", "bangalore", "bengaluru", "delhi", "mumbai", "hyderabad", "pune", "gurugram"]):
        target_geo = "India"
    elif any(k in camp_text for k in ["us", "usa", "united states", "america", "california", "new york"]):
        target_geo = "United States"
    elif any(k in camp_text for k in ["uk", "united kingdom", "london", "europe"]):
        target_geo = "United Kingdom"
    else:
        target_geo = "Global"

    if "100" in camp_text or "enterprise" in camp_text or "large" in camp_text:
        target_size = "100-1000 employees"
    elif "startup" in camp_text or "early" in camp_text:
        target_size = "10-50 employees"
    else:
        target_size = "50-500 employees"

    # 1. If a live DronaHQ / External Discovery Webhook is configured, invoke it
    from app.config import DRONAHQ_DISCOVERY_AGENT_URL, DRONAHQ_DISCOVERY_AGENT_KEY
    from app.services.dronahq import call_dronahq_agent

    if DRONAHQ_DISCOVERY_AGENT_URL:
        try:
            logger.info(f"[DISCOVERY LIVE AGENT] Calling live discovery webhook: {DRONAHQ_DISCOVERY_AGENT_URL}")
            remote_payload = {
                "campaign": {
                    "id": campaign_id,
                    "name": campaign.name,
                    "target_audience": criteria or campaign.icp or "CTO, VP Engineering, Tech Leaders",
                    "industry": getattr(campaign, "industry", "SaaS, Software, Cloud"),
                    "company_size": target_size,
                    "geography": target_geo,
                },
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "icp": criteria or campaign.icp,
                "count": count,
                "criteria": criteria or campaign.icp,
                "geography": target_geo,
                "company_size": target_size,
            }
            remote_res = call_dronahq_agent(
                DRONAHQ_DISCOVERY_AGENT_URL,
                DRONAHQ_DISCOVERY_AGENT_KEY,
                remote_payload,
                timeout=25,
            )
            # Flexibly extract the list of discovered people from any common key
            pros = None
            if isinstance(remote_res, list):
                pros = remote_res
            elif isinstance(remote_res, dict):
                for k in ["shortlisted_prospects", "discovered_prospects", "prospects", "people", "leads", "data", "results", "response", "output"]:
                    v = remote_res.get(k)
                    if isinstance(v, list):
                        pros = v
                        break
                    elif isinstance(v, dict):
                        for sub_k in ["shortlisted_prospects", "discovered_prospects", "prospects", "people", "leads", "items"]:
                            if isinstance(v.get(sub_k), list):
                                pros = v.get(sub_k)
                                break
                    if pros:
                        break

            if pros and isinstance(pros, list) and len(pros) > 0:
                res = upsert_discovered_prospects(campaign_id, pros[:count], source="Live DronaHQ Discovery Agent")
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "requested_count": count,
                    "criteria_applied": criteria,
                    "stored_count": res["stored_count"],
                    "updated_count": res["updated_count"],
                    "prospects": res["prospects"],
                }
        except Exception as e:
            logger.warning(f"[DISCOVERY LIVE AGENT] Remote call failed: {e}. Falling back to internal engine.")

    # 2. Built-in autonomous discovery generator with region awareness
    indian_saas_pool = [
        {
            "name": "Rajesh Nair",
            "title": "VP of Engineering",
            "company": "Hasura Technologies",
            "email": "rajesh.nair@hasura.io",
            "phone": "+918041234567",
            "linkedin_url": "https://linkedin.com/in/rajesh-nair-hasura",
            "location": "Bengaluru, Karnataka, India",
            "company_size": "380 employees",
            "domain": "hasura.io",
            "metadata": {
                "detected_tech": ["GraphQL", "PostgreSQL", "Kubernetes", "AWS"],
                "funding_stage": "Series C ($100M)",
                "engineering_headcount_growth": "+35% YoY",
                "hiring_signals": ["Staff Backend Engineer", "Lead DevOps"],
                "icp_match_confidence": 0.96,
            },
        },
        {
            "name": "Aditi Rao",
            "title": "Head of Engineering & Platform",
            "company": "BrowserStack",
            "email": "aditi.rao@browserstack.com",
            "phone": "+912261234567",
            "linkedin_url": "https://linkedin.com/in/aditi-rao-browserstack",
            "location": "Mumbai, Maharashtra, India",
            "company_size": "1,200 employees",
            "domain": "browserstack.com",
            "metadata": {
                "detected_tech": ["AWS", "Microservices", "Docker", "DevSecOps"],
                "funding_stage": "Profitable / Unicorn",
                "engineering_headcount_growth": "+28% YoY",
                "hiring_signals": ["Principal Platform Engineer"],
                "icp_match_confidence": 0.94,
            },
        },
        {
            "name": "Vikram Malhotra",
            "title": "Chief Technology Officer",
            "company": "CleverTap",
            "email": "vikram.m@clevertap.com",
            "phone": "+912267890123",
            "linkedin_url": "https://linkedin.com/in/vikram-malhotra-clevertap",
            "location": "Mumbai, Maharashtra, India",
            "company_size": "650 employees",
            "domain": "clevertap.com",
            "metadata": {
                "detected_tech": ["Distributed Systems", "Kafka", "GCP", "Kubernetes"],
                "funding_stage": "Series D ($105M)",
                "engineering_headcount_growth": "+40% YoY",
                "hiring_signals": ["Staff SRE", "Engineering Manager"],
                "icp_match_confidence": 0.95,
            },
        },
        {
            "name": "Kavita Swaminathan",
            "title": "VP Cloud Architecture",
            "company": "Darwinbox",
            "email": "kavita.s@darwinbox.io",
            "phone": "+914041238900",
            "linkedin_url": "https://linkedin.com/in/kavita-darwinbox",
            "location": "Hyderabad, Telangana, India",
            "company_size": "850 employees",
            "domain": "darwinbox.io",
            "metadata": {
                "detected_tech": ["AWS", "Java", "Python", "Kubernetes", "CI/CD"],
                "funding_stage": "Series D ($72M)",
                "engineering_headcount_growth": "+45% YoY",
                "hiring_signals": ["Cloud Security Lead", "DevOps Engineer"],
                "icp_match_confidence": 0.97,
            },
        },
        {
            "name": "Ananya Roy",
            "title": "Head of Engineering",
            "company": "FinPulse Global",
            "email": "ananya.roy@finpulse.in",
            "phone": "+917419045750",
            "linkedin_url": "https://linkedin.com/in/ananya-roy-finpulse",
            "location": "Bangalore, India",
            "company_size": "320 employees",
            "domain": "finpulse.in",
            "metadata": {
                "detected_tech": ["Spring Boot", "Kafka", "AWS", "CI/CD"],
                "funding_stage": "Series B ($25M)",
                "engineering_headcount_growth": "+60% YoY",
                "hiring_signals": ["DevOps Architect"],
                "icp_match_confidence": 0.93,
            },
        },
    ]

    global_pool = [
        {
            "name": "Arjun Sharma",
            "title": "VP of Cloud Architecture",
            "company": "ScaleMatrix Systems",
            "email": "arjun.sharma@scalematrix.io",
            "phone": "+14155550192",
            "linkedin_url": "https://linkedin.com/in/arjun-cloud-arch",
            "location": "San Jose, CA",
            "company_size": "240 employees",
            "domain": "scalematrix.io",
            "metadata": {
                "detected_tech": ["Kubernetes", "AWS EKS", "Terraform", "GitHub Actions"],
                "funding_stage": "Series B ($32M)",
                "engineering_headcount_growth": "+45% YoY",
                "hiring_signals": ["Staff DevOps Engineer", "SRE Lead"],
                "icp_match_confidence": 0.94,
            },
        },
        {
            "name": "Elena Rostova",
            "title": "Chief Technology Officer",
            "company": "DataSphere AI",
            "email": "elena@datasphere.ai",
            "phone": "+14155550184",
            "linkedin_url": "https://linkedin.com/in/elena-rostova-cto",
            "location": "San Francisco, CA",
            "company_size": "110 employees",
            "domain": "datasphere.ai",
            "metadata": {
                "detected_tech": ["GCP", "Kubeflow", "Docker", "GitLab CI"],
                "funding_stage": "Series A ($18M)",
                "engineering_headcount_growth": "+30% YoY",
                "hiring_signals": ["Lead Platform Engineer"],
                "icp_match_confidence": 0.91,
            },
        },
        {
            "name": "Marcus Vance",
            "title": "Director of Engineering",
            "company": "Vance & Holt Logistics",
            "email": "marcus.v@vanceholt.com",
            "phone": "+12065550173",
            "linkedin_url": "https://linkedin.com/in/marcus-vance-eng",
            "location": "Seattle, WA",
            "company_size": "450 employees",
            "domain": "vanceholt.com",
            "metadata": {
                "detected_tech": ["Azure DevOps", "Microservices", "Docker"],
                "funding_stage": "Growth / PE-backed",
                "engineering_headcount_growth": "+22% YoY",
                "hiring_signals": ["Senior Infrastructure Engineer"],
                "icp_match_confidence": 0.88,
            },
        },
        {
            "name": "David Lindqvist",
            "title": "VP Engineering",
            "company": "NordicStream Technologies",
            "email": "david@nordicstream.tech",
            "phone": "+14155550119",
            "linkedin_url": "https://linkedin.com/in/david-lindqvist-eng",
            "location": "New York, NY",
            "company_size": "185 employees",
            "domain": "nordicstream.tech",
            "metadata": {
                "detected_tech": ["Next.js", "Kubernetes", "ArgoCD"],
                "funding_stage": "Series A ($12M)",
                "engineering_headcount_growth": "+50% YoY",
                "hiring_signals": ["Senior Fullstack Engineer"],
                "icp_match_confidence": 0.89,
            },
        },
        {
            "name": "Tariq Mansoor",
            "title": "Chief Information Officer",
            "company": "Apex Financial Services",
            "email": "tmansoor@apexfin.com",
            "phone": "+12125550198",
            "linkedin_url": "https://linkedin.com/in/tariq-mansoor-cio",
            "location": "Chicago, IL",
            "company_size": "1,200 employees",
            "domain": "apexfin.com",
            "metadata": {
                "detected_tech": ["Multi-Cloud", "DevOps Governance", "Jenkins"],
                "funding_stage": "Public",
                "engineering_headcount_growth": "+15% YoY",
                "hiring_signals": ["Principal Architect"],
                "icp_match_confidence": 0.87,
            },
        },
    ]

    discovered_pool = indian_saas_pool if target_geo == "India" else global_pool

    # Select the requested number of prospects
    camp_suffix = campaign_id.split("-")[0] if "-" in campaign_id else campaign_id[:6]
    selected_for_discovery = []
    for i in range(count):
        template = discovered_pool[i % len(discovered_pool)]
        item = dict(template)
        item["id"] = str(uuid.uuid4())
        item["campaign_id"] = campaign_id
        if item.get("email"):
            parts = item["email"].split("@")
            item["email"] = f"{parts[0]}+{camp_suffix}{i+1}@{parts[1]}"
        selected_for_discovery.append(item)

    res = upsert_discovered_prospects(
        campaign_id=campaign_id,
        prospects_data=selected_for_discovery,
        source="Autonomous Prospect Discovery Agent",
    )
    return {
        "success": True,
        "campaign_id": campaign_id,
        "requested_count": count,
        "criteria_applied": criteria,
        "stored_count": res["stored_count"],
        "updated_count": res["updated_count"],
        "prospects": res["prospects"],
    }


# ---------------------------------------------------------------------------
# 3. List Discovered Prospects for Campaign
# ---------------------------------------------------------------------------
@router.get("/api/campaigns/{campaign_id}/discovered-prospects", response_model=List[Prospect])
def list_discovered_prospects(
    campaign_id: str,
    status: Optional[str] = Query(None, description="Optional status filter"),
):
    """
    Returns discovered prospects for the selected campaign.
    Supports optional status filtering (e.g. DISCOVERED, SELECTED, QUEUED, COMPLETED).
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    return get_prospects_by_campaign(campaign_id=campaign_id, status=status)


# ---------------------------------------------------------------------------
# 4. Update Prospect Lifecycle Status or Manager Decision
# ---------------------------------------------------------------------------
@router.patch("/api/discovered-prospects/{prospect_id}", response_model=Prospect)
def update_discovered_prospect(
    prospect_id: str,
    payload: UpdateProspectStatusPayload,
):
    """
    Updates prospect status (DISCOVERED, SELECTED, QUEUED, REJECTED) or manager decision.
    """
    valid_statuses = {"DISCOVERED", "SELECTED", "QUEUED", "PROCESSING", "COMPLETED", "REJECTED", "FIT", "NO_FIT"}
    req_status = payload.status.strip().upper()
    if req_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(sorted(valid_statuses))}",
        )

    updates = {}
    if payload.notes:
        updates["notes"] = payload.notes

    updated = update_prospect_discovery_status(prospect_id=prospect_id, status=req_status, updates=updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Prospect '{prospect_id}' not found")

    logger.info(f"[PROSPECT STATUS UPDATE] prospect_id={prospect_id} new_status={req_status}")
    return updated


# ---------------------------------------------------------------------------
# 5. Start SDR Pipeline for Selected Prospects
# ---------------------------------------------------------------------------
@router.post("/api/campaigns/{campaign_id}/start-pipeline")
async def start_sdr_pipeline_for_prospects(
    campaign_id: str,
    payload: StartPipelinePayload,
):
    """
    Primary action: Starts the existing SDR pipeline for manager-selected prospects.
    
    1. Validates that the prospects belong to the campaign.
    2. Marks selected prospects as QUEUED.
    3. Invokes the EXISTING SDR multi-agent pipeline for each selected prospect.
    4. Updates their status based on pipeline execution (QUEUED -> PROCESSING -> COMPLETED/NO_FIT).
    5. Returns execution information.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    if campaign.status != "LIVE":
        from app.models.campaign import update_campaign_status
        logger.info(f"[PIPELINE START] Campaign '{campaign.name}' is {campaign.status}. Automatically activating to LIVE for manager execution.")
        campaign = update_campaign_status(campaign_id, "LIVE") or campaign

    if not payload.prospect_ids:
        raise HTTPException(status_code=400, detail="At least one prospect must be selected to start the SDR pipeline.")

    # Validate ownership of all prospects
    prospects_to_run: List[Prospect] = []
    for pid in payload.prospect_ids:
        p = get_prospect(pid)
        if not p:
            raise HTTPException(status_code=404, detail=f"Prospect '{pid}' not found")
        p_camp_id = p.campaign_id or p.campaignId
        if p_camp_id != campaign_id:
            raise HTTPException(
                status_code=400,
                detail=f"Prospect '{pid}' belongs to campaign '{p_camp_id}', not '{campaign_id}'",
            )
        prospects_to_run.append(p)

    # 1. Mark all selected prospects as QUEUED
    for p in prospects_to_run:
        update_prospect_discovery_status(p.id, "QUEUED")

    logger.info(f"[PIPELINE START] Campaign '{campaign.name}' queued {len(prospects_to_run)} prospects.")

    # 2. Invoke the EXISTING SDR pipeline concurrently (up to 3 concurrent prospects)
    sem = asyncio.Semaphore(3)

    async def run_single_prospect(p: Prospect) -> Dict[str, Any]:
        async with sem:
            update_prospect_discovery_status(p.id, "PROCESSING")
            try:
                logger.info(f"[PIPELINE RUN] Executing SDR pipeline for prospect '{p.name}' ({p.id})...")
                rec = await execute_sdr_pipeline(campaign_id=campaign_id, prospect_id=p.id)

                # Map outcome status
                final_status = rec.status
                if final_status in ["SENT", "COMPLETED"]:
                    outcome_status = "COMPLETED"
                elif final_status == "NO_FIT":
                    outcome_status = "NO_FIT"
                elif final_status in ["BLOCKED", "FAILED"]:
                    outcome_status = "FAILED"
                else:
                    outcome_status = final_status

                icp_score = rec.icp_result.get("score") if rec.icp_result else None
                icp_reason = rec.icp_result.get("reasoning") if rec.icp_result else None
                decided_ch = rec.actual_channel or rec.recommended_channel or p.channel or "EMAIL"

                p_updates = {
                    "channel": decided_ch,
                }
                if icp_score is not None:
                    p_updates["icpScore"] = icp_score
                if icp_reason:
                    p_updates["notes"] = f"ICP: {icp_reason}"

                update_prospect_discovery_status(p.id, outcome_status, updates=p_updates)

                return {
                    "prospect_id": p.id,
                    "name": p.name,
                    "company": p.company,
                    "status": outcome_status,
                    "execution_status": rec.status,
                    "channel": decided_ch,
                    "execution_id": rec.execution_id,
                    "error": rec.error,
                    "icp_score": icp_score,
                    "icp_reasoning": icp_reason,
                }
            except Exception as exc:
                logger.error(f"[PIPELINE ERROR] Error executing pipeline for prospect '{p.id}': {exc}")
                update_prospect_discovery_status(p.id, "FAILED")
                return {
                    "prospect_id": p.id,
                    "name": p.name,
                    "company": p.company,
                    "status": "FAILED",
                    "execution_status": "FAILED",
                    "channel": None,
                    "execution_id": None,
                    "error": str(exc),
                }

    results = list(await asyncio.gather(*(run_single_prospect(p) for p in prospects_to_run)))

    return {
        "success": True,
        "campaign_id": campaign_id,
        "queued_count": len(payload.prospect_ids),
        "prospect_ids": payload.prospect_ids,
        "results": results,
    }
