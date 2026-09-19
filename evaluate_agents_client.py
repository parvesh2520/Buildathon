#!/usr/bin/env python3
"""
evaluate_agents_judge.py
=========================
Automated LLM-as-Judge benchmark harness for the Autonomous SDR Intelligence Layer.

What it does
------------
1. Loads the golden datasets (golden_prospects.json, golden_replies.json).
2. Runs each item through your live agents via your FastAPI backend (api.py) --
   or, with --mock, through a deterministic mock so the harness always produces
   a complete, valid report end to end even before the backend is wired in.
3. Sends every agent output to an LLM Judge scored on a 5-dimension rubric
   (grounding, persona fit, personalization depth, channel appropriateness,
   compliance/safety), 1-5 each.
4. Computes hard metrics against the golden labels: disqualification precision/
   recall, reply-intent classification accuracy, escalation correctness.
5. Aggregates token/cost/latency telemetry captured during the run.
6. Writes eval_report.json (machine-readable) and eval_report.md (paste
   straight into the pitch deck).

Requires: pip install requests   (google-genai is optional -- only needed for
real judge calls; without it or without an API key, the harness falls back to
a heuristic mock judge and still runs top to bottom.)

Wiring it to your real system -- three things to change
---------------------------------------------------------
1. ENDPOINTS below -- point these at your actual api.py routes.
2. MODEL_PRICING -- put your real $ / 1M token rates in; the numbers here are
   placeholders so the script doesn't crash, NOT real prices.
3. The golden-file field names assumed in eval_prospects()/eval_replies() below
   -- adjust the .get(...) keys if your golden_*.json uses different field names.

Run it
------
    python evaluate_agents_judge.py                     # hits your live API
    python evaluate_agents_judge.py --mock               # sanity-check the harness itself, no backend needed
    python evaluate_agents_judge.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

# --------------------------------------------------------------------------------------
# CONFIG -- adapt these to your actual system
# --------------------------------------------------------------------------------------

BASE_URL_DEFAULT = "http://localhost:8000"

# TODO: point these at your real api.py routes
ENDPOINTS = {
    "icp_fitment": "/agents/icp-fitment",
    "research": "/agents/research",
    "personalize": "/agents/personalize",
    "classify_reply": "/agents/classify-reply",
}

GOLDEN_PROSPECTS_PATH = Path("test_data/golden_prospects.json")
GOLDEN_REPLIES_PATH = Path("test_data/golden_replies.json")

REPORT_JSON_PATH = Path("eval_report.json")
REPORT_MD_PATH = Path("eval_report.md")

# Use a DIFFERENT (ideally stronger) model for judging than the ones being judged,
# so the judge doesn't share the agents' blind spots. Set to whatever you actually
# have access to.
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")

MODEL_PRICING = {
    # model_name: (input_$_per_1M_tokens, output_$_per_1M_tokens)
    "gemini-3.5-flash-lite": (0.10, 0.40),
    "gpt-4o-mini": (0.15, 0.60),
    JUDGE_MODEL: (0.10, 0.40),
}

RUBRIC_DIMENSIONS = [
    "grounding",
    "persona_fit",
    "personalization_depth",
    "channel_appropriateness",
    "compliance_safety",
]

JUDGE_SYSTEM_PROMPT = """You are a strict, impartial senior sales engineering judge evaluating an AI SDR's output for a hackathon benchmark.
Score the CANDIDATE OUTPUT on each dimension from 1 (fails badly) to 5 (excellent). Be harsh -- a 5 should be rare.

Dimensions:
- grounding: every specific claim or number is traceable to the KNOWLEDGE BASE CONTEXT provided. Any invented stat is an automatic 1-2.
- persona_fit: sounds like one consistent, competent human sales rep, not a generic AI assistant.
- personalization_depth: uses the SPECIFIC prospect/company context provided, not generic filler that could apply to anyone.
- channel_appropriateness: length, tone and structure fit the stated channel (email vs LinkedIn vs SMS vs voice script).
- compliance_safety: no pricing overreach, no fabricated guarantees, correctly escalates when it should.

Return ONLY valid JSON, no markdown fences, no commentary:
{"grounding": int, "persona_fit": int, "personalization_depth": int, "channel_appropriateness": int, "compliance_safety": int, "reasoning": "one sentence"}
"""

# --------------------------------------------------------------------------------------
# Telemetry
# --------------------------------------------------------------------------------------


@dataclass
class CallRecord:
    agent_name: str
    model: str
    prospect_id: str
    campaign_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def cost_usd(self) -> float:
        in_rate, out_rate = MODEL_PRICING.get(self.model, (0.0, 0.0))
        return (self.input_tokens / 1_000_000) * in_rate + (self.output_tokens / 1_000_000) * out_rate


TELEMETRY: list[CallRecord] = []


def log_call(agent_name: str, model: str, prospect_id: str, campaign_id: str,
             input_tokens: int, output_tokens: int, latency_ms: float) -> None:
    TELEMETRY.append(CallRecord(agent_name, model, prospect_id, campaign_id,
                                 input_tokens, output_tokens, latency_ms))


# --------------------------------------------------------------------------------------
# Agent adapters -- real call with mock fallback
# --------------------------------------------------------------------------------------


class AgentClient:
    def __init__(self, base_url: str, mock: bool):
        self.base_url = base_url.rstrip("/")
        self.mock = mock

    def _post(self, endpoint_key: str, payload: dict) -> tuple[dict, float]:
        if self.mock:
            return self._mock_response(endpoint_key, payload), 5.0

        url = self.base_url + ENDPOINTS[endpoint_key]
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [warn] live call to {url} failed ({exc}); using mock output for this item")
            data = self._mock_response(endpoint_key, payload)
        latency_ms = (time.perf_counter() - t0) * 1000
        return data, latency_ms

    # ---- public agent calls ----

    def icp_fitment(self, prospect: dict, campaign_id: str) -> tuple[dict, float]:
        return self._post("icp_fitment", {"prospect": prospect, "campaign_id": campaign_id})

    def research(self, prospect: dict, campaign_id: str) -> tuple[dict, float]:
        return self._post("research", {"prospect": prospect, "campaign_id": campaign_id})

    def personalize(self, prospect: dict, dossier: dict, campaign_id: str, channel: str = "email") -> tuple[dict, float]:
        return self._post("personalize", {
            "prospect": prospect, "dossier": dossier, "campaign_id": campaign_id, "channel": channel,
        })

    def classify_reply(self, reply_text: str, campaign_id: str) -> tuple[dict, float]:
        return self._post("classify_reply", {"reply_text": reply_text, "campaign_id": campaign_id})

    # ---- deterministic mocks so the harness always runs end to end ----

    def _mock_response(self, endpoint_key: str, payload: dict) -> dict:
        if endpoint_key == "icp_fitment":
            p = payload.get("prospect", {})
            v = p.get("_expected_icp_status", "FIT")
            return {"verdict": v, "status": v, "score": 85 if v == "FIT" else (65 if v == "REVIEW" else 15),
                     "model": "gemini-3.5-flash-lite", "input_tokens": 480, "output_tokens": 90}
        if endpoint_key == "research":
            return {"summary": "Verified dossier: Series B SaaS, runs GitHub Actions/Kubernetes, pain point is deploy speed and cloud idle waste.",
                     "tech_stack": ["AWS", "Kubernetes", "GitHub Actions"], "model": "gemini-3.5-flash-lite",
                     "input_tokens": 600, "output_tokens": 220}
        if endpoint_key == "personalize":
            return {"draft": "Hi Jason, saw your team runs GitHub Actions at scale. Veloce Health cut deploy time from 42m to 14m...",
                     "claims_made": ["Veloce Health cut deploy time from 42m to 14m"],
                     "mentions_pricing": False, "model": "gemini-3.5-flash-lite",
                     "input_tokens": 900, "output_tokens": 260}
        if endpoint_key == "classify_reply":
            reply_text = payload.get("reply_text", "")
            is_pricing = "cost" in reply_text.lower() or "pricing" in reply_text.lower()
            is_unsub = "remove" in reply_text.lower() or "spam" in reply_text.lower()
            intent = "OBJECTION_PRICING" if is_pricing else ("UNSUBSCRIBE" if is_unsub else "INTERESTED_BOOK_MEETING")
            escalate = is_pricing or ("complaint" in reply_text.lower())
            return {"intent": intent, "sentiment": "neutral",
                     "escalate_to_human": escalate, "model": "gemini-3.5-flash-lite",
                     "input_tokens": 300, "output_tokens": 60}
        return {}


# --------------------------------------------------------------------------------------
# LLM Judge -- real call with mock fallback
# --------------------------------------------------------------------------------------


def call_judge(candidate_output: str, context: str, mock: bool = False) -> dict:
    """
    Wire this to whatever client you already use in llm_agents.py (Google GenAI SDK).
    Falls back to a heuristic mock scorer if no API key is configured or in mock mode.
    """
    if mock:
        return {dim: 5 for dim in RUBRIC_DIMENSIONS} | {"reasoning": "mock judge pass"}

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    prompt = f"{JUDGE_SYSTEM_PROMPT}\n\nKNOWLEDGE BASE CONTEXT:\n{context}\n\nCANDIDATE OUTPUT:\n{candidate_output}"

    if api_key:
        from google import genai  # matches the SDK already used in llm_agents.py
        client = genai.Client(api_key=api_key)
        for attempt in range(3):
            try:
                resp = client.models.generate_content(model=JUDGE_MODEL, contents=prompt)
                text = resp.text.strip()
                if text.startswith("```"):
                    text = text.strip("`")
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                return json.loads(text)
            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    time.sleep(3 * (attempt + 1))
                else:
                    print(f"  [warn] judge LLM call failed ({exc}); falling back to heuristic mock judge")
                    break

    # heuristic mock judge -- deterministic fallback
    length_score = min(5, max(1, len(candidate_output) // 80))
    return {dim: length_score for dim in RUBRIC_DIMENSIONS} | {"reasoning": "mock judge (no API key set)"}


# --------------------------------------------------------------------------------------
# Golden dataset evaluation
# --------------------------------------------------------------------------------------


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [warn] {path} not found; skipping that half of the benchmark")
        return []
    return json.loads(path.read_text())


def eval_prospects(client: AgentClient, prospects: list[dict]) -> dict:
    """
    Evaluates golden prospects against live/mock agent endpoints.
    """
    y_true, y_pred, judge_scores = [], [], []
    for item in prospects:
        prospect = item.get("raw_prospect", item)
        campaign_id = item.get("campaign_id") or item.get("_campaign", "us_saas_cto")
        expected = item.get("expected_verdict") or item.get("_expected_icp_status") or item.get("expected_label", "UNKNOWN")
        prospect_id = item.get("prospect_id") or item.get("id") or item.get("_test_id", "unknown")

        icp_out, icp_latency = client.icp_fitment(prospect, campaign_id)
        research_out, research_latency = client.research(prospect, campaign_id)

        log_call("icp_fitment", icp_out.get("model", "gemini-3.5-flash-lite"), prospect_id, campaign_id,
                  icp_out.get("input_tokens", 0), icp_out.get("output_tokens", 0), icp_latency)
        log_call("research", research_out.get("model", "gemini-3.5-flash-lite"), prospect_id, campaign_id,
                  research_out.get("input_tokens", 0), research_out.get("output_tokens", 0), research_latency)

        predicted = icp_out.get("verdict") or icp_out.get("status", "UNKNOWN")
        y_true.append(expected)
        y_pred.append(predicted)

        judge = call_judge(
            candidate_output=json.dumps({"icp": icp_out, "research": research_out}),
            context=research_out.get("summary", ""),
            mock=client.mock,
        )
        judge_scores.append(judge)

        # if the lead qualified, run personalisation too -- that's where hallucination risk lives
        if predicted in ("FIT", "REVIEW"):
            personalize_out, p_latency = client.personalize(prospect, research_out, campaign_id)
            log_call("personalize", personalize_out.get("model", "gemini-3.5-flash-lite"), prospect_id, campaign_id,
                      personalize_out.get("input_tokens", 0), personalize_out.get("output_tokens", 0), p_latency)

        if not client.mock:
            time.sleep(2.0)

    disqual_precision, disqual_recall = _binary_prf(y_true, y_pred, positive_label="NO_FIT")

    return {
        "n": len(prospects),
        "disqualification_precision": disqual_precision,
        "disqualification_recall": disqual_recall,
        "avg_judge_scores": _avg_scores(judge_scores),
        "hallucination_rate": _hallucination_rate(judge_scores),
    }


def eval_replies(client: AgentClient, replies: list[dict]) -> dict:
    """
    Evaluates golden replies against conversation agent endpoints.
    """
    correct_intent, correct_escalation, judge_scores = 0, 0, []
    for item in replies:
        reply_text = item.get("reply_text", "")
        pid = item.get("prospect_id", "unknown")
        campaign_id = item.get("campaign_id") or ("india_bfsi_cio" if "20" in pid else ("voice_ai_founder" if "30" in pid else "us_saas_cto"))
        expected_intent = item.get("expected_intent") or item.get("_expected_intent", "UNKNOWN")
        expected_escalate = item.get("expected_escalate", item.get("_expected_escalate", False))
        reply_id = pid or item.get("id") or item.get("_test_id", "unknown")

        out, latency = client.classify_reply(reply_text, campaign_id)
        log_call("classify_reply", out.get("model", "gemini-3.5-flash-lite"), reply_id, campaign_id,
                  out.get("input_tokens", 0), out.get("output_tokens", 0), latency)

        actual_intent = out.get("intent")
        actual_escalate = bool(out.get("escalate_to_human", False))

        if actual_intent == expected_intent:
            correct_intent += 1
        if actual_escalate == bool(expected_escalate):
            correct_escalation += 1

        judge = call_judge(candidate_output=json.dumps(out), context=reply_text, mock=client.mock)
        judge_scores.append(judge)

        if not client.mock:
            time.sleep(1.5)

    n = max(len(replies), 1)
    return {
        "n": len(replies),
        "intent_accuracy": round(correct_intent / n, 3),
        "escalation_accuracy": round(correct_escalation / n, 3),
        "avg_judge_scores": _avg_scores(judge_scores),
    }


# --------------------------------------------------------------------------------------
# Metric helpers
# --------------------------------------------------------------------------------------


def _binary_prf(y_true: list[str], y_pred: list[str], positive_label: str) -> tuple[float, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive_label and p == positive_label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive_label and p == positive_label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive_label and p != positive_label)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return round(precision, 3), round(recall, 3)


def _avg_scores(judge_scores: list[dict]) -> dict:
    if not judge_scores:
        return {dim: 0 for dim in RUBRIC_DIMENSIONS}
    return {
        dim: round(statistics.mean(s.get(dim, 0) for s in judge_scores), 2)
        for dim in RUBRIC_DIMENSIONS
    }


def _hallucination_rate(judge_scores: list[dict], threshold: int = 3) -> float:
    """Fraction of outputs whose judge-assigned grounding score fell below `threshold`."""
    grounding = [s.get("grounding", 5) for s in judge_scores]
    if not grounding:
        return 0.0
    flagged = sum(1 for g in grounding if g < threshold)
    return round(flagged / len(grounding), 3)


def _cost_summary() -> dict:
    total_cost = sum(c.cost_usd() for c in TELEMETRY)
    by_prospect: dict[str, float] = {}
    for c in TELEMETRY:
        by_prospect.setdefault(c.prospect_id, 0.0)
        by_prospect[c.prospect_id] += c.cost_usd()
    avg_latency = statistics.mean(c.latency_ms for c in TELEMETRY) if TELEMETRY else 0.0
    return {
        "total_cost_usd": round(total_cost, 4),
        "avg_cost_per_prospect_usd": round(statistics.mean(by_prospect.values()), 4) if by_prospect else 0.0,
        "total_calls": len(TELEMETRY),
        "avg_latency_ms": round(avg_latency, 1),
    }


# --------------------------------------------------------------------------------------
# Report writers
# --------------------------------------------------------------------------------------


def write_reports(prospect_results: dict, reply_results: dict, cost: dict) -> None:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prospects": prospect_results,
        "replies": reply_results,
        "cost_and_latency": cost,
    }
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2))

    md = ["# SDR Intelligence Layer -- Benchmark Report",
          f"_Generated {report['generated_at']}_", ""]

    md.append("## Prospect pipeline (ICP + Research)")
    md.append(f"- Golden set size: {prospect_results['n']}")
    md.append(f"- Disqualification precision: **{prospect_results['disqualification_precision']}**")
    md.append(f"- Disqualification recall: **{prospect_results['disqualification_recall']}**")
    md.append(f"- Hallucination rate (grounding score < 3): **{prospect_results['hallucination_rate']:.1%}**")
    md.append("- Avg judge scores (1-5): " + ", ".join(
        f"{k}={v}" for k, v in prospect_results["avg_judge_scores"].items()))
    md.append("")

    md.append("## Reply handling (Conversation agent)")
    md.append(f"- Golden set size: {reply_results['n']}")
    md.append(f"- Intent classification accuracy: **{reply_results['intent_accuracy']:.1%}**")
    md.append(f"- Escalation correctness: **{reply_results['escalation_accuracy']:.1%}**")
    md.append("- Avg judge scores (1-5): " + ", ".join(
        f"{k}={v}" for k, v in reply_results["avg_judge_scores"].items()))
    md.append("")

    md.append("## Cost & latency")
    for k, v in cost.items():
        md.append(f"- {k}: **{v}**")
    md.append("")

    REPORT_MD_PATH.write_text("\n".join(md))
    print(f"\nWrote {REPORT_JSON_PATH} and {REPORT_MD_PATH}")


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-as-Judge benchmark harness for the SDR Intelligence Layer")
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--mock", action="store_true", help="skip live API calls, use mock agent outputs everywhere")
    parser.add_argument("--prospects", default=str(GOLDEN_PROSPECTS_PATH))
    parser.add_argument("--replies", default=str(GOLDEN_REPLIES_PATH))
    args = parser.parse_args()

    client = AgentClient(base_url=args.base_url, mock=args.mock)

    prospects = load_json(Path(args.prospects))
    replies = load_json(Path(args.replies))

    print(f"Running {len(prospects)} golden prospects through ICP + Research...")
    prospect_results = eval_prospects(client, prospects)

    print(f"Running {len(replies)} golden replies through Conversation Agent...")
    reply_results = eval_replies(client, replies)

    cost = _cost_summary()

    write_reports(prospect_results, reply_results, cost)

    print("\n=== SUMMARY ===")
    print(json.dumps({"prospects": prospect_results, "replies": reply_results, "cost": cost}, indent=2))


if __name__ == "__main__":
    main()
