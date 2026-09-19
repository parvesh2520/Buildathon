import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger("db.supabase")


def _get_headers(prefer_upsert: bool = False) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation" if prefer_upsert else "return=representation",
    }
    return headers


def _request(
    path: str,
    method: str = "GET",
    data: Optional[Any] = None,
    prefer_upsert: bool = False,
) -> Optional[Any]:
    """Base HTTP helper for Supabase PostgREST queries."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    clean_base = SUPABASE_URL.rstrip("/")
    url = f"{clean_base}/rest/v1/{path.lstrip('/')}"
    headers = _get_headers(prefer_upsert)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body) if resp_body else []
    except urllib.error.HTTPError as err:
        err_text = err.read().decode("utf-8")
        logger.error(f"[SUPABASE HTTP ERROR] {method} {path} HTTP {err.code}: {err_text}")
        return None
    except Exception as exc:
        logger.error(f"[SUPABASE ERROR] {method} {path}: {exc}")
        return None


# ============================================================================
# 1. CAMPAIGNS
# ============================================================================

def sb_get_campaigns() -> List[Dict[str, Any]]:
    res = _request("campaigns?select=*&order=created_at.desc")
    return res if isinstance(res, list) else []


def sb_get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    res = _request(f"campaigns?id=eq.{campaign_id}&select=*")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_upsert_campaign(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = dict(data)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = _request("campaigns", method="POST", data=payload, prefer_upsert=True)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


# ============================================================================
# 2. PROSPECTS
# ============================================================================

def sb_get_prospects() -> List[Dict[str, Any]]:
    res = _request("prospects?select=*&order=created_at.desc")
    return res if isinstance(res, list) else []


def sb_get_prospect(prospect_id: str) -> Optional[Dict[str, Any]]:
    res = _request(f"prospects?id=eq.{prospect_id}&select=*")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_upsert_prospect(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = dict(data)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = _request("prospects", method="POST", data=payload, prefer_upsert=True)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_update_prospect_status(prospect_id: str, status: str) -> Optional[Dict[str, Any]]:
    payload = {
        "status": status,
        "last_activity_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    res = _request(f"prospects?id=eq.{prospect_id}", method="PATCH", data=payload)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_delete_prospect(prospect_id: str) -> bool:
    res = _request(f"prospects?id=eq.{prospect_id}", method="DELETE")
    return res is not None



# ============================================================================
# 3. EXECUTIONS
# ============================================================================

def sb_get_executions() -> List[Dict[str, Any]]:
    res = _request("executions?select=*&order=started_at.desc")
    return res if isinstance(res, list) else []


def sb_get_execution(execution_id: str) -> Optional[Dict[str, Any]]:
    res = _request(f"executions?id=eq.{execution_id}&select=*")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_execution_by_provider_call_id(provider_call_id: str) -> Optional[Dict[str, Any]]:
    res = _request(f"executions?provider_call_id=eq.{provider_call_id}&select=*")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_upsert_execution(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Map execution_id to id if necessary
    payload = dict(data)
    if "execution_id" in payload and "id" not in payload:
        payload["id"] = payload["execution_id"]
    res = _request("executions", method="POST", data=payload, prefer_upsert=True)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


# ============================================================================
# 4. AGENT_RESULTS
# ============================================================================

def sb_insert_agent_result(
    execution_id: str,
    prospect_id: str,
    agent_type: str,
    raw_output: Dict[str, Any],
    summary: Optional[str] = None,
    score: Optional[float] = None,
    sources_cited: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    payload = {
        "execution_id": execution_id,
        "prospect_id": prospect_id,
        "agent_type": agent_type,
        "raw_output": raw_output,
        "summary": summary,
        "score": score,
        "sources_cited": sources_cited or [],
    }
    res = _request("agent_results", method="POST", data=payload, prefer_upsert=False)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_agent_results(execution_id: str) -> List[Dict[str, Any]]:
    res = _request(f"agent_results?execution_id=eq.{execution_id}&select=*&order=created_at.asc")
    return res if isinstance(res, list) else []


# ============================================================================
# 5. OUTREACH_MESSAGES
# ============================================================================

def sb_insert_outreach_message(
    prospect_id: str,
    channel: str,
    recipient: str,
    content: str,
    execution_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    subject: Optional[str] = None,
    status: str = "SENT",
    provider: Optional[str] = None,
    provider_message_id: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    payload = {
        "execution_id": execution_id,
        "prospect_id": prospect_id,
        "campaign_id": campaign_id,
        "channel": channel,
        "recipient": recipient,
        "subject": subject,
        "content": content,
        "status": status,
        "provider": provider,
        "provider_message_id": provider_message_id,
        "error": error,
        "sent_at": datetime.now(timezone.utc).isoformat() if status == "SENT" else None,
    }
    res = _request("outreach_messages", method="POST", data=payload, prefer_upsert=False)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_outreach_messages(prospect_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "outreach_messages?select=*&order=created_at.desc"
    if prospect_id:
        query = f"outreach_messages?prospect_id=eq.{prospect_id}&select=*&order=created_at.desc"
    res = _request(query)
    return res if isinstance(res, list) else []


# ============================================================================
# 6. CONVERSATIONS
# ============================================================================

def sb_upsert_conversation(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = dict(data)
    payload["last_message_at"] = datetime.now(timezone.utc).isoformat()
    res = _request("conversations", method="POST", data=payload, prefer_upsert=True)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_conversations(prospect_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "conversations?select=*&order=last_message_at.desc"
    if prospect_id:
        query = f"conversations?prospect_id=eq.{prospect_id}&select=*&order=last_message_at.desc"
    res = _request(query)
    return res if isinstance(res, list) else []


# ============================================================================
# 7. FOLLOW_UPS
# ============================================================================

def sb_create_follow_up(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    res = _request("follow_ups", method="POST", data=data, prefer_upsert=False)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_follow_ups(status: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "follow_ups?select=*&order=scheduled_at.asc"
    if status:
        query = f"follow_ups?status=eq.{status}&select=*&order=scheduled_at.asc"
    res = _request(query)
    return res if isinstance(res, list) else []


# ============================================================================
# 8. KNOWLEDGE_BASE
# ============================================================================

def sb_upsert_knowledge_base(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = dict(data)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = _request("knowledge_base", method="POST", data=payload, prefer_upsert=True)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def sb_get_knowledge_base(campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "knowledge_base?select=*&order=created_at.desc"
    if campaign_id:
        query = f"knowledge_base?campaign_id=eq.{campaign_id}&select=*&order=created_at.desc"
    res = _request(query)
    return res if isinstance(res, list) else []


# ============================================================================
# 9. DATABASE STATS / HEALTH
# ============================================================================

def sb_get_database_stats() -> Dict[str, Any]:
    """Returns row counts and health status across all 8 tables."""
    tables = [
        "campaigns",
        "prospects",
        "executions",
        "agent_results",
        "outreach_messages",
        "conversations",
        "follow_ups",
        "knowledge_base",
    ]
    counts = {}
    connected = True
    for table in tables:
        try:
            res = _request(f"{table}?select=id")
            counts[table] = len(res) if isinstance(res, list) else 0
        except Exception:
            counts[table] = 0
            connected = False

    return {
        "status": "connected" if connected else "error",
        "url": SUPABASE_URL,
        "tables": counts,
        "total_rows": sum(counts.values()),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

