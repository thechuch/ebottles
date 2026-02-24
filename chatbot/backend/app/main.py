from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.routes import lead_intake_router, transcribe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.WARNING)
    logging.info("eBottles AI Intake starting...")
    logging.info("Allowed origins: %s", settings.allowed_origins_list)
    yield
    # Shutdown
    logging.info("eBottles AI Intake shutting down...")


app = FastAPI(
    title="eBottles AI Lead Intake",
    description="AI-powered lead intake and qualification API for eBottles",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(lead_intake_router, tags=["Lead Intake"])
app.include_router(transcribe_router, tags=["Transcription"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "ebottles-ai-intake"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "eBottles AI Lead Intake",
        "version": "1.0.0",
        "endpoints": {
            "lead_intake": "POST /lead-intake",
            "transcribe": "POST /transcribe",
            "health": "GET /health",
        }
    }

