"""Checks each finalized tool individually. Run before swapping in Mohini's file."""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np

from rag import config, generate
from rag.data import load_chunks

results = []


def check(name, fn):
    try:
        msg = fn()
        results.append((name, "PASS", msg or ""))
    except Exception as e:
        traceback.print_exc()
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))


chunks = load_chunks(config.ROOT / "data" / "dummy_chunks.jsonl")
texts = [c.text for c in chunks]


def encoder_check(key):
    def f():
        from rag.embed import Encoder
        from rag.index import build_index

        enc = Encoder(key)
        v = enc.encode_docs(texts)
        assert v.shape == (len(texts), enc.dim) and v.dtype == np.float32
        assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-4), "vectors not normalized"
        idx = build_index(v)
        assert type(idx).__name__ == "IndexFlatIP"
        q = enc.encode_queries(["How many supermarkets does Cedar Grocers operate?"])
        _, ids = idx.search(q, 3)
        top = chunks[ids[0][0]].chunk_id
        assert top == "cedar_2024_item1_001", f"top-1 was {top}"
        params = sum(p.numel() for p in enc.model.parameters()) / 1e6
        return f"{enc.name}: dim={enc.dim}, {params:.0f}M params, top-1 ok"
    return f


def rerank_check():
    from rag.embed import Encoder
    from rag.retrieve import Retriever

    r = Retriever(Encoder("bge-small"), chunks, rerank=True).search("Where is Borealis's fabrication facility?", 5)
    assert len(r.chunk_ids) == 5 and r.rerank_ms > 0
    return f"{config.RERANKER}: top-1={r.chunk_ids[0]}, rerank {r.rerank_ms:.0f}ms"


def gemini_check():
    from rag.llm import Gemini

    g = Gemini()
    out = g.generate(generate.build_prompt("What is Acme's gross margin?", [(chunks[2].chunk_id, chunks[2].text)]), generate.SYSTEM)
    assert "38.5" in out, out
    return f"{g.model} via {g.backend}: {out[:60]!r}"


def groq_check():
    from rag.judge import judge
    from rag.llm import get_judge_llm

    g = get_judge_llm()
    ok = judge(g, "Gross margin?", "38.5%", "The gross margin was 38.5%.")["verdict"]
    bad = judge(g, "Gross margin?", "38.5%", "The gross margin was 12%.")["verdict"]
    miss = judge(g, "Gross margin?", "38.5%", "I cannot answer from the provided context.")["verdict"]
    assert (ok, bad, miss) == ("correct", "hallucination", "missing"), (ok, bad, miss)
    return f"{g.model} via {getattr(g, 'backend', 'groq')}: correct/hallucination/missing all judged right"


for k in config.ENCODERS:
    check(f"encoder+faiss [{k}]", encoder_check(k))
check("cross-encoder rerank", rerank_check)
check("Gemini generator", gemini_check)
check("Judge (Flash)", groq_check)

print("\n" + "=" * 70)
for n, s, m in results:
    print(f"{s:5} {n:28} {m}")
sys.exit(any(s == "FAIL" for _, s, _ in results))
