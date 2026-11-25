"""Trace view: follow every number in one answer back to the filing it came from.

    python answer_step/trace.py answer_step/results/<run>/per_question.jsonl v2_q11
    -> answer_step/traces/<run>_<qid>.md

For each sentence with a number: the citation -> (Value node: metric, year, number) -> the passage and the
exact line that prints the number -> the filing (company, fiscal year, accession, section) -> the SEC EDGAR
link that opens the 10-K at that number (Values) or the document (passages).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "vector_rag_baseline"))
from rag import metrics  # noqa: E402

from graph_context import VALUE_ID_RE, Graph, load_chunks  # noqa: E402


def line_with(text, nums):
    """The line of a passage that prints one of the numbers (the table row or sentence), shortened."""
    body = text.split("\n", 1)[-1]
    for ln in body.split("\n"):
        vals = [v for v, _ in metrics.extract_numbers(ln)]
        if any(metrics._supported(x, d, vals) for x, d in nums):
            return ln.strip()[:300]
    return None


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    path, qid = sys.argv[1], sys.argv[2]
    graph = sys.argv[3] if len(sys.argv) > 3 else os.path.join(REPO, "data/graph/fin10k_v1/processed/stage1")
    rec = next((json.loads(l) for l in open(path, encoding="utf-8") if json.loads(l)["qid"] in (qid, "v2_" + qid)), None)
    if not rec:
        raise SystemExit(f"{qid} not in {path}")
    g, chunks = Graph(graph), load_chunks(os.path.join(REPO, "data/chunks/chunks.jsonl"))
    filing = lambda c: chunks[c]
    out = [f"# Trace: {rec['qid']} ({rec['system']}, k = {rec['k']})", "",
           f"**Question:** {rec['question']}", "", f"**Answer:** {rec['answer']}", "",
           f"**Judge:** {rec['verdict']} ({rec['judge_reason']}) · **Reference:** {rec['gold_answer']}", ""]
    n = 0
    for s in re.split(r"(?<=[.;!?])\s+|\n+", rec["answer"]):
        nums = metrics.extract_numbers(re.sub(r"\[[^\]]*\]", " ", s), drop=rec["question"])
        if not nums:
            continue
        n += 1
        out += [f"## Claim {n}", "", f"> {s.strip()}", ""]
        cites = VALUE_ID_RE.findall(s) + metrics.cited_ids(s)
        if not cites:
            out += ["- **No citation**: this number cannot be traced.", ""]
            continue
        for cid in dict.fromkeys(cites):
            if VALUE_ID_RE.fullmatch(cid):
                if cid not in g.value_of:
                    out += [f"- `{cid}`: **not a Value in the graph** (invented id)", ""]
                    continue
                a = g.nodes[g.value_of[cid]][1]
                c = chunks[a["source_chunk_id"]]
                ok = any(metrics._supported(x, d, [v for v, _ in metrics.extract_numbers(a["printed_value"])]) for x, d in nums)
                out += [f"- **Value** `{cid}`: {g.value_of[cid]}",
                        f"  - metric: {a['metric']} · fiscal year: {a['fiscal_year']} · number: {a['display']}"
                        f" · XBRL: `{a['xbrl_concept']}` (fact `{a['xbrl_fact_id']}`)",
                        f"  - number in the sentence matches the Value: **{'yes' if ok else 'NO'}**",
                        f"  - printed in passage `{c['chunk_id']}`: `{line_with(c['text'], metrics.extract_numbers(a['printed_value'])) or a['printed_value']}`",
                        f"  - filing: {c['company']} 10-K, {c['fiscal_year']} (year ended {c['period_end']}), "
                        f"{c['section']} {c['section_title']}, accession {c['accession']}",
                        f"  - open at the number: {a['source_fact_url']}", ""]
            elif cid in chunks:
                c = chunks[cid]
                ln = line_with(c["text"], nums)
                out += [f"- **Passage** `{cid}`",
                        f"  - line with the number: " + (f"`{ln}`" if ln else "**number not found in this passage**"),
                        f"  - filing: {c['company']} 10-K, {c['fiscal_year']} (year ended {c['period_end']}), "
                        f"{c['section']} {c['section_title']}, accession {c['accession']}",
                        f"  - document: {c['source_url']}", ""]
            else:
                out += [f"- `{cid}`: **not a passage in the corpus**", ""]
    if not n:
        out.append("_The answer states no numbers._")
    os.makedirs(os.path.join(HERE, "traces"), exist_ok=True)
    dest = os.path.join(HERE, "traces", f"{os.path.basename(os.path.dirname(path))}_{rec['qid']}.md")
    open(dest, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print("wrote", dest)


if __name__ == "__main__":
    main()
