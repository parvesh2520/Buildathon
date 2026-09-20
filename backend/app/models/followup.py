import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


FOLLOWUP_STATUSES = {
    "PENDING",
    "SCHEDULED",
    "PROCESSING",
    "SENT",
    "WAITING",
    "STOPPED",
    "HUMAN_REVIEW",
    "FAILED",
}


class FollowUpRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    prospect_id: str
    touch_number: int
    channel: Optional[str] = None
    action: str
    status: str = "PENDING"
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    agent_decision: Dict[str, Any] = Field(default_factory=dict)
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    execution_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FOLLOWUPS_FILE = DATA_DIR / "followups.json"


def _load_followups() -> Dict[str, FollowUpRecord]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    loaded: Dict[str, FollowUpRecord] = {}
    if FOLLOWUPS_FILE.exists():
        try:
            with open(FOLLOWUPS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    rec = FollowUpRecord(**item)
                    loaded[rec.id] = rec
        except Exception:
            pass
    return loaded


def _save_followups(store: Dict[str, FollowUpRecord]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(FOLLOWUPS_FILE, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in store.values()], f, indent=2)
    except Exception:
        pass


_followups: Dict[str, FollowUpRecord] = _load_followups()


def save_followup(record: FollowUpRecord) -> FollowUpRecord:
    record.updated_at = datetime.now(timezone.utc).isoformat()
    _followups[record.id] = record
    _save_followups(_followups)
    try:
        from app.services.supabase_db import sb_create_follow_up

        sb_create_follow_up(record.model_dump())
    except Exception:
        pass
    return record


def create_followup(record: FollowUpRecord) -> FollowUpRecord:
    return save_followup(record)


def get_all_followups() -> List[FollowUpRecord]:
    return list(reversed(list(_followups.values())))


def get_followups_for_prospect(campaign_id: str, prospect_id: str) -> List[FollowUpRecord]:
    return [
        r
        for r in get_all_followups()
        if r.campaign_id == campaign_id and r.prospect_id == prospect_id
    ]


def find_followup_touch(campaign_id: str, prospect_id: str, touch_number: int) -> Optional[FollowUpRecord]:
    for rec in _followups.values():
        if (
            rec.campaign_id == campaign_id
            and rec.prospect_id == prospect_id
            and rec.touch_number == touch_number
            and rec.status in {"PENDING", "SCHEDULED", "PROCESSING", "SENT", "WAITING", "HUMAN_REVIEW"}
        ):
            return rec
    return None


def max_recorded_touch(campaign_id: str, prospect_id: str) -> int:
    max_touch = 0
    for rec in get_followups_for_prospect(campaign_id, prospect_id):
        if rec.status in {"SENT", "PROCESSING", "WAITING", "SCHEDULED", "HUMAN_REVIEW", "STOPPED"}:
            max_touch = max(max_touch, rec.touch_number)
    try:
        from app.models.execution import get_all_executions

        for rec in get_all_executions():
            if rec.campaign_id == campaign_id and rec.prospect_id == prospect_id and rec.status in {"SENT", "COMPLETED", "PENDING_MANUAL"}:
                max_touch = max(max_touch, rec.touch_number or 1)
    except Exception:
        pass
    return max_touch
