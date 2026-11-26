"""Build the poster demo ("Follow the Number") from the results already in the repo.

    python demo/build_data.py        # writes demo/demo_data.json and demo/index.html (open it in a browser)

No Gemini calls and no network: everything comes from
  answer_step/results/<run>_k10/per_question.jsonl   answers, verdicts, citations, retrieved chunks
  answer_step/results/<run>_k10/summary.json         scoreboard
  data/graph/fin10k_v1/processed/stage1/              the graph around each question
  data/chunks/chunks.jsonl                            passages, filings, links
  vector_rag_baseline/data/questions_v2.jsonl         questions, gold answers, gold facts and their chunks
  G-reasoner/results/hop_case/*_v2_q10.json           per-layer ranks for the hop animation (E7)
index.html is template.html with the data and vendor/vis-network.min.js (graph library, MIT/Apache-2.0)
inlined, so the page works offline.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(REPO, "answer_step"), os.path.join(REPO, "vector_rag_baseline")]
from rag import metrics  # noqa: E402
from graph_context import VALUE_ID_RE, Graph, load_chunks  # noqa: E402

SYSTEMS = [  # (run folder in answer_step/results, label, emoji)
    ("vector_rag", "Vector RAG", "🔍"),
    ("g_reasoner_finetuned", "Graph (G-reasoner)", "🕸️"),
    ("hybrid_finetuned_rule", "Hybrid", "🤝"),
]
SCOREBOARD = SYSTEMS[:2] + [("ppr", "PageRank", "🚶")] + SYSTEMS[2:]
SHOWCASE = [  # qid, tag, emoji, one-line story (from answer_step/README.md patterns)
    ("v2_q01", "Single fact", "🎯",
     "One number in one table: every system gets it. The hybrid cites the Value node, so the number traces straight to its XBRL tag."),
    ("v2_q39", "Graph wins", "🏆",
     "Two companies in one question. Vector search lands in J&J's text only and gives up; the graph starts from both company nodes and finds both net incomes."),
    ("v2_q12", "Wrong answer", "⚠️",
     "The graph's passages hold a real but different number ($5.0B effect on net income, not the $6.5B of gains). Supported by its source, still wrong: only the judge catches it."),
    ("v2_q16", "Missing", "🤷",
     "The question says \"J&J's largest product\" instead of naming DARZALEX, so the graph starts from J&J alone and wanders into its 450 subsidiaries. Gemini refuses; vector search finds the patent passage."),
    ("v2_q33", "Everyone fails", "🧱",
     "Employee headcount is in the text but not in the graph (it is not one of the 26 XBRL concepts), and vector search misses both years' passages. Nobody can answer."),
]
GRAPH_RUN = "g_reasoner_finetuned"      # start nodes and entities for the drawn subgraph
VALUE_RUN = "hybrid_finetuned_rule"     # Values shown on the drawn subgraph


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def short(name, n=60):
    return name if len(name) <= n else name[:n - 1] + "…"


def line_with(text, nums):
    body = text.split("\n", 1)[-1]
    for ln in body.split("\n"):
        vals = [v for v, _ in metrics.extract_numbers(ln)]
        if any(metrics._supported(x, d, vals) for x, d in nums):
            return ln.strip()[:240]
    return None


def chunk_info(c, gold_ids):
    return {"id": c["chunk_id"], "company": c["company"], "ticker": c["ticker"], "fy": c["fiscal_year"],
            "section": c["section"], "section_title": c["section_title"], "accession": c["accession"],
            "url": c["source_url"], "gold": c["chunk_id"] in gold_ids,
            "snippet": c["text"].split("\n", 1)[-1][:420]}


def traces(answer, question, g, chunks):
    """One entry per sentence with numbers: its citations, each followed to a passage line and a filing."""
    out = []
    for s in re.split(r"(?<=[.;!?])\s+|\n+", answer):
        nums = metrics.extract_numbers(re.sub(r"\[[^\]]*\]", " ", s), drop=question)
        if not nums:
            continue
        steps = []
        for cid in dict.fromkeys(VALUE_ID_RE.findall(s) + metrics.cited_ids(s)):
            if VALUE_ID_RE.fullmatch(cid) and cid in g.value_of:
                a = g.nodes[g.value_of[cid]][1]
                c = chunks[a["source_chunk_id"]]
                printed = metrics.extract_numbers(a["printed_value"])
                steps.append({"kind": "value", "id": cid, "name": g.value_of[cid], "metric": a["metric"],
                              "fy": a["fiscal_year"], "display": a["display"], "xbrl": a["xbrl_concept"],
                              "fact_id": a["xbrl_fact_id"], "matches": any(metrics._supported(x, d, [v for v, _ in printed]) for x, d in nums),
                              "chunk": c["chunk_id"], "line": line_with(c["text"], printed) or a["printed_value"],
                              "filing": f"{c['company']} 10-K {c['fiscal_year']}", "section": c["section"],
                              "accession": c["accession"], "url": a["source_fact_url"]})
            elif cid in chunks:
                c = chunks[cid]
                steps.append({"kind": "chunk", "id": cid, "line": line_with(c["text"], nums),
                              "filing": f"{c['company']} 10-K {c['fiscal_year']}", "section": c["section"],
                              "accession": c["accession"], "url": c["source_url"]})
            else:
                steps.append({"kind": "unknown", "id": cid})
        out.append({"sentence": s.strip(), "steps": steps})
    return out


def chunk_label(cid):
    t, fy, sec, n = cid.split("_")
    return f"{t} {fy[:2]}{fy[-2:]} {sec.replace('ITEM', 'Item ').replace('EX21', 'Ex.21')} #{int(n)}"


def subgraph(g, seeds, chunk_ids, mentions, cap=30):
    """Entities and Values around the question (graph_context.Graph.subgraph), plus the given passages,
    linked by is_mentioned_in where the graph has that link."""
    seeds = [s for s in dict.fromkeys(seeds) if s in g.nodes]
    edges = g.subgraph(seeds, cap=cap)
    names = list(dict.fromkeys(seeds + [n for e in edges for n in (e[0], e[2])]))
    nodes = [{"id": n, "label": short(n), "kind": g.kind(n), "start": False} for n in names]
    out = [{"s": s, "r": r, "t": t} for s, r, t in edges]
    for c in chunk_ids:
        nodes.append({"id": c, "label": chunk_label(c), "kind": "chunk", "start": False})
        out += [{"s": n, "r": "is_mentioned_in", "t": c} for n in names if (n, c) in mentions]
    return nodes, out


def main():
    g = Graph(os.path.join(REPO, "data/graph/fin10k_v1/processed/stage1"))
    chunks = load_chunks(os.path.join(REPO, "data/chunks/chunks.jsonl"))
    qs = {q["qid"]: q for q in load_jsonl(os.path.join(REPO, "vector_rag_baseline/data/questions_v2.jsonl"))}
    res = {run: {r["qid"]: r for r in load_jsonl(os.path.join(REPO, "answer_step/results", f"{run}_k10", "per_question.jsonl"))}
           for run, _, _ in SCOREBOARD}
    mentions = {(s, t) for s, r, t in g.edges if r == "is_mentioned_in"}
    gret = {r["qid"]: r for r in load_jsonl(os.path.join(REPO, "G-reasoner/results/finetuned_fin10k_v1/per_question.jsonl"))
            if r["k"] == 10}

    data = {"scoreboard": [], "systems": [{"id": r, "label": l, "emoji": e} for r, l, e in SYSTEMS],
            "questions": [], "chunks": {}}
    for run, label, emoji in SCOREBOARD:
        s = json.load(open(os.path.join(REPO, "answer_step/results", f"{run}_k10", "summary.json")))["overall"]
        data["scoreboard"].append({"id": run, "label": label, "emoji": emoji, "correct": s["correct_rate"],
                                   "hallucination": s["hallucination_rate"], "missing": s["missing_rate"]})

    for qid, tag, emoji, story in SHOWCASE:
        q = qs[qid]
        gold_ids = {c for ids in q["fact_chunks"].values() for c in ids}
        start = gret[qid]["start_nodes"]
        values = [g.value_of[v] for v in res[VALUE_RUN][qid]["values_given"] if v in g.value_of]
        shown = list(dict.fromkeys(sorted(gold_ids) + [c for run, _, _ in SYSTEMS for c in res[run][qid]["retrieved"]]))
        nodes, edges = subgraph(g, start + gret[qid]["top_entities"] + values, shown, mentions)
        for n in nodes:
            n["start"] = n["id"] in start
            if n["kind"] == "Value":
                n["value_id"] = g.value_id[n["id"]]
            if n["kind"] == "chunk":
                n["gold"] = n["id"] in gold_ids
                n["retrieved_by"] = [run for run, _, _ in SYSTEMS if n["id"] in res[run][qid]["retrieved"]]
        runs = {}
        for run, _, _ in SYSTEMS:
            r = res[run][qid]
            for c in r["retrieved"]:
                data["chunks"].setdefault(c, chunk_info(chunks[c], gold_ids))
            runs[run] = {"verdict": r["verdict"], "judge_reason": r["judge_reason"], "answer": r["answer"],
                         "stage": r["error_stage"], "missing_facts": r.get("missing_facts", []),
                         "retrieved": r["retrieved"], "gold_hits": [c for c in r["retrieved"] if c in gold_ids],
                         "values_given": r["values_given"], "traces": traces(r["answer"], q["question"], g, chunks)}
        for c in gold_ids:   # gold passages, so the page can show what was needed
            data["chunks"].setdefault(c, chunk_info(chunks[c], gold_ids))
            data["chunks"][c]["gold"] = True
        data["questions"].append({"qid": qid, "tag": tag, "emoji": emoji, "story": story, "type": q["type"],
                                  "hops": q.get("hops"), "question": q["question"], "gold_answer": q["gold_answer"],
                                  "facts": q["fact_chunks"], "start_nodes": start,
                                  "graph": {"nodes": nodes, "edges": edges}, "runs": runs})

    hop = {}
    for name in ("zero_shot", "finetuned"):
        p = os.path.join(REPO, "G-reasoner/results/hop_case", f"{name}_v2_q10.json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            hop[name] = {"tracked": [{"node": n, "type": d["tracked"][n]["type"], "of": d["tracked"][n]["of"],
                                      "ranks": [l["rank"] for l in d["tracked"][n]["layers"]]} for n in d["tracked_order"]],
                         "start_nodes": d["start_nodes"]}
    if hop:
        q10 = qs["v2_q10"]
        hop["question"], hop["gold_answer"] = q10["question"], q10["gold_answer"]
        names = [t["node"] for t in next(iter(hop.values()))["tracked"]]
        hop["edges"] = [{"s": s, "r": r, "t": t} for s, r, t in g.edges if s in names and t in names]
        hop["kinds"] = {n: ("chunk" if n in chunks else g.kind(n)) for n in names}
        hop["labels"] = {n: (chunk_label(n) if n in chunks else short(n, 48)) for n in names}
        data["hop_case"] = hop

    with open(os.path.join(HERE, "demo_data.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    page = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    vis = open(os.path.join(HERE, "vendor", "vis-network.min.js"), encoding="utf-8").read()
    page = page.replace("/*__VIS_NETWORK__*/", vis.replace("</script", "<\\/script"))
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page.replace("__DEMO_DATA__", blob))
    n_cites = sum(len(t["steps"]) for q in data["questions"] for r in q["runs"].values() for t in r["traces"])
    print(f"{len(data['questions'])} questions, {len(data['chunks'])} passages, {n_cites} traced citations, "
          f"hop case: {'yes' if hop else 'no'} -> demo/index.html")


if __name__ == "__main__":
    main()
