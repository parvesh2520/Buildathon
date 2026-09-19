from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import APP_NAME, APP_ENV
from app.routes import campaigns, prospects, sdr, email, voice, database
from app.services.sdr import process_dronahq_webhook

app = FastAPI(
    title=APP_NAME,
    description="Backend for the Autonomous SDR pipeline. Connects to DronaHQ and AI agents.",
    version="0.1.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(campaigns.router)
app.include_router(prospects.router)
app.include_router(sdr.router)
app.include_router(email.router)
app.include_router(voice.router)
app.include_router(database.router)


@app.post("/api/dronahq/webhook", tags=["SDR"])
async def dronahq_webhook_direct(request: Request):
    """Direct alias endpoint for DronaHQ incoming webhooks."""
    payload = await request.json()
    return process_dronahq_webhook(payload)


@app.get("/api/agents", tags=["Agents"])
def get_agents_direct():
    """Direct alias endpoint to get SDR agents telemetry."""
    from app.routes.sdr import get_agent_telemetry
    return get_agent_telemetry()


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "app": APP_NAME, "env": APP_ENV}
