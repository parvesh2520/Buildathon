from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.email import send_email, is_email_configured
from app.config import SMTP_USERNAME, SMTP_SERVER, RESEND_API_KEY

router = APIRouter(prefix="/api/email", tags=["Email"])


class TestEmailRequest(BaseModel):
    to_email: str
    subject: str = "Test Email from Autonomous SDR"
    body: str = "Hello! This is a test email sent from your Autonomous SDR platform."


@router.get("/status")
def get_email_status():
    configured = is_email_configured()
    provider = "Not Connected"
    sender = None
    if RESEND_API_KEY:
        provider = "Resend API (HTTP)"
        sender = "Autonomous SDR <onboarding@resend.dev>"
    elif configured:
        provider = "Gmail SMTP"
        sender = SMTP_USERNAME

    return {
        "configured": configured,
        "provider": provider,
        "sender_account": sender,
        "smtp_server": SMTP_SERVER,
    }


@router.post("/send-test")
async def send_test_email(req: TestEmailRequest):
    if not req.to_email:
        raise HTTPException(status_code=400, detail="Destination email is required.")
    
    res = await send_email(
        to_email=req.to_email,
        subject=req.subject,
        content=req.body,
        body_html=f"<h3>{req.subject}</h3><p>{req.body}</p><hr/><small>Sent via Autonomous SDR Platform</small>"
    )
    return res
