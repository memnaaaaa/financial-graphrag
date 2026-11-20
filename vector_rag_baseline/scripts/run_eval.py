"""Embed -> index -> retrieve -> generate -> judge -> metrics.

  python scripts/run_eval.py --chunks data/dummy_chunks.jsonl --questions data/dummy_questions.jsonl
  python scripts/run_eval.py ... --encoders bge-small distilbert --rerank --no-llm   # retrieval metrics only
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag import config, error_stage, generate, judge, metrics
from rag.data import check_gold_ids, load_chunks, load_questions
from rag.embed import Encoder
from rag.retrieve import Retriever

ap = argparse.ArgumentParser()
ap.add_argument("--chunks", required=True)
ap.add_argument("--questions", required=True)
ap.add_argument("--encoders", nargs="+", default=["bge-small"], choices=list(config.ENCODERS))
ap.add_argument("--rerank", action="store_true", help="also run cross-encoder rerank of top-20")
ap.add_argument("--no-llm", action="store_true", help="skip Gemini generation + Gemini judge")
ap.add_argument("--tickers", nargs="+", default=None, help="keep only chunks of these tickers (e.g. JNJ AAPL MSFT)")
ap.add_argument("--ks", nargs="+", type=int, default=list(config.KS))
ap.add_argument("--out", default=None)
a = ap.parse_args()

chunks, questions = load_chunks(a.chunks), load_questions(a.questions)
if a.tickers:
    chunks = [c for c in chunks if c.meta.get("ticker") in set(a.tickers)]
check_gold_ids(questions, chunks)
by_id = {c.chunk_id: c for c in chunks}
print(f"{len(chunks)} chunks, {len(questions)} questions")

gen = jdg = None
if not a.no_llm:
    from rag.llm import Gemini, get_judge_llm
    gen, jdg = Gemini(), get_judge_llm()

out_dir = Path(a.out) if a.out else config.RESULTS_DIR / time.strftime("%Y%m%d-%H%M%S")
out_dir.mkdir(parents=True, exist_ok=True)
rows, summary = [], []

for ek in a.encoders:
    enc = Encoder(ek)
    for rerank in [False] + ([True] if a.rerank else []):
        ret = Retriever(enc, chunks, rerank=rerank)
        name = f"{ek}{'+rerank' if rerank else ''}"
        ret.search("warm-up", 1)  # exclude one-time model warm-up from latency
        for k in a.ks:
            recs = []
            for q in questions:
                r = ret.search(q["question"], k)
                rec = {
                    "config": name, "k": k, "qid": q["qid"], "retrieved": r.chunk_ids,
                    "precision": metrics.precision_at_k(r.chunk_ids, q["gold_chunk_ids"], k),
                    "hit": metrics.hit_at_k(r.chunk_ids, q["gold_chunk_ids"], k),
                    **(metrics.facts_found(r.chunk_ids, q["fact_chunks"], k) if q.get("fact_chunks") else
                       {"facts_total": 1, "facts_found": int(metrics.hit_at_k(r.chunk_ids, q["gold_chunk_ids"], k)),
                        "missing_facts": [], "all_facts": metrics.hit_at_k(r.chunk_ids, q["gold_chunk_ids"], k)}),
                    "recall": metrics.recall_at_k(r.chunk_ids, q["gold_chunk_ids"], k),
                    "retrieve_ms": r.retrieve_ms, "rerank_ms": r.rerank_ms,
                }
                if gen:
                    passages = [(c, ret.get(c).text) for c in r.chunk_ids]
                    rec["answer"], rec["generate_ms"] = generate.answer(gen, q["question"], passages)
                    tj = time.perf_counter()
                    j = judge.judge(jdg, q["question"], q["gold_answer"], rec["answer"])
                    rec["judge_ms"] = (time.perf_counter() - tj) * 1000
                    rec["verdict"], rec["judge_reason"] = j["verdict"], j["reason"]
                    # traceability: numbers vs cited chunks, and citation accuracy (string checks, no LLM)
                    ctext = {c: ret.get(c).text for c in r.chunk_ids}
                    cfil = {c: f"{ret.get(c).meta.get('ticker')} {ret.get(c).meta.get('fiscal_year')}" for c in r.chunk_ids}
                    gfil = set(q.get("filings") or [f"{by_id[g].meta.get('ticker')} {by_id[g].meta.get('fiscal_year')}" for g in q["gold_chunk_ids"]])
                    cited = [c for c in metrics.cited_ids(rec["answer"]) if c in ctext]
                    rec["cited_ids"] = cited
                    rec.update(metrics.unsupported_numbers(rec["answer"], [ctext[c] for c in cited], q["question"]))
                    rec.update(metrics.citation_accuracy(rec["answer"], ctext, cfil, gfil, q["question"]))
                    rec.update(metrics.answer_support(rec["answer"], ctext))
                    rec["error_stage"] = error_stage.tag(rec["verdict"], bool(rec["all_facts"]))
                    rec["total_ms"] = rec["retrieve_ms"] + rec["rerank_ms"] + rec["generate_ms"]
                recs.append(rec)
                print(f"  [{name} k={k}] {q['qid']} hit={rec['hit']} " + (rec.get("verdict", "") if gen else ""), flush=True)
            rows += recs
            s = {"config": name, "k": k,
                 f"P@{k}": sum(r["precision"] for r in recs) / len(recs),
                 f"R@{k}": sum(r["recall"] for r in recs) / len(recs),
                 f"Hit@{k}": sum(r["hit"] for r in recs) / len(recs),
                 f"AllFacts@{k}": sum(r["all_facts"] for r in recs) / len(recs),
                 "retrieval_ms": metrics.latency_stats([r["retrieve_ms"] + r["rerank_ms"] for r in recs])["mean_ms"]}
            if gen:
                s["judge_mean_ms"] = sum(r["judge_ms"] for r in recs) / len(recs)
                s.update(metrics.judge_rates([r["verdict"] for r in recs]))
                s.update(metrics.aggregate_traceability(recs))
                stages = [r["error_stage"] for r in recs]
                s.update({f"stage_{st}": stages.count(st) / len(stages) for st in error_stage.STAGES})
                s.update({"e2e_" + k_: v for k_, v in metrics.latency_stats([r["total_ms"] for r in recs]).items()})
            summary.append(s)

(out_dir / "per_question.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
for s in summary:
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in s.items()})
print("saved to", out_dir)
