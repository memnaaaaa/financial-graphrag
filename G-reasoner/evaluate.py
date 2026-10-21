"""Score G-reasoner document retrieval on the team golden set, the same way the vector baseline is scored.

Uses vector_rag_baseline/data/questions.jsonl and vector_rag_baseline/rag/metrics.py from the repo,
and writes per_question.jsonl + summary.json in the baseline's format (config "g-reasoner"), so
the two can be compared row by row. Questions whose gold chunks are not all in the graph are
skipped and listed (fin10k_v0 only has JNJ, AAPL and MSFT).

    python evaluate.py --repo <repo> --root <data root> --out <results dir>

With --start-nodes (gemini_ner.py output) the start nodes come from that file instead of the
rule-based matcher; the file's matching time is added to the latency (config "g-reasoner+gemini-ner").
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from query import load_retriever  # noqa: E402


def covered_questions(repo, questions_path, retriever):
    """(questions whose gold chunks are all document nodes in the graph, skipped qids)."""
    qpath = questions_path or os.path.join(repo, "vector_rag_baseline", "data", "questions.jsonl")
    questions = [json.loads(line) for line in open(qpath, encoding="utf-8") if line.strip()]
    docs = {retriever.qa_data.id2node[i.item()] for i in retriever.graph.nodes_by_type["document"]}
    covered = [q for q in questions if all(g in docs for g in q["gold_chunk_ids"])]
    return covered, [q["qid"] for q in questions if q not in covered]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--root", required=True)
    ap.add_argument("--data-name", default="fin10k_v0")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("--questions", default=None, help="default: <repo>/vector_rag_baseline/data/questions.jsonl")
    ap.add_argument("--ks", nargs="+", type=int, default=[5, 10])
    ap.add_argument("--start-nodes", default=None, help="start_nodes.jsonl from gemini_ner.py")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sys.path.insert(0, os.path.join(a.repo, "vector_rag_baseline"))
    from rag import metrics  # the baseline's precision/recall/hit definitions

    config, ner, match_ms = "g-reasoner", None, {}
    if a.start_nodes:
        from gfm_components import FixedNER
        saved = [json.loads(line) for line in open(a.start_nodes, encoding="utf-8") if line.strip()]
        ner = FixedNER({r["question"]: r["gemini_start_nodes"] for r in saved})
        match_ms = {r["question"]: sum(r["gemini_ms"]) / len(r["gemini_ms"]) for r in saved}
        config = "g-reasoner+gemini-ner"
    retriever, ner = load_retriever(a.root, a.data_name, a.model, ner=ner)
    covered, skipped = covered_questions(a.repo, a.questions, retriever)
    print(f"{len(covered)} questions covered by the graph; skipped (gold not in graph): {skipped}")

    # The first query with start nodes loads (or compiles) G-reasoner's CUDA kernel: keep that out of the
    # latency. A query without entities does not run the GNN, so warm up with a real question.
    retriever.retrieve(covered[0]["question"], top_k=1)
    rows = []
    for q in covered:
        t0 = time.perf_counter()
        res = retriever.retrieve(q["question"], top_k=max(a.ks), target_types=["document", "entity", "attribute"])
        ms = (time.perf_counter() - t0) * 1000
        ranked = [it["id"] for it in res["document"]]
        if a.start_nodes and q["question"] not in match_ms:
            sys.exit(f"{q['qid']} has no saved start nodes; rerun gemini_ner.py")
        t1 = time.perf_counter()
        start = ner(q["question"])
        # rule matching runs inside retrieve() and is part of ms already; Gemini ran beforehand
        ner_ms = match_ms[q["question"]] if a.start_nodes else (time.perf_counter() - t1) * 1000
        for k in a.ks:
            rows.append({
                "config": config, "k": k, "qid": q["qid"], "type": q.get("type"),
                "retrieved": ranked[:k],
                "precision": metrics.precision_at_k(ranked, q["gold_chunk_ids"], k),
                "hit": metrics.hit_at_k(ranked, q["gold_chunk_ids"], k),
                "recall": metrics.recall_at_k(ranked, q["gold_chunk_ids"], k),
                "retrieve_ms": ms, "rerank_ms": 0.0, "start_nodes": start, "matching_ms": ner_ms,
                "total_ms": ms + (ner_ms if a.start_nodes else 0.0),
                "top_entities": [it["id"] for it in res["entity"][:5]],
                "top_attributes": [it["id"] for it in res["attribute"][:5]],
            })
        r5 = next(r for r in rows[-len(a.ks):] if r["k"] == min(a.ks))
        print(f"  {q['qid']} [{q.get('type')}] hit@{min(a.ks)}={r5['hit']} recall={r5['recall']:.2f}  start={start}")

    summary = []
    for k in a.ks:
        rs = [r for r in rows if r["k"] == k]
        summary.append({"config": config, "k": k, "n": len(rs),
                        f"P@{k}": sum(r["precision"] for r in rs) / len(rs),
                        f"R@{k}": sum(r["recall"] for r in rs) / len(rs),
                        f"Hit@{k}": sum(r["hit"] for r in rs) / len(rs),
                        "retrieval_ms": metrics.latency_stats([r["retrieve_ms"] for r in rs])["mean_ms"],
                        "matching_ms": sum(r["matching_ms"] for r in rs) / len(rs),
                        "total_ms": sum(r["total_ms"] for r in rs) / len(rs),
                        "skipped_qids": skipped})
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "per_question.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=2)
    print()
    for s in summary:
        k = s["k"]
        print(f"{config} k={k}: P@{k} {s[f'P@{k}']:.3f}  R@{k} {s[f'R@{k}']:.3f}  Hit@{k} {s[f'Hit@{k}']:.2f}  "
              f"retrieval {s['retrieval_ms']:.0f} ms, total {s['total_ms']:.0f} ms  (n={s['n']})")
    print("saved to", a.out)


if __name__ == "__main__":
    main()
