"""Build one labeling file per question: 40 candidate chunks pooled from bge-small + DistilBERT + BM25.
Pool = ~32 chunks from the filings the question names (reciprocal-rank fusion of the 3 retrievers, balanced across
companies) + ~8 off-target chunks (global fusion hits from other filings/years) so the labeler must reject distractors.
Order is shuffled; reference answers are NOT included (independent labeling)."""
import json, random, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rank_bm25 import BM25Okapi
from rag import config
from rag.data import load_chunks, load_questions
from rag.embed import Encoder
from rag.index import load_or_build

PER_FILING, OFF = int(sys.argv[1]) if len(sys.argv) > 1 else 32, 8   # chunks per named filing + off-target distractors
chunks = load_chunks("data/chunks.jsonl"); questions = load_questions("data/questions.jsonl")
cy = lambda cid: "_".join(cid.split("_")[:2])
filing = np.array([cy(c.chunk_id) for c in chunks])
tok = lambda t: re.findall(r"[a-z0-9$%.,]+", t.lower())
bm25 = BM25Okapi([tok(c.text) for c in chunks])

rank_lists = {}  # qid -> list of full-corpus rankings (arrays of indices), one per retriever
encs = {k: Encoder(k) for k in ("bge-small", "distilbert")}
idx = {k: load_or_build(encs[k], chunks) for k in encs}
for q in questions:
    lists = []
    for k, enc in encs.items():
        s, i = idx[k].search(enc.encode_queries([q["question"]]), len(chunks)); lists.append(i[0])
    lists.append(np.argsort(-bm25.get_scores(tok(q["question"]))))
    rank_lists[q["qid"]] = lists


def rrf(lists, allowed=None, kconst=60):
    score = {}
    for L in lists:
        r = 0
        for i in L:
            if allowed is not None and filing[i] not in allowed: continue
            r += 1; score[int(i)] = score.get(int(i), 0) + 1 / (kconst + r)
    return sorted(score, key=lambda i: -score[i])


out = Path("data/labeling"); out.mkdir(parents=True, exist_ok=True)
cov = []
for q in questions:
    # filings named by the question = company-years of the existing gold ids (the question text names them explicitly)
    fil = sorted({cy(g) for g in q["gold_chunk_ids"]})
    per = PER_FILING
    POOL = per * len(fil) + OFF
    chosen = []
    for f in fil:
        chosen += rrf(rank_lists[q["qid"]], allowed={f})[:per]
    for i in rrf(rank_lists[q["qid"]]):                     # off-target distractors
        if len([c for c in chosen if filing[c] not in fil]) >= OFF: break
        if i not in chosen and filing[i] not in fil: chosen.append(i)
    for i in rrf(rank_lists[q["qid"]], allowed=set(fil)):   # top up to POOL
        if len(chosen) >= POOL: break
        if i not in chosen: chosen.append(i)
    chosen = chosen[:POOL]
    random.Random(hash(q["qid"]) & 0xFFFF or 7).shuffle(chosen)
    cand = [{"chunk_id": chunks[i].chunk_id, "text": chunks[i].text} for i in chosen]
    body = (f"QUESTION: {q['question']}\n\nCANDIDATE CHUNKS ({len(cand)}):\n"
            + json.dumps(cand, ensure_ascii=False, indent=1))
    (out / f"{q['qid']}.txt").write_text(body, encoding="utf-8")
    ids = {c["chunk_id"] for c in cand}; g = q["gold_chunk_ids"]
    cov.append((q["qid"], len(cand), sum(x in ids for x in g), len(g), sum(1 for c in cand if cy(c["chunk_id"]) not in fil)))
    print(f"{q['qid']}: {len(cand)} chunks | current gold present {sum(x in ids for x in g)}/{len(g)} | off-target {cov[-1][4]} | ~{sum(len(c['text'].split()) for c in cand)} words")
print("\nTotal gold coverage:", sum(c[2] for c in cov), "/", sum(c[3] for c in cov))
