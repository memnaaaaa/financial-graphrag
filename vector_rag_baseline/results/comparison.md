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

- Old file reduced to the same 6 filings (1,855 chunks, `chunks_old_header_6filings.jsonl`, not stored in the repo: keep the 1,855 ids of the new file from the Oct 10 chunk file).
- Same 39 golden-set questions, same encoders, reranker, k (5 and 10), same Gemini 3.5 Flash-Lite generator and judge at temperature 0. The old-header run is `old_header_per_question.jsonl` (it has every retrieved chunk list, answer, verdict and failure stage); `old_header_summary.json` has the overall numbers.
- The new-header numbers are the saved Nov 19 runs (`results/v2_fixed_chunks`, `results/v2_distilbert`), recomputed with the same code.
- Code: `experiments/compare_headers.py` (retrieval) and `experiments/compare_headers_llm.py` (answers and grounding); both print the tables below.
- "Wrong-year chunks" = share of retrieved chunks from the right company but a fiscal year that holds no gold chunk of that question.

## Part 1. Retrieval (no LLM)

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

## Part 2. Answers, grounding and failure stages

| Configuration | k | Header | AllFacts | Correct | Halluc. | Missing | Unsupp. numbers | Citation acc. | Answer support | ok | retrieval fail | generation fail |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | old | 0.46 | 53.8% | 0.0% | 46.2% | 0.0% | 81.2% | 80.8% | 21 | 17 | 1 |
| bge-small | 5 | new | 0.49 | 59.0% | 0.0% | 41.0% | 0.0% | 83.3% | 73.1% | 23 | 16 | 0 |
| bge-small | 10 | old | 0.59 | 64.1% | 0.0% | 35.9% | 0.0% | 100.0% | 80.3% | 25 | 14 | 0 |
| bge-small | 10 | new | 0.56 | 66.7% | 2.6% | 30.8% | 3.6% | 81.8% | 78.1% | 26 | 12 | 1 |
| bge-small+rerank | 5 | old | 0.41 | 48.7% | 2.6% | 48.7% | 4.5% | 88.9% | 82.7% | 19 | 20 | 0 |
| bge-small+rerank | 5 | new | 0.51 | 56.4% | 2.6% | 41.0% | 3.7% | 90.5% | 82.5% | 22 | 17 | 0 |
| bge-small+rerank | 10 | old | 0.59 | 69.2% | 0.0% | 30.8% | 7.4% | 87.0% | 78.1% | 27 | 12 | 0 |
| bge-small+rerank | 10 | new | 0.64 | 69.2% | 2.6% | 28.2% | 0.0% | 95.5% | 77.4% | 27 | 11 | 1 |
| distilbert | 5 | old | 0.36 | 43.6% | 0.0% | 56.4% | 0.0% | 100.0% | 80.4% | 17 | 22 | 0 |
| distilbert | 5 | new | 0.36 | 48.7% | 0.0% | 51.3% | 0.0% | 100.0% | 85.4% | 19 | 20 | 0 |
| distilbert | 10 | old | 0.46 | 56.4% | 0.0% | 43.6% | 6.2% | 85.7% | 77.6% | 22 | 17 | 0 |
| distilbert | 10 | new | 0.46 | 51.3% | 2.6% | 46.2% | 18.8% | 78.6% | 69.1% | 20 | 18 | 1 |
| distilbert+rerank | 5 | old | 0.38 | 48.7% | 0.0% | 51.3% | 5.0% | 88.2% | 82.2% | 19 | 20 | 0 |
| distilbert+rerank | 5 | new | 0.54 | 59.0% | 2.6% | 38.5% | 3.6% | 85.7% | 80.0% | 23 | 16 | 0 |
| distilbert+rerank | 10 | old | 0.51 | 64.1% | 0.0% | 35.9% | 3.3% | 85.7% | 73.4% | 25 | 14 | 0 |
| distilbert+rerank | 10 | new | 0.56 | 64.1% | 2.6% | 33.3% | 3.4% | 95.0% | 81.8% | 25 | 13 | 1 |

**Correct answers by question type, k = 10 (old -> new)**

| Question type | n | bge-small | bge-small+rerank | distilbert | distilbert+rerank |
|---|---|---|---|---|---|
| single | 9 | 89% -> 100% | 100% -> 100% | 78% -> 67% | 78% -> 89% |
| relation | 6 | 50% -> 50% | 67% -> 67% | 33% -> 50% | 50% -> 50% |
| relation_text | 12 | 92% -> 92% | 92% -> 83% | 92% -> 75% | 92% -> 83% |
| relation_deep | 5 | 40% -> 40% | 40% -> 40% | 40% -> 40% | 40% -> 40% |
| cross_year | 4 | 25% -> 25% | 25% -> 50% | 0% -> 0% | 25% -> 50% |
| cross_company | 3 | 0% -> 0% | 0% -> 0% | 0% -> 0% | 33% -> 0% |

**Every gold fact retrieved (AllFacts) by question type, k = 10 (old -> new)**

| Question type | n | bge-small | bge-small+rerank | distilbert | distilbert+rerank |
|---|---|---|---|---|---|
| single | 9 | 89% -> 100% | 89% -> 89% | 56% -> 56% | 67% -> 78% |
| relation | 6 | 50% -> 33% | 50% -> 50% | 17% -> 17% | 17% -> 17% |
| relation_text | 12 | 83% -> 83% | 83% -> 83% | 92% -> 83% | 92% -> 75% |
| relation_deep | 5 | 40% -> 20% | 40% -> 40% | 20% -> 40% | 20% -> 40% |
| cross_year | 4 | 0% -> 0% | 0% -> 25% | 0% -> 0% | 0% -> 50% |
| cross_company | 3 | 0% -> 0% | 0% -> 33% | 0% -> 0% | 33% -> 33% |

**Questions whose verdict changed (old -> new), k = 10**

| Configuration | became correct | became wrong | net |
|---|---|---|---|
| bge-small | 3 (v2_q02, v2_q13, v2_q31) | 2 (v2_q15, v2_q30) | +1 |
| bge-small+rerank | 1 (v2_q35) | 1 (v2_q24) | +0 |
| distilbert | 1 (v2_q14) | 3 (v2_q02, v2_q17, v2_q27) | -2 |
| distilbert+rerank | 3 (v2_q05, v2_q14, v2_q35) | 3 (v2_q15, v2_q21, v2_q37) | +0 |

## Summary: what the new header changed

**Did better**
1. **Right filing, right year, more often.** Wrong-year chunks in the top k fall for every configuration (bge-small + rerank at k = 10: 41.3% to 34.1%; k = 5: 39.5% to 28.7%).
2. **Recall and precision up everywhere.** Recall@10: bge-small + rerank 0.538 to 0.625, DistilBERT + rerank 0.520 to 0.577, bge-small 0.549 to 0.557, DistilBERT 0.475 to 0.503. Largest gain: bge-small + rerank at k = 5 (precision 0.179 to 0.241, recall 0.417 to 0.514, Hit 0.69 to 0.79).
3. **Reranked configurations at k = 5 gain most in answers.** Correct: bge-small + rerank 48.7% to 56.4%, DistilBERT + rerank 48.7% to 59.0%, bge-small 53.8% to 59.0%, DistilBERT 43.6% to 48.7%. AllFacts for DistilBERT + rerank at k = 5: 0.38 to 0.54.
4. **Cross-year and cross-company retrieval.** With bge-small + rerank, every-fact retrieval goes 0% to 25% (cross-year) and 0% to 33% (cross-company); with DistilBERT + rerank, cross-year 0% to 50%. Correct cross-year answers double for both reranked configurations (25% to 50%).
5. **Single-hop.** bge-small 89% to 100% correct (AllFacts 89% to 100%); DistilBERT + rerank 78% to 89%.
6. **Retrieval-stage failures drop by 1 to 4 questions** in 7 of 8 configurations (for example DistilBERT + rerank, k = 5: 20 to 16; bge-small + rerank, k = 5: 20 to 17).

**No change or worse**
1. **At k = 10 the answer-level gain is small.** Correct is identical for bge-small + rerank (69.2% both) and DistilBERT + rerank (64.1% both); bge-small gains 2.6 points. Plain DistilBERT is worse (56.4% to 51.3%; descriptive 92% to 75%).
2. **Descriptive (relation_text) questions do not benefit.** Correct: 92% to 92% (bge-small), 92% to 83% (bge-small + rerank), 92% to 75% (DistilBERT). The longer header adds words that every chunk of a filing shares, so it helps pick the filing, not the passage inside it.
3. **Deep (3 to 5 hops) and relation (2 hops) are unchanged** (deep 40% in all configurations; relation 50% to 50%, 67% to 67%).
4. **Cross-company answers are still 0% for 3 of 4 configurations** (the one old 33% for DistilBERT + rerank became 0%, one question, q37, now a reasoning error after both figures were retrieved).
5. **Hallucination went from 0.0 to 2.6% (1 question) in 5 of 8 configurations**, and plain DistilBERT at k = 10 has 18.8% unsupported numbers (old: 6.2%). Each is one or two answers; treat as noise.
6. **Plain bge-small at k = 10: AllFacts 0.59 to 0.56** (gains q02, loses q12 and q30), though correct still rises (64.1% to 66.7%).

**Reading the result.** The header does what it was meant to do: it moves retrieval toward the right fiscal year, which shows up as higher recall, more right-filing chunks and fewer retrieval-stage failures, mostly with reranking and at k = 5. It does not fix the main failure of the baseline, right filing but wrong passage, so correct answers at k = 10 barely move, and multi-hop and descriptive questions are unchanged. With 39 questions, one question is 2.6 points: differences of 1 to 2 questions (for example the plain DistilBERT drop) are within run-to-run noise. Treat the retrieval gains (recall, wrong-year share) as the solid result and the answer-level changes as indicative.

**Best configuration is the same under both headers:** bge-small + rerank at k = 10 (69.2% correct); under the new header it has the higher AllFacts (0.64 vs 0.59), fewer unsupported numbers (0.0% vs 7.4%) and higher citation accuracy (95.5% vs 87.0%).
