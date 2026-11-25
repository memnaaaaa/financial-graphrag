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
  relation     entity -acquired / licensed_from / invests_in / partners_with / subsidiary_of-> entity, from the
               LLM-extracted edges of fin10k_v1, asked from both ends; gold chunks = the edges' evidence  (2 hops)
  relation_chain  the relation hop, then one structured hop from the answer: where it is incorporated
               (Exhibit 21) or its revenue  (3 hops)
  A few relation facts are held out of training (relation_dev.json) to tell learning from memorising.

Each pair has gfmrag's SFT fields (id, question, start_nodes, target_nodes) plus answer, template,
hops, path (the gold edges), tickers and split. Start nodes come from entity_index.EntityIndex, the
same matcher used at query time, so training and inference see the same inputs.

Leakage guards:
  - split by company: any question touching a --test-tickers company goes to test, so test companies
    are never seen in training;
  - golden overlap (golden set v2 by default): a question that asks for a number that appears in a
    golden-set answer for the same company, or a subsidiary question about a subsidiary that a golden
    question or answer names, or a relation question naming an entity that a golden question or answer
    names, is moved out of train/test into golden_overlap.json.

Standard library only:
    python make_synthetic_questions.py --repo .. --out synthetic/fin10k_v1
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
        self.edge_attrs = {}                       # (source, relation, target) -> attributes (LLM edges: evidence)
        for r in csv.DictReader(open(os.path.join(stage1, "edges.csv"), encoding="utf-8")):
            self.out[r["source"]].append((r["relation"], r["target"]))
            self.inn[r["target"]].append((r["relation"], r["source"]))
            if r["attributes"]:
                self.edge_attrs[(r["source"], r["relation"], r["target"])] = ast.literal_eval(r["attributes"])

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


# Known errors per graph version, excluded from the pairs. fin10k_v0: J&J's "research and development
# expense" Values are really "Charges for acquired in-process research and development" from the cash-flow
# statement ($109M FY2025, $1,841M FY2024; JNJ_FY2025_ITEM8_0008). Fixed in fin10k_v1 (total R&D $14,665M
# FY2025; acquired IPR&D is its own metric), so nothing is excluded there.
KNOWN_BAD_VALUES = {"fin10k_v0": [("JNJ", "Research and development expense")]}


def owner_phrase(g, subj):
    """'Apple's' for a company; 'Johnson & Johnson's DARZALEX' (no second possessive) otherwise."""
    return possessive(short_company(subj)) if g.kind(subj) == "Company" else subject_text(g, subj)


def collect_values(g, bad=()):
    """One record per Value node that is linked to at least one chunk (known-bad (ticker, metric) skipped)."""
    vals = []
    for n, (t, a) in g.nodes.items():
        if a.get("kind") != "Value" or (a.get("ticker"), a.get("metric")) in bad:
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


# Relation questions use only LLM-extracted edges (fin10k_v1) whose meaning is clear from the evidence. Left out:
# competes_with (mostly co-defendants in patent suits, not competitors), supplies_to / manufactures (2-3 edges,
# Kenvue only) and has_product (already used by the hierarchy template).
# Each relation phrased from both ends. FORWARD names the head and asks for the tail; INVERSE names the tail
# and asks for the head. {s}/{t} = the named entity, {c} = "Johnson & Johnson's" (or "its").
REL_FORWARD = {
    "acquired": "which companies or businesses did {s} acquire",
    "invests_in": "which companies has {s} invested in",
    "licensed_from": "from which company or companies does {s} license rights",
    "partners_with": "which companies does {s} collaborate with",
    "subsidiary_of": "{s} is a subsidiary of which company",
}
REL_INVERSE = {
    "acquired": "which company acquired {t}",
    "invests_in": "which company has invested in {t}",
    "licensed_from": "which company or product holds a license from {t}",
    "partners_with": "which company or product collaborates with {t}",
    "subsidiary_of": "which companies are subsidiaries of {t}",
}
REL_QUESTION = REL_FORWARD


def llm_edges(g, rels):
    """[(source, relation, target, evidence chunk ids)] for LLM-extracted edges of these relations, skipping
    edges inside one corporate family ("Bayer AG" -partners_with-> "Bayer Intellectual Property GmbH")."""
    out = []
    for (s, r, t), attrs in sorted(g.edge_attrs.items()):
        if r not in rels or attrs.get("source") != "llm" or not attrs.get("chunk_ids"):
            continue
        if base(s).split()[0].lower() == base(t).split()[0].lower():
            continue
        # LLM errors seen in the review: the filing company as someone's subsidiary ("Johnson & Johnson
        # -subsidiary_of-> JPI") or as the target of an investment or acquisition ("Red River Talc -invests_in->
        # Johnson & Johnson")
        if (r == "subsidiary_of" and g.kind(s) == "Company") or (r in ("invests_in", "acquired") and g.kind(t) == "Company"):
            continue
        out.append((s, r, t, sorted(attrs["chunk_ids"])))
    return out


def name_text(g, n):
    return short_company(n) if g.kind(n) == "Company" else base(n)


def _ask(g, phrase, named, ticker):
    """'According to Johnson & Johnson's 10-K filings, which company acquired Auris Health, Inc.'"""
    comp = company_of(g, ticker)
    c = "its" if named == comp else possessive(short_company(comp))
    return f"According to {c} 10-K filings, " + phrase.format(s=name_text(g, named), t=name_text(g, named))


def gen_relation(g, vals):
    """Relation questions from the LLM edges, in three forms:
      relation        one hop, both directions (A): names one end, asks for everything at the other end;
      relation_chain  relation hop + one structured hop from the answer entity (B): where it is incorporated
                      (Exhibit 21) or what its revenue was. Only when the answer is unique.
    Every record keeps `rel_edges` (the LLM edges it uses) so whole facts can be held out."""
    edges = llm_edges(g, REL_FORWARD)
    revenue = collections.defaultdict(list)
    for v in vals:
        if v["metric"] == "Revenue" and not v["loc"] and g.kind(v["subject"]) == "Product":
            revenue[v["subject"]].append(v)
    for direction, phrases in (("forward", REL_FORWARD), ("inverse", REL_INVERSE)):
        groups = collections.defaultdict(list)          # (named end, relation) -> [(answer end, edge, docs)]
        for s, r, t, docs in edges:
            named, ans = (s, t) if direction == "forward" else (t, s)
            groups[(named, r)].append((ans, (s, r, t), docs))
        for (named, r), ends in sorted(groups.items()):
            tickers = sorted({d.split("_")[0] for _, _, docs in ends for d in docs})
            if len(tickers) != 1:
                continue
            ans = sorted({a for a, _, _ in ends})
            docs = sorted({d for _, _, ds in ends for d in ds})
            rel_edges = [list(e) for _, e, _ in ends]
            q = _ask(g, phrases[r], named, tickers[0])
            yield dict(template="relation", hops=2, question=q + "?", answer="; ".join(name_text(g, a) for a in ans),
                       key_entities=[named], docs=docs, attributes=[], entities=ans, rel_edges=rel_edges,
                       path=rel_edges + [[named, "is_mentioned_in", d] for d in docs], tickers=tickers)
            if len(ans) != 1:                            # a chain needs one answer entity to continue from
                continue
            x, (_, e, edocs) = ans[0], ends[0]
            locs = g.targets(x, "incorporated_in")
            if len(locs) == 1 and g.kind(x) != "Company":
                xdocs = [d for d in g.docs(x) if "_EX21_" in d] or g.docs(x)
                yield dict(template="relation_chain", hops=3,
                           question=q + ", and in which jurisdiction is it incorporated or organized?",
                           answer=f"{name_text(g, x)}; {locs[0]}", key_entities=[named],
                           docs=sorted(set(edocs) | set(xdocs)), attributes=[], entities=[x, locs[0]],
                           rel_edges=[list(e)], tickers=tickers,
                           path=[list(e), [x, "incorporated_in", locs[0]]] + [[x, "is_mentioned_in", d] for d in xdocs])
            for v in revenue.get(x, []):
                yield dict(template="relation_chain", hops=3,
                           question=q + f", and what was its revenue in {fy_text(v['fy'])}?",
                           answer=f"{name_text(g, x)}; {v['display']} in {fy_text(v['fy'])}", key_entities=[named],
                           docs=sorted(set(edocs) | set(v["docs"])), attributes=[v["node"]], entities=[x],
                           rel_edges=[list(e)], tickers=tickers, path=[list(e)] + value_path(g, v))


def golden_facts(path):
    """({ticker: {number strings}}, {ticker: question + answer text}) from the golden set, to keep golden
    facts out of training: numbers in the answers, and names (e.g. a subsidiary) in questions or answers."""
    nums_out, text_out = collections.defaultdict(set), collections.defaultdict(str)
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        q = json.loads(line)
        tickers = {g.split("_")[0] for g in q["gold_chunk_ids"]}
        nums = {n for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["gold_answer"]) if len(re.sub(r"\D", "", n)) >= 3}
        for t in tickers:
            nums_out[t] |= nums
            text_out[t] += " " + q["question"] + " " + q["gold_answer"]
    return nums_out, text_out


def names_in(text, name):
    """Does the golden text name this node? Compared without the legal suffix ("Janssen Biotech, Inc.")."""
    from entity_index import LEGAL_SUFFIX
    short = LEGAL_SUFFIX.sub("", base(name)).strip()
    return len(short) >= 4 and re.search(r"(?<!\w)" + re.escape(short) + r"(?!\w)", text) is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--graph", default="fin10k_v1")
    ap.add_argument("--golden", default=None,
                    help="golden set kept out of the pairs (default: vector_rag_baseline/data/questions_v2.jsonl)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--test-tickers", nargs="+", default=["MSFT"],
                    help="companies held out for test (with 8 companies, hold out 2)")
    ap.add_argument("--max-per-template", type=int, default=600, help="cap so one template does not dominate")
    ap.add_argument("--review", type=int, default=40, help="pairs written to review.md for hand inspection")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--relation-dev", type=int, default=10,
                    help="relation facts (LLM edges) held out of training as a check for memorisation")
    a = ap.parse_args()

    stage1 = os.path.join(a.repo, "data", "graph", a.graph, "processed", "stage1")
    g, idx = Graph(stage1), EntityIndex(os.path.join(stage1, "nodes.csv"))
    vals = collect_values(g, KNOWN_BAD_VALUES.get(a.graph, ()))
    rng = random.Random(a.seed)
    golden_path = a.golden or os.path.join(a.repo, "vector_rag_baseline", "data", "questions_v2.jsonl")
    golden, golden_text = golden_facts(golden_path)

    pairs, dropped = [], collections.Counter()
    gens = [gen_lookup(g, vals), gen_change(g, vals), gen_hierarchy(g, vals), gen_share(g, vals),
            gen_compare(g, vals), gen_subsidiary(g), gen_relation(g, vals)]
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
        # also numbers computed for the answer (shares, changes): "13.1%" of DARZALEX in FY2024 is a golden answer
        # even though neither of the two values it is computed from is
        nums |= {x for x in re.findall(r"\d[\d,]*(?:\.\d+)?", p["answer"])
                 if len(re.sub(r"\D", "", x)) >= 3 and not re.fullmatch(r"(19|20)\d\d", x)}
        overlap = any(n and n in golden.get(t, set()) for t in p["tickers"] for n in nums)
        if p["template"] == "subsidiary":
            overlap = overlap or any(names_in(golden_text.get(t, ""), p["key_entities"][0]) for t in p["tickers"])
        if p["template"].startswith("relation"):             # any named or answer entity in the golden set
            # filers are in every golden question and places ("Delaware") in many: check the specific entities only
            ents = [e for e in p["key_entities"] + p["entities"] if g.kind(e) not in ("Company", "Location")]
            overlap = overlap or any(names_in(golden_text.get(t, ""), e) for t in p["tickers"] for e in ents)
        split = "golden_overlap" if overlap else ("test" if set(p["tickers"]) & set(a.test_tickers) else "train")
        rec = {"id": f"{a.graph}-{p['template']}-{i:05d}", "question": p["question"],
               "start_nodes": {"entity": p["start_nodes"]},
               "target_nodes": {"document": p["docs"], "attribute": p["attributes"], "entity": p["entities"]},
               "answer": p["answer"], "template": p["template"], "hops": p["hops"], "path": p["path"],
               "tickers": p["tickers"], "split": split}
        if p.get("rel_edges"):
            rec["rel_edges"] = p["rel_edges"]
        buckets[split].append(rec)

    # Held-out relation facts: a few LLM edges that only training would see are moved, with every question that
    # uses them, to relation_dev. After fine-tuning, better scores there (facts never trained on) mean the model
    # learned to follow relation edges; better scores only on trained facts mean it memorised them.
    trained = sorted({tuple(e) for r in buckets["train"] for e in r.get("rel_edges", [])})
    held = set(random.Random(a.seed).sample(trained, min(a.relation_dev, len(trained))))
    uses = lambda r: {tuple(e) for e in r.get("rel_edges", [])}  # noqa: E731
    # dev keeps only questions made purely of held-out facts; a question mixing held-out and trained facts
    # ("which companies does X collaborate with" -> one held-out, one trained answer) is dropped from both
    buckets["relation_dev"] = [r for r in buckets["train"] if uses(r) and uses(r) <= held]
    mixed = [r for r in buckets["train"] if uses(r) & held and not uses(r) <= held]
    buckets["train"] = [r for r in buckets["train"] if not uses(r) & held]
    for r in buckets["relation_dev"]:
        r["split"] = "relation_dev"

    os.makedirs(a.out, exist_ok=True)
    for name, recs in buckets.items():
        json.dump(recs, open(os.path.join(a.out, f"{name}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # the same held-out questions in golden-set format, for: evaluate.py --questions relation_dev_questions.jsonl
    with open(os.path.join(a.out, "relation_dev_questions.jsonl"), "w", encoding="utf-8") as f:
        for r in buckets["relation_dev"]:
            f.write(json.dumps({"qid": r["id"], "type": r["template"], "hops": r["hops"], "companies": r["tickers"],
                                "question": r["question"], "gold_chunk_ids": r["target_nodes"]["document"],
                                "gold_answer": r["answer"]}, ensure_ascii=False) + "\n")

    stats = {"graph": a.graph, "golden": os.path.relpath(golden_path, a.repo), "test_tickers": a.test_tickers,
             "relation_dev_edges": sorted(list(e) for e in held), "relation_dev_mixed_dropped": len(mixed),
             "excluded_values": KNOWN_BAD_VALUES.get(a.graph, []), "values_with_chunks": len(vals),
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
