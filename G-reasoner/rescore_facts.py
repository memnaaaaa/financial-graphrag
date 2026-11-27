"""Recompute AllFacts for a finished run from its saved retrievals, after `fact_chunks` was added to the
question file. Nothing is retrieved again (no GPU, no Colab): every row already holds its ranked `retrieved`
list, and AllFacts@k only asks whether each gold fact has a chunk in the top k.

Updates, in place, each row's facts_total / facts_found / missing_facts / all_facts / all_facts_source and
the summary's AllFacts@k / all_facts_from_fact_chunks. It also checks that P, R and Hit recomputed from
`retrieved` match the saved values, so a changed gold label stops the script instead of being mixed in.

    python rescore_facts.py results/zero_shot_fin10k_v1 results/finetuned_fin10k_v1

Rerun vector_rag_baseline/scripts/results_by_type.py on the folder afterwards for the table by type.
Standard library only (same definition as vector_rag_baseline/rag/metrics.py facts_found).
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def facts_found(retrieved, fact_chunks, k):
    top = set(retrieved[:k])
    found = [f for f, ids in fact_chunks.items() if top & set(ids)]
    return {"facts_total": len(fact_chunks), "facts_found": len(found),
            "missing_facts": [f for f in fact_chunks if f not in found],
            "all_facts": int(len(found) == len(fact_chunks)), "all_facts_source": "fact_chunks"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run folders holding per_question.jsonl and summary.json")
    ap.add_argument("--questions", default=os.path.join(REPO, "vector_rag_baseline", "data", "questions_v2.jsonl"))
    a = ap.parse_args()
    Q = {q["qid"]: q for q in map(json.loads, open(a.questions, encoding="utf-8")) if q}

    for run in a.runs:
        pq, sp = os.path.join(run, "per_question.jsonl"), os.path.join(run, "summary.json")
        rows = [json.loads(line) for line in open(pq, encoding="utf-8") if line.strip()]
        for r in rows:
            q, k = Q[r["qid"]], r["k"]
            gold, top = set(q["gold_chunk_ids"]), r["retrieved"][:k]
            got = len(gold & set(top))
            check = {"hit": int(got > 0), "precision": got / k, "recall": got / len(gold)}
            for key, v in check.items():
                if abs(v - r[key]) > 1e-9:
                    raise SystemExit(f"{run} {r['qid']} k={k}: {key} {r[key]} != {v} from retrieved; gold labels "
                                     f"changed since this run, so rerun it instead of rescoring")
            if q.get("fact_chunks"):
                r.update(facts_found(r["retrieved"], q["fact_chunks"], k))
        with open(pq, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

        summary = json.load(open(sp, encoding="utf-8"))
        for s in summary:
            rs = [r for r in rows if r["config"] == s["config"] and r["k"] == s["k"]]
            if len(rs) != s["n"]:
                raise SystemExit(f"{sp}: {s['config']} k={s['k']} has n={s['n']} but {len(rs)} rows")
            k = s["k"]
            s[f"AllFacts@{k}"] = sum(r["all_facts"] for r in rs) / len(rs)
            s["all_facts_from_fact_chunks"] = sum(r["all_facts_source"] == "fact_chunks" for r in rs)
            print(f"{run}: {s['config']} k={k} AllFacts@{k} {s[f'AllFacts@{k}']:.2f} "
                  f"({s['all_facts_from_fact_chunks']}/{s['n']} from fact_chunks)")
        json.dump(summary, open(sp, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
