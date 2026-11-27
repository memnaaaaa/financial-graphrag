"""Old vs new chunk header, answer level: correct / hallucination / missing, grounding checks, failure stages.
Old run: results/v2_old_vs_new_header/old_header_per_question.jsonl. New runs: results/v2_fixed_chunks + results/v2_distilbert.
Prints markdown tables (pasted into results/v2_old_vs_new_header/comparison.md); writes no file."""
import json, collections, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
from rag import metrics
Q = {json.loads(l)["qid"]: json.loads(l) for l in open(R/"data/questions_v2.jsonl")}
def text_map(path):
    return {json.loads(l)["chunk_id"]: json.loads(l)["text"] for l in open(path)}
def load(paths, chunks):
    ct = text_map(chunks); rows = {}
    for p in paths:
        for l in open(R/p if p.endswith(".jsonl") else R/p/"per_question.jsonl"):
            r = json.loads(l)
            if "n_sentences" not in r:
                r.update(metrics.answer_support(r["answer"], {c: ct[c] for c in metrics.cited_ids(r["answer"]) if c in ct}))
            rows[(r["qid"], r["config"], r["k"])] = r
    return rows
old = load(["results/v2_old_vs_new_header/old_header_per_question.jsonl"], R/"../chunks_old_header_6filings.jsonl")
new = load(["results/v2_fixed_chunks", "results/v2_distilbert"], R/"data/chunks.jsonl")
CFG = ["bge-small", "bge-small+rerank", "distilbert", "distilbert+rerank"]
def sel(rows, cfg, k, t=None): return [r for (q, c, kk), r in rows.items() if c == cfg and kk == k and (t is None or Q[q]["type"] == t)]
pct = lambda a, b: f"{a/b:.0%}" if b else "n/a"
def agg(xs):
    n = len(xs); v = collections.Counter(r["verdict"] for r in xs); st = collections.Counter(r["error_stage"] for r in xs)
    tr = metrics.aggregate_traceability(xs)
    ns = sum(r["n_sentences"] for r in xs); sup = sum(r["n_supported_sentences"] for r in xs)
    return dict(n=n, cor=v["correct"]/n, hal=v["hallucination"]/n, mis=(n-v["correct"]-v["hallucination"])/n,
                allf=sum(r["all_facts"] for r in xs)/n, unsup=tr["unsupported_number_rate"], cit=tr["citation_accuracy"],
                sup=sup/ns if ns else 0, ok=st["ok"], ret=st["retrieval"], gen=st["generation"])
out = ["| Configuration | k | Header | AllFacts | Correct | Halluc. | Missing | Unsupp. numbers | Citation acc. | Answer support | ok | retrieval fail | generation fail |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for cfg in CFG:
    for k in (5, 10):
        for nm, rows in (("old", old), ("new", new)):
            a = agg(sel(rows, cfg, k))
            out.append(f"| {cfg} | {k} | {nm} | {a['allf']:.2f} | {a['cor']:.1%} | {a['hal']:.1%} | {a['mis']:.1%} | {a['unsup']:.1%} | {a['cit']:.1%} | {a['sup']:.1%} | {a['ok']} | {a['ret']} | {a['gen']} |")
print("\n".join(out)); print()
T = ["single", "relation", "relation_text", "relation_deep", "cross_year", "cross_company"]
for metric, label in (("cor", "Correct answers"), ("allf", "Every gold fact retrieved (AllFacts)")):
    print(f"**{label} by question type, k = 10 (old -> new)**\n")
    print("| Question type | n | " + " | ".join(CFG) + " |\n|---|---|" + "---|" * len(CFG))
    for t in T:
        cells = [f"{agg(sel(old,c,10,t))[metric]:.0%} -> {agg(sel(new,c,10,t))[metric]:.0%}" for c in CFG]
        print(f"| {t} | {len(sel(new,CFG[0],10,t))} | " + " | ".join(cells) + " |")
    print()
print("**Questions whose verdict changed (old -> new), k = 10**\n\n| Configuration | became correct | became wrong | net |\n|---|---|---|---|")
for c in CFG:
    g = [q for (q, cc, k), r in new.items() if cc == c and k == 10 and r["verdict"] == "correct" and old[(q, c, 10)]["verdict"] != "correct"]
    l = [q for (q, cc, k), r in new.items() if cc == c and k == 10 and r["verdict"] != "correct" and old[(q, c, 10)]["verdict"] == "correct"]
    print(f"| {c} | {len(g)} ({', '.join(sorted(g))}) | {len(l)} ({', '.join(sorted(l))}) | {len(g)-len(l):+d} |")
