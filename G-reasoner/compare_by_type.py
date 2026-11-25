"""One retrieval table for the poster's Results panel: E1 to E4 on golden set v2, broken down by question type.

Systems (columns): vector RAG bge-small without and with reranking (E1, Mahua's v2_all_baselines run),
G-reasoner zero-shot (E2), fine-tuned (E3) and Personalized PageRank (E4), all on the same 39 questions.
Rows: question types in the baseline's order, plus ALL. One table per measure and k (Hit, P, R at 5 and 10).

AllFacts is left out on purpose: the baseline run had fact_chunks, the graph runs did not (their AllFacts is
Hit), so the two would not be comparable. Add it once questions_v2.jsonl carries fact_chunks and the graph
runs are redone.

Every system must cover exactly the same qids at each k, or the script stops.

    python compare_by_type.py --out results/e1_e4_by_type.md
Standard library only.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASELINE = os.path.join(REPO, "vector_rag_baseline", "results", "v2_all_baselines", "per_question_all.jsonl")

# (column label, experiment, file, config inside the file)
SYSTEMS = [
    ("Vector", "E1", BASELINE, "bge-small"),
    ("Vector+rerank", "E1", BASELINE, "bge-small+rerank"),
    ("G-r zero-shot", "E2", os.path.join(HERE, "results", "zero_shot_fin10k_v1", "per_question.jsonl"), "g-reasoner"),
    ("G-r fine-tuned", "E3", os.path.join(HERE, "results", "finetuned_fin10k_v1", "per_question.jsonl"),
     "g-reasoner-ft"),
    ("PageRank", "E4", os.path.join(HERE, "results", "ppr_fin10k_v1", "per_question.jsonl"), "ppr"),
]
ORDER = ["single", "relation", "relation_text", "relation_deep", "cross_year", "cross_company"]
TYPE_LABEL = {"single": "Single fact", "relation": "Relation", "relation_text": "Relation, descriptive",
              "relation_deep": "Deep chain (3-5 hops)", "cross_year": "Cross-year", "cross_company": "Cross-company"}
MEASURES = [("hit", "Hit"), ("precision", "Precision"), ("recall", "Recall")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--questions", default=os.path.join(REPO, "vector_rag_baseline", "data", "questions_v2.jsonl"))
    ap.add_argument("--ks", nargs="+", type=int, default=[5, 10])
    ap.add_argument("--out", default=os.path.join(HERE, "results", "e1_e4_by_type.md"))
    a = ap.parse_args()

    qtype = {q["qid"]: q["type"] for q in map(json.loads, open(a.questions, encoding="utf-8")) if q}
    data = {}  # (label, k) -> {qid: row}
    for label, _, path, cfg in SYSTEMS:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r["config"] == cfg and r["k"] in a.ks:
                    data.setdefault((label, r["k"]), {})[r["qid"]] = r
    for k in a.ks:
        ref = set(data[(SYSTEMS[0][0], k)])
        for label, *_ in SYSTEMS:
            got = set(data.get((label, k), {}))
            if got != ref:
                raise SystemExit(f"{label} k={k} covers different questions: missing {sorted(ref - got)}, "
                                 f"extra {sorted(got - ref)}")
        if ref - set(qtype):
            raise SystemExit(f"qids not in {a.questions}: {sorted(ref - set(qtype))}")
    n_q = len(data[(SYSTEMS[0][0], a.ks[0])])

    def mean(label, k, qids, key):
        return sum(data[(label, k)][q][key] for q in qids) / len(qids)

    lines = ["# Retrieval on golden set v2, E1 to E4, by question type", "",
             f"{n_q} questions, same for every system. Systems: "
             + "; ".join(f"{label} = {exp} (`{cfg}`)" for label, exp, _, cfg in SYSTEMS) + ".",
             "Vector RAG retrieves from the chunk index; the graph systems rank document nodes of `fin10k_v1` "
             "from the same rule-based start nodes. Best value in each row in bold.",
             "AllFacts is not shown: only the vector run had `fact_chunks` (see compare_by_type.py).", ""]
    for key, name in MEASURES:
        for k in a.ks:
            lines += [f"**{name}@{k}**", "",
                      "| Question type | n | " + " | ".join(label for label, *_ in SYSTEMS) + " |",
                      "|---|---|" + "---|" * len(SYSTEMS)]
            groups = [(TYPE_LABEL[t], [q for q in data[(SYSTEMS[0][0], k)] if qtype[q] == t]) for t in ORDER]
            groups.append(("**ALL**", list(data[(SYSTEMS[0][0], k)])))
            for tname, qids in groups:
                if not qids:
                    continue
                vals = [mean(label, k, qids, key) for label, *_ in SYSTEMS]
                best = max(vals)
                cells = [(f"**{v:.2f}**" if v == best else f"{v:.2f}") for v in vals]
                lines.append(f"| {tname} | {len(qids)} | " + " | ".join(cells) + " |")
            lines.append("")
    text = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(text)
    print(text)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
