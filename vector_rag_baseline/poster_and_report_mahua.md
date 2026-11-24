# Mahua: poster panel and report parts (vector RAG baseline)

All numbers come from `results/v2_all_baselines/summary.md` (golden set v2, 39 questions, fixed chunks, Gemini 3.5 Flash-Lite).

---

# PART A. POSTER PANEL: "Evaluation design and baseline results"

## Panel layout (top to bottom)

**Headline (one line):**
Vector retrieval fails on multi-hop and cross-filing questions, because it does not find the needed passage, not because the model makes things up.

**Box 1. Evaluation design**
- **Corpus:** 6 SEC 10-K filings (J&J, Apple, Microsoft; two fiscal years each), 1,855 chunks.
- **Golden set v2:** 39 hand-checked questions in 6 types: single-hop (9), relation 2-hop (6), relation with descriptive answer (12), deep 3-5 hops (5), cross-year (4), cross-company (3).
- **Gold labels:** each question has a gold answer, a list of gold facts, and the chunk that states each fact.
- **Baseline pipeline:** question → embed → cosine search over all chunks → top k (5 or 10) → optional cross-encoder rerank → Gemini 3.5 Flash-Lite answers and cites chunk ids → same model judges.
- **Configurations:** bge-small or DistilBERT, with or without rerank, k = 5 and 10 (8 runs).

**Box 2. What we measure**
- **Retrieval:** Precision@k, Recall@k, Hit@k, AllFacts@k (every gold fact retrieved).
- **Answer:** correct, hallucination, missing (judge).
- **Traceability:** unsupported-number rate, citation accuracy.
- **Failure stage:** first stage that failed (graph, entity linking, retrieval, generation).

**Box 3. Baseline numbers (table, k = 10)**

| Configuration | AllFacts | Correct | Halluc. | Missing |
|---|---|---|---|---|
| bge-small | 0.56 | 66.7% | 2.6% | 30.8% |
| bge-small + rerank | **0.64** | **69.2%** | 2.6% | 28.2% |
| DistilBERT | 0.46 | 51.3% | 2.6% | 46.2% |
| DistilBERT + rerank | 0.56 | 64.1% | 2.6% | 33.3% |

**Box 4. Chart: correct answers by question type** (bge-small + rerank, k = 10)
Single-hop 100% | Descriptive 83% | Relation 67% | Deep 40% | Cross-year 50% | Cross-company 0%

**Box 5. Where it fails (3 bullets)**
- 11-18 wrong answers per configuration are retrieval failures; only 1 is a generation error.
- Main cause: right filing, wrong passage (15-24 missing facts, against 0-3 for wrong company or wrong year).
- Cross-company: one company swamps the top 10 (q39: all 10 chunks from J&J). 0% correct in every configuration.

**Box 6. Takeaway / link to GNN**
Baseline to beat: 69% correct, AllFacts 0.64. The graph retriever should help where vector search is weakest: multi-hop (40%) and cross-company (0%).

**Speaker line (20 seconds):**
"We built 39 hand-checked financial questions and ran the strongest vector baseline. It answers 69% correctly. Almost every miss is retrieval: the right filing comes back, but not the right passage. That is the gap the graph retriever targets."

---

# PART B. REPORT SECTIONS

## B1. Experimental setup (vector RAG baseline)

**Corpus.** Six Form 10-K filings: Johnson & Johnson FY2024 and FY2025, Apple FY2024 and FY2025, Microsoft FY2025 and FY2026. Filings are split into 1,855 chunks (Items 1, 1A, 7, 8, Exhibit 21), each carrying the filing header (company, fiscal year, item).

**Golden set v2.** 39 questions with hand-checked answers. Types:

| Type | n | Description |
|---|---|---|
| single | 9 | one number in one passage |
| relation | 6 | two hops, short answer (for example subsidiary → state of incorporation) |
| relation_text | 12 | two hops, descriptive answer |
| relation_deep | 5 | three to five hops |
| cross_year | 4 | same company, two fiscal years |
| cross_company | 3 | two or three companies |

Each question stores `gold_answer`, `gold_facts` and `fact_chunks` (the chunks that state each fact). Gold chunks were pattern-matched, then checked by hand against the filings.

**Retriever.** Two encoders, L2-normalized: BAAI/bge-small-en-v1.5 (33M parameters, with the BGE query prefix) and multi-qa-distilbert-cos-v1 (66M). Search is exact cosine similarity over every chunk (FAISS IndexFlatIP, not approximate). Top k with k = 5 and 10. Optional reranking: the top 20 are rescored by the cross-encoder ms-marco-MiniLM-L-6-v2 and the best k kept.

**Generator and judge.** Gemini 3.5 Flash-Lite at temperature 0 for both (the team-agreed model). The generator answers only from the retrieved chunks, cites `[chunk_id]` after every number, and states the fiscal year of each number. The judge compares the answer with the gold answer and returns correct, hallucination or missing.

**Runs.** 2 encoders × {no rerank, rerank} × k ∈ {5, 10} = 8 configurations, 39 questions each, 312 question-runs.

## B2. Metric definitions

For a question with gold chunk set G, retrieved list R_k (top k), and gold facts F where fact f is stated by chunk set C_f:

- **Precision@k** = |R_k ∩ G| / k
- **Recall@k** = |R_k ∩ G| / |G|
- **Hit@k** = 1 if |R_k ∩ G| ≥ 1, else 0
- **AllFacts@k** = 1 if for every fact f in F, R_k ∩ C_f ≠ ∅, else 0
  (a single missing hop makes it 0)

Each is averaged over the questions.

**Answer metrics (judge).** Correct rate = share of answers judged correct; hallucination rate = share judged as stating something unsupported or false; missing rate = share where the answer is absent or incomplete. They sum to 100%.

**Traceability (string checks, no LLM).**
- **Unsupported-number rate** = (numbers in the answer found in none of the cited chunks) / (numbers in the answer). Numbers that appear in the question are ignored.
- **Citation accuracy** = (claims that pass) / (claims with a number). A claim is a sentence with a number. It passes if it cites at least one chunk, every number in it appears in one of its cited chunks, and every cited chunk is from the gold filing (right company and year).
- **Answer support** (text answers) = share of answer sentences whose content words are at least 70% covered by the cited chunks. Rough guide only.

**Latency.** Retrieve, rerank, generate and judge times per question are saved.

**Failure stage.** Each wrong answer receives the first stage that failed, in this order:
1. graph: the graph lacks the fact (not applicable to vector RAG)
2. entity_linking: question entities not linked to nodes (not applicable)
3. retrieval: AllFacts@k = 0, so some gold fact never reached the model
4. generation: all facts were retrieved but the answer is still wrong

## B3. Baseline results

Table 1. Overall (39 questions).

| Configuration | k | P@k | R@k | Hit@k | AllFacts | Correct | Halluc. | Missing | Unsupp. numbers | Citation acc. |
|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | 0.215 | 0.457 | 0.74 | 0.49 | 59.0% | 0.0% | 41.0% | 0.0% | 83.3% |
| bge-small | 10 | 0.141 | 0.557 | 0.85 | 0.56 | 66.7% | 2.6% | 30.8% | 3.6% | 81.8% |
| bge-small + rerank | 5 | 0.241 | 0.514 | 0.79 | 0.51 | 56.4% | 2.6% | 41.0% | 3.7% | 90.5% |
| bge-small + rerank | 10 | 0.164 | 0.625 | 0.82 | 0.64 | 69.2% | 2.6% | 28.2% | 0.0% | 95.5% |
| DistilBERT | 5 | 0.169 | 0.397 | 0.67 | 0.36 | 48.7% | 0.0% | 51.3% | 0.0% | 100.0% |
| DistilBERT | 10 | 0.123 | 0.503 | 0.74 | 0.46 | 51.3% | 2.6% | 46.2% | 18.8% | 78.6% |
| DistilBERT + rerank | 5 | 0.231 | 0.489 | 0.72 | 0.54 | 59.0% | 2.6% | 38.5% | 3.6% | 85.7% |
| DistilBERT + rerank | 10 | 0.146 | 0.577 | 0.79 | 0.56 | 64.1% | 2.6% | 33.3% | 3.4% | 95.0% |

Precision is low by design: a question has 1 to 7 gold chunks, so precision@10 cannot exceed about 0.3.

Table 2. Correct answers by question type (k = 10).

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 100% | 100% | 67% | 89% |
| Relation (2 hops) | 6 | 50% | 67% | 50% | 50% |
| Relation, descriptive | 12 | 92% | 83% | 75% | 83% |
| Deep (3-5 hops) | 5 | 40% | 40% | 40% | 40% |
| Cross-year | 4 | 25% | 50% | 0% | 50% |
| Cross-company | 3 | 0% | 0% | 0% | 0% |
| All | 39 | 67% | 69% | 51% | 64% |

**Findings.**
1. bge-small with reranking at k = 10 is the best baseline (69.2% correct, AllFacts 0.64).
2. DistilBERT is weaker, and reranking helps it more (51.3% to 64.1% at k = 10).
3. Going from k = 5 to k = 10 raises recall by 0.09-0.11 and correct answers by 3-13 points in every configuration. It lowers precision, which is expected.
4. Accuracy falls with the number of hops: single-hop 100%, descriptive 83-92%, relation 50-67%, deep 40%, cross-company 0%.
5. Hallucination is 0-2.6% everywhere. The dominant failure is a refusal: the model says it cannot answer when a fact is missing.
6. Traceability: unsupported numbers 0-4% in seven of eight configurations (DistilBERT at k = 10 without reranking: 18.8%); citation accuracy 79-100%. Rates rest on 20-45 numbers per configuration, so they are indicative.

Limits: 39 questions, 3-12 per type, so one question moves a rate by 8-33 points; the same model generates and judges.

## B4. Error findings

Table 3. Wrong answers by first failed stage (questions out of 39).

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

**Retrieval is the bottleneck.** Of the wrong answers at k = 10, all but one are retrieval failures. Graph and entity-linking stages are zero because vector RAG has neither; they are the stages to compare against G-Reasoner.

**Why retrieval fails (missing gold facts, k = 10).**

| Cause | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|
| Right filing, wrong passage | 18 | 15 | 24 | 19 |
| Wrong fiscal year, right company | 0 | 0 | 2 | 0 |
| Wrong company | 1 | 3 | 0 | 0 |

1. **Right filing, wrong passage (main cause).** The filing comes back but not the chunk with the fact. Example: the Exhibit 21 row giving Janssen Biotech's state of incorporation (q11). The second and third facts of a multi-hop question share few words with the question, so similarity does not rank them in the top k.
2. **Cross-company questions are swamped by one company.** For q39 (Apple vs J&J) all 10 retrieved chunks were J&J; for q38, 9 of 10. No configuration answers any cross-company question.
3. **Cross-year questions retrieve both years but not the needed passage.** For q33 (Apple headcount, FY2024 vs FY2025) the top 10 had 4 FY2024 and 6 FY2025 chunks, and neither headcount sentence. Wrong-year confusion is rare (2 facts).
4. **Multi-hop needs every fact.** Six of 11 failures for bge-small + rerank were missing two or more facts; one missing hop fails the question.
5. **Generation errors are rare (1 per configuration at k = 10).** Example: q37 retrieved and cited both R&D figures correctly ($34,550M and $35,562M) but named the wrong larger one. Traceability checks pass on this answer; only the judge catches it.

**Hardest questions** (wrong in all four configurations at k = 10): q11, q23, q28, q29, q33, q34, q37, q38, q39. **Easiest** (right in all four): 16 questions whose answer sits in one passage.

**Side experiment.** A company and fiscal-year filter before the search (bge-small) raised AllFacts@10 from 56% to 67% and correct answers from 67% to 74%. It did not help cross-year or cross-company, because it still runs one pooled search.

**Implication for the graph comparison.** Fixes the baseline cannot make by tuning: retrieving per company or per filing (cross-company, cross-year) and following relations between facts (deep chains). These are the cases where a graph retriever, which starts from several entity nodes at once and passes scores along edges, should gain. The same tagging rules and the same 39 questions will be used, so the stage counts in Table 3 compare directly.

---

Note: the request said "error findings from Notion". I have no access to the Notion page, so Part B4 is built from our own run results. If the Notion page has findings from Mohini or Rida, paste them and I will merge them.
