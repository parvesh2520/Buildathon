"""
intent_eval.py - measure the reply-intent classifier against the golden set and show WHERE it fails.

Usage
-----
    python intent_eval.py --golden test_data/golden_replies.json \
                          --classifier api:classify_reply --threshold 0.90

`--classifier module:function` must point at a callable `f(text: str) -> str | dict`.
If it returns a dict, `primary_intent` (or `intent`) is used. Return the SAME label strings the
golden file uses; if your enum differs, pass --map old=new (repeatable), e.g. --map pricing=pricing_inquiry.

The golden file may be a list of cases, or a dict containing a list (e.g. {"replies": [...]}).
Text/label keys are auto-detected (see TEXT_KEYS / LABEL_KEYS). Exit status is 1 if accuracy < threshold,
so this can gate CI or a pre-push hook.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import Counter, defaultdict

TEXT_KEYS = ("reply_text", "reply", "text", "message", "body", "inbound", "prospect_reply", "input")
LABEL_KEYS = ("_expected_intent", "expected_intent", "intent", "label", "expected", "gold", "expected_label", "ground_truth")


def load_cases(path: str) -> list[tuple[str, str]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    cases = []
    for i, row in enumerate(data):
        text = next((row[k] for k in TEXT_KEYS if k in row), None)
        label = next((row[k] for k in LABEL_KEYS if k in row), None)
        if text is None or label is None:
            raise SystemExit(f"row {i}: could not find text/label keys in {list(row)}; edit TEXT_KEYS/LABEL_KEYS")
        cases.append((str(text), str(label)))
    return cases


def resolve(spec: str):
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn)


def report(golds: list[str], preds: list[str], texts: list[str], threshold: float) -> int:
    n = len(golds)
    correct = sum(g == p for g, p in zip(golds, preds))
    acc = correct / n if n else 0.0
    labels = sorted(set(golds) | set(preds))
    print(f"\nAccuracy: {correct}/{n} = {acc:.1%}   (threshold {threshold:.0%})\n")

    print(f"{'label':22}{'support':>8}{'precision':>11}{'recall':>9}{'f1':>7}")
    for lab in labels:
        tp = sum(g == lab and p == lab for g, p in zip(golds, preds))
        fp = sum(g != lab and p == lab for g, p in zip(golds, preds))
        fn = sum(g == lab and p != lab for g, p in zip(golds, preds))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        print(f"{lab:22}{tp + fn:>8}{prec:>11.2f}{rec:>9.2f}{f1:>7.2f}")

    conf: dict[str, Counter] = defaultdict(Counter)
    for g, p in zip(golds, preds):
        if g != p:
            conf[g][p] += 1
    if conf:
        print("\nMost common confusions (gold -> predicted):")
        pairs = sorted(((c, g, p) for g, row in conf.items() for p, c in row.items()), reverse=True)
        for c, g, p in pairs[:10]:
            print(f"  {c:>3} x  {g}  ->  {p}")
        print("\nMisses:")
        for t, g, p in zip(texts, golds, preds):
            if g != p:
                print(f"  gold={g:<20} pred={p:<20} | {t[:90]!r}")
    return 0 if acc >= threshold else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--classifier", required=True, help="module:function")
    ap.add_argument("--threshold", type=float, default=0.90)
    ap.add_argument("--map", action="append", default=[], help="rename predicted labels: old=new")
    args = ap.parse_args()

    remap = dict(m.split("=", 1) for m in args.map)
    clf = resolve(args.classifier)
    cases = load_cases(args.golden)
    texts, golds, preds = [], [], []
    for text, gold in cases:
        try:
            out = clf(text)
        except Exception as exc:  # a crash is a miss, not a stop
            out = f"ERROR:{type(exc).__name__}"
        if isinstance(out, dict):
            out = out.get("primary_intent") or out.get("intent") or "MISSING"
        texts.append(text); golds.append(gold); preds.append(remap.get(str(out), str(out)))
    return report(golds, preds, texts, args.threshold)


if __name__ == "__main__":
    sys.exit(main())
