# Baseline summary: vector RAG on golden set v2

Vector RAG over 10-K filings of J&J, Apple and Microsoft (6 filings, 1,855 chunks, Mohini's fixed chunks with the full filing header). 39 hand-checked questions: 9 single-hop, 6 relation (2 hops), 12 relation with descriptive answers, 5 deep (3-5 hops), 4 cross-year, 3 cross-company.

**Pipeline:** embed the question, cosine search over all chunks, take the top k (5 or 10), optionally rerank the top 20 with a cross-encoder, then Gemini 3.5 Flash-Lite writes the answer and cites chunk ids. The same model judges the answer (correct / hallucination / missing). Four configurations: bge-small or DistilBERT, each with and without reranking, at k = 5 and 10.

## 1. Overall results

| Configuration | k | P@k | R@k | Hit@k | AllFacts | Correct | Halluc. | Missing | Unsupp. numbers | Citation acc. | Answer support |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | 0.215 | 0.457 | 0.74 | 0.49 | 59.0% | 0.0% | 41.0% | 0.0% | 83.3% | 73.1% |
| bge-small | 10 | 0.141 | 0.557 | 0.85 | 0.56 | 66.7% | 2.6% | 30.8% | 3.6% | 81.8% | 78.1% |
| bge-small + rerank | 5 | 0.241 | 0.514 | 0.79 | 0.51 | 56.4% | 2.6% | 41.0% | 3.7% | 90.5% | 82.5% |
| bge-small + rerank | 10 | 0.164 | 0.625 | 0.82 | 0.64 | 69.2% | 2.6% | 28.2% | 0.0% | 95.5% | 77.4% |
| DistilBERT | 5 | 0.169 | 0.397 | 0.67 | 0.36 | 48.7% | 0.0% | 51.3% | 0.0% | 100.0% | 85.4% |
| DistilBERT | 10 | 0.123 | 0.503 | 0.74 | 0.46 | 51.3% | 2.6% | 46.2% | 18.8% | 78.6% | 69.1% |
| DistilBERT + rerank | 5 | 0.231 | 0.489 | 0.72 | 0.54 | 59.0% | 2.6% | 38.5% | 3.6% | 85.7% | 80.0% |
| DistilBERT + rerank | 10 | 0.146 | 0.577 | 0.79 | 0.56 | 64.1% | 2.6% | 33.3% | 3.4% | 95.0% | 81.8% |

*Hit@k* = at least one gold chunk retrieved. *AllFacts* = every gold fact of the question is stated by a retrieved chunk (a missing hop fails it). Precision is low by design: a question has 1 to 7 gold chunks, so precision@10 cannot exceed about 0.3.

**Reading the table.** bge-small with reranking at k = 10 is best (69.2% correct, AllFacts 0.64). DistilBERT is weaker (51.3% at k = 10 without reranking) and reranking helps it more (to 64.1%). Hallucination is 0-3% everywhere; the dominant failure is a refusal (missing, 28-51%).

## 2. Results by question type (k = 10)

**Correct answers**

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 100% | 100% | 67% | 89% |
| Relation (2 hops) | 6 | 50% | 67% | 50% | 50% |
| Relation, descriptive | 12 | 92% | 83% | 75% | 83% |
| Deep (3-5 hops) | 5 | 40% | 40% | 40% | 40% |
| Cross-year | 4 | 25% | 50% | 0% | 50% |
| Cross-company | 3 | 0% | 0% | 0% | 0% |
| **ALL** | 39 | 67% | 69% | 51% | 64% |

**Every gold fact retrieved (AllFacts)**

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 100% | 89% | 56% | 78% |
| Relation (2 hops) | 6 | 33% | 50% | 17% | 17% |
| Relation, descriptive | 12 | 83% | 83% | 83% | 75% |
| Deep (3-5 hops) | 5 | 20% | 40% | 40% | 40% |
| Cross-year | 4 | 0% | 25% | 0% | 50% |
| Cross-company | 3 | 0% | 33% | 0% | 33% |
| **ALL** | 39 | 56% | 64% | 46% | 56% |

**Missing (refused or incomplete)**

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 0% | 0% | 33% | 11% |
| Relation (2 hops) | 6 | 50% | 33% | 50% | 50% |
| Relation, descriptive | 12 | 8% | 17% | 17% | 17% |
| Deep (3-5 hops) | 5 | 40% | 60% | 60% | 60% |
| Cross-year | 4 | 75% | 50% | 100% | 50% |
| Cross-company | 3 | 100% | 67% | 100% | 67% |
| **ALL** | 39 | 31% | 28% | 46% | 33% |

Full tables (precision, recall, hallucination, traceability columns, k = 5 and 10): `results_by_type.md` and `pivot_by_type.md`.

## 3. Error stages: where wrong answers start

Each wrong answer is tagged with the first stage that failed (graph, entity linking, retrieval, generation; rules in `README.md`). Vector RAG has no graph or linking step, so only the last two occur.

| Configuration | k | ok | retrieval | generation |
|---|---|---|---|---|
| bge-small | 5 | 23 | 16 | 0 |
| bge-small | 10 | 26 | 12 | 1 |
| bge-small + rerank | 5 | 22 | 17 | 0 |
| bge-small + rerank | 10 | 27 | 11 | 1 |
| DistilBERT | 5 | 19 | 20 | 0 |
| DistilBERT | 10 | 20 | 18 | 1 |
| DistilBERT + rerank | 5 | 23 | 16 | 0 |
| DistilBERT + rerank | 10 | 25 | 13 | 1 |

**Almost every wrong answer is a retrieval failure.** At k = 10, 11-18 questions per configuration lose at least one gold fact before the model sees it, and only 1 is a generation error. When a fact is missing, Gemini says it cannot answer, which is why "missing" is high and hallucination is low.

### What caused the retrieval failures (missing facts at k = 10)

| Cause | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|
| Right filing, wrong passage | 18 | 15 | 24 | 19 |
| Wrong fiscal year of the right company | 0 | 0 | 2 | 0 |
| Wrong company | 1 | 3 | 0 | 0 |

(Counts of missing gold facts. A fact counts as "right filing, wrong passage" when chunks from the filing that states it were retrieved but not the chunk that holds the fact.)

1. **The needed passage is not ranked in the top k, even inside the right filing.** This is the main cause (15-24 missing facts per configuration against 0-3 for the others). Examples: the Exhibit 21 row that gives Janssen Biotech's state (q11), the Shockwave acquisition and franchise passages (q28), the segment goodwill table for Activision (q29). The question words do not resemble the passage that holds the second or third fact, so similarity does not rank it high enough.
2. **Cross-company questions are swamped by one company.** For q38 (three companies) 9 of the 10 retrieved chunks were J&J, and for q39 (Apple vs J&J) all 10 were J&J (bge-small + rerank). One question vector sits near one company's text, so the other companies' facts never arrive. No configuration answers any cross-company question correctly.
3. **Cross-year questions fail although both years are retrieved.** For q33 (Apple headcount, FY2024 vs FY2025) the top 10 held 4 FY2024 and 6 FY2025 chunks (bge-small + rerank), yet neither headcount passage was among them. So the cause is again the passage, not year confusion. A wrong fiscal year of the right company is rare (2 facts, DistilBERT only).
4. **Multi-hop questions need every fact.** Among bge-small + rerank failures at k = 10, 6 of 11 questions were missing two or more facts; one missing hop is enough to fail the question.
5. **Generation errors are rare (1 per configuration at k = 10).** Example: q37 (R&D, Apple FY2025 vs Microsoft FY2026): both figures were retrieved and cited correctly ($34,550M and $35,562M), but the model named the wrong winner. The traceability checks pass on such an answer; only the judge catches it.

### Cross-year and cross-company: what goes wrong

These two types fail for different reasons. In both, retrieval does not pull the right passages; wrong-fiscal-year focus is not the main cause.

| | Cross-year (q33-q36) | Cross-company (q37-q39) |
|---|---|---|
| Correct answers (k = 10) | 0-50% | 0% in every configuration |
| Every gold fact retrieved (k = 10) | 0-50% | 0-33% |
| What was retrieved | chunks from **both** years (q33: 4 FY2024 + 6 FY2025, bge-small + rerank) | chunks from **one** company (q39: all 10 J&J; q38: 9 of 10 J&J) |
| Why it fails | the passage that holds the fact (for example the headcount sentence of each year) is not ranked in the top k | one question vector sits near one company's text, so the other companies' facts never reach Gemini |
| What the model does | cannot find the figure for one year, so it answers "missing" | cannot compare, so it refuses (or, rarely, compares wrongly) |

A wrong fiscal year of the right company is rare: 2 missing facts across all four configurations, DistilBERT only.

**What would fix them (not yet tested, except the filter):**
- **Cross-year:** retrieve per filing (one search per fiscal year), then merge, so each year's passage gets its own top-k.
- **Cross-company:** retrieve per company (one search per company), then merge.
- **A company and fiscal-year filter alone is not enough.** In the filter test (bge-small, k = 10) it left cross-year and cross-company at 0% of questions with every fact retrieved, because it still ran one pooled search over the allowed filings.
- **Graph retrieval** should help both by starting from several company and filing nodes at once; that is what the G-Reasoner comparison will show.

### Hardest and easiest questions (k = 10)

- **Wrong in all four configurations (9):** q11 (relation), q23 (relation_text), q28 (relation_deep), q29 (relation_deep), q33 (cross_year), q34 (cross_year), q37 (cross_company), q38 (cross_company), q39 (cross_company).
- **Right in all four (16):** q01, q03, q04, q06, q08, q09, q12, q14, q16, q18, q19, q20, q22, q25, q26, q32 (single-hop and descriptive questions whose answer sits in one passage).

## 4. Traceability (every number and answer traced to a cited chunk)

- Every answer cites chunk ids (citation rate 100%). The prompt asks for the chunk id after every number and the fiscal year of each number.
- **Unsupported numbers** (numbers found in none of the cited chunks): 0-4% in seven of the eight configurations; DistilBERT at k = 10 without reranking is the exception at 18.8%.
- **Citation accuracy** (cited chunk holds the number, in the right filing and year): 79-100%. It drops when the model also cites a chunk from the other year.
- **Answer support** (text answers: share of answer sentences whose content words appear in the cited chunks): 69-85%. This is a text-matching check, a rough guide and not exact.
- The rates rest on small counts (about 20-45 numbers and 18-30 claims per configuration), so treat them as indicative.

## 5. Caveats

- 39 questions; each question type has 3-12, so one question moves a rate by 8-33 points.
- The same Gemini model generates and judges (the team chose one model). At temperature 0 with a gold answer this is acceptable but can favor its own style.
- Retrieval is deterministic; answer and judge scores can shift slightly between runs.
- Gold chunks were pattern-matched and then checked by hand against the filings. Gold lists contain every chunk that states a fact, so recall is a stricter measure than AllFacts.

## 6. Side experiment (not part of the baseline)

A company + fiscal-year filter in front of the search (bge-small only, `experiments/`, results in `results/v2_filtered/` and `results/v2_comparison_plain_vs_filtered.md`) raised AllFacts@10 from 56% to 67% (64% to 74% with reranking) and correct answers from 67% to 74% (69% to 77%). It did not help cross-year or cross-company questions.

## 7. Files in this folder

| File | Contents |
|---|---|
| `summary.md`, `summary.json` | this summary; the overall numbers for code |
| `results_by_type.md`, `pivot_by_type.md` | all metrics by question type, k = 5 and 10 |
| `error_stages.md`, `error_cases.csv` | stage counts; every wrong answer with its stage and missing facts |
| `../v2_fixed_chunks/`, `../v2_distilbert/` | raw runs: every answer, retrieved chunks, verdict, traceability fields |
