"""
Agent 5: Conversation Agent (Inbound Reply Classifier)
Input: Inbound message from prospect
Output: ReplyClassification
"""

from schemas import ReplyClassification
from prompts import CONVERSATION_AGENT_SYSTEM_PROMPT

class ConversationAgent:
    def __init__(self):
        self.system_prompt = CONVERSATION_AGENT_SYSTEM_PROMPT

    def classify_reply(self, prospect_id: str, inbound_text: str) -> ReplyClassification:
        text_lower = inbound_text.lower()

        escalate = False
        if any(w in text_lower for w in ["pricing", "cost", "contract", "security audit", "sla", "expensive"]):
            intent = "OBJECTION_PRICING"
            sentiment = "NEUTRAL"
            escalate = True  # Flow 4 / HITL escalation for custom pricing questions
            notes = "Prospect inquiring about pricing or commercials. Flagged for review."
            
        elif any(w in text_lower for w in ["demo", "calendar", "time next week", "tuesday", "link", "chat", "sounds good"]):
            intent = "INTERESTED_BOOK_MEETING"
            sentiment = "POSITIVE"
            escalate = False
            notes = "Prospect requested demo or expressed interest in meeting."

        elif any(w in text_lower for w in ["datadog", "circleci", "finacle", "bancs", "already have", "competitor"]):
            intent = "OBJECTION_COMPETITOR"
            sentiment = "NEUTRAL"
            escalate = False
            notes = "Prospect mentioned competitor/existing vendor. Deploy playbook rebuttal."

        elif any(w in text_lower for w in ["busy", "not now", "next quarter", "later"]):
            intent = "OBJECTION_NO_TIME"
            sentiment = "NEUTRAL"
            escalate = False
            notes = "Timing objection. Snooze cadence for 30 days."

        elif any(w in text_lower for w in ["unsubscribe", "remove me", "stop", "opt out"]):
            intent = "UNSUBSCRIBE"
            sentiment = "NEGATIVE"
            escalate = False
            notes = "Prospect requested opt-out. Add to global suppression list."

        elif any(w in text_lower for w in ["out of office", "ooo", "maternity", "vacation", "auto-reply"]):
            intent = "OUT_OF_OFFICE"
            sentiment = "NEUTRAL"
            escalate = False
            notes = "Automated OOO response detected. Pause cadence until return date."

        else:
            intent = "TECHNICAL_QUESTION"
            sentiment = "POSITIVE"
            escalate = True
            notes = "Technical inquiry. May require engineering response."

        return ReplyClassification(
            prospect_id=prospect_id,
            inbound_message=inbound_text,
            intent=intent,
            sentiment=sentiment,
            escalate_to_human=escalate,
            extracted_notes=notes
        )
