"""Ablation: pick G-reasoner's start nodes with Gemini instead of the rule-based matcher.

gfmrag's default pipeline finds start nodes with an LLM (NER) plus an embedding-based entity linker.
Here Gemini does both in one call: it gets the question and the list of all entity node names in
the graph and returns the names the question refers to. Names that are not in the graph are
dropped and counted. The rule-based matcher (entity_index.py) runs on the same questions for
comparison, and both are timed.

Runs locally with the standard library only (Gemini REST API via urllib, like
data/graph/extract_relations_llm.py). Needs GEMINI_API_KEY in the environment or in the repo-root
.env file (git-ignored). Answers are cached in the output file: a rerun only calls Gemini for
questions not answered yet, so the start nodes stay fixed once written (use --refresh to redo).

    python gemini_ner.py --repo ..                     # golden questions covered by fin10k_v0 + probes
    python gemini_ner.py --repo .. --repeat 3          # also check that Gemini answers the same each time

Output (default results/gemini_ner_fin10k_v0/):
    start_nodes.jsonl   one line per question: rule vs Gemini start nodes, timings (evaluate.py
                        --start-nodes reads this to run G-reasoner with Gemini's start nodes)
    matching_summary.json   agreement and speed of the two matchers
"""
import argparse
import ast
import csv
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from entity_index import EntityIndex  # noqa: E402

csv.field_size_limit(sys.maxsize)
# Same model as data/graph/extract_relations_llm.py. The baseline's gemini-2.5-flash-lite is no longer
# offered to new API keys (HTTP 404, Oct 2026).
DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Paraphrases the alias table was not written for (not golden questions; no gold chunks, matching only).
PROBES = [
    "What did Apple spend on sales and marketing in fiscal 2025?",
    "What was J&J's top line last year?",
    "How much did Microsoft invest in R&D in its most recent fiscal year?",
    "What was Apple's operating profit in fiscal 2025?",
    "What were iPhone sales in 2025?",
    "How did Johnson and Johnson's pharmaceutical business perform in 2024?",
    "What were Microsoft's cloud revenues in fiscal 2025?",
    "Which subsidiaries does J&J have in Ireland?",
    "What was the company's gross margin percentage in fiscal 2024?",
]

PROMPT = """You link a question about company 10-K filings to nodes of a knowledge graph.

Below is every entity node in the graph, one per line as "name [kind]". Return the names of the
nodes the question refers to: companies, subsidiaries, segments, business lines, products,
financial metrics, locations and fiscal years. Fiscal-year nodes are per company (e.g. a year
for Apple is "FY2025 (AAPL)"); pick the fiscal year of each company the question is about.
Copy names exactly as listed. Return an empty list if nothing matches. Do not answer the question.

Entity nodes:
{nodes}

Question: {question}"""

SCHEMA = {"type": "ARRAY", "items": {"type": "STRING"}}


def load_key(repo):
    key = os.environ.get("GEMINI_API_KEY")
    env = os.path.join(repo, ".env")
    if not key and os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("GEMINI_API_KEY not set: put GEMINI_API_KEY=... in the repo-root .env file")
    return key


def call_gemini(key, model, prompt, retries=6):
    """(answer text, seconds for the successful call). Retries on rate limits and server errors."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                             "responseSchema": SCHEMA},
    }).encode()
    wait = 10
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json", "x-goog-api-key": key})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            secs = time.perf_counter() - t0
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts), secs
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (403, 429, 500, 503) and attempt < retries - 1:   # 403 seen as a transient throttle
                if e.code == 429 and "PerDay" in msg:
                    sys.exit("Daily Gemini limit reached; rerun tomorrow (answers so far are saved).")
                print(f"  HTTP {e.code}, waiting {wait}s ...", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            sys.exit(f"Gemini error HTTP {e.code}: {msg}")
        except (KeyError, IndexError):
            return "[]", time.perf_counter() - t0            # blocked or empty answer
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(wait)
                continue
            sys.exit(f"Cannot reach Gemini: {e}")
    return "[]", 0.0


def clean(name, entities):
    """Drop a copied " [Kind]" label ("Revenue [Metric]" -> "Revenue") when that gives a graph node."""
    m = re.fullmatch(r"(.+?) \[\w+\]", name.strip())
    return m.group(1) if m and m.group(1) in entities and name not in entities else name.strip()


def graph_entities(nodes_csv):
    """{name: kind} for every entity node."""
    out = {}
    for r in csv.DictReader(open(nodes_csv, encoding="utf-8")):
        if r["type"] == "entity":
            out[r["name"]] = ast.literal_eval(r["attributes"] or "{}").get("kind", "")
    return out


def golden_questions(repo, nodes_csv):
    """Golden questions whose gold chunks are all document nodes (same rule as evaluate.py)."""
    docs = {r["name"] for r in csv.DictReader(open(nodes_csv, encoding="utf-8")) if r["type"] == "document"}
    path = os.path.join(repo, "vector_rag_baseline", "data", "questions.jsonl")
    qs = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    return [q for q in qs if all(g in docs for g in q["gold_chunk_ids"])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--graph", default="fin10k_v0")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--repeat", type=int, default=1, help="calls per question (>1 checks consistency)")
    ap.add_argument("--no-probes", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="ignore saved answers and call Gemini again")
    ap.add_argument("--out", default=None, help="default: results/gemini_ner_<graph>")
    a = ap.parse_args()

    nodes_csv = os.path.join(a.repo, "data", "graph", a.graph, "processed", "stage1", "nodes.csv")
    out_dir = a.out or os.path.join(HERE, "results", f"gemini_ner_{a.graph}")
    out_path = os.path.join(out_dir, "start_nodes.jsonl")
    entities = graph_entities(nodes_csv)
    node_list = "\n".join(f"{n} [{k}]" for n, k in sorted(entities.items(), key=lambda x: (x[1], x[0])))

    t0 = time.perf_counter()
    index = EntityIndex(nodes_csv)
    rule_build_ms = (time.perf_counter() - t0) * 1000

    questions = [{"qid": q["qid"], "question": q["question"], "set": "golden"}
                 for q in golden_questions(a.repo, nodes_csv)]
    if not a.no_probes:
        questions += [{"qid": f"p{i:02d}", "question": q, "set": "probe"} for i, q in enumerate(PROBES, 1)]

    saved = {}
    if os.path.exists(out_path) and not a.refresh:
        for line in open(out_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                saved[r["qid"]] = r
    key = None
    rows = []
    os.makedirs(out_dir, exist_ok=True)

    def save():  # after every question, so a stopped run (rate limit, error) keeps its answers
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in rows + [s for k, s in saved.items()
                                                             if k not in {r["qid"] for r in rows}]) + "\n")

    for q in questions:
        t1 = time.perf_counter()
        rule = index.find(q["question"])
        rule_ms = (time.perf_counter() - t1) * 1000
        if q["qid"] in saved and saved[q["qid"]]["question"] == q["question"] \
                and len(saved[q["qid"]]["gemini_runs"]) >= a.repeat:
            r = saved[q["qid"]]
            r.update(rule_start_nodes=rule, rule_ms=rule_ms)
        else:
            key = key or load_key(a.repo)
            runs, secs = [], []
            for _ in range(a.repeat):
                text, s = call_gemini(key, a.model, PROMPT.format(nodes=node_list, question=q["question"]))
                try:
                    names = [n for n in json.loads(text) if isinstance(n, str)]
                except json.JSONDecodeError:
                    names = []
                runs.append(names)
                secs.append(s)
            r = {**q, "model": a.model, "rule_start_nodes": rule, "rule_ms": rule_ms,
                 "gemini_runs": runs, "gemini_ms": [s * 1000 for s in secs]}
        # Start nodes = Gemini's first answer. It sometimes copies the " [Kind]" label from the node
        # list; that is stripped (and counted) before names are checked against the graph.
        first = [clean(n, entities) for n in r["gemini_runs"][0]]
        r["gemini_label_copied"] = sum(n != c for n, c in zip(r["gemini_runs"][0], first))
        r["gemini_start_nodes"] = sorted({n for n in first if n in entities})
        r["gemini_invalid"] = sorted({n for n in first if n not in entities})
        r["agree"] = sorted(r["rule_start_nodes"]) == r["gemini_start_nodes"]
        r["only_rule"] = sorted(set(r["rule_start_nodes"]) - set(r["gemini_start_nodes"]))
        r["only_gemini"] = sorted(set(r["gemini_start_nodes"]) - set(r["rule_start_nodes"]))
        runs_clean = [sorted({clean(n, entities) for n in x}) for x in r["gemini_runs"]]
        r["gemini_consistent"] = all(x == runs_clean[0] for x in runs_clean)
        rows.append(r)
        save()
        flag ="same" if r["agree"] else f"rule-only {r['only_rule']}  gemini-only {r['only_gemini']}"
        print(f"{r['qid']:>4} [{r['set']}] {statistics.mean(r['gemini_ms']):6.0f} ms  {flag}"
              + (f"  invalid {r['gemini_invalid']}" if r["gemini_invalid"] else ""))

    with open(out_path, "w", encoding="utf-8") as f:   # final file: only this run's questions
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")

    all_ms = [ms for r in rows for ms in r["gemini_ms"]]
    summary = {"graph": a.graph, "model": a.model, "entity_nodes": len(entities),
               "rule_index_build_ms": rule_build_ms,
               "rule_ms_per_question": statistics.mean(r["rule_ms"] for r in rows),
               "gemini_ms_per_call_mean": statistics.mean(all_ms),
               "gemini_ms_per_call_median": statistics.median(all_ms),
               "gemini_calls": len(all_ms)}
    for s in ("golden", "probe"):
        rs = [r for r in rows if r["set"] == s]
        if rs:
            summary[s] = {"questions": len(rs),
                          "same_start_nodes": sum(r["agree"] for r in rs),
                          "questions_with_invalid_names": sum(bool(r["gemini_invalid"]) for r in rs),
                          "questions_with_copied_label": sum(r["gemini_label_copied"] > 0 for r in rs),
                          "gemini_consistent_across_repeats": sum(r["gemini_consistent"] for r in rs)}
    json.dump(summary, open(os.path.join(out_dir, "matching_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))
    print("saved to", out_dir)


if __name__ == "__main__":
    main()
