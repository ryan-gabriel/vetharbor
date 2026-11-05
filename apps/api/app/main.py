"""Application factory for the Vetharbor modular monolith (ADR-001)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.config import Profile, Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import CorrelationMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.outbox.router import router as outbox_router
from app.modules.rag.router import router as rag_router
from app.modules.scoring.router import router as scoring_router
from app.modules.upload.router import router as upload_router
from app.persistence.db import Database

API_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    """Liveness payload. Deliberately tiny: Render cold-start probes this."""

    status: Literal["ok"]
    profile: Profile
    version: str


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    db: Database = app.state.db
    await db.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(
        title="Vetharbor API",
        version=API_VERSION,
        description="Document screening with AI guardrails. Synthetic data only (ADR-010).",
        lifespan=_lifespan,
    )
    app.state.settings = settings
    app.state.db = Database(settings)

    app.add_middleware(CorrelationMiddleware)
    register_error_handlers(app)

    api = "/api/v1"
    app.include_router(auth_router, prefix=api)
    app.include_router(upload_router, prefix=api)
    app.include_router(outbox_router, prefix=api)
    app.include_router(scoring_router, prefix=api)
    app.include_router(rag_router, prefix=api)

    @app.get("/healthz", response_model=HealthResponse, tags=["ops"])
    async def healthz() -> HealthResponse:
        return HealthResponse(status="ok", profile=settings.profile, version=API_VERSION)

    return app


app = create_app()
