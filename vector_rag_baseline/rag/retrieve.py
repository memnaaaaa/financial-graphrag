import time
from dataclasses import dataclass

from sentence_transformers import CrossEncoder

from . import config
from .index import load_or_build


@dataclass
class Retrieval:
    chunk_ids: list[str]
    scores: list[float]
    retrieve_ms: float  # query embedding + FAISS search
    rerank_ms: float = 0.0


class Retriever:
    def __init__(self, encoder, chunks, rerank: bool = False):
        self.encoder, self.chunks = encoder, chunks
        self.index = load_or_build(encoder, chunks)
        self.reranker = CrossEncoder(config.RERANKER) if rerank else None

    def search(self, query: str, k: int) -> Retrieval:
        pool = max(k, config.RERANK_POOL) if self.reranker else k
        pool = min(pool, len(self.chunks))
        t0 = time.perf_counter()
        q = self.encoder.encode_queries([query])
        scores, ids = self.index.search(q, pool)
        t1 = time.perf_counter()
        hits = [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
        rerank_ms = 0.0
        if self.reranker:
            ce = self.reranker.predict([(query, self.chunks[i].text) for i, _ in hits])
            hits = sorted(zip([i for i, _ in hits], map(float, ce)), key=lambda x: -x[1])
            rerank_ms = (time.perf_counter() - t1) * 1000
        hits = hits[:k]
        return Retrieval(
            [self.chunks[i].chunk_id for i, _ in hits],
            [s for _, s in hits],
            (t1 - t0) * 1000,
            rerank_ms,
        )

    def get(self, chunk_id):
        return next(c for c in self.chunks if c.chunk_id == chunk_id)
