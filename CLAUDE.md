# CLAUDE.md

FastAPI service (Python 3.12, uv) that OCRs scanned PDFs to extract person names with
their page + bounding box in PDF points, fuzzy-matches them against a requested list,
and answers questions over ingested documents with RAG (README.md §What you're
building). Hexagonal architecture (TRD ADR-001).

> `CONSTITUTION.md` is the authority on how code is written; this file describes the
> current conventions. System-level decisions and ADRs live in
> `docs/trds/document-intelligence-trd.md` (+ `docs/adrs/`). The README is the PRD.

## Naming conventions

- Modules/files `snake_case.py`; classes `PascalCase`; functions/variables
  `snake_case`; constants `UPPER_SNAKE` (CONSTITUTION §10).
- Ports are role nouns as `Protocol`s (`OcrEngine`, `PersonNameRecognizer`,
  `Embedder`, `VectorStore`, `AnswerGenerator`, `PdfRasterizer`); adapters are
  `<Tech><Port>` (`TesseractOcrEngine`, `ChromaVectorStore`) (TRD §2).
- Use cases are verb phrases: `ExtractNames`, `IngestDocument`, `AnswerQuestion`
  (TRD §3).
- Errors are named by the violated rule (`UploadIsNotPdf`, `LlmUnavailable`), never
  generic (CONSTITUTION §10, §12).
- Code, identifiers, commits and docs in English.

## Core code patterns

- **Dependency rule:** `domain` ← `application` ← `infrastructure` / `api`. Domain and
  application never import `fastapi`, `pydantic`, or any vendor SDK (CONSTITUTION §1.2,
  §2.1; ADR-012).
- **Composition root:** adapters are built once in the FastAPI lifespan (`app/main.py`)
  and injected via constructor; no module-level singletons, no service locator.
- **Fixed contract:** `app/models/schemas.py` shapes are frozen by the PRD — add
  optional fields only with a reason recorded in `DECISIONS.md`.
- **Errors:** `DomainError` → 4xx, `InfrastructureError` → 5xx with `request_id`;
  vendor exceptions translated inside the adapter (CONSTITUTION §8).
- **Config:** every host/port/model/threshold/DPI/limit comes from the `Settings`
  object (env-overridable); none hardcoded (README §Requirements).
- **Logging:** structured JSON, `event` names, `request_id` per request; never log
  person names or document text (CONSTITUTION §9).
- **Sync CPU work:** endpoints that OCR/embed are plain `def` (threadpool), not
  `async def` (TRD §8).

## Build & validation commands

<!-- PENDING: these become real in phase P0 (TRD §14). Update once pyproject is configured. -->
```bash
uv sync --extra dev                  # install
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run mypy app                      # type-check (strict)
uv run lint-imports                  # hexagonal dependency contracts
uv run pytest -m "not integration"   # fast suite (fakes)
uv run pytest                        # full suite (needs Tesseract installed)
uv run uvicorn app.main:app --reload # run locally
```

## On-demand context

| Module | Load when |
|---|---|
| `.claude/context/architecture.md` | Creating/moving modules, adding a port or adapter, wiring DI |
| `.claude/context/extraction-pipeline.md` | Touching OCR, NER, bounding boxes, coordinates, or fuzzy matching |
| `.claude/context/testing.md` | Writing tests, fakes, golden sets or evals |
| `.claude/context/requirements-traceability.md` | Planning a ticket, reviewing, or before opening the PR |

## Hard rules

- Run the full validation gate (above) before every commit that goes into a PR.
- Tests first (TDD): the failing test precedes the code (CONSTITUTION §11).
- Never change field names/types in `app/models/schemas.py`.
- Never commit secrets; `.env` is git-ignored — document keys in `.env.example`.
- No new dependency without an ADR (CONSTITUTION §12).
- No `except: pass`, no bare `Exception` raises, no `Any`/`type: ignore` without a
  justification comment.
- Never put PII (names, document text) in logs or error messages.

## Miscellaneous / Gotchas

<!-- Running list — add entries as you discover things the agent repeatedly misunderstands -->
- Windows dev box: Tesseract is **not installed** and the PATH entry
  `C:\Program Files\Tesseract-OCR` is stale — install it (verify the id with
  `winget search tesseract`) or run integration tests in Docker.
- uv may pick Anaconda's Python 3.9 by default → spaCy's `blis` fails to build. Pin the
  interpreter (`.python-version` = 3.12 / `uv run --python 3.12`).
- spaCy models are installed as pinned wheel URLs in `pyproject.toml`, not via
  `python -m spacy download` (uv venvs ship without pip).
- OCR text contains curly apostrophes (`O’Brien`); the Windows console (cp1252)
  mangles them — set `PYTHONIOENCODING=utf-8` when printing.
- The repo lives under a OneDrive path with spaces — quote paths in shell commands.
- spaCy `en_core_web_sm` tags the codename `'Atlas'` (company_memo.pdf) as PERSON —
  a known false positive kept in the golden set.
