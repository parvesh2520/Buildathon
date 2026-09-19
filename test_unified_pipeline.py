"""Test script for upgraded pipeline with unified state, telemetry, and self-healing."""
import os
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from llm_agents import SDRAgentPipeline

print("Initializing pipeline...", flush=True)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
pipe = SDRAgentPipeline(api_key=GEMINI_API_KEY)

prospect = {
    'prospect_id': 'P001',
    'campaign_id': 'us_saas_cto',
    'name': 'Jason Miller',
    'title': 'VP of Engineering',
    'company': 'CloudScale Systems',
    'domain': 'cloudscale.io',
    'location': 'San Francisco, CA',
    'company_size_estimate': '120 employees',
    'raw_notes': 'Series B SaaS on AWS/K8s, slow CI/CD build queues'
}

print("Running full pipeline...", flush=True)
res = pipe.run_full_pipeline(prospect)

print(f"Final State: {res['final_state']}", flush=True)
print(f"Was Healed: {res['was_healed']}", flush=True)
print(f"Timeline Events: {len(res['timeline'])}", flush=True)
for ev in res['timeline']:
    print(f"  - {ev}", flush=True)

state = res['unified_state']
print(f"\nUnified Rep: {state['rep_persona']['rep_name']} ({state['rep_persona']['rep_title']})", flush=True)
print(f"Touchpoints Recorded: {len(state['interaction_history'])}", flush=True)
print(f"Cadence Touches Count: {state['cadence']['touches_count']}", flush=True)
print(f"Rolling Context: {pipe.get_or_create_state('P001', 'us_saas_cto').rolling_context_summary()}", flush=True)

print("\nTelemetry Report:", flush=True)
import json
print(json.dumps(pipe.get_telemetry_report(), indent=2), flush=True)
print("\nTest completed successfully!", flush=True)
