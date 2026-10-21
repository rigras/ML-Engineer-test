# Changelog — rag

## 2026-10-21 — Approval
- Approved by the human gate (Pablo): T-004 v2 (after CR-001).

## 2026-10-21 — CR-001 (Type B)
- Spike S6 preliminary run: bge-reranker-v2-m3 21.1 s / 20 pairs on CPU (budget 2 s).
- TRD §8.2, §15 S6 and ADR-014 updated: default reranker
  `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, 2.0 s).
- Regenerated: T-004 (v1→v2). Back to pending-approval.

## 2026-10-21 — Approval
- Approved by the human gate (Pablo): T-001…T-006. Before approval, at his request:
  T-001 / ADR-015 now split an oversized paragraph only between sentences (then words),
  never at visual lines; spec.md states explicitly that different documents never
  overwrite each other and only an identical PDF replaces its own chunks.

## 2026-10-21 — Initial generation
- Created T-001…T-006 from `README.md` (PRD) + `docs/trds/document-intelligence-trd.md`
  (v0.1 with the 2026-10-21 RAG revisions) + ADR-014 + ADR-015, scoped to TRD §14 phase
  P2. All pending-approval.
