"""
Agent 2: ICP Fitment Agent
Input: RawProspect, ResearchDossier
Output: ICPEvaluation (status: FIT, REVIEW, NO_FIT)
"""

from schemas import RawProspect, ResearchDossier, ICPEvaluation
from prompts import ICP_AGENT_SYSTEM_PROMPT
from rag.store import kb_store

class ICPFitmentAgent:
    def __init__(self):
        self.system_prompt = ICP_AGENT_SYSTEM_PROMPT

    def run(self, prospect: RawProspect, dossier: ResearchDossier) -> ICPEvaluation:
        """
        Evaluates prospect against campaign-specific ICP rules.
        """
        campaign_id = prospect.campaign_id
        kb_context = kb_store.get_campaign_context(campaign_id)
        icp_rules = kb_context.get("icp_criteria", "")

        matched = []
        unmatched = []
        score = 50  # baseline

        title_l = prospect.title.lower()
        company_l = prospect.company.lower()
        notes_l = (prospect.raw_notes or "").lower()

        # Check campaign specific rules
        if campaign_id == "us_saas_cto":
            # Target: CTO, VP Eng at 50-500 person US B2B SaaS
            if any(t in title_l for t in ["cto", "vp of engineering", "vp engineering", "head of infrastructure"]):
                matched.append("Executive engineering title (CTO / VP Engineering)")
                score += 25
            else:
                unmatched.append("Title does not match core engineering leadership ICP")

            if any(tech in dossier.detected_tech_stack for tech in ["Kubernetes", "Docker", "AWS"]):
                matched.append("Target cloud-native tech stack (AWS/Kubernetes)")
                score += 15

            if "agency" in company_l or "consulting" in company_l or "recruiting" in company_l:
                unmatched.append("Negative ICP: Disqualified due to agency/consulting model")
                score -= 40
            else:
                matched.append("B2B SaaS product company model")
                score += 10

        elif campaign_id == "india_bfsi_cio":
            # Target: CIO, CTO, CISO in Indian BFSI
            if any(t in title_l for t in ["cio", "cto", "ciso", "digital banking"]):
                matched.append("BFSI technology leadership title (CIO/CTO/CISO)")
                score += 25
            else:
                unmatched.append("Title does not match BFSI executive ICP")

            if any(loc in prospect.location.lower() for loc in ["india", "mumbai", "delhi", "bengaluru", "chennai", "pune"]):
                matched.append("Geography matches India jurisdiction requirements")
                score += 20
            else:
                unmatched.append("Geography outside Indian regulatory territory")
                score -= 30

            if any(w in notes_l for w in ["bank", "nbfc", "fintech", "lending"]):
                matched.append("Regulated BFSI or financial services sector")
                score += 15

        elif campaign_id == "voice_ai_founder":
            # Target: Founder, CEO, AI Lead
            if any(t in title_l for t in ["founder", "ceo", "co-founder", "head of ai", "ml"]):
                matched.append("Founder or technical AI leadership title")
                score += 25
            else:
                unmatched.append("Non-founder / non-AI lead persona")

            if any(w in notes_l for w in ["voice", "agent", "speech", "telephony", "webrtc"]):
                matched.append("Core product initiative is conversational/voice AI")
                score += 25
            else:
                unmatched.append("No active conversational voice signal detected")

        # Normalize score
        score = max(0, min(100, score))

        # Flow 2 Thresholds:
        # FIT (>=75), REVIEW (60-74), NO_FIT (<60)
        if score >= 75:
            status = "FIT"
            reasoning = f"Strong qualification match with {score}% fit score. Matches core target titles and firmographics."
        elif score >= 60:
            status = "REVIEW"
            reasoning = f"Borderline qualification ({score}%). Meets several criteria but requires cautious strategy or manual confirmation."
        else:
            status = "NO_FIT"
            reasoning = f"Disqualified with {score}% fit score. Fails primary target criteria or triggered negative ICP exclusions."

        return ICPEvaluation(
            prospect_id=prospect.prospect_id,
            fit_score=score,
            status=status,
            matched_criteria=matched,
            unmatched_criteria=unmatched,
            reasoning=reasoning
        )
