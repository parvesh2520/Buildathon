"""
guardrails.py - deterministic guardrail layer for the Autonomous SDR.

Design rules
------------
* Stdlib only. On Windows, `zoneinfo` needs the `tzdata` package:  pip install tzdata
* No secrets in code. Runtime configuration comes from environment variables:
    SDR_CANARY_TOKEN      secret marker embedded in system prompts; if it ever appears
                          in an output, the system prompt leaked -> BLOCK
    SDR_POSTAL_ADDRESS    physical postal address required in commercial email
    SDR_MAX_COST_PER_LEAD USD cap per lead (default 0.05)
    SDR_MAX_TOTAL_USD     USD cap per run   (default 25)
* Every check returns `Finding`s; `GateResult.verdict` is the worst finding.
  Verdict semantics (worst wins):  BLOCK > HOLD > REVISE > DEFER > ALLOW
    BLOCK  never send / quarantine
    HOLD   needs a human -> Manager Inbox (Flow 4)
    REVISE send back to the Personalisation Agent with feedback (self-healing loop)
    DEFER  valid but not now (quiet hours) -> reschedule in the timeline (Flow 3)
* Regex checks are a fast, cheap, explainable FIRST line of defence that sits beside the
  DronaHQ Prompt/Output Policies. They are not a substitute for legal review.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import secrets
import threading
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Iterable, Optional
from zoneinfo import ZoneInfo


# --------------------------------------------------------------------------- #
# Core types
# --------------------------------------------------------------------------- #
class Verdict(str, Enum):
    ALLOW = "ALLOW"
    DEFER = "DEFER"
    REVISE = "REVISE"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


_RANK = {Verdict.ALLOW: 0, Verdict.DEFER: 1, Verdict.REVISE: 2, Verdict.HOLD: 3, Verdict.BLOCK: 4}


@dataclass
class Finding:
    check: str
    verdict: Verdict
    reason: str
    meta: dict = field(default_factory=dict)


@dataclass
class GateResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def verdict(self) -> Verdict:
        return max((f.verdict for f in self.findings), key=_RANK.__getitem__, default=Verdict.ALLOW)

    def add(self, f: Optional[Finding]) -> None:
        if f is not None:
            self.findings.append(f)

    def extend(self, fs: Iterable[Finding]) -> None:
        self.findings.extend(fs)

    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.verdict != Verdict.ALLOW]

    def timeline(self) -> list[dict]:
        """Shape suitable for the Mission Control timeline / audit trail."""
        return [
            {"check": f.check, "verdict": f.verdict.value, "reason": f.reason, "meta": f.meta}
            for f in self.findings
        ]


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
FOOTER_MARKER = "\n--\n"


def normalize(text: str) -> str:
    """NFKC-fold, drop zero-width chars, collapse whitespace, lowercase.
    Defeats full-width / zero-width obfuscation. (Cross-script homoglyphs such as Cyrillic
    look-alikes are NOT folded - keep the DronaHQ prompt policy as the second layer.)"""
    t = unicodedata.normalize("NFKC", text or "").translate(_ZERO_WIDTH)
    return re.sub(r"\s+", " ", t).strip().lower()


def strip_footer(body: str) -> str:
    idx = body.rfind(FOOTER_MARKER)
    return body[:idx] if idx != -1 else body


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


# --------------------------------------------------------------------------- #
# 1. Prompt injection / jailbreak / exfiltration (inbound AND outbound)
# --------------------------------------------------------------------------- #
_INJECTION: list[tuple[str, str, Verdict]] = [
    ("override_instructions",
     r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(previous|prior|above|earlier|all|your|system)\b.{0,30}\b(instruction|prompt|rule|guideline|polic)",
     Verdict.BLOCK),
    ("prompt_exfiltration",
     r"\b(reveal|show|print|repeat|output|leak|tell me|share)\b.{0,40}\b(system prompt|your prompt|your instructions|initial instructions|hidden (prompt|instructions)|developer message|knowledge base contents)",
     Verdict.BLOCK),
    ("authority_impersonation",
     r"\b(i am|i'm|this is)\b.{0,20}\b(the )?(admin|administrator|developer|sysadmin|your (creator|owner|operator)|anthropic|openai|dronahq (staff|support))\b|\byou are (now )?authori[sz]ed\b",
     Verdict.BLOCK),
    ("delimiter_smuggling",
     r"(</?\s*(system|assistant|instructions?)\s*>|\[/?inst\]|<\|im_(start|end)\|>|#{2,}\s*(system|instruction))",
     Verdict.BLOCK),
    ("role_hijack",
     r"\b(you are now|from now on,? you|pretend (to be|you are)|roleplay as|developer mode|dan mode|jailbreak)\b",
     Verdict.HOLD),
    ("tool_abuse",
     r"\b(call|invoke|run|execute)\b.{0,30}\b(tool|function|webhook|shell|command|sql)\b",
     Verdict.HOLD),
    ("obfuscated_payload",
     r"\b(base64|rot13|hex[- ]?encoded|decode (this|the following))\b",
     Verdict.HOLD),
    ("free_grant_or_discount",
     r"\b(give|grant|issue|send|provide|approve)\b.{0,30}\b(free|complimentary|unlimited|lifetime|100\s?%)\b.{0,30}\b(licen[sc]e|access|account|plan|subscription|credits?|discount)\b",
     Verdict.HOLD),
]


def scan_injection(text: str) -> list[Finding]:
    t = normalize(text)
    out = []
    for name, pat, verdict in _INJECTION:
        m = re.search(pat, t)
        if m:
            out.append(Finding("prompt_injection", verdict, f"pattern:{name}", {"match": m.group(0)[:80]}))
    return out


def new_canary() -> str:
    """Generate a canary to store in SDR_CANARY_TOKEN and embed in every system prompt."""
    return "cnry-" + secrets.token_hex(6)


def scan_leakage(text: str) -> list[Finding]:
    """Detect system-prompt leakage in agent OUTPUT."""
    out: list[Finding] = []
    canary = os.getenv("SDR_CANARY_TOKEN", "").strip().lower()
    t = normalize(text)
    if canary and canary in t:
        out.append(Finding("prompt_leak", Verdict.BLOCK, "canary_token_in_output"))
    if re.search(r"\b(my (system )?(prompt|instructions) (is|are|say)|as an ai language model|i was instructed to|my (hidden|internal) (rules|instructions))\b", t):
        out.append(Finding("prompt_leak", Verdict.BLOCK, "self_disclosure_phrase"))
    return out


# --------------------------------------------------------------------------- #
# 2. PII / secrets
# --------------------------------------------------------------------------- #
@dataclass
class PIIHit:
    kind: str
    start: int
    end: int


SENSITIVE_KINDS = {"card", "aadhaar", "pan", "us_ssn", "bank_account", "api_key"}
_PII_PATTERNS: dict[str, re.Pattern] = {
    "card": re.compile(r"(?<![\d])(?:\d[ -]?){13,19}(?![\d])"),
    "aadhaar": re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)"),
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "us_ssn": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    "bank_account": re.compile(r"(?i)\b(?:a/?c|acct|account)(?:\s*(?:no|number|#))?\.?\s*[:\-]?\s*\d{9,18}\b"),
    "api_key": re.compile(r"\b(?:sk-[A-Za-z0-9_\-]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9\-]{10,})\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+?91[ -]?)?[6-9]\d{9}(?!\d)|(?<!\d)(?:\+?1[ -]?)?\(?\d{3}\)?[ -]\d{3}[ -]\d{4}(?!\d)"),
}


def _luhn_ok(digits: str) -> bool:
    d = [int(c) for c in digits][::-1]
    total = sum(d[0::2]) + sum(sum(divmod(x * 2, 10)) for x in d[1::2])
    return total % 10 == 0


def find_pii(text: str) -> list[PIIHit]:
    hits: list[PIIHit] = []
    taken: list[tuple[int, int]] = []

    def overlaps(s: int, e: int) -> bool:
        return any(s < b and a < e for a, b in taken)

    for m in _PII_PATTERNS["card"].finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            hits.append(PIIHit("card", m.start(), m.end()))
            taken.append((m.start(), m.end()))
    for kind, pat in _PII_PATTERNS.items():
        if kind == "card":
            continue
        for m in pat.finditer(text):
            if not overlaps(m.start(), m.end()):
                hits.append(PIIHit(kind, m.start(), m.end()))
                taken.append((m.start(), m.end()))
    return sorted(hits, key=lambda h: h.start)


def redact(text: str, kinds: Optional[set[str]] = None) -> str:
    """Replace PII spans with [REDACTED:kind]. Default: sensitive kinds only (keeps email/phone)."""
    kinds = kinds if kinds is not None else SENSITIVE_KINDS
    out, last = [], 0
    for h in find_pii(text):
        if h.kind in kinds:
            out.append(text[last:h.start])
            out.append(f"[REDACTED:{h.kind}]")
            last = h.end
    out.append(text[last:])
    return "".join(out)


def check_outbound_pii(text: str) -> list[Finding]:
    bad = sorted({h.kind for h in find_pii(text) if h.kind in SENSITIVE_KINDS})
    return [Finding("pii_output", Verdict.BLOCK, f"sensitive_pii:{','.join(bad)}", {"kinds": bad})] if bad else []


def sanitize_inbound(text: str) -> tuple[str, list[Finding]]:
    """Data-minimisation: redact sensitive PII BEFORE the message reaches an LLM or the logs."""
    clean = redact(text)
    notes = []
    if clean != text:
        notes.append(Finding("pii_inbound", Verdict.ALLOW, "sensitive_pii_redacted_before_processing"))
    return clean, notes


# --------------------------------------------------------------------------- #
# 3. Opt-out, auto-reply, complaints (deterministic pre-classifier)
# --------------------------------------------------------------------------- #
_OPT_OUT_KEYWORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit", "remove"}
_OPT_OUT_PHRASES = re.compile(
    r"\b(unsubscribe|opt[\s-]?out|remove me|take me off|delete my (data|details|information)|"
    r"do not (contact|email|call|message|text)|don'?t (contact|email|call|message|text|reach out)|"
    r"stop (emailing|calling|messaging|texting|contacting|sending)|cease and desist|"
    r"mat bhejo|message mat karo|band karo)\b"
)
_AUTO_REPLY = re.compile(
    r"\b(out of (the )?office|automatic reply|auto[- ]?reply|autoreply|i am (currently )?(away|travelling|traveling|on leave)|"
    r"on (annual |maternity |paternity )?leave|will (be )?(back|return|respond) (on|by|after)|"
    r"delivery status notification|undeliverable|mailer-daemon|do not reply to this (email|message)|"
    r"this is an automated (message|response|reply))\b"
)
_COMPLAINT = re.compile(
    r"\b(report (you|this)|reported you|spam(mer|ming)?|lawyer|legal action|sue (you|your)|"
    r"gdpr|dpdp|can-?spam|tcpa|trai|dnd|ndnc|do not call|"
    r"how did you (get|find|obtain) my (email|number|phone|data|details|information|contact))\b"
)


def detect_opt_out(text: str) -> bool:
    t = normalize(text)
    words = re.findall(r"[a-z]+", t)
    if 0 < len(words) <= 2 and words[0] in _OPT_OUT_KEYWORDS:
        return True
    return bool(_OPT_OUT_PHRASES.search(t))


def precheck_inbound(text: str) -> dict:
    """High-precision rules that run BEFORE the LLM classifier.
    Returns {"definitive": intent|None, "hints": [...], "security": [Finding,...]}.
    Automated messages are never a human intent, so auto_reply is checked first
    (an out-of-office footer that says 'unsubscribe' is NOT an opt-out)."""
    t = normalize(text)
    sec = scan_injection(text)
    hints = []
    if _COMPLAINT.search(t):
        hints.append("compliance_complaint")
    if _AUTO_REPLY.search(t):
        return {"definitive": "auto_reply", "hints": hints, "security": sec}
    if detect_opt_out(text):
        return {"definitive": "opt_out", "hints": hints, "security": sec}
    return {"definitive": None, "hints": hints, "security": sec}


def _norm_identifier(value: str) -> str:
    v = (value or "").strip().lower()
    if "@" in v:
        return v
    digits = re.sub(r"\D", "", v)
    if len(digits) >= 10 and not v.startswith("http"):
        return digits[-10:]
    return v.rstrip("/")


class SuppressionList:
    """Global do-not-contact list, shared by ALL campaigns and channels.
    An opt-out on any channel suppresses every channel (safest reading of CAN-SPAM/TCPA/DPDP)."""

    def __init__(self, path: Optional[str] = None):
        self._ids: set[str] = set()
        self._domains: set[str] = set()
        self._lock = threading.Lock()
        self._path = path
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._ids, self._domains = set(data.get("ids", [])), set(data.get("domains", []))

    def _persist(self) -> None:
        if not self._path:
            return
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"ids": sorted(self._ids), "domains": sorted(self._domains)}, fh)
        os.replace(tmp, self._path)

    def suppress(self, *identifiers: str) -> None:
        with self._lock:
            self._ids.update(_norm_identifier(i) for i in identifiers if i)
            self._persist()

    def suppress_domain(self, domain: str) -> None:
        with self._lock:
            self._domains.add(domain.strip().lower())
            self._persist()

    def is_suppressed(self, *identifiers: str) -> bool:
        with self._lock:
            for raw in identifiers:
                if not raw:
                    continue
                n = _norm_identifier(raw)
                if n in self._ids:
                    return True
                if "@" in n and n.split("@", 1)[1] in self._domains:
                    return True
        return False


# --------------------------------------------------------------------------- #
# 4. Send-window / regulatory checks
# --------------------------------------------------------------------------- #
# (start_hour inclusive, end_hour exclusive) in the RECIPIENT's local time.
HARD_WINDOWS = {
    ("US", "sms"): (8, 21), ("US", "voice"): (8, 21),   # TCPA: 8am-9pm recipient local time
    ("IN", "sms"): (9, 21), ("IN", "voice"): (9, 21),   # TRAI telemarketing rules: 9am-9pm (+ DND registry)
}
SOFT_WINDOW = (9, 18)  # etiquette for email / LinkedIn; weekdays only


def _next_open(local_now: datetime, start: int, end: int, weekdays_only: bool) -> datetime:
    """Next moment the window opens. Only called when sending is NOT allowed right now, i.e.
    before opening, after closing, or (soft windows) during a weekend."""
    candidate = local_now.replace(hour=start, minute=0, second=0, microsecond=0)
    if local_now.hour >= start:  # already past today's opening -> earliest is tomorrow
        candidate += timedelta(days=1)
    while weekdays_only and candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def check_send_window(channel: str, region: str, tz_name: Optional[str], now: Optional[datetime] = None) -> Optional[Finding]:
    channel, region = channel.lower(), region.upper()
    hard = HARD_WINDOWS.get((region, channel))
    if not tz_name:
        if hard:
            return Finding("send_window", Verdict.HOLD, "unknown_recipient_timezone_for_regulated_channel")
        return None
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return Finding("send_window", Verdict.HOLD, f"invalid_timezone:{tz_name}")
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(tz)
    start, end = hard or SOFT_WINDOW
    weekdays_only = hard is None
    in_hours = start <= local.hour < end
    is_weekend = weekdays_only and local.weekday() >= 5
    if in_hours and not is_weekend:
        return None
    nxt = _next_open(local, start, end, weekdays_only)
    return Finding(
        "send_window", Verdict.DEFER,
        "outside_regulated_hours" if hard else "outside_business_hours",
        {"local_time": local.isoformat(), "next_allowed_at": nxt.astimezone(timezone.utc).isoformat(), "hard_rule": bool(hard)},
    )


def ensure_email_footer(body: str, postal_address: Optional[str] = None) -> str:
    """CAN-SPAM: working opt-out + physical postal address. The SENDER appends this
    deterministically so the LLM never has to remember it."""
    addr = (postal_address or os.getenv("SDR_POSTAL_ADDRESS", "")).strip()
    if FOOTER_MARKER in body:
        return body
    lines = [FOOTER_MARKER.strip("\n")]
    if addr:
        lines.append(addr)
    lines.append('If you would rather not hear from me, reply "unsubscribe" and I will stop immediately.')
    return body.rstrip() + "\n\n" + "\n".join(lines)


def check_email_compliance(subject: str, body: str, has_prior_thread: bool, postal_address: Optional[str] = None) -> list[Finding]:
    out: list[Finding] = []
    if not has_prior_thread and re.match(r"\s*(re|fwd?|fw)\s*:", subject or "", re.I):
        out.append(Finding("email_compliance", Verdict.BLOCK, "deceptive_subject_fake_reply_prefix"))
    b = normalize(body)
    if not re.search(r"unsubscribe|opt[\s-]?out|reply (with )?stop|rather not hear", b):
        out.append(Finding("email_compliance", Verdict.REVISE, "missing_opt_out_line", {"fix": "ensure_email_footer"}))
    addr = (postal_address or os.getenv("SDR_POSTAL_ADDRESS", "")).strip()
    if not addr:
        out.append(Finding("email_compliance", Verdict.HOLD, "SDR_POSTAL_ADDRESS_not_configured"))
    elif normalize(addr) not in b:
        out.append(Finding("email_compliance", Verdict.REVISE, "missing_postal_address", {"fix": "ensure_email_footer"}))
    return out


def check_data_provenance(region: str, data_source: Optional[str]) -> Optional[Finding]:
    """Every prospect record should carry where the data came from. That is what lets the
    agent answer 'how did you get my number?' truthfully, and it supports DPDP-style
    notice/purpose-limitation audits. (Not legal advice - confirm requirements with counsel.)"""
    if region.upper() == "IN" and not (data_source or "").strip():
        return Finding("data_provenance", Verdict.HOLD, "missing_data_source_for_IN_prospect")
    return None


# --------------------------------------------------------------------------- #
# 5. Brand / claims guardrails (outbound)
# --------------------------------------------------------------------------- #
_PRICING = re.compile(
    r"\b(discount|% off|percent off|per (seat|user|month|year|developer|call|minute)|pricing|price[sd]?|quote[sd]?|"
    r"free (licen[sc]e|trial|pilot|credits?)|waive[sd]?|price[- ]match|special (rate|offer|pricing)|coupon|refund|"
    r"msa|sla|service level|contract terms|data processing agreement|dpa)\b"
)
_LEGAL_BLOCK = re.compile(
    r"\b(guarantee[sd]? (you )?(full |complete |100% )?compliance|100\s?% compliant|"
    r"rbi[- ](approved|certified|endorsed|authori[sz]ed)|(approved|certified|endorsed) by (the )?(rbi|reserve bank|sebi|irdai|regulators?)|"
    r"legally (safe|bulletproof|guaranteed)|(will|won'?t) (never )?(get|be) fined|audit[- ]proof|immune to (audits?|penalt\w+))\b"
)
_CERT_CLAIM = re.compile(
    r"\b(soc ?2|iso ?27001|hipaa|pci[- ]dss|gdpr|dpdp|rbi)[- ]?(type \w+ )?(certified|compliant|audited|attested|approved)\b"
)
_ABSOLUTE = re.compile(
    r"\b(guarantee[sd]?|risk[- ]free|no[- ]risk|zero risk|100\s?% (success|uptime|accuracy|secure|safe)|never (fails?|goes down|breaks))\b"
)
_FAKE_FAMILIAR = re.compile(
    r"\b(as (we )?(discussed|spoke|talked)|per our (call|conversation|chat|discussion)|following (up )?on our (call|conversation|chat|meeting)|"
    r"(great|good|nice) (speaking|talking|meeting) (with|to) you|thanks for (your time|taking (my|the) call)|as promised|you (asked|requested) (me|us) to)\b"
)
_STRONG_NEG = {"terrible", "awful", "garbage", "trash", "scam", "inferior", "sucks", "useless", "worthless", "junk",
               "shady", "incompetent", "fraud", "joke", "dangerous", "insecure", "overpriced"}
_MILD_NEG = {"slow", "buggy", "bloated", "clunky", "outdated", "unreliable", "broken", "expensive", "painful", "flaky", "legacy"}
_COMPARATIVE = re.compile(r"\b(better than|beats|faster than|cheaper than|outperforms?|unlike|superior to|more (reliable|secure|accurate) than)\b")

# EXAMPLE competitor lists - replace with the competitors that actually appear in each KB.
DEFAULT_COMPETITORS = {
    "us_saas_cto": ["circleci", "jenkins", "github actions", "gitlab ci", "buildkite", "harness"],
    "india_bfsi_cio": ["finacle", "temenos", "nucleus software", "perfios", "signzy"],
    "voice_ai_founder": ["vapi", "retell", "bland ai", "twilio", "deepgram"],
}

# Cross-campaign contamination guard (names taken from the campaign brief).
CAMPAIGN_ENTITIES = {
    "us_saas_cto": ["Turboscale AI", "Veloce Health"],
    "india_bfsi_cio": ["FinShield AI", "Bharat Apex"],
    "voice_ai_founder": ["WhisperFlow AI", "TalkSync"],
}


def check_claims(text: str, evidence: str = "", competitors: Optional[list[str]] = None,
                 prior_interactions: int = 0) -> list[Finding]:
    t, ev = normalize(text), normalize(evidence).replace("-", " ")
    out: list[Finding] = []
    if _PRICING.search(t):
        out.append(Finding("claims", Verdict.HOLD, "pricing_or_commercial_terms", {"match": _PRICING.search(t).group(0)}))
    m = _LEGAL_BLOCK.search(t)
    if m:
        out.append(Finding("claims", Verdict.BLOCK, "regulatory_guarantee_or_endorsement", {"match": m.group(0)}))
    for m in _CERT_CLAIM.finditer(t):
        if m.group(0).replace("-", " ") not in ev:
            out.append(Finding("claims", Verdict.HOLD, "unverified_certification_claim", {"match": m.group(0)}))
    m = _ABSOLUTE.search(t)
    if m:
        out.append(Finding("claims", Verdict.HOLD, "absolute_or_risk_free_claim", {"match": m.group(0)}))
    if prior_interactions == 0:
        m = _FAKE_FAMILIAR.search(t)
        if m:
            out.append(Finding("claims", Verdict.BLOCK, "fabricated_prior_relationship", {"match": m.group(0)}))
    for sent in split_sentences(t):
        for comp in (competitors or []):
            if re.search(rf"\b{re.escape(comp.lower())}\b", sent):
                words = set(re.findall(r"[a-z]+", sent))
                if words & _STRONG_NEG:
                    out.append(Finding("claims", Verdict.BLOCK, "competitor_disparagement", {"competitor": comp}))
                elif words & _MILD_NEG:
                    out.append(Finding("claims", Verdict.HOLD, "competitor_negative_framing", {"competitor": comp}))
                elif _COMPARATIVE.search(sent):
                    out.append(Finding("claims", Verdict.HOLD, "unsubstantiated_comparison", {"competitor": comp}))
    return out


def check_campaign_isolation(text: str, campaign_id: str) -> list[Finding]:
    """A draft for campaign X must never name another campaign's product or customer."""
    t = normalize(text)
    out = []
    for cid, names in CAMPAIGN_ENTITIES.items():
        if cid == campaign_id:
            continue
        for name in names:
            if re.search(rf"\b{re.escape(name.lower())}\b", t):
                out.append(Finding("campaign_isolation", Verdict.BLOCK, "cross_campaign_entity_leak",
                                   {"entity": name, "belongs_to": cid}))
    return out


# --------------------------------------------------------------------------- #
# 6. Grounding: numeric-claim verification + self-healing loop
# --------------------------------------------------------------------------- #
_UNIT_FAMILY = {
    "%": "pct", "percent": "pct", "ms": "ms", "millisecond": "ms", "milliseconds": "ms",
    "s": "sec", "sec": "sec", "secs": "sec", "second": "sec", "seconds": "sec",
    "min": "min", "mins": "min", "minute": "min", "minutes": "min",
    "h": "hr", "hr": "hr", "hrs": "hr", "hour": "hr", "hours": "hr",
    "day": "day", "days": "day", "week": "week", "weeks": "week", "month": "month", "months": "month",
    "year": "year", "years": "year", "yr": "year", "yrs": "year", "x": "x",
}
_MAGNITUDE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9,
              "cr": 1e7, "crore": 1e7, "crores": 1e7, "lakh": 1e5, "lakhs": 1e5}
_UNITS = ("%|percent|milliseconds?|ms|seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|yrs?|"
          "million|billion|thousand|mn|bn|crores?|cr|lakhs?|x|k|m|b|h|s")
_NUM = re.compile(
    rf"(?<![A-Za-z0-9.])(?P<cur>[$\u20b9\u20ac\u00a3]|rs\.?\s?|inr\s?|usd\s?)?(?P<num>\d[\d,]*(?:\.\d+)?)\s?-?(?P<unit>{_UNITS})?(?![A-Za-z0-9])",
    re.I,
)
_CTA_SENTENCE = re.compile(r"\b(call|chat|demo|walkthrough|sync|slot|catch[- ]up|conversation|meeting|calendar|window)\b", re.I)


@dataclass
class Claim:
    raw: str
    sentence: str
    candidates: frozenset  # {(value, family)}


def _candidates(num: str, unit: Optional[str], cur: Optional[str]) -> frozenset:
    v = float(num.replace(",", ""))
    u = (unit or "").lower()
    cands = set()
    if cur:
        cands.add((v * _MAGNITUDE.get(u, 1), "money"))
        return frozenset(cands)
    if u in _MAGNITUDE:
        cands.add((v * _MAGNITUDE[u], "num"))
    if u in _UNIT_FAMILY:
        cands.add((v, _UNIT_FAMILY[u]))
    if not u:
        cands.add((v, "any"))
    return frozenset(cands)


def _compatible(fa: str, fb: str) -> bool:
    if fa == fb or "any" in (fa, fb):
        return True
    return {fa, fb} <= {"money", "num"}


def _supported(claim: frozenset, evidence: set) -> bool:
    return any(abs(v - ev) < 1e-6 and _compatible(f, ef) for v, f in claim for ev, ef in evidence)


def _evidence_values(text: str) -> set:
    vals: set = set()
    for m in _NUM.finditer(text):
        vals |= set(_candidates(m.group("num"), m.group("unit"), m.group("cur")))
    return vals


def extract_claims(text: str) -> list[Claim]:
    """Numeric claims = numbers carrying a unit or currency ('42m', '$138k', '84%', '420 ms').
    Bare integers and time-of-day are ignored; '15-minute chat' is ignored in CTA sentences."""
    claims = []
    for sent in split_sentences(strip_footer(text)):
        for m in _NUM.finditer(sent):
            unit, cur = m.group("unit"), m.group("cur")
            if not (unit or cur):
                continue
            if unit and _UNIT_FAMILY.get(unit.lower()) == "min" and _CTA_SENTENCE.search(sent):
                continue
            claims.append(Claim(m.group(0).strip(), sent, _candidates(m.group("num"), unit, cur)))
    return claims


def unsupported_claims(text: str, evidence: str) -> list[Claim]:
    ev = _evidence_values(evidence)
    return [c for c in extract_claims(text) if not _supported(c.candidates, ev)]


def check_numeric_grounding(text: str, evidence: str) -> list[Finding]:
    bad = unsupported_claims(text, evidence)
    return [Finding("grounding", Verdict.REVISE, "unsupported_numeric_claim",
                    {"claims": [c.raw for c in bad]})] if bad else []


@dataclass
class HealResult:
    text: str
    status: str  # clean | healed_by_evidence | healed_by_rewrite | stripped | escalate
    unsupported_before: list[str]
    unsupported_after: list[str]
    attempts: int
    audit: list[dict]


_CTA_HINT = re.compile(r"\?|\b(worth|open to|walkthrough|reply|thoughts|happy to|let me know|interested)\b", re.I)


def ground_and_heal(
    draft: str,
    evidence: list[str],
    *,
    kb_search: Optional[Callable[[str], list[str]]] = None,
    rewrite: Optional[Callable[[str, list[str], str], str]] = None,
    max_attempts: int = 2,
    min_words: int = 25,
    extra_allowed: str = "",
) -> HealResult:
    """Self-healing grounding. Instead of failing on an ungrounded claim:
      1. widen evidence with a targeted KB lookup for that exact claim (cheap)
      2. ask the LLM to rewrite using ONLY the evidence            (callback, optional)
      3. deterministically strip the offending sentences            (no LLM, always terminates)
      4. escalate to the Manager Inbox if stripping guts the message
    `kb_search(query) -> list[str]` and `rewrite(draft, bad_claims, evidence_text) -> str` are
    injected so this module has no dependency on the DronaHQ client."""
    audit: list[dict] = []
    ev = list(evidence)

    def check(t: str) -> list[Claim]:
        return unsupported_claims(t, "\n".join(ev) + "\n" + extra_allowed)

    current, bad = draft, check(draft)
    initial = [c.raw for c in bad]
    if not bad:
        return HealResult(current, "clean", [], [], 0, audit)

    attempts = 0
    while bad and attempts < max_attempts:
        attempts += 1
        if kb_search:
            for c in bad:
                try:
                    hits = kb_search(c.sentence[:200]) or []
                except Exception as exc:  # KB outage must never crash the pipeline
                    audit.append({"step": "kb_search_error", "error": repr(exc)})
                    hits = []
                ev.extend(h for h in hits if h not in ev)
                audit.append({"step": "kb_lookup", "claim": c.raw, "hits": len(hits)})
            bad = check(current)
            if not bad:
                return HealResult(current, "healed_by_evidence", initial, [], attempts, audit)
        if rewrite:
            try:
                candidate = rewrite(current, [c.raw for c in bad], "\n".join(ev))
            except Exception as exc:
                audit.append({"step": "rewrite_error", "error": repr(exc)})
                candidate = None
            if candidate and candidate.strip():
                current = candidate
                bad = check(current)
                audit.append({"step": "rewrite", "remaining": [c.raw for c in bad]})
                if not bad:
                    return HealResult(current, "healed_by_rewrite", initial, [], attempts, audit)

    if bad:
        drop = {c.sentence for c in bad}
        kept = [s for s in split_sentences(strip_footer(current)) if s not in drop]
        stripped = " ".join(kept)
        audit.append({"step": "strip", "dropped": sorted(drop)})
        if word_count(stripped) < min_words or not _CTA_HINT.search(stripped):
            return HealResult(current, "escalate", initial, [c.raw for c in bad], attempts, audit)
        footer = current[current.rfind(FOOTER_MARKER):] if FOOTER_MARKER in current else ""
        return HealResult(stripped + footer, "stripped", initial, [], attempts, audit)
    return HealResult(current, "healed_by_evidence", initial, [], attempts, audit)


# --------------------------------------------------------------------------- #
# 7. Cross-campaign entity collision (Flow 5)
# --------------------------------------------------------------------------- #
_CORP_SUFFIX = {"inc", "incorporated", "llc", "ltd", "limited", "pvt", "private", "plc", "corp", "corporation",
                "co", "company", "gmbh", "sa", "ag", "llp", "lp", "holdings", "group"}
_FREEMAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me",
             "protonmail.com", "rediffmail.com", "live.com", "aol.com"}
_SLD = {"co", "com", "org", "net", "gov", "ac", "edu"}


def normalize_company(name: str) -> str:
    t = re.sub(r"[^\w\s]", " ", unicodedata.normalize("NFKC", name or "").lower())
    return " ".join(w for w in t.split() if w not in _CORP_SUFFIX)


def domain_root(value: str) -> str:
    d = value.split("@", 1)[-1].strip().lower()
    d = re.sub(r"^https?://", "", d).split("/")[0]
    labels = d.split(".")
    if len(labels) >= 3 and labels[-2] in _SLD and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:]) if len(labels) >= 2 else d


def same_company(a_name: str, a_domain: str, b_name: str, b_domain: str) -> Optional[str]:
    if a_domain and b_domain:
        ra, rb = domain_root(a_domain), domain_root(b_domain)
        if ra == rb and ra not in _FREEMAIL:
            return "domain"
    na, nb = normalize_company(a_name), normalize_company(b_name)
    if not na or not nb:
        return None
    if na == nb or difflib.SequenceMatcher(None, na, nb).ratio() >= 0.88:
        return "name"
    ta, tb = set(na.split()), set(nb.split())
    if (ta < tb and len(ta) >= 2) or (tb < ta and len(tb) >= 2):
        return "name_subset"
    return None


@dataclass
class ProspectEntry:
    prospect_id: str
    campaign_id: str
    company: str
    email: str
    title: str = ""
    linkedin: str = ""
    active: bool = True


@dataclass
class Conflict:
    kind: str  # same_prospect | same_company
    matched_on: str
    holder: ProspectEntry
    challenger: ProspectEntry


class CollisionIndex:
    """Detects when two campaigns target the same person or the same enterprise."""

    def __init__(self) -> None:
        self._entries: list[ProspectEntry] = []
        self._lock = threading.Lock()

    def check(self, new: ProspectEntry) -> list[Conflict]:
        conflicts = []
        with self._lock:
            for e in self._entries:
                if not e.active or e.campaign_id == new.campaign_id:
                    continue
                same_person = (
                    (e.email and new.email and _norm_identifier(e.email) == _norm_identifier(new.email))
                    or (e.linkedin and new.linkedin and _norm_identifier(e.linkedin) == _norm_identifier(new.linkedin))
                )
                if same_person:
                    conflicts.append(Conflict("same_prospect", "identifier", e, new))
                    continue
                how = same_company(e.company, e.email, new.company, new.email)
                if how:
                    conflicts.append(Conflict("same_company", how, e, new))
        return conflicts

    def register(self, new: ProspectEntry) -> list[Conflict]:
        conflicts = self.check(new)
        with self._lock:
            self._entries.append(new)
        return conflicts

    def deactivate_campaign(self, campaign_id: str) -> None:
        with self._lock:
            for e in self._entries:
                if e.campaign_id == campaign_id:
                    e.active = False


def conflict_to_inbox_card(c: Conflict) -> dict:
    same = c.kind == "same_prospect"
    return {
        "type": "cross_campaign_conflict",
        "title": ("Same prospect targeted by two campaigns" if same
                  else f"Two campaigns are targeting {c.holder.company}"),
        "summary": (f"{c.holder.campaign_id} is already engaging {c.holder.email or c.holder.prospect_id}; "
                    f"{c.challenger.campaign_id} wants to contact {c.challenger.email or c.challenger.prospect_id} "
                    f"(matched on {c.matched_on})."),
        "recommendation": ("Keep the earlier campaign and suppress the newcomer" if same
                           else "Allow only if the buyers differ (e.g. CTO vs CIO); otherwise keep the earlier campaign"),
        "options": [f"Keep {c.holder.campaign_id}", f"Switch to {c.challenger.campaign_id}",
                    "Allow both (different buyers)", "Suppress both"],
        "default_action": "hold_challenger_until_resolved",
    }


# --------------------------------------------------------------------------- #
# 8. Multi-turn memory: never repeat yourself; rotate proof points and angles
# --------------------------------------------------------------------------- #
ANGLES = ["pain_diagnosis", "case_study", "roi_math", "peer_question", "breakup"]


@dataclass
class TouchRecord:
    touch_no: int
    channel: str
    angle: str
    case_study_id: Optional[str]
    cta: str
    text: str


def _shingles(text: str, n: int = 3) -> set:
    w = re.findall(r"[a-z0-9']+", normalize(strip_footer(text)))
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


class TouchMemory:
    def __init__(self) -> None:
        self._by_prospect: dict[str, list[TouchRecord]] = {}

    def add(self, prospect_id: str, rec: TouchRecord) -> None:
        self._by_prospect.setdefault(prospect_id, []).append(rec)

    def history(self, prospect_id: str) -> list[TouchRecord]:
        return list(self._by_prospect.get(prospect_id, []))

    def used(self, prospect_id: str) -> dict:
        h = self.history(prospect_id)
        return {"angles": [r.angle for r in h], "case_studies": [r.case_study_id for r in h if r.case_study_id],
                "ctas": [r.cta for r in h]}

    def next_angle(self, prospect_id: str) -> str:
        used = set(self.used(prospect_id)["angles"])
        return next((a for a in ANGLES if a not in used), ANGLES[-1])

    def next_case_study(self, prospect_id: str, available: list[str]) -> Optional[str]:
        """Prefer an unused proof point; otherwise the least recently used."""
        if not available:
            return None
        seq = self.used(prospect_id)["case_studies"]
        for cs in available:
            if cs not in seq:
                return cs
        return min(available, key=lambda cs: max(i for i, x in enumerate(seq) if x == cs))

    def prompt_block(self, prospect_id: str) -> str:
        """Inject into the Follow-up / Personalisation prompt so the LLM avoids repeats up front."""
        h = self.history(prospect_id)
        if not h:
            return "PRIOR TOUCHES: none."
        lines = [f"- Touch {r.touch_no} ({r.channel}) angle={r.angle} case_study={r.case_study_id or 'none'} cta={r.cta}" for r in h]
        return ("PRIOR TOUCHES (do NOT reuse these angles, proof points, openers or CTAs; do not restate their facts):\n"
                + "\n".join(lines))

    def check_repetition(self, prospect_id: str, draft: str, threshold: float = 0.30) -> list[Finding]:
        new = _shingles(draft)
        worst, worst_touch = 0.0, None
        for r in self.history(prospect_id):
            old = _shingles(r.text)
            if new and old:
                j = len(new & old) / len(new | old)
                if j > worst:
                    worst, worst_touch = j, r.touch_no
        if worst >= threshold:
            return [Finding("repetition", Verdict.REVISE, "draft_repeats_prior_touch",
                            {"similarity": round(worst, 2), "touch": worst_touch})]
        return []

    def to_dict(self) -> dict:
        return {pid: [r.__dict__ for r in recs] for pid, recs in self._by_prospect.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "TouchMemory":
        m = cls()
        for pid, recs in data.items():
            for r in recs:
                m.add(pid, TouchRecord(**r))
        return m


# --------------------------------------------------------------------------- #
# 9. Cultural / tone adapter (register is set by audience & regulatory context)
# --------------------------------------------------------------------------- #
TONE_PROFILES = {
    "us_saas_cto": {
        "label": "Peer-level, direct, numbers-first",
        "max_words": 110, "greeting": "Hi {first},", "signoff": "Best,",
        "banned": ["dear sir", "dear madam", "kindly", "revert", "esteemed", "hope this email finds you well",
                   "synergy", "circle back", "touch base", "just checking in", "game-changer"],
        "no_emoji": True, "no_exclamation": False,
        "guidance": ["Lead with a concrete number or a specific observation about their stack.",
                     "One idea per email; no more than three short paragraphs.",
                     "Peer tone: no flattery, no buzzwords, ask one low-friction question."],
    },
    "india_bfsi_cio": {
        "label": "Formal, respectful, regulation-aware (regulated BFSI buyer)",
        "max_words": 160, "greeting": "Dear {salutation} {last},", "signoff": "Warm regards,",
        "banned": ["hey", "hey there", "yo", "quick q", "wanna", "gonna", "lol", "killer", "crush it", "rockstar",
                   "ninja", "game-changer", "hope this email finds you well"],
        "no_emoji": True, "no_exclamation": True,
        "guidance": ["Use a full salutation and complete sentences; no slang, emojis or exclamation marks.",
                     "Anchor on the regulatory context the KB supports (RBI, DPDP Act) without claiming approval or certification.",
                     "Prefer outcomes an audit committee cares about (turnaround time, control, auditability) and a low-pressure CTA."],
    },
    "voice_ai_founder": {
        "label": "Founder-to-founder, casual, technical",
        "max_words": 80, "greeting": "Hey {first},", "signoff": "Cheers,",
        "banned": ["dear", "esteemed", "kindly", "hope this finds you well", "leverage", "synergy", "solutions",
                   "enterprise-grade", "cutting-edge", "world-class"],
        "no_emoji": True, "no_exclamation": False,
        "guidance": ["Talk in latency and completion-rate terms, not marketing terms.",
                     "Under 80 words; one specific technical hook; one direct question.",
                     "Sound like a builder writing to a builder; never sound like a template."],
    },
}
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def tone_prompt_block(campaign_id: str) -> str:
    p = TONE_PROFILES[campaign_id]
    rules = "\n".join(f"- {g}" for g in p["guidance"])
    return (f"TONE PROFILE ({p['label']}): greeting '{p['greeting']}', sign-off '{p['signoff']}', "
            f"max {p['max_words']} words.\n{rules}\nNever use: {', '.join(p['banned'])}.")


def tone_lint(campaign_id: str, body: str) -> list[Finding]:
    p = TONE_PROFILES.get(campaign_id)
    if not p:
        return []
    core, t = strip_footer(body), normalize(strip_footer(body))
    out = []
    if word_count(core) > p["max_words"]:
        out.append(Finding("tone", Verdict.REVISE, "too_long_for_audience", {"words": word_count(core), "max": p["max_words"]}))
    hits = [b for b in p["banned"] if re.search(rf"(?<![a-z]){re.escape(b)}(?![a-z])", t)]
    if hits:
        out.append(Finding("tone", Verdict.REVISE, "register_mismatch_phrase", {"phrases": hits}))
    if p["no_emoji"] and _EMOJI.search(core):
        out.append(Finding("tone", Verdict.REVISE, "emoji_not_allowed_for_audience"))
    if p["no_exclamation"] and "!" in core:
        out.append(Finding("tone", Verdict.REVISE, "exclamation_not_allowed_for_audience"))
    return out


# --------------------------------------------------------------------------- #
# 10. Circuit breakers: cost and reply loops
# --------------------------------------------------------------------------- #
class BudgetBreaker:
    """Kill-switch so an autonomous agent can never run away on cost."""

    def __init__(self, max_cost_per_lead: Optional[float] = None, max_total: Optional[float] = None):
        self.max_cost_per_lead = max_cost_per_lead if max_cost_per_lead is not None else float(os.getenv("SDR_MAX_COST_PER_LEAD", "0.05"))
        self.max_total = max_total if max_total is not None else float(os.getenv("SDR_MAX_TOTAL_USD", "25"))
        self._per_lead: dict[str, float] = {}
        self._total = 0.0
        self._lock = threading.Lock()

    def record(self, lead_id: str, cost_usd: float) -> None:
        with self._lock:
            self._per_lead[lead_id] = self._per_lead.get(lead_id, 0.0) + cost_usd
            self._total += cost_usd

    def check(self, lead_id: str, est_cost: float = 0.0) -> Optional[Finding]:
        with self._lock:
            lead, total = self._per_lead.get(lead_id, 0.0) + est_cost, self._total + est_cost
        if total > self.max_total:
            return Finding("budget", Verdict.BLOCK, "global_budget_exhausted", {"total_usd": round(total, 4)})
        if lead > self.max_cost_per_lead:
            return Finding("budget", Verdict.HOLD, "per_lead_cost_cap_exceeded", {"lead_usd": round(lead, 4)})
        return None


class ThreadLoopGuard:
    """Stops bot-to-bot ping-pong and runaway conversations."""

    def __init__(self, max_agent_turns: int = 6):
        self.max_agent_turns = max_agent_turns
        self._turns: dict[str, int] = {}

    def record_agent_turn(self, thread_id: str) -> None:
        self._turns[thread_id] = self._turns.get(thread_id, 0) + 1

    def check(self, thread_id: str, inbound_text: str = "") -> Optional[Finding]:
        if inbound_text and _AUTO_REPLY.search(normalize(inbound_text)):
            return Finding("loop_guard", Verdict.BLOCK, "auto_reply_do_not_answer")
        if self._turns.get(thread_id, 0) >= self.max_agent_turns:
            return Finding("loop_guard", Verdict.HOLD, "max_agent_turns_reached")
        return None


# --------------------------------------------------------------------------- #
# Orchestrators
# --------------------------------------------------------------------------- #
@dataclass
class OutboundContext:
    campaign_id: str
    channel: str                       # email | linkedin | sms | voice
    region: str                        # US | IN | OTHER
    prospect_id: str
    prospect_tz: Optional[str] = None  # IANA name, e.g. "America/New_York"
    prior_interactions: int = 0
    data_source: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    competitors: Optional[list[str]] = None
    identifiers: list[str] = field(default_factory=list)  # emails / phones / linkedin urls
    now: Optional[datetime] = None


def evaluate_outbound(subject: str, body: str, ctx: OutboundContext, *, suppression: Optional[SuppressionList] = None,
                      memory: Optional[TouchMemory] = None, breaker: Optional[BudgetBreaker] = None,
                      postal_address: Optional[str] = None) -> GateResult:
    """Policy Gate for every outbound touch. Order matters: hard stops first."""
    res = GateResult()
    text = f"{subject}\n{body}" if subject else body
    if suppression and suppression.is_suppressed(*ctx.identifiers):
        res.add(Finding("suppression", Verdict.BLOCK, "recipient_on_global_suppression_list"))
    res.extend(scan_leakage(text))
    res.extend(check_outbound_pii(text))
    res.extend(check_campaign_isolation(text, ctx.campaign_id))
    comps = ctx.competitors if ctx.competitors is not None else DEFAULT_COMPETITORS.get(ctx.campaign_id, [])
    evidence_text = "\n".join(ctx.evidence)
    res.extend(check_claims(text, evidence_text, comps, ctx.prior_interactions))
    res.extend(check_numeric_grounding(body, evidence_text))
    res.extend(tone_lint(ctx.campaign_id, body))
    if memory:
        res.extend(memory.check_repetition(ctx.prospect_id, body))
    if ctx.channel.lower() == "email":
        res.extend(check_email_compliance(subject, body, ctx.prior_interactions > 0, postal_address))
    res.add(check_data_provenance(ctx.region, ctx.data_source))
    if breaker:
        res.add(breaker.check(ctx.prospect_id))
    res.add(check_send_window(ctx.channel, ctx.region, ctx.prospect_tz, ctx.now))
    return res


def evaluate_inbound(text: str, *, thread_id: str = "", loop_guard: Optional[ThreadLoopGuard] = None) -> tuple[str, dict, GateResult]:
    """Sanitise + pre-classify an inbound reply BEFORE any LLM sees it.
    Returns (sanitised_text, precheck_result, gate_result)."""
    res = GateResult()
    clean, notes = sanitize_inbound(text)
    res.extend(notes)
    pre = precheck_inbound(clean)
    res.extend(pre["security"])
    if pre["definitive"] == "opt_out":
        res.add(Finding("opt_out", Verdict.BLOCK, "opt_out_detected_suppress_all_channels"))
    if pre["definitive"] == "auto_reply" and loop_guard:
        res.add(loop_guard.check(thread_id, clean))
    elif loop_guard and thread_id:
        res.add(loop_guard.check(thread_id))
    if "compliance_complaint" in pre["hints"]:
        res.add(Finding("complaint", Verdict.HOLD, "compliance_complaint_route_to_human"))
    return clean, pre, res
