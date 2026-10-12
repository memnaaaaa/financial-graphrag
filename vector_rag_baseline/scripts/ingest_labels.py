"""Validate labeler replies in data/labeling/replies/qNN.json and (optionally) apply them as gold.
Checks per reply: every candidate in data/labeling/qNN.txt is labeled exactly once; labels are valid; every 'answer'
has a quote that appears verbatim in its chunk (whitespace and '|' separators normalized) AND the quote contains a
digit or a name from the fact (so a bare column header does not count); answer chunks match the filing the question names.
  python scripts/ingest_labels.py            # validate + show diff vs current gold
  python scripts/ingest_labels.py --apply    # write validated answers into data/questions.jsonl (backup kept)"""
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
chunks = {}
for l in open(ROOT / "data/chunks.jsonl", encoding="utf-8"):
    r = json.loads(l); chunks[r["chunk_id"]] = r["text"]
norm = lambda s: re.sub(r"[\s|]+", " ", s).strip().lower()
cy = lambda c: "_".join(c.split("_")[:2])
qs = {json.loads(l)["qid"]: json.loads(l) for l in open(ROOT / "data/questions.jsonl", encoding="utf-8")}
apply = "--apply" in sys.argv
new_gold = {}

for f in sorted((ROOT / "data/labeling/replies").glob("q*.json")):
    qid = f.stem; rep = json.load(open(f)); q = qs[qid]
    pool = re.findall(r'"chunk_id": "([^"]+)"', (ROOT / f"data/labeling/{qid}.txt").read_text(encoding="utf-8"))
    labs = rep["labels"]; ids = [x["chunk_id"] for x in labs]
    problems, answers, rejected = [], [], []
    if set(ids) != set(pool) or len(ids) != len(set(ids)):
        problems.append(f"label ids differ from pool: missing {sorted(set(pool)-set(ids))[:3]}, extra {sorted(set(ids)-set(pool))[:3]}, dups {len(ids)-len(set(ids))}")
    filings = {cy(g) for g in q["gold_chunk_ids"]}   # filings the question names
    for x in labs:
        if x["label"] not in ("answer", "supporting", "irrelevant"): problems.append(f"bad label {x['chunk_id']}"); continue
        if x["label"] != "answer": continue
        why = None
        if x["chunk_id"] not in chunks: why = "unknown chunk id"
        elif not x.get("quote"): why = "no quote"
        elif norm(x["quote"]) not in norm(chunks[x["chunk_id"]]): why = "quote not found verbatim in chunk"
        elif not re.search(r"\d", x["quote"]): why = "quote contains no figure (header only, does not state the fact)"
        elif cy(x["chunk_id"]) not in filings: why = f"wrong filing {cy(x['chunk_id'])}"
        (rejected if why else answers).append((x["chunk_id"], why))
    ans = [a for a, _ in answers]; old = q["gold_chunk_ids"]
    print(f"\n== {qid}: {len(pool)} candidates | {len(ans)} accepted answers | {len(rejected)} rejected | problems: {problems or 'none'}")
    for c, w in rejected: print(f"   REJECTED {c}: {w}")
    print(f"   labeler-only (new vs my gold): {sorted(set(ans)-set(old))}")
    print(f"   my-gold-only (labeler did not mark): {sorted(set(old)-set(ans))}")
    if rep.get("missing_facts"): print("   labeler missing_facts:", rep["missing_facts"])
    if not problems: new_gold[qid] = ans

if apply and new_gold:
    bk = ROOT / "data/questions_pattern_gold.jsonl"
    if not bk.exists(): shutil.copy(ROOT / "data/questions.jsonl", bk)
    out = []
    for qid, q in qs.items():
        if qid in new_gold:
            q = {**q, "gold_chunk_ids": new_gold[qid], "gold_source": "llm-labeler (validated)"}
        out.append(q)
    (ROOT / "data/questions.jsonl").write_text("\n".join(json.dumps(q) for q in out) + "\n", encoding="utf-8")
    print("\napplied to data/questions.jsonl for:", sorted(new_gold), "| backup:", bk.name)
