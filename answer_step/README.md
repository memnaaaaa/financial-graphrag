# Answer step with citations and trace view

Owner: Mohini. Turns any retriever's output into a cited answer, scores it, and traces each number back to
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
python answer_step/answer.py --system g_reasoner_zero_shot --retrievals <E2 per_question.jsonl>
python answer_step/answer.py --system g_reasoner_finetuned --retrievals <E3 per_question.jsonl>
python answer_step/answer.py --system ppr --retrievals <E4 per_question.jsonl>

python answer_step/compare.py                                   # table of all runs -> results/comparison.md
python answer_step/trace.py answer_step/results/g_reasoner_finetuned_k10/per_question.jsonl v2_q11
```

Options: `--dry-run` (no Gemini calls, fake answers: checks the pipeline only), `--types relation relation_deep`
or `--only v2_q11` (a subset), `--no-graph-context` (chunks only), `--rpm` (requests per minute, default 10).
One run is 39 answers + 39 judge calls.

## Results so far

| Run | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. |
| --- | --- | --- | --- | --- | --- |
| `vector_rag_k10` (bge-small + rerank, k = 10), Nov 25 | 69.2% | 0.0% | 30.8% | 23.3% (7 of 30) | 85.7% |

Sanity check: the vector RAG run reproduces the baseline's 69.2% correct
(`vector_rag_baseline/results/v2_all_baselines`), with the same judge verdict on 38 of 39 questions. The
higher unsupported-number rate (baseline 0%) comes from two answers Gemini worded differently this run:
v2_q37 states six numbers without a citation and then refuses, and v2_q10's "$60.4 billion" is not found in
its cited passage. G-reasoner (zero-shot, fine-tuned) and Personalized PageRank are run once their
per-question retrieval files are in the repo.

## Files

| File | What it does |
| --- | --- |
| `answer.py` | prompt, Gemini, judge, scores; writes `results/<system>_k<k>/per_question.jsonl` and `summary.json` (overall and by question type) |
| `graph_context.py` | loads the graph, Value ids, subgraph |
| `retrievals.py` | reads vector RAG / G-reasoner / PPR outputs into one format |
| `llm.py` | Gemini REST client with the reply cache |
| `compare.py` | one table over all runs |
| `trace.py` | trace view: answer sentence -> Value -> passage line -> filing -> SEC EDGAR link (`traces/`) |
