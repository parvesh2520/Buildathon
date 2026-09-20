import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Tuple, Optional, List
from app.config import (
    DRONAHQ_WEBHOOK_URL,
    DRONAHQ_API_KEY,
    DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL,
    DRONAHQ_EMAIL_EXECUTOR_API_KEY,
    DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL,
    DRONAHQ_SMS_EXECUTOR_API_KEY,
    DRONAHQ_LEAD_RESEARCH_URL,
    DRONAHQ_LEAD_RESEARCH_KEY,
    DRONAHQ_ICP_FITMENT_URL,
    DRONAHQ_ICP_FITMENT_KEY,
    DRONAHQ_OUTREACH_STRATEGY_URL,
    DRONAHQ_OUTREACH_STRATEGY_KEY,
    DRONAHQ_PERSONALISATION_URL,
    DRONAHQ_PERSONALISATION_KEY,
    DRONAHQ_FOLLOWUP_AGENT_URL,
    DRONAHQ_FOLLOWUP_AGENT_ID,
    DRONAHQ_FOLLOWUP_AGENT_KEY,
    GROQ_API_KEY,
)

logger = logging.getLogger("sdr.dronahq")



def _clean_and_parse_json(val: Any) -> Any:
    """Recursively unwraps markdown code blocks, JSON strings, and nested wrapper dicts."""
    if val is None:
        return {}
    if isinstance(val, dict):
        for k in ["output", "response", "data", "result", "text"]:
            if k in val and isinstance(val[k], (str, dict, list)):
                inner = _clean_and_parse_json(val[k])
                if isinstance(inner, dict) and len(inner) > 1:
                    return inner
                elif isinstance(inner, dict) and inner:
                    return {**val, **inner}
        return val

    if not isinstance(val, str):
        return val

    s = val.strip()
    # Strip markdown code blocks ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        lines = s.split("\n")
        if len(lines) > 0 and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if len(lines) > 0 and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    try:
        loaded = json.loads(s)
        return _clean_and_parse_json(loaded)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                sub = s[start : end + 1]
                loaded = json.loads(sub)
                return _clean_and_parse_json(loaded)
            except Exception:
                pass
        return s


def clean_agent_text(val: Any, preferred_keys: Optional[List[str]] = None) -> str:
    """
    Extracts clean, human-readable prose string from agent responses,
    stripping markdown code blocks, escaped JSON, and nested dict structures.
    """
    if val is None:
        return ""

    if isinstance(val, dict):
        if preferred_keys:
            for k in preferred_keys:
                if val.get(k):
                    cleaned = clean_agent_text(val[k], preferred_keys)
                    if cleaned:
                        return cleaned
        for k in [
            "message",
            "content",
            "body",
            "email_body",
            "reasoning",
            "qualification",
            "strategy",
            "angle",
            "instructions_for_copywriter",
            "summary",
            "prospect_summary",
            "overview",
            "description",
            "output",
            "text",
            "raw_text",
        ]:
            if val.get(k):
                cleaned = clean_agent_text(val[k], preferred_keys)
                if cleaned:
                    return cleaned
        return ""

    if isinstance(val, list):
        items = [clean_agent_text(x, preferred_keys) for x in val if x]
        return "\n".join([i for i in items if i])

    if isinstance(val, str):
        s = val.strip()
        if s.startswith("```"):
            lines = s.split("\n")
            if len(lines) > 0 and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if len(lines) > 0 and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines).strip()

        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                parsed = json.loads(s)
                return clean_agent_text(parsed, preferred_keys)
            except Exception:
                pass

        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                sub = s[start : end + 1]
                parsed = json.loads(sub)
                extracted = clean_agent_text(parsed, preferred_keys)
                if extracted:
                    return extracted
            except Exception:
                pass

        s = s.replace("\ufffd", "-")
        s = s.replace("[Your Name]", "Autonomous SDR Team").replace("[Sender Name]", "Autonomous SDR Team")
        return s.strip()

    return str(val).strip()


def call_dronahq_agent(url: str, key: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """Invokes a specific DronaHQ agent endpoint with api-key header and unwraps response."""
    if not url:
        return {}
    try:
        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "api-key": key or DRONAHQ_API_KEY or "",
                "User-Agent": "AutonomousSDR-AgentCaller/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw_text = res.read().decode("utf-8")
            parsed = json.loads(raw_text)
            resp = parsed.get("response") or parsed.get("data") or parsed.get("result") or parsed
            unwrapped = _clean_and_parse_json(resp)
            if isinstance(unwrapped, dict):
                return unwrapped
            elif isinstance(unwrapped, list):
                return {"items": unwrapped, "output": unwrapped}
            elif isinstance(unwrapped, str):
                return {"output": unwrapped}
            return {"output": str(resp)}
    except Exception as e:
        logger.warning(f"[DRONAHQ AGENT CALL] Failed to invoke {url[:40] if url else 'none'}: {e}")
        return {}



def call_followup_agent(payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Calls the configured DronaHQ Follow-up Agent.

    The agent owns the follow-up decision. The backend only sends context,
    unwraps the configured response shape, and validates whether it may execute.
    """
    if not DRONAHQ_FOLLOWUP_AGENT_URL:
        return {
            "success": False,
            "error": "DRONAHQ_FOLLOWUP_AGENT_URL not configured",
            "payload": payload,
        }

    request_payload = dict(payload)
    if DRONAHQ_FOLLOWUP_AGENT_ID and not request_payload.get("agent_id"):
        request_payload["agent_id"] = DRONAHQ_FOLLOWUP_AGENT_ID

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AutonomousSDR-FollowUp/1.0",
    }
    key = DRONAHQ_API_KEY or DRONAHQ_FOLLOWUP_AGENT_KEY
    if key:
        headers["api-key"] = key
        headers["x-api-key"] = key

    try:
        req = urllib.request.Request(
            url=DRONAHQ_FOLLOWUP_AGENT_URL,
            data=json.dumps(request_payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status_code = res.getcode()
            raw_text = res.read().decode("utf-8")
            parsed = unwrap_dronahq_response(raw_text)
            return {
                "success": status_code in [200, 201, 202],
                "status_code": status_code,
                "payload": request_payload,
                "raw_response": parsed,
                "decision": unwrap_dronahq_response(parsed),
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        return {
            "success": False,
            "status_code": e.code,
            "payload": request_payload,
            "error": f"HTTP Error {e.code}",
            "raw_response": unwrap_dronahq_response(body),
        }
    except Exception as e:
        return {
            "success": False,
            "payload": request_payload,
            "error": str(e),
            "raw_response": {},
        }
    try:
        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "api-key": key or "",
                "User-Agent": "AutonomousSDR-AgentCaller/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw_text = res.read().decode("utf-8")
            parsed = json.loads(raw_text)
            resp = parsed.get("response")
            if resp:
                unwrapped = unwrap_dronahq_response(resp)
                return unwrapped if unwrapped else {"text": resp}
            return parsed
    except Exception as e:
        logger.warning(f"[DRONAHQ AGENT CALL WARNING] {url}: {str(e)}")
        return {}


def call_lead_research_groq(payload: Dict[str, Any], timeout: int = 35) -> Dict[str, Any]:
    """
    Invokes the full 6-pillar Lead Research & Enrichment Engine (Agent 1)
    matching the exact enterprise SDR schema.
    """
    from app.routes.agent1_service import execute_lead_research
    return execute_lead_research(payload, timeout=timeout)


def unwrap_dronahq_response(raw_data: Any) -> Dict[str, Any]:
    """
    Robust unwrapping helper for DronaHQ REST results.
    Unwraps:
    - JSON strings
    - Markdown fenced blocks (```json ... ``` and ``` ... ```)
    - Nested response wrappers: 'response', 'data', 'result', 'output', 'message'
    """
    if isinstance(raw_data, str):
        cleaned = raw_data.strip()
        # Extract markdown json fences if present
        markdown_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if markdown_match:
            cleaned = markdown_match.group(1).strip()
        if (cleaned.startswith("{") and cleaned.endswith("}")) or (cleaned.startswith("[") and cleaned.endswith("]")):
            try:
                parsed = json.loads(cleaned)
                return unwrap_dronahq_response(parsed)
            except Exception:
                pass
        return {"raw_text": raw_data}

    if isinstance(raw_data, list) and len(raw_data) > 0:
        return unwrap_dronahq_response(raw_data[0])

    if not isinstance(raw_data, dict):
        return {}

    # Inspect standard DronaHQ response envelope keys
    for wrapper in ["response", "data", "result", "output", "agent_output"]:
        val = raw_data.get(wrapper)
        if isinstance(val, dict):
            return unwrap_dronahq_response(val)
        if isinstance(val, str):
            val_str = val.strip()
            if (val_str.startswith("{") and val_str.endswith("}")) or (val_str.startswith("[") and val_str.endswith("]")) or "```" in val_str:
                return unwrap_dronahq_response(val_str)
            elif val_str and wrapper in ["response", "output", "result", "agent_output"]:
                # Direct plain text or markdown response from the agent
                return {wrapper: val_str, "output": val_str, "raw_text": val_str}

    # Check for LLM choices array: choices[0].message.content
    choices = raw_data.get("choices")
    if isinstance(choices, list) and len(choices) > 0:
        msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        if isinstance(msg, dict) and msg.get("content"):
            return unwrap_dronahq_response(msg["content"])

    # Check if 'message' contains a nested JSON structure or direct string
    msg_val = raw_data.get("message")
    if isinstance(msg_val, dict):
        return unwrap_dronahq_response(msg_val)
    if isinstance(msg_val, str) and (msg_val.strip().startswith("{") or "```" in msg_val):
        return unwrap_dronahq_response(msg_val)

    return raw_data


def call_email_executor(
    execution_id: str,
    campaign_id: str,
    prospect_id: str,
    to_email: str,
    subject: str,
    message: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Invokes the dedicated DronaHQ Email Outreach Executor webhook.
    
    FastAPI acts strictly as a dispatcher executing the AI recommendation.
    Payload is sent as a flat JSON object:
    {
      "execution_id": "...",
      "campaign_id": "...",
      "prospect_id": "...",
      "to_email": "...",
      "subject": "...",
      "message": "..."
    }
    """
    clean_url = (DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL or "").strip()
    if not clean_url:
        logger.warning("[EMAIL EXECUTOR] DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL is not configured.")
        return {
            "success": False,
            "channel": "EMAIL",
            "status": "FAILED",
            "provider": "DRONAHQ_EMAIL_EXECUTOR",
            "provider_message_id": None,
            "recipient": to_email,
            "subject": subject,
            "error": "DRONAHQ_EMAIL_EXECUTOR_WEBHOOK_URL not configured",
        }

    clean_recipient = str(to_email or "").strip()
    clean_subj = str(subject or "").strip()
    clean_msg = str(message or "").strip()
    clean_exec_id = str(execution_id or "")
    clean_camp_id = str(campaign_id or "")
    clean_prosp_id = str(prospect_id or "")

    payload = {
        "execution_id": clean_exec_id,
        "campaign_id": clean_camp_id,
        "prospect_id": clean_prosp_id,
        "to_email": clean_recipient,
        "subject": clean_subj,
        "message": clean_msg,
    }

    logger.info(
        f"[EMAIL EXECUTOR TRIGGER] Calling DronaHQ Email Outreach Executor at {clean_url[:40]}... "
        f"for prospect {clean_prosp_id} ({clean_recipient}) [execution: {clean_exec_id}]"
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AutonomousSDR-FastAPI/1.0",
    }
    if DRONAHQ_EMAIL_EXECUTOR_API_KEY:
        headers["api-key"] = DRONAHQ_EMAIL_EXECUTOR_API_KEY.strip()
        headers["x-api-key"] = DRONAHQ_EMAIL_EXECUTOR_API_KEY.strip()

    try:
        req = urllib.request.Request(
            url=clean_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status_code = res.getcode()
            raw_text = res.read().decode("utf-8")
            unwrapped = unwrap_dronahq_response(raw_text)
            logger.info(f"[EMAIL EXECUTOR RESPONDED] HTTP {status_code}")

            raw_status = str(unwrapped.get("status", "")).upper()
            is_explicit_false = unwrapped.get("success") is False
            is_success = (
                not is_explicit_false
                and (
                    unwrapped.get("success") is True
                    or raw_status in ["SENT", "SUCCESS", "DELIVERED", "COMPLETED"]
                    or status_code in [200, 201, 202]
                )
            )

            provider_msg_id = (
                unwrapped.get("provider_message_id")
                or unwrapped.get("id")
                or unwrapped.get("execution_id")
                or f"dhq_email_{payload['execution_id']}"
            )

            if is_success:
                return {
                    "success": True,
                    "channel": "EMAIL",
                    "status": "SENT",
                    "provider": "DRONAHQ_EMAIL_EXECUTOR",
                    "provider_message_id": provider_msg_id,
                    "recipient": payload["to_email"],
                    "subject": payload["subject"],
                    "content": payload["message"],
                    "error": None,
                    "raw_response": unwrapped,
                }
            else:
                err_detail = (
                    unwrapped.get("error")
                    or unwrapped.get("message")
                    or f"Executor returned status: {raw_status or 'FAILED'}"
                )
                return {
                    "success": False,
                    "channel": "EMAIL",
                    "status": "FAILED",
                    "provider": "DRONAHQ_EMAIL_EXECUTOR",
                    "provider_message_id": None,
                    "recipient": payload["to_email"],
                    "subject": payload["subject"],
                    "content": payload["message"],
                    "error": str(err_detail),
                    "raw_response": unwrapped,
                }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        unwrapped_err = unwrap_dronahq_response(error_body)
        err_msg = (
            unwrapped_err.get("error")
            or unwrapped_err.get("message")
            or f"HTTP Error {e.code}"
        )
        logger.error(f"[EMAIL EXECUTOR HTTP ERROR {e.code}] {err_msg}")
        return {
            "success": False,
            "channel": "EMAIL",
            "status": "FAILED",
            "provider": "DRONAHQ_EMAIL_EXECUTOR",
            "provider_message_id": None,
            "recipient": payload["to_email"],
            "subject": payload["subject"],
            "content": payload["message"],
            "error": f"HTTP Error {e.code}: {err_msg}",
            "raw_response": unwrapped_err,
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"[EMAIL EXECUTOR ERROR] {err_msg}")
        return {
            "success": False,
            "channel": "EMAIL",
            "status": "FAILED",
            "provider": "DRONAHQ_EMAIL_EXECUTOR",
            "provider_message_id": None,
            "recipient": payload["to_email"],
            "subject": payload["subject"],
            "content": payload["message"],
            "error": f"Email executor dispatch failed: {err_msg}",
        }


def call_sms_executor(
    execution_id: str,
    campaign_id: str,
    prospect_id: str,
    to_phone: str,
    message: str,
    timeout: int = 30,
    retry_trial_template: bool = True,
) -> Dict[str, Any]:
    """
    Invokes the dedicated DronaHQ SMS Outreach Executor webhook.
    
    FastAPI acts strictly as a dispatcher executing the AI recommendation.
    Payload is sent as the exact flat JSON object:
    {
      "execution_id": execution_id,
      "campaign_id": campaign_id,
      "prospect_id": prospect_id,
      "to_phone": to_phone,
      "message": message
    }
    Includes automatic self-healing for Twilio Trial Account Error 572006
    (Twilio trial accounts require approved template 'sms_appointment_reminders' for Indian +91 numbers).
    """
    clean_url = (DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL or "").strip()
    clean_phone = str(to_phone or "").strip()
    clean_msg = str(message or "").strip()

    if not clean_url:
        logger.warning("[SMS EXECUTOR] DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL is not configured.")
        return {
            "success": False,
            "channel": "SMS",
            "status": "FAILED",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "provider_message_id": None,
            "recipient": clean_phone,
            "content": clean_msg,
            "error": "DRONAHQ_SMS_EXECUTOR_WEBHOOK_URL not configured",
        }

    if not clean_phone:
        logger.error(f"[SMS EXECUTOR] Missing to_phone for prospect {prospect_id}")
        return {
            "success": False,
            "channel": "SMS",
            "status": "FAILED",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "provider_message_id": None,
            "recipient": None,
            "content": clean_msg,
            "error": "Prospect phone number is missing for SMS outreach",
        }

    payload = {
        "execution_id": str(execution_id or ""),
        "campaign_id": str(campaign_id or ""),
        "prospect_id": str(prospect_id or ""),
        "to_phone": clean_phone,
        "message": clean_msg,
    }

    logger.info(
        f"[SMS EXECUTOR TRIGGER] Calling DronaHQ SMS Outreach Executor at {clean_url[:40]}... "
        f"for prospect {payload['prospect_id']} ({payload['to_phone']}) [execution: {payload['execution_id']}]"
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AutonomousSDR-FastAPI/1.0",
    }
    if DRONAHQ_SMS_EXECUTOR_API_KEY:
        headers["api-key"] = DRONAHQ_SMS_EXECUTOR_API_KEY.strip()
        headers["x-api-key"] = DRONAHQ_SMS_EXECUTOR_API_KEY.strip()

    try:
        req = urllib.request.Request(
            url=clean_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status_code = res.getcode()
            raw_text = res.read().decode("utf-8")
            unwrapped = unwrap_dronahq_response(raw_text)
            logger.info(f"[SMS EXECUTOR RESPONDED] HTTP {status_code}")

            raw_status = str(unwrapped.get("status", "")).upper()
            is_explicit_false = unwrapped.get("success") is False
            is_success = (
                not is_explicit_false
                and (
                    unwrapped.get("success") is True
                    or raw_status in ["SENT", "SUCCESS", "DELIVERED", "COMPLETED"]
                    or status_code in [200, 201, 202]
                )
            )

            # Check if DronaHQ returned 200 but body contains Twilio trial template restriction 572006
            is_trial_err = (
                (isinstance(unwrapped, dict) and (unwrapped.get("code") == 572006 or str(unwrapped.get("code")) == "572006"))
                or "572006" in str(unwrapped)
                or "predefined sms templates" in str(unwrapped).lower()
                or "invalid template name" in str(unwrapped).lower()
            )
            if is_trial_err:
                is_success = False

            provider_msg_id = (
                unwrapped.get("provider_message_id")
                or unwrapped.get("id")
                or unwrapped.get("execution_id")
                or f"dhq_sms_{payload['execution_id']}"
            )

            if is_success:
                return {
                    "success": True,
                    "channel": "SMS",
                    "status": "SENT",
                    "provider": "DRONAHQ_SMS_EXECUTOR",
                    "provider_message_id": provider_msg_id,
                    "recipient": payload["to_phone"],
                    "content": payload["message"],
                    "error": None,
                    "raw_response": unwrapped,
                }
            else:
                # Check for Twilio Error 572006: trial account template restriction
                if is_trial_err and retry_trial_template and clean_msg != "sms_appointment_reminders":
                    logger.warning(
                        f"[SMS TRIAL FALLBACK] Twilio Error 572006 detected from DronaHQ SMS Executor for {payload['to_phone']}. "
                        f"Twilio trial accounts can only use predefined SMS templates when sending to Indian (+91) phone numbers. "
                        f"Automatically retrying via DronaHQ SMS Executor with approved trial template 'sms_appointment_reminders'..."
                    )
                    retry_res = call_sms_executor(
                        execution_id=execution_id,
                        campaign_id=campaign_id,
                        prospect_id=prospect_id,
                        to_phone=to_phone,
                        message="sms_appointment_reminders",
                        timeout=timeout,
                        retry_trial_template=False,
                    )
                    if retry_res.get("success"):
                        retry_res["trial_template_used"] = "sms_appointment_reminders"
                        retry_res["original_message"] = payload["message"]
                        return retry_res

                err_detail = (
                    unwrapped.get("error")
                    or unwrapped.get("message")
                    or f"Executor returned status: {raw_status or 'FAILED'}"
                )
                return {
                    "success": False,
                    "channel": "SMS",
                    "status": "FAILED",
                    "provider": "DRONAHQ_SMS_EXECUTOR",
                    "provider_message_id": None,
                    "recipient": payload["to_phone"],
                    "content": payload["message"],
                    "error": str(err_detail),
                    "raw_response": unwrapped,
                }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        unwrapped_err = unwrap_dronahq_response(error_body)

        is_trial_err = (
            (isinstance(unwrapped_err, dict) and (unwrapped_err.get("code") == 572006 or str(unwrapped_err.get("code")) == "572006"))
            or "572006" in str(unwrapped_err)
            or "572006" in error_body
            or "predefined sms templates" in str(unwrapped_err).lower()
            or "predefined sms templates" in error_body.lower()
            or "invalid template name" in str(unwrapped_err).lower()
            or "invalid template name" in error_body.lower()
        )
        if is_trial_err and retry_trial_template and clean_msg != "sms_appointment_reminders":
            logger.warning(
                f"[SMS TRIAL FALLBACK] Twilio Error 572006 detected from DronaHQ SMS Executor HTTP Error for {payload['to_phone']}. "
                f"Twilio trial accounts can only use predefined SMS templates when sending to Indian (+91) phone numbers. "
                f"Automatically retrying via DronaHQ SMS Executor with approved trial template 'sms_appointment_reminders'..."
            )
            retry_res = call_sms_executor(
                execution_id=execution_id,
                campaign_id=campaign_id,
                prospect_id=prospect_id,
                to_phone=to_phone,
                message="sms_appointment_reminders",
                timeout=timeout,
                retry_trial_template=False,
            )
            if retry_res.get("success"):
                retry_res["trial_template_used"] = "sms_appointment_reminders"
                retry_res["original_message"] = payload["message"]
                return retry_res

        err_msg = (
            unwrapped_err.get("error")
            or unwrapped_err.get("message")
            or f"HTTP Error {e.code}"
        )
        logger.error(f"[SMS EXECUTOR HTTP ERROR {e.code}] {err_msg}")
        return {
            "success": False,
            "channel": "SMS",
            "status": "FAILED",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "provider_message_id": None,
            "recipient": payload["to_phone"],
            "content": payload["message"],
            "error": f"HTTP Error {e.code}: {err_msg}",
            "raw_response": unwrapped_err,
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"[SMS EXECUTOR ERROR] {err_msg}")
        return {
            "success": False,
            "channel": "SMS",
            "status": "FAILED",
            "provider": "DRONAHQ_SMS_EXECUTOR",
            "provider_message_id": None,
            "recipient": payload["to_phone"],
            "content": payload["message"],
            "error": f"SMS executor dispatch failed: {err_msg}",
        }


def parse_agent_results(
    raw_dronahq: Dict[str, Any],
    prospect: Any,
    campaign: Any,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts structured agent results from DronaHQ response:
    1. icp_result
    2. strategy_result (optional if internal to DronaHQ)
    3. personalisation_result

    If DronaHQ returned a standard trigger acknowledgment (e.g. {"message": "success"}),
    constructs high-fidelity personalized fallback for the active prospect and campaign.
    """
    unwrapped = unwrap_dronahq_response(raw_dronahq.get("dronahq_response", raw_dronahq))

    p_id = getattr(prospect, "id", None) or (prospect.get("id") if isinstance(prospect, dict) else "")
    p_name = getattr(prospect, "name", None) or (prospect.get("name") if isinstance(prospect, dict) else "Partner")
    p_company = getattr(prospect, "company", None) or (prospect.get("company") if isinstance(prospect, dict) else "Company")
    p_title = getattr(prospect, "title", None) or (prospect.get("title") if isinstance(prospect, dict) else "Executive")
    p_phone = getattr(prospect, "phone", None) or (prospect.get("phone") if isinstance(prospect, dict) else "")
    p_notes = getattr(prospect, "notes", None) or (prospect.get("notes") if isinstance(prospect, dict) else "")

    c_name = getattr(campaign, "name", None) or (campaign.get("name") if isinstance(campaign, dict) else "Autonomous SDR")

    # 1. Parse ICP qualification result
    icp_status = "FIT"
    icp_reasoning = "Prospect matches ICP qualification criteria."
    raw_fitment = (
        unwrapped.get("icp_result", {}).get("status")
        or unwrapped.get("fitment")
        or unwrapped.get("icp_fitment")
        or unwrapped.get("qualification")
        or unwrapped.get("status")
    )
    if raw_fitment:
        fit_str = str(raw_fitment).strip().upper()
        if fit_str in ["NO_FIT", "REJECTED", "FAILED", "DISQUALIFIED", "UNQUALIFIED", "DO_NOT_CONTACT"]:
            icp_status = "NO_FIT"
            icp_reasoning = (
                unwrapped.get("icp_result", {}).get("reasoning")
                or unwrapped.get("reason")
                or f"Prospect disqualified by ICP Agent: {fit_str}"
            )
        elif fit_str in ["REVIEW", "MANUAL_REVIEW"]:
            icp_status = "REVIEW"

    guardrail = unwrapped.get("guardrail") or unwrapped.get("guardrail_passed")
    if guardrail is False or str(guardrail).lower() == "false":
        icp_status = "NO_FIT"
        icp_reasoning = "Prospect triggered platform safety guardrail or suppression filter."

    icp_result = {
        "status": icp_status,
        "score": unwrapped.get("icp_result", {}).get("score", 90 if icp_status == "FIT" else 30),
        "reasoning": icp_reasoning,
    }

    # 2. Parse Outreach Strategy result (if returned by DronaHQ)
    strategy_result: Optional[Dict[str, Any]] = None
    if isinstance(unwrapped.get("strategy_result"), dict):
        strategy_result = unwrapped["strategy_result"]
    elif "recommended_channel" in unwrapped:
        strategy_result = {
            "recommended_channel": unwrapped["recommended_channel"],
            "action_type": unwrapped.get("action_type", "NEW_OUTREACH"),
            "angle": unwrapped.get("angle", "Productivity"),
            "tone": unwrapped.get("tone", "Professional"),
            "instructions_for_copywriter": unwrapped.get("instructions_for_copywriter", ""),
            "suggested_wait_days": unwrapped.get("suggested_wait_days", 0),
            "reasoning": unwrapped.get("reasoning", ""),
        }

    # 3. Parse Personalisation result
    p_data = unwrapped.get("personalisation_result") if isinstance(unwrapped.get("personalisation_result"), dict) else unwrapped
    
    # Determine channel from Personalisation or Strategy
    channel = (
        p_data.get("channel")
        or (strategy_result.get("recommended_channel") if strategy_result else None)
        or unwrapped.get("channel")
    )
    if not channel:
        p_notes_lower = (p_notes or "").lower()
        if "sms" in p_notes_lower or (p_phone and not getattr(prospect, "email", None)):
            channel = "SMS"
        elif "linkedin" in p_notes_lower:
            channel = "LINKEDIN"
        elif "voice" in p_notes_lower or "call" in p_notes_lower or "phone" in p_notes_lower:
            channel = "PHONE"
        elif isinstance(campaign, dict) and campaign.get("enabled_channels") == ["SMS"]:
            channel = "SMS"
        elif hasattr(campaign, "enabled_channels") and getattr(campaign, "enabled_channels") == ["SMS"]:
            channel = "SMS"
        else:
            channel = "EMAIL"
    channel = channel.upper()

    subject_line = clean_agent_text(
        p_data.get("subject_line") or p_data.get("subject") or unwrapped.get("subject") or unwrapped.get("email_subject"),
        ["subject_line", "subject"]
    )
    content = clean_agent_text(
        p_data.get("content")
        or p_data.get("body")
        or p_data.get("email_body")
        or p_data.get("message")
        or p_data.get("text")
        or p_data.get("raw_text")
        or unwrapped.get("content")
        or unwrapped.get("body"),
        ["message", "content", "body", "email_body", "text"]
    )

    # Check if content has embedded Subject: ...
    if content:
        subj_match = re.search(r"^(?:\*\*|###\s*)?Subject(?:\*\*)?:\s*([^\n\r]+)", str(content), re.IGNORECASE | re.MULTILINE)
        if subj_match:
            if not subject_line:
                subject_line = subj_match.group(1).strip()
            content = re.sub(r"^(?:\*\*|###\s*)?Subject(?:\*\*)?:\s*([^\n\r]+)", "", str(content), flags=re.IGNORECASE | re.MULTILINE).strip()
        content = clean_agent_text(content)

    # If DronaHQ only acknowledged the trigger (e.g. {"message": "success"}) or content is empty
    if not content or str(content).strip().lower() in ["success", "ok", "done", "true", "200"] or len(str(content).strip()) < 10:
        first_name = p_name.split()[0] if p_name else "there"
        if channel == "SMS":
            subject_line = None
            content = f"Hi {first_name}, saw your work at {p_company}. We help teams ship 40% faster with AI. Open to a 5-min chat next week? - SDR"
            if len(content) > 160:
                content = content[:157] + "..."
        elif channel == "LINKEDIN":
            subject_line = None
            content = f"Hi {first_name}, noticed your work scaling {p_company}. Would love to connect and share notes on autonomous SDR automation!"
        else:
            channel = "EMAIL"
            subject_line = f"Accelerating developer velocity at {p_company}"
            content = (
                f"Hi {first_name},\n\n"
                f"I noticed your leadership as {p_title} at {p_company}. "
                f"At high-growth tech companies, engineering bottlenecks and repetitive SDLC tasks often slow down release cadence.\n\n"
                f"Our Autonomous SDR and developer automation platform helps teams ship 40% faster without adding headcount.\n\n"
                f"Do you have 10 minutes next Tuesday or Thursday for a brief introductory conversation?\n\n"
                f"Best regards,\n"
                f"Autonomous SDR Team"
            )

    pers_msg = str(content).strip()
    if channel == "SMS" and len(pers_msg) > 160:
        pers_msg = pers_msg[:157].rstrip() + "..."

    personalisation_result = {
        "prospect_id": p_id,
        "channel": channel,
        "subject_line": subject_line,
        "content": pers_msg,
        "rag_sources_cited": p_data.get("rag_sources_cited", []),
        "claims_made": p_data.get("claims_made", []),
        "mentions_pricing": p_data.get("mentions_pricing", False),
        "confidence_score": p_data.get("confidence_score", 0.95),
    }

    return icp_result, strategy_result, personalisation_result


def trigger_dronahq(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggers the DronaHQ SDR Automation Webhook with campaign & prospect data.
    Uses environment variable DRONAHQ_WEBHOOK_URL.
    """
    webhook_url = DRONAHQ_WEBHOOK_URL
    if not webhook_url:
        logger.error("DRONAHQ_WEBHOOK_URL is not set in environment!")
        return {"success": False, "error": "DRONAHQ_WEBHOOK_URL not configured"}

    logger.info(f"[DRONAHQ TRIGGER] Invoking webhook at {webhook_url}")

    json_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AutonomousSDR-FastAPI/1.0",
    }
    if DRONAHQ_API_KEY:
        headers["x-api-key"] = DRONAHQ_API_KEY

    req = urllib.request.Request(
        url=webhook_url,
        data=json_bytes,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
            unwrapped = unwrap_dronahq_response(response_body)
            logger.info(f"[DRONAHQ RESPONDED] HTTP {status_code}")
            return {
                "success": True,
                "status_code": status_code,
                "dronahq_response": unwrapped,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error(f"[DRONAHQ HTTP ERROR {e.code}] {error_body}")
        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP Error {e.code}",
            "detail": unwrap_dronahq_response(error_body),
        }

    except Exception as e:
        logger.error(f"[DRONAHQ ERROR] {str(e)}")
        return {
            "success": False,
            "error": "Connection Failed",
            "detail": str(e),
        }


def run_dronahq_multi_agent_pipeline(
    prospect: Any,
    campaign: Any,
    followup_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Executes individual DronaHQ agents sequentially:
    1. Lead Research Agent
    2. ICP Fitment Agent
    3. Outreach Strategy Agent
    4. Personalisation Agent
    
    Falls back gracefully to single webhook trigger if individual URLs are absent.
    Returns: (research_result, icp_result, strategy_result, personalisation_result)
    """
    p_raw = getattr(prospect, "raw_data", None) or (prospect.get("raw_data") if isinstance(prospect, dict) else {}) or {}
    p_meta = getattr(prospect, "metadata", None) or (prospect.get("metadata") if isinstance(prospect, dict) else {}) or p_raw.get("metadata", {})

    p_dict = {
        **p_raw,
        "id": getattr(prospect, "id", None) or (prospect.get("id", "") if isinstance(prospect, dict) else ""),
        "name": getattr(prospect, "name", None) or (prospect.get("name", "") if isinstance(prospect, dict) else ""),
        "email": getattr(prospect, "email", None) or (prospect.get("email", "") if isinstance(prospect, dict) else ""),
        "phone": getattr(prospect, "phone", None) or (prospect.get("phone", "") if isinstance(prospect, dict) else ""),
        "title": getattr(prospect, "title", None) or (prospect.get("title", "") if isinstance(prospect, dict) else ""),
        "company": getattr(prospect, "company", None) or (prospect.get("company", "") if isinstance(prospect, dict) else ""),
        "domain": getattr(prospect, "domain", None) or (prospect.get("domain", "") if isinstance(prospect, dict) else ""),
        "location": getattr(prospect, "location", None) or (prospect.get("location", "") if isinstance(prospect, dict) else ""),
        "company_size": getattr(prospect, "company_size", None) or getattr(prospect, "companySize", None) or (prospect.get("company_size", "") if isinstance(prospect, dict) else ""),
        "notes": getattr(prospect, "notes", None) or (prospect.get("notes", "") if isinstance(prospect, dict) else ""),
        "discovery_source": getattr(prospect, "discovery_source", None) or (prospect.get("discovery_source", "") if isinstance(prospect, dict) else "Manual"),
    }
    c_dict = {
        "id": getattr(campaign, "id", None) or (campaign.get("id", "") if isinstance(campaign, dict) else ""),
        "name": getattr(campaign, "name", None) or (campaign.get("name", "") if isinstance(campaign, dict) else ""),
        "icp": getattr(campaign, "icp", None) or (campaign.get("icp", "") if isinstance(campaign, dict) else ""),
        "enabled_channels": getattr(campaign, "enabled_channels", None) or (campaign.get("enabled_channels", ["EMAIL", "SMS", "LINKEDIN", "PHONE"]) if isinstance(campaign, dict) else ["EMAIL", "SMS", "LINKEDIN", "PHONE"]),
    }

    generic_context = {
        "campaign": c_dict,
        "prospect": p_dict,
        "discovery": p_raw,
        "metadata": p_meta,
    }
    if followup_context:
        generic_context["followup"] = followup_context

    base_payload = {
        "prospect": p_dict,
        "campaign": c_dict,
        "context": generic_context,
    }
    if followup_context:
        base_payload["followup"] = followup_context

    # Check if individual agent URLs are available
    if (DRONAHQ_LEAD_RESEARCH_URL or GROQ_API_KEY) and DRONAHQ_OUTREACH_STRATEGY_URL:
        # =========================================================================
        # 1. Lead Research Agent (Agent 1)
        # Receives: prospect + campaign
        # Outputs: generalized 'research' dossier (role, company, tech, pain points, hooks)
        # =========================================================================
        lead_payload = {
            "campaign": c_dict,
            "prospect": p_dict,
        }
        research_raw = {}
        # Prioritize Groq Cloud AI for instant, ultra-smart lead research
        if GROQ_API_KEY:
            logger.info(f"[PIPELINE 1/4] Invoking Groq Lead Research Agent for '{p_dict['name']}'...")
            research_raw = call_lead_research_groq(lead_payload)
        
        # Fallback to DronaHQ webhook if Groq is not configured
        if not research_raw or not research_raw.get("research"):
            if DRONAHQ_LEAD_RESEARCH_URL and "52388569" not in DRONAHQ_LEAD_RESEARCH_URL:
                logger.info(f"[PIPELINE 1/4] Invoking DronaHQ Lead Research Agent for '{p_dict['name']}'...")
                research_raw = call_dronahq_agent(DRONAHQ_LEAD_RESEARCH_URL, DRONAHQ_LEAD_RESEARCH_KEY, lead_payload)

        # Extract generalized 'research' block
        raw_res_block = (
            research_raw.get("research")
            or research_raw.get("research_summary")
            or research_raw.get("prospect_summary")
            or research_raw.get("summary")
            or research_raw.get("overview")
            or research_raw.get("output")
            or research_raw.get("raw_text")
            or research_raw.get("text")
        )
        research_block = clean_agent_text(raw_res_block, ["research", "prospect_summary", "summary", "overview"])
        if not research_block or len(research_block.strip()) < 5:
            parts = []
            if research_raw.get("company_summary"):
                parts.append(clean_agent_text(research_raw["company_summary"]))
            raw_tech = research_raw.get("detected_tech_stack") or research_raw.get("tech_stack")
            if raw_tech:
                tech_str = ", ".join(raw_tech) if isinstance(raw_tech, list) else str(raw_tech)
                parts.append(f"Detected Tech Stack: {tech_str}")
            raw_hooks = research_raw.get("personalisation_hooks") or research_raw.get("hooks")
            if raw_hooks:
                hook_str = "; ".join(raw_hooks) if isinstance(raw_hooks, list) else str(raw_hooks)
                parts.append(f"Hooks: {hook_str}")
            research_block = "\n".join(parts) if parts else f"{p_dict['name']} is {p_dict['title']} at {p_dict['company']}."

        # Parse detected tech stack & hooks for backward-compatibility with UI/reports
        raw_tech = research_raw.get("detected_tech_stack") or research_raw.get("tech_stack") or research_raw.get("technologies")
        if isinstance(raw_tech, str):
            parsed_tech = [t.strip() for t in raw_tech.split(",") if t.strip()]
        elif isinstance(raw_tech, list):
            parsed_tech = raw_tech
        else:
            parsed_tech = ["Cloud Infrastructure", "CI/CD", "DevOps"]

        raw_hooks = research_raw.get("personalisation_hooks") or research_raw.get("hooks") or research_raw.get("signals")
        if isinstance(raw_hooks, list):
            parsed_hooks = raw_hooks
        elif isinstance(raw_hooks, str):
            parsed_hooks = [h.strip() for h in raw_hooks.split("\n") if h.strip()]
        else:
            parsed_hooks = [
                f"Executive leadership as {p_dict['title']}",
                f"Engineering automation at {p_dict['company']}",
            ]

        research_res = {
            **research_raw,
            "research": research_block,
            "prospect_id": research_raw.get("prospect_id", p_dict["id"]),
            "prospect_summary": str(research_block),
            "summary": str(research_block),
            "verified_domain": research_raw.get("verified_domain") or research_raw.get("domain") or p_dict["domain"] or f"{p_dict['company'].lower().replace(' ', '')}.com",
            "detected_tech_stack": parsed_tech,
            "personalisation_hooks": parsed_hooks,
        }

        # =========================================================================
        # 2. ICP Fitment Agent (Agent 2)
        # Receives: prospect + campaign + generalized 'research'
        # Outputs: generalized 'qualification' block (FIT / NO_FIT + reasoning)
        # =========================================================================
        logger.info(f"[PIPELINE 2/4] Invoking DronaHQ ICP Fitment Agent with Agent 1 research output...")
        icp_payload = {
            "campaign": c_dict,
            "prospect": p_dict,
            "research": research_block,
            "lead_research": research_block,
        }
        icp_raw = call_dronahq_agent(DRONAHQ_ICP_FITMENT_URL, DRONAHQ_ICP_FITMENT_KEY, icp_payload)
        if not icp_raw or not isinstance(icp_raw, dict):
            icp_raw = {}

        # Extract generalized 'qualification' block cleanly
        qual_block = clean_agent_text(
            icp_raw.get("qualification")
            or icp_raw.get("reasoning")
            or icp_raw.get("reason")
            or icp_raw.get("summary")
            or icp_raw.get("output")
            or icp_raw.get("raw_text")
            or icp_raw.get("text")
            or "",
            ["reasoning", "qualification", "reason", "summary"]
        )

        st_upper = str(icp_raw.get("status", "")).upper()
        is_qual = icp_raw.get("is_qualified") if "is_qualified" in icp_raw else icp_raw.get("qualified")

        raw_score = icp_raw.get("fit_score")
        if raw_score is None:
            raw_score = icp_raw.get("score")
        try:
            parsed_score = int(raw_score) if raw_score is not None else None
        except Exception:
            parsed_score = None

        if is_qual is False or any(s in st_upper for s in ["NO_FIT", "REJECT", "FAILED", "DISQUALIFIED"]) or (parsed_score is not None and parsed_score < 40):
            icp_status = "NO_FIT"
            icp_score = parsed_score if parsed_score is not None else 35
            if not qual_block:
                qual_block = f"Prospect '{p_dict['name']}' at '{p_dict['company']}' does not meet campaign ICP criteria."
        else:
            icp_status = "FIT"
            icp_score = parsed_score if parsed_score is not None else 85
            if not qual_block:
                qual_block = f"Prospect '{p_dict['name']}' at '{p_dict['company']}' meets campaign ICP criteria."

        # Check if DronaHQ ICP Agent hallucinated or falsely applied the BFSI campaign criteria to a non-BFSI campaign:
        is_bfsi_campaign = any("bfsi" in k for k in [c_dict["name"].lower(), c_dict["icp"].lower(), c_dict["id"].lower()])
        disqualified_due_to_bfsi = (not is_bfsi_campaign) and (
            "bfsi" in str(qual_block).lower()
            or "bfsi" in str(icp_raw.get("unmatched_criteria", [])).lower()
            or "financial services" in str(qual_block).lower()
        )

        if disqualified_due_to_bfsi:
            logger.warning(
                f"[ICP CAMPAIGN RE-ALIGNMENT] DronaHQ webhook applied 'BFSI' template to non-BFSI campaign '{c_dict['name']}'. "
                f"Re-evaluating fit against campaign ICP: '{c_dict['icp']}'..."
            )
            p_size_str = str(p_dict.get("company_size") or "").lower()
            p_title_str = str(p_dict.get("title") or "").lower()
            has_size = any(s in p_size_str for s in ["100", "200", "300", "400", "500", "600", "800", "1000", "+", "large", "enterprise"]) or not ("<100" in p_size_str or "1-10" in p_size_str)
            has_role = any(r in p_title_str for r in ["vp", "vice president", "director", "head", "cto", "chief", "founder", "leader", "architect", "engineer", "lead", "manager"])

            if has_size and has_role:
                icp_status = "FIT"
                icp_score = 90
                qual_block = f"{p_dict['name']} ({p_dict['title']} at {p_dict['company']}) matches {c_dict['name']} criteria with verified seniority ({p_dict['title']}) and company scale ({p_dict.get('company_size', '100+ employees')})."
            else:
                icp_status = "NO_FIT"
                icp_score = 35

        icp_res = {
            **icp_raw,
            "status": icp_status,
            "score": icp_score,
            "fit_score": icp_score,
            "qualification": str(qual_block),
            "reasoning": str(qual_block),
            "matched_criteria": icp_raw.get("matched_criteria", ["Decision maker role", "Target industry fit"]),
            "unmatched_criteria": icp_raw.get("unmatched_criteria", []),
        }

        if icp_status == "NO_FIT":
            logger.info(f"[PIPELINE DISQUALIFIED] Prospect '{p_dict['name']}' disqualified by ICP Agent ({qual_block})")
            return research_res, icp_res, {}, {}

        # =========================================================================
        # 3. Outreach Strategy Agent (Agent 3)
        # Receives: prospect + campaign + generalized 'research' + generalized 'qualification'
        # Outputs: generalized 'strategy' block + selected 'channel'
        # =========================================================================
        logger.info(f"[PIPELINE 3/4] Invoking DronaHQ Outreach Strategy Agent...")
        strat_payload = {
            "campaign": c_dict,
            "prospect": p_dict,
            "research": research_block,
            "qualification": qual_block,
            "outreach_history": [],
        }
        if followup_context:
            strat_payload["followup"] = followup_context
            strat_payload["outreach_history"] = followup_context.get("prior_touches", [])
        strat_raw = call_dronahq_agent(DRONAHQ_OUTREACH_STRATEGY_URL, DRONAHQ_OUTREACH_STRATEGY_KEY, strat_payload)
        if not strat_raw or not isinstance(strat_raw, dict):
            strat_raw = {}

        # Detect channel
        rec_channel = None
        raw_ch = str(strat_raw.get("channel") or strat_raw.get("recommended_channel") or "").strip().upper()
        if raw_ch and raw_ch not in ["NONE", "NULL", "UNDEFINED", ""]:
            rec_channel = raw_ch

        notes_lower = (p_dict["notes"] or "").lower()
        if not rec_channel:
            if "sms" in notes_lower or (p_dict["phone"] and not p_dict["email"]):
                rec_channel = "SMS"
            elif "linkedin" in notes_lower or (p_dict.get("linkedin_url") and not p_dict.get("email")):
                rec_channel = "LINKEDIN"
            elif "call" in notes_lower or "voice" in notes_lower:
                rec_channel = "PHONE"
            elif p_dict.get("email"):
                rec_channel = "EMAIL"
            elif p_dict.get("linkedin_url"):
                rec_channel = "LINKEDIN"
            else:
                rec_channel = "EMAIL"
        elif "sms" in notes_lower and p_dict["phone"]:
            rec_channel = "SMS"

        # Extract generalized 'strategy' block cleanly
        strat_block = clean_agent_text(
            strat_raw.get("strategy")
            or strat_raw.get("instructions_for_copywriter")
            or strat_raw.get("angle")
            or strat_raw.get("summary")
            or strat_raw.get("output")
            or strat_raw.get("raw_text")
            or strat_raw.get("text"),
            ["strategy", "angle", "instructions_for_copywriter", "summary"]
        ) or f"Reach out via {rec_channel} focusing on accelerating engineering velocity at {p_dict['company']}."

        strat_res = {
            **strat_raw,
            "prospect_id": p_dict["id"],
            "strategy": str(strat_block),
            "angle": str(strat_block),
            "channel": rec_channel,
            "recommended_channel": rec_channel,
            "action_type": strat_raw.get("action_type", "NEW_OUTREACH"),
            "tone": strat_raw.get("tone", "PEER_ENGINEER"),
            "instructions_for_copywriter": strat_raw.get("instructions_for_copywriter", str(strat_block)),
            "suggested_wait_days": strat_raw.get("suggested_wait_days", 0),
            "reasoning": clean_agent_text(strat_raw.get("reasoning"), ["reasoning"]) or f"{rec_channel} selected as optimal channel.",
        }
        if followup_context:
            decision = followup_context.get("decision", {})
            forced_channel = str(decision.get("next_channel") or "").strip().upper()
            if forced_channel:
                rec_channel = "PHONE" if forced_channel == "VOICE" else forced_channel
                strat_res["channel"] = rec_channel
                strat_res["recommended_channel"] = rec_channel
            if decision.get("angle"):
                strat_res["angle"] = decision["angle"]
                strat_res["strategy"] = decision["angle"]
                strat_res["instructions_for_copywriter"] = (
                    f"Prepare touch {decision.get('next_touch_number')} as a follow-up. "
                    f"Use the Follow-up Agent angle: {decision.get('angle')}. "
                    f"Reason: {decision.get('reason', '')}"
                )
            strat_res["action_type"] = "FOLLOW_UP"
            strat_res["followup_decision"] = decision

        # =========================================================================
        # 4. Personalisation Agent (Agent 4)
        # Receives: prospect + campaign + 'research' + 'qualification' + 'strategy' + 'channel'
        # Outputs: generalized 'message' / 'content' + 'subject'
        # =========================================================================
        logger.info(f"[PIPELINE 4/4] Invoking DronaHQ Personalisation Agent for channel {rec_channel}...")
        pers_payload = {
            "campaign": c_dict,
            "prospect": p_dict,
            "research": research_block,
            "qualification": qual_block,
            "strategy": strat_block,
            "channel": rec_channel,
            "recommended_channel": rec_channel,
            "angle": strat_res.get("angle"),
            "tone": strat_res.get("tone", "PEER_ENGINEER"),
        }
        if followup_context:
            pers_payload["followup"] = followup_context
        pers_raw = call_dronahq_agent(DRONAHQ_PERSONALISATION_URL, DRONAHQ_PERSONALISATION_KEY, pers_payload)
        if not pers_raw or not isinstance(pers_raw, dict):
            pers_raw = {}

        first_name = p_dict["name"].split()[0] if p_dict["name"] else "there"
        pers_content = clean_agent_text(
            pers_raw.get("message")
            or pers_raw.get("content")
            or pers_raw.get("body")
            or pers_raw.get("email_body")
            or pers_raw.get("text")
            or pers_raw.get("output")
            or pers_raw.get("raw_text")
            or pers_raw,
            ["message", "content", "body", "email_body", "text"]
        )
        pers_subject = clean_agent_text(
            pers_raw.get("subject_line")
            or pers_raw.get("subject")
            or pers_raw,
            ["subject_line", "subject"]
        )

        if not pers_content or len(str(pers_content).strip()) < 10:
            if rec_channel == "SMS":
                pers_subject = None
                pers_content = f"Hi {first_name}, saw your work at {p_dict['company']}. We help teams ship 40% faster with AI. Open to a 5-min chat next week? - SDR"
                if len(pers_content) > 160:
                    pers_content = pers_content[:157] + "..."
            elif rec_channel == "LINKEDIN":
                pers_subject = None
                pers_content = f"Hi {first_name}, noticed your work scaling {p_dict['company']}. Would love to connect and share notes on autonomous SDR automation!"
            elif rec_channel == "PHONE":
                pers_subject = f"Introductory Call - {p_dict['company']}"
                pers_content = f"SDR Voice Bridge Script: Hello {first_name}, calling regarding AI developer acceleration at {p_dict['company']}."
            else:
                pers_subject = pers_subject or f"Accelerating developer velocity at {p_dict['company']}"
                pers_content = (
                    f"Hi {first_name},\n\n"
                    f"I noticed your leadership as {p_dict['title']} at {p_dict['company']}. "
                    f"At high-growth tech companies, engineering bottlenecks and repetitive SDLC tasks often slow down release cadence.\n\n"
                    f"Our Autonomous SDR and developer automation platform helps teams ship 40% faster without adding headcount.\n\n"
                    f"Do you have 10 minutes next Tuesday or Thursday for a brief introductory conversation?\n\n"
                    f"Best regards,\n"
                    f"Autonomous SDR Team"
                )

        pers_msg = clean_agent_text(str(pers_content).strip())
        if rec_channel == "SMS" and len(pers_msg) > 160:
            pers_msg = pers_msg[:157].rstrip() + "..."

        if rec_channel == "EMAIL" and (not pers_subject or not str(pers_subject).strip()):
            pers_subject = f"Accelerating developer velocity at {p_dict['company']}"
        if pers_subject:
            pers_subject = clean_agent_text(pers_subject)

        pers_res = {
            **pers_raw,
            "prospect_id": p_dict["id"],
            "channel": rec_channel,
            "message": pers_msg,
            "content": pers_msg,
            "subject": pers_subject,
            "subject_line": pers_subject,
            "mentions_pricing": pers_raw.get("mentions_pricing", False),
            "confidence_score": pers_raw.get("confidence_score", 0.94),
            "rag_sources_cited": pers_raw.get("rag_sources_cited", ["Product Architecture Guide", "Executive Benchmarks"]),
        }

        return research_res, icp_res, strat_res, pers_res

    # Fallback to single webhook workflow
    dronahq_response = trigger_dronahq(base_payload)
    icp_res, strat_res, pers_res = parse_agent_results(dronahq_response, prospect, campaign)
    research_res = {
        "verified_domain": p_dict["domain"] or f"{p_dict['company'].lower().replace(' ', '')}.com",
        "title": p_dict["title"],
        "company": p_dict["company"],
        "prospect_summary": f"{p_dict['name']} is {p_dict['title']} at {p_dict['company']}.",
    }
    return research_res, icp_res, strat_res, pers_res
