import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import urllib.error

from app.services.dronahq import call_email_executor, call_sms_executor
from app.services.email import send_email
from app.services.channel_dispatcher import dispatch_outreach
from app.services.sdr import execute_sdr_pipeline
from app.models.execution import ExecutionRecord


def _mock_http_response(status_code: int, data: dict):
    """Creates a mock urllib response with the given JSON payload."""
    raw_bytes = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.getcode.return_value = status_code
    resp.read.return_value = raw_bytes
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = None
    return resp


class TestEmailExecutorWebhook:
    """Tests for DronaHQ Email Outreach Executor webhook caller."""

    @patch("app.services.dronahq.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-email-executor")
    @patch("app.services.dronahq.DRONAHQ_EMAIL_EXECUTOR_API_KEY", "test-api-key-xyz")
    @patch("urllib.request.urlopen")
    def test_call_email_executor_payload_structure(self, mock_urlopen):
        """Verifies flat JSON payload schema and headers sent to DronaHQ Email Executor."""
        mock_urlopen.return_value = _mock_http_response(
            200,
            {
                "success": True,
                "channel": "EMAIL",
                "status": "SENT",
                "execution_id": "exec-123",
                "prospect_id": "prospect-456",
                "provider_message_id": "msg-dhq-789",
            },
        )

        result = call_email_executor(
            execution_id="exec-123",
            campaign_id="camp-saas",
            prospect_id="prospect-456",
            to_email="sarah.chen@cloudscale.io",
            subject="Accelerating Engineering Cadence",
            message="Hi Sarah, noticed your engineering leadership...",
        )

        # 1. Verify URL and method
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://automations.dronahq.com/webhook/test-email-executor"
        assert req.get_method() == "POST"

        # 2. Verify headers
        headers = {k.lower(): v for k, v in req.headers.items()}
        assert headers.get("content-type") == "application/json"
        assert headers.get("api-key") == "test-api-key-xyz"

        # 3. Verify flat JSON payload structure
        payload = json.loads(req.data.decode("utf-8"))
        assert payload == {
            "execution_id": "exec-123",
            "campaign_id": "camp-saas",
            "prospect_id": "prospect-456",
            "to_email": "sarah.chen@cloudscale.io",
            "subject": "Accelerating Engineering Cadence",
            "message": "Hi Sarah, noticed your engineering leadership...",
        }

        # 4. Verify parsed output
        assert result["success"] is True
        assert result["status"] == "SENT"
        assert result["channel"] == "EMAIL"
        assert result["provider"] == "DRONAHQ_EMAIL_EXECUTOR"
        assert result["provider_message_id"] == "msg-dhq-789"
        assert result["error"] is None

    @patch("app.services.dronahq.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-email-executor")
    @patch("urllib.request.urlopen")
    def test_call_email_executor_failure_handling(self, mock_urlopen):
        """Verifies graceful handling when DronaHQ Email Executor returns failure."""
        mock_urlopen.return_value = _mock_http_response(
            200,
            {
                "success": False,
                "status": "FAILED",
                "error": "Recipient mailbox does not exist",
            },
        )

        result = call_email_executor(
            execution_id="exec-fail",
            campaign_id="camp-saas",
            prospect_id="prospect-999",
            to_email="invalid@domain.org",
            subject="Test Subject",
            message="Test Message",
        )

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert result["provider"] == "DRONAHQ_EMAIL_EXECUTOR"
        assert "Recipient mailbox does not exist" in result["error"]

    def test_call_email_executor_when_unconfigured(self):
        """Returns structured error when DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL is not set."""
        with patch("app.services.dronahq.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", ""):
            result = call_email_executor(
                execution_id="exec-empty",
                campaign_id="camp-saas",
                prospect_id="prospect-000",
                to_email="test@example.com",
                subject="Test",
                message="Test",
            )
            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert "not configured" in result["error"].lower()


class TestEmailDispatcherIntegration:
    """Tests for send_email dispatch routing with executor vs fallback."""

    @pytest.mark.asyncio
    @patch("app.services.email.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-email-executor")
    @patch("app.services.email.call_email_executor")
    async def test_send_email_uses_executor_when_configured(self, mock_call_executor):
        """When DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL is set, send_email routes to call_email_executor."""
        mock_call_executor.return_value = {
            "success": True,
            "channel": "EMAIL",
            "status": "SENT",
            "provider": "DRONAHQ_EMAIL_EXECUTOR",
            "provider_message_id": "dhq-msg-555",
            "error": None,
        }

        outcome = await send_email(
            to_email="alex.rivera@fintech.io",
            subject="DevOps Acceleration",
            content="Hello Alex, saw your work scaling platforms...",
            prospect_id="p-101",
            campaign_id="c-202",
            execution_id="e-303",
        )

        assert mock_call_executor.called
        kwargs = mock_call_executor.call_args[1]
        assert kwargs["execution_id"] == "e-303"
        assert kwargs["campaign_id"] == "c-202"
        assert kwargs["prospect_id"] == "p-101"
        assert kwargs["to_email"] == "alex.rivera@fintech.io"
        assert kwargs["subject"] == "DevOps Acceleration"
        assert kwargs["message"] == "Hello Alex, saw your work scaling platforms..."

        assert outcome["status"] == "SENT"
        assert outcome["provider"] == "DRONAHQ_EMAIL_EXECUTOR"
        assert outcome["provider_message_id"] == "dhq-msg-555"

    @pytest.mark.asyncio
    @patch("app.services.email.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-email-executor")
    @patch("app.services.email.call_email_executor")
    @patch("smtplib.SMTP")
    async def test_send_email_executor_failure_does_not_send_smtp(self, mock_smtp, mock_call_executor):
        """If DronaHQ Email Executor is configured but fails, do NOT send via old SMTP."""
        mock_call_executor.return_value = {
            "success": False,
            "channel": "EMAIL",
            "status": "FAILED",
            "error": "Rate limit exceeded on executor",
        }

        outcome = await send_email(
            to_email="marcus@fintech.io",
            subject="Platform Efficiency",
            content="Hello Marcus...",
            prospect_id="p-202",
            campaign_id="c-303",
            execution_id="e-404",
        )

        assert mock_call_executor.called
        # Verify SMTP was NEVER attempted
        assert not mock_smtp.called
        assert outcome["status"] == "FAILED"
        assert outcome["provider"] == "DRONAHQ_EMAIL_EXECUTOR"
        assert "Rate limit exceeded" in outcome["error"]

    @pytest.mark.asyncio
    @patch("app.services.email.DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "")
    async def test_send_email_falls_back_when_executor_unconfigured(self):
        """When executor is not configured, fallback (simulation / SMTP) operates normally."""
        outcome = await send_email(
            to_email="dev@example.com",
            subject="Introductory Note",
            content="Checking in...",
            prospect_id="p-303",
            campaign_id="c-404",
        )
        assert outcome["status"] == "SENT"
        assert outcome["provider"] in ["DEMO_SIMULATOR", "GMAIL_SMTP", "RESEND_API", "GMAIL_SMTP (Cloud Logged)"]


class TestChannelDispatcherRouting:
    """Tests that channel dispatcher respects recommended_channel and preserves other channels."""

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.send_email")
    async def test_dispatcher_routes_email_with_execution_id(self, mock_send_email):
        mock_send_email.return_value = {"channel": "EMAIL", "status": "SENT"}

        prospect = {"id": "p-1", "email": "elena@scale.io", "phone": "+15551234567"}
        personalisation = {"content": "Email message body", "subject": "Email Subject"}

        outcome = await dispatch_outreach(
            recommended_channel="EMAIL",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-uuid-999",
        )

        assert mock_send_email.called
        assert mock_send_email.call_args[1]["execution_id"] == "exec-uuid-999"
        assert mock_send_email.call_args[1]["to_email"] == "elena@scale.io"

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.send_sms")
    @patch("app.services.channel_dispatcher.send_email")
    async def test_dispatcher_preserves_sms_channel(self, mock_send_email, mock_send_sms):
        """SMS is routed to Twilio send_sms and does NOT invoke email executor."""
        mock_send_sms.return_value = {"channel": "SMS", "status": "SENT"}

        prospect = {"id": "p-2", "email": "test@scale.io", "phone": "+15551234567"}
        personalisation = {"content": "Quick question on dev velocity?"}

        outcome = await dispatch_outreach(
            recommended_channel="SMS",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-sms-1",
        )

        assert mock_send_sms.called
        assert not mock_send_email.called
        assert outcome["channel"] == "SMS"

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.send_linkedin")
    @patch("app.services.channel_dispatcher.send_email")
    async def test_dispatcher_preserves_linkedin_channel(self, mock_send_email, mock_send_linkedin):
        """LINKEDIN is routed to send_linkedin and does NOT invoke email executor."""
        mock_send_linkedin.return_value = {"channel": "LINKEDIN", "status": "SENT"}

        prospect = {"id": "p-3", "linkedin_url": "https://linkedin.com/in/testprospect"}
        personalisation = {"content": "Would love to connect!"}

        outcome = await dispatch_outreach(
            recommended_channel="LINKEDIN",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-li-1",
        )

        assert mock_send_linkedin.called
        assert not mock_send_email.called
        assert outcome["channel"] == "LINKEDIN"


class TestIdempotency:
    """Tests that duplicate sends are prevented if outreach was already sent."""

    @pytest.mark.asyncio
    @patch("app.services.sdr.get_all_executions")
    @patch("app.services.sdr.run_dronahq_multi_agent_pipeline")
    async def test_idempotency_prevents_duplicate_send(self, mock_pipeline, mock_get_execs):
        """If an execution for (campaign, prospect) already has status SENT, short-circuit."""
        existing_rec = ExecutionRecord(
            execution_id="exec-already-sent-123",
            campaign_id="camp-fintech",
            prospect_id="prospect-elena",
            status="SENT",
            channel="EMAIL",
            recommended_channel="EMAIL",
            actual_channel="EMAIL",
        )
        mock_get_execs.return_value = [existing_rec]

        with patch("app.services.sdr.get_campaign") as mock_camp, \
             patch("app.services.sdr.get_prospect") as mock_prosp:
            mock_camp.return_value = MagicMock(id="camp-fintech", status="LIVE", name="Fintech Scale")
            mock_prosp.return_value = MagicMock(id="prospect-elena", name="Elena", email="elena@example.com")

            rec = await execute_sdr_pipeline("camp-fintech", "prospect-elena")

            # Must return the existing record and NEVER invoke the pipeline
            assert rec.execution_id == "exec-already-sent-123"
            assert rec.status == "SENT"
            assert not mock_pipeline.called


class TestSMSExecutorWebhook:
    """Tests for DronaHQ SMS Outreach Executor webhook caller."""

    @patch("app.services.dronahq.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-sms-executor")
    @patch("app.services.dronahq.DRONAHQ_SMS_EXECUTOR_API_KEY", "test-sms-key-xyz")
    @patch("urllib.request.urlopen")
    def test_call_sms_executor_payload_structure(self, mock_urlopen):
        """Test A & H: Verifies exact flat JSON payload schema and headers sent to DronaHQ SMS Executor."""
        mock_urlopen.return_value = _mock_http_response(
            200,
            {
                "success": True,
                "channel": "SMS",
                "status": "SENT",
                "execution_id": "exec-sms-123",
                "campaign_id": "camp-sms-456",
                "prospect_id": "prosp-sms-789",
                "provider_message_id": "dhq-sms-msg-1",
            },
        )

        result = call_sms_executor(
            execution_id="exec-sms-123",
            campaign_id="camp-sms-456",
            prospect_id="prosp-sms-789",
            to_phone="+15559876543",
            message="Hi John, saw your engineering work. Open for a brief chat next week?",
        )

        # 1. Verify URL and method
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://automations.dronahq.com/webhook/test-sms-executor"
        assert req.get_method() == "POST"

        # 2. Verify headers
        headers = {k.lower(): v for k, v in req.headers.items()}
        assert headers.get("content-type") == "application/json"
        assert headers.get("api-key") == "test-sms-key-xyz"

        # 3. Verify exact flat JSON payload structure
        payload = json.loads(req.data.decode("utf-8"))
        assert payload == {
            "execution_id": "exec-sms-123",
            "campaign_id": "camp-sms-456",
            "prospect_id": "prosp-sms-789",
            "to_phone": "+15559876543",
            "message": "Hi John, saw your engineering work. Open for a brief chat next week?",
        }

        # 4. Verify parsed output
        assert result["success"] is True
        assert result["status"] == "SENT"
        assert result["channel"] == "SMS"
        assert result["provider"] == "DRONAHQ_SMS_EXECUTOR"
        assert result["error"] is None

    @patch("app.services.dronahq.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-sms-executor")
    @patch("urllib.request.urlopen")
    def test_call_sms_executor_non_2xx_handling(self, mock_urlopen):
        """Test G: When DronaHQ SMS webhook returns non-2xx or error, execution is marked FAILED."""
        fp = BytesIO(b'{"success": false, "error": "Twilio rate limit exceeded"}')
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://automations.dronahq.com/webhook/test-sms-executor",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=fp,
        )

        result = call_sms_executor(
            execution_id="exec-sms-fail",
            campaign_id="camp-fail",
            prospect_id="prosp-fail",
            to_phone="+15550001111",
            message="Test message",
        )

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert result["provider"] == "DRONAHQ_SMS_EXECUTOR"
        assert "500" in result["error"]

    def test_call_sms_executor_missing_url(self):
        """Test F: When DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL is missing, returns clear configuration error."""
        with patch("app.services.dronahq.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", ""):
            result = call_sms_executor(
                execution_id="exec-empty-url",
                campaign_id="camp-1",
                prospect_id="p-1",
                to_phone="+15551234567",
                message="Hello",
            )
            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert "DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL not configured" in result["error"]

    @patch("app.services.dronahq.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-sms-executor")
    def test_call_sms_executor_missing_phone(self):
        """Test E: Missing to_phone does NOT call webhook and returns clear error."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            result = call_sms_executor(
                execution_id="exec-no-phone",
                campaign_id="camp-1",
                prospect_id="p-1",
                to_phone="",
                message="Hello",
            )
            assert result["success"] is False
            assert result["status"] == "FAILED"
            assert not mock_urlopen.called
            assert "phone number is missing" in result["error"].lower()


class TestSMSDispatcherIntegration:
    """Tests for channel dispatcher and send_sms integration with SMS executor."""

    @pytest.mark.asyncio
    @patch("app.services.sms.SMS_PROVIDER", "dronahq")
    @patch("app.services.sms.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-sms-executor")
    @patch("app.services.sms.call_sms_executor")
    async def test_send_sms_calls_executor_and_marks_sent(self, mock_call_sms):
        """Test A & H: send_sms routes to call_sms_executor and marks status SENT."""
        from app.services.sms import send_sms
        mock_call_sms.return_value = {
            "success": True,
            "channel": "SMS",
            "status": "SENT",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "provider_message_id": "dhq-sms-sid-99",
            "recipient": "+15557778888",
            "content": "Hi there, test SMS",
            "error": None,
        }

        outcome = await send_sms(
            to_phone="+15557778888",
            content="Hi there, test SMS",
            prospect_id="p-sms-1",
            campaign_id="c-sms-1",
            execution_id="e-sms-1",
        )

        assert mock_call_sms.called
        kwargs = mock_call_sms.call_args[1]
        assert kwargs["execution_id"] == "e-sms-1"
        assert kwargs["campaign_id"] == "c-sms-1"
        assert kwargs["prospect_id"] == "p-sms-1"
        assert kwargs["to_phone"] == "+15557778888"
        assert kwargs["message"] == "Hi there, test SMS"

        assert outcome["status"] == "SENT"
        assert outcome["provider"] == "DRONAHQ_SMS_EXECUTOR"

    @pytest.mark.asyncio
    @patch("app.services.sms.SMS_PROVIDER", "dronahq")
    @patch("app.services.sms.DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "https://automations.dronahq.com/webhook/test-sms-executor")
    @patch("app.services.sms.call_sms_executor")
    @patch("urllib.request.urlopen")
    async def test_send_sms_executor_failure_does_not_call_twilio(self, mock_urlopen, mock_call_sms):
        """Test G: When SMS executor fails, execution is FAILED and old Twilio is NOT called."""
        from app.services.sms import send_sms
        mock_call_sms.return_value = {
            "success": False,
            "channel": "SMS",
            "status": "FAILED",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "error": "DronaHQ Twilio connection failed",
        }

        outcome = await send_sms(
            to_phone="+15557778888",
            content="Hi there",
            prospect_id="p-sms-fail",
            campaign_id="c-sms-fail",
            execution_id="e-sms-fail",
        )

        assert outcome["status"] == "FAILED"
        assert outcome["provider"] == "DRONAHQ_SMS_EXECUTOR"
        assert not mock_urlopen.called

    @pytest.mark.asyncio
    async def test_send_sms_missing_phone_fails_early(self):
        """Test E: send_sms without phone returns FAILED and does not call any webhook."""
        from app.services.sms import send_sms
        outcome = await send_sms(
            to_phone="",
            content="Hello",
            prospect_id="p-no-phone",
            campaign_id="c-no-phone",
        )
        assert outcome["status"] == "FAILED"
        assert "phone number is missing" in outcome["error"].lower()


class TestChannelIsolation:
    """Tests B, C, D: Verify non-SMS channels do NOT invoke SMS executor."""

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.send_email")
    @patch("app.services.channel_dispatcher.send_sms")
    async def test_email_channel_does_not_call_sms_executor(self, mock_sms, mock_email):
        """Test B: recommended_channel = EMAIL routes to email and NOT SMS executor."""
        mock_email.return_value = {"channel": "EMAIL", "status": "SENT"}
        prospect = {"id": "p-1", "email": "test@domain.com", "phone": "+15551234567"}
        personalisation = {"content": "Email message", "subject": "Subject"}

        outcome = await dispatch_outreach(
            recommended_channel="EMAIL",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-email-1",
        )

        assert mock_email.called
        assert not mock_sms.called
        assert outcome["channel"] == "EMAIL"

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.initiate_voice_call")
    @patch("app.services.channel_dispatcher.send_sms")
    async def test_phone_channel_does_not_call_sms_executor(self, mock_sms, mock_voice):
        """Test C: recommended_channel = PHONE routes to voice and NOT SMS executor."""
        mock_voice.return_value = {"channel": "PHONE", "status": "INITIATING"}
        prospect = {"id": "p-2", "phone": "+15551234567"}
        personalisation = {"content": "Voice call"}

        outcome = await dispatch_outreach(
            recommended_channel="PHONE",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-voice-1",
        )

        assert mock_voice.called
        assert not mock_sms.called
        assert outcome["channel"] == "PHONE"

    @pytest.mark.asyncio
    @patch("app.services.channel_dispatcher.send_linkedin")
    @patch("app.services.channel_dispatcher.send_sms")
    async def test_linkedin_channel_does_not_call_sms_executor(self, mock_sms, mock_linkedin):
        """Test D: recommended_channel = LINKEDIN routes to linkedin and NOT SMS executor."""
        mock_linkedin.return_value = {"channel": "LINKEDIN", "status": "SENT"}
        prospect = {"id": "p-3", "linkedin_url": "https://linkedin.com/in/prospect"}
        personalisation = {"content": "Connection note"}

        outcome = await dispatch_outreach(
            recommended_channel="LINKEDIN",
            prospect=prospect,
            personalisation=personalisation,
            execution_id="exec-li-1",
        )

        assert mock_linkedin.called
        assert not mock_sms.called
        assert outcome["channel"] == "LINKEDIN"


class TestSMSIdempotency:
    """Test I: Verify duplicate send retry is prevented if SMS was already sent."""

    @pytest.mark.asyncio
    @patch("app.services.sdr.get_all_executions")
    @patch("app.services.sdr.run_dronahq_multi_agent_pipeline")
    async def test_sms_idempotency_prevents_duplicate_send(self, mock_pipeline, mock_get_execs):
        """Test I: If an SMS execution for (campaign, prospect) is already SENT, do not re-dispatch."""
        existing_rec = ExecutionRecord(
            execution_id="exec-sms-sent-already",
            campaign_id="camp-sms-idempotent",
            prospect_id="prospect-sms-bob",
            status="SENT",
            channel="SMS",
            recommended_channel="SMS",
            actual_channel="SMS",
        )
        mock_get_execs.return_value = [existing_rec]

        with patch("app.services.sdr.get_campaign") as mock_camp, \
             patch("app.services.sdr.get_prospect") as mock_prosp:
            mock_camp.return_value = MagicMock(id="camp-sms-idempotent", status="LIVE", name="SMS Campaign")
            mock_prosp.return_value = MagicMock(id="prospect-sms-bob", name="Bob", phone="+15558889999")

            rec = await execute_sdr_pipeline("camp-sms-idempotent", "prospect-sms-bob")

            assert rec.execution_id == "exec-sms-sent-already"
            assert rec.status == "SENT"
            assert not mock_pipeline.called

