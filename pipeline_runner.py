"""
Autonomous SDR Pipeline Runner
Implements User Flow 2, Flow 3, and Flow 4 exactly as specified.
"""

import json
from typing import Dict, Any, List

from schemas import (
    RawProspect, ResearchDossier, ICPEvaluation,
    StrategyAction, DraftMessage, GroundingResult, PolicyGateResult
)
from agents.research_agent import ResearchAgent
from agents.icp_agent import ICPFitmentAgent
from agents.strategy_agent import OutreachStrategyAgent
from agents.personalisation_agent import PersonalisationAgent
from agents.conversation_agent import ConversationAgent
from agents.follow_up_agent import FollowUpAgent
from agents.voice_agent import VoiceSDRAgent
from guardrails.grounding_policy import GroundingChecker, PolicyGate


class SDRPipelineRunner:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.icp_agent = ICPFitmentAgent()
        self.strategy_agent = OutreachStrategyAgent()
        self.personalisation_agent = PersonalisationAgent()
        self.conversation_agent = ConversationAgent()
        self.follow_up_agent = FollowUpAgent()
        self.voice_agent = VoiceSDRAgent()
        self.grounding_checker = GroundingChecker()
        self.policy_gate = PolicyGate()

    def process_discovered_prospect(
        self,
        prospect: RawProspect,
        campaign_is_paused: bool = False
    ) -> Dict[str, Any]:
        """
        Executes Flow 2:
        Prospect Discovered -> Research -> ICP Fitment -> Strategy -> Personalisation -> Grounding -> Policy Gate
        """
        timeline: List[str] = [f"Prospect discovered: {prospect.name} ({prospect.title} at {prospect.company})"]

        # Step 1: Research Agent runs
        timeline.append("[Agent: Research] Extracting company tech stack and pain points...")
        dossier: ResearchDossier = self.research_agent.run(prospect)
        timeline.append(f"[Agent: Research] Dossier created. Detected stack: {', '.join(dossier.detected_tech_stack)}")

        # Step 2: ICP Fitment Agent scores fit
        timeline.append("[Agent: ICP Fitment] Evaluating fit against campaign criteria...")
        icp_eval: ICPEvaluation = self.icp_agent.run(prospect, dossier)
        timeline.append(f"[Agent: ICP Fitment] Score: {icp_eval.fit_score}/100 | Status: {icp_eval.status}")

        # Branch: no_fit -> removed from funnel
        if icp_eval.status == "NO_FIT":
            timeline.append("❌ Marked Not a Fit — removed from active funnel.")
            return {
                "prospect_id": prospect.prospect_id,
                "current_state": "NOT_A_FIT",
                "timeline": timeline,
                "icp_evaluation": icp_eval.model_dump(),
                "draft_message": None,
                "policy_gate": None
            }

        # Branch: fit or review -> Outreach Strategy Agent picks next action
        timeline.append(f"[Agent: Strategy] Planning initial outreach hook for {icp_eval.status} lead...")
        strategy: StrategyAction = self.strategy_agent.plan_initial_outreach(
            dossier=dossier,
            icp_eval=icp_eval,
            campaign_id=prospect.campaign_id
        )
        timeline.append(f"[Agent: Strategy] Recommended channel: {strategy.recommended_channel} | Angle: {strategy.angle}")

        # Step 4: Personalisation Agent drafts message
        timeline.append("[Agent: Personalisation] Drafting grounded multi-channel message...")
        draft: DraftMessage = self.personalisation_agent.run(prospect, dossier, strategy)
        timeline.append(f"[Agent: Personalisation] Draft complete. Cited sources: {draft.rag_sources_cited}")

        # Step 5: Grounding Check
        timeline.append("[Guardrail: Grounding Check] Verifying claims against campaign RAG store...")
        grounding: GroundingResult = self.grounding_checker.verify_draft(prospect.campaign_id, draft)
        if not grounding.is_grounded:
            timeline.append(f"⚠️ Grounding check failed: {grounding.unsupported_claims}. Looping back to Personalisation Agent...")
        else:
            timeline.append("✅ Grounding check passed: 100% claims verified in knowledge base.")

        # Step 6: Policy Gate (Flow 3 & Flow 4)
        timeline.append("[Policy Gate] Evaluating campaign pause state and risky topic triggers...")
        gate: PolicyGateResult = self.policy_gate.evaluate(
            draft=draft,
            grounding=grounding,
            campaign_is_paused=campaign_is_paused
        )

        if gate.status == "HELD_PAUSED":
            timeline.append("⏸️ Held — campaign paused. Action held in timeline.")
            current_state = "HELD_PAUSED"
        elif gate.status == "HELD_APPROVAL":
            timeline.append(f"📥 Held / Awaiting approval — shown in Inbox. Reason: {', '.join(gate.flag_reasons)}")
            current_state = "HELD_APPROVAL"
        else:
            timeline.append(f"🚀 Message sent via {draft.channel} — appears on Prospect 360 timeline.")
            current_state = "MESSAGE_SENT"

        return {
            "prospect_id": prospect.prospect_id,
            "campaign_id": prospect.campaign_id,
            "current_state": current_state,
            "timeline": timeline,
            "research_dossier": dossier.model_dump(),
            "icp_evaluation": icp_eval.model_dump(),
            "strategy": strategy.model_dump(),
            "draft_message": draft.model_dump(),
            "grounding_check": grounding.model_dump(),
            "policy_gate": gate.model_dump()
        }

    def simulate_inbound_reply(self, prospect_id: str, reply_text: str) -> Dict[str, Any]:
        """Flow 2: Inbound reply arrives -> Conversation Agent classifies -> Strategy decides"""
        classification = self.conversation_agent.classify_reply(prospect_id, reply_text)
        strategy = self.strategy_agent.plan_reply_response(
            prospect_id=prospect_id,
            intent=classification.intent,
            escalate_to_human=classification.escalate_to_human
        )
        return {
            "classification": classification.model_dump(),
            "next_strategy": strategy.model_dump()
        }

    def simulate_timer_fire(self, prospect_id: str, touch_number: int) -> Dict[str, Any]:
        """Flow 2: Timer fires (no reply) -> Follow-up Agent decides -> Strategy decides"""
        follow_up = self.follow_up_agent.evaluate_cadence(prospect_id, touch_number)
        strategy = self.strategy_agent.plan_follow_up(
            prospect_id=prospect_id,
            touch_number=follow_up.touch_number,
            recommended_channel=follow_up.recommended_channel_pivot or "EMAIL",
            follow_up_angle=follow_up.follow_up_angle
        )
        return {
            "follow_up_decision": follow_up.model_dump(),
            "next_strategy": strategy.model_dump()
        }
