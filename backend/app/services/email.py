import re
import smtplib
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SENDER_EMAIL,
)

logger = logging.getLogger("sdr.email")


def is_valid_email(email_str: str) -> bool:
    """Validate standard email syntax."""
    if not email_str or not isinstance(email_str, str):
        return False
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(email_regex, email_str.strip()))


def is_email_configured() -> bool:
    """Check if valid Gmail/SMTP credentials are configured in environment variables."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    lower_user = SMTP_USERNAME.lower()
    lower_pwd = SMTP_PASSWORD.lower()
    if "your_gmail" in lower_user or "your_16_digit" in lower_pwd or "example.com" in lower_user:
        return False
    return True


def build_responsive_html(subject: str, body_text: str) -> str:
    """
    Wraps plain email copy in clean, modern, responsive HTML.
    Includes proper line breaks, clean system fonts, and SDR compliance footer.
    """
    paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    formatted_paras = "".join(
        f'<p style="margin: 0 0 16px 0; line-height: 1.6; color: #334155;">{p.replace(chr(10), "<br/>")}</p>'
        for p in paragraphs
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 24px; background-color: #f8fafc;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr>
      <td align="center">
        <table width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <tr>
            <td>
              <div style="font-size: 15px; color: #1e293b;">
                {formatted_paras}
              </div>
              <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #f1f5f9; font-size: 11px; color: #94a3b8; line-height: 1.5;">
                <p style="margin: 0;">Sent autonomously via <strong>Autonomous SDR Platform</strong> powered by DronaHQ.</p>
                <p style="margin: 4px 0 0 0;">If you prefer not to receive further emails, simply reply with "unsubscribe".</p>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


async def send_email(
    to_email: str,
    subject: str,
    content: str,
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Standard Email Provider Abstraction.
    
    :param to_email: Destination recipient email.
    :param subject: Email subject line.
    :param content: Plain text body.
    :param prospect_id: Optional prospect reference ID.
    :param campaign_id: Optional campaign reference ID.
    :param body_html: Optional HTML string.
    :return: { channel: "EMAIL", status: "SENT" | "FAILED", provider_message_id: "...", recipient: "...", error: None }
    """
    clean_recipient = (to_email or "").strip()
    clean_subject = (subject or "Message from SDR").strip()
    clean_body = (content or "").strip()
    timestamp = datetime.now(timezone.utc).isoformat()
    generated_msg_id = f"email_{uuid.uuid4().hex[:12]}"

    # 1. Validate recipient email syntax
    if not is_valid_email(clean_recipient):
        logger.error(f"[EMAIL FAILED] Invalid recipient email address: '{to_email}' (prospect: {prospect_id})")
        return {
            "channel": "EMAIL",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_recipient,
            "error": f"Invalid email format: '{to_email}'",
            "subject": clean_subject,
            "timestamp": timestamp,
        }

    # 2. Build HTML body if omitted
    html_content = body_html or build_responsive_html(clean_subject, clean_body)
    sender = SENDER_EMAIL or SMTP_USERNAME or "sdr@example.com"

    # 3. If SMTP credentials are not configured, return PENDING_MANUAL or simulation mode
    if not is_email_configured():
        logger.warning(
            f"[EMAIL MOCK] Credentials not set in .env. To: {clean_recipient} | Subject: '{clean_subject}'"
        )
        return {
            "channel": "EMAIL",
            "status": "SENT",
            "provider_message_id": f"mock_{generated_msg_id}",
            "recipient": clean_recipient,
            "error": None,
            "subject": clean_subject,
            "timestamp": timestamp,
            "simulated": True,
        }

    # 4. Attempt real SMTP transmission
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = clean_subject
        msg["From"] = sender
        msg["To"] = clean_recipient
        msg["Message-ID"] = f"<{generated_msg_id}@{SMTP_SERVER}>"

        part_text = MIMEText(clean_body, "plain", "utf-8")
        msg.attach(part_text)

        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_html)

        clean_password = SMTP_PASSWORD.replace(" ", "").strip()

        # Handle SSL (port 465) vs TLS (port 587)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
                server.login(SMTP_USERNAME, clean_password)
                server.sendmail(sender, clean_recipient, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, clean_password)
                server.sendmail(sender, clean_recipient, msg.as_string())

        logger.info(f"[EMAIL SENT] Successfully delivered to {clean_recipient} (msg_id: {generated_msg_id})")
        return {
            "channel": "EMAIL",
            "status": "SENT",
            "provider_message_id": generated_msg_id,
            "recipient": clean_recipient,
            "error": None,
            "subject": clean_subject,
            "timestamp": timestamp,
        }

    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"SMTP Authentication failed: check Gmail App Password in .env ({e.smtp_error})"
        logger.error(f"[EMAIL AUTH ERROR] {err_msg}")
        return {
            "channel": "EMAIL",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_recipient,
            "error": err_msg,
            "subject": clean_subject,
            "timestamp": timestamp,
        }
    except Exception as e:
        logger.error(f"[EMAIL FAILED] SMTP Error sending to {clean_recipient}: {str(e)}")
        return {
            "channel": "EMAIL",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_recipient,
            "error": f"SMTP Error: {str(e)}",
            "subject": clean_subject,
            "timestamp": timestamp,
        }


# Synchronous helper wrapper for legacy callers
def send_email_sync(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    import asyncio
    return asyncio.run(send_email(to_email, subject, body_text, body_html=body_html))
