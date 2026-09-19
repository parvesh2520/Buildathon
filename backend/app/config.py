from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME: str = os.getenv("APP_NAME", "Autonomous SDR API")
APP_ENV: str = os.getenv("APP_ENV", "development")

# Gmail / SMTP Settings
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")

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

DRONAHQ_ICP_FITMENT_URL: str = os.getenv("DRONAHQ_ICP_FITMENT_URL", "")
DRONAHQ_ICP_FITMENT_KEY: str = os.getenv("DRONAHQ_ICP_FITMENT_KEY", "")

DRONAHQ_OUTREACH_STRATEGY_URL: str = os.getenv("DRONAHQ_OUTREACH_STRATEGY_URL", "")
DRONAHQ_OUTREACH_STRATEGY_KEY: str = os.getenv("DRONAHQ_OUTREACH_STRATEGY_KEY", "")

DRONAHQ_PERSONALISATION_URL: str = os.getenv("DRONAHQ_PERSONALISATION_URL", "")
DRONAHQ_PERSONALISATION_KEY: str = os.getenv("DRONAHQ_PERSONALISATION_KEY", "")

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

# Backend Host for Telephony Callbacks
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# Supabase Database & REST API Settings
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ueostzaevpteuxdmxnww.supabase.co")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")


