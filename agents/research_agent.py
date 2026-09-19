"""
Agent 1: Lead Research & Enrichment Agent
Input: RawProspect
Output: ResearchDossier
"""

from schemas import RawProspect, ResearchDossier
from prompts import RESEARCH_AGENT_SYSTEM_PROMPT

class ResearchAgent:
    def __init__(self):
        self.system_prompt = RESEARCH_AGENT_SYSTEM_PROMPT

    def run(self, prospect: RawProspect) -> ResearchDossier:
        """
        Synthesizes prospect metadata into a structured research dossier.
        """
        # Heuristic analysis based on title, company, notes
        notes = (prospect.raw_notes or "").lower()
        title_lower = prospect.title.lower()
        
        tech_stack = []
        if any(w in notes for w in ["k8s", "kubernetes", "aws", "docker"]):
            tech_stack.extend(["Kubernetes", "Docker", "AWS", "GitHub Actions"])
        elif any(w in notes for w in ["finacle", "bancs", "core banking"]):
            tech_stack.extend(["Infosys Finacle", "VMware", "Red Hat Linux"])
        elif any(w in notes for w in ["voice", "webrtc", "twilio", "speech"]):
            tech_stack.extend(["WebRTC", "Twilio", "Python", "Deepgram"])
        else:
            tech_stack.extend(["Cloud Infrastructure", "REST APIs"])

        pain_points = []
        if "cto" in title_lower or "engineering" in title_lower or "devops" in title_lower:
            pain_points.append("CI/CD pipeline queue latency and developer onboarding friction")
            pain_points.append("Runaway cloud compute expenditure on non-production clusters")
        elif "cio" in title_lower or "ciso" in title_lower or "banking" in notes:
            pain_points.append("Regulatory audit compliance under DPDP Act 2023")
            pain_points.append("Multi-day manual turnaround time for customer KYC verification")
        elif "founder" in title_lower or "ceo" in title_lower or "voice" in notes:
            pain_points.append("Audio latency lag (>1s) causing unnatural call interruptions")
            pain_points.append("High per-minute telephony costs when scaling outbound agents")
        else:
            pain_points.append("Manual operational workflows slowing GTM cycle")

        hooks = []
        if prospect.company_size_estimate:
            hooks.append(f"Company scaling actively ({prospect.company_size_estimate} team size)")
        if prospect.raw_notes:
            hooks.append(f"Noted signal: {prospect.raw_notes}")
        else:
            hooks.append(f"Leadership role as {prospect.title} at {prospect.company}")

        summary = (
            f"{prospect.name} serves as {prospect.title} at {prospect.company}, "
            f"operating out of {prospect.location}. Focuses on scaling operations while optimizing technical efficiency."
        )

        return ResearchDossier(
            prospect_id=prospect.prospect_id,
            prospect_summary=summary,
            detected_tech_stack=tech_stack,
            observed_pain_points=pain_points,
            personalisation_hooks=hooks,
            company_initiatives=[f"Modernizing architecture and scaling {prospect.company}'s core product line."]
        )
