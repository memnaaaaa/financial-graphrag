# Old chunk header vs new chunk header (experiment E10)

## What changed (and what did not)

| | Old chunks (Oct 10) | New chunks (Mohini, Nov 18) |
|---|---|---|
| Chunk ids | 1,855 ids for the 6 filings | the same 1,855 ids |
| Chunk body (text after the header line) | - | identical in all 1,855 chunks |
| First line (header) | `Apple Inc. (AAPL) \| FY2025 Form 10-K \| Item 8. Financial Statements...` | `Apple Inc. (AAPL) \| Form 10-K annual report for fiscal year 2025 (FY2025), fiscal year ended September 27, 2025 \| Item 8. Financial Statements...` |
| Average size | 291 tokens (1,338 characters) | 309 tokens (1,411 characters) |
| Extra fields | - | `twin_chunk_id`, `twin_similarity` (750 chunks have a twin in the other year) |

So the only text change is a longer first line that spells out company, form, fiscal year and the fiscal year-end date. Boundaries and ids did not change, so every gold chunk id still holds.

## How we compared

- Old file reduced to the same 6 filings (1,855 chunks, `chunks_old_header_6filings.jsonl`).
- Same 39 golden-set questions, same encoders, same reranker, same k (5 and 10). Retrieval only (no Gemini), so the numbers are exact and repeatable.
- The new-header numbers are recomputed from the saved runs with the same code, so both sides use one definition.
- Code: `experiments/compare_headers.py`. Old run: `results/v2_old_header_retrieval/`.
- "Wrong-year chunks" = share of retrieved chunks from the right company but a fiscal year that holds no gold chunk of that question.

## Results

| Configuration | k | Header | P@k | R@k | Hit@k | AllFacts | Wrong-year chunks | Wrong-company chunks | Right-filing chunks |
|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | old | 0.185 | 0.408 | 0.67 | 0.46 | 39.5% | 0.0% | 60.5% |
| bge-small | 5 | new | 0.215 | 0.457 | 0.74 | 0.49 | 29.7% | 0.0% | 70.3% |
| bge-small | 10 | old | 0.136 | 0.549 | 0.85 | 0.59 | 38.5% | 0.3% | 61.3% |
| bge-small | 10 | new | 0.141 | 0.557 | 0.85 | 0.56 | 31.3% | 0.0% | 68.7% |
| bge-small+rerank | 5 | old | 0.179 | 0.417 | 0.69 | 0.41 | 39.5% | 0.0% | 60.5% |
| bge-small+rerank | 5 | new | 0.241 | 0.514 | 0.79 | 0.51 | 28.7% | 0.0% | 71.3% |
| bge-small+rerank | 10 | old | 0.128 | 0.538 | 0.79 | 0.59 | 41.3% | 0.0% | 58.7% |
| bge-small+rerank | 10 | new | 0.164 | 0.625 | 0.82 | 0.64 | 34.1% | 0.0% | 65.9% |
| distilbert | 5 | old | 0.149 | 0.355 | 0.59 | 0.36 | 45.1% | 0.0% | 54.9% |
| distilbert | 5 | new | 0.169 | 0.397 | 0.67 | 0.36 | 42.1% | 0.0% | 57.9% |
| distilbert | 10 | old | 0.108 | 0.475 | 0.74 | 0.46 | 42.3% | 0.3% | 57.4% |
| distilbert | 10 | new | 0.123 | 0.503 | 0.74 | 0.46 | 41.3% | 0.0% | 58.7% |
| distilbert+rerank | 5 | old | 0.179 | 0.422 | 0.69 | 0.38 | 39.0% | 0.0% | 61.0% |
| distilbert+rerank | 5 | new | 0.231 | 0.489 | 0.72 | 0.54 | 31.8% | 0.0% | 68.2% |
| distilbert+rerank | 10 | old | 0.121 | 0.520 | 0.77 | 0.51 | 41.3% | 0.3% | 58.5% |
| distilbert+rerank | 10 | new | 0.146 | 0.577 | 0.79 | 0.56 | 35.6% | 0.0% | 64.4% |

**Questions whose AllFacts changed (old -> new), k = 10**

| Configuration | gained (0 -> 1) | lost (1 -> 0) | net |
|---|---|---|---|
| bge-small | 1 (v2_q02) | 2 (v2_q12, v2_q30) | -1 |
| bge-small+rerank | 2 (v2_q35, v2_q37) | 0 () | +2 |
| distilbert | 2 (v2_q09, v2_q31) | 2 (v2_q02, v2_q17) | +0 |
| distilbert+rerank | 5 (v2_q05, v2_q12, v2_q30, v2_q35, v2_q36) | 3 (v2_q15, v2_q17, v2_q21) | +2 |

**AllFacts by question type, bge-small + rerank, k = 10 (old / new)**

| Type | n | old | new |
|---|---|---|---|
| single | 9 | 89% | 89% |
| relation | 6 | 50% | 50% |
| relation_text | 12 | 83% | 83% |
| relation_deep | 5 | 40% | 40% |
| cross_year | 4 | 0% | 25% |
| cross_company | 3 | 0% | 33% |

## Impact on the numbers

1. **More of the top k comes from the right filing.** Wrong-year chunks fall from 38-45% to 30-42% of the top k. For bge-small + rerank at k = 10: 41.3% to 34.1%. The year words in the header pull the question toward the right year.
2. **Recall and precision go up in every configuration.** Recall@10: bge-small 0.549 to 0.557, bge-small + rerank 0.538 to 0.625, DistilBERT 0.475 to 0.503, DistilBERT + rerank 0.520 to 0.577. The largest gain is bge-small + rerank at k = 5 (precision 0.179 to 0.241, recall 0.417 to 0.514, Hit 0.69 to 0.79).
3. **AllFacts (every gold fact retrieved) improves only where it matters.** bge-small + rerank at k = 10: 0.59 to 0.64 (+2 questions, no losses). DistilBERT + rerank at k = 10: 0.51 to 0.56. The gains are cross-year (0% to 25%) and cross-company (0% to 33%) with bge-small + rerank. Single-hop, relation, descriptive and deep are unchanged.
4. **The header is not a clean win.** bge-small without reranking at k = 10 goes from 0.59 to 0.56 (gains 1 question, loses 2), and plain DistilBERT is unchanged. Questions swap in and out because 18 more tokens per chunk shift the ranking slightly. With 39 questions, one question is 2.6 points, so differences of 1 to 2 questions are noise.
5. **Wrong-year confusion is reduced, not removed.** Thirty percent or more of retrieved chunks are still from the other year, because the other year's twin chunk reads almost the same (the twin cosine in Mohini's analysis was 0.95 or higher). The header helps the ranking but does not break the tie.

## Not yet measured

- Correct, hallucination and missing rates on the old chunks. These need Gemini, and the gcloud token expired. After `gcloud auth login`, run:
  `.venv/bin/python scripts/run_eval.py --chunks ../chunks_old_header_6filings.jsonl --questions data/questions_v2.jsonl --encoders bge-small distilbert --rerank --ks 5 10 --out results/v2_old_header`
