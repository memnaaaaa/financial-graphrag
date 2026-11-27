# Vector-RAG baseline for multi-hop financial QA

Baseline retrieval-augmented generation over SEC 10-K filings (J&J, Apple, Microsoft; 6 filings), built to compare against a
GNN retriever (G-Reasoner) and a Personalized PageRank walk on the same filings. This README is maintained by hand
(`scripts/make_docs.py` no longer overwrites it).

**Status (Nov 25).** Baseline rerun done on Mohini's fixed chunks (1,855 chunks, 6 filings) with `gemini-3.5-flash-lite` as generator and judge, on golden set v2 (39 questions, hand-checked): bge-small and DistilBERT, with and without reranking, k = 5 and 10. The grounding measures (unsupported numbers, citation accuracy, answer support) and the failure-stage rules are in. Best baseline: bge-small + rerank at k = 10, 69% correct, AllFacts 0.64. Retrieval is the bottleneck: nearly every wrong answer is a retrieval failure. Start with `results/v2_all_baselines/summary.md` (setup, tables, error stages, causes). Per-question data (question, gold, retrieved chunk ids, answer, verdict, failure stage) is in `results/v2_all_baselines/per_question_all.csv` and `.jsonl`.

## Pipeline

```
chunks.jsonl (6 filings) -> embed (bge-small) -> FAISS IndexFlatIP -> dense top-k (k = 5, 10)
   -> optional cross-encoder rerank of the top 20 -> generate with chunk-id citations (Gemini 3.5 Flash-Lite, T=0)
   -> judge (rag/judge.py, same Gemini model, T=0) + grounding checks (rag/metrics.py) -> failure stage (rag/error_stage.py)
```

| Component | Choice |
|---|---|
| Embedding | `BAAI/bge-small-en-v1.5` (33M); `multi-qa-distilbert-cos-v1` (66M) is still available with `--encoders distilbert` |
| Index | FAISS `IndexFlatIP`, L2-normalized vectors (exact cosine search); rebuilt automatically when the chunk file changes |
| Rerank | `cross-encoder/ms-marco-MiniLM-L-6-v2` over the top 20 (optional) |
| Generator and judge | `gemini-3.5-flash-lite`, temperature 0, set once in `rag/config.py` (`AGREED_GEMINI`); override with `GEMINI_MODEL` / `JUDGE_MODEL` |
| Judge | unchanged: `rag/judge.py` labels each answer correct / hallucination / missing against the gold answer |

## Golden set v2 (`data/questions_v2.jsonl`, also in `seed_question_v2/`)

39 questions on J&J, Apple and Microsoft, all `gold_source` = "hand-checked":

| Type | n | What it tests |
|---|---|---|
| single | 9 | one figure in one filing |
| relation | 6 | 2-hop chain, e.g. Genmab -> DARZALEX -> Innovative Medicine -> segment sales |
| relation_text | 12 | 2-3 hop chain with a descriptive answer |
| relation_deep | 5 | 3-5 hop chains |
| cross_year | 4 | same company, two filings |
| cross_company | 3 | two or three companies |

Each question has `gold_chunk_ids` (every chunk that states any needed fact), `gold_facts` (the facts the answer needs) and
`fact_chunks` (the chunks that state each fact), which makes the retrieval stage checkable fact by fact. `answer_kind` is numeric or text.

## Metrics

| Metric | Definition |
|---|---|
| P@k, R@k, Hit@k | gold chunks in the top-k over k, over all gold chunks, and at least one found |
| **AllFacts@k** | share of questions where **every** gold fact is stated by a retrieved chunk (a missing hop fails it) |
| Judge rates | correct / hallucination / missing share of answers (`rag/judge.py`) |
| **Unsupported-number rate** | numbers in an answer that appear in none of the chunks it cites, over all numbers in answers. Rounding and thousand/million rescaling are allowed (`$416.2 billion` vs `416,161`); years and numbers already in the question are ignored |
| **Citation accuracy** | an answer sentence with a number is a claim; correct if it cites a chunk, every number in it is in a chunk it cites, and each cited chunk is from the right filing (company and fiscal year) |
| Latency | retrieve + rerank + generate (judge not counted), mean and p95 |

The generator prompt asks for `[chunk_id]` after every number and the fiscal year of each number; `rag/metrics.py` does the checks (no LLM).

## Failure-stage rules

Every wrong answer (judge says hallucination, missing or invalid) gets **one** tag: the first stage that failed, checked in this
order. `rag/error_stage.py` implements it and `run_eval.py` writes it as `error_stage`. The vector-RAG baseline has no graph and
no linking step, so only `retrieval` and `generation` occur for it (a wrong fiscal year counts as `retrieval`).

| # | Stage | Rule: it failed if... | Example (real cases from `results/v2_fixed_chunks`, k = 10, unless noted) |
|---|---|---|---|
| 1 | **graph** | a gold fact has no node or edge in the graph: no Value node whose source is one of `fact_chunks[fact]`, or the relation edge is missing | not applicable to vector RAG. Would be, for q10 (Genmab -> DARZALEX), a graph with no `licensed_from` edge from DARZALEX to Genmab, so no path to the segment exists |
| 2 | **entity_linking** | an entity named in the question (company, fiscal year, product, subsidiary) is linked to the wrong node or to none; compare linked nodes with the question's `companies` and `filings` | not applicable to vector RAG. Would be, for q04 "Microsoft's total revenue in fiscal 2026", the question linked to the FY2025 filing node |
| 3 | **retrieval** | graph and linking are fine, but at least one gold fact has none of its `fact_chunks` in the evidence given to the generator (`metrics.facts_found`: `all_facts` = 0). The `missing_facts` list names the lost hop | **real, q13** (Azure -> Intelligent Cloud revenue, bge-small + rerank, k = 10): the top-10 had neither the segment description (`m_ic_def`) nor the segment revenue table (`m_ic26`), only a total-revenue chunk. `missing_facts = [m_ic_def, m_ic26]`; the model could not give the segment revenue |
| 4 | **generation** | every gold fact is in the evidence, but the judge does not say correct. Subtypes in `error_stage.generation_subtype`: refused or incomplete, unsupported number, wrong citation, wrong value or reasoning | **real, q37** (R&D, Apple FY2025 vs Microsoft FY2026, bge-small + rerank, k = 10): both figures were retrieved and cited correctly ($34,550M and $35,562M, 0 unsupported numbers), yet the answer says Apple spent more. The judge marks it hallucination. The grounding checks pass here; only the judge catches a reasoning error |

A correct answer is tagged `ok` even if a fact was missed from the evidence (the model may have known it); those cases are listed
separately in the report as possible memory leakage.

## Results (bge-small and DistilBERT, with and without reranking, fixed chunks, golden set v2, 39 questions)

Runs: `results/v2_fixed_chunks/` (bge-small) and `results/v2_distilbert/`; combined table in `results/v2_all_baselines/results_by_type.md` (pivots in `pivot_by_type.md`). Generator and judge: `gemini-3.5-flash-lite`, T = 0.

| Config | k | Question type | n | P@k | R@k | Hit@k | AllFacts@k | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. | Answer support |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | single | 9 | 0.244 | 0.339 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 88% of 8 |
| bge-small | 5 | relation | 6 | 0.233 | 0.417 | 0.83 | 0.33 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 67% of 6 |
| bge-small | 5 | relation_text | 12 | 0.233 | 0.722 | 0.75 | 0.75 | 83% | 0% | 17% | 0% of 4 | 25% of 4 | 78% of 27 |
| bge-small | 5 | relation_deep | 5 | 0.240 | 0.417 | 0.80 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 67% of 6 |
| bge-small | 5 | cross_year | 4 | 0.100 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 0% of 3 | 100% of 2 | 67% of 3 |
| bge-small | 5 | cross_company | 3 | 0.133 | 0.178 | 0.67 | 0.00 | 0% | 0% | 100% | n/a | n/a | 0% of 2 |
| bge-small | 5 | **ALL** | 39 | 0.215 | 0.457 | 0.74 | 0.49 | 59% | 0% | 41% | 0% of 20 | 83% of 18 | 73% of 52 |
| bge-small | 10 | single | 9 | 0.200 | 0.512 | 1.00 | 1.00 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 78% of 9 |
| bge-small | 10 | relation | 6 | 0.167 | 0.542 | 1.00 | 0.33 | 50% | 0% | 50% | 0% of 4 | 100% of 4 | 83% of 12 |
| bge-small | 10 | relation_text | 12 | 0.125 | 0.806 | 0.83 | 0.83 | 92% | 0% | 8% | 0% of 4 | 0% of 3 | 83% of 30 |
| bge-small | 10 | relation_deep | 5 | 0.160 | 0.533 | 0.80 | 0.20 | 40% | 20% | 40% | 0% of 6 | 100% of 4 | 64% of 11 |
| bge-small | 10 | cross_year | 4 | 0.050 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 20% of 5 | 50% of 2 | 50% of 2 |
| bge-small | 10 | cross_company | 3 | 0.067 | 0.178 | 0.67 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| bge-small | 10 | **ALL** | 39 | 0.141 | 0.557 | 0.85 | 0.56 | 67% | 3% | 31% | 4% of 28 | 82% of 22 | 78% of 64 |
| bge-small+rerank | 5 | single | 9 | 0.333 | 0.460 | 0.89 | 0.89 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 89% of 9 |
| bge-small+rerank | 5 | relation | 6 | 0.167 | 0.361 | 0.67 | 0.17 | 17% | 0% | 83% | 0% of 1 | 100% of 1 | 75% of 4 |
| bge-small+rerank | 5 | relation_text | 12 | 0.233 | 0.778 | 0.83 | 0.75 | 75% | 0% | 25% | 0% of 5 | 67% of 3 | 87% of 31 |
| bge-small+rerank | 5 | relation_deep | 5 | 0.320 | 0.479 | 1.00 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 80% of 5 |
| bge-small+rerank | 5 | cross_year | 4 | 0.150 | 0.375 | 0.50 | 0.25 | 50% | 0% | 50% | 0% of 4 | 100% of 3 | 100% of 3 |
| bge-small+rerank | 5 | cross_company | 3 | 0.133 | 0.178 | 0.67 | 0.00 | 0% | 33% | 67% | 20% of 5 | 67% of 3 | 40% of 5 |
| bge-small+rerank | 5 | **ALL** | 39 | 0.241 | 0.514 | 0.79 | 0.51 | 56% | 3% | 41% | 4% of 27 | 90% of 21 | 82% of 57 |
| bge-small+rerank | 10 | single | 9 | 0.256 | 0.650 | 0.89 | 0.89 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 89% of 9 |
| bge-small+rerank | 10 | relation | 6 | 0.167 | 0.583 | 0.83 | 0.50 | 67% | 0% | 33% | 0% of 4 | 100% of 4 | 78% of 9 |
| bge-small+rerank | 10 | relation_text | 12 | 0.125 | 0.806 | 0.83 | 0.83 | 83% | 0% | 17% | 0% of 3 | 50% of 2 | 77% of 30 |
| bge-small+rerank | 10 | relation_deep | 5 | 0.200 | 0.629 | 1.00 | 0.40 | 40% | 0% | 60% | 0% of 6 | 100% of 4 | 60% of 10 |
| bge-small+rerank | 10 | cross_year | 4 | 0.075 | 0.375 | 0.50 | 0.25 | 50% | 0% | 50% | 0% of 4 | 100% of 2 | 100% of 2 |
| bge-small+rerank | 10 | cross_company | 3 | 0.100 | 0.244 | 0.67 | 0.33 | 0% | 33% | 67% | 0% of 2 | 100% of 1 | 100% of 2 |
| bge-small+rerank | 10 | **ALL** | 39 | 0.164 | 0.625 | 0.82 | 0.64 | 69% | 3% | 28% | 0% of 28 | 95% of 22 | 77% of 62 |
| distilbert | 5 | single | 9 | 0.133 | 0.207 | 0.56 | 0.56 | 67% | 0% | 33% | 0% of 6 | 100% of 6 | 100% of 6 |
| distilbert | 5 | relation | 6 | 0.133 | 0.278 | 0.67 | 0.00 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 90% of 10 |
| distilbert | 5 | relation_text | 12 | 0.250 | 0.778 | 0.83 | 0.75 | 75% | 0% | 25% | 0% of 4 | 100% of 2 | 85% of 20 |
| distilbert | 5 | relation_deep | 5 | 0.240 | 0.324 | 1.00 | 0.00 | 0% | 0% | 100% | 0% of 1 | 100% of 1 | 50% of 2 |
| distilbert | 5 | cross_year | 4 | 0.100 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 0% of 3 | 100% of 2 | 67% of 3 |
| distilbert | 5 | cross_company | 3 | 0.000 | 0.000 | 0.00 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| distilbert | 5 | **ALL** | 39 | 0.169 | 0.397 | 0.67 | 0.36 | 49% | 0% | 51% | 0% of 16 | 100% of 13 | 85% of 41 |
| distilbert | 10 | single | 9 | 0.111 | 0.304 | 0.56 | 0.56 | 67% | 0% | 33% | 0% of 6 | 100% of 6 | 83% of 6 |
| distilbert | 10 | relation | 6 | 0.100 | 0.361 | 0.83 | 0.17 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 64% of 11 |
| distilbert | 10 | relation_text | 12 | 0.142 | 0.833 | 0.83 | 0.83 | 75% | 8% | 17% | 0% of 2 | 50% of 2 | 77% of 26 |
| distilbert | 10 | relation_deep | 5 | 0.220 | 0.602 | 1.00 | 0.40 | 40% | 0% | 60% | 60% of 5 | 33% of 3 | 45% of 11 |
| distilbert | 10 | cross_year | 4 | 0.075 | 0.375 | 0.75 | 0.00 | 0% | 0% | 100% | 0% of 1 | 100% of 1 | 100% of 1 |
| distilbert | 10 | cross_company | 3 | 0.033 | 0.067 | 0.33 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| distilbert | 10 | **ALL** | 39 | 0.123 | 0.503 | 0.74 | 0.46 | 51% | 3% | 46% | 19% of 16 | 79% of 14 | 69% of 55 |
| distilbert+rerank | 5 | single | 9 | 0.222 | 0.280 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 75% of 8 |
| distilbert+rerank | 5 | relation | 6 | 0.133 | 0.306 | 0.50 | 0.17 | 17% | 17% | 67% | 0% of 2 | 100% of 2 | 100% of 4 |
| distilbert+rerank | 5 | relation_text | 12 | 0.267 | 0.806 | 0.83 | 0.75 | 83% | 0% | 17% | 0% of 5 | 33% of 3 | 76% of 29 |
| distilbert+rerank | 5 | relation_deep | 5 | 0.360 | 0.529 | 1.00 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 100% of 3 |
| distilbert+rerank | 5 | cross_year | 4 | 0.200 | 0.500 | 0.50 | 0.50 | 50% | 0% | 50% | 0% of 5 | 100% of 4 | 100% of 4 |
| distilbert+rerank | 5 | cross_company | 3 | 0.133 | 0.133 | 0.33 | 0.33 | 33% | 0% | 67% | 20% of 5 | 50% of 2 | 50% of 2 |
| distilbert+rerank | 5 | **ALL** | 39 | 0.231 | 0.489 | 0.72 | 0.54 | 59% | 3% | 38% | 4% of 28 | 86% of 21 | 80% of 50 |
| distilbert+rerank | 10 | single | 9 | 0.156 | 0.391 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 88% of 8 |
| distilbert+rerank | 10 | relation | 6 | 0.117 | 0.444 | 0.83 | 0.17 | 50% | 0% | 50% | 0% of 3 | 100% of 3 | 80% of 5 |
| distilbert+rerank | 10 | relation_text | 12 | 0.133 | 0.806 | 0.83 | 0.75 | 83% | 0% | 17% | 0% of 3 | 100% of 2 | 83% of 29 |
| distilbert+rerank | 10 | relation_deep | 5 | 0.240 | 0.707 | 1.00 | 0.40 | 40% | 0% | 60% | 0% of 6 | 100% of 4 | 80% of 10 |
| distilbert+rerank | 10 | cross_year | 4 | 0.125 | 0.625 | 0.75 | 0.50 | 50% | 0% | 50% | 0% of 4 | 100% of 2 | 100% of 2 |
| distilbert+rerank | 10 | cross_company | 3 | 0.100 | 0.200 | 0.33 | 0.33 | 0% | 33% | 67% | 20% of 5 | 0% of 1 | 0% of 1 |
| distilbert+rerank | 10 | **ALL** | 39 | 0.146 | 0.577 | 0.79 | 0.56 | 64% | 3% | 33% | 3% of 29 | 95% of 20 | 82% of 55 |

Traceability columns: **Unsupported numbers** = numbers in answers found in none of the cited chunks; **Citation acc.** = numeric claims whose cited chunks hold the number, in the right filing and year; **Answer support** = answer sentences whose content words (70%+) appear in the cited chunks (a text-matching check for answers that are text, not numbers). "X% of N" gives the count behind each rate, which is small.

## Rerun

Run everything from the folder that holds `rag/`, `scripts/` and `data/` (`vector_rag_baseline/` in the repo). `data/chunks.jsonl` is not stored in git: copy Mohini's fixed chunk file there (1,855 chunks for the 6 filings; the file may also hold other companies, `--tickers` keeps the three).

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # once (requirements.txt is also at the repo root)
cp .env.example .env                                                # Gemini access, see "Gemini access" below
# 1. baseline: retrieval metrics + answers + judge + grounding checks + failure stage
.venv/bin/python scripts/run_eval.py --chunks data/chunks.jsonl --questions data/questions_v2.jsonl \
    --tickers JNJ AAPL MSFT --encoders bge-small --rerank --out results/v2_fixed_chunks
.venv/bin/python scripts/run_eval.py --chunks data/chunks.jsonl --questions data/questions_v2.jsonl \
    --tickers JNJ AAPL MSFT --encoders distilbert --rerank --out results/v2_distilbert
# 2. one table by question type (several runs can be combined)
.venv/bin/python scripts/results_by_type.py results/v2_fixed_chunks results/v2_distilbert \
    --questions data/questions_v2.jsonl --chunks data/chunks.jsonl --out results/v2_all_baselines
# 3. one file with every question, retrieved chunks, answer, verdict and failure stage (for comparing systems)
.venv/bin/python scripts/export_per_question.py results/v2_fixed_chunks results/v2_distilbert
# retrieval-only check (no Gemini needed): add --no-llm to step 1
# unit tests
.venv/bin/python -m pytest -q tests
```

`--rerank` runs each encoder with and without reranking; `--ks` defaults to 5 and 10. To rebuild the golden set and `golden_v2_review.md` after editing `scripts/build_questions_v2.py`: `.venv/bin/python scripts/build_questions_v2.py`.

### Gemini access

`gemini-3.5-flash-lite` is served only from the `global` location (404 elsewhere). Either use a Google AI Studio key (`GEMINI_API_KEY` in `.env`, no GCP needed) or Vertex AI (`GOOGLE_CLOUD_PROJECT` in `.env`, then `gcloud auth login`; the location defaults to `global`). Without any Gemini access, `--no-llm` still gives all retrieval metrics.

## Side experiments (do not change the baseline)

| Experiment | Files | Result |
|---|---|---|
| Old short chunk header vs the new full header (same 1,855 ids, same bodies; only the first line differs) | `experiments/compare_headers.py`, `experiments/compare_headers_llm.py`, `results/v2_old_vs_new_header/` (`comparison.md` and the old-header run) | wrong-year chunks in the top 10 fall from about 41% to 34% (bge-small + rerank); recall@10 0.54 to 0.63; correct answers +5 to +10 points at k = 5, about unchanged at k = 10; helps cross-year, cross-company and single-hop, not descriptive or deep questions |

## Layout

| Path | Contents |
|---|---|
| `rag/` | `config.py` (models, locations), `embed.py`, `index.py`, `retrieve.py`, `generate.py`, `judge.py`, `metrics.py` (retrieval, fact-level and grounding metrics incl. `answer_support`), `error_stage.py`, `llm.py` |
| `scripts/` | `run_eval.py`, `results_by_type.py`, `export_per_question.py`, `build_questions_v2.py`; older helpers (`build_questions.py`, `build_label_pools.py`, `ingest_labels.py`, `chunk_10k_pdf.py`, `grep_chunks.py`, `probe.py`, `smoke_test.py`) are from the first version |
| `data/` | `questions_v2.jsonl` (fields: qid, type, hops, companies, filings, question, gold_chunk_ids, gold_answer, gold_facts, fact_chunks, answer_kind, relation_chain), `golden_v2_review.md`; `chunks.jsonl` is not stored here |
| `experiments/` | one side experiments above |
| `docs/` | `ERROR_STAGES.md`, method and report drafts, contribution log entries |
| `results/` | `v2_fixed_chunks/` (bge-small) and `v2_distilbert/` (raw runs: `per_question.jsonl`, `summary.json`), `v2_all_baselines/` (`summary.md`, `results_by_type.md`, `pivot_by_type.md`, `error_stages.md`, `error_cases.csv`, `per_question_all.*`), `v2_filtered/`, `v2_old_vs_new_header/` (old vs new chunk header comparison) and `v2_comparison_plain_vs_filtered.md` |
| `tests/` | `test_units.py` (10 tests: grounding checks, error stage, fact-level retrieval, answer support) |
