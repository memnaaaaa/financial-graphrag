"""One results table broken down by question type, from a run_eval.py output folder.

  python scripts/results_by_type.py results/v2_fixed_chunks results/v2_distilbert --out results/v2_all_baselines

Rows: config x k x question type (+ an ALL row). Retrieval columns need no LLM; answer columns appear if the run had
generation + judging. AllFacts = share of questions where EVERY gold fact is stated by a retrieved chunk.
"X% of N" = rate over N numbers (unsupported), N numeric claims (citation accuracy) or N answer sentences (answer support: content words found in the cited chunks); small N means read it with care.
Writes <run>/results_by_type.md and prints it.
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("run", nargs="+", help="one or more run folders; their rows are combined (use --out to name the result)")
ap.add_argument("--questions", default="data/questions_v2.jsonl")
ap.add_argument("--chunks", default="data/chunks.jsonl", help="needed to back-fill answer support for older runs")
ap.add_argument("--out", default=None, help="folder to write results_by_type.md to (default: the first run folder)")
a = ap.parse_args()

Q = {q["qid"]: q for q in map(json.loads, open(a.questions, encoding="utf-8")) if q}
rows = [json.loads(l) for run in a.run for l in open(Path(run) / "per_question.jsonl", encoding="utf-8") if l.strip()]
if any("answer" in r and "n_sentences" not in r for r in rows):  # back-fill the sentence-support check from stored answers
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from rag import metrics
    ctext = {c["chunk_id"]: c["text"] for c in map(json.loads, open(a.chunks, encoding="utf-8"))}
    for r in rows:
        if "answer" in r and "n_sentences" not in r:
            r.update(metrics.answer_support(r["answer"], ctext))
ORDER = ["single", "relation", "relation_text", "relation_deep", "cross_year", "cross_company"]
has_llm = any("verdict" in r for r in rows)


def mean(rs, key):
    return sum(r[key] for r in rs) / len(rs)


def line(cfg, k, typ, rs):
    c = [cfg, k, typ, len(rs), f"{mean(rs, 'precision'):.3f}", f"{mean(rs, 'recall'):.3f}", f"{mean(rs, 'hit'):.2f}",
         f"{mean(rs, 'all_facts'):.2f}"]
    if has_llm:
        v = [r.get("verdict") for r in rs]
        n = len(rs)
        nn = sum(r.get("n_numbers", 0) for r in rs)
        nu = sum(r.get("n_unsupported", 0) for r in rs)
        ncl = sum(r.get("n_claims", 0) for r in rs)
        nok = sum(r.get("n_correct", 0) for r in rs)
        nsen = sum(r.get("n_sentences", 0) for r in rs)
        nsup = sum(r.get("n_supported_sentences", 0) for r in rs)
        c += [f"{v.count('correct') / n:.0%}", f"{v.count('hallucination') / n:.0%}", f"{v.count('missing') / n:.0%}",
              f"{nu / nn:.0%} of {nn}" if nn else "n/a", f"{nok / ncl:.0%} of {ncl}" if ncl else "n/a",
              f"{nsup / nsen:.0%} of {nsen}" if nsen else "n/a"]
    return "| " + " | ".join(str(x) for x in c) + " |"


head = ["Config", "k", "Question type", "n", "P@k", "R@k", "Hit@k", "AllFacts@k"]
if has_llm:
    head += ["Correct", "Halluc.", "Missing", "Unsupported numbers", "Citation acc.", "Answer support"]
out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
for cfg in dict.fromkeys(r["config"] for r in rows):
    for k in sorted({r["k"] for r in rows if r["config"] == cfg}):
        sub = [r for r in rows if r["config"] == cfg and r["k"] == k]
        for typ in ORDER:
            rs = [r for r in sub if Q[r["qid"]]["type"] == typ]
            if rs:
                out.append(line(cfg, k, typ, rs))
        out.append(line(cfg, k, "**ALL**", sub))
text = "\n".join(out)
(Path(a.out or a.run[0]) / "results_by_type.md").write_text(text + "\n", encoding="utf-8")
print(text)
