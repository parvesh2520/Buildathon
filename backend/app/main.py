from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import APP_NAME, APP_ENV
from app.routes import campaigns, prospects, sdr, email, voice, database, operational_controls, discovery, agent1_service, inbound, followups
from app.routes.inbound_twilio import router as inbound_twilio_router
from app.services.sdr import process_dronahq_webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    # Start Gmail reply poller background thread (every 2h by default)
    from app.services.gmail_poller import start_background_gmail_poller
    start_background_gmail_poller()
    from app.services.followup import start_background_followup_scheduler
    start_background_followup_scheduler()
    yield
    # (shutdown cleanup goes here if needed)


app = FastAPI(
    title=APP_NAME,
    description="Backend for the Autonomous SDR pipeline. Connects to DronaHQ and AI agents.",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(discovery.router)
app.include_router(sdr.router)
app.include_router(email.router)
app.include_router(voice.router)
app.include_router(database.router)
app.include_router(operational_controls.router)
app.include_router(agent1_service.router)
app.include_router(inbound.router)
app.include_router(followups.router)
app.include_router(inbound_twilio_router)


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
    return {"status": "ok", "app": APP_NAME, "env": APP_ENV, "version": "1.0.3"}
