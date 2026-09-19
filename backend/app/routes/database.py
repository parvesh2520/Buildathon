import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.supabase_db import (
    sb_get_database_stats,
    sb_get_agent_results,
    sb_get_outreach_messages,
    sb_get_conversations,
    sb_upsert_conversation,
    sb_get_follow_ups,
    sb_create_follow_up,
    sb_get_knowledge_base,
    sb_upsert_knowledge_base,
)

logger = logging.getLogger("routes.database")

router = APIRouter(prefix="/api/database", tags=["Database"])


# Request Models aligned with Supabase Schema
class ConversationPayload(BaseModel):
    prospect_id: str
    campaign_id: Optional[str] = None
    channel: str = "EMAIL"
    status: str = "ACTIVE"
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    objections: Optional[List[str]] = None
    interested: bool = False
    next_action: Optional[str] = None


class FollowUpPayload(BaseModel):
    prospect_id: str
    campaign_id: str
    conversation_id: Optional[str] = None
    step_number: int = 1
    scheduled_channel: str = "EMAIL"
    scheduled_at: str
    status: str = "SCHEDULED"
    angle: Optional[str] = None
    notes: Optional[str] = None


class KnowledgeBasePayload(BaseModel):
    campaign_id: Optional[str] = None
    category: str = "PRODUCT_OVERVIEW"
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True


# Endpoints
@router.get("/stats")
def get_db_stats() -> Dict[str, Any]:
    """Returns real-time connection status and row counts across all 8 tables in Supabase."""
    return sb_get_database_stats()


@router.get("/agent-results/{execution_id}")
def get_agent_results_by_execution(execution_id: str) -> List[Dict[str, Any]]:
    """Returns all multi-agent stage outputs (Research, ICP, Strategy, Personalisation) for an execution."""
    return sb_get_agent_results(execution_id)


@router.get("/outreach-messages")
def list_outreach_messages(prospect_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Returns outreach messages sent/queued, optionally filtered by prospect_id."""
    return sb_get_outreach_messages(prospect_id=prospect_id)


@router.get("/conversations")
def list_conversations(prospect_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Returns conversation history, optionally filtered by prospect_id."""
    return sb_get_conversations(prospect_id=prospect_id)


@router.post("/conversations")
def create_or_update_conversation(payload: ConversationPayload) -> Dict[str, Any]:
    """Creates or updates a prospect conversation record."""
    res = sb_upsert_conversation(payload.model_dump(exclude_none=True))
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save conversation to Supabase")
    return res


@router.get("/follow-ups")
def list_follow_ups(status: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Returns scheduled follow-ups, optionally filtered by status (SCHEDULED, EXECUTED, etc.)."""
    return sb_get_follow_ups(status=status)


@router.post("/follow-ups")
def create_follow_up(payload: FollowUpPayload) -> Dict[str, Any]:
    """Schedules a new follow-up outreach."""
    res = sb_create_follow_up(payload.model_dump(exclude_none=True))
    if not res:
        raise HTTPException(status_code=500, detail="Failed to create follow-up in Supabase")
    return res


@router.get("/knowledge-base")
def list_knowledge_base(campaign_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Returns grounding knowledge base documents, optionally filtered by campaign_id."""
    return sb_get_knowledge_base(campaign_id=campaign_id)


@router.post("/knowledge-base")
def upsert_knowledge_base_item(payload: KnowledgeBasePayload) -> Dict[str, Any]:
    """Adds or updates a document in the knowledge base."""
    res = sb_upsert_knowledge_base(payload.model_dump(exclude_none=True))
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save knowledge base item to Supabase")
    return res
