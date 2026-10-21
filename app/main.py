"""App factory and composition root (CONSTITUTION §4.5, ADR-012).

The lifespan is the only place adapters are instantiated; routers receive them through
the providers in ``app/api/dependencies.py``.
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.dependencies import Container
from app.api.errors import register_error_handlers
from app.api.extract import router as extract_router
from app.api.health import router as health_router
from app.api.middleware import RequestIdMiddleware
from app.api.rag import router as rag_router
from app.infrastructure.logging import configure_logging
from app.infrastructure.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def build_container(settings: Settings) -> Container:
    """Build every adapter and use case once, from configuration."""
    return Container()


def create_app(
    settings: Settings | None = None,
    build_container: Callable[[Settings], Container] = build_container,
) -> FastAPI:
    """Create the app; settings load (and fail fast) here, adapters in the lifespan."""
    resolved = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(resolved.log_level)
        app.state.container = build_container(resolved)
        logger.info("startup_completed")
        yield

    app = FastAPI(title="Document Intelligence Service", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)
    app.include_router(health_router, tags=["health"])
    app.include_router(extract_router, prefix="/api", tags=["extraction"])
    app.include_router(rag_router, prefix="/api", tags=["rag"])
    return app


app = create_app()
