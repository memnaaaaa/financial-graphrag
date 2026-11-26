"""Answer step (E5): retrieved chunks (+ for graph retrievers, Value nodes and the connected subgraph) go to
Gemini; the answer must cite passage ids and Value ids; it is then scored with the vector baseline's judge and
grounding checks, plus a check that each cited Value really holds the number stated next to it.

    python answer_step/answer.py --system vector_rag --retrievals vector_rag_baseline/results/v2_all_baselines/per_question_all.jsonl --config bge-small+rerank
    python answer_step/answer.py --system g_reasoner_zero_shot --retrievals <Rida's per_question.jsonl>
    python answer_step/answer.py ... --dry-run          # no Gemini calls: checks the pipeline only
    python answer_step/compare.py                       # table over all runs in answer_step/results/

Prompt, judge and metrics are imported from vector_rag_baseline/rag (unchanged), so the scores are comparable
with the baseline. With no graph nodes in the input, the prompt is exactly the baseline's prompt.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "vector_rag_baseline"))

from rag import error_stage, generate, judge, metrics  # noqa: E402  (Mahua's code, imported unchanged)

import retrievals  # noqa: E402
from graph_context import VALUE_ID_RE, Graph, load_chunks, select_values, triple_text  # noqa: E402
from llm import DEFAULT_MODEL, FakeGemini, Gemini  # noqa: E402

GRAPH_SYSTEM = generate.SYSTEM + (
    " The context may also list Facts (relations between companies, products and segments, taken from the "
    "filings) and Values (reported numbers, each with an id such as [V-JNJ-0001]). When a number comes from a "
    "Value, cite the Value id in square brackets, e.g. [V-JNJ-0001]; when it comes from a passage, cite the "
    "passage id. Use the Facts to connect companies, subsidiaries and products.")


def build_prompt(g, chunks, q, ret, use_graph, value_mode="retriever"):
    passages = [(c, chunks[c]["text"]) for c in ret["chunks"] if c in chunks]
    values = [v for v in ret["values"] if v in g.value_id] if use_graph else []
    if use_graph and value_mode == "rule":
        # item 2: Values picked by rule from the linked nodes; the retriever's own Values only as a fallback
        values = select_values(g, (ret["start_nodes"] or []) + ret["entities"]) or values
    seeds = (ret["start_nodes"] or []) + ret["entities"] + values if use_graph else []
    triples = g.subgraph(seeds) if seeds else []
    if not (values or triples):
        return generate.SYSTEM, generate.build_prompt(q["question"], passages), values, triples
    parts = []
    if triples:
        parts.append("Facts:\n" + "\n".join("- " + triple_text(g, e) for e in triples))
    if values:
        parts.append("Values:\n" + "\n".join("- " + g.value_line(v) for v in values))
    ctx = "\n\n".join(f"[{cid}]\n{text}" for cid, text in passages)
    prompt = "\n\n".join(parts) + f"\n\nContext:\n{ctx}\n\nQuestion: {q['question']}\nAnswer:"
    return GRAPH_SYSTEM, prompt, values, triples


def score(g, chunks, q, ret, answer, values):
    """All string checks; no LLM."""
    filing = lambda c: f"{chunks[c]['ticker']} {chunks[c]['fiscal_year']}"
    src = {g.value_id[v]: g.nodes[v][1]["source_chunk_id"] for v in values}
    # A cited Value counts as citing the passage its number is printed in.
    scored = VALUE_ID_RE.sub(lambda m: src.get(m.group(0), m.group(0)), answer)
    evidence = list(dict.fromkeys(ret["chunks"] + list(src.values())))
    ctext = {c: chunks[c]["text"] for c in evidence if c in chunks}
    cfil = {c: filing(c) for c in ctext}
    gfil = set(q.get("filings") or [filing(c) for c in q["gold_chunk_ids"]])
    cited = [c for c in metrics.cited_ids(scored) if c in ctext]
    rec = {"cited_ids": metrics.cited_ids(answer), "cited_value_ids": list(dict.fromkeys(VALUE_ID_RE.findall(answer)))}
    rec.update(metrics.unsupported_numbers(scored, [ctext[c] for c in cited], q["question"]))
    rec.update(metrics.citation_accuracy(scored, ctext, cfil, gfil, q["question"]))
    if hasattr(metrics, "answer_support"):
        rec.update(metrics.answer_support(scored, ctext))
    # Value check: a sentence that cites a Value must state that Value's number (as printed, any scale).
    n_v = n_ok = n_unknown = 0
    for s in re.split(r"(?<=[.;!?])\s+|\n+", answer):
        for vid in dict.fromkeys(VALUE_ID_RE.findall(s)):
            n_v += 1
            if vid not in src:
                n_unknown += 1
                continue
            a = g.nodes[g.value_of[vid]][1]
            printed = [x for x, _ in metrics.extract_numbers(a["printed_value"])]
            nums = metrics.extract_numbers(VALUE_ID_RE.sub(" ", s), drop=q["question"])
            n_ok += any(metrics._supported(x, d, printed) for x, d in nums)
    rec.update(n_value_cites=n_v, n_value_cites_ok=n_ok, n_value_cites_unknown=n_unknown)
    # Retrieval: chunk metrics on the ranked chunks; facts on everything the generator saw (chunks + Values' sources)
    k = ret["k"]
    rec.update(precision=metrics.precision_at_k(ret["chunks"], q["gold_chunk_ids"], k),
               recall=metrics.recall_at_k(ret["chunks"], q["gold_chunk_ids"], k),
               hit=metrics.hit_at_k(ret["chunks"], q["gold_chunk_ids"], k))
    if q.get("fact_chunks"):
        rec.update(metrics.facts_found(evidence, q["fact_chunks"], len(evidence)))
    else:   # golden set without fact_chunks: fall back to "any gold chunk seen", as run_eval.py does
        h = metrics.hit_at_k(evidence, q["gold_chunk_ids"], len(evidence))
        rec.update(facts_total=1, facts_found=h, missing_facts=[], all_facts=h)
    rec["fact_check"] = "fact_chunks" if q.get("fact_chunks") else "gold_chunk_hit"
    return rec


def summarize(recs):
    n = len(recs)
    s = {"n": n, "hit": sum(r["hit"] for r in recs) / n, "all_facts": sum(r["all_facts"] for r in recs) / n}
    s.update(metrics.judge_rates([r["verdict"] for r in recs]))
    s.update(metrics.aggregate_traceability(recs))
    nv = sum(r["n_value_cites"] for r in recs)
    s["value_cites"] = nv
    s["value_cite_accuracy"] = sum(r["n_value_cites_ok"] for r in recs) / nv if nv else None
    s["stages"] = dict(collections.Counter(r["error_stage"] for r in recs))
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", required=True, help="name of the run, e.g. vector_rag, g_reasoner_zero_shot, ppr")
    ap.add_argument("--retrievals", required=True, help="per-question retrieval file (see retrievals.py)")
    ap.add_argument("--config", help="row filter for files with several configs (e.g. bge-small+rerank)")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--questions", default=os.path.join(REPO, "vector_rag_baseline/data/questions_v2.jsonl"))
    ap.add_argument("--graph", default=os.path.join(REPO, "data/graph/fin10k_v1/processed/stage1"))
    ap.add_argument("--chunks", default=os.path.join(REPO, "data/chunks/chunks.jsonl"))
    ap.add_argument("--no-graph-context", action="store_true", help="ignore retrieved nodes: chunks only")
    ap.add_argument("--values", choices=["retriever", "rule"], default="retriever",
                    help="which Value nodes go to Gemini: the retriever's top Values, or chosen by rule from the "
                         "question's linked company/product, metric and fiscal-year nodes (item 2)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--rpm", type=float, default=10, help="max Gemini requests per minute")
    ap.add_argument("--types", nargs="+", help="only these question types (e.g. relation relation_deep)")
    ap.add_argument("--only", nargs="+", help="only these qids")
    ap.add_argument("--dry-run", action="store_true", help="no Gemini calls (fake answers): pipeline check only")
    ap.add_argument("--out", help="default: answer_step/results/<system>_k<k>")
    a = ap.parse_args()

    g, chunks = Graph(a.graph), load_chunks(a.chunks)
    questions = [json.loads(l) for l in open(a.questions, encoding="utf-8") if l.strip()]
    if a.types:
        questions = [q for q in questions if q["type"] in a.types]
    if a.only:
        questions = [q for q in questions if q["qid"] in a.only or q["qid"].replace("v2_", "") in a.only]
    rets = retrievals.load(a.retrievals, a.system, a.config, a.k)
    missing = [q["qid"] for q in questions if q["qid"] not in rets]
    if missing:
        print(f"warning: no retrieval for {len(missing)} questions: {missing}", file=sys.stderr)
    llm = FakeGemini() if a.dry_run else Gemini(REPO, a.model, rpm=a.rpm)
    out = a.out or os.path.join(HERE, "results", f"{a.system}_k{a.k}" + ("_dryrun" if a.dry_run else ""))
    os.makedirs(out, exist_ok=True)

    recs = []
    for q in questions:
        if q["qid"] not in rets:
            continue
        ret = rets[q["qid"]]
        system, prompt, values, triples = build_prompt(g, chunks, q, ret, not a.no_graph_context, a.values)
        answer = llm.generate(prompt, system=system)
        j = judge.judge(llm, q["question"], q["gold_answer"], answer)
        rec = {"system": a.system, "k": a.k, "qid": q["qid"], "type": q["type"], "hops": q.get("hops"),
               "companies": q.get("companies"), "question": q["question"], "gold_answer": q["gold_answer"],
               "retrieved": ret["chunks"], "values_given": [g.value_id[v] for v in values],
               "n_triples_given": len(triples), "start_nodes": ret["start_nodes"], "answer": answer,
               "verdict": j["verdict"], "judge_reason": j["reason"]}
        rec.update(score(g, chunks, q, ret, answer, values))
        linked = True if ret["start_nodes"] is None else bool(ret["start_nodes"])
        rec["error_stage"] = error_stage.tag(rec["verdict"], bool(rec["all_facts"]), entities_linked=linked)
        recs.append(rec)
        print(f"  [{a.system}] {q['qid']:7} {rec['verdict']:13} stage={rec['error_stage']:10} "
              f"cites={len(rec['cited_ids'])}+{len(rec['cited_value_ids'])}V  unsupported={rec['n_unsupported']}", flush=True)

    with open(os.path.join(out, "per_question.jsonl"), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_type = collections.defaultdict(list)
    for r in recs:
        by_type[r["type"]].append(r)
    summary = {"system": a.system, "k": a.k, "model": a.model, "graph": os.path.relpath(a.graph, REPO),
               "retrievals": os.path.relpath(a.retrievals, REPO), "config": a.config, "dry_run": a.dry_run,
               "values": a.values,
               "fact_check": recs[0]["fact_check"] if recs else None,
               "overall": summarize(recs), "by_type": {t: summarize(rs) for t, rs in sorted(by_type.items())}}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=2)
    o = summary["overall"]
    print(f"\n{a.system}: {o['n']} questions | correct {o['correct_rate']:.1%} halluc {o['hallucination_rate']:.1%} "
          f"missing {o['missing_rate']:.1%} | unsupported numbers {o['unsupported_number_rate']:.1%} | "
          f"citation acc {o['citation_accuracy']:.1%} | value cites {o['value_cites']}"
          f" (acc {o['value_cite_accuracy'] if o['value_cite_accuracy'] is None else format(o['value_cite_accuracy'], '.1%')})")
    print(f"Gemini calls {llm.calls}, cached {llm.hits}; wrote {out}")


if __name__ == "__main__":
    main()
