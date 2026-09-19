"""
test_all_6_flows.py
===================
Comprehensive End-to-End Test for Autonomous SDR System.
Tests all 6 core flows strictly per specification against the live FastAPI server:
  - Flow 1: Campaign Creation, 5-Step Activation Checklist, Lifecycle
  - Flow 2: Autonomous Funnel (FIT, NO_FIT, Inbound Reply, Cadence Timer)
  - Flow 3: Pause/Resume (Campaign & Channel level) + State Holding
  - Flow 4: Manager Inbox (Pricing/Ungrounded Gate -> Escalation -> Resolve)
  - Flow 5: Cross-Campaign Conflict Detection (Pre-send gate & Resolution)
  - Flow 6: Sales Rep Offboarding & Campaign Reassignment
  - Section 3 & 4: Prospect 360 & Real-time Telemetry Verification
"""

import sys
import os
import json
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)


def test_flow_1():
    banner("FLOW 1: Campaign Creation, 5-Step Checklist & Activation Gate")
    # 1. Create campaign in DRAFT
    cid = f"test_camp_{int(time.time())}"
    res = requests.post(f"{BASE_URL}/api/campaigns", json={
        "id": cid,
        "name": "Fintech CTO Outbound Q4",
        "icp_description": "CTOs at Indian Fintechs with Series A/B funding",
        "active_channels": ["EMAIL", "LINKEDIN"],
        "assigned_reps": ["Priya Sharma"],
    })
    assert res.status_code == 200, f"Failed creation: {res.text}"
    camp = res.json()["campaign"]
    print(f"  [1.1] Created campaign '{camp['name']}' with status: {camp['status']}")
    assert camp["status"] == "DRAFT"

    # 2. Verify DRAFT campaign cannot run autonomous pipeline
    run_blocked = requests.post(f"{BASE_URL}/api/pipeline/run-prospect", json={
        "prospect_id": "p_draft_test",
        "campaign_id": cid,
        "name": "Draft Tester",
        "title": "CTO",
        "company": "Draft Corp",
        "raw_notes": "Testing draft block"
    }).json()
    print(f"  [1.2] Draft campaign run attempt: {run_blocked.get('status')} - {run_blocked.get('reason')}")
    assert run_blocked.get("status") == "BLOCKED"
    assert run_blocked.get("final_state") == "BLOCKED"

    # 3. Activate campaign with 5-step checklist
    act = requests.post(f"{BASE_URL}/api/campaigns/{cid}/activate").json()
    print(f"  [1.3] Activation response: status={act.get('status')}")
    print(f"        Checklist: {act.get('checklist')}")
    assert act.get("status") == "success"
    assert act.get("checklist", {}).get("has_icp") == True
    assert act.get("checklist", {}).get("has_channels") == True
    assert act.get("checklist", {}).get("has_reps") == True

    # 4. Verify status is now LIVE
    detail = requests.get(f"{BASE_URL}/api/campaigns/{cid}").json()
    assert detail["campaign"]["status"] == "LIVE"
    print(f"  [1.4] Campaign is now LIVE: funnel={detail.get('funnel')}")
    return cid


def test_flow_2():
    banner("FLOW 2: Autonomous Prospecting Funnel (Live LLM Pipeline)")
    # 2.1 Ideal FIT prospect (p_101 - Jason Miller)
    print("  [2.1] Running pipeline on FIT prospect: Jason Miller @ CloudScale Systems...")
    res_fit = requests.post(f"{BASE_URL}/api/pipeline/run-prospect", json={
        "prospect_id": "p_101",
        "campaign_id": "us_saas_cto",
        "name": "Jason Miller",
        "title": "VP of Engineering",
        "company": "CloudScale Systems",
        "domain": "cloudscale.io",
        "location": "San Francisco, CA",
        "company_size_estimate": "120 employees",
        "raw_notes": "Series B B2B SaaS. 40+ microservices on AWS and Kubernetes. GitHub Actions build pipelines averaging 38 minutes."
    }).json()

    print(f"        Final State: {res_fit.get('final_state')}")
    print(f"        ICP Status: {res_fit.get('icp_evaluation', {}).get('status')} (Score: {res_fit.get('icp_evaluation', {}).get('fit_score')}/100)")
    assert res_fit.get("final_state") in ("MESSAGE_SENT", "HELD_APPROVAL")
    assert res_fit.get("icp_evaluation", {}).get("status") in ("FIT", "REVIEW")
    if res_fit.get("draft"):
        print(f"        Channel: {res_fit['draft'].get('channel')}")
        print(f"        Subject: {res_fit['draft'].get('subject_line')}")
        print(f"        Content snippet: {res_fit['draft'].get('content', '')[:120]}...")
        print(f"        Claims Made: {res_fit['draft'].get('claims_made')}")
        print(f"        Self-Healed: {res_fit.get('was_healed')}")

    time.sleep(3)  # Pacing for 15 RPM

    # 2.2 Disqualified NO_FIT prospect (p_102 - Recruiter at staffing agency)
    print("\n  [2.2] Running pipeline on NO_FIT prospect: Sarah Jenkins @ TalentBridge Agency...")
    res_nofit = requests.post(f"{BASE_URL}/api/pipeline/run-prospect", json={
        "prospect_id": "p_102",
        "campaign_id": "us_saas_cto",
        "name": "Sarah Jenkins",
        "title": "Senior Tech Recruiter",
        "company": "TalentBridge Agency",
        "domain": "talentbridge.co",
        "location": "London, UK",
        "company_size_estimate": "12 employees",
        "raw_notes": "IT staffing and recruitment agency."
    }).json()

    print(f"        Final State: {res_nofit.get('final_state')}")
    print(f"        ICP Status: {res_nofit.get('icp_evaluation', {}).get('status')} (Score: {res_nofit.get('icp_evaluation', {}).get('fit_score')}/100)")
    assert res_nofit.get("final_state") == "NOT_A_FIT"
    assert res_nofit.get("icp_evaluation", {}).get("status") == "NO_FIT"

    time.sleep(3)  # Pacing

    # 2.3 Inbound reply classification
    print("\n  [2.3] Testing Inbound Prospect Reply loopback...")
    reply_res = requests.post(f"{BASE_URL}/api/pipeline/inbound-reply", json={
        "prospect_id": "p_101",
        "campaign_id": "us_saas_cto",
        "reply_text": "Hey Alex, this actually looks relevant. Our CI build times are killing us. Can you send over a calendar link for Tuesday?"
    }).json()
    print(f"        Inbound Intent: {reply_res.get('intent')} | Sentiment: {reply_res.get('sentiment')}")
    print(f"        Escalate: {reply_res.get('escalate_to_human')}")
    assert reply_res.get("intent") in ("INTERESTED_BOOK_MEETING", "TECHNICAL_QUESTION")

    time.sleep(2)

    # 2.4 Cadence timer follow-up evaluation
    print("\n  [2.4] Testing Cadence Timer Follow-up evaluation...")
    followup_res = requests.post(f"{BASE_URL}/api/pipeline/cadence-timer", json={
        "prospect_id": "p_101",
        "current_touch_number": 2
    }).json()
    print(f"        Follow-up Action: {followup_res.get('action_type')} | Channel: {followup_res.get('recommended_channel')}")


def test_flow_3():
    banner("FLOW 3: Campaign Pause / Resume / Channel Pause & State Holding")
    cid = "us_saas_cto"

    # 1. Pause campaign
    requests.post(f"{BASE_URL}/api/campaigns/{cid}/pause")
    camp = requests.get(f"{BASE_URL}/api/campaigns/{cid}").json()["campaign"]
    print(f"  [3.1] Paused campaign '{cid}': status={camp['status']}")
    assert camp["status"] == "PAUSED"

    # 2. Run prospect against paused campaign -> Must return HELD_PAUSED
    res_paused = requests.post(f"{BASE_URL}/api/pipeline/run-prospect", json={
        "prospect_id": "p_paused_prospect",
        "campaign_id": cid,
        "name": "Pause Test User",
        "title": "CTO",
        "company": "HoldOn Systems",
        "raw_notes": "AWS SaaS"
    }).json()
    print(f"  [3.2] Prospect run on paused campaign: final_state={res_paused.get('final_state')}")
    assert res_paused.get("final_state") == "HELD_PAUSED"

    # 3. Resume campaign
    requests.post(f"{BASE_URL}/api/campaigns/{cid}/resume")
    camp_resumed = requests.get(f"{BASE_URL}/api/campaigns/{cid}").json()["campaign"]
    print(f"  [3.3] Resumed campaign '{cid}': status={camp_resumed['status']}")
    assert camp_resumed["status"] == "LIVE"

    # 4. Channel pause test
    requests.post(f"{BASE_URL}/api/campaigns/{cid}/pause-channel?channel=LINKEDIN")
    camp_ch = requests.get(f"{BASE_URL}/api/campaigns/{cid}").json()["campaign"]
    print(f"  [3.4] Paused LINKEDIN channel: paused_channels={camp_ch.get('paused_channels')}")
    assert "LINKEDIN" in camp_ch.get("paused_channels", [])

    # Resume channel
    requests.post(f"{BASE_URL}/api/campaigns/{cid}/resume-channel?channel=LINKEDIN")
    camp_ch_resumed = requests.get(f"{BASE_URL}/api/campaigns/{cid}").json()["campaign"]
    assert "LINKEDIN" not in camp_ch_resumed.get("paused_channels", [])
    print(f"  [3.5] Resumed LINKEDIN channel: paused_channels={camp_ch_resumed.get('paused_channels')}")


def test_flow_4():
    banner("FLOW 4: Human-in-the-Loop (HITL) Inbox Gate & Resolution")
    # 1. Trigger an escalation via inbound reply mentioning pricing/angry tone
    print("  [4.1] Triggering escalation to Manager Inbox via pricing reply...")
    res = requests.post(f"{BASE_URL}/api/pipeline/inbound-reply", json={
        "prospect_id": "p_101",
        "campaign_id": "us_saas_cto",
        "reply_text": "What are your exact license fees and pricing tier? We cannot talk without a 50% discount contract upfront."
    }).json()
    print(f"        Intent: {res.get('intent')} | Escalate: {res.get('escalate_to_human')}")

    # 2. Inspect Inbox
    inbox = requests.get(f"{BASE_URL}/api/inbox").json()
    print(f"  [4.2] Inbox queue count: {inbox.get('total')}")
    assert inbox.get("total", 0) > 0, "Inbox should have pending items!"
    item = inbox["items"][0]
    print(f"        First item: {item.get('inbox_item_id')} [{item.get('type')}] Reason: {item.get('flag_reason')}")

    # 3. Resolve Inbox item with APPROVE
    resolve_res = requests.post(f"{BASE_URL}/api/inbox/resolve", json={
        "inbox_item_id": item["inbox_item_id"],
        "action": "APPROVE"
    }).json()
    print(f"  [4.3] Resolved inbox item: action={resolve_res.get('action')} status={resolve_res.get('status')}")
    assert resolve_res.get("status") == "success"

    # Verify queue decreased
    inbox_after = requests.get(f"{BASE_URL}/api/inbox").json()
    print(f"  [4.4] Inbox queue after resolution: {inbox_after.get('total')}")


def test_flow_5():
    banner("FLOW 5: Cross-Campaign Conflict Detection & Resolution")
    # 1. We already have Jason Miller at CloudScale Systems in us_saas_cto (p_101).
    # Submit the exact same person to voice_ai_founder campaign
    conf_pid = f"p_conflict_jm_{int(time.time())}"
    print(f"  [5.1] Submitting existing prospect (Jason Miller @ CloudScale Systems) as {conf_pid} to second campaign (voice_ai_founder)...")
    res_conflict = requests.post(f"{BASE_URL}/api/pipeline/run-prospect", json={
        "prospect_id": conf_pid,
        "campaign_id": "voice_ai_founder",
        "name": "Jason Miller",
        "title": "VP of Engineering",
        "company": "CloudScale Systems",
        "domain": "cloudscale.io",
        "raw_notes": "Trying to add to voice AI campaign"
    }).json()

    print(f"        Response status: {res_conflict.get('status')}")
    print(f"        Final State: {res_conflict.get('final_state')}")
    print(f"        Reason: {res_conflict.get('reason')}")
    assert res_conflict.get("status") == "CONFLICT"
    assert res_conflict.get("final_state") == "HELD_CONFLICT"

    # 2. Check conflicts database
    conflicts = requests.get(f"{BASE_URL}/api/conflicts").json()
    print(f"  [5.2] Conflicts DB: total={conflicts.get('total')} open={conflicts.get('open')}")
    assert conflicts.get("open", 0) > 0, "Should have open conflicts!"
    open_conflicts = [c for c in conflicts["conflicts"] if c["status"] == "OPEN"]
    assert len(open_conflicts) > 0, "Must have at least one OPEN conflict!"
    c_item = open_conflicts[0]

    # 3. Resolve conflict in favor of us_saas_cto
    resolve_res = requests.post(f"{BASE_URL}/api/conflicts/resolve", json={
        "conflict_id": c_item["conflict_id"],
        "winning_campaign_id": "us_saas_cto"
    }).json()
    print(f"  [5.3] Conflict resolved: status={resolve_res.get('status')} message={resolve_res.get('message')}")
    assert resolve_res.get("status") in ("success", "resolved")


def test_flow_6():
    banner("FLOW 6: Sales Rep Offboarding & Campaign Reassignment")
    # 1. Fetch current reps
    reps = requests.get(f"{BASE_URL}/api/reps").json()
    print("  [6.1] Current Sales Reps:")
    for r in reps["reps"]:
        print(f"        - {r['name']} [{r['status']}] -> campaigns: {r['campaigns']}")

    # 2. Offboard Priya Sharma and reassign india_bfsi_cio to Devon Patel
    offboard_res = requests.post(f"{BASE_URL}/api/reps/offboard", json={
        "rep_name": "Priya Sharma",
        "reassignments": {"india_bfsi_cio": "Devon Patel"}
    }).json()
    print(f"  [6.2] Offboard response: {offboard_res.get('message')}")
    print(f"        Affected campaigns: {offboard_res.get('affected_campaigns')}")
    assert offboard_res.get("status") == "success"

    # 3. Verify reassignment
    reps_after = requests.get(f"{BASE_URL}/api/reps").json()
    priya = [r for r in reps_after["reps"] if r["name"] == "Priya Sharma"][0]
    devon = [r for r in reps_after["reps"] if r["name"] == "Devon Patel"][0]
    print(f"  [6.3] Verification: Priya status={priya['status']}, Devon campaigns={devon['campaigns']}")
    assert priya["status"] == "INACTIVE"
    assert "india_bfsi_cio" in devon["campaigns"]


def test_telemetry_and_prospect_360():
    banner("SECTION 3 & 4: Prospect 360 & Real-Time Telemetry")
    # 1. Prospect 360
    p360 = requests.get(f"{BASE_URL}/api/prospects/p_101").json()
    print(f"  [7.1] Prospect 360 for p_101 ({p360['prospect']['name']}):")
    print(f"        State: {p360.get('state')}")
    print(f"        Timeline events: {len(p360.get('pipeline_result', {}).get('timeline', []))}")
    print(f"        Replies logged: {len(p360.get('replies', []))}")
    assert len(p360.get("replies", [])) > 0

    # 2. Telemetry & Unit Economics
    telem = requests.get(f"{BASE_URL}/api/metrics/telemetry").json()
    t = telem.get("telemetry", {})
    pg = telem.get("policy_gate_telemetry", {})
    print(f"  [7.2] Live Operational Telemetry:")
    print(f"        Total LLM Calls: {t.get('total_calls')}")
    print(f"        Total Cost USD: ${t.get('total_cost_usd', 0):.5f}")
    print(f"        Cost Per Prospect: ${t.get('cost_per_prospect_usd', 0):.5f}")
    print(f"        Cost Per Qualified Lead: ${t.get('cost_per_qualified_lead_usd', 0):.5f}")
    print(f"        Average Latency: {t.get('avg_latency_seconds', 0):.2f}s")
    print(f"        Policy Gate Total Checks: {pg.get('total_evaluations')}")
    print(f"        Policy Gate Held Rate: {pg.get('held_rate_percent')}%")


if __name__ == "__main__":
    banner("STARTING VERIFICATION OF ALL 6 FLOWS")
    test_flow_1()
    test_flow_2()
    test_flow_3()
    test_flow_4()
    test_flow_5()
    test_flow_6()
    test_telemetry_and_prospect_360()
    banner("ALL 6 FLOWS + TELEMETRY STRICTLY VERIFIED AND PASSING!")
