"""
SDR Autonomous Agent System - Core Schemas
Matches Flow 2, Flow 3, and Flow 4 architecture exactly.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# =====================================================================
# 1. PROSPECT INTAKE & RESEARCH SCHEMAS
# =====================================================================

class RawProspect(BaseModel):
    """Raw prospect discovered via CSV import or agent discovery."""
    prospect_id: str
    campaign_id: str
    name: str
    title: str
    company: str
    domain: str
    location: str
    linkedin_url: Optional[str] = None
    company_size_estimate: Optional[str] = None
    raw_notes: Optional[str] = None


class ResearchDossier(BaseModel):
    """Output from Agent 1: Lead Research & Enrichment Agent."""
    prospect_id: str
    prospect_summary: str = Field(description="2-3 sentence executive summary of the lead")
    detected_tech_stack: List[str] = Field(default_factory=list, description="Technologies used (e.g. AWS, K8s)")
    observed_pain_points: List[str] = Field(default_factory=list, description="Identified operational or technical pain points")
    personalisation_hooks: List[str] = Field(default_factory=list, description="Recent funding, blog posts, hiring, promotions")
    company_initiatives: List[str] = Field(default_factory=list, description="Strategic goals of the prospect's company")


# =====================================================================
# 2. ICP QUALIFICATION SCHEMAS
# =====================================================================

class ICPEvaluation(BaseModel):
    """Output from Agent 2: ICP Fitment Agent."""
    prospect_id: str
    fit_score: int = Field(ge=0, le=100, description="Score between 0 and 100")
    status: Literal["FIT", "REVIEW", "NO_FIT"] = Field(
        description="FIT (>=75), REVIEW (60-74), NO_FIT (<60)"
    )
    # 4-dimension score breakdown (adds rigor for judges)
    role_fit_score: int = Field(default=25, ge=0, le=25, description="Role & seniority fit (0-25)")
    company_fit_score: int = Field(default=25, ge=0, le=25, description="Company size & geography fit (0-25)")
    tech_fit_score: int = Field(default=25, ge=0, le=25, description="Tech stack alignment (0-25)")
    pain_fit_score: int = Field(default=20, ge=0, le=25, description="Operational pain urgency (0-25)")
    score_breakdown: Optional[Dict[str, Any]] = None
    matched_criteria: List[str] = Field(default_factory=list)
    unmatched_criteria: List[str] = Field(default_factory=list)
    negative_icp_triggers: List[str] = Field(default_factory=list)
    reasoning: str = Field(description="Why this prospect was qualified, flagged for review, or disqualified")


# =====================================================================
# 3. OUTREACH STRATEGY SCHEMAS
# =====================================================================

class StrategyAction(BaseModel):
    """Output from Agent 3: Outreach Strategy Agent."""
    prospect_id: str
    trigger_source: Literal["ICP_QUALIFIED", "REPLY_RECEIVED", "TIMER_FIRED", "MANAGER_REJECTED"]
    recommended_channel: Literal["EMAIL", "LINKEDIN", "SMS", "PHONE"]
    action_type: Literal["NEW_OUTREACH", "REPLY", "FOLLOW_UP", "ESCALATE_HUMAN", "CLOSE_CADENCE"]
    angle: str = Field(description="Core hook or angle (e.g. DevOps latency case study)")
    tone: Literal["PEER_ENGINEER", "EXECUTIVE", "CONCISE", "CASUAL"]
    instructions_for_copywriter: str
    suggested_wait_days: int = Field(default=0, description="Days to wait before sending if follow-up")


# =====================================================================
# 4. PERSONALISATION & COPYWRITING SCHEMAS
# =====================================================================

class DraftMessage(BaseModel):
    """Output from Agent 4: Personalisation Agent."""
    prospect_id: str
    channel: Literal["EMAIL", "LINKEDIN", "SMS", "PHONE"]
    subject_line: Optional[str] = None  # None for LinkedIn/SMS
    content: str = Field(description="The drafted outreach body text")
    rag_sources_cited: List[str] = Field(default_factory=list, description="IDs/names of case studies or playbooks used")
    claims_made: List[str] = Field(default_factory=list, description="Specific factual metrics/claims made in the draft")
    mentions_pricing: bool = Field(default=False, description="Flagged true if pricing, discounts, or commercial terms are mentioned")
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.9)


# =====================================================================
# 5. GROUNDING & POLICY GATE SCHEMAS (FLOWS 2, 3, 4)
# =====================================================================

class GroundingResult(BaseModel):
    """Output from Grounding Check component."""
    prospect_id: str
    is_grounded: bool
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims not backed by RAG knowledge base")
    revision_feedback: Optional[str] = Field(default=None, description="Instructions if draft needs revision")


class PolicyGateResult(BaseModel):
    """Output from Policy Gate (Flow 3 & Flow 4 gatekeeper)."""
    prospect_id: str
    allowed_to_send: bool
    status: Literal["ALLOWED", "HELD_APPROVAL", "HELD_PAUSED"]
    needs_approval: bool = Field(default=False, description="True if risky topics like pricing flagged")
    flag_reasons: List[str] = Field(default_factory=list, description="Reasons for holding in Inbox (e.g. 'Mentions pricing')")


# =====================================================================
# 6. CONVERSATION & FOLLOW-UP SCHEMAS
# =====================================================================

class ReplyClassification(BaseModel):
    """Output from Agent 5: Conversation Agent."""
    prospect_id: str
    inbound_message: str
    intent: Literal[
        "INTERESTED_BOOK_MEETING",
        "TECHNICAL_QUESTION",
        "OBJECTION_PRICING",
        "OBJECTION_COMPETITOR",
        "OBJECTION_NO_TIME",
        "NOT_INTERESTED",
        "OUT_OF_OFFICE",
        "UNSUBSCRIBE"
    ]
    sentiment: Literal["POSITIVE", "NEUTRAL", "NEGATIVE"]
    escalate_to_human: bool
    extracted_notes: str


class FollowUpDecision(BaseModel):
    """Output from Agent 6: Follow-up Agent."""
    prospect_id: str
    touch_number: int
    max_allowed_touches: int
    should_follow_up: bool
    recommended_channel_pivot: Optional[Literal["EMAIL", "LINKEDIN", "SMS"]] = None
    follow_up_angle: str
    is_final_breakup: bool
    reason: str


# =====================================================================
# 7. VOICE SDR SCHEMAS
# =====================================================================

class VoiceCallScript(BaseModel):
    """Output from Agent 7: Voice SDR Agent."""
    prospect_id: str
    opening_hook: str = Field(description="15-second pattern interrupt opener")
    qualifying_questions: List[str]
    objection_rebuttals: Dict[str, str] = Field(description="Key-value mapping of common objections to quick pivots")
    closing_ask: str = Field(description="Ask for 15-min calendar slot")


# =====================================================================
# 8. UNIFIED SDR BRAIN & CROSS-CHANNEL STATE (Phase 1)
# =====================================================================

from enum import Enum

class Channel(str, Enum):
    EMAIL = "EMAIL"
    LINKEDIN = "LINKEDIN"
    SMS = "SMS"
    PHONE = "PHONE"


class RepPersona(BaseModel):
    """Loaded once per campaign, injected into every channel-facing agent's system prompt.
    This one object is what makes 5 different agents sound like the same rep."""
    rep_name: str
    rep_title: str
    company_name: str
    tone_descriptors: List[str] = Field(default_factory=lambda: ["direct", "peer-to-peer", "consultative"])
    signature_block: str
    banned_phrases: List[str] = Field(default_factory=lambda: ["just checking in", "circling back", "supercharge", "synergy"])


class Touchpoint(BaseModel):
    """One immutable record of an agent touching a prospect. Every agent appends
    exactly one of these after it acts."""
    touch_id: str
    channel: str
    agent_name: str
    timestamp: str
    prompt_version: str = "v1.0"
    summary: str  # 1-2 sentence compressed summary, NOT full transcript
    claims_made: List[str] = Field(default_factory=list)
    grounding_ok: bool = True
    prospect_response_summary: Optional[str] = None
    sentiment: Optional[str] = None


class CadenceState(BaseModel):
    """Tracks progression across the 3-touch cadence."""
    touches_count: int = 0
    max_allowed_touches: int = 3
    last_channel: Optional[str] = None
    last_touch_at: Optional[str] = None
    next_action_due_at: Optional[str] = None
    is_unsubscribed: bool = False
    is_final_breakup: bool = False
    outcome: Optional[str] = None  # MEETING_BOOKED, DISQUALIFIED, UNRESPONSIVE


class UnifiedProspectState(BaseModel):
    """The single SDR brain. One instance per prospect per campaign."""
    prospect_id: str
    campaign_id: str
    rep_persona: RepPersona
    dossier: Optional[Dict[str, Any]] = None
    icp_evaluation: Optional[Dict[str, Any]] = None
    current_strategy: Optional[Dict[str, Any]] = None
    interaction_history: List[Touchpoint] = Field(default_factory=list)
    cadence: CadenceState = Field(default_factory=CadenceState)
    escalated_to_human: bool = False

    def rolling_context_summary(self, max_touches: int = 3) -> str:
        """Cheap-token context for the NEXT agent call — last N touch summaries."""
        if not self.interaction_history:
            return "No prior touches with this prospect."
        recent = self.interaction_history[-max_touches:]
        return "\n".join(f"[{t.channel} / {t.agent_name}] {t.summary}" for t in recent)


# =====================================================================
# 9. TELEMETRY & COST ACCOUNTING (Phase 1)
# =====================================================================

class CallRecord(BaseModel):
    """Logs token consumption, latency, and model routing per call."""
    timestamp: str
    agent_name: str
    model: str
    prospect_id: str
    campaign_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    grounding_passed: Optional[bool] = None
    hitl_flagged: Optional[bool] = None

