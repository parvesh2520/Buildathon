# Autonomous SDR Platform

A full-stack sales automation system for prospect discovery, campaign orchestration, outreach execution, follow-up management, and voice/email handling. The project combines a FastAPI backend with a React + TypeScript frontend and is designed to run either locally or as a Render deployment.

## Overview

This workspace contains:

- A Python backend that exposes the SDR workflow APIs
- A Vite + React frontend for monitoring campaigns and agent activity
- Multi-channel outreach capabilities across email, SMS, voice, and inbound workflows
- Agent-style workflow pages for sourcing, research, ICP gating, timing optimization, conversation handling, and voice AI
- Integration points for DronaHQ, Twilio, Supabase, and SMTP-driven communication

## Architecture

```text
Frontend (React + Vite)
        |
        v
FastAPI backend
        |
   +----+------------------------------+
   |    |                              |
   v    v                              v
Campaigns  Prospect discovery        SDR execution
   |    |                              |
   v    v                              v
Email / SMS / Voice / Follow-ups / Inbound webhooks / Analytics
```

## Tech stack

- Backend: Python, FastAPI, Pydantic
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Communications: Twilio, SMTP, email automation
- Workflow orchestration: DronaHQ webhook integrations
- Data layer: JSON-backed persistence in the current app, with Supabase-ready configuration
- Deployment: Render

## Repository structure

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routes/
│   │   └── services/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   ├── README.md
│   └── start.ps1
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── README.md
├── render.yaml
├── README.md
└── .gitignore
```

## Core features

### Campaign and prospect management
- Create, list, update, and duplicate campaigns
- Add prospect records and track their status
- Run discovery pipelines against target buyers or leads
- Review campaign execution history

### SDR execution engine
- Trigger campaign runs through the backend API
- Retrieve execution records and telemetry
- Expose agent-level metrics and operational status

### Communication and outbound flows
- Email send/test endpoints
- Voice AI / Twilio callback endpoints
- SMS and follow-up orchestration
- Inbound webhook support for Twilio and app-driven events

### Operational control centre
- Agent pause / resume logic
- System kill switches
- Conflict scanning and resolution routes
- Knowledge-base and RAG-style operational controls

### Frontend experience
- Dashboard summaries
- Campaign detail screens
- Discovery and prospect selectors
- Agent fleet pages for each SDR stage
- Activity, analytics, settings, and inbox views

## Prerequisites

Before running the project locally, install:

- Python 3.11+
- Node.js 18+
- npm
- A terminal such as PowerShell, Bash, or Command Prompt

## Local backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Local frontend setup

```bash
cd frontend
npm install
npm run dev -- --host
```

The frontend will typically run at:

- http://localhost:5173

If the frontend needs to talk to a different backend, define a custom API URL:

```bash
# .env in frontend/
VITE_API_BASE_URL=http://localhost:8000
```

## Environment variables

The backend can be configured with environment variables such as:

```bash
APP_ENV=development
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
SENDER_EMAIL=your_sender_email
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_twilio_number
DRONAHQ_WEBHOOK_URL=your_dronahq_webhook
BACKEND_BASE_URL=http://localhost:8000
```

The deployment configuration already includes many of these in the root [render.yaml](render.yaml) file.

## Deployment

This repository includes a Render deployment config in [render.yaml](render.yaml). It is configured to deploy the Python backend from the backend folder.

Typical deployment flow:

1. Push this repository to GitHub
2. Connect the repo to Render
3. Ensure environment variables are set in Render
4. Deploy the service

## Useful API endpoints

Some of the routes included in the backend:

- GET /health
- POST /api/dronahq/webhook
- GET /api/agents
- /api/campaigns
- /api/prospects
- /api/discovery
- /api/sdr
- /api/email
- /api/voice
- /api/followups
- /api/inbound
- /api/system

## Notes

- The project is strongly oriented around SDR automation and AI-led sales operations.
- The current backend uses JSON-based in-memory or local data structures for many workflows and is ready to be connected to a production database.
- The frontend is built as a command-and-control dashboard for the operations layer behind the SDR system.

## Recommended next steps

- Connect the app to a persistent database (Supabase/Postgres)
- Add authentication and authorization
- Replace stubbed workflow logic with production-safe orchestration
- Add automated tests for a broader backend and frontend suite
- Harden environment configuration and deployment secrets

## License

This project does not currently include a project-specific license file. If you plan to distribute or publish it, add a license before release.
