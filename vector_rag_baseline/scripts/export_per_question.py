"""Merge all per-question baseline runs into one file for comparison with G-Reasoner.

Reads results/<run>/per_question.jsonl for each run folder given, joins the question,
gold answer, gold facts and gold chunk ids from data/questions_v2.jsonl, and writes:
  <out>/per_question_all.jsonl   one row per (question, config, k)
  <out>/per_question_all.csv     same, flat, easy to filter in Excel
Use the same columns for the G-Reasoner run so the two can be joined on (qid, config, k).
"""
import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("runs", nargs="+", help="run folders, e.g. results/v2_fixed_chunks results/v2_distilbert")
ap.add_argument("--out", default="results/v2_all_baselines")
ap.add_argument("--questions", default="data/questions_v2.jsonl")
a = ap.parse_args()

qs = {}
for line in open(ROOT / a.questions):
    q = json.loads(line)
    qs[q["qid"]] = q

rows = []
for run in a.runs:
    for line in open(ROOT / run / "per_question.jsonl"):
        r = json.loads(line)
        q = qs[r["qid"]]
        gold = set(q["gold_chunk_ids"])
        rows.append({
            "qid": r["qid"], "type": q["type"], "companies": ";".join(q["companies"]),
            "config": r["config"], "k": r["k"],
            "question": q["question"], "gold_answer": q["gold_answer"],
            "gold_facts": q["gold_facts"], "gold_chunk_ids": q["gold_chunk_ids"],
            "retrieved": r["retrieved"],
            "gold_in_retrieved": [c for c in r["retrieved"] if c in gold],
            "answer": r["answer"], "cited_ids": r.get("cited_ids", []),
            "verdict": r["verdict"], "judge_reason": r.get("judge_reason", ""),
            "all_facts": r["all_facts"], "facts_found": r.get("facts_found"),
            "missing_facts": r.get("missing_facts"), "error_stage": r["error_stage"],
            "precision": r["precision"], "recall": r["recall"], "hit": r["hit"],
            "unsupported": r.get("unsupported", []),
        })
rows.sort(key=lambda x: (x["qid"], x["config"], x["k"]))

out = ROOT / a.out
out.mkdir(parents=True, exist_ok=True)
with open(out / "per_question_all.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(out / "per_question_all.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
print(len(rows), "rows ->", out)
