"""Phase 2: extract relations written in prose (licences, acquisitions, partners, ...) with Gemini,
then add them to the rule-based graph as a new version (fin10k_v0 -> fin10k_v1).

Step 1, extract (calls Gemini; needs GEMINI_API_KEY in the repo-root .env file):
    python data/graph/extract_relations_llm.py extract --test     # 5 hand-picked chunks only
    python data/graph/extract_relations_llm.py extract            # all text chunks of Items 1, 7, 8
Answers are cached in data/graph/llm_cache/<model>.jsonl (one line per chunk). A rerun skips
chunks already in the cache, so it is safe to stop and restart (e.g. after hitting a daily limit).

Step 2, build (no API calls):
    python data/graph/extract_relations_llm.py build
Reads the cache, keeps only triples whose evidence quote is really in the chunk, merges names
into existing nodes, and writes data/graph/fin10k_v1/processed/stage1/ plus merge_report.csv.

Only the Python standard library is used (the Gemini REST API is called with urllib).
"""
import argparse
import ast
import collections
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

TICKERS = ["JNJ", "AAPL", "MSFT"]
SECTIONS = {"Item 1", "Item 7", "Item 8"}
TEST_CHUNKS = [
    "JNJ_FY2025_ITEM1_0011",    # DARZALEX: Genmab patents, exclusive licence to Janssen Biotech
    "JNJ_FY2025_ITEM7_0031",    # Shockwave Medical acquisition
    "MSFT_FY2025_ITEM8_0023",   # OpenAI partnership
    "MSFT_FY2025_ITEM1_0010",   # competition + Intelligent Cloud products
    "AAPL_FY2025_ITEM7_0010",   # outsourcing partners / suppliers
]
DEFAULT_MODEL = "gemini-3.5-flash-lite"

RELATIONS = {
    "licensed_from": "A company or product uses rights (patents, technology, a drug) licensed from another company.",
    "acquired": "A company acquired another company or business.",
    "partners_with": "Two organizations have a named collaboration, alliance, joint venture or partnership.",
    "competes_with": "A company or product competes with a named company or product.",
    "manufactures": "A company makes or produces a product (or another company makes it for them).",
    "supplies_to": "A company supplies components, products or services to another company.",
    "has_product": "A company, segment or business line sells or offers this product or service (owning patents for it is not enough).",
    "subsidiary_of": "A company is a subsidiary (owned or controlled) of another company.",
    "invests_in": "A company holds an investment or equity stake in another company.",
}

PROMPT = """You extract business relationships from one passage of a Form 10-K annual report.

The filer is {company} ({ticker}), fiscal year {fy}. When the passage says "the Company", "we",
"us" or "our", the entity is "{company}".

Allowed relations (use exactly these names; head -> tail):
{relations}

Direction matters. Examples:
- "Johnson & Johnson" has_product "DARZALEX"  (never "DARZALEX" has_product "Johnson & Johnson")
- "Janssen Biotech, Inc." licensed_from "Genmab A/S"
- "Microsoft Corporation" acquired "Activision Blizzard"

Rules:
1. Only include relationships the passage states directly. Do not use outside knowledge.
2. Head and tail must be named organizations or named products/services (for example
   "Genmab A/S", "DARZALEX", "Azure"). Skip people, places, laws, generic groups such as
   "competitors" or "suppliers", and numbers.
3. Write names as they appear in the passage, without descriptions in brackets:
   "DARZALEX (daratumumab)" -> "DARZALEX".
4. "evidence" must be copied word for word from the passage (one sentence or part of one,
   at most 40 words) and must support the relationship.
5. head_type and tail_type are one of: company, product, segment.
6. When a subsidiary holds a licence, return both "<subsidiary> licensed_from <licensor>" and
   "<product> licensed_from <licensor>".
7. competes_with, partners_with and supplies_to need a named company or product on both sides.
   Skip generic groups such as "security solution vendors" or "online professional networks".
8. If there are no relationships, return an empty list.

Passage:
\"\"\"
{text}
\"\"\"
"""

SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "head": {"type": "STRING"},
            "head_type": {"type": "STRING", "enum": ["company", "product", "segment"]},
            "relation": {"type": "STRING", "enum": list(RELATIONS)},
            "tail": {"type": "STRING"},
            "tail_type": {"type": "STRING", "enum": ["company", "product", "segment"]},
            "evidence": {"type": "STRING"},
        },
        "required": ["head", "head_type", "relation", "tail", "tail_type", "evidence"],
    },
}


# ---------------------------------------------------------------- shared helpers
def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_chunks(repo):
    out = []
    for line in open(os.path.join(repo, "data/chunks/chunks.jsonl"), encoding="utf-8"):
        c = json.loads(line)
        if c["ticker"] in TICKERS and c["section"] in SECTIONS and not c["has_table"]:
            out.append(c)
    return out


def cache_path(repo, model):
    return os.path.join(repo, "data/graph/llm_cache", f"{model}.jsonl")


def read_cache(path):
    done = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                done[r["chunk_id"]] = r
    return done


# ---------------------------------------------------------------- step 1: extract
def call_gemini(key, model, prompt, retries=6):
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
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 503) and attempt < retries - 1:
                if e.code == 429 and "PerDay" in msg:
                    raise SystemExit("Daily Gemini limit reached. Run the same command again tomorrow; "
                                     "finished chunks are cached.")
                print(f"  HTTP {e.code}, waiting {wait}s ...", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            raise SystemExit(f"Gemini error HTTP {e.code}: {msg}")
        except (KeyError, IndexError):
            return "[]"                                      # blocked or empty answer
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(wait)
                continue
            raise SystemExit(f"Cannot reach Gemini: {e}")
    return "[]"


def extract(a):
    key = os.environ.get("GEMINI_API_KEY") or load_env(os.path.join(a.repo, ".env")).get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY not found in the environment or in .env at the repo root.")
    chunks = load_chunks(a.repo)
    if a.test:
        by_id = {c["chunk_id"]: c for c in chunks}
        chunks = [by_id[c] for c in TEST_CHUNKS]
    if a.limit:
        chunks = chunks[: a.limit]
    path = cache_path(a.repo, a.model)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    done = read_cache(path)
    todo = chunks if a.redo else [c for c in chunks if c["chunk_id"] not in done]
    print(f"{len(chunks)} chunks selected, {len(chunks) - len(todo)} already cached, {len(todo)} to send "
          f"to {a.model} (about {len(todo) * 60 / a.rpm / 60:.0f} min at {a.rpm} per minute)")
    rel_text = "\n".join(f"- {k}: {v}" for k, v in RELATIONS.items())
    with open(path, "a", encoding="utf-8") as out:
        for i, c in enumerate(todo, 1):
            t0 = time.time()
            prompt = PROMPT.format(company=c["company"], ticker=c["ticker"], fy=c["fiscal_year"],
                                   relations=rel_text, text=c["text"].split("\n", 1)[-1])
            raw = call_gemini(key, a.model, prompt)
            try:
                triples = json.loads(raw)
            except json.JSONDecodeError:
                triples = []
            out.write(json.dumps({"chunk_id": c["chunk_id"], "model": a.model, "triples": triples,
                                  "raw": raw if not triples else ""}, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(todo)}] {c['chunk_id']}: {len(triples)} triples")
            if a.test:
                for t in triples:
                    print(f"     {t['head']} --{t['relation']}--> {t['tail']}   \"{t['evidence'][:90]}\"")
            time.sleep(max(0.0, 60.0 / a.rpm - (time.time() - t0)))
    print("cache:", path)


# ---------------------------------------------------------------- step 2: build fin10k_v1
SUFFIX = re.compile(r"\b(incorporated|inc|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|plc|ag|"
                    r"gmbh|a/s|as|sa|s\.a|nv|n\.v|bv|b\.v|lp|l\.p|holdings?)\b\.?", re.I)


def norm(name):
    s = name.lower().replace("&", " and ").replace("’", "'")
    s = re.sub(r"\((jnj|aapl|msft)\)$", "", s)
    s = SUFFIX.sub(" ", s)
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9+' ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


FILER_WORDS = {"the company", "company", "we", "us", "our", "the registrant", "registrant"}


def squash(s):
    """Lowercase letters and digits only, so curly quotes, dashes or spacing changed by the
    model do not make a real quote look missing."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def build(a):
    v0 = os.path.join(a.repo, "data/graph", a.base, "processed/stage1")
    nodes = {r["name"]: (r["type"], ast.literal_eval(r["attributes"]))
             for r in csv.DictReader(open(f"{v0}/nodes.csv", encoding="utf-8"))}
    rels = {r["name"]: ast.literal_eval(r["attributes"])
            for r in csv.DictReader(open(f"{v0}/relations.csv", encoding="utf-8"))}
    edges = {(r["source"], r["relation"], r["target"]): ast.literal_eval(r["attributes"])
             for r in csv.DictReader(open(f"{v0}/edges.csv", encoding="utf-8"))}
    chunks = {c["chunk_id"]: c for c in load_chunks(a.repo)}
    cache = read_cache(cache_path(a.repo, a.model))
    if not cache:
        raise SystemExit("No cached answers yet; run the extract step first.")

    # Name index over existing entity nodes: normalised name -> [(node, ticker)]
    index = collections.defaultdict(list)
    for name, (ntype, attrs) in nodes.items():
        if ntype != "entity" or attrs.get("kind") in ("Metric", "FiscalYear"):
            continue
        tk = attrs.get("ticker") or attrs.get("parent_ticker")
        kind = attrs.get("kind")
        keys = {norm(name)} | {norm(p) for p in re.sub(r" \((JNJ|AAPL|MSFT)\)$", "", name).split("/")}
        for k in keys:
            if k:
                index[k].append((name, tk, kind))
    company_of = {n: a_.get("ticker") for n, (t, a_) in nodes.items() if a_.get("kind") == "Company"}
    filer = {tk: n for n, tk in company_of.items()}

    report = []

    kinds_for = {"company": {"Company", "Subsidiary", "Organization"},
                 "product": {"Product", "BusinessLine"}, "segment": {"Segment", "BusinessLine"}}

    def pick(cands, ntype):
        """cands: [(node, ticker, kind)] -> one node name or None."""
        names = {n for n, _, _ in cands}
        if len(names) > 1 and any(kd == "Company" for _, _, kd in cands):
            names = {n for n, _, kd in cands if kd == "Company"}     # the filer wins over subsidiaries
        if len(names) > 1:
            names = {n for n, _, kd in cands if kd in kinds_for.get(ntype, set())} or names
        return names.pop() if len(names) == 1 else None

    def resolve(raw, ntype, ticker):
        if raw.strip().lower() in FILER_WORDS:
            return filer[ticker], "filer"
        k = norm(raw)
        if not k:
            return None, "empty"
        hits = [h for h in index.get(k, []) if h[1] in (ticker, None)] or index.get(k, [])
        if hits:
            node = pick(hits, ntype)
            return (node, "exact") if node else (None, "ambiguous")
        # Short name of an existing node of the same company ("Shockwave" -> "Shockwave Medical,
        # Inc."): take the shortest matching names, then prefer the right kind of node.
        pref = [(kk, h) for kk, lst in index.items() if kk.startswith(k + " ")
                for h in lst if h[1] == ticker]
        if pref:
            shortest = min(len(kk) for kk, _ in pref)
            node = pick([h for kk, h in pref if len(kk) == shortest], ntype)
            return (node, "prefix") if node else (None, "ambiguous")
        return None, "new"

    kept = dropped = 0
    new_nodes = {}
    for cid, rec in cache.items():
        c = chunks.get(cid)
        if not c:
            continue
        body = squash(c["text"])
        for t in rec.get("triples") or []:
            head, rel, tail, ev = t.get("head", ""), t.get("relation"), t.get("tail", ""), t.get("evidence", "")
            if rel == "has_product" and t.get("head_type") == "product" and t.get("tail_type") in ("company", "segment"):
                head, tail = tail, head                       # model wrote it backwards: flip
                t = dict(t, head_type=t.get("tail_type"), tail_type="product")
            why = None
            if rel not in RELATIONS:
                why = "unknown relation"
            elif not ev or squash(ev) not in body:
                why = "evidence not in chunk"
            elif any(not re.search(r"[A-Z]", x) and x.strip().lower() not in FILER_WORDS for x in (head, tail)):
                why = "generic name (no capital letter)"
            elif norm(head) == norm(tail):
                why = "head = tail"
            else:
                for side in (head, tail):
                    if side.strip().lower() not in FILER_WORDS and squash(side) not in body:
                        why = f"name not in chunk: {side}"
            if why:
                dropped += 1
                report.append([cid, head, rel, tail, "dropped", why, "", ""])
                continue
            ends = []
            for raw, typ in ((head, t.get("head_type")), (tail, t.get("tail_type"))):
                node, how = resolve(raw, typ, c["ticker"])
                if node is None:
                    clean = raw.strip()
                    node = clean if clean not in nodes or nodes[clean][0] == "entity" else f"{clean} (llm)"
                    if node not in nodes:
                        kind = {"company": "Organization", "product": "Product", "segment": "Segment"}.get(typ, "Organization")
                        new_nodes.setdefault(node, ("entity", {"kind": kind, "source": "llm",
                                                               "context_ticker": c["ticker"]}))
                    how = how if how == "ambiguous" else "new"
                ends.append((raw, node, how))
            (hr, hn, hh), (tr, tn, th) = ends
            attrs = edges.setdefault((hn, rel, tn), {"source": "llm", "chunk_ids": [], "evidence": ev})
            if cid not in attrs.get("chunk_ids", []):
                attrs.setdefault("chunk_ids", []).append(cid)
            for n in (hn, tn):
                edges.setdefault((n, "is_mentioned_in", cid), {})
            kept += 1
            report.append([cid, head, rel, tail, "kept", "", f"{hn} [{hh}]", f"{tn} [{th}]"])

    for n, v in new_nodes.items():
        nodes.setdefault(n, v)
    for r, d in RELATIONS.items():
        rels.setdefault(r, {"description": d})

    out = os.path.join(a.repo, "data/graph", a.name, "processed/stage1")
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/nodes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "type", "attributes"])
        for n, (t, at) in sorted(nodes.items(), key=lambda x: (x[1][0], x[0])):
            w.writerow([n, t, repr(at)])
    with open(f"{out}/relations.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "attributes"])
        for r, at in rels.items():
            w.writerow([r, repr(at)])
    with open(f"{out}/edges.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "relation", "target", "attributes"])
        for (s, r, t), at in sorted(edges.items()):
            w.writerow([s, r, t, repr(at)])
    rep = os.path.join(a.repo, "data/graph", a.name, "merge_report.csv")
    with open(rep, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["chunk_id", "head", "relation", "tail", "status", "reason", "head_node", "tail_node"])
        w.writerows(report)
    llm_edges = sum(1 for (_, r, _), at in edges.items() if at.get("source") == "llm")
    how = collections.Counter(x.split("[")[-1].rstrip("]") for row in report if row[4] == "kept" for x in row[6:8])
    stats = {"base": a.base, "model": a.model, "chunks_in_cache": len(cache), "triples_kept": kept,
             "triples_dropped": dropped, "llm_edges": llm_edges, "new_nodes": len(new_nodes),
             "name_matching": dict(how), "nodes": len(nodes), "edges": len(edges)}
    json.dump(stats, open(os.path.join(a.repo, "data/graph", a.name, "graph_stats.json"), "w"), indent=2)
    print(json.dumps(stats, indent=2))
    print("wrote", out, "and", rep)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["extract", "build"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--test", action="store_true", help="extract: only the 5 test chunks")
    ap.add_argument("--redo", action="store_true",
                    help="extract: send the selected chunks again even if cached (newest answer is used)")
    ap.add_argument("--limit", type=int, default=0, help="extract: only the first N chunks")
    ap.add_argument("--rpm", type=float, default=10, help="extract: max requests per minute")
    ap.add_argument("--base", default="fin10k_v0", help="build: graph to start from")
    ap.add_argument("--name", default="fin10k_v1", help="build: output graph name")
    a = ap.parse_args()
    extract(a) if a.step == "extract" else build(a)


if __name__ == "__main__":
    main()
