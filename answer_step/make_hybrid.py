"""Item 1: hybrid retrieval = vector RAG chunks + graph retriever chunks and nodes, in one retrieval file.

    python answer_step/make_hybrid.py --graph G-reasoner/results/finetuned_fin10k_v1/per_question.jsonl --name hybrid_finetuned
    -> answer_step/retrievals/hybrid_finetuned.jsonl, which answer.py reads like any other retrieval file

Chunks: the two ranked lists interleaved (vector 1st, graph 1st, vector 2nd, ...), duplicates skipped, cut at
k (10), so each retriever contributes about k/2 chunks. Entities, Values and start nodes come from the graph
retriever. The input files are only read.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import retrievals  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vector", default=os.path.join(REPO, "vector_rag_baseline/results/v2_all_baselines/per_question_all.jsonl"))
    ap.add_argument("--vector-config", default="bge-small+rerank")
    ap.add_argument("--graph", required=True, help="graph retriever per_question.jsonl (G-reasoner or PPR)")
    ap.add_argument("--name", required=True)
    ap.add_argument("--k", type=int, default=10)
    a = ap.parse_args()
    vec = retrievals.load(a.vector, "vector", a.vector_config, a.k)
    gra = retrievals.load(a.graph, "graph", None, a.k)
    os.makedirs(os.path.join(HERE, "retrievals"), exist_ok=True)
    out = os.path.join(HERE, "retrievals", f"{a.name}.jsonl")
    n_from = {"vector": 0, "graph": 0}
    with open(out, "w", encoding="utf-8") as fh:
        for qid in sorted(set(vec) & set(gra)):
            v, g = vec[qid]["chunks"], gra[qid]["chunks"]
            merged = []
            for i in range(max(len(v), len(g))):
                for src, lst in (("vector", v), ("graph", g)):
                    if i < len(lst) and lst[i] not in merged and len(merged) < a.k:
                        merged.append(lst[i])
                        n_from[src] += 1
            fh.write(json.dumps({"qid": qid, "k": a.k, "config": a.name, "retrieved": merged,
                                 "top_entities": gra[qid]["entities"], "top_attributes": gra[qid]["values"],
                                 "start_nodes": gra[qid]["start_nodes"],
                                 "vector_chunks": v, "graph_chunks": g}) + "\n")
    print(f"{len(set(vec) & set(gra))} questions -> {out}; chunks from vector {n_from['vector']}, graph {n_from['graph']}")


if __name__ == "__main__":
    main()
