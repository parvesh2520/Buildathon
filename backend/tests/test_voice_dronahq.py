import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.voice import initiate_voice_call, _is_usable_phone, _extract_call_id
from app.services.channel_dispatcher import dispatch_outreach
from app.models.prospect import Prospect


def _mock_http_response(status_code: int, data: dict):
    """Creates a mock urllib response with the given JSON payload."""
    raw_bytes = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.getcode.return_value = status_code
    resp.read.return_value = raw_bytes
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = None
    return resp


class TestDronaHQVoiceDispatch:
    """Tests for DronaHQ Outbound Voice Agent integration."""

    @pytest.mark.asyncio
    @patch("app.services.voice.DRONAHQ_VOICE_AGENT_ENDPOINT", "https://agents-backend.dronahq.com/voice/outbound/dispatch")
    @patch("app.services.voice.DRONAHQ_API_KEY", "test-voice-api-key")
    @patch("app.services.voice.DRONAHQ_SOURCE_PHONE", "+17372508034")
    @patch("app.services.voice.DRONAHQ_VOICE_AGENT_ID", "b7f2d792-925e-429a-8551-0cb0207c72d9")
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_success_payload(self, mock_urlopen):
        """Verifies payload structure, headers, and INITIATED status on success."""
        mock_urlopen.return_value = _mock_http_response(
            200,
            {
                "success": True,
                "status": "INITIATED",
                "call_id": "dronahq_call_abc123",
                "message": "Outbound call dispatched successfully",
            },
        )

        result = await initiate_voice_call(
            prospect_phone="+14155550123",
            prospect_id="jason_miller_cloudscale",
            campaign_id="us_saas_cto",
            execution_id="exec-voice-001",
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args_list[0][0][0]

        # Verify endpoint and method
        assert req.full_url == "https://agents-backend.dronahq.com/voice/outbound/dispatch"
        assert req.get_method() == "POST"

        # Verify headers
        headers = {k.lower(): v for k, v in req.headers.items()}
        assert headers.get("content-type") == "application/json"
        assert headers.get("api-key") == "test-voice-api-key"

        # Verify exact payload structure required by DronaHQ Voice API
        payload = json.loads(req.data.decode("utf-8"))
        assert payload == {
            "destination_phonenumber": ["+14155550123"],
            "source_phone_number": "+17372508034",
            "agent_id": "b7f2d792-925e-429a-8551-0cb0207c72d9",
            "agent_overrides": {},
        }

        # Verify output
        assert result["success"] is True
        assert result["channel"] == "PHONE"
        assert result["status"] == "INITIATED"
        assert result["prospect_id"] == "jason_miller_cloudscale"
        assert result["recipient"] == "+14155550123"
        assert result["external_call_id"] == "dronahq_call_abc123"
        assert result["provider_call_id"] == "dronahq_call_abc123"

    @pytest.mark.asyncio
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_missing_phone(self, mock_urlopen):
        """Missing phone must fail early with status=FAILED and not call DronaHQ."""
        result = await initiate_voice_call(
            prospect_phone="",
            prospect_id="prospect_no_phone",
        )

        assert not mock_urlopen.called
        assert result["success"] is False
        assert result["channel"] == "PHONE"
        assert result["status"] == "FAILED"
        assert "missing" in result["reason"].lower()

    @pytest.mark.asyncio
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_unusable_phone(self, mock_urlopen):
        """Unusable phone number (e.g. letters or too short) must fail early."""
        result = await initiate_voice_call(
            prospect_phone="invalid-phone-abc",
            prospect_id="prospect_bad_phone",
        )

        assert not mock_urlopen.called
        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert "unusable" in result["reason"].lower() or "invalid" in result["reason"].lower()

    @pytest.mark.asyncio
    @patch("os.getenv", return_value="")
    @patch("app.services.voice.DRONAHQ_API_KEY", "")
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_missing_api_key(self, mock_urlopen, mock_env):
        """Missing API key returns status=FAILED and helpful reason without exposing secrets."""
        result = await initiate_voice_call(
            prospect_phone="+14155550123",
            prospect_id="prospect_test",
        )

        assert not mock_urlopen.called
        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert "dronahq_api_key" in result["reason"].lower()

    @pytest.mark.asyncio
    @patch("app.services.voice.DRONAHQ_API_KEY", "valid-key")
    @patch("app.services.voice.DRONAHQ_SOURCE_PHONE", "")
    @patch("app.services.voice.TWILIO_PHONE_NUMBER", "")
    @patch("os.getenv")
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_missing_source_phone(self, mock_urlopen, mock_env):
        """Missing source phone returns status=FAILED."""
        mock_env.side_effect = lambda k, default="": "" if "SOURCE" in k or "PHONE" in k else "valid-key"
        result = await initiate_voice_call(
            prospect_phone="+14155550123",
            prospect_id="prospect_test",
        )

        assert not mock_urlopen.called
        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert "source phone" in result["reason"].lower()

    @pytest.mark.asyncio
    @patch("app.services.voice.DRONAHQ_API_KEY", "valid-key")
    @patch("app.services.voice.DRONAHQ_SOURCE_PHONE", "+17372508034")
    @patch("app.services.voice.DRONAHQ_VOICE_AGENT_ID", "b7f2d792-925e-429a-8551-0cb0207c72d9")
    @patch("urllib.request.urlopen")
    async def test_initiate_voice_call_http_error_handling(self, mock_urlopen):
        """HTTP error from DronaHQ returns FAILED status and redacts secrets."""
        import urllib.error
        from io import BytesIO

        err_fp = BytesIO(b'{"error": "Agent quota exceeded", "status": "FAILED"}')
        http_err = urllib.error.HTTPError(
            url="https://agents-backend.dronahq.com/voice/outbound/dispatch",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=err_fp,
        )
        mock_urlopen.side_effect = http_err

        result = await initiate_voice_call(
            prospect_phone="+14155550123",
            prospect_id="jason_miller",
        )

        assert result["success"] is False
        assert result["channel"] == "PHONE"
        assert result["status"] == "FAILED"
        assert "429" in result["reason"] or "quota" in result["reason"].lower()
        # Ensure secret is NEVER exposed in the reason
        assert "valid-key" not in result["reason"]

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.initiate_voice_call")
    @patch("app.services.channel_dispatcher.send_email")
    @patch("app.services.channel_dispatcher.send_sms")
    async def test_channel_dispatcher_phone_routes_to_voice(self, mock_sms, mock_email, mock_voice):
        """Channel dispatcher receives PHONE and routes to initiate_voice_call with prospect.phone."""
        mock_voice.return_value = {
            "success": True,
            "channel": "PHONE",
            "status": "INITIATED",
            "prospect_id": "jason_miller_cloudscale",
            "recipient": "+14155550123",
        }

        prospect = {
            "id": "jason_miller_cloudscale",
            "name": "Jason Miller",
            "phone": "+14155550123",
        }

        outcome = await dispatch_outreach(
            recommended_channel="PHONE",
            prospect=prospect,
            personalisation={"content": "Intro briefing"},
            execution_id="exec-phone-001",
        )

        assert mock_voice.called
        assert not mock_email.called
        assert not mock_sms.called

        # Verify phone number passed to voice service is from prospect.phone
        call_kwargs = mock_voice.call_args[1]
        assert call_kwargs["prospect_phone"] == "+14155550123"
        assert outcome["channel"] == "PHONE"
        assert outcome["status"] == "INITIATED"


class TestVoiceApiEndpoint:
    """Tests for POST /api/voice/test."""

    @patch("app.routes.voice.initiate_voice_call")
    def test_post_voice_test_endpoint_success(self, mock_voice):
        """Test development endpoint POST /api/voice/test returns safe structured response."""
        mock_voice.return_value = {
            "success": True,
            "channel": "PHONE",
            "status": "INITIATED",
            "prospect_id": "test_prospect",
            "recipient": "+14155550123",
            "external_call_id": "call_test_999",
            "provider_call_id": "call_test_999",
            "dronahq_response": {"status": "INITIATED", "call_id": "call_test_999"},
        }

        client = TestClient(app)
        response = client.post(
            "/api/voice/test",
            json={"prospect_id": "test_prospect", "phone": "+14155550123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["channel"] == "PHONE"
        assert data["status"] == "INITIATED"
        assert data["prospect_id"] == "test_prospect"
        assert data["provider_call_id"] == "call_test_999"

    @patch("app.routes.voice.initiate_voice_call")
    def test_post_voice_test_endpoint_missing_phone(self, mock_voice):
        """Test endpoint returns FAILED when phone is completely missing and prospect not found."""
        client = TestClient(app)
        response = client.post(
            "/api/voice/test",
            json={"prospect_id": "nonexistent_prospect_xyz", "phone": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "FAILED"
        assert "missing phone" in data["reason"].lower()
