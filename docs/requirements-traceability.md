# Requirements traceability — README requirement → rule → verification

Every graded requirement in README §"Requirements that matter" maps to a rule and a
mechanical check. Keep this table current; a requirement without a check is a gap.

| README requirement | Rule | Verified by |
|---|---|---|
| SOLID, separation of concerns | CONSTITUTION §1, §6 | import-linter layers contract; review |
| Services depend on abstractions (Protocols/ABCs), not singletons | CONSTITUTION §1.3, §4, §5 | Use-case tests run against fakes (proves substitutability) |
| Dependency injection | CONSTITUTION §4.5, ADR-012 | import-linter `forbidden` (api/domain/application never import infrastructure); review |
| Thin routers; logic testable without HTTP | CONSTITUTION §2.1 | Use-case tests without `TestClient`; routers contain no domain `if`s |
| Config: no hardcoded hosts/ports/models/thresholds/DPI | CONSTITUTION §6 (Configuration), §12 | `Settings` unit test; `.env.example` lists every key; review |
| Timeouts + retries on external calls (LLM, vector store) | CONSTITUTION §8 | Adapter tests with a fake server/timeout; config-driven values |
| Meaningful failure modes; no `except: pass` | CONSTITUTION §8, §12 | ruff rules (`S110`, `BLE001`, `E722`); API tests for each error → status |
| Reject non-PDF by content, empty, oversized; validate bodies | CONSTITUTION §8 (Validate at the edge) | API tests: renamed `.txt` as `.pdf`, empty file, oversize, bad `names` JSON |
| No leaked file handles / temp files | CONSTITUTION §8 (Resources are scoped) | Test asserting temp dir empty after success **and** after failure |
| Structured logging with context | CONSTITUTION §9 | Test capturing a log record: JSON, `event`, `request_id`, no names |
| OCR every page incl. first | TRD §1, §2 (Extract flow) | Unit test with fake rasterizer of N pages; e2e on 2-page samples |
| Boxes in PDF space, not pixels | TRD ADR-003 | Geometry unit test (px→pt); e2e: boxes within 612×792 |
| Case/accent-insensitive, OCR-noise-robust, full-string matching | TRD ADR-005 | Golden pairs unit tests (`María González`~`Maria Gonzalez`, `Ana` ≁ `Ana María Rodríguez`) |
| Chunking never cuts words | TRD ADR-011 | Property test on the chunker |
| Grounded answers; no hallucinated `sources` | TRD ADR-006 | Use-case test: sources ⊆ retrieved chunk metadata |
| Vector IDs unique across documents | TRD ADR-007 | Test: ingest A, ingest B, both retrievable |
| Tests: tricky logic (mock heavy models) + ≥1 e2e | CONSTITUTION §7 | `pytest` suites; fakes = the "mocks" the README asks for |
| Disclose AI use; own every line | README §Use of AI tools | `DECISIONS.md` section |
