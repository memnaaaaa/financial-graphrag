"""Hop analysis case study (E7): follow one question's reasoning chain through G-reasoner's layers.

For one golden question, records after every GNN layer (layer_trace.py's readout) the score and the rank of
each node on the question's chain (rank among nodes of the same type, 1 = best), of every gold chunk and of
chosen distractors, together with each node's hop distance from the chain's anchor and from the nearest
start node. plot_hop_case.py draws the figure; run once per model so the two can be shown side by side.

    python hop_case.py --root <data root> --out results/hop_case/zero_shot_v2_q10.json
    python hop_case.py --root <data root> --model <finetune dir>/pretrained --name g-reasoner-ft \
        --out results/hop_case/finetuned_v2_q10.json

Default case: v2_q10 ("Which Johnson & Johnson segment sells the drug licensed from Genmab, and what were that
segment's sales in fiscal 2025?"). Its chain in fin10k_v1 is
    Genmab A/S -licensed_from- DARZALEX (JNJ) -has_product- Oncology (JNJ) -has_business_line-
    Innovative Medicine (JNJ) -has_value- "Innovative Medicine (JNJ) revenue FY2025 = $60,401 million"
    -is_mentioned_in- its source chunks (JNJ_FY2025_ITEM8_0120, _0126).
Note for the write-up: the other start nodes (Johnson & Johnson, FY2025 (JNJ), Revenue) are 1 hop from every
gold chunk through is_mentioned_in, so "hops from anchor" (Genmab) is the chain, "hops from start" the shortcut.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# qid -> (anchor, chain in order, distractors). Gold chunks are added from the question file.
CASES = {
    "v2_q10": ("Genmab A/S",
               ["Genmab A/S", "DARZALEX (JNJ)", "Oncology (JNJ)", "Innovative Medicine (JNJ)",
                "Innovative Medicine (JNJ) revenue FY2025 = $60,401 million"],
               ["DARZALEX (JNJ) revenue FY2025 = $14,351 million"]),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--root", required=True)
    ap.add_argument("--data-name", default="fin10k_v1")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("--name", default=None, help='label (default "g-reasoner", or "g-reasoner-ft" for a local --model)')
    ap.add_argument("--questions", default=None, help="default: <repo>/vector_rag_baseline/data/questions_v2.jsonl")
    ap.add_argument("--qid", default="v2_q10", choices=sorted(CASES))
    ap.add_argument("--top", type=int, default=5, help="top documents kept per layer")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import torch
    from layer_trace import MAX_HOPS, LayerTrace, hop_distance
    from query import load_retriever

    qpath = a.questions or os.path.join(a.repo, "vector_rag_baseline", "data", "questions_v2.jsonl")
    q = next((json.loads(line) for line in open(qpath, encoding="utf-8")
              if line.strip() and json.loads(line)["qid"] == a.qid), None)
    if q is None:
        sys.exit(f"{a.qid} not in {qpath}")
    anchor, chain, distractors = CASES[a.qid]
    tracked = chain + [g for g in q["gold_chunk_ids"] if g not in chain] + distractors

    name = a.name or ("g-reasoner-ft" if os.path.isdir(a.model) else "g-reasoner")
    retriever, ner = load_retriever(a.root, a.data_name, a.model)
    node2id, g = retriever.qa_data.node2id, retriever.graph
    missing = [n for n in tracked if n not in node2id]
    if missing:
        sys.exit(f"not in the graph (check CASES against {a.data_name}): {missing}")

    retriever.retrieve(q["question"], top_k=1)  # warm-up: the first GNN call compiles the kernel
    start = ner(q["question"])
    start_ids = [node2id[n] for n in start if n in node2id]
    with LayerTrace(retriever) as tr:
        res = retriever.retrieve(q["question"], top_k=10, target_types=["document"])
    diff = float((tr.scores[-1] - tr.final).abs().max())
    if diff > 1e-2:
        print(f"WARNING: last-layer readout differs from the model output by {diff:.3g}")

    from_start = hop_distance(g.edge_index, g.num_nodes, start_ids, MAX_HOPS)
    from_anchor = hop_distance(g.edge_index, g.num_nodes, [node2id[anchor]], MAX_HOPS)
    rec = tr.track(retriever, tracked)
    for n in tracked:
        i = node2id[n]
        rec[n]["role"] = "chain" if n in chain else ("gold chunk" if n in q["gold_chunk_ids"] else "distractor")
        rec[n]["hops_from_anchor"] = int(from_anchor[i]) if from_anchor[i] >= 0 else None
        rec[n]["hops_from_start"] = int(from_start[i]) if from_start[i] >= 0 else None
        rec[n]["is_start"] = i in start_ids

    doc_ids = g.nodes_by_type["document"].cpu()
    top_docs = []
    for s in tr.scores:
        top = torch.topk(s[doc_ids], a.top)
        top_docs.append([retriever.qa_data.id2node[int(i)] for i in doc_ids[top.indices]])

    out = {"qid": a.qid, "question": q["question"], "gold_answer": q.get("gold_answer"), "model": a.model,
           "name": name, "graph": a.data_name, "anchor": anchor, "start_nodes": start,
           "max_abs_diff_last_layer": diff, "tracked_order": tracked, "tracked": rec,
           "top_docs_by_layer": top_docs, "retrieved": [it["id"] for it in res["document"]]}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)

    print(f"{name} on {a.qid}: start nodes {start}")
    print(f"{'node':58} {'hops a/s':>8}  " + " ".join(f"L{l:<5}" for l in range(len(tr.scores))))
    for n in tracked:
        r = rec[n]
        h = f"{r['hops_from_anchor']}/{r['hops_from_start']}"
        print(f"{n[:58]:58} {h:>8}  " + " ".join(f"{x['rank']:<6}" for x in r["layers"]))
    print("final top-10 documents:", out["retrieved"])
    print("saved", a.out)


if __name__ == "__main__":
    main()
