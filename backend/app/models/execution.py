from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# Execution Statuses:
# PENDING, RUNNING, NO_FIT, READY_TO_SEND, SENT, PENDING_MANUAL, FAILED, CHANNEL_MISMATCH, BLOCKED

class ExecutionRecord(BaseModel):
    execution_id: str
    campaign_id: str
    prospect_id: str
    status: str = "PENDING"
    current_agent: str = "ORCHESTRATOR"
    channel: Optional[str] = None
    recommended_channel: Optional[str] = None
    actual_channel: Optional[str] = None
    action_type: Optional[str] = None
    provider_call_id: Optional[str] = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    answered_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration: Optional[int] = None
    call_outcome: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    research_result: Optional[Dict[str, Any]] = None
    icp_result: Optional[Dict[str, Any]] = None
    strategy_result: Optional[Dict[str, Any]] = None
    personalisation_result: Optional[Dict[str, Any]] = None
    channel_result: Optional[Dict[str, Any]] = None
    voice_agent_result: Optional[Dict[str, Any]] = None


import json
from pathlib import Path

# Persistent execution store — backed by JSON file in backend/data/executions.json
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EXECUTIONS_FILE = DATA_DIR / "executions.json"


def _load_executions() -> Dict[str, ExecutionRecord]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    loaded: Dict[str, ExecutionRecord] = {}
    if EXECUTIONS_FILE.exists():
        try:
            with open(EXECUTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        rec = ExecutionRecord(**item)
                        loaded[rec.execution_id] = rec
        except Exception:
            pass
    return loaded


def _save_executions(store: Dict[str, ExecutionRecord]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(EXECUTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in store.values()], f, indent=2)
    except Exception:
        pass


_executions: Dict[str, ExecutionRecord] = _load_executions()


def _to_db_payload(record: ExecutionRecord) -> Dict[str, Any]:
    return {
        "id": record.execution_id,
        "campaign_id": record.campaign_id,
        "prospect_id": record.prospect_id,
        "status": "FAILED" if record.status in ["BUSY", "NO_ANSWER", "CANCELED"] else record.status,
        "current_agent": record.current_agent,
        "recommended_channel": record.recommended_channel,
        "actual_channel": record.actual_channel,
        "action_type": record.action_type or "NEW_OUTREACH",
        "provider_call_id": record.provider_call_id,
        "started_at": record.started_at,
        "answered_at": record.answered_at,
        "ended_at": record.ended_at,
        "duration": record.duration,
        "call_outcome": record.call_outcome,
        "completed_at": record.completed_at,
        "error": record.error,
    }


def create_execution(record: ExecutionRecord) -> ExecutionRecord:
    from app.services.supabase_db import sb_upsert_execution
    _executions[record.execution_id] = record
    _save_executions(_executions)
    try:
        sb_upsert_execution(_to_db_payload(record))
    except Exception:
        pass
    return record


def get_execution(execution_id: str) -> Optional[ExecutionRecord]:
    return _executions.get(execution_id)


def get_campaign_executions(campaign_id: str) -> List[ExecutionRecord]:
    return [e for e in _executions.values() if e.campaign_id == campaign_id]


def get_all_executions() -> List[ExecutionRecord]:
    return list(reversed(list(_executions.values())))


def save_execution(record: ExecutionRecord) -> ExecutionRecord:
    from app.services.supabase_db import sb_upsert_execution
    _executions[record.execution_id] = record
    _save_executions(_executions)
    try:
        sb_upsert_execution(_to_db_payload(record))
    except Exception:
        pass
    return record


def update_execution(execution_id: str, **kwargs) -> Optional[ExecutionRecord]:
    from app.services.supabase_db import sb_upsert_execution
    rec = _executions.get(execution_id)
    if not rec:
        return None
    kwargs.pop("execution_id", None)
    updated = rec.model_copy(update=kwargs)
    _executions[execution_id] = updated
    _save_executions(_executions)
    try:
        sb_upsert_execution(_to_db_payload(updated))
    except Exception:
        pass
    return updated


def get_execution_by_provider_call_id(provider_call_id: str) -> Optional[ExecutionRecord]:
    clean_id = (provider_call_id or "").strip()
    if not clean_id:
        return None
    for rec in _executions.values():
        if rec.provider_call_id == clean_id:
            return rec
        if rec.channel_result and rec.channel_result.get("provider_call_id") == clean_id:
            return rec
    return None
