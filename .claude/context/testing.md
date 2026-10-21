# Testing (load when writing tests, fakes, golden sets, or evals)

Source: CONSTITUTION §7, TRD §11. **State today: no tests exist yet** — this is the
intended convention, to be confirmed once P0 lands.

## Layers

| Layer | Folder | Uses | Marker |
|---|---|---|---|
| Domain unit | `tests/unit/domain/` | Pure functions/dataclasses. No mocks, no I/O | — |
| Use case | `tests/unit/application/` | In-memory **fakes** from `tests/fakes/` | — |
| API | `tests/unit/api/` | FastAPI `TestClient` with fake use cases/adapters (validation, status mapping) | — |
| Adapter | `tests/integration/` | Real Tesseract / spaCy / Chroma / embedder | `integration` |
| E2E | `tests/e2e/` | Real app over HTTP on `sample_pdfs/` | `integration` |
| Evals | `tests/golden/` + `scripts/eval_*.py` | Golden set; thresholds in TRD §1 | `eval` |

## Rules

- Fakes, not mocks, for ports. LLM → scripted fake; never assert exact LLM text.
- Name tests after the behavior: `test_second_ingest_does_not_overwrite_first_document`.
- Each graded invariant in `extraction-pipeline.md` (and the RAG ones: word-safe
  chunking, unique IDs across documents, sources ⊆ retrieved) has at least one test.
- Fast suite (`-m "not integration"`) must run in seconds without Tesseract installed.
- No shared state between tests; temp dirs via `tmp_path`.
