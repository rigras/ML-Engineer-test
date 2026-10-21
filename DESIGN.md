# DESIGN — Document Intelligence Service

> **Visual version (3 pages): [DESIGN.pdf](DESIGN.pdf)** — same content, built from
> [`docs/design/design.html`](docs/design/design.html).

Scanned PDF → every person name with its **page and box in PDF points** → fuzzy match
against a requested list; plus RAG answers grounded in ingested documents. FastAPI,
Python 3.12, hexagonal architecture. Full record: the
[TRD](docs/trds/document-intelligence-trd.md) and ADR-001…015.

| NER P / R | Boxes verified | Retrieval hit@1 | Answers pass^3 | Ungrounded sources |
|---|---|---|---|---|
| 1.00 / 0.98 | 54 / 54 | 10 / 10 | 13 / 13 | 0 |

## 1. Components

![Components: driving adapters, use cases, ports, adapters](docs/design/components.svg)

Use cases depend only on **ports** (`Protocol`s); each library lives in one adapter;
`app/main.py` builds the adapters once at startup and injects them. `import-linter` fails
the build if domain or application import FastAPI, Pydantic or a vendor SDK.

## 2. Extract flow

![Extract pipeline: validate, rasterize, OCR, pixels to points, NER and align, match](docs/design/extract-flow.svg)

Names are located by **character offsets**, not by searching the text: one box per real
occurrence, repeated names handled, honorifics excluded. Matching is
`max(ratio, token_sort_ratio) ≥ 0.90` on casefolded, accent-stripped names
(`María González` ~ `Maria Gonzalez`, word order tolerated, no substring inflation).
Pages are 0-based; origin top-left (a bottom-left consumer flips
`y' = page_height − y − height`).

## 3. Engineering practices

| | |
|---|---|
| Configuration | One `Settings` object; every host, model, threshold, DPI and limit is a `DOCINTEL_*` variable (`.env.example`). |
| Validation | By content at the edge: `%PDF-`, empty, size, page count, encrypted/corrupt, malformed `names` — each a specific 4xx code. |
| Resilience | Domain errors → 4xx, infrastructure → 5xx with `request_id`; LLM timeout + retries; OCR per-page timeout. |
| Observability | Structured JSON logs with event names and `request_id`; names and document text never logged. |
| Tests | ~870: pure domain, use cases on fakes, real-engine adapters, end-to-end on the samples; plus 5 eval scripts. |

## 4. Ask sequence

![Ask sequence: hybrid retrieval, rerank, gate, LLM, grounding](docs/design/ask-sequence.svg)

**Ingest** packs OCR layout blocks into ≤ 250-token, page-bounded chunks (a unit that
doesn't fit moves whole to the next chunk, so no word is cut) with IDs
`sha256(pdf)[:16]:chunk` — unique across documents, idempotent on re-ingest. **Hybrid +
rerank** because dense search misses exact names and figures and BM25 catches them; the
reranker's score, unlike e5 similarity, separates relevant from irrelevant, so it powers
the "not found" gate.

## 5. Technology choices and trade-offs

| Need | Choice | Why | Trade-off / rejected |
|---|---|---|---|
| OCR | Tesseract 5 | Word boxes + confidence, light, CPU | Weak on poor scans → docTR / cloud OCR behind `OcrEngine` |
| PDF → image | PyMuPDF | Page size in points, rotation | AGPL → pypdfium2 for commercial use |
| NER | spaCy `en_core_web_lg` | Only model with P/R ≥ 0.90 and zero ORG leaks; no torch | `sm` tagged "Atlas"/"Forbes" as people |
| Matching | rapidfuzz | Full-string similarity | thefuzz is a wrapper over it |
| Embeddings | multilingual-e5-small | Spanish + English, CPU | MiniLM English-only; bge-m3 too heavy |
| Reranker | mmarco-mMiniLMv2-L12 | Multilingual, 1.5 s/question on CPU | bge-reranker-v2-m3: 21 s on CPU |
| Vector store | Chroma, embedded | Zero infrastructure; volume in Docker | Single writer; Qdrant one adapter away |
| LLM | Groq gpt-oss-120b | Any OpenAI-compatible endpoint by config | Free tier ≈ 30 req/min |

## 6. Scaling to 1000+ PDFs/hour

![Scaling: async API, object storage, queue, autoscaled OCR workers, results and vector DB](docs/design/scaling.svg)

1000 PDFs/h = 0.28 PDF/s; at ~2–3 CPU-s per page, a 5-page average keeps ~4 cores busy
(~8 with headroom). The upload returns `202` + job id, stateless OCR workers (this same
image) autoscale on queue depth, OCR is cached by content hash, and the vector store
becomes a service with native hybrid search.

## 7. Failure modes and mitigations

| Failure | Mitigation | Response |
|---|---|---|
| Not a PDF / empty / too big / encrypted | Checked by content before any OCR | 4xx, specific code |
| Tesseract missing or stuck | Per-page timeout | 503 `ocr_unavailable` |
| Noisy scan | Low-confidence words dropped | fewer names, no box over noise |
| LLM slow / rate-limited / down | SDK timeout + backoff; extract/ingest unaffected | 503/502 `llm_*` |
| LLM invents a source | Sources built from cited passages only | impossible by construction |
| Question not covered | Rerank-score gate, no LLM call | "not found" |
| Prompt injection | Passages delimited as data, no tools, plain-text UI | golden probe passes |
| Duplicate ingest | Content-hash IDs | idempotent upsert |
| ALL-CAPS documents | Known limit of the NER | documented |

## 8. Routing between models by query complexity

`AnswerGenerator` is a port, so a router is one more adapter. A **deterministic** router
scores the question after retrieval (passages above the gate, comparison / aggregation /
"why" cues, length): simple lookups → small fast model (`gpt-oss-20b`), multi-passage or
reasoning → large model (`gpt-oss-120b`); if the small model returns no valid citation
while the gate found evidence, retry once on the large one. Thresholds are tuned on the
golden Q&A set (pass^3 and cost), never decided by the LLM.
