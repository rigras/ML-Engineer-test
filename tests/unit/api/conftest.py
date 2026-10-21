from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import Container
from app.infrastructure.settings import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture
def make_client(
    settings: Settings,
) -> Iterator[Callable[..., TestClient]]:
    clients: list[TestClient] = []

    def _make(app: FastAPI | None = None, **kwargs: bool) -> TestClient:
        target = app or create_app(settings, build_container=lambda _: Container())
        client = TestClient(target, **kwargs)
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)
