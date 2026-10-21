from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import Container
from app.api.upload import UploadLimits
from app.application.extract_names import ExtractNames
from app.application.ingest_document import IngestDocument
from app.application.ports import PdfRasterizer
from app.infrastructure.settings import Settings
from app.main import create_app
from tests.fakes import (
    FakeEmbedder,
    FakeOcrEngine,
    FakeRasterizer,
    FakeRecognizer,
    InMemoryVectorStore,
)


def fake_container(
    settings: Settings,
    rasterizer: PdfRasterizer | None = None,
    ocr: FakeOcrEngine | None = None,
    recognizer: FakeRecognizer | None = None,
    store: InMemoryVectorStore | None = None,
) -> Container:
    """A container wired with in-memory fakes: no model, no binary."""
    rasterizer = rasterizer or FakeRasterizer(pages=1)
    ocr = ocr or FakeOcrEngine()
    extract_names = ExtractNames(
        rasterizer=rasterizer,
        ocr=ocr,
        recognizer=recognizer or FakeRecognizer(),
        dpi=settings.render_dpi,
        fuzzy_threshold=settings.fuzzy_threshold,
    )
    ingest_document = IngestDocument(
        rasterizer=rasterizer,
        ocr=ocr,
        embedder=FakeEmbedder(),
        store=store if store is not None else InMemoryVectorStore(),
        dpi=settings.render_dpi,
        max_tokens=settings.chunk_max_tokens,
    )
    return Container(
        upload_limits=UploadLimits(settings.max_upload_bytes, settings.max_pages),
        rasterizer=rasterizer,
        extract_names=extract_names,
        ingest_document=ingest_document,
    )


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
