from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

APP_NAME: str = os.getenv("APP_NAME", "Autonomous SDR API")
APP_ENV: str = os.getenv("APP_ENV", "development")

# Gmail / SMTP Settings
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")

# Gmail IMAP Reply Poller (0 = disabled, 7200 = every 2 hours)
GMAIL_POLL_INTERVAL_SECONDS: int = int(os.getenv("GMAIL_POLL_INTERVAL_SECONDS", "0"))

# Resend HTTP Email API (Bypasses cloud provider SMTP firewall port blocks)
RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "Autonomous SDR <onboarding@resend.dev>")

# DronaHQ Automation Webhook Settings
DRONAHQ_WEBHOOK_URL: str = os.getenv(
    "DRONAHQ_WEBHOOK_URL",
    "https://automations.dronahq.com/webhook/6aae11050d2831ebfde39bf5"
)
DRONAHQ_API_KEY: str = os.getenv("DRONAHQ_API_KEY", "")

# Individual DronaHQ Agent Endpoints
DRONAHQ_LEAD_RESEARCH_URL: str = os.getenv("DRONAHQ_LEAD_RESEARCH_URL", "")
DRONAHQ_LEAD_RESEARCH_KEY: str = os.getenv("DRONAHQ_LEAD_RESEARCH_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

DRONAHQ_ICP_FITMENT_URL: str = os.getenv("DRONAHQ_ICP_FITMENT_URL", "")
DRONAHQ_ICP_FITMENT_KEY: str = os.getenv("DRONAHQ_ICP_FITMENT_KEY", "")

DRONAHQ_OUTREACH_STRATEGY_URL: str = os.getenv("DRONAHQ_OUTREACH_STRATEGY_URL", "")
DRONAHQ_OUTREACH_STRATEGY_KEY: str = os.getenv("DRONAHQ_OUTREACH_STRATEGY_KEY", "")

DRONAHQ_PERSONALISATION_URL: str = os.getenv("DRONAHQ_PERSONALISATION_URL", "")
DRONAHQ_PERSONALISATION_KEY: str = os.getenv("DRONAHQ_PERSONALISATION_KEY", "")

# Email Provider: "gmail" (default) or "dronahq"
EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "gmail")

# DronaHQ Email Outreach Executor Settings (Optional: leave blank to use Gmail SMTP)
DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL: str = os.getenv("DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL", "")
DRONAHQ_EMAIL_EXECUTOR_API_KEY: str = os.getenv("DRONAHQ_EMAIL_EXECUTOR_API_KEY", "")

# SMS Provider: "twilio" (default direct delivery) or "dronahq"
SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "twilio")

# DronaHQ SMS Outreach Executor Settings (Optional: leave blank to use Twilio directly)
DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL: str = os.getenv("DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL", "")
DRONAHQ_SMS_EXECUTOR_API_KEY: str = os.getenv("DRONAHQ_SMS_EXECUTOR_API_KEY", "")

# DronaHQ Conversation Agent (handles inbound prospect replies)
DRONAHQ_CONVERSATION_AGENT_URL: str = os.getenv("DRONAHQ_CONVERSATION_AGENT_URL", "")
DRONAHQ_CONVERSATION_AGENT_KEY: str = os.getenv("DRONAHQ_CONVERSATION_AGENT_KEY", "")
DRONAHQ_CONVERSATION_AGENT_ID: str = os.getenv("DRONAHQ_CONVERSATION_AGENT_ID", "")

# DronaHQ Follow-up Agent (decides next cadence action only)
DRONAHQ_FOLLOWUP_AGENT_URL: str = os.getenv("DRONAHQ_FOLLOWUP_AGENT_URL", "")
DRONAHQ_FOLLOWUP_AGENT_ID: str = os.getenv("DRONAHQ_FOLLOWUP_AGENT_ID", "")
DRONAHQ_FOLLOWUP_AGENT_KEY: str = os.getenv("DRONAHQ_FOLLOWUP_AGENT_KEY", "")
FOLLOWUP_SCHEDULER_INTERVAL_SECONDS: int = int(os.getenv("FOLLOWUP_SCHEDULER_INTERVAL_SECONDS", "0"))

# DronaHQ LinkedIn Automation Webhook Settings
DRONAHQ_LINKEDIN_WEBHOOK_URL: str = os.getenv("DRONAHQ_LINKEDIN_WEBHOOK_URL", "")
DRONAHQ_LINKEDIN_API_KEY: str = os.getenv("DRONAHQ_LINKEDIN_API_KEY", "")

# Twilio Telephony Settings (Voice & SMS)
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

# Voice SDR & Telephony Provider Settings
VOICE_PROVIDER: str = os.getenv("VOICE_PROVIDER", "twilio")
VOICE_AGENT_ENDPOINT: str = os.getenv("VOICE_AGENT_ENDPOINT", "")
VOICE_PROVIDER_API_KEY: str = os.getenv("VOICE_PROVIDER_API_KEY", "")

# DronaHQ "SDR Voice Script Agent" Settings
DRONAHQ_VOICE_AGENT_URL: str = os.getenv("DRONAHQ_VOICE_AGENT_URL", "")
DRONAHQ_VOICE_AGENT_KEY: str = os.getenv("DRONAHQ_VOICE_AGENT_KEY", "")
DRONAHQ_VOICE_AGENT_ENDPOINT: str = os.getenv(
    "DRONAHQ_VOICE_AGENT_ENDPOINT",
    "https://agents-backend.dronahq.com/voice/outbound/dispatch"
)
DRONAHQ_VOICE_AGENT_ID: str = os.getenv(
    "DRONAHQ_VOICE_AGENT_ID",
    "b7f2d792-925e-429a-8551-0cb0207c72d9"
)
DRONAHQ_SOURCE_PHONE: str = os.getenv("DRONAHQ_SOURCE_PHONE", "")

# DronaHQ Prospect Discovery Agent Webhook (Optional live discovery webhook)
DRONAHQ_DISCOVERY_AGENT_URL: str = os.getenv("DRONAHQ_DISCOVERY_AGENT_URL", "")
DRONAHQ_DISCOVERY_AGENT_KEY: str = os.getenv("DRONAHQ_DISCOVERY_AGENT_KEY", "")

# Backend Host for Telephony Callbacks
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# Supabase Database & REST API Settings
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ueostzaevpteuxdmxnww.supabase.co")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

