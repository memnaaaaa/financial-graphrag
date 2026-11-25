"""Score G-reasoner document retrieval on the team golden set, the same way the vector baseline is scored.

Uses golden set v2 (vector_rag_baseline/data/questions_v2.jsonl) and vector_rag_baseline/rag/metrics.py
from the repo, and writes per_question.jsonl + summary.json in the baseline's format (config "g-reasoner"),
so the two can be compared row by row and fed to the baseline's scripts/results_by_type.py. Questions whose
gold chunks are not all document nodes in the graph are skipped and listed.

AllFacts@k needs `fact_chunks` (gold fact -> chunks that state it) in the question file. Without it,
all_facts falls back to hit (as the baseline's run_eval.py does); this is printed as a warning and recorded
in each row as "all_facts_source".

    python evaluate.py --root <data root> --out <results dir>
    python evaluate.py --root <data root> --out <results dir> --layer-log    # + layers.jsonl for the hop analysis

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
    qpath = questions_path or os.path.join(repo, "vector_rag_baseline", "data", "questions_v2.jsonl")
    questions = [json.loads(line) for line in open(qpath, encoding="utf-8") if line.strip()]
    docs = {retriever.qa_data.id2node[i.item()] for i in retriever.graph.nodes_by_type["document"]}
    covered = [q for q in questions if all(g in docs for g in q["gold_chunk_ids"])]
    return covered, [q["qid"] for q in questions if q not in covered]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--root", required=True)
    ap.add_argument("--data-name", default="fin10k_v1")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("--questions", default=None, help="default: <repo>/vector_rag_baseline/data/questions_v2.jsonl")
    ap.add_argument("--ks", nargs="+", type=int, default=[5, 10])
    ap.add_argument("--start-nodes", default=None, help="start_nodes.jsonl from gemini_ner.py")
    ap.add_argument("--layer-log", action="store_true",
                    help="also write layers.jsonl: node scores after every GNN layer (layer_trace.py)")
    ap.add_argument("--layer-top", type=int, default=10, help="top nodes per type and layer in layers.jsonl")
    ap.add_argument("--name", default=None,
                    help='config label in the results (default "g-reasoner", or "g-reasoner-ft" for a local --model)')
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sys.path.insert(0, os.path.join(a.repo, "vector_rag_baseline"))
    from rag import metrics  # the baseline's precision/recall/hit definitions

    config = a.name or ("g-reasoner-ft" if os.path.isdir(a.model) else "g-reasoner")
    ner, match_ms = None, {}
    if a.start_nodes:
        from gfm_components import FixedNER
        saved = [json.loads(line) for line in open(a.start_nodes, encoding="utf-8") if line.strip()]
        ner = FixedNER({r["question"]: r["gemini_start_nodes"] for r in saved})
        match_ms = {r["question"]: sum(r["gemini_ms"]) / len(r["gemini_ms"]) for r in saved}
        config = a.name or "g-reasoner+gemini-ner"
    retriever, ner = load_retriever(a.root, a.data_name, a.model, ner=ner)
    covered, skipped = covered_questions(a.repo, a.questions, retriever)
    print(f"{len(covered)} questions covered by the graph; skipped (gold not in graph): {skipped}")
    no_facts = [q["qid"] for q in covered if not q.get("fact_chunks")]
    if no_facts:
        print(f"WARNING: {len(no_facts)}/{len(covered)} questions have no fact_chunks; AllFacts falls back to "
              f"Hit for them and is NOT comparable to a run that has fact_chunks")
    if a.layer_log:
        from layer_trace import LayerTrace
        os.makedirs(a.out, exist_ok=True)
        layer_out = open(os.path.join(a.out, "layers.jsonl"), "w", encoding="utf-8")

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
        if a.layer_log:  # separate pass, so the hooks do not count in the latency above
            with LayerTrace(retriever) as tr:
                retriever.retrieve(q["question"], top_k=1)
            start_ids = [retriever.qa_data.node2id[n] for n in start if n in retriever.qa_data.node2id]
            trace = tr.summarize(retriever, start_ids, q["gold_chunk_ids"], top_n=a.layer_top)
            layer_out.write(json.dumps({"qid": q["qid"], "type": q.get("type"), "hops": q.get("hops"),
                                        "question": q["question"], "start_nodes": start, **trace}) + "\n")
            if trace["max_abs_diff_last_layer"] > 1e-2:
                print(f"  WARNING {q['qid']}: last-layer readout differs from the model output by "
                      f"{trace['max_abs_diff_last_layer']:.3g}; check layer_trace.py against this gfmrag version")
        for k in a.ks:
            hit = metrics.hit_at_k(ranked, q["gold_chunk_ids"], k)
            facts = (dict(metrics.facts_found(ranked, q["fact_chunks"], k), all_facts_source="fact_chunks")
                     if q.get("fact_chunks") else
                     {"facts_total": 1, "facts_found": hit, "missing_facts": [], "all_facts": hit,
                      "all_facts_source": "hit_fallback"})
            rows.append({
                "config": config, "k": k, "qid": q["qid"], "type": q.get("type"), "hops": q.get("hops"),
                "companies": q.get("companies"),
                "retrieved": ranked[:k],
                "precision": metrics.precision_at_k(ranked, q["gold_chunk_ids"], k),
                "hit": hit,
                **facts,
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
                        f"AllFacts@{k}": sum(r["all_facts"] for r in rs) / len(rs),
                        "all_facts_from_fact_chunks": sum(r["all_facts_source"] == "fact_chunks" for r in rs),
                        "retrieval_ms": metrics.latency_stats([r["retrieve_ms"] for r in rs])["mean_ms"],
                        "matching_ms": sum(r["matching_ms"] for r in rs) / len(rs),
                        "total_ms": sum(r["total_ms"] for r in rs) / len(rs),
                        "skipped_qids": skipped})
    if a.layer_log:
        layer_out.close()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "per_question.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=2)
    print()
    for s in summary:
        k = s["k"]
        print(f"{config} k={k}: P@{k} {s[f'P@{k}']:.3f}  R@{k} {s[f'R@{k}']:.3f}  Hit@{k} {s[f'Hit@{k}']:.2f}  "
              f"AllFacts@{k} {s[f'AllFacts@{k}']:.2f} ({s['all_facts_from_fact_chunks']}/{s['n']} from fact_chunks)  "
              f"retrieval {s['retrieval_ms']:.0f} ms, total {s['total_ms']:.0f} ms  (n={s['n']})")
    print("saved to", a.out)


if __name__ == "__main__":
    main()
