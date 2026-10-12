"""Regenerate README.md and GOLDEN_SET.md from the current data and results, so they never go stale."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q = [json.loads(l) for l in open(ROOT / "data/questions.jsonl", encoding="utf-8")]
RUN = ROOT / "results/full_run_2/summary.json"
S = json.load(open(RUN)) if RUN.exists() else []
validated = [q for q in Q if q["gold_source"].startswith("llm-labeler")]
types = {t: sum(q["type"] == t for q in Q) for t in ("single", "within", "cross")}
replies = sorted(p.stem for p in (ROOT / "data/labeling/replies").glob("q*.json"))
name = {"bge-small": "bge-small", "bge-small+rerank": "bge-small + rerank", "distilbert": "DistilBERT",
        "distilbert+rerank": "DistilBERT + rerank"}

# ----------------------------------------------------------------- GOLDEN_SET.md
g = f"""# Golden set

The golden set is the list of questions used to evaluate retrieval, with the **gold chunk ids** that a retriever should
find and a **gold answer** that the LLM judge compares generated answers against.

## Status: {len(validated)} of {len(Q)} questions validated

| | Count |
|---|---|
| Questions | {len(Q)} ({types['single']} single-fact, {types['within']} multi-hop within one company, {types['cross']} cross-company) |
| Gold labels validated by an independent LLM labeler | **{len(validated)}** ({', '.join(q['qid'] for q in validated) or 'none'}) |
| Gold labels from pattern matching, **not yet verified** | **{len(Q) - len(validated)}** |
| Labeler replies received so far | {len(replies)} ({', '.join(replies) or 'none'}) |

Treat every retrieval number in this repo as **preliminary** until all questions are validated and checked by a human
against the filings.

## Files

| File | What it is |
|---|---|
| `data/questions.jsonl` | The golden set currently used by the evaluation. One JSON object per question. |
| `data/questions_pattern_gold.jsonl` | The original pattern-matched labels, kept as a backup and for comparison. |
| `data/labeling/q01.txt` ... `q19.txt` | **Not stored in this repo** (they contain chunk text). Candidate-chunk pools sent to the labeler (40 chunks for single-filing questions, 72 for two-filing questions, shuffled, no reference answer). Regenerate them with `python scripts/build_label_pools.py` once `data/chunks.jsonl` is in place. |
| `data/labeling/PROMPT.txt` | The fixed labeler prompt. |
| `data/labeling/replies/qNN.json` | Labeler replies (saved with the per-chunk `reason` text omitted). |
| `scripts/build_questions.py` | Builds the pattern-based gold labels. |
| `scripts/build_label_pools.py` | Builds the candidate pools for labeling. |
| `scripts/ingest_labels.py` | Validates labeler replies and applies them to `questions.jsonl`. |

## Row format (`data/questions.jsonl`)

```json
{{"qid": "q01", "hops": 1, "type": "single", "question": "...", "gold_chunk_ids": ["AAPL_FY2025_ITEM7_0004", "..."],
 "gold_answer": "...", "gold_source": "llm-labeler (validated)"}}
```

`type` is `single`, `within` (multi-hop inside one company) or `cross` (two companies). `gold_source` is
`llm-labeler (validated)` or `pattern-match (unverified)`.

## How the gold chunks were made

1. **Pattern matching (all questions).** For each fact, every chunk in the filing the question names whose text matches a
   label-plus-number pattern (for example `Total net sales | $416,161`) is gold. This counts duplicates across MD&A and the
   financial statements as gold, because any of them answers the question. A pattern can miss a valid chunk.
2. **Independent LLM labeling.** For each question, a pool of candidate chunks is built from bge-small, DistilBERT and BM25
   results restricted to the named filings, plus 8 off-target chunks from other filings and years. The pool is shuffled,
   contains no reference answer, and goes to a labeler from a different model family together with `PROMPT.txt`. The labeler
   marks each chunk `answer`, `supporting` or `irrelevant` and must quote the supporting text verbatim.
3. **Validation (`scripts/ingest_labels.py`).** A reply is accepted only if every candidate chunk is labeled exactly once,
   every `answer` quote appears verbatim in its chunk and contains a figure (a bare column header does not count), and the
   chunk is from the company and fiscal year the question names. Rejected labels are reported, and only validated answers
   replace the gold set. The original file is kept as `data/questions_pattern_gold.jsonl`.

### Rules for what counts as gold

* The company **and fiscal year** must match the question. A prior-year column inside a later filing does not make that
  later filing's chunk an answer for the earlier year.
* A question that needs several facts needs gold chunks for each fact.
* Scope and units must match (for example "net income attributable to X" is not "consolidated net income").

## Questions and gold chunks

| Q | Type | Question | Gold chunks | Source |
|---|---|---|---|---|
"""
for q in Q:
    ids = "<br>".join(f"`{i}`" for i in q["gold_chunk_ids"])
    g += f"| {q['qid']} | {q['type']} | {q['question']} | {ids} | {q['gold_source'].split(' (')[0]} |\n"
g += f"""
## Known limitations

* **Mostly unverified.** Only {len(validated)} of {len(Q)} questions have validated labels.
* **Pattern labels can miss chunks.** For q01 the pattern missed `AAPL_FY2025_ITEM8_0000` (a valid income-statement chunk
  that writes the figure without a `$`), which the labeler found.
* **Pooling limit.** A labeler can only label chunks it is shown. The pools contained 51 of the 57 pattern-based gold chunks, so
  facts phrased very differently from the question (for example "associates" for "employees") may need a second pool.
* **Duplicates are counted.** A fact repeated in several chunks gives a question several gold chunks, which lowers recall and
  precision even when a correct chunk is found. Use hit@k alongside recall@k.
* **Small set.** {len(Q)} questions; one question moves a percentage by {100 / len(Q):.1f} points.
* **Different fiscal year-ends.** Apple (September), Microsoft (June) and Walmart (January) differ, which affects the
  cross-company questions.

## Adding or replacing labels

1. Put the shared chunks file at `data/chunks.jsonl` and run `python scripts/build_label_pools.py` to create `data/labeling/qNN.txt`. Send `data/labeling/PROMPT.txt` and one `qNN.txt` per chat to a labeler from a different model family.
2. Save each JSON reply as `data/labeling/replies/qNN.json`.
3. Run `python scripts/ingest_labels.py` to validate and compare with the current gold, then `--apply` to write the validated
   answers into `data/questions.jsonl` (a backup is kept).
4. Spot-check a few questions against the SEC filings (every chunk has a `source_url`), then rerun the evaluation.
"""
(ROOT / "GOLDEN_SET.md").write_text(g, encoding="utf-8")

# ----------------------------------------------------------------- README.md
tbl = ""
for x in S:
    k = x["k"]
    tbl += (f"| {name[x['config']]} | {k} | {x[f'P@{k}']:.3f} | {x[f'R@{k}']:.3f} | {x.get(f'Hit@{k}', float('nan')):.2f} | "
            f"{x['correct_rate'] * 100:.1f}% | {x['hallucination_rate'] * 100:.1f}% | {x['missing_rate'] * 100:.1f}% | "
            f"{x['retrieval_ms']:.0f} | {x['e2e_mean_ms']:.0f} |\n")
r = f"""# Vector-RAG baseline for multi-hop financial QA

Baseline retrieval-augmented generation pipeline over SEC 10-K filings, built to compare against a GNN retriever
(G-Reasoner fine-tuned on a graph of the same filings). It covers the vector-RAG baseline, a hand-built golden question set,
the evaluation metrics, and the first results.

> **Golden set status: {len(validated)} of {len(Q)} questions validated.** Gold chunk labels for the other
> {len(Q) - len(validated)} questions come from pattern matching and are not yet verified, so all numbers below are preliminary.
> See [GOLDEN_SET.md](GOLDEN_SET.md) for how the golden set was built, its status per question, and its limitations.

## Pipeline

```
chunks.jsonl -> embed (bge-small / DistilBERT) -> FAISS IndexFlatIP -> dense top-k -> optional cross-encoder rerank (top 20)
             -> generate (Gemini 2.5 Flash-Lite, T=0) -> judge (Gemini 2.5 Flash, T=0) -> metrics + latency
```

| Component | Choice |
|---|---|
| Embedding | `BAAI/bge-small-en-v1.5` (33M) and `sentence-transformers/multi-qa-distilbert-cos-v1` (66M) |
| Index | FAISS `IndexFlatIP`, L2-normalized vectors (exact cosine search) |
| Retrieval | Dense top-k, k = 5 and 10 |
| Rerank | `cross-encoder/ms-marco-MiniLM-L-6-v2` over the top 20 (optional) |
| Generator / judge | Gemini 2.5 Flash-Lite / Gemini 2.5 Flash, temperature 0 |
| Metrics | precision@k, recall@k, hit@k, judge accuracy / hallucination / missing rate, latency |

## Results (run `full_run_2`, {len(Q)} questions, 7,339 chunks)

| Config | k | P@k | R@k | Hit@k | Correct | Halluc. | Missing | Retrieval ms | End-to-end ms |
|---|---|---|---|---|---|---|---|---|---|
{tbl}
Definitions of every metric are in `docs/baseline_report_v2.docx` (Appendix A). Main findings: retrieval never picks the wrong
company but picks the wrong fiscal year of the right company 43% of the time; cross-company questions almost never retrieve
both companies' answer chunks; generation is about 94% of end-to-end latency. Raw per-question results are in
`results/full_run_1/` and `results/full_run_2/`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add GEMINI_API_KEY, or use Vertex AI (see below)
python -m pytest -q tests        # unit tests, no network needed
python scripts/smoke_test.py     # checks each tool: encoders, FAISS, reranker, generator, judge

# put the shared chunks file at data/chunks.jsonl (it is not stored in this folder), then:
python scripts/run_eval.py --chunks data/chunks.jsonl --questions data/questions.jsonl \\
    --encoders bge-small distilbert --rerank --out results/my_run
```

**Generator and judge access.** Set `GEMINI_API_KEY` to use Google AI Studio, or leave it unset and call Gemini through Vertex AI
by setting `GOOGLE_CLOUD_PROJECT` (and signing in with `gcloud auth login`). Machine-specific values can go in the git-ignored
`rag/local_config.py` (see `rag/local_config.example.py`).

`data/chunks.jsonl` needs the fields `chunk_id` and `text` (aliases in `rag/config.py`); other fields are kept as metadata.

## Layout

| Path | Contents |
|---|---|
| `rag/` | data loading, embedding, FAISS index, retrieval and rerank, generation, judge, metrics |
| `scripts/` | `run_eval.py`, `smoke_test.py`, `build_questions.py`, `build_label_pools.py`, `ingest_labels.py`, `make_docs.py` |
| `data/` | `questions.jsonl` (golden set), `questions_pattern_gold.jsonl`, `labeling/` (labeler pools, prompt, replies), `dummy_*` stand-ins |
| `results/` | `full_run_1/`, `full_run_2/` (`per_question.jsonl` and `summary.json`) |
| `docs/` | `baseline_report_v2.docx`: flow, results, explanations, metric definitions |
| `tests/` | unit tests for metrics, the judge parser and the data loader |

## Known limitations

* Golden set mostly unverified (see above); 19 questions is small.
* The LLM judge is noisy: it flipped one verdict between two identical runs and mislabeled some answers, so judge-based rates
  are rough.
* Retrieval picks the wrong fiscal year of the right company often; a year filter and a BM25 or hybrid baseline are the
  next experiments.
"""
(ROOT / "README.md").write_text(r, encoding="utf-8")
print("wrote README.md and GOLDEN_SET.md")
