"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .database import init_db
from .logging_config import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    configure_logging,
)
from .routers import auth, tasks

configure_logging(settings.log_level)
logger = logging.getLogger("taskflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if a real deployment forgot to set a secret.
    if settings.is_production and settings.secret_key == "dev-only-insecure-secret-change-me":
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")
    init_db()
    logger.info("%s v%s started (%s)", settings.app_name, __version__, settings.environment)
    yield
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
