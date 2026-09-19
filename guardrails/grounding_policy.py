"""
Grounding Check & Policy Gate Components (Iteration 2)
Directly implements User Flows 2, 3, and 4.
Features:
- Regex metric extraction ($138k, 42m, 84%, etc.) against RAG store
- PolicyGate telemetry (hold rate, pricing flag rate)
- Dict or DraftMessage duck typing
"""

import re
from typing import List, Optional, Union, Dict, Any
from schemas import DraftMessage, GroundingResult, PolicyGateResult
from rag.store import kb_store
from guardrails.numeric_grounding_checker import verify_numeric_claims


class GroundingChecker:
    """
    Flow 2 Grounding Check:
    Verifies that claims made in the draft are strictly backed by the campaign RAG store.
    """
    def __init__(self):
        self.total_checks = 0
        self.total_failed = 0

    def verify_draft(self, campaign_id: str, draft: Union[DraftMessage, Dict[str, Any]]) -> GroundingResult:
        self.total_checks += 1
        raw_kb = str(kb_store.get_campaign_context(campaign_id))
        kb_text = raw_kb.lower()
        kb_text_no_commas = kb_text.replace(",", "")  # Normalized for numeric comparison
        unsupported = []

        if isinstance(draft, dict):
            prospect_id = draft.get("prospect_id", "unknown")
            claims = draft.get("claims_made", [])
            content = draft.get("content", "")
        else:
            prospect_id = draft.prospect_id
            claims = draft.claims_made
            content = draft.content

        # 1. Deterministic Numeric Claim Pattern Verification (Currencies, percentages, durations)
        num_res = verify_numeric_claims(content, raw_kb)
        if not num_res.ok:
            for ungrounded_num in num_res.ungrounded_numbers:
                unsupported.append(f"Numeric claim '{ungrounded_num}' in draft not found in campaign knowledge base.")

        # 2. Verify extracted claims_made
        for claim in claims:
            # Extract numbers/metrics: e.g. 42, 14, 138, 84, 450, 72, 4
            numbers = re.findall(r'\b\d+[\d,\.]*\b', claim)
            for num in numbers:
                clean_num = num.replace(",", "")
                if clean_num not in kb_text_no_commas:
                    msg = f"Metric '{num}' in claim '{claim}' not found in campaign knowledge base."
                    if msg not in unsupported:
                        unsupported.append(msg)

        # 3. Extract standalone numbers directly from message body
        body_numbers = re.findall(r'\b\d+[\d,\.]*\b', content)
        # Allow common small conversational numbers and prospect-derived data
        ALLOWED_SMALL = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                         "15", "20", "25", "30", "45", "60", "90", "100"}
        for num in body_numbers:
            clean_num = num.replace(",", "")
            if clean_num not in ALLOWED_SMALL:
                if clean_num not in kb_text_no_commas:
                    msg = f"Unverified number '{num}' in drafted content not found in campaign knowledge base."
                    if msg not in unsupported:
                        unsupported.append(msg)

        if unsupported:
            self.total_failed += 1
            return GroundingResult(
                prospect_id=prospect_id,
                is_grounded=False,
                unsupported_claims=unsupported,
                revision_feedback=f"Remove or correct ungrounded claims: {'; '.join(unsupported)}"
            )

        return GroundingResult(
            prospect_id=prospect_id,
            is_grounded=True,
            unsupported_claims=[]
        )


class PolicyGate:
    """
    Flow 2, Flow 3, and Flow 4 Policy Gate:
    Enforces campaign pause state and human-in-the-loop triggers (pricing/risk).
    """
    def __init__(self):
        self.total_evaluations = 0
        self.total_held_approval = 0
        self.total_held_paused = 0
        self.total_allowed = 0

    def evaluate(
        self,
        draft: Union[DraftMessage, Dict[str, Any]],
        grounding: Optional[GroundingResult] = None,
        campaign_is_paused: bool = False,
        campaign_id: str = "us_saas_cto"
    ) -> PolicyGateResult:
        self.total_evaluations += 1
        flags = []

        if isinstance(draft, dict):
            prospect_id = draft.get("prospect_id", "unknown")
            mentions_pricing = draft.get("mentions_pricing", False)
            content = draft.get("content", "")
        else:
            prospect_id = draft.prospect_id
            mentions_pricing = draft.mentions_pricing
            content = draft.content

        # Flow 3: Campaign Pause Gate Check
        if campaign_is_paused:
            self.total_held_paused += 1
            return PolicyGateResult(
                prospect_id=prospect_id,
                allowed_to_send=False,
                status="HELD_PAUSED",
                needs_approval=False,
                flag_reasons=["Campaign is paused — action held in timeline"]
            )

        # Flow 2: Grounding Failure Gate Check
        if grounding and not grounding.is_grounded:
            self.total_held_approval += 1
            return PolicyGateResult(
                prospect_id=prospect_id,
                allowed_to_send=False,
                status="HELD_APPROVAL",
                needs_approval=True,
                flag_reasons=[f"Ungrounded claim: {c}" for c in grounding.unsupported_claims]
            )

        # Flow 4: Human-in-the-Loop Risky Topic Check (Pricing / Contract)
        content_lower = content.lower()
        if mentions_pricing or any(w in content_lower for w in [
            "pricing", "discount", "dollar", "cost per", "license fee", "enterprise tier",
            "per month", "per year", "annual fee", "free trial", "free tier",
            "roi guarantee", "payback", "per minute", "per seat",
            "usd", "inr", "₹", "rs."
        ]) or "$" in content:
            flags.append("Mentions pricing / commercial terms — needs approval")

        if flags:
            self.total_held_approval += 1
            return PolicyGateResult(
                prospect_id=prospect_id,
                allowed_to_send=False,
                status="HELD_APPROVAL",
                needs_approval=True,
                flag_reasons=flags
            )

        # Clean - Approved to send automatically
        self.total_allowed += 1
        return PolicyGateResult(
            prospect_id=prospect_id,
            allowed_to_send=True,
            status="ALLOWED",
            needs_approval=False,
            flag_reasons=[]
        )

    def get_policy_telemetry(self) -> dict:
        total = self.total_evaluations or 1
        return {
            "total_evaluations": self.total_evaluations,
            "total_allowed": self.total_allowed,
            "total_held_approval": self.total_held_approval,
            "total_held_paused": self.total_held_paused,
            "held_rate_percent": round((self.total_held_approval / total) * 100, 1),
            "approval_pass_rate_percent": round((self.total_allowed / total) * 100, 1),
        }
