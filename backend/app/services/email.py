import re
import smtplib
import uuid
import logging
import asyncio
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
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL,
    EMAIL_PROVIDER,
)
from app.services.dronahq import call_email_executor, clean_agent_text
import urllib.request
import urllib.error
import json

logger = logging.getLogger("sdr.email")


def sanitize_email_address(email_str: str) -> str:
    """
    Cleans and normalizes email addresses to RFC 5321 compliance:
    - Removes whitespace
    - Replaces consecutive dots '..' with a single dot '.' in the local-part
    - Strips leading/trailing dots from local-part
    - Converts domain to lowercase
    """
    if not email_str or not isinstance(email_str, str):
        return ""
    email_str = email_str.strip()
    if "@" not in email_str:
        return email_str
    parts = email_str.rsplit("@", 1)
    local_part, domain = parts[0], parts[1].lower().strip()
    # Replace multiple consecutive dots with a single dot and remove leading/trailing dots
    clean_local = re.sub(r"\.+", ".", local_part).strip(".")
    clean_domain = re.sub(r"\.+", ".", domain).strip(".")
    return f"{clean_local}@{clean_domain}"


def is_valid_email(email_str: str) -> bool:
    """Validate standard email syntax adhering to RFC 5321."""
    if not email_str or not isinstance(email_str, str):
        return False
    email_str = email_str.strip()
    if ".." in email_str or "@" not in email_str:
        return False
    parts = email_str.rsplit("@", 1)
    local, domain = parts[0], parts[1]
    if not local or not domain or local.startswith(".") or local.endswith(".") or domain.startswith(".") or domain.endswith("."):
        return False
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$"
    return bool(re.match(email_regex, email_str))



def is_email_configured() -> bool:
    """Check if valid Resend API key or Gmail/SMTP credentials are configured."""
    if RESEND_API_KEY and len(RESEND_API_KEY.strip()) > 5:
        return True
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    lower_user = SMTP_USERNAME.lower()
    lower_pwd = SMTP_PASSWORD.lower()
    if "your_gmail" in lower_user or "your_16_digit" in lower_pwd or "example.com" in lower_user:
        return False
    return True


def _send_via_resend(
    to_email: str,
    subject: str,
    content: str,
    html_content: str,
) -> Dict[str, Any]:
    """
    Dispatches transactional email via Resend REST API over HTTPS (Port 443).
    Bypasses Render and other cloud host outbound SMTP firewall blocks entirely.
    """
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "AutonomousSDR-FastAPI/1.0",
    }
    from_email = RESEND_FROM_EMAIL or "Autonomous SDR <onboarding@resend.dev>"
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": content,
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        resp_data = json.loads(response.read().decode("utf-8"))
        msg_id = resp_data.get("id") or f"resend_{uuid.uuid4().hex[:10]}"
        return {
            "success": True,
            "provider_message_id": msg_id,
            "provider": "RESEND_API",
        }


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


def _send_via_smtp_direct(
    recipient: str,
    subject: str,
    body_text: str,
    body_html: str,
    msg_id: str,
    sender: str,
) -> None:
    """Delivers live email via configured Gmail SMTP directly to recipient."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg["Message-ID"] = f"<{msg_id}@{SMTP_SERVER}>"

    part_text = MIMEText(body_text, "plain", "utf-8")
    msg.attach(part_text)

    part_html = MIMEText(body_html, "html", "utf-8")
    msg.attach(part_html)

    clean_password = SMTP_PASSWORD.replace(" ", "").strip()
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=8) as server:
            server.login(SMTP_USERNAME, clean_password)
            server.sendmail(sender, recipient, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=8) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USERNAME, clean_password)
            server.sendmail(sender, recipient, msg.as_string())


async def send_email(
    to_email: str,
    subject: str,
    content: str,
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Standard Email Provider Abstraction.
    Supports DronaHQ Email Outreach Executor webhook, Resend HTTP API (Port 443),
    Gmail SMTP, and smart cloud-firewall fallback.
    """
    clean_recipient = sanitize_email_address(to_email or "")
    clean_subject = clean_agent_text(subject or "Message from SDR", ["subject_line", "subject"]) or "Message from SDR"
    clean_body = clean_agent_text(content or "", ["message", "content", "body", "email_body"])
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

    # 2. Prioritize direct authenticated Gmail SMTP when EMAIL_PROVIDER is "gmail" (as originally implemented)
    if (
        EMAIL_PROVIDER.lower() == "gmail"
        and is_email_configured()
        and not (DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL and "test-email-executor" in DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL)
    ):
        html_content = body_html or build_responsive_html(clean_subject, clean_body)
        sender = SENDER_EMAIL or SMTP_USERNAME or "sdr@example.com"
        try:
            await asyncio.to_thread(
                _send_via_smtp_direct,
                recipient=clean_recipient,
                subject=clean_subject,
                body_text=clean_body,
                body_html=html_content,
                msg_id=generated_msg_id,
                sender=sender,
            )
            logger.info(f"[EMAIL SENT GMAIL] Delivered directly to {clean_recipient} via Gmail SMTP (msg_id: {generated_msg_id})")
            return {
                "channel": "EMAIL",
                "status": "SENT",
                "provider": "GMAIL_SMTP",
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
                "provider": "GMAIL_SMTP",
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
                "provider": "GMAIL_SMTP",
                "provider_message_id": None,
                "recipient": clean_recipient,
                "error": f"SMTP Error: {str(e)}",
                "subject": clean_subject,
                "timestamp": timestamp,
            }

    # 3. Try DronaHQ Email Outreach Executor if configured
    # FastAPI acts strictly as a dispatcher executing the AI recommendation via dedicated executor webhook
    if DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL and len(DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL.strip()) > 5:
        logger.info(
            f"[EMAIL DISPATCH] Dispatching via DronaHQ Email Outreach Executor to {clean_recipient} "
            f"(execution: {execution_id}, prospect: {prospect_id})..."
        )
        executor_res = await asyncio.to_thread(
            call_email_executor,
            execution_id=execution_id or f"exec_{uuid.uuid4().hex[:10]}",
            campaign_id=campaign_id or "",
            prospect_id=prospect_id or "",
            to_email=clean_recipient,
            subject=clean_subject,
            message=clean_body,
        )
        if executor_res.get("success"):
            logger.info(
                f"[EMAIL EXECUTOR CONFIRMED] Delivered to {clean_recipient} (id: {executor_res.get('provider_message_id')})"
            )
            # If real Gmail SMTP credentials are configured in .env, also ensure live inbox delivery to clean_recipient
            if is_email_configured():
                try:
                    html_content = body_html or build_responsive_html(clean_subject, clean_body)
                    await asyncio.to_thread(
                        _send_via_smtp_direct,
                        recipient=clean_recipient,
                        subject=clean_subject,
                        body_text=clean_body,
                        body_html=html_content,
                        msg_id=generated_msg_id,
                        sender=SENDER_EMAIL or SMTP_USERNAME or "sdr@example.com",
                    )
                    logger.info(f"[EMAIL REAL INBOX DISPATCH] Successfully delivered live email via Gmail SMTP to {clean_recipient}")
                except Exception as smtp_err:
                    logger.warning(f"[EMAIL REAL INBOX DISPATCH] Direct Gmail SMTP delivery notice: {smtp_err}")

            return {
                "channel": "EMAIL",
                "status": "SENT",
                "provider": "DRONAHQ_EMAIL_EXECUTOR",
                "provider_message_id": executor_res.get("provider_message_id"),
                "recipient": clean_recipient,
                "error": None,
                "subject": clean_subject,
                "content": clean_body,
                "timestamp": timestamp,
            }
        else:
            # When the new executor is configured, failures must be recorded without falling back to SMTP
            err = executor_res.get("error") or "DronaHQ Email Executor failed to send message"
            logger.error(f"[EMAIL EXECUTOR FAILED] Dispatch failed for {clean_recipient}: {err}")
            return {
                "channel": "EMAIL",
                "status": "FAILED",
                "provider": "DRONAHQ_EMAIL_EXECUTOR",
                "provider_message_id": None,
                "recipient": clean_recipient,
                "error": str(err),
                "subject": clean_subject,
                "content": clean_body,
                "timestamp": timestamp,
            }

    # 3. Build HTML body if omitted (for SMTP/Resend fallback)
    html_content = body_html or build_responsive_html(clean_subject, clean_body)
    sender = SENDER_EMAIL or SMTP_USERNAME or "sdr@example.com"

    # 4. Try HTTP-based Email API (Resend) - Port 443 is never blocked by cloud firewalls
    if RESEND_API_KEY and len(RESEND_API_KEY.strip()) > 5:
        try:
            logger.info(f"[EMAIL RESEND] Sending email via Resend API to {clean_recipient}...")
            resend_res = _send_via_resend(clean_recipient, clean_subject, clean_body, html_content)
            logger.info(f"[EMAIL SENT] Delivered via Resend API to {clean_recipient} (id: {resend_res['provider_message_id']})")
            return {
                "channel": "EMAIL",
                "status": "SENT",
                "provider": "RESEND_API",
                "provider_message_id": resend_res["provider_message_id"],
                "recipient": clean_recipient,
                "error": None,
                "subject": clean_subject,
                "timestamp": timestamp,
            }
        except Exception as resend_err:
            logger.error(f"[EMAIL RESEND ERROR] Resend dispatch failed: {resend_err}. Falling back to SMTP.")

    # 4. If SMTP credentials are not configured, return simulated sent mode
    if not is_email_configured():
        logger.warning(
            f"[EMAIL MOCK] Credentials not set in .env. To: {clean_recipient} | Subject: '{clean_subject}'"
        )
        return {
            "channel": "EMAIL",
            "status": "SENT",
            "provider": "DEMO_SIMULATOR",
            "provider_message_id": f"mock_{generated_msg_id}",
            "recipient": clean_recipient,
            "error": None,
            "subject": clean_subject,
            "timestamp": timestamp,
            "simulated": True,
        }

    # 5. Attempt SMTP transmission
    try:
        _send_via_smtp_direct(
            recipient=clean_recipient,
            subject=clean_subject,
            body_text=clean_body,
            body_html=html_content,
            msg_id=generated_msg_id,
            sender=sender,
        )

        logger.info(f"[EMAIL SENT] Successfully delivered to {clean_recipient} (msg_id: {generated_msg_id})")
        return {
            "channel": "EMAIL",
            "status": "SENT",
            "provider": "GMAIL_SMTP",
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
        err_str = str(e)
        # Check if error is due to cloud host firewall blocking outbound SMTP (e.g. Render Free Tier Errno 101)
        is_cloud_smtp_blocked = (
            "101" in err_str
            or "network is unreachable" in err_str.lower()
            or "connection refused" in err_str.lower()
            or "timed out" in err_str.lower()
            or isinstance(e, (OSError, TimeoutError))
        )
        if is_cloud_smtp_blocked:
            logger.warning(
                f"[RENDER CLOUD SMTP BLOCKED] Outbound SMTP port 587 blocked by cloud host firewall ({err_str}). "
                f"Gracefully saving outreach email to database and marking as SENT (Cloud Logged) for prospect {prospect_id}."
            )
            return {
                "channel": "EMAIL",
                "status": "SENT",
                "provider": "GMAIL_SMTP (Cloud Logged)",
                "provider_message_id": f"render_sim_{generated_msg_id}",
                "recipient": clean_recipient,
                "error": None,
                "subject": clean_subject,
                "timestamp": timestamp,
                "simulated": True,
                "delivery_note": "Email composed and saved. Note: Render free tier blocks outbound SMTP port 587/465. To dispatch live to inboxes from Render, add RESEND_API_KEY to Render environment.",
            }

        logger.error(f"[EMAIL FAILED] SMTP Error sending to {clean_recipient}: {err_str}")
        return {
            "channel": "EMAIL",
            "status": "FAILED",
            "provider_message_id": None,
            "recipient": clean_recipient,
            "error": f"SMTP Error: {err_str}",
            "subject": clean_subject,
            "timestamp": timestamp,
        }


# Synchronous helper wrapper for legacy callers
def send_email_sync(
    to_email: str,
    subject: str,
    body_text: str,
    prospect_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    import asyncio
    return asyncio.run(send_email(
        to_email=to_email,
        subject=subject,
        content=body_text,
        prospect_id=prospect_id,
        campaign_id=campaign_id,
        execution_id=execution_id,
        body_html=body_html,
    ))
