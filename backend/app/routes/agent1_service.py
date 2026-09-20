"""
Lead Research & Enrichment Engine (Agent 1)
Autonomous enterprise SDR lead research and 6-pillar enrichment service.
Supports standalone HTTP invocation, DronaHQ ActionFlow compatibility,
and internal orchestrator chaining.
"""

import json
import logging
import re
import urllib.request
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException
from app.config import GROQ_API_KEY

logger = logging.getLogger("sdr.agent1")
router = APIRouter(prefix="/api/agents", tags=["Agent 1: Lead Research"])

AGENT1_SYSTEM_PROMPT = """You are the Lead Research & Enrichment Engine inside an autonomous enterprise SDR platform.

### MISSION & OPERATIONAL CONTEXT
You do not simply collect high-level trivia or unverified snippets. You build a continuously updated, evidence-backed, reusable Prospect Intelligence Profile spanning person, company, business situation, and relationship history.

Your intelligence serves as the foundation for downstream agents:
- ICP Fitment Agent: Uses company metrics, firmographics, exclusions, and growth data for qualification.
- Outreach Strategy Agent: Uses timing signals, relationship history, and executive priorities to determine channels, angles, and cadences.
- Personalisation Agent: Uses verified facts, technical initiatives, and pain points to craft authentic outreach.
- Conversation & Voice Agents: Uses tech stack details, competitive landscape, and strategic challenges for live objection handling and call briefings.

You are campaign-agnostic by design. The campaign and research brief tell you what to prioritize, not what you are capable of investigating.

### CORE 6-PILLAR TAXONOMY:
- Pillar A: Company Intelligence (firmographics, recent developments, growth velocity, core tech stack, cloud infrastructure)
- Pillar B: Person & Leadership Intelligence (identity, authority, career pedigree, public footprint, interests, transitions)
- Pillar C: Business & Strategic Context (observed fact -> evidence-backed interpretation -> potential operational relevance)
- Pillar D: Buying & Intent Signals (buying intent, pain signals, competitive signals, timing signals with recency)
- Pillar E: Relationship & Interaction Context (stage: NEW_PROSPECT, interaction history)
- Pillar F: Evidence, Verification & Confidence (VERIFIED, LIKELY, UNVERIFIED, CONFLICTING, or NOT_FOUND)

### OUTPUT RULE — ABSOLUTE ZERO FLUFF
- Your entire response MUST start with { and end with }.
- Do NOT write "Here is the dossier", "Sure!", or any greeting.
- Do NOT write markdown code blocks (no ```json or ```).
- Do NOT write closing thoughts or commentary.
- Emit ONLY the raw JSON string matching the exact schema below:

{
  "prospect_id": "string",
  "identity": {
    "person_name": "string",
    "job_title": "string",
    "seniority": "string",
    "department": "string",
    "company_name": "string",
    "location": "string"
  },
  "company_intelligence": {
    "profile": {
      "website": "string",
      "industry": "string",
      "sub_industry": "string",
      "business_model": "string",
      "company_size": "string",
      "revenue_range": "string or null",
      "headquarters": "string",
      "operating_geographies": ["string"],
      "funding_stage": "string",
      "total_funding": "string or null",
      "key_investors": ["string"]
    },
    "recent_developments": [
      {
        "event": "string",
        "type": "funding | product_launch | expansion | partnership | leadership | acquisition",
        "date": "string",
        "source": "string"
      }
    ],
    "growth_signals": [
      {
        "signal": "string",
        "metric": "string or null",
        "source": "string"
      }
    ],
    "technology": {
      "detected_tech_stack": ["string"],
      "recent_technology_adoption": ["string"],
      "cloud_infrastructure": ["string"],
      "competitor_technology_used": ["string"]
    }
  },
  "person_intelligence": {
    "tenure_in_role": "string or null",
    "areas_of_responsibility": ["string"],
    "career_background": ["string"],
    "public_activity": [
      {
        "activity": "string",
        "channel": "linkedin | podcast | article | conference | interview",
        "date": "string or null",
        "source": "string"
      }
    ],
    "interests_and_expertise": ["string"],
    "recent_changes": ["string"]
  },
  "strategic_context": {
    "current_priorities": ["string"],
    "observed_challenges": ["string"],
    "causal_implications": [
      {
        "observed_fact": "string",
        "evidence_backed_interpretation": "string",
        "potential_relevance": "string"
      }
    ]
  },
  "signals": {
    "buying_intent": [
      {
        "signal": "string",
        "date": "string",
        "source": "string",
        "confidence": "HIGH | MEDIUM | LOW",
        "relevance": "HIGH | MEDIUM | LOW"
      }
    ],
    "pain_signals": [
      {
        "signal": "string",
        "date": "string",
        "source": "string",
        "confidence": "HIGH | MEDIUM | LOW",
        "relevance": "HIGH | MEDIUM | LOW"
      }
    ],
    "competitive_signals": [
      {
        "signal": "string",
        "date": "string",
        "source": "string",
        "confidence": "HIGH | MEDIUM | LOW",
        "relevance": "HIGH | MEDIUM | LOW"
      }
    ],
    "timing_signals": [
      {
        "signal": "string",
        "date": "string",
        "source": "string",
        "confidence": "HIGH | MEDIUM | LOW",
        "relevance": "HIGH | MEDIUM | LOW"
      }
    ]
  },
  "relationship_context": {
    "relationship_stage": "NEW_PROSPECT",
    "existing_customer": false,
    "previous_outreach_history": [],
    "last_interaction": null
  },
  "research_summary": {
    "key_findings": ["string"],
    "potential_relevance": "string",
    "important_unknowns": ["string"],
    "conflicting_information": ["string"]
  },
  "evidence_and_confidence": {
    "confidence_rating": "HIGH | MEDIUM | LOW",
    "verification_status": "VERIFIED | LIKELY | UNVERIFIED | CONFLICTING | NOT_FOUND",
    "evidence_log": [
      {
        "finding": "string",
        "source": "string",
        "date": "string",
        "confidence": "HIGH | MEDIUM | LOW",
        "relevance": "HIGH | MEDIUM | LOW",
        "why": "string"
      }
    ]
  }
}"""


def resolve_prospect_input(payload: Any) -> Dict[str, Any]:
    """
    Implements the Input Ingestion Contract:
    1. Single Prospect Object (Standard / ActionFlow loop)
    2. Plain text direct format
    3. Upstream Agent 0 Multi-Prospect Output (shortlisted_prospects)
    """
    if isinstance(payload, str):
        return {
            "name": payload,
            "company": "Target Account",
            "title": "Decision Maker",
            "raw_text": payload,
        }

    if not isinstance(payload, dict):
        return {"name": "Prospect", "company": "Company"}

    # Format 3: Upstream Agent 0 Output with shortlisted_prospects
    shortlisted = payload.get("shortlisted_prospects") or payload.get("discovered_prospects")
    if isinstance(shortlisted, list) and len(shortlisted) > 0:
        target_id = payload.get("target_prospect_id")
        target_idx = payload.get("target_index")

        candidate = None
        if target_id is not None:
            for item in shortlisted:
                if str(item.get("prospect_id")) == str(target_id) or str(item.get("id")) == str(target_id):
                    candidate = item
                    break

        if not candidate and target_idx is not None:
            try:
                idx = int(target_idx)
                if 0 <= idx < len(shortlisted):
                    candidate = shortlisted[idx]
            except Exception:
                pass

        # Default fallback to top candidate
        if not candidate:
            candidate = shortlisted[0]

        return {
            "id": candidate.get("prospect_id") or candidate.get("id"),
            "name": candidate.get("person_name") or candidate.get("name"),
            "title": candidate.get("job_title") or candidate.get("title"),
            "company": candidate.get("company_name") or candidate.get("company"),
            "website": candidate.get("website") or candidate.get("domain"),
            "domain": candidate.get("website") or candidate.get("domain"),
            "location": candidate.get("location"),
            "linkedin_url": candidate.get("source_url") or candidate.get("source") or candidate.get("linkedin_url"),
            "industry": candidate.get("industry"),
            "notes": candidate.get("sourcing_rationale"),
            "campaign": payload.get("campaign") or {},
        }

    # Format 1: Single Prospect Object
    prospect = payload.get("prospect") if isinstance(payload.get("prospect"), dict) else payload
    campaign = payload.get("campaign") if isinstance(payload.get("campaign"), dict) else {}

    return {
        "id": prospect.get("id") or prospect.get("prospect_id") or "lead_01",
        "name": prospect.get("person_name") or prospect.get("name") or "Executive",
        "title": prospect.get("job_title") or prospect.get("title") or "Leader",
        "company": prospect.get("company_name") or prospect.get("company") or "Company",
        "website": prospect.get("website") or prospect.get("domain") or "",
        "domain": prospect.get("website") or prospect.get("domain") or "",
        "location": prospect.get("location") or "",
        "linkedin_url": prospect.get("source_url") or prospect.get("source") or prospect.get("linkedin_url") or "",
        "industry": prospect.get("industry") or "",
        "notes": prospect.get("sourcing_rationale") or prospect.get("notes") or "",
        "campaign": campaign,
    }


def execute_lead_research(payload: Any, timeout: int = 35) -> Dict[str, Any]:
    """
    Executes deep 6-pillar lead research on the prospect using Groq Cloud LLM.
    Returns the exact Prospect Intelligence Profile matching the user's required schema,
    plus extracted summary blocks for downstream agent consumption.
    """
    from app.config import GROQ_API_KEY
    if not GROQ_API_KEY:
        logger.warning("[AGENT 1] GROQ_API_KEY not configured!")
        return {}

    target = resolve_prospect_input(payload)
    camp = target.get("campaign") or {}

    user_query = f"""Execute full 6-pillar Prospect Intelligence Profile research:
Target Person: {target.get('name')}
Job Title: {target.get('title')}
Company: {target.get('company')}
Website / Domain: {target.get('domain') or target.get('website')}
LinkedIn: {target.get('linkedin_url')}
Location: {target.get('location')}
Campaign Context: {camp.get('name', 'B2B Enterprise Outreach')}
Target ICP: {camp.get('icp', 'Enterprise Technology Decision Makers')}
Additional Notes: {target.get('notes')}

CRITICAL: Keep descriptions concise (1-2 sentences per item) and limit each array to 1-2 key items so the entire JSON is compact.
"""

    models_to_try = ["groq/compound-mini", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
    last_err = None

    for model_name in models_to_try:
        req_body = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": AGENT1_SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.1,
            "max_tokens": 950,
        }

        try:
            req = urllib.request.Request(
                url="https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(req_body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "AutonomousSDR-Agent1/2.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_content = data["choices"][0]["message"]["content"].strip()

                # Clean markdown JSON fences if present
                cleaned = raw_content
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                profile = json.loads(cleaned)
                break
        except Exception as e:
            last_err = e
            logger.warning(f"[AGENT 1 RETRY] Model {model_name} failed: {e}. Trying next model...")
            profile = None

    if not profile:
        logger.error(f"[AGENT 1 FAILED] All models failed. Last error: {last_err}")
        return {
            "success": False,
            "error": str(last_err),
            "research": f"{target.get('name')} is {target.get('title')} at {target.get('company')}.",
            "prospect_summary": f"{target.get('name')} is {target.get('title')} at {target.get('company')}.",
        }

    # Build unified 'research' dossier block for downstream SDR agents
    key_findings = profile.get("research_summary", {}).get("key_findings", [])
    findings_text = " ".join(key_findings) if isinstance(key_findings, list) else str(key_findings)
    relevance = profile.get("research_summary", {}).get("potential_relevance", "")

    tech_list = profile.get("company_intelligence", {}).get("technology", {}).get("detected_tech_stack", [])
    tech_text = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)

    causal = profile.get("strategic_context", {}).get("causal_implications", [])
    causal_text = ""
    if isinstance(causal, list) and len(causal) > 0:
        first_c = causal[0]
        if isinstance(first_c, dict):
            causal_text = f"Priority: {first_c.get('observed_fact', '')} -> {first_c.get('potential_relevance', '')}"

    research_narrative = (
        f"{target.get('name')} is {target.get('title')} at {target.get('company')}. "
        f"{findings_text} "
        f"{f'Tech Stack includes: {tech_text}. ' if tech_text else ''}"
        f"{causal_text} "
        f"{relevance}"
    ).strip()

    # Merge with top-level helper fields for backward compatibility
    profile["research"] = research_narrative
    profile["prospect_summary"] = research_narrative
    profile["summary"] = research_narrative
    profile["detected_tech_stack"] = tech_list
    profile["personalisation_hooks"] = [
        s.get("signal", "") for s in profile.get("signals", {}).get("timing_signals", []) if isinstance(s, dict)
    ] or key_findings[:2]

    logger.info(f"[AGENT 1] Successfully generated 6-pillar intelligence profile for '{target.get('name')}'")
    return profile


@router.post("/lead-research")
async def lead_research_webhook(request: Request):
    """
    Exposes Agent 1 (Lead Research & Enrichment Engine) as a dedicated REST endpoint.
    Accepts:
    1. Single prospect payload: { person_name, job_title, company_name, website, location }
    2. Agent 0 payload: { shortlisted_prospects: [...], target_prospect_id: "..." }
    3. Standard { campaign: {...}, prospect: {...} }
    Returns: Complete 6-pillar Prospect Intelligence Profile.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = execute_lead_research(body)
    if not result:
        raise HTTPException(status_code=500, detail="Lead research failed to execute")
    return result
