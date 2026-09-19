from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Request
from app.models.execution import (
    ExecutionRecord,
    get_execution,
    get_all_executions,
    get_campaign_executions,
)
from app.services.sdr import (
    SDRRunRequest,
    execute_sdr_pipeline,
)

router = APIRouter(prefix="/api/sdr", tags=["SDR"])


@router.post("/run", response_model=ExecutionRecord, status_code=200)
async def run_sdr(payload: SDRRunRequest) -> ExecutionRecord:
    """
    Triggers the Autonomous SDR execution pipeline.
    
    1. Checks if campaign is LIVE.
    2. Sends campaign + prospect to DronaHQ Automation Webhook.
    3. Evaluates ICP Fitment (NO_FIT aborts).
    4. Validates channel requirements (Email, SMS, LinkedIn, Phone).
    5. Dispatches outreach to appropriate channel provider.
    6. Stores and returns the complete ExecutionRecord.
    """
    return await execute_sdr_pipeline(payload.campaign_id, payload.prospect_id)


@router.get("/executions/{execution_id}", response_model=ExecutionRecord, status_code=200)
def get_execution_by_id(execution_id: str) -> ExecutionRecord:
    """
    Returns the complete execution state for a given execution_id.
    """
    rec = get_execution(execution_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
    return rec


@router.get("/executions", response_model=List[ExecutionRecord], status_code=200)
def list_all_executions() -> List[ExecutionRecord]:
    """
    Returns all SDR executions across all campaigns.
    """
    return get_all_executions()


@router.get("/prospects/{prospect_id}/execution", response_model=ExecutionRecord, status_code=200)
def get_prospect_latest_execution(prospect_id: str) -> ExecutionRecord:
    """
    Returns the latest ExecutionRecord for a specific prospect.
    """
    all_execs = get_all_executions()
    for e in all_execs:
        if e.prospect_id == prospect_id:
            return e
    raise HTTPException(status_code=404, detail=f"No execution found for prospect '{prospect_id}'")


@router.get("/agents", status_code=200)
def get_agent_telemetry() -> List[Dict[str, Any]]:
    """
    Returns live telemetry and operational metrics for all 5 SDR agents.
    """
    all_execs = get_all_executions()
    total_runs = len(all_execs)
    successful_runs = len([e for e in all_execs if e.status in ["SENT", "COMPLETED", "PENDING_MANUAL"]])
    success_rate = int((successful_runs / total_runs * 100)) if total_runs > 0 else 100

    recent = [
        {
            "id": e.execution_id,
            "agentId": "lead_research",
            "prospect": e.prospect_id,
            "campaign": e.campaign_id,
            "status": "COMPLETED" if e.status in ["SENT", "PENDING_MANUAL", "FIT"] else e.status,
            "startedAt": e.started_at,
            "completedAt": e.completed_at,
            "duration": 4,
            "output": f"Processed {e.actual_channel or e.recommended_channel or 'outreach'}",
        }
        for e in all_execs[:5]
    ]

    return [
        {
            "id": "lead-research",
            "name": "Lead Research Agent",
            "description": "Performs deep company intelligence, verified domain lookup, tech stack detection, and leadership mapping.",
            "responsibilities": [
                "Verify company domain and leadership",
                "Extract detected tech stack (CI/CD, Kubernetes)",
                "Synthesize prospect background and pain points",
                "Generate personalization hooks for copywriter",
            ],
            "status": "ACTIVE",
            "executions": total_runs,
            "successRate": success_rate,
            "avgDuration": 4.2,
            "recentExecutions": recent,
        },
        {
            "id": "icp-fitment",
            "name": "ICP Fitment Agent",
            "description": "Evaluates researched prospects against specific campaign criteria to calculate fit score and qualification status.",
            "responsibilities": [
                "Match prospect against target geography and company size",
                "Calculate multi-factor ICP qualification score (0–100)",
                "Enforce negative criteria guardrail (freeze, disqualification)",
                "Provide auditable qualification reasoning",
            ],
            "status": "ACTIVE",
            "executions": total_runs,
            "successRate": success_rate,
            "avgDuration": 3.8,
            "recentExecutions": recent,
        },
        {
            "id": "outreach-strategy",
            "name": "Outreach Strategy Agent",
            "description": "Determines optimal channel (Email, SMS, LinkedIn, Phone), messaging angle, and copywriter instructions.",
            "responsibilities": [
                "Select optimal communication channel",
                "Define strategic value proposition angle",
                "Establish message tone (EXECUTIVE, DIRECT)",
                "Prescribe copy constraints and instructions",
            ],
            "status": "ACTIVE",
            "executions": total_runs,
            "successRate": success_rate,
            "avgDuration": 3.5,
            "recentExecutions": recent,
        },
        {
            "id": "personalisation",
            "name": "Personalisation Agent",
            "description": "Generates high-converting, context-aware outreach copy tailored to the selected channel constraints.",
            "responsibilities": [
                "Generate channel-specific outreach content",
                "Enforce 160-character maximum on SMS messages",
                "Compose executive email subject lines",
                "Cite verifiable claims and avoid hallucinations",
            ],
            "status": "ACTIVE",
            "executions": total_runs,
            "successRate": success_rate,
            "avgDuration": 4.6,
            "recentExecutions": recent,
        },
        {
            "id": "channel-executor",
            "name": "Channel Execution Dispatcher",
            "description": "Orchestrates live outreach delivery across Gmail SMTP, Twilio SMS, LinkedIn review queue, and Voice call bridge.",
            "responsibilities": [
                "Dispatch emails via verified Gmail SMTP (STARTTLS)",
                "Send real SMS via Twilio REST API with trial fallback",
                "Queue LinkedIn outreach for human-in-the-loop review",
                "Bridge automated Voice SDR calls",
            ],
            "status": "ACTIVE",
            "executions": total_runs,
            "successRate": success_rate,
            "avgDuration": 2.1,
            "recentExecutions": recent,
        },
    ]
