from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.prospect import (
    Prospect,
    ProspectCreate,
    get_all_prospects,
    get_prospect,
    create_prospect,
    delete_prospect,
    update_prospect_status,
)

router = APIRouter(prefix="/api/prospects", tags=["Prospects"])


class ProspectStatusUpdate(BaseModel):
    status: str
    channel: Optional[str] = None
    icp_score: Optional[int] = None


@router.get("", response_model=list[Prospect])
def list_prospects() -> list[Prospect]:
    return get_all_prospects()


@router.get("/{prospect_id}", response_model=Prospect)
def retrieve_prospect(prospect_id: str) -> Prospect:
    prospect = get_prospect(prospect_id)
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.post("", response_model=Prospect, status_code=201)
def add_prospect(payload: ProspectCreate) -> Prospect:
    return create_prospect(payload)


@router.patch("/{prospect_id}/status", response_model=Prospect)
def update_status(prospect_id: str, payload: ProspectStatusUpdate) -> Prospect:
    updated = update_prospect_status(
        prospect_id=prospect_id,
        status=payload.status,
        channel=payload.channel,
        icp_score=payload.icp_score,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return updated


@router.delete("/{prospect_id}", status_code=200)
def remove_prospect(prospect_id: str):
    delete_prospect(prospect_id)
    return {"status": "deleted", "id": prospect_id}


