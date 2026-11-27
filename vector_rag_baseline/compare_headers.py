"""Old short header vs new full header: same 1,855 chunk ids, same bodies, same questions.
Reads retrieval-only per_question files; recomputes every metric the same way for both.
Prints the tables (pasted into results/v2_old_vs_new_header/comparison.md); writes no file."""
import json, collections, re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
Q = {}
for l in open(R/"data/questions_v2.jsonl"):
    q = json.loads(l); Q[q["qid"]] = q
def fil(c): m = re.match(r"([A-Z]+)_FY(\d{4})", c); return m.group(1), m.group(2)
def load_old():
    rows = [json.loads(l) for l in open(R/"results/v2_old_vs_new_header/old_header_per_question.jsonl")]
    return {(r["qid"], r["config"], r["k"]): r for r in rows}
def load(*paths):
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(R/p/"per_question.jsonl")]
    return {(r["qid"], r["config"], r["k"]): r for r in rows}
old = load_old()
new = load("results/v2_fixed_chunks", "results/v2_distilbert")
def stats(rows):
    out = collections.defaultdict(list)
    for (qid, cfg, k), r in rows.items():
        q = Q[qid]; gold_f = {fil(c) for c in q["gold_chunk_ids"]}; gold_t = {t for t, _ in gold_f}
        ret = r["retrieved"]; n = len(ret)
        wrong_co = sum(fil(c)[0] not in gold_t for c in ret)
        wrong_yr = sum(fil(c)[0] in gold_t and fil(c) not in gold_f for c in ret)
        right_f = n - wrong_co - wrong_yr
        out[(cfg, k)].append(dict(qid=qid, type=q["type"], all=r["all_facts"], rec=r["recall"], hit=r["hit"], prec=r["precision"],
                                  wc=wrong_co/n, wy=wrong_yr/n, rf=right_f/n))
    return out
so, sn = stats(old), stats(new)
m = lambda xs, k: sum(x[k] for x in xs)/len(xs)
lines = ["| Configuration | k | Header | P@k | R@k | Hit@k | AllFacts | Wrong-year chunks | Wrong-company chunks | Right-filing chunks |", "|---|---|---|---|---|---|---|---|---|---|"]
for cfg in ["bge-small","bge-small+rerank","distilbert","distilbert+rerank"]:
    for k in (5,10):
        for name, s in (("old", so), ("new", sn)):
            xs = s[(cfg,k)]
            lines.append(f"| {cfg} | {k} | {name} | {m(xs,'prec'):.3f} | {m(xs,'rec'):.3f} | {m(xs,'hit'):.2f} | {m(xs,'all'):.2f} | {m(xs,'wy'):.1%} | {m(xs,'wc'):.1%} | {m(xs,'rf'):.1%} |")
lines += ["", "**Questions whose AllFacts changed (old -> new), k = 10**", "", "| Configuration | gained (0 -> 1) | lost (1 -> 0) | net |", "|---|---|---|---|"]
flips = {}
for cfg in ["bge-small","bge-small+rerank","distilbert","distilbert+rerank"]:
    g = [x["qid"] for x in sn[(cfg,10)] if x["all"] and not next(y for y in so[(cfg,10)] if y["qid"]==x["qid"])["all"]]
    l = [x["qid"] for x in sn[(cfg,10)] if not x["all"] and next(y for y in so[(cfg,10)] if y["qid"]==x["qid"])["all"]]
    flips[cfg] = (g, l)
    lines.append(f"| {cfg} | {len(g)} ({', '.join(g)}) | {len(l)} ({', '.join(l)}) | {len(g)-len(l):+d} |")
lines += ["", "**AllFacts by question type, bge-small + rerank, k = 10 (old / new)**", "", "| Type | n | old | new |", "|---|---|---|---|"]
for t in ["single","relation","relation_text","relation_deep","cross_year","cross_company"]:
    o = [x for x in so[("bge-small+rerank",10)] if x["type"]==t]; n_ = [x for x in sn[("bge-small+rerank",10)] if x["type"]==t]
    lines.append(f"| {t} | {len(o)} | {m(o,'all'):.0%} | {m(n_,'all'):.0%} |")
print("\n".join(lines))
