"""
Agent 7: Voice SDR Agent
Input: Prospect Dossier + Campaign Strategy
Output: VoiceCallScript
"""

from schemas import VoiceCallScript, RawProspect, ResearchDossier
from prompts import VOICE_AGENT_SYSTEM_PROMPT
from rag.store import kb_store

class VoiceSDRAgent:
    def __init__(self):
        self.system_prompt = VOICE_AGENT_SYSTEM_PROMPT

    def generate_call_script(self, prospect: RawProspect, dossier: ResearchDossier) -> VoiceCallScript:
        campaign_id = prospect.campaign_id
        first_name = prospect.name.split()[0]

        if campaign_id == "us_saas_cto":
            opener = f"Hi {first_name}, Alex here from Turboscale. I know I caught you out of the blue, but I saw your team scaling Kubernetes on AWS—do you have 20 seconds?"
            questions = [
                "Are your developers feeling friction with slow GitHub Actions queue times as the team grows?",
                "How are you currently tracking idle Kubernetes pod spend across dev and staging clusters?"
            ]
            rebuttals = {
                "in_a_meeting": "Completely understand, I'll drop a 2-line email with our Veloce Health case study. What's the best email?",
                "use_datadog": "Datadog is great for dashboards, but we autonomously kill orphaned pods to cut bills by 30% in real-time.",
                "no_bandwidth": "Understood. Setup takes 10 minutes via read-only AWS IAM, zero code changes."
            }
            closing = "Would you be against a 10-minute technical run-through next Tuesday at 10 AM?"

        elif campaign_id == "india_bfsi_cio":
            opener = f"Good day Mr./Ms. {first_name}, Priya Sharma from FinShield AI. Calling regarding RBI's new automated digital lending compliance guidelines."
            questions = [
                "What is your current loan origination TAT across multi-bureau verification?",
                "Is your team prioritizing DPDP Act 2023 audit readiness for core banking integrations?"
            ]
            rebuttals = {
                "in_a_meeting": "Understood, Sir/Ma'am. May I send an executive brief to your office email?",
                "no_cloud_allowed": "FinShield is 100% on-premise or sovereign Indian private cloud. No data ever leaves your perimeter.",
                "have_finacle": "We do not replace Finacle; we sit on top via ISO 20022 APIs to automate underwriter checks."
            }
            closing = "Could we schedule a 15-minute architectural review with your technology committee next week?"

        else:
            opener = f"Hey {first_name}, Devon from WhisperFlow. Saw your conversational voice agent demo online—quick question on telephony latency."
            questions = [
                "Are you running into the 1-second audio lag over cellular phone lines?",
                "How are you handling customer barge-in and audio interruptions right now?"
            ]
            rebuttals = {
                "using_openai_realtime": "OpenAI Realtime is great, but costs 6x more ($0.30/min vs $0.05/min) and doesn't handle SIP trunks.",
                "built_in_house": "Managing WebSockets and packet jitter eats months. TalkSync cut latency to 420ms in 1 day with us."
            }
            closing = "Let's connect for 10 minutes so I can give you free API sandbox keys to test with your models."

        return VoiceCallScript(
            prospect_id=prospect.prospect_id,
            opening_hook=opener,
            qualifying_questions=questions,
            objection_rebuttals=rebuttals,
            closing_ask=closing
        )
