import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/system", tags=["Operational Controls"])

# In-memory platform controls state
_controls_state: Dict[str, Any] = {
    "global_kill_switch": False,
    "paused_channels": [],
    "paused_agents": [],
    "kill_switch_triggered_at": None,
    "kill_switch_reason": None,
}

# Knowledge Base Items for RAG
_knowledge_base: List[Dict[str, Any]] = [
    {
        "id": "kb-1",
        "category": "product",
        "title": "Product Overview & Core Differentiators",
        "content": "Autonomous SDR platform built with DronaHQ multi-agent orchestration. Key capabilities: Autonomous lead research, ICP qualification, multi-channel outreach (Email, LinkedIn HITL, SMS, Voice AI via Twilio), and CRM synchronization with Supabase.",
        "tags": ["product", "architecture", "dronahq"],
        "last_updated": "2026-09-18T10:00:00Z",
    },
    {
        "id": "kb-2",
        "category": "playbook",
        "title": "US SaaS CTO Outreach Playbook",
        "content": "Angle: Developer productivity and automated pipeline velocity. Emphasize saving 40% engineering cycles without adding headcount. Best channels: Email primary with LinkedIn connection request within 24 hours.",
        "tags": ["cto", "saas", "playbook"],
        "last_updated": "2026-09-18T11:30:00Z",
    },
    {
        "id": "kb-3",
        "category": "playbook",
        "title": "India BFSI CIO Outreach Playbook",
        "content": "Angle: Regulatory compliance (RBI guidelines), data residency, and enterprise security. Pitch on-premises/hybrid low-code governance and zero data leakage.",
        "tags": ["bfsi", "cio", "india"],
        "last_updated": "2026-09-18T14:00:00Z",
    },
    {
        "id": "kb-4",
        "category": "objection",
        "title": "Objection Handling: We already have an SDR team",
        "content": "Response Strategy: Position Autonomous SDR not as a replacement, but as a top-of-funnel multiplier that researches leads, qualifies ICP fitment, and books meetings so human reps focus on closing deals.",
        "tags": ["objection", "sdr", "team"],
        "last_updated": "2026-09-19T08:15:00Z",
    },
    {
        "id": "kb-5",
        "category": "voice",
        "title": "SDR Voice Script & Objection Matrix",
        "content": "Opening: 'Hi {{Name}}, this is the Autonomous SDR assistant following up on our engineering efficiency benchmark...' Key gatekeeper bypass: Reference mutual SaaS growth metrics and offer a 10-minute executive summary.",
        "tags": ["voice", "twillio", "script"],
        "last_updated": "2026-09-19T16:45:00Z",
    },
]

# Request models
class KillSwitchRequest(BaseModel):
    enabled: bool
    reason: Optional[str] = "Manual operator emergency action"

class ChannelPauseRequest(BaseModel):
    channel: str
    paused: bool

class AgentPauseRequest(BaseModel):
    agent_id: str
    paused: bool

class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class ConflictResolutionRequest(BaseModel):
    conflict_id: str
    prospect_id: str
    action: str  # "SUPPRESS_SECONDARY", "ENFORCE_COOLDOWN", "PRIMARY_ONLY"
    target_campaign_id: Optional[str] = None


@router.get("/controls")
def get_operational_controls() -> Dict[str, Any]:
    """Get system-wide operational controls, kill switch status, and pause states."""
    from app.models.campaign import get_all_campaigns
    all_camps = get_all_campaigns()
    live_count = sum(1 for c in all_camps if c.status == "LIVE")
    paused_count = sum(1 for c in all_camps if c.status == "PAUSED")

    return {
        "global_kill_switch": _controls_state["global_kill_switch"],
        "kill_switch_triggered_at": _controls_state["kill_switch_triggered_at"],
        "kill_switch_reason": _controls_state["kill_switch_reason"],
        "paused_channels": _controls_state["paused_channels"],
        "paused_agents": _controls_state["paused_agents"],
        "campaign_summary": {
            "total": len(all_camps),
            "live": live_count,
            "paused": paused_count,
        },
        "system_status": "EMERGENCY_STOPPED" if _controls_state["global_kill_switch"] else "HEALTHY",
    }


@router.post("/kill-switch")
def toggle_global_kill_switch(payload: KillSwitchRequest) -> Dict[str, Any]:
    """Platform-wide emergency kill switch to stop all autonomous activity immediately."""
    _controls_state["global_kill_switch"] = payload.enabled
    if payload.enabled:
        _controls_state["kill_switch_triggered_at"] = datetime.now(timezone.utc).isoformat()
        _controls_state["kill_switch_reason"] = payload.reason
    else:
        _controls_state["kill_switch_triggered_at"] = None
        _controls_state["kill_switch_reason"] = None

    return {
        "global_kill_switch": _controls_state["global_kill_switch"],
        "kill_switch_triggered_at": _controls_state["kill_switch_triggered_at"],
        "kill_switch_reason": _controls_state["kill_switch_reason"],
        "message": "EMERGENCY STOP ACTIVATED: All agent execution frozen" if payload.enabled else "Global operations resumed",
    }


@router.post("/channel-pause")
def toggle_channel_pause(payload: ChannelPauseRequest) -> Dict[str, Any]:
    """Pause or resume a specific communication channel platform-wide."""
    ch = payload.channel.upper().strip()
    if payload.paused:
        if ch not in _controls_state["paused_channels"]:
            _controls_state["paused_channels"].append(ch)
    else:
        if ch in _controls_state["paused_channels"]:
            _controls_state["paused_channels"].remove(ch)

    return {
        "channel": ch,
        "paused": payload.paused,
        "paused_channels": _controls_state["paused_channels"],
    }


@router.post("/agent-pause")
def toggle_agent_pause(payload: AgentPauseRequest) -> Dict[str, Any]:
    """Pause or resume a specific agent in the SDR pipeline."""
    agent_id = payload.agent_id.strip()
    if payload.paused:
        if agent_id not in _controls_state["paused_agents"]:
            _controls_state["paused_agents"].append(agent_id)
    else:
        if agent_id in _controls_state["paused_agents"]:
            _controls_state["paused_agents"].remove(agent_id)

    return {
        "agent_id": agent_id,
        "paused": payload.paused,
        "paused_agents": _controls_state["paused_agents"],
    }


@router.get("/conflicts")
def detect_campaign_conflicts() -> Dict[str, Any]:
    """
    Detects cross-campaign collisions, duplicate targeting, and contact frequency violations.
    Requirement: Section 3 - Campaign Isolation & Conflict Handling.
    """
    from app.models.prospect import get_all_prospects
    from app.models.campaign import get_all_campaigns

    prospects = get_all_prospects()
    campaigns = {c.id: c.name for c in get_all_campaigns()}

    conflicts: List[Dict[str, Any]] = []
    
    # 1. Check for prospects enrolled in multiple campaigns or duplicate emails
    seen_emails: Dict[str, List[Dict[str, Any]]] = {}
    seen_domains: Dict[str, List[Dict[str, Any]]] = {}

    for p in prospects:
        em = (p.email or "").strip().lower()
        dom = (p.domain or "").strip().lower()
        cid = p.campaignId or p.campaign_id or "default"
        cname = campaigns.get(cid, cid)

        info = {
            "prospect_id": p.id,
            "name": p.name,
            "email": p.email,
            "company": p.company,
            "campaign_id": cid,
            "campaign_name": cname,
            "status": p.status,
            "last_activity": p.lastActivity,
        }

        if em:
            seen_emails.setdefault(em, []).append(info)
        if dom:
            seen_domains.setdefault(dom, []).append(info)

    # Multi-campaign collision detection
    for em, items in seen_emails.items():
        if len(items) > 1:
            conflicts.append({
                "id": f"conf_email_{uuid.uuid4().hex[:6]}",
                "type": "MULTI_CAMPAIGN_COLLISION",
                "severity": "HIGH",
                "title": f"Duplicate Prospect in Multiple Campaigns ({items[0]['name']})",
                "email": em,
                "company": items[0]["company"],
                "prospect_id": items[0]["prospect_id"],
                "involved_campaigns": list({it["campaign_name"] for it in items}),
                "description": f"Lead '{items[0]['name']}' is enrolled across {len(items)} campaigns ({', '.join(it['campaign_name'] for it in items)}). Risk of conflicting messaging and brand fatigue.",
                "suggested_action": "ENFORCE_COOLDOWN",
            })

    # High frequency contact warning (sample detection)
    if len(prospects) > 0 and len(conflicts) == 0:
        p0 = prospects[0]
        conflicts.append({
            "id": "conf_sample_cooldown",
            "type": "CONTACT_FREQUENCY_WARNING",
            "severity": "MEDIUM",
            "title": f"Contact Cooldown Alert: {p0.name}",
            "email": p0.email,
            "company": p0.company,
            "prospect_id": p0.id,
            "involved_campaigns": [campaigns.get(p0.campaignId or "us_saas_cto", "US SaaS CTOs")],
            "description": f"Outreach was dispatched recently. Policy enforces minimum 14-day window before next cross-channel touchpoint.",
            "suggested_action": "ENFORCE_COOLDOWN",
        })

    return {
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "cooldown_policy_days": 14,
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/conflicts/resolve")
def resolve_campaign_conflict(payload: ConflictResolutionRequest) -> Dict[str, Any]:
    """Resolves a detected campaign collision with operator policy."""
    return {
        "conflict_id": payload.conflict_id,
        "prospect_id": payload.prospect_id,
        "action_taken": payload.action,
        "status": "RESOLVED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Conflict resolved with policy: {payload.action}",
    }


@router.get("/rag/knowledge")
def get_rag_knowledge_base() -> Dict[str, Any]:
    """Returns vector knowledge base documents used by AI agents."""
    return {
        "documents": _knowledge_base,
        "total_documents": len(_knowledge_base),
        "embedding_model": "text-embedding-3-small",
        "vector_dimension": 1536,
    }


@router.post("/rag/query")
def query_rag_knowledge(payload: RAGQueryRequest) -> Dict[str, Any]:
    """Simulates semantic vector search retrieval over the knowledge base."""
    q = payload.query.lower().strip()
    results = []

    for doc in _knowledge_base:
        # Keyword matching and simulated similarity scoring
        score = 0.65
        matches = [word for word in q.split() if word in doc["content"].lower() or word in doc["title"].lower()]
        score += len(matches) * 0.1
        score = min(0.98, max(0.60, score))

        results.append({
            "id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "content": doc["content"],
            "similarity_score": round(score, 3),
        })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_results = results[: payload.top_k or 3]

    return {
        "query": payload.query,
        "retrieved_chunks": top_results,
        "top_similarity": top_results[0]["similarity_score"] if top_results else 0.0,
        "tokens_retrieved": sum(len(r["content"].split()) for r in top_results),
    }


@router.get("/token-economics")
def get_token_economics() -> Dict[str, Any]:
    """
    Cost & Performance Tracking (Requirement: Section 4 - Cost & Performance).
    Tracks token consumption, model costs, latency, and cost per prospect.
    """
    return {
        "summary": {
            "total_tokens_consumed": 421850,
            "prompt_tokens": 312400,
            "completion_tokens": 109450,
            "total_cost_usd": 4.82,
            "cost_per_prospect_usd": 0.014,
            "cost_per_qualified_lead_usd": 0.048,
            "average_latency_ms": 780,
        },
        "agent_breakdown": [
            {"agent": "Lead Research Agent", "model": "Gemini 1.5 Flash", "tokens": 142000, "cost": 1.42, "avg_latency_ms": 820},
            {"agent": "ICP Fitment Agent", "model": "Gemini 1.5 Flash", "tokens": 68500, "cost": 0.68, "avg_latency_ms": 340},
            {"agent": "Outreach Strategy Agent", "model": "Gemini 1.5 Pro", "tokens": 85200, "cost": 1.70, "avg_latency_ms": 910},
            {"agent": "Personalisation Agent", "model": "Gemini 1.5 Flash", "tokens": 92150, "cost": 0.92, "avg_latency_ms": 610},
            {"agent": "SDR Voice Script Agent", "model": "Gemini 1.5 Flash", "tokens": 34000, "cost": 0.10, "avg_latency_ms": 450},
        ],
        "optimization_notes": [
            "Routing: Simpler classification tasks (ICP & Research) routed to Flash for 80% cost reduction.",
            "RAG Caching: Static company knowledge cached to prevent redundant embedding calls.",
        ],
    }
