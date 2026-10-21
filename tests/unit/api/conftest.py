from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import Container
from app.application.extract_names import ExtractNames
from app.infrastructure.settings import Settings
from app.main import create_app
from tests.fakes import FakeOcrEngine, FakeRasterizer, FakeRecognizer


def fake_container(
    settings: Settings,
    rasterizer: FakeRasterizer | None = None,
    ocr: FakeOcrEngine | None = None,
    recognizer: FakeRecognizer | None = None,
) -> Container:
    """A container wired with in-memory fakes: no model, no binary."""
    rasterizer = rasterizer or FakeRasterizer(pages=1)
    extract_names = ExtractNames(
        rasterizer=rasterizer,
        ocr=ocr or FakeOcrEngine(),
        recognizer=recognizer or FakeRecognizer(),
        dpi=settings.render_dpi,
        fuzzy_threshold=settings.fuzzy_threshold,
    )
    return Container(rasterizer=rasterizer, extract_names=extract_names)


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture
def make_client(
    settings: Settings,
) -> Iterator[Callable[..., TestClient]]:
    clients: list[TestClient] = []

    def _make(app: FastAPI | None = None, **kwargs: bool) -> TestClient:
        target = app or create_app(settings, build_container=fake_container)
        client = TestClient(target, **kwargs)
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)
