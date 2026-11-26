# Answer step with citations and trace view

Turns any retriever's output into a cited answer, scores it, and traces each number back to
its filing. Every system gets the same model (`gemini-3.5-flash-lite`, temperature 0), the same answer rules
and the same scoring, so differences between systems come from retrieval.

```
retrieved chunks (top k)  ─┐
retrieved entities, Values ┼─> prompt: Facts (subgraph) + Values (with ids) + Passages ─> Gemini ─> answer with [chunk ids] and [V-… ids]
                           │                                                                     │
                           └────────────────────────────────────────── scoring <─────────────────┘
        judge (correct / hallucination / missing), unsupported numbers, citation accuracy, Value-cite check, error stage
```

## What goes to Gemini

- **Passages:** the retriever's top-k chunks, each labelled with its chunk id (as in the vector baseline).
- **Values** (graph retrievers only): the retrieved Value nodes, one line each with a short id, e.g.
  `[V-JNJ-0095] DARZALEX (JNJ) revenue FY2025 = $14,351 million (printed as "14,351" in JNJ FY2025 10-K,
  Item 8, passage JNJ_FY2025_ITEM8_0111)`. Ids are `V-<ticker>-<nnnn>`, numbered by node name within each
  company, so they are stable for a given graph; they can never be mistaken for a chunk id.
- **Facts** (graph retrievers only): the connected subgraph, at most 40 triples: every edge between two
  retrieved nodes (entities, Values, the question's start nodes), plus one 2-hop path for each pair of
  retrieved nodes that are not linked directly. `is_mentioned_in`, `of_metric` and `for_period` are left
  out (the passages and Value lines already carry them), and hubs (> 60 links) are never used as connectors.
- **Rules:** the vector baseline's system prompt (`vector_rag_baseline/rag/generate.py`) unchanged, plus one
  sentence: cite a Value id for a number taken from a Value, a passage id for one taken from a passage. With
  no graph nodes in the input, the prompt is exactly the baseline's.

## Scoring (no LLM except the judge)

| Measure | How |
| --- | --- |
| Correct / hallucination / missing | `vector_rag_baseline/rag/judge.py`, unchanged |
| Unsupported numbers, citation accuracy | `rag/metrics.py`, unchanged; a cited Value counts as citing the passage its number is printed in |
| Value-cite accuracy | new: a sentence that cites a Value must state that Value's number (any scale: 14,351 million = 14.4 billion) |
| P@k, R@k, Hit@k | on the ranked chunks |
| All facts given | every gold fact appears in a chunk the model saw (retrieved chunks + the source passages of the Values given) |
| Error stage | `rag/error_stage.py`; entity linking fails when a graph retriever found no start node. The graph stage (fact missing from the graph) is tagged by hand |

All facts and the error stage need `fact_chunks` in `questions_v2.jsonl`; without it they fall back to "a
gold chunk was seen" (`fact_check: gold_chunk_hit` in the results), like `run_eval.py`.

## Run

From the repo root. Needs only `numpy` and `GEMINI_API_KEY` in the repo-root `.env` (same key as
`extract_relations_llm.py`). Every Gemini reply is cached in `answer_step/cache/` (git-ignored), so a rerun
or a stop at the daily limit costs nothing: run the same command again.

```bash
# vector RAG (E1 retrievals, bge-small + rerank, k = 10): also the sanity check against Mahua's own answers
python answer_step/answer.py --system vector_rag --config bge-small+rerank \
    --retrievals vector_rag_baseline/results/v2_all_baselines/per_question_all.jsonl

# graph retrievers: any per_question.jsonl with retrieved / top_entities / top_attributes / start_nodes
python answer_step/answer.py --system g_reasoner_zero_shot --config g-reasoner \
    --retrievals G-reasoner/results/zero_shot_fin10k_v1/per_question.jsonl
python answer_step/answer.py --system g_reasoner_finetuned --config g-reasoner-ft \
    --retrievals G-reasoner/results/finetuned_fin10k_v1/per_question.jsonl
python answer_step/answer.py --system ppr --config ppr \
    --retrievals G-reasoner/results/ppr_fin10k_v1/per_question.jsonl

python answer_step/compare.py                                   # table of all runs -> results/comparison.md
python answer_step/trace.py answer_step/results/g_reasoner_finetuned_k10/per_question.jsonl v2_q11
```

Options: `--dry-run` (no Gemini calls, fake answers: checks the pipeline only), `--types relation relation_deep`
or `--only v2_q11` (a subset), `--no-graph-context` (chunks only), `--values rule` (Values chosen by rule), `--rpm` (requests per minute, default 10).
One run is 39 answers + 39 judge calls.

## Two improvements (Nov 25)

- **Hybrid retrieval** (`make_hybrid.py`): vector RAG and a graph retriever fail on different questions, so
  their chunks are merged (interleaved, about 5 each, 10 in total); the entities, Values and start nodes come
  from the graph retriever. Every needed fact is in the 10 chunks for 29 of 39 questions with fine-tuned
  G-reasoner, against 25 for vector RAG alone and 19 for the graph alone.
- **Values chosen by rule** (`answer.py --values rule`): instead of the retriever's top Values (often
  unrelated, e.g. FY2023 cost of sales for a revenue question), Gemini gets the Values of the linked
  companies, segments and products for the linked metric and fiscal years (e.g. v2_q37: Apple FY2025 and
  Microsoft FY2025/FY2026 R&D). Questions that name no metric keep the retriever's Values.

```bash
python answer_step/make_hybrid.py --graph G-reasoner/results/finetuned_fin10k_v1/per_question.jsonl --name hybrid_finetuned
python answer_step/answer.py --system hybrid_finetuned_rule --retrievals answer_step/retrievals/hybrid_finetuned.jsonl --values rule
```

## Results (Nov 25, golden set v2, k = 10)

All four systems answered with the same model, prompt rules and scoring (`results/comparison.md`).
Error stages use the golden set's `fact_chunks` (every gold fact checked).

| System | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. | Value-cite acc. | Wrong: retrieval / generation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vector RAG (bge-small + rerank) | 69% | 0% | 31% | 23% | 86% | - | 11 / 1 |
| G-reasoner zero-shot | 15% | 0% | 85% | 0% | 100% | 100% (1 cite) | 31 / 2 |
| G-reasoner fine-tuned | 51% | 3% | 46% | 8% | 84% | - (no cites) | 18 / 1 |
| Personalized PageRank | 51% | 3% | 46% | 6% | 92% | 100% (17 cites) | 19 / 0 |
| G-reasoner fine-tuned, Values by rule | 54% | 3% | 44% | 11% | 83% | 100% | 17 / 1 |
| Personalized PageRank, Values by rule | 51% | 8% | 41% | 15% | 79% | 96% | 18 / 1 |
| **Hybrid: vector + fine-tuned G-reasoner** | **77%** | 3% | 21% | 8% | 89% | - (1 cite) | 8 / 1 |
| **Hybrid (fine-tuned), Values by rule** | **77%** | 3% | 21% | 8% | 89% | 90% | 8 / 1 |
| Hybrid: vector + PPR, Values by rule | 69% | 0% | 31% | 5% | 93% | 92% | 12 / 0 |

| Correct by type | single (9) | relation (6) | relation_text (12) | relation_deep (5) | cross_year (4) | cross_company (3) |
| --- | --- | --- | --- | --- | --- | --- |
| Vector RAG | 100% | 67% | 83% | 40% | 50% | 0% |
| G-reasoner zero-shot | 33% | 0% | 17% | 0% | 25% | 0% |
| G-reasoner fine-tuned | 100% | 33% | 42% | 40% | 0% | 67% |
| Personalized PageRank | 100% | 17% | 33% | 60% | 25% | 67% |
| Hybrid: vector + fine-tuned G-reasoner | 100% | 50% | 83% | 80% | 50% | 67% |

**What the results show**

1. **Retrieval causes almost every wrong answer, in every system** (92% of wrong answers for vector RAG,
   94-100% for the graph retrievers). When the needed facts reach Gemini it answers correctly; it refuses
   rather than guesses when they do not (hallucination 0-3%). The one vector-RAG generation error is
   v2_q37: both R&D figures were retrieved and cited, but the comparison was wrong.
2. **Five questions fail for every system:** v2_q11 (Janssen Biotech's state, a bare Exhibit 21 table
   row), v2_q23 (STELARA), v2_q28 (Shockwave chain, 3-4 facts) and v2_q33/v2_q34 (employee counts for two
   years).
3. **Some facts are not in the graph at all:** employee counts (v2_q33, v2_q34) and remaining performance
   obligations (v2_q36) are not among the 26 XBRL concepts the graph keeps, so a graph retriever cannot
   reach them. These are graph-stage failures; the automatic tagger counts them as retrieval, so they are
   re-tagged by hand.
4. **The graph misses facts that exist only in prose and that the question describes instead of names:**
   Genmab's patents and expiry (v2_q16), the Activision acquisition (v2_q19), manufacturing and tariffs
   (v2_q21), Proteologix (v2_q22), the EU Digital Markets Act (v2_q26), the Epic litigation (v2_q27). The
   start node is then often only the company, and the walk spreads into its Exhibit 21 subsidiaries. This
   is most of the gap on `relation_text` (83% vs 33-42%).
5. **The graph helps when the question names several entities:** cross-company v2_q39 (Apple vs J&J net
   income: both companies' figures retrieved by the graph, neither by vector RAG), v2_q29 (Activision
   goodwill), and v2_q13 for the fine-tuned model.
6. **Fine-tuning brought G-reasoner from 15% to 51%, level with Personalized PageRank but not above it.**
7. **Value citations are accurate when used but rare:** the retrievers seldom return the Values a question
   needs, so Gemini cites passages instead.
8. **Cross-year is weaker for the graph** (fine-tuned 0 of 4): partly point 3, partly the two years'
   Values not both being retrieved (v2_q35, DARZALEX FY2024 vs FY2025).

**The two improvements (Nov 26)**

9. **Hybrid retrieval is the best system: 77% correct** (vector RAG 69%, either graph retriever 51%). It
   answers 5 questions vector RAG misses (v2_q24, v2_q29, v2_q31, v2_q37, v2_q39) and loses 2 (v2_q10,
   v2_q21); deep questions go from 40% to 80% and cross-company from 0% to 67%. Vector search and the
   graph fail on different questions, so combining them works. With PPR instead of the fine-tuned model
   the hybrid only matches vector RAG (69%): fine-tuning matters once the graph is combined with vectors.
10. **Values chosen by rule make answers traceable without changing accuracy:** in the hybrid, the
    verdicts are identical, but 12 answers now cite a Value and 90% of those citations hold the stated
    number. Alone, the rule adds one correct answer for fine-tuned G-reasoner (51% to 54%) and none for
    PPR, where extra numbers pushed two weak answers into hallucinations (3% to 8%).

The two improvements were designed after seeing the failure patterns above, on the same 39 questions;
77% vs 69% is 3 questions.

Caveats: 39 questions, 3-12 per type, so one question moves a type's rate by 8-33 points. Sanity check:
the vector-RAG run reproduces the baseline's 69.2% correct with the same verdict on 38 of 39 questions; its
higher unsupported-number rate comes from two answers worded differently this run (v2_q37, v2_q10).

## Files

| File | What it does |
| --- | --- |
| `answer.py` | prompt, Gemini, judge, scores; writes `results/<system>_k<k>/per_question.jsonl` and `summary.json` (overall and by question type) |
| `graph_context.py` | loads the graph, Value ids, subgraph |
| `retrievals.py` | reads vector RAG / G-reasoner / PPR outputs into one format |
| `llm.py` | Gemini REST client with the reply cache |
| `make_hybrid.py` | merges vector RAG and graph retrievals into one retrieval file (`retrievals/`) |
| `compare.py` | one table over all runs |
| `trace.py` | trace view: answer sentence -> Value -> passage line -> filing -> SEC EDGAR link (`traces/`) |
