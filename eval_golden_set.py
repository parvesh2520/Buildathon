#!/usr/bin/env python3
"""
Golden-Set Evaluation Harness — ReplyClassification
Inter Guild Buildathon 2026 (Tech Contingent IIT Madras x DronaHQ)

Your 50 pytest cases check that guardrails/core.py behaves correctly (code logic).
This script checks something different: whether your LLM actually classifies
real prospect replies correctly against 10 hand-labeled ground-truth cases.

WIRE-UP (do this first):
    Edit the `classify()` function below to call your real pipeline —
    either import your classification function directly, or hit your
    running FastAPI server. Two options are sketched inside the docstring.

RUN:
    python eval_golden_set.py
    python eval_golden_set.py --save-report report.json
"""

import argparse
import json
import sys
import time
from collections import defaultdict

# --------------------------------------------------------------------------
# 1. GOLDEN SET — hand-labeled ground truth
def load_golden_set(path="test_data/golden_replies.json"):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [
        {
            "prospect_id": c["prospect_id"],
            "reply_text": c["reply_text"],
            "expected_intent": c.get("_expected_intent") or c.get("expected_intent"),
            "expected_escalate": c.get("_expected_escalate") if "_expected_escalate" in c else c.get("expected_escalate", False)
        }
        for c in raw
    ]

GOLDEN_SET = load_golden_set()


VALID_INTENTS = {
    "INTERESTED_BOOK_MEETING", "TECHNICAL_QUESTION", "OBJECTION_PRICING",
    "OBJECTION_COMPETITOR", "OBJECTION_NO_TIME", "NOT_INTERESTED",
    "OUT_OF_OFFICE", "UNSUBSCRIBE",
}
VALID_SENTIMENTS = {"POSITIVE", "NEUTRAL", "NEGATIVE"}


# --------------------------------------------------------------------------
# 2. ADAPTER — wire this to YOUR pipeline
# --------------------------------------------------------------------------
def classify(prospect_id: str, reply_text: str) -> dict:
    from api import pipeline
    result = pipeline.run_conversation_classifier(
        prospect_id=prospect_id,
        reply_text=reply_text,
        campaign_id="us_saas_cto"
    )
    return result if isinstance(result, dict) else result.model_dump()



# --------------------------------------------------------------------------
# 3. EVAL LOOP
# --------------------------------------------------------------------------
def validate_schema(pred: dict) -> list:
    """Return a list of schema violations (empty list = valid)."""
    errors = []
    if pred.get("intent") not in VALID_INTENTS:
        errors.append(f"invalid intent: {pred.get('intent')!r}")
    if pred.get("sentiment") not in VALID_SENTIMENTS:
        errors.append(f"invalid sentiment: {pred.get('sentiment')!r}")
    if not isinstance(pred.get("escalate_to_human"), bool):
        errors.append(f"escalate_to_human not bool: {pred.get('escalate_to_human')!r}")
    if not isinstance(pred.get("extracted_notes"), str):
        errors.append("extracted_notes missing or not str")
    return errors


def run_eval(save_report: str = None):
    results = []
    intent_correct = 0
    escalate_correct = 0
    escalate_false_negatives = []   # should have escalated, didn't -> highest-risk failure
    escalate_false_positives = []
    latencies = []

    print(f"Running {len(GOLDEN_SET)} golden-set cases...\n")

    for i, case in enumerate(GOLDEN_SET, 1):
        t0 = time.time()
        try:
            pred = classify(case["prospect_id"], case["reply_text"])
        except NotImplementedError as e:
            print(e)
            sys.exit(1)
        except Exception as e:
            print(f"[{i}] {case['prospect_id']}: classify() raised {type(e).__name__}: {e}")
            results.append({**case, "predicted": None, "error": str(e)})
            continue
        latency = time.time() - t0
        latencies.append(latency)

        schema_errors = validate_schema(pred)
        intent_ok = pred.get("intent") == case["expected_intent"]
        escalate_ok = pred.get("escalate_to_human") == case["expected_escalate"]

        if intent_ok:
            intent_correct += 1
        if escalate_ok:
            escalate_correct += 1
        elif case["expected_escalate"] and not pred.get("escalate_to_human"):
            escalate_false_negatives.append(case["prospect_id"])
        elif not case["expected_escalate"] and pred.get("escalate_to_human"):
            escalate_false_positives.append(case["prospect_id"])

        status = "PASS" if (intent_ok and escalate_ok and not schema_errors) else "FAIL"
        print(f"[{i}] {status}  {case['prospect_id']:8s}  "
              f"expected={case['expected_intent']:28s} got={pred.get('intent', 'N/A')}"
              f"{'  (schema errors: ' + '; '.join(schema_errors) + ')' if schema_errors else ''}")

        results.append({
            **case, "predicted": pred, "intent_ok": intent_ok,
            "escalate_ok": escalate_ok, "schema_errors": schema_errors,
            "latency_s": round(latency, 2),
        })

    n = len(GOLDEN_SET)
    print("\n" + "=" * 60)
    print(f"Intent accuracy:     {intent_correct}/{n}  ({100*intent_correct/n:.0f}%)")
    print(f"Escalation accuracy: {escalate_correct}/{n}  ({100*escalate_correct/n:.0f}%)")
    if latencies:
        print(f"Avg latency:         {sum(latencies)/len(latencies):.2f}s/case")

    if escalate_false_negatives:
        print(f"\n[!] MISSED ESCALATIONS (highest-risk failure -- angry/urgent replies "
              f"that went un-escalated): {escalate_false_negatives}")
    if escalate_false_positives:
        print(f"[i] Over-escalations (safe but noisy): {escalate_false_positives}")

    misses = [r for r in results if not r.get("intent_ok", False)]
    if misses:
        print("\nIntent misses:")
        for r in misses:
            got = r.get("predicted", {}).get("intent") if r.get("predicted") else "ERROR"
            print(f"  {r['prospect_id']}: expected {r['expected_intent']!r}, got {got!r}")

    if save_report:
        with open(save_report, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nFull report saved to {save_report}")

    # Non-zero exit code so this can slot into prepush_check.py / CI
    if intent_correct < n or escalate_correct < n or escalate_false_negatives:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-report", default=None, help="Path to save a JSON report")
    args = parser.parse_args()
    run_eval(save_report=args.save_report)
