from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.followup import FollowUpRecord, get_all_followups
from app.services.followup import (
    build_followup_agent_input,
    process_due_followups,
    process_followup_payload,
)


router = APIRouter(prefix="/api/followups", tags=["Follow-ups"])


class FollowUpTestRequest(BaseModel):
    prospect_id: str
    campaign: str
    icp_fit_score: int | None = None
    touch_number: int = 0
    max_allowed_touches: int = 3
    allowed_channels: List[str] = Field(default_factory=list)
    prior_touches: List[Dict[str, Any]] = Field(default_factory=list)
    send: bool = False


@router.post("/test")
async def test_followup(payload: FollowUpTestRequest) -> Dict[str, Any]:
    """
    Development endpoint: calls the real Follow-up Agent, but dry-runs by default.
    Pass send=true only when an actual outreach dispatch is intended.
    """
    try:
        data = payload.model_dump()
        data["campaign_id"] = data.pop("campaign")
        send = data.pop("send", False)
        return await process_followup_payload(data, dry_run=not send)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/run-due")
async def run_due_followups(limit: int = Query(25, ge=1, le=100)) -> Dict[str, Any]:
    return await process_due_followups(limit=limit)


@router.get("/records", response_model=List[FollowUpRecord])
def list_followup_records() -> List[FollowUpRecord]:
    return get_all_followups()


@router.post("/payload")
def preview_followup_payload(payload: FollowUpTestRequest) -> Dict[str, Any]:
    try:
        return build_followup_agent_input(
            campaign_id=payload.campaign,
            prospect_id=payload.prospect_id,
            current_touch=payload.touch_number,
            max_allowed_touches=payload.max_allowed_touches,
            allowed_channels=payload.allowed_channels,
            prior_touches=payload.prior_touches,
            icp_fit_score=payload.icp_fit_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
