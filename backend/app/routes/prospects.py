from fastapi import APIRouter, HTTPException
from app.models.prospect import (
    Prospect,
    ProspectCreate,
    get_all_prospects,
    get_prospect,
    create_prospect,
    delete_prospect,
)

router = APIRouter(prefix="/api/prospects", tags=["Prospects"])


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


@router.delete("/{prospect_id}", status_code=200)
def remove_prospect(prospect_id: str):
    delete_prospect(prospect_id)
    return {"status": "deleted", "id": prospect_id}

