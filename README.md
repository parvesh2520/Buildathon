# Autonomous SDR Intelligence Engine & Control Plane

> **Inter Guild Buildathon 2026 — Tech Contingent IIT Madras × DronaHQ**  
> *Theme: Multi-Channel Autonomous Sales Development Representative (SDR)*

An enterprise-grade, multi-agent GTM execution engine built with **DronaHQ** as the control plane and a custom **Python/FastAPI orchestration layer** backed by LLMs, zero-hallucination numeric guardrails, and real-time telemetry.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DRONAHQ CONTROL PLANE (UI)                            │
│  - Mission Control: 3 Concurrent Campaigns (US SaaS, India BFSI, Voice AI)  │
│  - Flow 4 Manager Inbox (Approve / Edit / Reject flagged drafts)            │
│  - DronaHQ Voice Studio (Autonomous Voice SDR with ElevenLabs TTS)          │
│  - DronaHQ Knowledge Bases (RAG Collections with vector embeddings)         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST Connector
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOM BACKEND ORCHESTRATOR (FastAPI)                    │
│                                                                             │
│  [Prospect Discovered]                                                      │
│         │                                                                   │
│         ▼                                                                   │
│  1. SDR Research Agent (Enriches prospect tech stack & pain points)         │
│         │                                                                   │
│         ▼                                                                   │
│  2. SDR ICP Fitment Agent (Scores 0-100; FIT, REVIEW, or NO_FIT)            │
│         │                                                                   │
│         ├── (NO_FIT) ──► Pipeline halted; removed from funnel               │
│         ▼                                                                   │
│  3. SDR Outreach Strategy Agent (Multi-trigger: Inbound, Timer, ICP)        │
│         │                                                                   │
│         ▼                                                                   │
│  4. SDR Personalisation Agent (Drafts channel-specific copy: Email/LI/SMS)  │
│         │                                                                   │
│         ▼                                                                   │
│  5. Zero-Hallucination Grounding Checker (Regex + RAG fact verification)    │
│         │                                                                   │
│         ▼                                                                   │
│  6. Policy Gate (Flow 3 pause enforcement + Flow 4 HITL pricing detector)   │
│         │                                                                   │
│         ├── (Blocked) ──► Held in Manager Inbox / Timeline                  │
│         ▼                                                                   │
│  [Message Dispatched]                                                       │
│         │                                                                   │
│         ├── [Prospect Replies] ──► 7. SDR Conversation Agent (Classifies)  │
│         └── [Timer Fires]      ──► 8. SDR Follow-up Agent (Cadence logic)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Capabilities

1. **Multi-Channel Orchestration**: Coordinated outreach across Email, LinkedIn connection notes, SMS, and outbound AI Voice calling (ElevenLabs Turbo v2.5).
2. **3 Concurrent Campaigns**:
   - `us_saas_cto`: Turboscale AI (CI/CD build optimization for US CTOs on AWS/K8s)
   - `india_bfsi_cio`: FinShield AI (RBI-compliant lending automation & data sovereignty)
   - `voice_ai_founder`: WhisperFlow AI (Sub-450ms voice telephony for AI founders)
3. **Zero-Hallucination Numeric Grounding**: Custom guardrail (`numeric_grounding_checker.py`) cross-verifies every dollar savings, percentage, and case study metric against campaign knowledge bases before dispatch.
4. **Autonomous Flow Execution**:
   - **Flow 1**: Campaign Creation & Launch
   - **Flow 2**: Autonomous Lead Lifecycle (Research $\to$ ICP $\to$ Copy $\to$ Grounding $\to$ Send)
   - **Flow 3**: Mid-Execution Campaign Pause
   - **Flow 4**: Human-in-the-Loop Inbox (Approve, Edit, Reject risky drafts)
   - **Flow 5**: Cross-Campaign Prospect Conflict Resolution
   - **Flow 6**: Sales Rep Offboarding & Reassignment
5. **Telemetry & Cost Tracking**: Full audit logging in `telemetry.jsonl` tracking latency, token usage, and cost per prospect.

---

## 📊 Evaluation & Benchmark Results

Evaluated against the Golden Dataset (12 prospects across 3 campaigns + 10 reply scenarios):

| Metric | Measured Value | Benchmark Target | Status |
|---|---|---|---|
| **ICP Qualification Accuracy** | **91.7%** (11/12) | $\ge 90\%$ | 🟢 PASS |
| **Negative ICP Disqualification** | **100.0%** (5/5) | $100\%$ | 🟢 PASS |
| **Reply Intent Classification** | **100.0%** (10/10) | $\ge 85\%$ | 🟢 PASS |
| **HITL Escalation Precision** | **80.0%** | $\ge 80\%$ | 🟢 PASS |
| **LLM-as-Judge Quality Score** | **5.0 / 5.0** | $\ge 4.5$ | 🟢 PASS |
| **Hallucination Rate** | **0.0%** | $0.0\%$ | 🟢 ZERO HALLUCINATION |
| **Cost per Discovered Prospect** | **$0.00117** | $<\$0.01$ | 🟢 99.9% SAVINGS |
| **Cost per Qualified Lead** | **$0.00469** | $<\$0.05$ | 🟢 PRODUCTION GRADE |
| **Average Pipeline Latency** | **2,920 ms** | $<3,500\text{ ms}$ | 🟢 SUB-3S |

---

## 📁 Repository Structure

```
├── agents/                       # Specialized rule-based fallback modules
│   ├── conversation_agent.py     # Inbound reply intent classifier
│   ├── follow_up_agent.py        # Cadence timing & breakup evaluator
│   ├── icp_agent.py              # 0-100 ICP fitment scorer
│   ├── personalisation_agent.py  # Grounded email & LinkedIn copywriter
│   ├── research_agent.py         # Tech stack & pain point extractor
│   ├── strategy_agent.py         # Multi-ingress strategy router
│   └── voice_agent.py            # Phone call script generator
├── guardrails/
│   ├── grounding_policy.py       # Grounding checker & Policy Gate
│   └── numeric_grounding_checker.py  # Fact-checking regex & string verifier
├── knowledge_bases/              # Campaign RAG context files
│   ├── us_saas_cto/knowledge.md
│   ├── india_bfsi_cio/knowledge.md
│   └── voice_ai_founder/knowledge.md
├── dronahq_kb_uploads/           # Clean knowledge base uploads for DronaHQ
├── prompts/                      # Production system prompts with few-shot examples
│   ├── 01_research_agent.md
│   ├── 02_icp_fitment_agent.md
│   ├── 03_strategy_agent.md
│   ├── 04_personalisation_agent.md
│   ├── 05_conversation_agent.md
│   ├── 06_follow_up_agent.md
│   └── 07_voice_sdr_agent.md
├── rag/
│   └── store.py                  # Isolated campaign knowledge base store
├── test_data/                    # Golden evaluation datasets
│   ├── golden_prospects.json     # 12 test prospects with expected outcomes
│   └── golden_replies.json       # 10 reply scenarios with expected intents
├── api.py                        # FastAPI control plane orchestrator (Flows 1-6)
├── llm_agents.py                 # Core production 7-agent LLM pipeline
├── schemas.py                    # Strict Pydantic models for all agent contracts
├── test_all_6_flows.py           # Comprehensive E2E test suite for all 6 flows
├── evaluate_agents_judge.py      # LLM-as-a-Judge benchmark harness
├── eval_report.md                # Latest benchmark report
├── eval_report.json              # Machine-readable benchmark telemetry
├── telemetry.jsonl               # Live token, latency, and cost telemetry
├── Dockerfile                    # Containerization for deployment
├── railway.toml                  # One-click deployment to Railway
└── requirements.txt              # Production Python dependencies
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`venv` or `uv`)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/parvesh2520/Buildathon.git
cd Buildathon

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

### 4. Run the Backend Server
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at:  
👉 **`http://localhost:8000/docs`**

### 5. Run the Automated Test & Benchmark Suite
```bash
# Run end-to-end pipeline test
python test_e2e_flow.py

# Run LLM-as-a-Judge evaluation benchmark
python evaluate_agents_judge.py
```

---

## 🔗 DronaHQ Integration

See **[`dronahq_setup_guide.md`](./dronahq_setup_guide.md)** for:
1. Exact instructions to create the 7 specialized agents in DronaHQ.
2. Setting up the native Voice SDR Agent in DronaHQ Voice Studio.
3. Connecting DronaHQ Apps Studio to the FastAPI backend via REST Connector.
