import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.followup import FollowUpRecord
from app.services.dronahq import call_followup_agent
from app.services.followup import (
    build_followup_agent_input,
    process_followup_payload,
    validate_decision,
)


def _mock_http_response(status_code: int, data: dict):
    raw_bytes = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.getcode.return_value = status_code
    resp.read.return_value = raw_bytes
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = None
    return resp


def _no_write_record(record: FollowUpRecord) -> FollowUpRecord:
    return record


class TestFollowUpAgentCall:
    @patch("app.services.dronahq.DRONAHQ_FOLLOWUP_AGENT_URL", "https://automations.dronahq.com/webhook/followup-test")
    @patch("app.services.dronahq.DRONAHQ_FOLLOWUP_AGENT_ID", "followup-agent-1")
    @patch("app.services.dronahq.DRONAHQ_API_KEY", "test-key")
    @patch("urllib.request.urlopen")
    def test_call_followup_agent_payload_and_response(self, mock_urlopen):
        mock_urlopen.return_value = _mock_http_response(
            200,
            {
                "response": {
                    "prospect_id": "p1",
                    "action": "FOLLOW_UP",
                    "next_channel": "EMAIL",
                    "next_touch_number": 2,
                    "wait_days": 0,
                    "angle": "CI_BUILD_TIME",
                    "reason": "No reply after first touch",
                }
            },
        )

        payload = {"prospect_id": "p1", "campaign_id": "us_saas_cto"}
        result = call_followup_agent(payload)

        req = mock_urlopen.call_args[0][0]
        sent_payload = json.loads(req.data.decode("utf-8"))
        headers = {k.lower(): v for k, v in req.headers.items()}

        assert req.full_url == "https://automations.dronahq.com/webhook/followup-test"
        assert sent_payload["agent_id"] == "followup-agent-1"
        assert sent_payload["prospect_id"] == "p1"
        assert headers["api-key"] == "test-key"
        assert result["decision"]["action"] == "FOLLOW_UP"
        assert result["decision"]["next_touch_number"] == 2


class TestFollowUpPayloadAndValidation:
    def test_build_payload_uses_context_without_redeciding(self):
        payload = build_followup_agent_input(
            campaign_id="us_saas_cto",
            prospect_id="jason_miller_cloudscale",
            current_touch=2,
            max_allowed_touches=3,
            allowed_channels=["EMAIL", "LINKEDIN"],
            prior_touches=[
                {
                    "touch_number": 1,
                    "channel": "EMAIL",
                    "days_ago": 3,
                    "angle": "CI_BUILD_TIME",
                    "proof_point": "VELOCE_42_TO_14",
                    "reply_received": False,
                }
            ],
            icp_fit_score=92,
        )

        assert payload["prospect_id"] == "jason_miller_cloudscale"
        assert payload["campaign"] == "us_saas_cto"
        assert payload["icp_fit_score"] == 92
        assert payload["touch_number"] == 2
        assert payload["max_allowed_touches"] == 3
        assert payload["allowed_channels"] == ["EMAIL", "LINKEDIN"]
        assert payload["prior_touches"][0]["angle"] == "CI_BUILD_TIME"

    def test_rejects_channel_outside_allowed_channels(self):
        error = validate_decision(
            {
                "prospect_id": "p1",
                "action": "FOLLOW_UP",
                "next_channel": "SMS",
                "next_touch_number": 3,
            },
            {
                "prospect_id": "p1",
                "touch_number": 2,
                "max_allowed_touches": 3,
                "allowed_channels": ["EMAIL", "LINKEDIN"],
            },
        )
        assert "not in allowed_channels" in error

    def test_rejects_touch_above_limit(self):
        error = validate_decision(
            {
                "prospect_id": "p1",
                "action": "FOLLOW_UP",
                "next_channel": "EMAIL",
                "next_touch_number": 4,
            },
            {
                "prospect_id": "p1",
                "touch_number": 3,
                "max_allowed_touches": 3,
                "allowed_channels": ["EMAIL"],
            },
        )
        assert "Touch limit exceeded" in error


class TestFollowUpExecution:
    @pytest.mark.asyncio
    @patch("app.services.followup.has_reply_since_last_outbound", return_value=False)
    @patch("app.services.followup.find_followup_touch", return_value=None)
    @patch("app.services.followup.create_followup", side_effect=_no_write_record)
    @patch("app.services.followup.call_followup_agent")
    async def test_dry_run_does_not_send_outreach(self, mock_agent, mock_create, _mock_duplicate, _mock_reply):
        mock_agent.return_value = {
            "decision": {
                "prospect_id": "p1",
                "action": "FOLLOW_UP",
                "next_channel": "EMAIL",
                "next_touch_number": 2,
                "wait_days": 0,
                "angle": "CI_BUILD_TIME",
                "reason": "No reply",
            },
            "raw_response": {},
        }

        with patch("app.services.sdr.execute_sdr_pipeline") as mock_sdr:
            result = await process_followup_payload(
                {
                    "campaign_id": "us_saas_cto",
                    "prospect_id": "p1",
                    "touch_number": 1,
                    "max_allowed_touches": 3,
                    "allowed_channels": ["EMAIL", "LINKEDIN"],
                    "prior_touches": [],
                },
                dry_run=True,
            )

        assert result["status"] == "SCHEDULED"
        assert result["dry_run"] is True
        assert result["payload"]["allowed_channels"] == ["EMAIL", "LINKEDIN"]
        assert not mock_sdr.called
        assert mock_create.called

    @pytest.mark.asyncio
    @patch("app.services.followup.has_reply_since_last_outbound", return_value=True)
    @patch("app.services.followup.call_followup_agent")
    async def test_reply_routes_to_conversation_agent_without_calling_followup_agent(self, mock_agent, _mock_reply):
        result = await process_followup_payload(
            {
                "campaign_id": "us_saas_cto",
                "prospect_id": "p1",
                "touch_number": 1,
                "max_allowed_touches": 3,
            },
            dry_run=True,
        )

        assert result["status"] == "ROUTED_TO_CONVERSATION_AGENT"
        assert not mock_agent.called

    @pytest.mark.asyncio
    @patch("app.services.followup.has_reply_since_last_outbound", return_value=False)
    @patch("app.services.followup.find_followup_touch")
    @patch("app.services.followup.call_followup_agent")
    async def test_duplicate_touch_is_not_sent(self, mock_agent, mock_duplicate, _mock_reply):
        mock_agent.return_value = {
            "decision": {
                "prospect_id": "p1",
                "action": "FOLLOW_UP",
                "next_channel": "EMAIL",
                "next_touch_number": 2,
            }
        }
        mock_duplicate.return_value = FollowUpRecord(
            campaign_id="us_saas_cto",
            prospect_id="p1",
            touch_number=2,
            channel="EMAIL",
            action="FOLLOW_UP",
            status="SENT",
        )

        with patch("app.services.sdr.execute_sdr_pipeline") as mock_sdr:
            result = await process_followup_payload(
                {
                    "campaign_id": "us_saas_cto",
                    "prospect_id": "p1",
                    "touch_number": 1,
                    "max_allowed_touches": 3,
                    "allowed_channels": ["EMAIL"],
                }
            )

        assert result["status"] == "SKIPPED_DUPLICATE"
        assert not mock_sdr.called
