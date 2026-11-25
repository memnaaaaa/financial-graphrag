"""Draw the hand-check sample of LLM-extracted edges in fin10k_v1 (same method as edge_check.csv).

    python data/graph/make_llm_edge_check.py            # writes edge_check_llm.csv and edge_check_llm.md

The sample is stratified by relation (fixed quotas, fixed seed), because a purely random draw would be
about 3/4 has_product. edge_check_llm.csv has the same columns as edge_check.csv; fill in `correct`
(Y/N), `error_type` and `notes` by hand. edge_check_llm.md shows, for each edge, the evidence quote, how
each name was matched to a node, and the chunk passage, so the check can be done from that one file.

Error types for N: wrong_direction, wrong_relation, not_stated, wrong_merge, generic.
"""
import argparse
import ast
import csv
import json
import os
import random
import re

QUOTAS = {"has_product": 12, "competes_with": 4, "acquired": 3, "partners_with": 3, "subsidiary_of": 2,
          "licensed_from": 2, "invests_in": 2, "supplies_to": 1, "manufactures": 1}
COLUMNS = ["id", "check_group", "source", "relation", "target", "where_to_check", "evidence_text",
           "correct", "error_type", "notes"]


def squash(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--graph", default="fin10k_v1")
    ap.add_argument("--seed", type=int, default=22)
    a = ap.parse_args()
    g = os.path.join(a.repo, "data/graph", a.graph)
    csv.field_size_limit(2**31 - 1)
    edges = [r for r in csv.DictReader(open(f"{g}/processed/stage1/edges.csv", encoding="utf-8"))
             if "'llm'" in r["attributes"]]
    for r in edges:
        r["attrs"] = ast.literal_eval(r["attributes"])
    report = list(csv.DictReader(open(f"{g}/merge_report.csv", encoding="utf-8")))
    chunks = {c["chunk_id"]: c for c in map(json.loads, open(os.path.join(a.repo, "data/chunks/chunks.jsonl"),
                                                               encoding="utf-8"))}
    rng = random.Random(a.seed)
    sample = []
    for rel, n in QUOTAS.items():
        pool = sorted((e for e in edges if e["relation"] == rel), key=lambda e: (e["source"], e["target"]))
        sample += rng.sample(pool, min(n, len(pool)))

    rows, md = [], ["# Hand check of 30 LLM edges (fin10k_v1)", "",
                    "For each edge: is the relation stated in the quote, in this direction, between these two "
                    "entities, and was each name matched to the right node? Mark Y or N in `edge_check_llm.csv` "
                    "(error types: wrong_direction, wrong_relation, not_stated, wrong_merge, generic).", ""]
    for i, e in enumerate(sample, 1):
        cid = e["attrs"]["chunk_ids"][0]
        ev = e["attrs"].get("evidence", "")
        rows.append({"id": i, "check_group": e["relation"], "source": e["source"], "relation": e["relation"],
                     "target": e["target"], "where_to_check": f"chunk {cid} (chunks.jsonl)", "evidence_text": ev,
                     "correct": "", "error_type": "", "notes": ""})
        # how the raw names became these nodes (merge_report rows of this chunk and relation)
        how = [r for r in report if r["chunk_id"] in e["attrs"]["chunk_ids"] and r["relation"] == e["relation"]
               and r["status"] == "kept" and r["head_node"].startswith(e["source"] + " [")
               and r["tail_node"].startswith(e["target"] + " [")]
        body = chunks[cid]["text"].split("\n", 1)[-1]
        # show the passage around the quote (whole chunk if the quote cannot be placed)
        words = ev.split()
        pos = body.find(" ".join(words[:4])) if len(words) >= 4 else -1
        excerpt = body if pos < 0 else body[max(0, pos - 400): pos + len(ev) + 400]
        md += [f"## {i}. `{e['source']}` --{e['relation']}--> `{e['target']}`", "",
               f"- **Chunk:** `{cid}`" + (f" (+{len(e['attrs']['chunk_ids']) - 1} more)" if len(e['attrs']['chunk_ids']) > 1 else ""),
               f"- **Quote:** \"{ev}\""]
        for r in how[:1]:
            md.append(f"- **Name matching:** \"{r['head']}\" -> {r['head_node']}; \"{r['tail']}\" -> {r['tail_node']}")
        md += ["", "```", excerpt.strip(), "```", "", "**Correct (Y/N):** ___   **Error type:** ___", ""]
    with open(os.path.join(a.repo, "data/graph/edge_check_llm.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    open(os.path.join(a.repo, "data/graph/edge_check_llm.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"{len(rows)} edges -> data/graph/edge_check_llm.csv and edge_check_llm.md")


if __name__ == "__main__":
    main()
