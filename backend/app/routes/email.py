from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.email import send_email, is_email_configured
from app.config import SMTP_USERNAME, SMTP_SERVER

router = APIRouter(prefix="/api/email", tags=["Email"])


class TestEmailRequest(BaseModel):
    to_email: str
    subject: str = "Test Email from Autonomous SDR"
    body: str = "Hello! This is a test email sent from your Autonomous SDR platform."


@router.get("/status")
def get_email_status():
    configured = is_email_configured()
    return {
        "configured": configured,
        "provider": "Gmail SMTP" if configured else "Not Connected",
        "sender_account": SMTP_USERNAME if configured else None,
        "smtp_server": SMTP_SERVER,
    }


@router.post("/send-test")
def send_test_email(req: TestEmailRequest):
    if not req.to_email:
        raise HTTPException(status_code=400, detail="Destination email is required.")
    
    res = send_email(
        to_email=req.to_email,
        subject=req.subject,
        body_text=req.body,
        body_html=f"<h3>{req.subject}</h3><p>{req.body}</p><hr/><small>Sent via Autonomous SDR Platform</small>"
    )
    return res
