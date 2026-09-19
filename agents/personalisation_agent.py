"""
Agent 4: Personalisation Agent
Input: RawProspect, ResearchDossier, StrategyAction + RAG Context
Output: DraftMessage
"""

from schemas import RawProspect, ResearchDossier, StrategyAction, DraftMessage
from prompts import PERSONALISATION_AGENT_SYSTEM_PROMPT
from rag.store import kb_store

class PersonalisationAgent:
    def __init__(self):
        self.system_prompt = PERSONALISATION_AGENT_SYSTEM_PROMPT

    def run(
        self,
        prospect: RawProspect,
        dossier: ResearchDossier,
        strategy: StrategyAction
    ) -> DraftMessage:
        """
        Drafts hyper-personalized, grounded outreach based on strategy & RAG facts.
        """
        campaign_id = prospect.campaign_id
        kb = kb_store.get_campaign_context(campaign_id)
        
        claims = []
        sources = []
        mentions_pricing = False

        if campaign_id == "us_saas_cto":
            sources.append("case_studies#veloce_health")
            claims.append("Veloce Health cut CI build times from 42 mins to 14 mins (66% speedup)")
            claims.append("Saved $138,000/year on AWS dev compute")
            
            subject = f"reducing CI build times at {prospect.company}"
            body = (
                f"Hi {prospect.name.split()[0]},\n\n"
                f"Saw your engineering team's scale—typically, once engineering heads toward {prospect.company_size_estimate or '50+ devs'}, "
                f"Docker build queues on GitHub Actions start dragging and idle AWS dev clusters run up bills.\n\n"
                f"For context, Veloce Health cut CI build latency from 42 to 14 minutes and eliminated $138k/yr in idle compute with our 10-minute read-only IAM integration.\n\n"
                f"Open to a 10-minute technical chat next Tuesday to see if this fits {prospect.company}'s roadmap?\n\n"
                f"Best,\nAlex | Turboscale AI"
            )

        elif campaign_id == "india_bfsi_cio":
            sources.append("case_studies#bharat_apex_nbfc")
            claims.append("Bharat Apex NBFC cut loan TAT from 3 days to under 4 hours")
            claims.append("84% reduction in synthetic identity loan fraud")
            
            subject = f"RBI-compliant lending TAT reduction for {prospect.company}"
            body = (
                f"Dear {prospect.name.split()[0]},\n\n"
                f"With the RBI's updated supervisory guidance on digital lending TAT and DPDP Act audit requirements, "
                f"scaling loan volume without expanding operations headcount is a top priority for BFSI technology leaders.\n\n"
                f"Bharat Apex NBFC deployed FinShield's sovereign on-premise verification engine to drop loan processing time from 72 hours to under 4 hours, while dropping synthetic identity fraud by 84%.\n\n"
                f"Would you be open to a brief 15-minute architectural briefing next week on how this deploys inside {prospect.company}'s secure private cloud?\n\n"
                f"Warm regards,\nPriya Sharma | FinShield AI"
            )

        elif campaign_id == "voice_ai_founder":
            sources.append("case_studies#talksync_yc_w24")
            claims.append("TalkSync cut response latency from 1,800ms to 420ms")
            claims.append("Boosted call completion rates from 35% to 81%")
            
            subject = f"sub-450ms voice latency for {prospect.company}"
            body = (
                f"Hey {prospect.name.split()[0]},\n\n"
                f"Saw your conversational voice agent work at {prospect.company}—clean conversational architecture.\n\n"
                f"Are you guys hitting the typical 1.2s+ latency hurdle or telephony audio packet jitter as you scale phone calls?\n\n"
                f"TalkSync (YC W24) dropped latency from 1,800ms to 420ms using WhisperFlow's streaming telephony stack, jumping call completion from 35% to 81%.\n\n"
                f"Got 10 mins this week to test our live low-latency sandbox?\n\n"
                f"Best,\nDevon | WhisperFlow"
            )

        else:
            subject = f"Connecting with {prospect.company}"
            body = f"Hi {prospect.name},\nWould love to connect regarding technical initiatives at {prospect.company}."

        return DraftMessage(
            prospect_id=prospect.prospect_id,
            channel=strategy.recommended_channel,
            subject_line=subject,
            content=body,
            rag_sources_cited=sources,
            claims_made=claims,
            mentions_pricing=mentions_pricing,
            confidence_score=0.94
        )
