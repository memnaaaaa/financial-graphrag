"""Load G-reasoner on a prepared, indexed graph and retrieve nodes for questions.

The model and the embedding model load once; every question then takes well under a second.
Run index_graph.py first.

    python query.py --root .../data -q "What were Apple's total net sales in fiscal 2025?"
    python query.py --root .../data --questions questions.jsonl --out results.jsonl
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from entity_index import EntityIndex  # noqa: E402
from gfm_components import AliasNER, PassThroughEL  # noqa: E402
from gfmrag import GFMRetriever  # noqa: E402
from vllm_limits import limit_vllm_memory  # noqa: E402


def load_questions(a):
    qs = [{"qid": f"q{i}", "question": q} for i, q in enumerate(a.q, 1)]
    if a.questions:
        for line in open(a.questions, encoding="utf-8"):
            if line.strip():
                r = json.loads(line) if line.lstrip().startswith("{") else {"question": line.strip()}
                r.setdefault("qid", f"f{len(qs) + 1}")
                qs.append(r)
    return qs


def load_retriever(root, data_name, model, ner=None):
    """(retriever, ner) for a prepared and indexed dataset. Shared with evaluate.py.
    ner defaults to the rule-based matcher (AliasNER)."""
    stage1 = os.path.join(root, data_name, "processed", "stage1")
    stage2 = os.path.join(root, data_name, "processed", "stage2")
    if not os.path.isdir(stage2):
        sys.exit(f"no stage2 cache under {stage2}; run index_graph.py first")
    ner = ner or AliasNER(EntityIndex(os.path.join(stage1, "nodes.csv")))
    limit_vllm_memory()
    t0 = time.time()
    retriever = GFMRetriever.from_index(data_dir=root, data_name=data_name, model_path=model,
                                        ner_model=ner, el_model=PassThroughEL())
    print(f"=== G-reasoner loaded in {time.time() - t0:.0f}s on {retriever.device} ===")
    print("node types:", {k: len(v) for k, v in retriever.graph.nodes_by_type.items()})
    return retriever, ner


def short(item):
    attrs = item["attributes"] or {}
    text = attrs.get("content", "")
    text = text.split("\n", 1)[-1] if text else ""
    return f"{item['score']:8.3f}  {item['id'][:80]}" + (f"\n              {text[:140]!r}" if text else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--data-name", default="fin10k_v1")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("-q", action="append", default=[], help="a question (repeatable)")
    ap.add_argument("--questions", help="file: JSONL with 'question' (and 'qid'), or one question per line")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--types", nargs="+", default=["document", "entity", "attribute"])
    ap.add_argument("--out", help="write one JSON line per question here")
    a = ap.parse_args()
    questions = load_questions(a)
    if not questions:
        sys.exit("give -q or --questions")

    retriever, ner = load_retriever(a.root, a.data_name, a.model)

    out = open(a.out, "w", encoding="utf-8") if a.out else None
    for q in questions:
        t1 = time.time()
        start = ner(q["question"])
        res = retriever.retrieve(q["question"], top_k=a.top_k,
                                 target_types=[t for t in a.types if t in retriever.graph.nodes_by_type])
        ms = (time.time() - t1) * 1000
        print(f"\n### [{q['qid']}] {q['question']}\nstart nodes: {start or 'none'}   ({ms:.0f} ms)")
        for t, items in res.items():
            print(f"  top {t}:")
            for it in items:
                print("    " + short(it))
        if out:
            out.write(json.dumps({**q, "start_nodes": start, "retrieve_ms": ms,
                                  "retrieved": {t: [{"id": it["id"], "score": it["score"]} for it in items]
                                                for t, items in res.items()}}) + "\n")
    if out:
        out.close()
        print("\nwrote", a.out)


if __name__ == "__main__":
    main()
