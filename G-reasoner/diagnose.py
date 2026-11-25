"""Why does G-reasoner miss the gold chunks? Run the covered golden questions under a few variants
with one model load, and compare hit@k / recall@k.

Variants:
  all          start nodes as in evaluate.py (company, fiscal year, metric, product, segment)
  no_hubs      without Company and FiscalYear start nodes. Those two link to every chunk of a filing
               through the chunk header, so they may drown out the specific entities.
  hubs_only    only Company and FiscalYear start nodes (how much do they alone explain?)
  dense_qwen3  no graph: cosine between the query and the document node embeddings G-reasoner uses
               (Qwen3-Embedding-0.6B). Separates "the GNN ranks badly" from "the embeddings are weak".

    python diagnose.py --root <data root> --out <results dir>
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import torch  # noqa: E402

from evaluate import covered_questions  # noqa: E402
from gfm_components import AliasNER  # noqa: E402
from query import load_retriever  # noqa: E402

HUBS = {"Company", "FiscalYear"}


class FilteredNER(AliasNER):
    def __init__(self, index, keep):
        super().__init__(index)
        self.keep = keep

    def __call__(self, text):
        return [n for n in self.index.find(text) if self.keep(self.index.kind[n])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--root", required=True)
    ap.add_argument("--data-name", default="fin10k_v1")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("--ks", nargs="+", type=int, default=[5, 10])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sys.path.insert(0, os.path.join(a.repo, "vector_rag_baseline"))
    from rag import metrics

    retriever, ner = load_retriever(a.root, a.data_name, a.model)
    covered, skipped = covered_questions(a.repo, None, retriever)
    print(f"{len(covered)} covered questions; skipped {skipped}")
    retriever.retrieve(covered[0]["question"], top_k=1)  # loads the CUDA kernel (needs start nodes)

    index = ner.index
    variants = {
        "all": FilteredNER(index, lambda k: True),
        "no_hubs": FilteredNER(index, lambda k: k not in HUBS),
        "hubs_only": FilteredNER(index, lambda k: k in HUBS),
    }
    doc_ids = retriever.graph.nodes_by_type["document"]
    doc_x = retriever.graph.x[doc_ids]
    K = max(a.ks)

    rows = []
    for name, v_ner in list(variants.items()) + [("dense_qwen3", None)]:
        for q in covered:
            if v_ner is None:
                qe = retriever.text_emb_model.encode([q["question"]], is_query=True, show_progress_bar=False)
                scores = (doc_x @ qe.to(doc_x.device, doc_x.dtype).T).squeeze(1)
                top = doc_ids[torch.topk(scores, K).indices]
                ranked = [retriever.qa_data.id2node[i.item()] for i in top]
                start = []
            else:
                retriever.ner_model = v_ner
                start = v_ner(q["question"])
                ranked = [it["id"] for it in retriever.retrieve(q["question"], top_k=K)["document"]]
            for k in a.ks:
                rows.append({"config": name, "k": k, "qid": q["qid"], "start_nodes": start, "retrieved": ranked[:k],
                             "hit": metrics.hit_at_k(ranked, q["gold_chunk_ids"], k),
                             "recall": metrics.recall_at_k(ranked, q["gold_chunk_ids"], k),
                             "precision": metrics.precision_at_k(ranked, q["gold_chunk_ids"], k)})
    retriever.ner_model = ner

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "diagnose_per_question.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")

    names = list(variants) + ["dense_qwen3"]
    print(f"\n{'variant':12}" + "".join(f"  Hit@{k}  R@{k}" for k in a.ks))
    for n in names:
        line = f"{n:12}"
        for k in a.ks:
            rs = [r for r in rows if r["config"] == n and r["k"] == k]
            line += f"  {sum(r['hit'] for r in rs) / len(rs):5.2f}  {sum(r['recall'] for r in rs) / len(rs):4.2f}"
        print(line)
    print(f"\nhit@{K} per question:   " + "  ".join(f"{n[:9]:>9}" for n in names))
    for q in covered:
        cells = [next(r["hit"] for r in rows if r["config"] == n and r["k"] == K and r["qid"] == q["qid"]) for n in names]
        print(f"  {q['qid']} [{q.get('type', ''):6}]   " + "  ".join(f"{c:>9}" for c in cells))
    print("saved to", a.out)


if __name__ == "__main__":
    main()
