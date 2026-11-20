"""
Trinetra: Digital Trust & Provenance Backend
FastAPI entrypoint and router registration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    CORS_ORIGINS,
    STATIC_FILES_DIR,
    MOCK_MODE,
    DATA_DIR
)
from app.strings import load_strings
from app.routers import health, analyze, passport, match_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trinetra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing Trinetra Backend...")
    logger.info(f"Mode: {'MOCK' if MOCK_MODE else 'PRODUCTION'}")
    
    # Ensure static and data directories exist
    STATIC_FILES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load shared / fallback strings
    load_strings()
    logger.info("Strings loaded successfully.")
    yield
    # Shutdown actions
    logger.info("Shutting down Trinetra Backend.")


app = FastAPI(
    title="Trinetra: Digital Trust & Provenance API",
    description="Backend API for Trinetra: origin engine, edit diff, C2PA verification, and Provenance Passport.",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration: Allow localhost, PWA, and browser extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving: /files/{name}
STATIC_FILES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(STATIC_FILES_DIR)), name="files")

# Register routers
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(passport.router)
app.include_router(match_hash.router)


@app.get("/")
async def root():
    return {
        "project": "Trinetra: Digital Trust & Cybersecurity",
        "team": "Team Kinetix",
        "track": "Misinformation & Provenance",
        "event": "Code for Innovex '26",
        "theme": "Navyug - A New Era",
        "docs_url": "/docs",
        "health_url": "/health"
    }
