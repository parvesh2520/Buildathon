"""
numeric_grounding_checker.py
==============================
Deterministic, regex-based grounding checker for the SDR Personalisation Agent.

This complements -- does not replace -- your existing GroundingChecker.claims_made
verification and the LLM Judge's "grounding" score. It's a second, free, always-on
line of defense against the exact failure mode judges will probe for: a rogue number
in the draft that doesn't appear anywhere in the campaign knowledge base
(e.g. "saved 90%" when the KB actually says "saved 66%"). A claims_made-list check
alone can miss this if the model lists the right claim *text* but the number inside
it has drifted -- this catches that specific case cheaply, with zero LLM calls.

Wire it in
----------
In guardrails/grounding_policy.py, call verify_numeric_claims(draft.content, kb_text)
alongside your existing claims_made check, and fold `result.ok` into PolicyGate's
ungrounded-claim condition (HELD_APPROVAL / trigger the self-healing regenerate loop
when ok is False).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Matches: $138k, $1.2M, $45,000  |  INR 3,200 Cr, ₹500, Rs 250  |  84%, 99.9%  |  42 minutes, 14m, 420ms, 72h, 3 days
NUMERIC_CLAIM_PATTERN = re.compile(
    r"""
    (?:\$\s?\d[\d,]*\.?\d*\s?[kKmMbB]?)
    |
    (?:(?:INR|₹|Rs\.?)\s?\d[\d,]*\.?\d*\s?(?:Cr|Lakhs?|L|crore|lakh)?)
    |
    (?:\d[\d,]*\.?\d*\s?%)
    |
    (?:\d[\d,]*\.?\d*\s?(?:ms|milliseconds?|mins?|minutes?|hrs?|hours?|days?|secs?|seconds?))
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize(token: str) -> str:
    """Strip whitespace/commas and lowercase, so '1,200' / '1200' / '1 200' all compare equal."""
    return re.sub(r"[\s,]", "", token).lower()


@dataclass
class NumericGroundingResult:
    ok: bool
    claimed_numbers: list[str] = field(default_factory=list)
    ungrounded_numbers: list[str] = field(default_factory=list)


def verify_numeric_claims(draft_text: str, kb_text: str) -> NumericGroundingResult:
    """
    Extracts every $-amount, percentage, and time-duration in draft_text and checks
    each one appears (normalized) somewhere in kb_text. Anything in the draft that
    isn't in the KB is flagged as a fabricated/drifted number.

    Note: this is a substring check on normalized text, not semantic matching -- it
    will not catch a number that's technically present in the KB but misapplied to
    the wrong fact (e.g. reusing campaign A's $138k for campaign B's case study).
    Pair it with your claims_made / campaign-isolation checks for that case.
    """
    claimed = [_normalize(m) for m in NUMERIC_CLAIM_PATTERN.findall(draft_text)]
    kb_normalized = _normalize(kb_text)

    ungrounded = [c for c in claimed if c not in kb_normalized]

    return NumericGroundingResult(
        ok=len(ungrounded) == 0,
        claimed_numbers=claimed,
        ungrounded_numbers=ungrounded,
    )


if __name__ == "__main__":
    kb = ("Veloce Health cut deploy time from 42 minutes to 14 minutes, "
          "saving $138k and reducing incidents by 66%.")
    good_draft = "We helped Veloce Health go from 42 minutes to 14 minutes, saving them $138k."
    bad_draft = "We helped a similar company cut their incidents by 90% and saved $500k."

    print("Good draft:", verify_numeric_claims(good_draft, kb))
    print("Bad draft: ", verify_numeric_claims(bad_draft, kb))
