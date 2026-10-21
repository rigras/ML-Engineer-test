# Extraction pipeline (load when touching OCR, NER, boxes, coordinates, or matching)

Source: README §`POST /api/extract` + §Correctness details; TRD ADR-002…ADR-005.

## Invariants (graded — each needs a test)

- **Every page is OCR'd, including page 0.** Page numbers in output are **0-based**.
- **Boxes are in PDF points** (72/inch), **top-left origin, y down** (PyMuPDF/pdf.js
  convention, ADR-003), inside the page rect. Never raw pixels.
  `pt = px × 72 / DPI` — converted **once, in the OCR adapter**; domain words are always
  in points.
- **PERSON only.** spaCy label `PERSON` (English) / `PER` (Spanish model). ORG, GPE,
  DATE, PRODUCT, etc. are discarded.
- **One box per real occurrence.** A name repeated 5 times yields 5 entries.
- **Honorifics** (`Dr.`, `Prof.`, `Mr.`, `Ms.`, `Mrs.`) are not part of the name or box.
- **Name wrapping lines** → one box per line segment (never a union spanning lines).

## Alignment algorithm (ADR-004)

1. OCR adapter returns, per page, ordered `Word(text, box_pt, confidence, line_id)`.
2. Domain builds the page text by joining words (space within a line, `\n` between
   lines) and records each word's `[start, end)` char span.
3. NER runs on that page text → entity char spans.
4. Each entity span maps to the words whose spans overlap it → merge their boxes per
   line → occurrence.
5. Words below the OCR confidence floor (config) are excluded from alignment.

No fuzzy string search is used for *location* — only char offsets.

## Fuzzy matching (ADR-005)

- Normalize both sides: casefold → NFKD + drop combining marks → strip honorifics and
  punctuation → collapse whitespace. (`María González` → `maria gonzalez`.)
- Score with `rapidfuzz.fuzz.ratio` (full string; never `partial_ratio`/`token_set_ratio`
  — they inflate substring matches like `Ana` vs `Ana María Rodríguez`).
- Requested name = `f"{first_name} {last_name}"`. Report only `score ≥ threshold`
  (config, default 0.90). Scores in the response are 0..1.

## Known tricky inputs from `sample_pdfs/`

`Dr. Yuki Tanaka`, `Kevin O’Brien` (curly apostrophe), `Fatima Al-Rashidi` (hyphen),
`Prof. Michael O’Sullivan`, repeated `Richard Hernandez`, ORGs `NovaTech Solutions`,
`ETH Zurich`, `Stanford University`, and the false positive `'Atlas'`.
