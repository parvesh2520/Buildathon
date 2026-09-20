"""
Gmail IMAP Reply Poller
=========================
Connects to Gmail via IMAP using existing SMTP App Password credentials.
Finds UNSEEN emails in INBOX, matches them to known prospects by email address,
and routes each reply through the Conversation Agent pipeline.

Runs automatically every GMAIL_POLL_INTERVAL_SECONDS (default 7200 = 2 hours).
Can also be triggered manually via POST /api/inbound/gmail/poll.
"""

import email as email_lib
import imaplib
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from email.header import decode_header
from typing import Any, Dict, List, Optional, Tuple

from app.config import (
    SMTP_USERNAME,
    SMTP_PASSWORD,
    GMAIL_POLL_INTERVAL_SECONDS,
)
from app.services.supabase_db import _request

logger = logging.getLogger("sdr.gmail_poller")

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Global lock — prevents concurrent polls from processing the same emails twice
_poll_lock = threading.Lock()


# ---------------------------------------------------------------------------
# IMAP helpers
# ---------------------------------------------------------------------------

def _connect_imap() -> Optional[imaplib.IMAP4_SSL]:
    """Open an authenticated IMAP connection to Gmail."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("[GMAIL POLL] SMTP_USERNAME or SMTP_PASSWORD not configured — skipping.")
        return None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(SMTP_USERNAME, SMTP_PASSWORD)
        return mail
    except imaplib.IMAP4.error as e:
        logger.error(f"[GMAIL POLL] IMAP login failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[GMAIL POLL] IMAP connection error: {str(e)}")
        return None


def _decode_mime_words(raw: str) -> str:
    """Decode MIME-encoded header values (e.g. =?utf-8?b?...?=)."""
    parts = decode_header(raw or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                decoded.append(part.decode("utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_email_address(raw_from: str) -> str:
    """Pull just the email address out of a From: header like 'John Doe <john@example.com>'."""
    match = re.search(r"<([^>]+)>", raw_from)
    if match:
        return match.group(1).strip().lower()
    # Bare email with no display name
    return raw_from.strip().lower()


def _extract_body(msg: email_lib.message.Message) -> str:
    """Extract the plain-text body from an email (handles multipart)."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in disp:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return str(msg.get_payload())
    return ""


def _find_prospect_by_email(from_email: str) -> Optional[Dict[str, Any]]:
    """Look up a prospect in Supabase by their email address."""
    res = _request(f"prospects?email=eq.{from_email}&select=*&limit=1")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return None


def _find_campaign_for_prospect(prospect_id: str) -> Optional[str]:
    """Find the most recent active campaign for this prospect via outreach_messages."""
    res = _request(
        f"outreach_messages?prospect_id=eq.{prospect_id}"
        f"&select=campaign_id&order=created_at.desc&limit=1"
    )
    if isinstance(res, list) and len(res) > 0:
        return res[0].get("campaign_id")
    return None


# ---------------------------------------------------------------------------
# Main poll function
# ---------------------------------------------------------------------------

async def poll_gmail_replies() -> Dict[str, Any]:
    """
    Connect to Gmail via IMAP, find UNSEEN emails in INBOX,
    match each to a prospect, and route to the Conversation Agent.

    Returns a summary dict of what was processed.
    """
    if not _poll_lock.acquire(blocking=False):
        logger.info("[GMAIL POLL] Another poll is already running — skipping this cycle.")
        return {"status": "skipped", "reason": "poll already in progress"}

    processed = 0
    skipped = 0
    errors = 0
    results: List[Dict[str, Any]] = []

    try:
        mail = _connect_imap()
        if mail is None:
            return {
                "status": "error",
                "reason": "IMAP connection failed — check SMTP_USERNAME and SMTP_PASSWORD",
                "processed": 0,
            }

        try:
            mail.select("INBOX")
            # Search for UNSEEN (unread) emails only
            status, msg_ids = mail.search(None, "UNSEEN")
            if status != "OK" or not msg_ids[0]:
                logger.info("[GMAIL POLL] No unseen emails found.")
                return {"status": "ok", "processed": 0, "skipped": 0, "errors": 0}

            id_list = msg_ids[0].split()
            logger.info(f"[GMAIL POLL] Found {len(id_list)} unseen email(s) to process.")

            for msg_id in id_list:
                try:
                    # Fetch the full email
                    status, data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK" or not data or not data[0]:
                        skipped += 1
                        continue

                    raw_email = data[0][1]
                    msg = email_lib.message_from_bytes(raw_email)

                    # Extract fields
                    raw_from = msg.get("From", "")
                    from_email = _extract_email_address(raw_from)
                    subject = _decode_mime_words(msg.get("Subject", ""))
                    message_id_header = msg.get("Message-ID", "") or str(uuid.uuid4())
                    body = _extract_body(msg).strip()

                    if not from_email or not body:
                        logger.info(f"[GMAIL POLL] Skipping email from '{raw_from}' — empty body or address.")
                        # Mark as seen so we don't re-process
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        skipped += 1
                        continue

                    # Skip emails FROM ourselves (outbound echoes)
                    if from_email == (SMTP_USERNAME or "").lower():
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        skipped += 1
                        continue

                    # Look up prospect
                    prospect = _find_prospect_by_email(from_email)
                    if not prospect:
                        logger.info(
                            f"[GMAIL POLL] Email from {from_email} — no matching prospect found. Skipping."
                        )
                        # Do NOT mark as seen — it might be a genuine email from a non-prospect
                        skipped += 1
                        continue

                    prospect_id = prospect.get("id", "")
                    campaign_id = _find_campaign_for_prospect(prospect_id) or ""

                    # Use Message-ID header as idempotency key (strip angle brackets)
                    stable_id = message_id_header.strip().strip("<>").replace("@", "_at_")

                    logger.info(
                        f"[GMAIL POLL] Routing reply from {from_email} "
                        f"(prospect: {prospect_id}, campaign: {campaign_id})"
                    )

                    # Route to Conversation Agent
                    from app.services.conversation import handle_inbound_message
                    result = await handle_inbound_message(
                        message_id=stable_id,
                        prospect_id=prospect_id,
                        campaign_id=campaign_id,
                        channel="EMAIL",
                        prospect_message=body,
                        to_address=from_email,
                        subject=subject,
                        prospect_info={
                            "name": prospect.get("name"),
                            "company": prospect.get("company"),
                            "email": from_email,
                        },
                    )

                    # Mark email as SEEN so we don't re-process on next poll
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    processed += 1
                    results.append({
                        "from": from_email,
                        "prospect_id": prospect_id,
                        "action": result.get("action"),
                    })

                except Exception as e:
                    logger.error(f"[GMAIL POLL] Error processing email {msg_id}: {str(e)}")
                    errors += 1

        finally:
            try:
                mail.logout()
            except Exception:
                pass

    finally:
        _poll_lock.release()

    logger.info(
        f"[GMAIL POLL] Cycle complete — processed: {processed}, skipped: {skipped}, errors: {errors}"
    )
    return {
        "status": "ok",
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "polled_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Background auto-poller thread
# ---------------------------------------------------------------------------

def _run_background_poller():
    """
    Background thread that calls poll_gmail_replies() every
    GMAIL_POLL_INTERVAL_SECONDS seconds. Runs as a daemon so it
    stops automatically when the server shuts down.
    """
    import asyncio

    interval = GMAIL_POLL_INTERVAL_SECONDS
    logger.info(f"[GMAIL POLLER] Auto-poll started — interval: {interval}s ({interval // 3600}h)")

    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(poll_gmail_replies())
            loop.close()
            logger.info(f"[GMAIL POLLER] Poll result: {result}")
        except Exception as e:
            logger.error(f"[GMAIL POLLER] Unhandled error in poll cycle: {str(e)}")

        # Sleep until next cycle
        logger.info(f"[GMAIL POLLER] Next poll in {interval}s ({interval // 60} min).")
        time.sleep(interval)


def start_background_gmail_poller():
    """
    Launch the Gmail reply poller as a background daemon thread.
    Call this once from app startup (main.py lifespan).
    Does nothing if GMAIL_POLL_INTERVAL_SECONDS == 0.
    """
    if not GMAIL_POLL_INTERVAL_SECONDS or GMAIL_POLL_INTERVAL_SECONDS <= 0:
        logger.info("[GMAIL POLLER] Auto-poll disabled (GMAIL_POLL_INTERVAL_SECONDS=0).")
        return

    thread = threading.Thread(target=_run_background_poller, daemon=True, name="gmail-poller")
    thread.start()
    logger.info(f"[GMAIL POLLER] Background thread started (interval: {GMAIL_POLL_INTERVAL_SECONDS}s).")
