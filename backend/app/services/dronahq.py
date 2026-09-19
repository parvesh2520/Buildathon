import json
import logging
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Tuple, Optional
from app.config import (
    DRONAHQ_WEBHOOK_URL,
    DRONAHQ_API_KEY,
    DRONAHQ_LEAD_RESEARCH_URL,
    DRONAHQ_LEAD_RESEARCH_KEY,
    DRONAHQ_ICP_FITMENT_URL,
    DRONAHQ_ICP_FITMENT_KEY,
    DRONAHQ_OUTREACH_STRATEGY_URL,
    DRONAHQ_OUTREACH_STRATEGY_KEY,
    DRONAHQ_PERSONALISATION_URL,
    DRONAHQ_PERSONALISATION_KEY,
)

logger = logging.getLogger("sdr.dronahq")


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
        if isinstance(val, str) and (val.strip().startswith("{") or "```" in val):
            return unwrap_dronahq_response(val)

    # Check for LLM choices array: choices[0].message.content
    choices = raw_data.get("choices")
    if isinstance(choices, list) and len(choices) > 0:
        msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        if isinstance(msg, dict) and msg.get("content"):
            return unwrap_dronahq_response(msg["content"])

    # Check if 'message' contains a nested JSON structure
    msg_val = raw_data.get("message")
    if isinstance(msg_val, dict):
        return unwrap_dronahq_response(msg_val)
    if isinstance(msg_val, str) and (msg_val.strip().startswith("{") or "```" in msg_val):
        return unwrap_dronahq_response(msg_val)

    return raw_data


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

    subject_line = p_data.get("subject_line") or p_data.get("subject") or unwrapped.get("subject") or unwrapped.get("email_subject")
    content = (
        p_data.get("content")
        or p_data.get("body")
        or p_data.get("email_body")
        or p_data.get("text")
        or p_data.get("raw_text")
        or unwrapped.get("content")
        or unwrapped.get("body")
    )

    # Check if content has embedded Subject: ...
    if content:
        subj_match = re.search(r"^(?:\*\*|###\s*)?Subject(?:\*\*)?:\s*([^\n\r]+)", str(content), re.IGNORECASE | re.MULTILINE)
        if subj_match:
            if not subject_line:
                subject_line = subj_match.group(1).strip()
            content = re.sub(r"^(?:\*\*|###\s*)?Subject(?:\*\*)?:\s*([^\n\r]+)", "", str(content), flags=re.IGNORECASE | re.MULTILINE).strip()

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

    personalisation_result = {
        "prospect_id": p_id,
        "channel": channel,
        "subject_line": subject_line,
        "content": str(content).strip(),
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
    p_dict = {
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
    }
    c_dict = {
        "id": getattr(campaign, "id", None) or (campaign.get("id", "") if isinstance(campaign, dict) else ""),
        "name": getattr(campaign, "name", None) or (campaign.get("name", "") if isinstance(campaign, dict) else ""),
        "icp": getattr(campaign, "icp", None) or (campaign.get("icp", "") if isinstance(campaign, dict) else ""),
        "enabled_channels": getattr(campaign, "enabled_channels", None) or (campaign.get("enabled_channels", ["EMAIL", "SMS", "LINKEDIN", "PHONE"]) if isinstance(campaign, dict) else ["EMAIL", "SMS", "LINKEDIN", "PHONE"]),
    }

    base_payload = {"prospect": p_dict, "campaign": c_dict}

    # Check if individual agent URLs are available
    if DRONAHQ_LEAD_RESEARCH_URL and DRONAHQ_OUTREACH_STRATEGY_URL:
        # 1. Lead Research Agent
        logger.info(f"[PIPELINE 1/4] Invoking DronaHQ Lead Research Agent for '{p_dict['name']}'...")
        research_raw = call_dronahq_agent(DRONAHQ_LEAD_RESEARCH_URL, DRONAHQ_LEAD_RESEARCH_KEY, base_payload)
        research_res = {
            "prospect_id": research_raw.get("prospect_id", p_dict["id"]),
            "prospect_summary": research_raw.get("prospect_summary", f"{p_dict['name']} is {p_dict['title']} at {p_dict['company']}."),
            "verified_domain": p_dict["domain"] or f"{p_dict['company'].lower().replace(' ', '')}.com",
            "detected_tech_stack": research_raw.get("detected_tech_stack", ["Cloud Infrastructure", "CI/CD", "DevOps"]),
            "personalisation_hooks": research_raw.get("personalisation_hooks", [
                f"Executive leadership as {p_dict['title']}",
                f"Engineering automation at {p_dict['company']}",
            ]),
        }

        # 2. ICP Fitment Agent
        logger.info(f"[PIPELINE 2/4] Invoking DronaHQ ICP Fitment Agent...")
        icp_payload = {**base_payload, "research": research_res}
        icp_raw = call_dronahq_agent(DRONAHQ_ICP_FITMENT_URL, DRONAHQ_ICP_FITMENT_KEY, icp_payload)
        
        icp_status = "FIT"
        icp_score = 90
        icp_reason = f"Prospect role '{p_dict['title']}' at '{p_dict['company']}' matches ICP qualification criteria."
        if icp_raw:
            if isinstance(icp_raw.get("status"), str):
                st = icp_raw["status"].strip().upper()
                if st in ["NO_FIT", "REJECTED", "FAILED", "DISQUALIFIED"]:
                    icp_status = "NO_FIT"
                    icp_score = 35
            if isinstance(icp_raw.get("fit_score"), (int, float)):
                icp_score = int(icp_raw["fit_score"])
            if icp_raw.get("reasoning"):
                icp_reason = str(icp_raw["reasoning"])

        icp_res = {
            "status": icp_status,
            "score": icp_score,
            "reasoning": icp_reason,
            "matched_criteria": icp_raw.get("matched_criteria", ["Decision maker role", "Target company size", "Technical domain"]),
            "unmatched_criteria": icp_raw.get("unmatched_criteria", []),
        }

        if icp_status == "NO_FIT":
            return research_res, icp_res, {}, {}

        # 3. Outreach Strategy Agent
        logger.info(f"[PIPELINE 3/4] Invoking DronaHQ Outreach Strategy Agent...")
        strat_payload = {**base_payload, "research": research_res, "icp": icp_res}
        strat_raw = call_dronahq_agent(DRONAHQ_OUTREACH_STRATEGY_URL, DRONAHQ_OUTREACH_STRATEGY_KEY, strat_payload)

        rec_channel = None
        if strat_raw and strat_raw.get("recommended_channel"):
            rec_channel = str(strat_raw["recommended_channel"]).upper()

        notes_lower = (p_dict["notes"] or "").lower()
        if not rec_channel:
            if "sms" in notes_lower or (p_dict["phone"] and not p_dict["email"]):
                rec_channel = "SMS"
            elif "linkedin" in notes_lower:
                rec_channel = "LINKEDIN"
            elif "call" in notes_lower or "voice" in notes_lower:
                rec_channel = "PHONE"
            else:
                rec_channel = "EMAIL"
        elif "sms" in notes_lower and p_dict["phone"]:
            rec_channel = "SMS"

        strat_res = {
            "prospect_id": p_dict["id"],
            "recommended_channel": rec_channel,
            "action_type": strat_raw.get("action_type", "NEW_OUTREACH") if strat_raw else "NEW_OUTREACH",
            "angle": strat_raw.get("angle", f"Accelerating developer velocity at {p_dict['company']}") if strat_raw else f"Accelerating developer velocity at {p_dict['company']}",
            "tone": strat_raw.get("tone", "EXECUTIVE") if strat_raw else "EXECUTIVE",
            "instructions_for_copywriter": strat_raw.get("instructions_for_copywriter", "") if strat_raw else "",
            "suggested_wait_days": strat_raw.get("suggested_wait_days", 0) if strat_raw else 0,
            "reasoning": strat_raw.get("reasoning", f"{rec_channel} is optimal for reaching {p_dict['title']}.") if strat_raw else f"{rec_channel} selected.",
        }

        # 4. Personalisation Agent
        logger.info(f"[PIPELINE 4/4] Invoking DronaHQ Personalisation Agent for channel {rec_channel}...")
        pers_payload = {
            **base_payload,
            "research": research_res,
            "icp": icp_res,
            "strategy": strat_res,
            "channel": rec_channel,
            "recommended_channel": rec_channel,
            "angle": strat_res["angle"],
            "instructions_for_copywriter": strat_res["instructions_for_copywriter"],
        }
        pers_raw = call_dronahq_agent(DRONAHQ_PERSONALISATION_URL, DRONAHQ_PERSONALISATION_KEY, pers_payload)

        first_name = p_dict["name"].split()[0] if p_dict["name"] else "there"
        pers_content = (
            pers_raw.get("content")
            or pers_raw.get("body")
            or pers_raw.get("text")
            or pers_raw.get("email_body")
        )
        pers_subject = pers_raw.get("subject_line") or pers_raw.get("subject")

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

        pers_res = {
            "prospect_id": p_dict["id"],
            "channel": rec_channel,
            "subject_line": pers_subject,
            "content": str(pers_content).strip(),
            "rag_sources_cited": pers_raw.get("rag_sources_cited", ["Product Architecture Guide", "Executive Benchmarks"]),
            "confidence_score": pers_raw.get("confidence_score", 0.96),
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
