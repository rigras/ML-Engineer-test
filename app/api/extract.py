"""`POST /api/extract` — thin driving adapter: parse, call the use case, map (ADR-012).

Sync ``def`` on purpose: OCR and NER are CPU-bound, so FastAPI runs this in its threadpool
instead of blocking the event loop (TRD §8).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_extract_names
from app.api.mapping import to_extraction_response, to_requested_names
from app.application.extract_names import ExtractNames
from app.domain.errors import UploadMissing
from app.models.schemas import ExtractionResponse

router = APIRouter()

DESCRIPTION = """Upload a scanned PDF (`pdf_file`) and, optionally, the people to check
(`names`: JSON list of `{"first_name", "last_name"}`; omitted means `[]`).

Returns one `extracted_names` entry per occurrence of a PERSON, ordered by page then
reading order. `page_number` is **0-based**; `x`, `y`, `width`, `height` are in **PDF
points** (1/72 inch) with the origin at the **top-left** of the page and `y` growing
down. `fuzzy_matches` lists each extracted name scoring at or above the configured
threshold (0..1) against a requested name."""


@router.post("/extract", response_model=ExtractionResponse, description=DESCRIPTION)
def extract(
    extract_names: Annotated[ExtractNames, Depends(get_extract_names)],
    pdf_file: Annotated[UploadFile | None, File()] = None,
    names: Annotated[str, Form()] = "[]",
) -> ExtractionResponse:
    """Extract person names with page and box, and match them to the requested names."""
    if pdf_file is None:
        raise UploadMissing("The pdf_file field is required")
    requested = to_requested_names(names)
    pdf = pdf_file.file.read()
    return to_extraction_response(extract_names.execute(pdf, requested))
