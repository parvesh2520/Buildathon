from fastapi import APIRouter, HTTPException
from app.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignStatusUpdate,
    get_all_campaigns,
    get_campaign,
    create_campaign,
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
