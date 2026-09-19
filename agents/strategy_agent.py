"""
Agent 3: Outreach Strategy Agent
Input: Prospect Dossier + Trigger Event (ICP Fitment / Reply / Timer / Manager Feedback)
Output: StrategyAction
"""

from typing import Optional
from schemas import StrategyAction, ResearchDossier, ICPEvaluation
from prompts import STRATEGY_AGENT_SYSTEM_PROMPT

class OutreachStrategyAgent:
    def __init__(self):
        self.system_prompt = STRATEGY_AGENT_SYSTEM_PROMPT

    def plan_initial_outreach(
        self, 
        dossier: ResearchDossier, 
        icp_eval: ICPEvaluation,
        campaign_id: str
    ) -> StrategyAction:
        """
        Plans first touchpoint when prospect is qualified (FIT or REVIEW).
        """
        # Determine channel and angle by campaign persona
        if campaign_id == "us_saas_cto":
            channel = "EMAIL"
            tone = "PEER_ENGINEER"
            angle = "Highlight Veloce Health DevOps CI/CD speedup and AWS compute waste elimination"
            instructions = "Be direct. Lead with the 42 min to 14 min build time reduction. Request a 10-minute technical evaluation."
        
        elif campaign_id == "india_bfsi_cio":
            channel = "EMAIL"
            tone = "EXECUTIVE"
            angle = "Emphasize RBI regulatory compliance, on-premise sovereign deployment, and Bharat Apex NBFC 4-hour TAT"
            instructions = "Formal tone. Emphasize data sovereignty and DPDP Act 2023 compliance. Offer an enterprise architectural briefing."

        elif campaign_id == "voice_ai_founder":
            channel = "LINKEDIN"  # Founders convert higher on LinkedIn / Twitter
            tone = "CASUAL"
            angle = "Focus on sub-450ms voice latency and TalkSync YC case study"
            instructions = "Short, developer-first note. Focus on solving awkward 1-second audio pauses and telephone interruption handling."

        else:
            channel = "EMAIL"
            tone = "CONCISE"
            angle = "General product introduction"
            instructions = "Keep under 75 words."

        return StrategyAction(
            prospect_id=dossier.prospect_id,
            trigger_source="ICP_QUALIFIED",
            recommended_channel=channel,
            action_type="NEW_OUTREACH",
            angle=angle,
            tone=tone,
            instructions_for_copywriter=instructions,
            suggested_wait_days=0
        )

    def plan_follow_up(
        self,
        prospect_id: str,
        touch_number: int,
        recommended_channel: str,
        follow_up_angle: str
    ) -> StrategyAction:
        """
        Plans next touch when timer fires (from Follow-up Agent).
        """
        return StrategyAction(
            prospect_id=prospect_id,
            trigger_source="TIMER_FIRED",
            recommended_channel=recommended_channel,
            action_type="FOLLOW_UP",
            angle=follow_up_angle,
            tone="CONCISE",
            instructions_for_copywriter=f"Touch #{touch_number}. Gently bump with a fresh proof point. Avoid passive-aggressive 'just checking in'.",
            suggested_wait_days=3
        )

    def plan_reply_response(
        self,
        prospect_id: str,
        intent: str,
        escalate_to_human: bool
    ) -> StrategyAction:
        """
        Plans next move after Conversation Agent classifies prospect reply.
        """
        if escalate_to_human:
            return StrategyAction(
                prospect_id=prospect_id,
                trigger_source="REPLY_RECEIVED",
                recommended_channel="EMAIL",
                action_type="ESCALATE_HUMAN",
                angle="Human Rep Handover",
                tone="EXECUTIVE",
                instructions_for_copywriter="Notify assigned account executive with conversation context.",
                suggested_wait_days=0
            )

        return StrategyAction(
            prospect_id=prospect_id,
            trigger_source="REPLY_RECEIVED",
            recommended_channel="EMAIL",
            action_type="REPLY",
            angle=f"Address intent: {intent}",
            tone="CONCISE",
            instructions_for_copywriter="Directly answer prospect objection using campaign playbook before proposing meeting.",
            suggested_wait_days=0
        )
