# Architecture map (load when creating modules, ports, adapters, or wiring DI)

Source: TRD §2–§3, ADR-001, ADR-012, CONSTITUTION §1–§2.

## Intended layout

```
app/
  main.py                 # app factory + lifespan = composition root (builds adapters once)
  models/schemas.py       # FIXED HTTP contract (Pydantic) — driving-adapter DTOs, do not reshape
  api/                    # driving adapter: routers, upload validation, error→status map, DI providers
  application/
    ports.py              # Protocols: PdfRasterizer, OcrEngine, PersonNameRecognizer,
                          #            Embedder, VectorStore, AnswerGenerator
    <use_case>.py         # ExtractNames, IngestDocument, AnswerQuestion (plain classes)
  domain/                 # pure: entities/value objects (dataclasses), alignment & geometry,
                          #       name normalization/matching, chunking, error hierarchy
  infrastructure/         # adapters (one per port) + Settings + logging setup
tests/
  unit/  integration/  e2e/  golden/  fakes/
```

The skeleton's `app/services/*.py` stubs are replaced by this layout (ADR-001).

## Dependency rule (enforced by import-linter)

```
api ─────────┐
             ├──► application ──► domain
infrastructure┘
```

- `domain` imports stdlib + pure computation libs only (e.g. `rapidfuzz`).
- `application` imports `domain` only. No `fastapi`, `pydantic`, SDKs.
- `infrastructure` and `api` may import inward; they never import each other except the
  composition root (`app/main.py`), which wires everything.

## Adding a new external capability

1. Define the port in `application/ports.py` with **domain types** in the signature.
2. Write the fake in `tests/fakes/` and the use-case test against it.
3. Implement the adapter in `infrastructure/`, translating vendor exceptions to domain/
   infrastructure errors at the edge.
4. Add an adapter test against the real engine (`@pytest.mark.integration`).
5. Wire it in the lifespan; read its config from `Settings`.
6. New library ⇒ ADR first.
