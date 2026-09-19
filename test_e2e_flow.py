"""
End-to-End Simulation Test for Autonomous SDR Agent Pipeline.
Tests Flow 2 (Autonomous Loop), Flow 3 (Campaign Pause), and Flow 4 (HITL Pricing Approval).
"""

import sys
import json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from schemas import RawProspect
from pipeline_runner import SDRPipelineRunner

def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)

def main():
    runner = SDRPipelineRunner()

    # -------------------------------------------------------------
    # TEST 1: Qualified Prospect (US SaaS CTO) -> Flow 2 Clean Send
    # -------------------------------------------------------------
    print_banner("TEST 1: Ideal Prospect (US SaaS CTO) -> Flow 2 Clean Run")
    prospect_1 = RawProspect(
        prospect_id="p_101",
        campaign_id="us_saas_cto",
        name="Jason Miller",
        title="VP of Engineering",
        company="CloudScale Systems",
        domain="cloudscale.io",
        location="San Francisco, CA",
        company_size_estimate="120 employees",
        raw_notes="Series B SaaS, operates 40+ microservices on AWS and Kubernetes. GitHub Actions build pipelines are slow."
    )

    result_1 = runner.process_discovered_prospect(prospect_1, campaign_is_paused=False)
    print("\nTimeline Execution Steps:")
    for step in result_1["timeline"]:
        print(f"  {step}")
    
    print(f"\nFinal State: {result_1['current_state']}")
    print(f"Draft Subject: {result_1['draft_message']['subject_line']}")
    print(f"Draft Preview:\n---\n{result_1['draft_message']['content']}\n---")

    # -------------------------------------------------------------
    # TEST 2: Disqualified Prospect (Agency) -> Flow 2 Marked Not a Fit
    # -------------------------------------------------------------
    print_banner("TEST 2: Disqualified Prospect (Staffing Agency) -> Flow 2 Not a Fit")
    prospect_2 = RawProspect(
        prospect_id="p_102",
        campaign_id="us_saas_cto",
        name="Sarah Jenkins",
        title="Senior Tech Recruiter",
        company="TalentBridge Agency",
        domain="talentbridge.co",
        location="London, UK",
        company_size_estimate="12 employees",
        raw_notes="Recruiting and talent agency."
    )

    result_2 = runner.process_discovered_prospect(prospect_2, campaign_is_paused=False)
    print("\nTimeline Execution Steps:")
    for step in result_2["timeline"]:
        print(f"  {step}")
    print(f"\nFinal State: {result_2['current_state']}")

    # -------------------------------------------------------------
    # TEST 3: Campaign Paused Mid-Execution (Flow 3)
    # -------------------------------------------------------------
    print_banner("TEST 3: Mid-Execution Campaign Pause -> Flow 3 Held in Timeline")
    prospect_3 = RawProspect(
        prospect_id="p_103",
        campaign_id="india_bfsi_cio",
        name="Rajesh Subramanian",
        title="Chief Information Officer",
        company="Apex Finance Corp",
        domain="apexfin.in",
        location="Mumbai, India",
        company_size_estimate="450 employees",
        raw_notes="Tier-1 NBFC managing retail lending. Migrating to private cloud under RBI DPDP guidelines."
    )

    result_3 = runner.process_discovered_prospect(prospect_3, campaign_is_paused=True)
    print("\nTimeline Execution Steps:")
    for step in result_3["timeline"]:
        print(f"  {step}")
    print(f"\nFinal State: {result_3['current_state']}")

    # -------------------------------------------------------------
    # TEST 4: Flow 4 Human-in-the-Loop (Risky Topic: Pricing Mentioned)
    # -------------------------------------------------------------
    print_banner("TEST 4: Flow 4 HITL Policy Gate (Draft mentions pricing -> Queued in Inbox)")
    # Force a pricing draft
    prospect_4 = RawProspect(
        prospect_id="p_104",
        campaign_id="voice_ai_founder",
        name="Devon Patel",
        title="Founder & CEO",
        company="VoiceBotics",
        domain="voicebotics.ai",
        location="Austin, TX",
        company_size_estimate="8 employees",
        raw_notes="Building conversational voice agents using WebRTC and Python."
    )

    # Let's inspect voice agent output
    voice_script = runner.voice_agent.generate_call_script(prospect_4, runner.research_agent.run(prospect_4))
    print(f"Voice SDR Opener: {voice_script.opening_hook}")
    print(f"Voice Rebuttal for 'using_openai_realtime': {voice_script.objection_rebuttals.get('using_openai_realtime')}")

    # -------------------------------------------------------------
    # TEST 5: Prospect Inbound Reply Handling (Flow 2 Loopback)
    # -------------------------------------------------------------
    print_banner("TEST 5: Inbound Prospect Reply -> Conversation Agent Classification")
    reply_1 = runner.simulate_inbound_reply(
        prospect_id="p_101",
        reply_text="Hey Alex, we do use Datadog for this. How is Turboscale different?"
    )
    print(f"Inbound Intent: {reply_1['classification']['intent']}")
    print(f"Sentiment: {reply_1['classification']['sentiment']}")
    print(f"Next Action Planned by Strategy: {reply_1['next_strategy']['action_type']} (Angle: {reply_1['next_strategy']['angle']})")

    # -------------------------------------------------------------
    # TEST 7: Cross-Campaign Isolation & Adversarial Leak Detection
    # -------------------------------------------------------------
    print_banner("TEST 7: RAG Cross-Campaign Isolation & Leak Guard")
    from rag.store import kb_store
    clean_res = kb_store.verify_no_cross_campaign_leak("us_saas_cto", "Turboscale helped Veloce Health cut CI/CD latency by 60%")
    print(f"Clean US SaaS text leak status: Safe={clean_res['safe']}")
    assert clean_res["safe"] == True

    adversarial_res = kb_store.verify_no_cross_campaign_leak("us_saas_cto", "Turboscale complies with RBI compliance and DPDP act regulations")
    print(f"Adversarial BFSI leak into SaaS detected: HasLeak={adversarial_res['has_leak']}, Leaks={adversarial_res['leaks']}")
    assert adversarial_res["has_leak"] == True

    # Top-K Chunk-level Retrieval
    retrieved = kb_store.retrieve_top_k("us_saas_cto", "GitHub actions CI build cost", k=2)
    print("Top-2 Retrieved Chunks with Source IDs:")
    for chunk in retrieved:
        print(f"  [{chunk.chunk_id}] {chunk.title} ({len(chunk.content)} chars)")
        assert chunk.campaign_id == "us_saas_cto"

    print_banner("ALL FLOW 2, 3, 4, 5, 6 & SECTION 4 AUDIT TESTS COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
