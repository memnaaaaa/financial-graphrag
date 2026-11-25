"""Read any retriever's per-question output into one format:
    {qid, system, k, chunks: [chunk ids, ranked], entities: [...], values: [...], start_nodes: [...] or None}

Accepted inputs (fields are found by name, lists may be JSON lists or Python-list strings):
  - Mahua's vector RAG export (vector_rag_baseline/results/v2_all_baselines/per_question_all.jsonl):
    rows per (config, k) with `retrieved`; pick one with --config and --k.
  - G-reasoner / Personalized PageRank per_question.jsonl (G-reasoner/evaluate.py format): `retrieved`
    (document ids), `top_entities`, `top_attributes` (Value node names), `start_nodes`.
"""
import ast
import json

CHUNK_KEYS = ["retrieved", "retrieved_chunks", "documents", "docs"]
ENTITY_KEYS = ["top_entities", "entities", "retrieved_entities"]
VALUE_KEYS = ["top_attributes", "attributes", "values", "retrieved_values"]


def _list(v):
    if v is None or isinstance(v, list):
        return v or []
    v = str(v).strip()
    if not v:
        return []
    try:
        return list(json.loads(v))
    except json.JSONDecodeError:
        return list(ast.literal_eval(v))


def _first(row, keys):
    for k in keys:
        if k in row:
            return _list(row[k])
    return []


def load(path, system, config=None, k=10, max_nodes=10):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if config and str(r.get("config")) != config:
            continue
        if "k" in r and str(r["k"]) != str(k):
            continue
        qid = r["qid"] if str(r["qid"]).startswith("v2_") else f"v2_{r['qid']}"
        out[qid] = {"qid": qid, "system": system, "k": k,
                    "chunks": _first(r, CHUNK_KEYS)[:k],
                    "entities": _first(r, ENTITY_KEYS)[:max_nodes],
                    "values": _first(r, VALUE_KEYS)[:max_nodes],
                    "start_nodes": _list(r["start_nodes"]) if "start_nodes" in r else None}
    if not out:
        raise SystemExit(f"no rows in {path} for config={config!r}, k={k}")
    return out
