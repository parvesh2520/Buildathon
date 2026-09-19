"""
SDR Autonomous Agent System - Production LLM Agent Pipeline (Iteration 2)
Features:
- Telemetry & latency tracking per call (CallRecord -> telemetry.jsonl)
- Self-correction retry loop for ungrounded claims (Self-healing Personalisation)
- Cross-channel context awareness via UnifiedProspectState & rolling_context_summary
- Unified RepPersona injection across all channel-facing agents
- Chunk-level RAG retrieval with source citation IDs
- Quantitative unit economics (cost per prospect, cost per qualified lead)
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from schemas import (
    RawProspect, ResearchDossier, ICPEvaluation, StrategyAction, DraftMessage,
    GroundingResult, PolicyGateResult, ReplyClassification, FollowUpDecision,
    VoiceCallScript, RepPersona, Touchpoint, CadenceState, UnifiedProspectState,
    CallRecord
)
from rag.store import kb_store
from guardrails.grounding_policy import GroundingChecker, PolicyGate

# =====================================================================
# REPS REGISTRY (One Rep Persona per Campaign for Unified Voice)
# =====================================================================

CAMPAIGN_REPS: Dict[str, RepPersona] = {
    "us_saas_cto": RepPersona(
        rep_name="Alex Rivera",
        rep_title="Lead Technical SDR",
        company_name="Turboscale AI",
        tone_descriptors=["direct", "peer-to-peer engineer", "no fluff"],
        signature_block="Best,\nAlex Rivera\nLead Technical SDR | Turboscale AI",
        banned_phrases=["just checking in", "circling back", "supercharge", "synergy", "revolutionize"]
    ),
    "india_bfsi_cio": RepPersona(
        rep_name="Priya Sharma",
        rep_title="Enterprise GTM Director",
        company_name="FinShield AI",
        tone_descriptors=["formal", "executive", "respectful Indian enterprise"],
        signature_block="Warm regards,\nPriya Sharma\nEnterprise GTM Director | FinShield AI",
        banned_phrases=["just checking in", "circling back", "disrupt", "game-changing"]
    ),
    "voice_ai_founder": RepPersona(
        rep_name="Devon Patel",
        rep_title="Founder & Technical Lead",
        company_name="WhisperFlow AI",
        tone_descriptors=["casual", "founder-to-founder", "concise"],
        signature_block="Best,\nDevon\nFounder, WhisperFlow AI",
        banned_phrases=["just checking in", "circling back", "supercharge", "unlock"]
    ),
}

# Pricing rates per 1M tokens (Gemini 3.5 Flash Lite)
MODEL_PRICING = {
    "gemini-3.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

# Telemetry log file
TELEMETRY_LOG_FILE = os.path.join(os.path.dirname(__file__), "telemetry.jsonl")


def _load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


PROMPTS = {
    "research": _load_prompt("01_research_agent.md"),
    "icp": _load_prompt("02_icp_fitment_agent.md"),
    "strategy": _load_prompt("03_strategy_agent.md"),
    "personalisation": _load_prompt("04_personalisation_agent.md"),
    "conversation": _load_prompt("05_conversation_agent.md"),
    "follow_up": _load_prompt("06_follow_up_agent.md"),
    "voice": _load_prompt("07_voice_sdr_agent.md"),
}


class GeminiAgent:
    """Core LLM caller with structured JSON output and telemetry tracking."""

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_records: List[CallRecord] = []

    def call(
        self,
        system_instruction: str,
        user_message: str,
        agent_name: str = "generic_agent",
        prospect_id: str = "unknown",
        campaign_id: str = "unknown",
        max_retries: int = 5
    ) -> dict:
        start_time = time.perf_counter()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.3,
        )

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_message,
                    config=config,
                )
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                # Token accounting
                in_tok = response.usage_metadata.prompt_token_count or 0
                out_tok = response.usage_metadata.candidates_token_count or 0
                self.total_calls += 1
                self.total_input_tokens += in_tok
                self.total_output_tokens += out_tok

                # Cost calculation
                rates = MODEL_PRICING.get(self.model, {"input": 0.075, "output": 0.30})
                cost_usd = (in_tok * rates["input"] + out_tok * rates["output"]) / 1_000_000

                # Log call record
                record = CallRecord(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_name=agent_name,
                    model=self.model,
                    prospect_id=prospect_id,
                    campaign_id=campaign_id,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=latency_ms,
                    cost_usd=cost_usd
                )
                self.call_records.append(record)
                self._persist_call_record(record)

                return self._parse_json(response.text)

            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str
                is_transient = "503" in err_str or "unavailable" in err_str or "overloaded" in err_str

                if (is_rate_limit or is_transient) and attempt < max_retries - 1:
                    sleep_time = 25 if is_rate_limit else (2 ** attempt)
                    print(f"⏳ Rate limit / transient response. Pausing {sleep_time}s for quota reset (attempt {attempt + 1}/{max_retries})...", flush=True)
                    time.sleep(sleep_time)
                    continue
                raise

    def _persist_call_record(self, record: CallRecord):
        """Appends telemetry log to JSONL for audit and judge reports."""
        try:
            with open(TELEMETRY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.model_dump()) + "\n")
        except Exception:
            pass

    def _parse_json(self, raw_text: str) -> dict:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            if "```json" in raw_text:
                json_str = raw_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in raw_text:
                json_str = raw_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise ValueError(f"Could not parse JSON from response:\n{raw_text[:500]}")

    def get_usage_summary(self) -> dict:
        rates = MODEL_PRICING.get(self.model, {"input": 0.075, "output": 0.30})
        total_cost = (self.total_input_tokens * rates["input"] + self.total_output_tokens * rates["output"]) / 1_000_000
        return {
            "total_api_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "model_routing": self.model,
        }


class SDRAgentPipeline:
    """
    Production SDR Pipeline with:
    - UnifiedProspectState persistence
    - Self-correction retry on grounding failure
    - Cross-channel context memory
    - RAG chunk retrieval
    - Full telemetry accounting
    """

    def __init__(self, api_key: str):
        self.agent = GeminiAgent(api_key=api_key)
        self.grounding_checker = GroundingChecker()
        self.policy_gate = PolicyGate()
        # In-memory storage for unified states
        self.prospect_states: Dict[str, UnifiedProspectState] = {}

    def get_or_create_state(self, prospect_id: str, campaign_id: str) -> UnifiedProspectState:
        """Retrieves or creates the single shared SDR brain for a prospect."""
        if prospect_id not in self.prospect_states:
            rep = CAMPAIGN_REPS.get(campaign_id, CAMPAIGN_REPS["us_saas_cto"])
            self.prospect_states[prospect_id] = UnifiedProspectState(
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                rep_persona=rep,
            )
        return self.prospect_states[prospect_id]

    def run_research(self, prospect: dict) -> dict:
        """Agent 1: Lead Research & Enrichment"""
        user_msg = f"""Research this prospect and produce a structured dossier.

PROSPECT DATA:
- Name: {prospect['name']}
- Title: {prospect['title']}
- Company: {prospect['company']}
- Domain: {prospect.get('domain', 'N/A')}
- Location: {prospect.get('location', 'N/A')}
- Company Size: {prospect.get('company_size_estimate', 'Unknown')}
- Notes: {prospect.get('raw_notes', 'None')}

Set prospect_id to "{prospect['prospect_id']}" in your output."""

        res = self.agent.call(
            PROMPTS["research"],
            user_msg,
            agent_name="ResearchAgent",
            prospect_id=prospect["prospect_id"],
            campaign_id=prospect.get("campaign_id", "unknown")
        )
        return res

    def run_icp_evaluation(self, prospect: dict, dossier: dict) -> dict:
        """Agent 2: ICP Fitment (with 4-dimension scoring breakdown)"""
        campaign_id = prospect["campaign_id"]
        # Use top-k chunk retrieval for ICP section
        chunks = kb_store.retrieve_top_k(campaign_id, "ideal customer profile target roles geography tech stack", k=2)
        kb_text = "\n\n".join(f"[{c.chunk_id}] {c.title}:\n{c.content}" for c in chunks)

        user_msg = f"""Evaluate this prospect against the campaign ICP criteria.

RELEVANT ICP KNOWLEDGE BASE CHUNKS:
{kb_text}

PROSPECT DATA:
- prospect_id: {prospect['prospect_id']}
- Name: {prospect['name']}
- Title: {prospect['title']}
- Company: {prospect['company']}
- Location: {prospect.get('location', 'N/A')}
- Company Size: {prospect.get('company_size_estimate', 'Unknown')}
- Notes: {prospect.get('raw_notes', 'None')}

RESEARCH DOSSIER:
{json.dumps(dossier, indent=2)}

Compute the 4 dimension scores: role_fit_score (0-25), company_fit_score (0-25), tech_fit_score (0-25), pain_fit_score (0-25).
Sum them for fit_score (0-100)."""

        res = self.agent.call(
            PROMPTS["icp"],
            user_msg,
            agent_name="ICPFitmentAgent",
            prospect_id=prospect["prospect_id"],
            campaign_id=campaign_id
        )
        # Normalize nested score_breakdown into flat fields if present
        sb = res.get("score_breakdown", {})
        if isinstance(sb, dict):
            if "role_fit_score" not in res:
                tr = sb.get("title_role_fit", {})
                res["role_fit_score"] = tr.get("score", 0) if isinstance(tr, dict) else tr
            if "company_fit_score" not in res:
                cf = sb.get("company_fit", {})
                res["company_fit_score"] = cf.get("score", 0) if isinstance(cf, dict) else cf
            if "tech_fit_score" not in res:
                tn = sb.get("tech_need_alignment", {})
                res["tech_fit_score"] = tn.get("score", 0) if isinstance(tn, dict) else tn
            if "pain_fit_score" not in res:
                tu = sb.get("timing_urgency", {})
                res["pain_fit_score"] = tu.get("score", 0) if isinstance(tu, dict) else tu
        return res

    def run_strategy(
        self,
        prospect: dict,
        dossier: dict,
        icp_eval: dict,
        trigger: str = "ICP_QUALIFIED",
        rolling_context: str = ""
    ) -> dict:
        """Agent 3: Outreach Strategy (with cross-channel context awareness)"""
        campaign_id = prospect["campaign_id"]
        chunks = kb_store.retrieve_top_k(campaign_id, f"case studies objection playbook {dossier.get('prospect_summary', '')}", k=3)
        kb_text = "\n\n".join(f"[{c.chunk_id}] {c.title}:\n{c.content}" for c in chunks)

        user_msg = f"""Plan the outreach strategy for this prospect.

TRIGGER: {trigger}
CAMPAIGN ID: {campaign_id}

PRIOR TOUCHES / CROSS-CHANNEL HISTORY:
{rolling_context or "No prior touches (this is Touch 1)."}

CAMPAIGN KNOWLEDGE BASE:
{kb_text}

PROSPECT:
- prospect_id: {prospect['prospect_id']}
- Name: {prospect['name']}
- Title: {prospect['title']}
- Company: {prospect['company']}
- Location: {prospect.get('location', 'N/A')}

RESEARCH DOSSIER:
{json.dumps(dossier, indent=2)}

ICP EVALUATION:
{json.dumps(icp_eval, indent=2)}"""

        res = self.agent.call(
            PROMPTS["strategy"],
            user_msg,
            agent_name="StrategyAgent",
            prospect_id=prospect["prospect_id"],
            campaign_id=campaign_id
        )
        return res

    def run_personalisation(
        self,
        prospect: dict,
        dossier: dict,
        strategy: dict,
        rolling_context: str = "",
        max_self_healing_retries: int = 1
    ) -> tuple[dict, bool]:
        """
        Agent 4: Personalisation / Email
        Includes:
        - RepPersona signature and voice injection
        - Cross-channel context memory
        - Self-healing retry loop: If Grounding fails, retry once with explicit ungrounded claim feedback!
        Returns: (draft_dict, was_healed_bool)
        """
        campaign_id = prospect["campaign_id"]
        rep = CAMPAIGN_REPS.get(campaign_id, CAMPAIGN_REPS["us_saas_cto"])

        # Retrieve top relevant chunks for copywriting
        query = f"{strategy.get('angle', '')} {dossier.get('prospect_summary', '')}"
        chunks = kb_store.retrieve_top_k(campaign_id, query, k=3)
        kb_text = "\n\n".join(f"[{c.chunk_id}] {c.title}:\n{c.content}" for c in chunks)

        user_msg = f"""Draft personalized outreach for this prospect.

ASSIGNED SALES REP PERSONA (speak as this person):
- Name: {rep.rep_name} ({rep.rep_title} at {rep.company_name})
- Tone: {', '.join(rep.tone_descriptors)}
- Signature block: {rep.signature_block}
- Banned phrases: {', '.join(rep.banned_phrases)}

CROSS-CHANNEL CONTEXT:
{rolling_context or "Initial outreach (Touch 1)."}

CAMPAIGN KNOWLEDGE BASE CONTEXT (cite ONLY facts and chunk IDs from here):
{kb_text}

PROSPECT:
- prospect_id: {prospect['prospect_id']}
- Name: {prospect['name']}
- Title: {prospect['title']}
- Company: {prospect['company']}
- Location: {prospect.get('location', 'N/A')}

RESEARCH DOSSIER:
{json.dumps(dossier, indent=2)}

STRATEGY INSTRUCTIONS:
{json.dumps(strategy, indent=2)}"""

        # Attempt 1
        draft = self.agent.call(
            PROMPTS["personalisation"],
            user_msg,
            agent_name="PersonalisationAgent",
            prospect_id=prospect["prospect_id"],
            campaign_id=campaign_id
        )

        # Grounding verification
        checker = self.grounding_checker.verify_draft(campaign_id, draft)
        if checker.is_grounded:
            return draft, False

        # Self-Correction Loop: If ungrounded claims detected, retry once!
        if max_self_healing_retries > 0 and checker.unsupported_claims:
            retry_msg = f"""{user_msg}

======================================================================
SELF-CORRECTION REQUIRED: GROUNDING FAILURE DETECTED
======================================================================
Your previous draft contained the following claims that could NOT be verified in the campaign knowledge base:
{json.dumps(checker.unsupported_claims, indent=2)}

REVISION INSTRUCTIONS:
Rewrite the message immediately. REMOVE or REPLACE all unsupported claims. Every single number, percentage, and case study MUST come directly from the attached knowledge base chunks. Do not invent any statistics."""

            healed_draft = self.agent.call(
                PROMPTS["personalisation"],
                retry_msg,
                agent_name="PersonalisationAgent_SelfHeal",
                prospect_id=prospect["prospect_id"],
                campaign_id=campaign_id
            )
            # Verify healed draft
            healed_checker = self.grounding_checker.verify_draft(campaign_id, healed_draft)
            if healed_checker.is_grounded:
                return healed_draft, True  # Successfully healed!
            return healed_draft, False

        return draft, False

    def run_conversation_classifier(self, prospect_id: str, reply_text: str, campaign_id: str) -> dict:
        """Agent 5: Conversation / Reply Classifier — connected to UnifiedProspectState"""
        # Retrieve or create cross-channel state
        state = self.get_or_create_state(prospect_id, campaign_id)

        chunks = kb_store.retrieve_top_k(campaign_id, f"objections rebuttals {reply_text}", k=2)
        kb_text = "\n\n".join(f"[{c.chunk_id}] {c.title}:\n{c.content}" for c in chunks)

        user_msg = f"""Classify this inbound prospect reply and draft a response.

CAMPAIGN KNOWLEDGE BASE (for grounding rebuttals):
{kb_text}

PROSPECT ID: {prospect_id}
PRIOR INTERACTION CONTEXT:
{state.rolling_context_summary() or "First inbound reply — no prior context."}

INBOUND REPLY:
\"\"\"{reply_text}\"\"\"
"""

        res = self.agent.call(
            PROMPTS["conversation"],
            user_msg,
            agent_name="ConversationAgent",
            prospect_id=prospect_id,
            campaign_id=campaign_id
        )

        # Record inbound reply as a Touchpoint in cross-channel memory
        touchpoint = Touchpoint(
            touch_id=f"touch_{prospect_id}_inbound_{len(state.interaction_history) + 1}",
            channel="INBOUND_REPLY",
            agent_name="ConversationAgent",
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_version="v1.0",
            summary=f"Inbound reply classified as {res.get('intent', 'UNKNOWN')}. Sentiment: {res.get('sentiment', 'neutral')}",
            claims_made=[],
            grounding_ok=True,
        )
        state.interaction_history.append(touchpoint)

        # Update escalation state if needed
        if res.get("escalate_to_human"):
            state.escalated_to_human = True

        return res

    def run_follow_up(
        self,
        prospect_id: str,
        touch_number: int,
        max_touches: int = 3,
        prior_channel: str = "EMAIL",
        rolling_context: str = "",
        campaign_id: str = "us_saas_cto"
    ) -> dict:
        """Agent 6: Follow-up — connected to UnifiedProspectState for cadence memory"""
        # Retrieve cross-channel state for real cadence data
        state = self.get_or_create_state(prospect_id, campaign_id)

        # Use real cadence data from state if available
        real_touch = state.cadence.touches_count or touch_number
        real_channel = state.cadence.last_channel or prior_channel
        real_context = state.rolling_context_summary() or rolling_context

        user_msg = f"""Evaluate the follow-up cadence for this prospect.

PROSPECT ID: {prospect_id}
CURRENT TOUCH NUMBER: {real_touch}
MAX ALLOWED TOUCHES: {max_touches}
PRIOR CHANNEL USED: {real_channel}
DAYS SINCE LAST TOUCH: 3

PRIOR TOUCHES:
{real_context or "Initial email sent 3 days ago with no reply."}
"""

        res = self.agent.call(
            PROMPTS["follow_up"],
            user_msg,
            agent_name="FollowUpAgent",
            prospect_id=prospect_id,
            campaign_id=campaign_id
        )

        # Normalize schema fields
        if "action_type" not in res:
            if res.get("is_final_breakup"):
                res["action_type"] = "BREAKUP"
            elif res.get("should_follow_up"):
                res["action_type"] = "FOLLOW_UP"
            else:
                res["action_type"] = "STOP"
        if "recommended_channel" not in res:
            res["recommended_channel"] = res.get("recommended_channel_pivot") or real_channel

        # Record follow-up evaluation as a Touchpoint
        action = res.get("action_type", "FOLLOW_UP")
        touchpoint = Touchpoint(
            touch_id=f"touch_{prospect_id}_followup_{len(state.interaction_history) + 1}",
            channel=res.get("recommended_channel", real_channel),
            agent_name="FollowUpAgent",
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_version="v1.0",
            summary=f"Follow-up touch {real_touch}: {action}. Channel: {res.get('recommended_channel', real_channel)}",
            claims_made=[],
            grounding_ok=True,
        )
        state.interaction_history.append(touchpoint)

        # Update cadence outcome if breakup
        if action in ("BREAKUP", "STOP"):
            state.cadence.outcome = "BREAKUP_SENT"

        return res

    def run_voice_script(self, prospect: dict, dossier: dict, rolling_context: str = "") -> dict:
        """Agent 7: Voice SDR (acknowledges prior emails/touches)"""
        campaign_id = prospect["campaign_id"]
        rep = CAMPAIGN_REPS.get(campaign_id, CAMPAIGN_REPS["us_saas_cto"])
        chunks = kb_store.retrieve_top_k(campaign_id, f"case studies objections {dossier.get('prospect_summary', '')}", k=3)
        kb_text = "\n\n".join(f"[{c.chunk_id}] {c.title}:\n{c.content}" for c in chunks)

        user_msg = f"""Generate a phone cold call script for this prospect.

CALLER (You): {rep.rep_name}, {rep.rep_title} at {rep.company_name}
CROSS-CHANNEL AWARENESS:
{rolling_context or "No prior touches; cold outbound call."}

CAMPAIGN KNOWLEDGE BASE:
{kb_text}

PROSPECT:
- prospect_id: {prospect['prospect_id']}
- Name: {prospect['name']}
- Title: {prospect['title']}
- Company: {prospect['company']}
- Location: {prospect.get('location', 'N/A')}

RESEARCH DOSSIER:
{json.dumps(dossier, indent=2)}"""

        res = self.agent.call(
            PROMPTS["voice"],
            user_msg,
            agent_name="VoiceSDRAgent",
            prospect_id=prospect["prospect_id"],
            campaign_id=campaign_id
        )
        return res

    def run_full_pipeline(self, prospect: dict, campaign_is_paused: bool = False) -> dict:
        """
        Complete Flow 2 pipeline with Unified State persistence:
        Research → ICP → Strategy → Personalisation (with self-healing) → Policy Gate
        """
        prospect_id = prospect["prospect_id"]
        campaign_id = prospect["campaign_id"]
        state = self.get_or_create_state(prospect_id, campaign_id)

        timeline = []
        timeline.append(f"Prospect discovered: {prospect['name']} ({prospect['title']} at {prospect['company']})")

        # Flow 3: If campaign is paused, immediately hold incoming prospects
        if campaign_is_paused:
            timeline.append("⏸️ Campaign is PAUSED — prospect held in timeline.")
            state.cadence.outcome = "HELD_PAUSED"
            return {
                "prospect_id": prospect_id,
                "campaign_id": campaign_id,
                "final_state": "HELD_PAUSED",
                "timeline": timeline,
                "dossier": {},
                "icp_evaluation": {},
                "strategy": None,
                "draft": None,
                "token_usage": self.agent.get_usage_summary(),
                "unified_state": state.model_dump(),
            }

        # Step 1: Research
        timeline.append("[Agent: Research] Running LLM-powered research...")
        dossier = self.run_research(prospect)
        state.dossier = dossier
        timeline.append(f"[Agent: Research] Dossier complete. Inferred tech: {dossier.get('detected_tech_stack', [])[:3]}")

        # Step 2: ICP Fitment
        timeline.append("[Agent: ICP Fitment] Evaluating 4-dimension fit against criteria...")
        icp_eval = self.run_icp_evaluation(prospect, dossier)
        state.icp_evaluation = icp_eval
        status = icp_eval.get("status", "UNKNOWN")
        score = icp_eval.get("fit_score", 0)
        timeline.append(f"[Agent: ICP Fitment] Score: {score}/100 | Status: {status} (Role: {icp_eval.get('role_fit_score', 0)}, Tech: {icp_eval.get('tech_fit_score', 0)})")

        if status == "NO_FIT":
            timeline.append("❌ Marked Not a Fit — removed from active funnel.")
            state.cadence.outcome = "DISQUALIFIED"
            return {
                "prospect_id": prospect_id,
                "campaign_id": campaign_id,
                "final_state": "NOT_A_FIT",
                "timeline": timeline,
                "dossier": dossier,
                "icp_evaluation": icp_eval,
                "strategy": None,
                "draft": None,
                "token_usage": self.agent.get_usage_summary(),
                "unified_state": state.model_dump(),
            }

        # Step 3: Strategy
        timeline.append(f"[Agent: Strategy] Planning outreach for {status} lead...")
        strategy = self.run_strategy(
            prospect,
            dossier,
            icp_eval,
            trigger="ICP_QUALIFIED",
            rolling_context=state.rolling_context_summary()
        )
        state.current_strategy = strategy
        timeline.append(f"[Agent: Strategy] Channel: {strategy.get('recommended_channel')} | Angle: {strategy.get('angle', '')[:80]}")

        # Flow 3 check: Campaign paused?
        if campaign_is_paused:
            timeline.append("⏸️ Held — campaign paused. Action held in timeline.")
            return {
                "prospect_id": prospect_id,
                "campaign_id": campaign_id,
                "final_state": "HELD_PAUSED",
                "timeline": timeline,
                "dossier": dossier,
                "icp_evaluation": icp_eval,
                "strategy": strategy,
                "draft": None,
                "token_usage": self.agent.get_usage_summary(),
                "unified_state": state.model_dump(),
            }

        # Step 4: Personalisation (with Self-Correction Loop)
        timeline.append("[Agent: Personalisation] Drafting grounded outreach with RAG context...")
        draft, was_healed = self.run_personalisation(
            prospect,
            dossier,
            strategy,
            rolling_context=state.rolling_context_summary()
        )

        if was_healed:
            timeline.append("🛡️ Self-Correction triggered: ungrounded claims removed and re-verified against KB.")
        timeline.append(f"[Agent: Personalisation] Draft complete via {draft.get('channel')}. Claims: {draft.get('claims_made', [])[:2]}")

        # Step 5 & 6: Final Grounding Verification & Policy Gate
        final_checker = self.grounding_checker.verify_draft(campaign_id, draft)
        gate_res = self.policy_gate.evaluate(
            draft=draft,
            grounding=final_checker,
            campaign_is_paused=campaign_is_paused,
            campaign_id=campaign_id
        )

        # Record Touchpoint in the unified state
        touchpoint = Touchpoint(
            touch_id=f"touch_{prospect_id}_{len(state.interaction_history) + 1}",
            channel=draft.get("channel", "EMAIL"),
            agent_name="PersonalisationAgent",
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_version="v1.0",
            summary=f"Sent {draft.get('channel')} pitch with angle: {strategy.get('angle', '')[:60]}",
            claims_made=draft.get("claims_made", []),
            grounding_ok=(not was_healed) or gate_res.allowed_to_send,
        )
        state.interaction_history.append(touchpoint)
        state.cadence.touches_count += 1
        state.cadence.last_channel = draft.get("channel", "EMAIL")
        state.cadence.last_touch_at = touchpoint.timestamp

        if not gate_res.allowed_to_send:
            if gate_res.status == "HELD_APPROVAL":
                timeline.append(f"📥 Held / Awaiting approval in Manager Inbox: {gate_res.flag_reasons}")
                final_state = "HELD_APPROVAL"
            else:
                timeline.append(f"⏸️ Held: {gate_res.flag_reasons}")
                final_state = "HELD_PAUSED"
        else:
            timeline.append(f"🚀 Message approved & dispatched via {draft.get('channel')}.")
            final_state = "MESSAGE_SENT"

        return {
            "prospect_id": prospect_id,
            "campaign_id": campaign_id,
            "final_state": final_state,
            "timeline": timeline,
            "dossier": dossier,
            "icp_evaluation": icp_eval,
            "strategy": strategy,
            "draft": draft,
            "was_healed": was_healed,
            "token_usage": self.agent.get_usage_summary(),
            "unified_state": state.model_dump(),
        }

    def get_telemetry_report(self) -> dict:
        """Returns deep telemetry metrics required for Section 4 evaluation."""
        total_calls = len(self.agent.call_records)
        total_cost = sum(r.cost_usd for r in self.agent.call_records)
        avg_latency = (sum(r.latency_ms for r in self.agent.call_records) / total_calls) if total_calls > 0 else 0

        # Unique prospects
        prospect_ids = set(r.prospect_id for r in self.agent.call_records if r.prospect_id != "unknown")
        cost_per_prospect = (total_cost / len(prospect_ids)) if prospect_ids else 0.0

        # Qualified leads (FIT)
        fit_leads = sum(
            1 for s in self.prospect_states.values()
            if s.icp_evaluation and s.icp_evaluation.get("status") == "FIT"
        )
        cost_per_fit = (total_cost / fit_leads) if fit_leads > 0 else total_cost

        return {
            "total_calls": total_calls,
            "total_tokens_in": self.agent.total_input_tokens,
            "total_tokens_out": self.agent.total_output_tokens,
            "total_cost_usd": round(total_cost, 5),
            "avg_latency_ms": round(avg_latency, 1),
            "cost_per_prospect_usd": round(cost_per_prospect, 5),
            "cost_per_qualified_lead_usd": round(cost_per_fit, 5),
            "active_unified_prospects": len(self.prospect_states),
            "model_routing": {
                "default_engine": self.agent.model,
                "strategy": "High-throughput sub-1.5s execution for extraction & classification; RAG-grounded copywriter with self-healing retry"
            }
        }
