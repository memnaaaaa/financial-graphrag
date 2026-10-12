"""Build indexes on a chunks file and show top hits for ad-hoc queries (sanity check, no gold labels needed)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag.data import load_chunks
from rag.embed import Encoder
from rag.retrieve import Retriever

chunks = load_chunks(sys.argv[1])
queries = sys.argv[2:] or ["What was Apple's total net sales in fiscal 2025?"]
for ek in ("bge-small", "distilbert"):
    t = time.time(); enc = Encoder(ek); ret = Retriever(enc, chunks, rerank=True)
    print(f"\n=== {ek} on {enc.model.device}: {len(chunks)} chunks indexed in {time.time()-t:.0f}s")
    for q in queries:
        for rr in (False, True):
            ret_ = ret if rr else Retriever.__new__(Retriever)
            if not rr:
                ret_.__dict__.update(ret.__dict__); ret_.reranker = None
            r = ret_.search(q, 3)
            print(f"Q: {q} [{'rerank' if rr else 'dense'}] {r.retrieve_ms+r.rerank_ms:.0f}ms")
            for cid, s in zip(r.chunk_ids, r.scores): print(f"   {s:.3f} {cid}")
