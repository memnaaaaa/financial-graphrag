"""Generate synthetic question / gold-subgraph pairs from a team graph, for fine-tuning G-reasoner.

Recipe (project plan, workstream C): sample a 2-3 hop path in the graph, write a question whose
answer needs that path, and keep the path as the gold subgraph. Questions are written from
templates here (no LLM, so no API cost); an LLM can later reword them to sound less formulaic.

Templates (all answers are computed from graph values, never typed by hand):
  lookup       subject -has_value-> Value -is_mentioned_in-> chunk           (2 hops)
  change       the same subject and metric in two consecutive fiscal years    (2 facts, 2 hops each)
  hierarchy    segment/business line -has_product-> product -has_value-> Value (3 hops)
  share        product or segment revenue / company revenue, same year       (2 facts, up to 3 hops)
  compare      the same metric for two companies in the same fiscal year     (cross-company)
  subsidiary   company -has_subsidiary-> subsidiary -incorporated_in-> place  (2 hops)

Each pair has gfmrag's SFT fields (id, question, start_nodes, target_nodes) plus answer, template,
hops, path (the gold edges), tickers and split. Start nodes come from entity_index.EntityIndex, the
same matcher used at query time, so training and inference see the same inputs.

Leakage guards:
  - split by company: any question touching a --test-tickers company goes to test, so test companies
    are never seen in training;
  - golden overlap: a question that asks for a number that appears in a golden-set answer for the
    same company is moved out of train/test into golden_overlap.json.

Standard library only:
    python make_synthetic_questions.py --repo .. --out synthetic/fin10k_v0
"""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from entity_index import EntityIndex  # noqa: E402

csv.field_size_limit(sys.maxsize)
SHORT = {"Apple Inc.": "Apple", "Microsoft Corporation": "Microsoft", "JPMorgan Chase & Co.": "JPMorgan Chase",
         "Exxon Mobil Corporation": "ExxonMobil", "The Procter & Gamble Company": "Procter & Gamble",
         "Walmart Inc.": "Walmart", "Caterpillar Inc.": "Caterpillar"}
TAG = re.compile(r" \(([A-Z]{1,5})\)$")


def short_company(name):
    return SHORT.get(name, name)


def base(name):
    return TAG.sub("", name)


def fy_text(fy):
    return f"fiscal {fy[2:]}"


def fmt_amount(v, unit):
    if unit == "USD/shares":
        return f"${v:,.2f} per share"
    m = v / 1e6
    return f"{'-' if m < 0 else ''}${abs(m):,.0f} million" if abs(m - round(m)) < 1e-9 else f"${m:,.1f} million"


def number_key(display):
    """'$14,351 million' -> '14,351'; '$18.81 per share' -> '18.81'."""
    m = re.search(r"\d[\d,]*(\.\d+)?", display)
    return m.group(0) if m else ""


class Graph:
    def __init__(self, stage1):
        self.nodes = {}
        for r in csv.DictReader(open(os.path.join(stage1, "nodes.csv"), encoding="utf-8")):
            self.nodes[r["name"]] = (r["type"], ast.literal_eval(r["attributes"]) if r["attributes"] else {})
        self.out = collections.defaultdict(list)   # source -> [(relation, target)]
        self.inn = collections.defaultdict(list)   # target -> [(relation, source)]
        for r in csv.DictReader(open(os.path.join(stage1, "edges.csv"), encoding="utf-8")):
            self.out[r["source"]].append((r["relation"], r["target"]))
            self.inn[r["target"]].append((r["relation"], r["source"]))

    def kind(self, n):
        t, a = self.nodes[n]
        return a.get("kind", t)

    def targets(self, n, rel):
        return [t for r, t in self.out[n] if r == rel]

    def sources(self, n, rel):
        return [s for r, s in self.inn[n] if r == rel]

    def docs(self, n):
        return sorted(self.targets(n, "is_mentioned_in"))


def company_of(g, ticker):
    return next(n for n, (t, a) in g.nodes.items() if a.get("kind") == "Company" and a.get("ticker") == ticker)


def possessive(s):
    return s + "'" if s.endswith("s") else s + "'s"


def subject_text(g, subj):
    k, a = g.kind(subj), g.nodes[subj][1]
    if k == "Company":
        return short_company(subj)
    comp = short_company(company_of(g, a["ticker"]))
    if base(subj).startswith(comp):                      # "Microsoft 365 ..." already names the company
        return base(subj)
    return {"Segment": f"{possessive(comp)} {base(subj)} segment",
            "BusinessLine": f"{possessive(comp)} {base(subj)} business"}.get(k, f"{possessive(comp)} {base(subj)}")


# Known errors in the team graph, excluded until the graph is fixed. fin10k_v0: J&J's
# "research and development expense" Values are really "Charges for acquired in-process research
# and development" from the cash-flow statement ($109M FY2025, $1,841M FY2024; JNJ_FY2025_ITEM8_0008).
KNOWN_BAD_VALUES = [("JNJ", "Research and development expense")]


def owner_phrase(g, subj):
    """'Apple's' for a company; 'Johnson & Johnson's DARZALEX' (no second possessive) otherwise."""
    return possessive(short_company(subj)) if g.kind(subj) == "Company" else subject_text(g, subj)


def collect_values(g):
    """One record per Value node that is linked to at least one chunk (known-bad facts skipped)."""
    vals = []
    for n, (t, a) in g.nodes.items():
        if a.get("kind") != "Value" or (a.get("ticker"), a.get("metric")) in KNOWN_BAD_VALUES:
            continue
        docs = g.docs(n)
        subj = g.sources(n, "has_value")
        if not docs or len(subj) != 1:
            continue
        loc = g.targets(n, "in_location")
        vals.append({"node": n, "subject": subj[0], "metric": a["metric"], "fy": a["fiscal_year"],
                     "ticker": a["ticker"], "value": a["value"], "unit": a["unit"], "display": a["display"],
                     "instant": "period_start" not in a, "loc": loc[0] if loc else None, "docs": docs})
    return vals


def loc_text(loc):
    if not loc:
        return ""
    if loc.startswith("Outside"):
        return f" {loc[0].lower()}{loc[1:]}"
    return f" in the {base(loc)}" if base(loc) == "United States" else f" in {base(loc)}"


def when_text(v):
    return f"at the end of {fy_text(v['fy'])}" if v["instant"] else f"in {fy_text(v['fy'])}"


def value_path(g, v):
    p = [[v["subject"], "has_value", v["node"]], [v["node"], "of_metric", v["metric"]]]
    p += [[v["node"], "for_period", t] for t in g.targets(v["node"], "for_period")]
    if v["loc"]:
        p.append([v["node"], "in_location", v["loc"]])
    return p + [[v["node"], "is_mentioned_in", d] for d in v["docs"]]


def gen_lookup(g, vals):
    for v in vals:
        q = f"What was {owner_phrase(g, v['subject'])} {v['metric'][0].lower() + v['metric'][1:]}{loc_text(v['loc'])} {when_text(v)}?"
        yield dict(template="lookup", hops=2, question=q, answer=v["display"], key_entities=[v["subject"]],
                   docs=v["docs"], attributes=[v["node"]], entities=[], path=value_path(g, v), tickers=[v["ticker"]])


def gen_change(g, vals):
    idx = {(v["subject"], v["metric"], v["loc"], v["fy"]): v for v in vals}
    for v in vals:
        prev = idx.get((v["subject"], v["metric"], v["loc"], f"FY{int(v['fy'][2:]) - 1}"))
        if not prev or prev["value"] == 0:
            continue
        diff, pct = v["value"] - prev["value"], (v["value"] / prev["value"] - 1) * 100
        word = "increased" if diff > 0 else "decreased"
        q = (f"How did {owner_phrase(g, v['subject'])} {v['metric'][0].lower() + v['metric'][1:]}{loc_text(v['loc'])} "
             f"change from {fy_text(prev['fy'])} to {fy_text(v['fy'])}?")
        a = (f"It {word} by {fmt_amount(abs(diff), v['unit'])} ({pct:+.1f}%), "
             f"from {prev['display']} to {v['display']}.")
        yield dict(template="change", hops=2, question=q, answer=a, key_entities=[v["subject"]],
                   docs=sorted(set(v["docs"]) | set(prev["docs"])), attributes=[prev["node"], v["node"]], entities=[],
                   path=value_path(g, prev) + value_path(g, v), tickers=[v["ticker"]])


def gen_hierarchy(g, vals):
    for v in vals:
        if g.kind(v["subject"]) != "Product" or v["metric"] != "Revenue" or v["loc"]:
            continue
        parents = [p for p in g.sources(v["subject"], "has_product") if g.kind(p) in ("Segment", "BusinessLine")]
        if len(parents) != 1:
            continue
        par, comp = parents[0], short_company(company_of(g, v["ticker"]))
        both = sorted(set(g.docs(par)) & set(g.docs(v["subject"])))
        q = (f"Which {comp} segment or business line includes {base(v['subject'])}, and what was "
             f"{possessive(base(v['subject']))} revenue in {fy_text(v['fy'])}?")
        a = f"{base(par)} ({g.kind(par)}); {base(v['subject'])} revenue was {v['display']} in {fy_text(v['fy'])}."
        yield dict(template="hierarchy", hops=3, question=q, answer=a, key_entities=[v["subject"]],
                   docs=sorted(set(v["docs"]) | set(both)), attributes=[v["node"]], entities=[par],
                   path=[[par, "has_product", v["subject"]]] + value_path(g, v), tickers=[v["ticker"]])


def gen_share(g, vals):
    totals = {(v["ticker"], v["fy"]): v for v in vals
              if g.kind(v["subject"]) == "Company" and v["metric"] == "Revenue" and not v["loc"]}
    for v in vals:
        tot = totals.get((v["ticker"], v["fy"]))
        if (not tot or v["metric"] != "Revenue" or v["loc"] or g.kind(v["subject"]) not in ("Product", "Segment")
                or tot["value"] <= 0 or not 0 < v["value"] < tot["value"]):
            continue
        comp = short_company(v["subject"] if g.kind(v["subject"]) == "Company" else company_of(g, v["ticker"]))
        what = f"its {base(v['subject'])} segment" if g.kind(v["subject"]) == "Segment" else base(v["subject"])
        q = f"What share of {possessive(comp)} {fy_text(v['fy'])} revenue came from {what}?"
        a = f"About {v['value'] / tot['value'] * 100:.1f}% ({v['display']} of {tot['display']})."
        yield dict(template="share", hops=3, question=q, answer=a, key_entities=[v["subject"], tot["subject"]],
                   docs=sorted(set(v["docs"]) | set(tot["docs"])), attributes=[v["node"], tot["node"]], entities=[],
                   path=value_path(g, v) + value_path(g, tot), tickers=[v["ticker"]])


def gen_compare(g, vals):
    by = collections.defaultdict(list)
    for v in vals:
        if g.kind(v["subject"]) == "Company" and not v["loc"]:
            by[(v["metric"], v["fy"], v["instant"])].append(v)
    for (metric, fy, _), vs in by.items():
        vs = sorted(vs, key=lambda v: v["ticker"])
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                a_, b_ = vs[i], vs[j]
                if a_["unit"] != b_["unit"]:
                    continue
                hi, lo = (a_, b_) if a_["value"] >= b_["value"] else (b_, a_)
                m = metric[0].lower() + metric[1:]
                q = (f"Which had higher {m} {when_text(a_)}, {short_company(a_['subject'])} or "
                     f"{short_company(b_['subject'])}, and by how much?")
                ans = (f"{short_company(hi['subject'])}, by {fmt_amount(hi['value'] - lo['value'], hi['unit'])} "
                       f"({hi['display']} vs {lo['display']}).")
                yield dict(template="compare", hops=2, question=q, answer=ans,
                           key_entities=[a_["subject"], b_["subject"]], docs=sorted(set(a_["docs"]) | set(b_["docs"])),
                           attributes=[a_["node"], b_["node"]], entities=[], path=value_path(g, a_) + value_path(g, b_),
                           tickers=sorted({a_["ticker"], b_["ticker"]}))


def gen_subsidiary(g):
    for comp, (t, a) in g.nodes.items():
        if a.get("kind") != "Company":
            continue
        for sub in g.targets(comp, "has_subsidiary"):
            locs, docs = g.targets(sub, "incorporated_in"), g.docs(sub)
            docs = [d for d in docs if "_EX21_" in d] or docs     # Exhibit 21 is where the jurisdiction is stated
            if len(locs) != 1 or not docs:
                continue
            q = f"In which jurisdiction is {sub}, a subsidiary of {short_company(comp)}, incorporated or organized?"
            yield dict(template="subsidiary", hops=2, question=q, answer=locs[0], key_entities=[sub],
                       docs=docs, attributes=[], entities=[locs[0]],
                       path=[[comp, "has_subsidiary", sub], [sub, "incorporated_in", locs[0]]] +
                            [[sub, "is_mentioned_in", d] for d in docs], tickers=[a["ticker"]])


def golden_numbers(repo):
    """{ticker: {number strings}} from golden-set answers, to keep golden facts out of training."""
    path = os.path.join(repo, "vector_rag_baseline", "data", "questions.jsonl")
    out = collections.defaultdict(set)
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        q = json.loads(line)
        tickers = {g.split("_")[0] for g in q["gold_chunk_ids"]}
        nums = {n for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["gold_answer"]) if len(re.sub(r"\D", "", n)) >= 3}
        for t in tickers:
            out[t] |= nums
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--graph", default="fin10k_v0")
    ap.add_argument("--out", required=True)
    ap.add_argument("--test-tickers", nargs="+", default=["MSFT"],
                    help="companies held out for test (with 8 companies, hold out 2)")
    ap.add_argument("--max-per-template", type=int, default=600, help="cap so one template does not dominate")
    ap.add_argument("--review", type=int, default=40, help="pairs written to review.md for hand inspection")
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()

    stage1 = os.path.join(a.repo, "data", "graph", a.graph, "processed", "stage1")
    g, idx = Graph(stage1), EntityIndex(os.path.join(stage1, "nodes.csv"))
    vals = collect_values(g)
    rng = random.Random(a.seed)
    golden = golden_numbers(a.repo)

    pairs, dropped = [], collections.Counter()
    gens = [gen_lookup(g, vals), gen_change(g, vals), gen_hierarchy(g, vals), gen_share(g, vals),
            gen_compare(g, vals), gen_subsidiary(g)]
    for gen in gens:
        items = list(gen)
        rng.shuffle(items)
        kept = 0
        for p in items:
            start = idx.find(p["question"])
            if not all(k in start for k in p["key_entities"]):
                dropped[f"{p['template']}: key entity not found by the query-time matcher"] += 1
                continue
            if not p["docs"]:
                dropped[f"{p['template']}: no evidence chunk"] += 1
                continue
            if kept >= a.max_per_template:
                dropped[f"{p['template']}: over cap"] += 1
                continue
            kept += 1
            p["start_nodes"] = start
            pairs.append(p)

    seen, uniq = set(), []
    for p in pairs:
        if p["question"] not in seen:
            seen.add(p["question"])
            uniq.append(p)
    buckets = {"train": [], "test": [], "golden_overlap": []}
    for i, p in enumerate(uniq):
        nums = {number_key(g.nodes[n][1]["display"]) for n in p["attributes"]}
        overlap = any(n and n in golden.get(t, set()) for t in p["tickers"] for n in nums)
        split = "golden_overlap" if overlap else ("test" if set(p["tickers"]) & set(a.test_tickers) else "train")
        rec = {"id": f"{a.graph}-{p['template']}-{i:05d}", "question": p["question"],
               "start_nodes": {"entity": p["start_nodes"]},
               "target_nodes": {"document": p["docs"], "attribute": p["attributes"], "entity": p["entities"]},
               "answer": p["answer"], "template": p["template"], "hops": p["hops"], "path": p["path"],
               "tickers": p["tickers"], "split": split}
        buckets[split].append(rec)

    os.makedirs(a.out, exist_ok=True)
    for name, recs in buckets.items():
        json.dump(recs, open(os.path.join(a.out, f"{name}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    stats = {"graph": a.graph, "test_tickers": a.test_tickers, "values_with_chunks": len(vals),
             "pairs": len(uniq), "by_split": {k: len(v) for k, v in buckets.items()},
             "by_template": dict(collections.Counter(p["template"] for p in uniq)),
             "by_template_and_split": {k: dict(collections.Counter(r["template"] for r in v)) for k, v in buckets.items()},
             "dropped": dict(dropped)}
    json.dump(stats, open(os.path.join(a.out, "stats.json"), "w"), indent=2)

    # Hand-inspection sheet: an even mix of templates, with the evidence line for each number
    chunks = {}
    for line in open(os.path.join(a.repo, "data", "chunks", "chunks.jsonl"), encoding="utf-8"):
        c = json.loads(line)
        chunks[c["chunk_id"]] = c["text"]
    allrecs = [r for v in buckets.values() for r in v]
    by_t = collections.defaultdict(list)
    for r in allrecs:
        by_t[r["template"]].append(r)
    sample = []
    while len(sample) < min(a.review, len(allrecs)):
        for t in sorted(by_t):
            if by_t[t] and len(sample) < a.review:
                sample.append(by_t[t].pop(rng.randrange(len(by_t[t]))))
    lines = [f"# Synthetic pairs for hand review ({a.graph})", "",
             "For each pair check: is the question natural and unambiguous, is the answer right, and does the "
             "evidence line support it? Mark OK / WRONG / UNCLEAR in the last column and note why.", "",
             "| # | Template | Question | Answer | Start nodes | Evidence (first gold chunk, line with the number) | Split | Check |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(sample, 1):
        ev = ""
        nums = [number_key(g.nodes[n][1]["display"]) for n in r["target_nodes"]["attribute"]]
        pats = [re.compile(r"(?<![\d,.])" + re.escape(n) + r"(?![\d]|,\d|\.\d)") for n in nums if n]
        if r["template"] == "subsidiary":
            pats = [re.compile(re.escape(r["path"][0][2]))]
        for d in r["target_nodes"]["document"]:
            hit = next((ln for ln in chunks.get(d, "").split("\n") if any(p.search(ln) for p in pats)), "")
            if hit:
                ev = f"`{d}`: {hit[:140]}"
                break
        ev = ev or f"`{r['target_nodes']['document'][0]}` (number not found on one line)"
        cell = lambda s: str(s).replace("|", "\\|")  # noqa: E731
        lines.append(f"| {i} | {r['template']} | {cell(r['question'])} | {cell(r['answer'])} | "
                     f"{cell(', '.join(r['start_nodes']['entity']))} | {cell(ev)} | {r['split']} | |")
    open(os.path.join(a.out, "review.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=2))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
