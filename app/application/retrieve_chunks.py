"""Retrieve-chunks step of /ask: hybrid candidates → rerank → gate (TRD ADR-014).

Every question goes through the same pipeline — no question-type special cases:
meaning-based candidates (dense) plus exact-term candidates (BM25), reranked together by a
cross-encoder; if even the best one scores below the gate, nothing is relevant.
"""

import logging
from dataclasses import dataclass
from time import perf_counter

from app.application.ports import Embedder, Reranker, VectorStore
from app.domain.chunking import Chunk
from app.domain.lexical import rank_by_terms

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    """A retrieved chunk with its rerank score (higher = more relevant)."""

    chunk: Chunk
    score: float


class RetrieveChunks:
    """Find the few chunks most likely to answer a question, or nothing."""

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        reranker: Reranker,
        candidates: int,
        top_k: int,
        min_score: float,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._reranker = reranker
        self._candidates = candidates
        self._top_k = top_k
        self._min_score = min_score

    def execute(self, question: str) -> tuple[ScoredChunk, ...]:
        """Up to ``top_k`` chunks, best first; empty when nothing clears the gate."""
        stats: dict[str, object] = {"dense_count": 0, "lexical_count": 0, "top_score": None}
        ranked = self._rank(question, stats)
        relevant = bool(ranked) and ranked[0].score >= self._min_score
        retrieved = tuple(ranked) if relevant else ()
        stats["returned_count"] = len(retrieved)
        stats["outcome"] = "relevant" if relevant else "nothing_relevant"
        logger.info("retrieval_completed", extra=stats)
        return retrieved

    def _rank(self, question: str, stats: dict[str, object]) -> list[ScoredChunk]:
        stored = self._store.all_chunks()
        if not stored:  # nothing ingested: don't load the models for nothing
            return []

        started = perf_counter()
        embedding = self._embedder.embed_question(question)
        stats["embed_ms"] = _elapsed_ms(started)

        started = perf_counter()
        dense = self._store.search(embedding, self._candidates)
        by_id = {chunk.id: chunk for chunk in stored}
        documents = [(chunk.id, chunk.text) for chunk in stored]
        lexical = [by_id[i] for i, _ in rank_by_terms(question, documents, self._candidates)]
        candidates = list({chunk.id: chunk for chunk in dense + lexical}.values())
        stats["search_ms"] = _elapsed_ms(started)

        started = perf_counter()
        scores = self._reranker.score(question, [chunk.text for chunk in candidates])
        ranked = sorted(
            (ScoredChunk(chunk, score) for chunk, score in zip(candidates, scores, strict=True)),
            key=lambda scored: scored.score,
            reverse=True,
        )[: self._top_k]
        stats["rerank_ms"] = _elapsed_ms(started)

        stats.update(
            dense_count=len(dense),
            lexical_count=len(lexical),
            candidate_count=len(candidates),
            top_score=round(ranked[0].score, 4) if ranked else None,
        )
        return ranked


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 1)
