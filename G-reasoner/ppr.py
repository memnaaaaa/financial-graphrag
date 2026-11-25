"""Personalized PageRank on the team graph (E4): the non-learned graph walk, as in HippoRAG.

Same inputs as evaluate.py, so the numbers compare row by row with G-reasoner:
  - graph: data/graph/<name>/processed/stage1 (nodes.csv, edges.csv), straight from the repo
  - start nodes: entity_index.EntityIndex.find(question), the rule-based matcher G-reasoner uses
  - questions: golden set v2, only those whose gold chunks are all document nodes (as evaluate.py)
  - metrics: vector_rag_baseline/rag/metrics.py when importable (it needs numpy), else the same definitions below
  - output: per_question.jsonl + summary.json in the baseline's format, config "ppr"

The walk (HippoRAG's choices):
  - every edge is undirected and counted once per node pair, whatever its relation (no learned weights)
  - restart distribution: uniform over the question's start nodes
  - damping 0.5 = probability of following an edge at each step (HippoRAG passes alpha=0.5 to PageRank)
  - power iteration to an L1 change below --tol; mass on nodes without edges goes back to the start nodes
Documents are ranked by their PPR score. A question with no start nodes gets an empty ranking (scored as
a miss); HippoRAG falls back to dense retrieval there, we do not, so the count is printed and saved.

Standard library only, no GPU:
    python ppr.py --out results/ppr_fin10k_v1
    python ppr.py --graph fin10k_v0 --out results/ppr_fin10k_v0
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from entity_index import EntityIndex  # noqa: E402

csv.field_size_limit(sys.maxsize)  # document nodes hold whole chunks in their attributes


class Metrics:
    """Same definitions as vector_rag_baseline/rag/metrics.py (used only if that file cannot be imported)."""

    @staticmethod
    def precision_at_k(retrieved, gold, k):
        return len(set(retrieved[:k]) & set(gold)) / k

    @staticmethod
    def recall_at_k(retrieved, gold, k):
        return len(set(retrieved[:k]) & set(gold)) / len(set(gold))

    @staticmethod
    def hit_at_k(retrieved, gold, k):
        return int(bool(set(retrieved[:k]) & set(gold)))

    @staticmethod
    def facts_found(retrieved, fact_chunks, k):
        top = set(retrieved[:k])
        found = [f for f, ids in fact_chunks.items() if top & set(ids)]
        return {"facts_total": len(fact_chunks), "facts_found": len(found),
                "missing_facts": [f for f in fact_chunks if f not in found],
                "all_facts": int(len(found) == len(fact_chunks))}


def load_graph(stage1):
    """(node types, adjacency as {node: set(neighbours)}) from nodes.csv and edges.csv."""
    types = {r["name"]: r["type"] for r in csv.DictReader(open(os.path.join(stage1, "nodes.csv"), encoding="utf-8"))}
    adj = defaultdict(set)
    unknown = 0
    for r in csv.DictReader(open(os.path.join(stage1, "edges.csv"), encoding="utf-8")):
        s, t = r["source"], r["target"]
        if s not in types or t not in types:
            unknown += 1
            continue
        if s != t:
            adj[s].add(t)
            adj[t].add(s)
    if unknown:
        print(f"WARNING: {unknown} edges name a node that is not in nodes.csv; ignored")
    return types, adj


def personalized_pagerank(adj, seeds, damping=0.5, tol=1e-10, max_iter=200):
    """{node: score} with restart distribution uniform over seeds. Scores sum to 1."""
    restart = {s: 1.0 / len(seeds) for s in seeds}
    p = dict(restart)
    for it in range(max_iter):
        nxt = defaultdict(float)
        dangling = 0.0
        for u, mass in p.items():
            nbrs = adj.get(u)
            if nbrs:
                share = damping * mass / len(nbrs)
                for v in nbrs:
                    nxt[v] += share
            else:
                dangling += damping * mass
        for s, w in restart.items():
            nxt[s] += (1 - damping + dangling) * w
        delta = sum(abs(nxt[n] - p.get(n, 0.0)) for n in nxt) + sum(m for n, m in p.items() if n not in nxt)
        p = nxt
        if delta < tol:
            return p, it + 1
    print(f"WARNING: PPR did not converge in {max_iter} iterations (last change {delta:.2e})")
    return p, max_iter


def ranked(scores, types, kind, n):
    items = sorted(((s, name) for name, s in scores.items() if types.get(name) == kind and s > 0), reverse=True)
    return [name for _, name in items[:n]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--graph", default="fin10k_v1", help="folder under data/graph/ in the repo")
    ap.add_argument("--questions", default=None, help="default: <repo>/vector_rag_baseline/data/questions_v2.jsonl")
    ap.add_argument("--ks", nargs="+", type=int, default=[5, 10])
    ap.add_argument("--damping", type=float, default=0.5, help="probability of following an edge (HippoRAG: 0.5)")
    ap.add_argument("--tol", type=float, default=1e-10)
    ap.add_argument("--name", default="ppr", help='config label in the results (default "ppr")')
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        sys.path.insert(0, os.path.join(a.repo, "vector_rag_baseline"))
        from rag import metrics
        print("metrics: vector_rag_baseline/rag/metrics.py")
    except ImportError as e:
        metrics = Metrics
        print(f"metrics: local copy of the baseline definitions (rag.metrics not importable: {e})")

    stage1 = os.path.join(a.repo, "data", "graph", a.graph, "processed", "stage1")
    t0 = time.perf_counter()
    types, adj = load_graph(stage1)
    index = EntityIndex(os.path.join(stage1, "nodes.csv"))
    n_edges = sum(len(v) for v in adj.values()) // 2
    print(f"{a.graph}: {len(types)} nodes, {n_edges} undirected node pairs, loaded in "
          f"{time.perf_counter() - t0:.1f}s")

    qpath = a.questions or os.path.join(a.repo, "vector_rag_baseline", "data", "questions_v2.jsonl")
    questions = [json.loads(line) for line in open(qpath, encoding="utf-8") if line.strip()]
    docs = {n for n, t in types.items() if t == "document"}
    covered = [q for q in questions if all(g in docs for g in q["gold_chunk_ids"])]
    skipped = [q["qid"] for q in questions if q not in covered]
    print(f"{len(covered)} questions covered by the graph; skipped (gold not in graph): {skipped}")
    no_facts = [q["qid"] for q in covered if not q.get("fact_chunks")]
    if no_facts:
        print(f"WARNING: {len(no_facts)}/{len(covered)} questions have no fact_chunks; AllFacts falls back to "
              f"Hit for them and is NOT comparable to a run that has fact_chunks")

    rows, no_start = [], []
    for q in covered:
        t1 = time.perf_counter()
        start = [s for s in index.find(q["question"]) if s in types]
        match_ms = (time.perf_counter() - t1) * 1000
        t2 = time.perf_counter()
        if start:
            scores, iters = personalized_pagerank(adj, start, a.damping, a.tol)
        else:
            scores, iters = {}, 0
            no_start.append(q["qid"])
        docs_ranked = ranked(scores, types, "document", max(a.ks))
        ppr_ms = (time.perf_counter() - t2) * 1000
        for k in a.ks:
            hit = metrics.hit_at_k(docs_ranked, q["gold_chunk_ids"], k)
            facts = (dict(metrics.facts_found(docs_ranked, q["fact_chunks"], k), all_facts_source="fact_chunks")
                     if q.get("fact_chunks") else
                     {"facts_total": 1, "facts_found": hit, "missing_facts": [], "all_facts": hit,
                      "all_facts_source": "hit_fallback"})
            rows.append({
                "config": a.name, "k": k, "qid": q["qid"], "type": q.get("type"), "hops": q.get("hops"),
                "companies": q.get("companies"),
                "retrieved": docs_ranked[:k],
                "precision": metrics.precision_at_k(docs_ranked, q["gold_chunk_ids"], k),
                "hit": hit,
                **facts,
                "recall": metrics.recall_at_k(docs_ranked, q["gold_chunk_ids"], k),
                "retrieve_ms": ppr_ms, "rerank_ms": 0.0, "start_nodes": start, "matching_ms": match_ms,
                "total_ms": ppr_ms + match_ms, "ppr_iterations": iters,
                "top_entities": ranked(scores, types, "entity", 5),
                "top_attributes": ranked(scores, types, "attribute", 5),
            })
        r = next(r for r in rows[-len(a.ks):] if r["k"] == min(a.ks))
        print(f"  {q['qid']} [{q.get('type')}] hit@{min(a.ks)}={r['hit']} recall={r['recall']:.2f}  start={start}")

    summary = []
    for k in a.ks:
        rs = [r for r in rows if r["k"] == k]
        summary.append({"config": a.name, "k": k, "n": len(rs),
                        f"P@{k}": sum(r["precision"] for r in rs) / len(rs),
                        f"R@{k}": sum(r["recall"] for r in rs) / len(rs),
                        f"Hit@{k}": sum(r["hit"] for r in rs) / len(rs),
                        f"AllFacts@{k}": sum(r["all_facts"] for r in rs) / len(rs),
                        "all_facts_from_fact_chunks": sum(r["all_facts_source"] == "fact_chunks" for r in rs),
                        "retrieval_ms": sum(r["retrieve_ms"] for r in rs) / len(rs),
                        "matching_ms": sum(r["matching_ms"] for r in rs) / len(rs),
                        "total_ms": sum(r["total_ms"] for r in rs) / len(rs),
                        "damping": a.damping, "graph": a.graph,
                        "no_start_node_qids": no_start, "skipped_qids": skipped})
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "per_question.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=2)
    print(f"\nno start nodes (empty ranking): {len(no_start)}/{len(covered)} {no_start}")
    for s in summary:
        k = s["k"]
        print(f"{a.name} k={k}: P@{k} {s[f'P@{k}']:.3f}  R@{k} {s[f'R@{k}']:.3f}  Hit@{k} {s[f'Hit@{k}']:.2f}  "
              f"AllFacts@{k} {s[f'AllFacts@{k}']:.2f} ({s['all_facts_from_fact_chunks']}/{s['n']} from fact_chunks)  "
              f"total {s['total_ms']:.0f} ms  (n={s['n']})")
    print("saved to", a.out)


if __name__ == "__main__":
    main()
