"""Ports: what the application needs from the outside world (TRD ADR-001).

Signatures use domain types only, so adapters can be swapped without touching use cases.
"""

from collections.abc import Iterator
from typing import Protocol

from app.domain.document import Page, PageImage, PdfInfo
from app.domain.persons import PersonSpan


class PdfRasterizer(Protocol):
    """Turns PDF bytes into page images."""

    def probe(self, pdf: bytes) -> PdfInfo:
        """Read page count and encryption without rendering; raises ``PdfUnreadable``."""
        ...

    def render(self, pdf: bytes, dpi: int) -> Iterator[PageImage]:
        """Yield every page (index 0..n-1); raises ``PdfUnreadable`` / ``PdfEncrypted``."""
        ...


class OcrEngine(Protocol):
    """Reads the words on a page image."""

    def recognize(self, image: PageImage) -> Page:
        """Return the page's words with boxes in PDF points; raises ``OcrUnavailable``."""
        ...


class PersonNameRecognizer(Protocol):
    """Finds person names in text."""

    def recognize(self, text: str) -> list[PersonSpan]:
        """Return PERSON spans, honorifics trimmed; raises ``NerModelUnavailable``."""
        ...
