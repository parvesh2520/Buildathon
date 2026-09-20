from fastapi import APIRouter, HTTPException
from app.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignStatusUpdate,
    get_all_campaigns,
    get_campaign,
    create_campaign,
    delete_campaign,
    update_campaign_status,
)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.get("", response_model=list[Campaign])
def list_campaigns() -> list[Campaign]:
    return get_all_campaigns()


@router.get("/{campaign_id}", response_model=Campaign)
def retrieve_campaign(campaign_id: str) -> Campaign:
    campaign = get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("", response_model=Campaign, status_code=201)
def add_campaign(payload: CampaignCreate) -> Campaign:
    return create_campaign(payload)


@router.delete("/{campaign_id}", status_code=200)
def remove_campaign(campaign_id: str):
    delete_campaign(campaign_id)
    return {"status": "deleted", "id": campaign_id}


@router.patch("/{campaign_id}/status", response_model=Campaign)
def change_campaign_status(campaign_id: str, payload: CampaignStatusUpdate) -> Campaign:
    campaign = update_campaign_status(campaign_id, payload.status)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/executions")
def get_campaign_execution_history(campaign_id: str):
    """Returns execution records belonging only to the specified campaign."""
    from app.models.execution import get_campaign_executions
    return get_campaign_executions(campaign_id)


from pydantic import BaseModel
from typing import Optional, Dict, Any

class DuplicateCampaignRequest(BaseModel):
    variant_name: Optional[str] = None

class EnrollLeadsRequest(BaseModel):
    prospect_ids: Optional[list[str]] = None

class SavePromptsRequest(BaseModel):
    system_prompt: str
    agent_prompts: Dict[str, str]
    author: Optional[str] = "Campaign Manager"

class RollbackPromptsRequest(BaseModel):
    target_version: str

class AssignRepRequest(BaseModel):
    name: str
    email: str
    role: Optional[str] = "SDR"
    channels: Optional[list[str]] = ["EMAIL", "LINKEDIN"]
    daily_quota: Optional[int] = 50
    working_hours: Optional[str] = "09:00 - 18:00"

class OffboardRepRequest(BaseModel):
    rep_id: str
    reassign_to_id: Optional[str] = None


@router.post("/{campaign_id}/duplicate", response_model=Campaign)
def duplicate_existing_campaign(campaign_id: str, payload: DuplicateCampaignRequest = DuplicateCampaignRequest()):
    """Duplicate campaign into an A/B test variant (Section 3 - Stretch)."""
    from app.models.campaign import duplicate_campaign
    try:
        return duplicate_campaign(campaign_id, payload.variant_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{campaign_id}/enroll-leads")
def enroll_leads_to_campaign(campaign_id: str, payload: EnrollLeadsRequest = EnrollLeadsRequest()):
    """Enrolls leads/prospects into a target campaign, updating local state and Supabase."""
    from app.models.prospect import assign_prospects_to_campaign
    updated = assign_prospects_to_campaign(campaign_id, payload.prospect_ids)
    return {"enrolled_count": len(updated), "prospects": updated}


@router.get("/{campaign_id}/prompts")
def get_prompts_for_campaign(campaign_id: str):
    """Get campaign system prompt and per-agent prompts with version history (Section 3 & 4)."""
    from app.models.campaign import get_campaign_prompts
    return get_campaign_prompts(campaign_id)


@router.post("/{campaign_id}/prompts")
def save_prompts_for_campaign(campaign_id: str, payload: SavePromptsRequest):
    """Save new version of campaign prompts."""
    from app.models.campaign import save_campaign_prompts
    return save_campaign_prompts(
        campaign_id=campaign_id,
        system_prompt=payload.system_prompt,
        agent_prompts=payload.agent_prompts,
        author=payload.author or "Campaign Manager",
    )


@router.post("/{campaign_id}/prompts/rollback")
def rollback_prompts_for_campaign(campaign_id: str, payload: RollbackPromptsRequest):
    """Roll back campaign prompts to an earlier version."""
    from app.models.campaign import rollback_campaign_prompts
    try:
        return rollback_campaign_prompts(campaign_id, payload.target_version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{campaign_id}/reps")
def list_campaign_reps(campaign_id: str):
    """Get sales reps assigned to campaign with daily quotas (Section 3)."""
    from app.models.campaign import get_campaign_reps
    return get_campaign_reps(campaign_id)


@router.post("/{campaign_id}/reps")
def assign_rep_to_campaign(campaign_id: str, payload: AssignRepRequest):
    """Assign sales representative to campaign."""
    from app.models.campaign import assign_campaign_rep
    return assign_campaign_rep(campaign_id, payload.model_dump())


@router.post("/{campaign_id}/reps/offboard")
def offboard_rep(campaign_id: str, payload: OffboardRepRequest):
    """Offboard sales rep and reassign campaigns (Section 3)."""
    from app.models.campaign import offboard_campaign_rep
    return offboard_campaign_rep(campaign_id, payload.rep_id, payload.reassign_to_id)
