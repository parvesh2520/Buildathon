# Autonomous SDR API

A minimal FastAPI backend that serves as the foundation for an Autonomous Sales Development Representative (SDR) pipeline. It is intentionally simple — no database, no auth, no queues — so it is easy to extend in subsequent iterations.

---

## What this backend does

- Manages **Campaigns** (in-memory, LIVE / PAUSED lifecycle)
- Manages **Prospects** (in-memory)
- Exposes a **SDR run endpoint** that will later trigger the DronaHQ / AI agent pipeline
- Provides automatic **Swagger** and **ReDoc** documentation

---

## Project structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, router registration
│   ├── config.py        # Environment config (APP_NAME, APP_ENV)
│   ├── models/
│   │   ├── campaign.py  # Campaign Pydantic models + in-memory store
│   │   └── prospect.py  # Prospect Pydantic models + in-memory store
│   ├── routes/
│   │   ├── campaigns.py # GET/POST/PATCH campaign endpoints
│   │   ├── prospects.py # GET/POST prospect endpoints
│   │   └── sdr.py       # POST /api/sdr/run endpoint
│   └── services/
│       └── sdr.py       # SDR pipeline stub (future DronaHQ integration)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment variables
copy .env.example .env
```

---

## Running locally

```bash
uvicorn app.main:app --reload
```

The server starts at **http://127.0.0.1:8000**

---

## API documentation

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | Swagger UI (interactive) |
| http://127.0.0.1:8000/redoc | ReDoc |

---

## Example API requests

### Health check
```bash
curl http://127.0.0.1:8000/health
```

### Create a campaign
```bash
curl -X POST http://127.0.0.1:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name":"US SaaS CTOs","icp":"CTO at SaaS companies with 50-500 employees","status":"LIVE"}'
```

### List campaigns
```bash
curl http://127.0.0.1:8000/api/campaigns
```

### Pause a campaign
```bash
curl -X PATCH http://127.0.0.1:8000/api/campaigns/{campaign_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status":"PAUSED"}'
```

### Add a prospect
```bash
curl -X POST http://127.0.0.1:8000/api/prospects \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","email":"jane@acme.com","title":"CTO","company":"Acme Inc"}'
```

### Trigger SDR run
```bash
curl -X POST http://127.0.0.1:8000/api/sdr/run \
  -H "Content-Type: application/json" \
  -d '{"campaign_id":"<campaign_id>","prospect_id":"<prospect_id>"}'
```

---

## Future DronaHQ integration

When connecting to the DronaHQ automation pipeline:

1. Add `app/services/dronahq.py` with the HTTP client / webhook logic.
2. Replace the stub in `app/services/sdr.py → queue_sdr_run()` with a real call to that service.
3. The routes and models do **not** need to change.

The SDR service layer is the single integration point by design.
