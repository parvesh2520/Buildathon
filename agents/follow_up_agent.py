"""
Agent 6: Follow-up Agent
Input: Cadence touch state + Timer trigger
Output: FollowUpDecision
"""

from schemas import FollowUpDecision
from prompts import FOLLOW_UP_AGENT_SYSTEM_PROMPT

class FollowUpAgent:
    def __init__(self):
        self.system_prompt = FOLLOW_UP_AGENT_SYSTEM_PROMPT

    def evaluate_cadence(
        self,
        prospect_id: str,
        current_touch: int,
        max_touches: int = 3,
        prior_channel: str = "EMAIL"
    ) -> FollowUpDecision:
        """
        Flow 2: Evaluates whether to bump, pivot channels, or send breakup email.
        """
        if current_touch >= max_touches:
            return FollowUpDecision(
                prospect_id=prospect_id,
                touch_number=current_touch + 1,
                max_allowed_touches=max_touches,
                should_follow_up=False,
                recommended_channel_pivot=None,
                follow_up_angle="Cadence exhausted",
                is_final_breakup=True,
                reason="Maximum touches reached without engagement. Archiving prospect."
            )

        if current_touch == 1:
            return FollowUpDecision(
                prospect_id=prospect_id,
                touch_number=2,
                max_allowed_touches=max_touches,
                should_follow_up=True,
                recommended_channel_pivot="EMAIL",
                follow_up_angle="Quick follow-up with concrete metric and low-friction question",
                is_final_breakup=False,
                reason="Touch 2: Provide short second touchpoint."
            )

        elif current_touch == 2:
            return FollowUpDecision(
                prospect_id=prospect_id,
                touch_number=3,
                max_allowed_touches=max_touches,
                should_follow_up=True,
                recommended_channel_pivot="LINKEDIN" if prior_channel == "EMAIL" else "EMAIL",
                follow_up_angle="Polite breakup message, offering asynchronous docs link",
                is_final_breakup=True,
                reason="Touch 3: Final breakup touchpoint with channel pivot."
            )

        return FollowUpDecision(
            prospect_id=prospect_id,
            touch_number=current_touch + 1,
            max_allowed_touches=max_touches,
            should_follow_up=False,
            recommended_channel_pivot=None,
            follow_up_angle="Stopped",
            is_final_breakup=True,
            reason="Cadence concluded."
        )
