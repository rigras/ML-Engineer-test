"""Extract-names use case: OCR → page text → NER → alignment → matching (TRD §2)."""

import logging
from time import perf_counter

from app.application.ports import OcrEngine, PdfRasterizer
from app.domain.document import Page

logger = logging.getLogger(__name__)


def read_pages(rasterizer: PdfRasterizer, ocr: OcrEngine, pdf: bytes, dpi: int) -> list[Page]:
    """OCR every page of the PDF, first page included, in page order."""
    pages = []
    page_ms = []
    for image in rasterizer.render(pdf, dpi):
        started = perf_counter()
        pages.append(ocr.recognize(image))
        page_ms.append(round((perf_counter() - started) * 1000, 1))
    logger.info(
        "ocr_completed",
        extra={
            "page_count": len(pages),
            "word_count": sum(len(page.words) for page in pages),
            "page_duration_ms": page_ms,
        },
    )
    return pages
