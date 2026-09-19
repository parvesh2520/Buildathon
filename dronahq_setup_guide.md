# DronaHQ Setup Guide — 7 Agents + REST Connector

## Step 1: Create the 7 Specialized Agents

Go to **agents.dronahq.com** → **Agents** → **New Agent** for each:

### Agent 1: SDR Research Agent
- **Name**: `SDR Research Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/01_research_agent.md`
- **Knowledge Base**: None needed (research doesn't need product KB)
- **Structured Output**: Enable, paste this schema:
```json
{
  "prospect_id": "string",
  "prospect_summary": "string",
  "detected_tech_stack": ["string"],
  "observed_pain_points": ["string"],
  "personalisation_hooks": ["string"],
  "company_initiatives": ["string"]
}
```

### Agent 2: SDR ICP Fitment Agent
- **Name**: `SDR ICP Fitment Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/02_icp_fitment_agent.md`
- **Knowledge Base**: Attach all 3 KBs (ICP criteria are in the KBs)
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "fit_score": "integer (0-100)",
  "status": "FIT | REVIEW | NO_FIT",
  "matched_criteria": ["string"],
  "unmatched_criteria": ["string"],
  "reasoning": "string"
}
```

### Agent 3: SDR Strategy Agent
- **Name**: `SDR Strategy Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/03_strategy_agent.md`
- **Knowledge Base**: Attach all 3 KBs
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "trigger_source": "ICP_QUALIFIED | REPLY_RECEIVED | TIMER_FIRED | MANAGER_REJECTED",
  "recommended_channel": "EMAIL | LINKEDIN | SMS | PHONE",
  "action_type": "NEW_OUTREACH | REPLY | FOLLOW_UP | ESCALATE_HUMAN | CLOSE_CADENCE",
  "angle": "string",
  "tone": "PEER_ENGINEER | EXECUTIVE | CONCISE | CASUAL",
  "instructions_for_copywriter": "string",
  "suggested_wait_days": "integer"
}
```

### Agent 4: SDR Personalisation Agent
- **Name**: `SDR Personalisation Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/04_personalisation_agent.md`
- **Knowledge Base**: Attach all 3 KBs (for grounding claims)
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "channel": "EMAIL | LINKEDIN | SMS | PHONE",
  "subject_line": "string or null",
  "content": "string",
  "rag_sources_cited": ["string"],
  "claims_made": ["string"],
  "mentions_pricing": "boolean",
  "confidence_score": "float (0-1)"
}
```

### Agent 5: SDR Conversation Agent
- **Name**: `SDR Conversation Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/05_conversation_agent.md`
- **Knowledge Base**: Attach all 3 KBs
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "inbound_message": "string",
  "intent": "INTERESTED_BOOK_MEETING | TECHNICAL_QUESTION | OBJECTION_PRICING | OBJECTION_COMPETITOR | OBJECTION_NO_TIME | NOT_INTERESTED | OUT_OF_OFFICE | UNSUBSCRIBE",
  "sentiment": "POSITIVE | NEUTRAL | NEGATIVE",
  "escalate_to_human": "boolean",
  "extracted_notes": "string"
}
```

### Agent 6: SDR Follow-up Agent
- **Name**: `SDR Follow-up Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/06_follow_up_agent.md`
- **Knowledge Base**: None needed
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "touch_number": "integer",
  "max_allowed_touches": "integer",
  "should_follow_up": "boolean",
  "recommended_channel_pivot": "EMAIL | LINKEDIN | SMS | null",
  "follow_up_angle": "string",
  "is_final_breakup": "boolean",
  "reason": "string"
}
```

### Agent 7: SDR Voice Agent
- **Name**: `SDR Voice Agent`
- **Model**: `gpt-4o-mini`
- **System Prompt**: Copy FULL contents of `prompts/07_voice_sdr_agent.md`
- **Knowledge Base**: Attach all 3 KBs
- **Structured Output**:
```json
{
  "prospect_id": "string",
  "opening_hook": "string",
  "qualifying_questions": ["string"],
  "objection_rebuttals": {"objection": "rebuttal"},
  "closing_ask": "string"
}
```

---

## Step 2: Test Each Agent in Playground

For each agent, go to **Playground** and paste one of these test messages:

**Research Agent test:**
```
Research this prospect:
- Name: Jason Miller
- Title: VP of Engineering
- Company: CloudScale
- Domain: cloudscale.io
- Location: San Francisco, CA
- Company Size: 120 employees
- Notes: Recently raised Series B, migrating to Kubernetes
```

**ICP Fitment test:**
```
Campaign: us_saas_cto
Evaluate: Jason Miller, VP Engineering at CloudScale (120 emp, SF, AWS/K8s, Series B)
Research shows: Docker, K8s, CI/CD pipeline issues, 42-person eng team
```

**Conversation Agent test:**
```
Classify this reply from prospect P001:
"Interesting, but we're currently evaluating Datadog for this. What makes you different?"
```

---

## Step 3: Set Up Voice Agent (DronaHQ Voice)

1. Go to **Voice > Agents** on DronaHQ
2. Create a new voice agent
3. Paste the system prompt from `prompts/07_voice_sdr_agent.md`
4. Attach `kb_us_saas_cto` knowledge base
5. Configure voice settings (ElevenLabs or Deepgram)
6. Test in the voice playground

---

## Step 4: Set Up REST API Connector

1. Go to **DronaHQ Apps Studio** → **Connectors** → **Add Connector** → **REST API**
2. **Name**: `SDR Backend API`
3. **Base URL**: Your deployed backend URL (e.g., `https://your-app.railway.app` or your ngrok URL)
4. **Authentication**: None (or add API key if you add one later)

### Configure these endpoints as queries:

| Query Name | Method | Path | Description |
|---|---|---|---|
| `getDashboard` | GET | `/api/dashboard-summary` | Mission Control data |
| `getCampaigns` | GET | `/api/campaigns` | All campaigns |
| `getCampaignDetail` | GET | `/api/campaigns/{{campaign_id}}` | Single campaign detail |
| `createCampaign` | POST | `/api/campaigns` | Create new campaign |
| `activateCampaign` | POST | `/api/campaigns/{{campaign_id}}/activate` | Activate draft |
| `pauseCampaign` | POST | `/api/campaigns/{{campaign_id}}/pause` | Pause campaign |
| `resumeCampaign` | POST | `/api/campaigns/{{campaign_id}}/resume` | Resume campaign |
| `runPipeline` | POST | `/api/pipeline/run-prospect` | Run full agent pipeline |
| `getInbox` | GET | `/api/inbox` | HITL inbox items |
| `resolveInbox` | POST | `/api/inbox/resolve` | Approve/Edit/Reject |
| `getProspect` | GET | `/api/prospects/{{prospect_id}}` | Prospect 360 timeline |
| `listProspects` | GET | `/api/prospects` | All prospects |
| `getConflicts` | GET | `/api/conflicts` | Cross-campaign conflicts |
| `resolveConflict` | POST | `/api/conflicts/resolve` | Resolve conflict |
| `getReps` | GET | `/api/reps` | All reps |
| `offboardRep` | POST | `/api/reps/offboard` | Offboard a rep |
| `killSwitch` | POST | `/api/system/kill-switch?enable={{enable}}` | Emergency stop |
| `voiceScript` | POST | `/api/pipeline/voice-script` | Generate call script |
| `healthCheck` | GET | `/api/health` | System health |

---

## Step 5: Build the DronaHQ UI Screens

### Screen 1: Mission Control Dashboard
- **Data source**: `getDashboard` query
- **Layout**:
  - Top bar: Global Kill Switch toggle + Inbox badge count
  - 3 campaign cards (use Table Grid or Card List)
  - Each card shows: Name, Status badge (🟢/🟠/🔴), channels, reps, funnel metrics
  - Pause/Resume button per card
  - "New Campaign" button → navigates to wizard

### Screen 2: Campaign Wizard (Flow 1)
- **Multi-step form** (use DronaHQ's Stepper component):
  - Step 1: Campaign name + ID
  - Step 2: ICP description
  - Step 3: Select channels (checkboxes: EMAIL, LINKEDIN, SMS, PHONE)
  - Step 4: Assign reps (dropdown from `getReps`)
  - Step 5: Review + Pre-launch checklist
- Submit → `createCampaign` → then `activateCampaign`

### Screen 3: Pipeline Runner (Flow 2 Demo)
- **Form**: Prospect name, title, company, domain, location, campaign dropdown
- **Button**: "Run Pipeline"
- **Output**: Timeline display showing each agent step
- Data source: `runPipeline`

### Screen 4: Manager Inbox (Flow 4 & 5)
- **Data source**: `getInbox` query
- **Cards** for each held item:
  - Type: APPROVAL (pricing flag) or CONFLICT (cross-campaign)
  - Show: prospect name, company, channel, draft text, flag reason
  - Buttons: Approve / Edit / Reject
- Bind buttons to `resolveInbox`

### Screen 5: Prospect 360 (optional)
- **Input**: prospect_id search
- **Output**: Full timeline from `getProspect`

---

## Credit Budget Strategy

| Activity | Estimated Credits | Priority |
|---|---|---|
| Creating 7 agents (config only) | 0 | Must do |
| Testing each agent in Playground (7 × 2 tests) | ~28 | Must do |
| Running UI demo flows (10 pipeline runs) | ~100 | Must do |
| Voice agent testing | ~50 | Should do |
| Judge testing / live demo | ~200 | Reserve |
| Buffer | ~400 | Safety margin |
| **Total budget** | **~800** | |
