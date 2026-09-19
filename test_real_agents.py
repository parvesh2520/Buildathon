"""
Real LLM Agent Test — Runs golden prospects through Gemini-powered pipeline.
"""
import sys
import json
import os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from llm_agents import SDRAgentPipeline

API_KEY = os.environ.get("GEMINI_API_KEY", "")


def banner(title):
    print(f"\n{'='*80}\n {title}\n{'='*80}")


def run_tests():
    if not API_KEY:
        print("ERROR: Set GEMINI_API_KEY environment variable")
        sys.exit(1)

    pipeline = SDRAgentPipeline(api_key=API_KEY)

    # Load golden test prospects
    with open("test_data/golden_prospects.json", "r", encoding="utf-8") as f:
        prospects = json.load(f)

    # ---------------------------------------------------------------
    # TEST 1: Full pipeline on ideal US SaaS CTO prospect (T01)
    # ---------------------------------------------------------------
    banner("TEST 1: Full Pipeline — Ideal US SaaS CTO (T01)")
    p = prospects[0]  # Jason Miller, VP Eng, CloudScale
    result = pipeline.run_full_pipeline(p, campaign_is_paused=False)

    print("\n📋 Timeline:")
    for step in result["timeline"]:
        print(f"  {step}")

    print(f"\n🏁 Final State: {result['final_state']}")
    print(f"\n📊 ICP Score: {result['icp_evaluation'].get('fit_score')}/100 ({result['icp_evaluation'].get('status')})")

    if result["draft"]:
        print(f"\n✉️  Subject: {result['draft'].get('subject_line')}")
        print(f"\n📝 Email Draft:\n---\n{result['draft'].get('content')}\n---")
        print(f"\n📎 Claims Made: {result['draft'].get('claims_made')}")
        print(f"📎 RAG Sources: {result['draft'].get('rag_sources_cited')}")

    # ---------------------------------------------------------------
    # TEST 2: Disqualified prospect (T02 — staffing agency)
    # ---------------------------------------------------------------
    banner("TEST 2: Disqualification — Staffing Agency (T02)")
    p2 = prospects[1]  # Sarah Jenkins, Recruiter, TalentBridge Agency
    result2 = pipeline.run_full_pipeline(p2, campaign_is_paused=False)

    print("\n📋 Timeline:")
    for step in result2["timeline"]:
        print(f"  {step}")

    print(f"\n🏁 Final State: {result2['final_state']}")
    print(f"📊 ICP Score: {result2['icp_evaluation'].get('fit_score')}/100 ({result2['icp_evaluation'].get('status')})")
    if result2['icp_evaluation'].get('negative_icp_triggers'):
        print(f"🚫 Negative Triggers: {result2['icp_evaluation']['negative_icp_triggers']}")

    # ---------------------------------------------------------------
    # TEST 3: India BFSI CIO prospect (T05) — paused campaign (Flow 3)
    # ---------------------------------------------------------------
    banner("TEST 3: Flow 3 — India BFSI CIO with Campaign Paused (T05)")
    p3 = prospects[4]  # Rajesh Subramanian, CIO, Apex Finance
    result3 = pipeline.run_full_pipeline(p3, campaign_is_paused=True)

    print("\n📋 Timeline:")
    for step in result3["timeline"]:
        print(f"  {step}")
    print(f"\n🏁 Final State: {result3['final_state']}")

    # ---------------------------------------------------------------
    # TEST 4: Conversation Agent — competitor objection reply (R02)
    # ---------------------------------------------------------------
    banner("TEST 4: Conversation Agent — Competitor Objection Reply")
    with open("test_data/golden_replies.json", "r", encoding="utf-8") as f:
        replies = json.load(f)

    reply = replies[1]  # "We already use Datadog..."
    conv_result = pipeline.run_conversation_classifier(
        prospect_id=reply["prospect_id"],
        reply_text=reply["reply_text"],
        campaign_id="us_saas_cto"
    )
    print(f"\n📨 Inbound: \"{reply['reply_text'][:80]}...\"")
    print(f"🏷️  Intent: {conv_result.get('intent')}")
    print(f"😊 Sentiment: {conv_result.get('sentiment')}")
    print(f"🔄 Escalate: {conv_result.get('escalate_to_human')}")
    print(f"\n💬 Suggested Reply:\n---\n{conv_result.get('suggested_reply')}\n---")

    # ---------------------------------------------------------------
    # TEST 5: Voice SDR Script for Voice AI Founder (T09)
    # ---------------------------------------------------------------
    banner("TEST 5: Voice SDR Agent — Cold Call Script")
    p5 = prospects[8]  # Devon Patel, Founder, VoiceBotics
    # Quick research first
    dossier5 = pipeline.run_research(p5)
    voice_result = pipeline.run_voice_script(p5, dossier5)
    print(f"\n🎤 Opening Hook:\n  \"{voice_result.get('opening_hook')}\"")
    print(f"\n❓ Qualifying Questions:")
    for q in voice_result.get("qualifying_questions", []):
        print(f"  • {q}")
    print(f"\n🛡️ Objection Rebuttals:")
    for obj, reb in voice_result.get("objection_rebuttals", {}).items():
        print(f"  [{obj}]: {reb}")
    print(f"\n🎯 Close: \"{voice_result.get('closing_ask')}\"")

    # ---------------------------------------------------------------
    # USAGE SUMMARY
    # ---------------------------------------------------------------
    banner("TOKEN USAGE SUMMARY")
    usage = pipeline.agent.get_usage_summary()
    print(f"  Total API Calls: {usage['total_api_calls']}")
    print(f"  Total Input Tokens: {usage['total_input_tokens']:,}")
    print(f"  Total Output Tokens: {usage['total_output_tokens']:,}")
    print(f"  Total Tokens: {usage['total_input_tokens'] + usage['total_output_tokens']:,}")


if __name__ == "__main__":
    run_tests()
