"""Quick test of all new API endpoints."""
import requests
import json

BASE = "http://localhost:8000"

def test_dashboard():
    r = requests.get(f"{BASE}/api/dashboard-summary")
    data = r.json()
    print("=== Dashboard Summary ===")
    print(f"Campaigns: {len(data['campaigns'])}")
    for c in data["campaigns"]:
        print(f"  - {c['name']} [{c['status']}] channels={c['active_channels']} reps={c['assigned_reps']}")
    print(f"Inbox: {data['inbox_count']}")
    print(f"Conflicts: {data['conflicts_open']}")
    print()

def test_campaign_crud():
    print("=== Flow 1: Campaign CRUD ===")
    # Create
    r = requests.post(f"{BASE}/api/campaigns", json={
        "id": "test_flow1",
        "name": "Test Flow 1 Campaign",
        "icp_description": "CTOs at Series A startups",
        "active_channels": ["EMAIL", "LINKEDIN"],
        "assigned_reps": ["Alex Rivera"],
    })
    print(f"Create: {r.json()['status']} | Status: {r.json()['campaign']['status']}")

    # Activate
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/activate")
    print(f"Activate: {r.json()['status']} | Checklist: {r.json().get('checklist')}")

    # Detail
    r = requests.get(f"{BASE}/api/campaigns/test_flow1")
    print(f"Detail funnel: {r.json()['funnel']}")

    # Pause
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/pause")
    print(f"Pause: {r.json()['campaign']['status']}")

    # Resume
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/resume")
    print(f"Resume: {r.json()['campaign']['status']}")

    # Channel pause
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/pause-channel?channel=EMAIL")
    print(f"Pause EMAIL: {r.json()['paused_channels']}")

    # Agent pause
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/pause-agent?agent_name=research")
    print(f"Pause research agent: {r.json()['paused_agents']}")

    # Archive
    r = requests.post(f"{BASE}/api/campaigns/test_flow1/archive")
    print(f"Archive: {r.json()['campaign']['status']}")
    print()

def test_reps():
    print("=== Flow 6: Rep Management ===")
    r = requests.get(f"{BASE}/api/reps")
    for rep in r.json()["reps"]:
        print(f"  {rep['name']} [{rep['status']}] -> {rep['campaigns']}")

    # Offboard Alex Rivera, reassign to "Jordan Lee"
    r = requests.post(f"{BASE}/api/reps/offboard", json={
        "rep_name": "Alex Rivera",
        "reassignments": {"us_saas_cto": "Jordan Lee"},
    })
    print(f"Offboard: {r.json()['message']}")
    print(f"Affected: {r.json()['affected_campaigns']}")

    # Verify new state
    r = requests.get(f"{BASE}/api/reps")
    for rep in r.json()["reps"]:
        print(f"  After: {rep['name']} [{rep['status']}] -> {rep['campaigns']}")
    print()

def test_conflicts():
    print("=== Flow 5: Conflict Detection ===")
    r = requests.get(f"{BASE}/api/conflicts")
    print(f"Conflicts: {r.json()['total']} total, {r.json()['open']} open")
    print()

def test_health():
    print("=== Health Check ===")
    r = requests.get(f"{BASE}/api/health")
    print(json.dumps(r.json(), indent=2))
    print()

if __name__ == "__main__":
    test_dashboard()
    test_campaign_crud()
    test_reps()
    test_conflicts()
    test_health()
    print("✅ All endpoint tests passed!")
