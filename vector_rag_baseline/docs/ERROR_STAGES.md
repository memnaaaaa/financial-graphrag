# Error-stage scheme

Every wrong answer gets exactly one tag: **the first stage of the pipeline that failed**. Check the stages in this
order and stop at the first one that fails. Code: `rag/error_stage.py` (`tag()`), already called by `scripts/run_eval.py`
(field `error_stage` per answer, `stage_*` shares in `summary.json`).

An answer is **wrong** when the judge says `hallucination` or `missing` (or `invalid`). Correct answers are tagged `ok`.

| # | Stage | Rule: it failed if... | How it is checked | Small example (illustrative) |
|---|---|---|---|---|
| 1 | **graph** | the fact needed is not in the graph: no Value node holds the gold number, or the edge for the relation is missing | look the gold fact up in the graph by its `gold_facts` / source chunk | "Which segment sells the drug licensed from Genmab?" but the graph has no `LICENSED_FROM` edge from DARZALEX to Genmab, so no path exists |
| 2 | **entity_linking** | the question's entities (company, fiscal year, product, subsidiary) are not linked to the right nodes | compare linked node ids with the entities named in the question (`companies`, `filings`) | "Apple's R&D in fiscal 2025" is linked to the FY2024 filing node, or "Azure" is linked to nothing |
| 3 | **retrieval** | graph and linking are fine but at least one gold fact of the question has none of its chunks in the evidence given to the generator (a missing hop) | `all_facts` = 0 from `metrics.facts_found` (uses `fact_chunks` in golden set v2); `missing_facts` names the lost fact | the retrieved chunks are Microsoft's FY2025 segment table, so the FY2026 Intelligent Cloud revenue never reaches the model |
| 4 | **generation** | the evidence contains the gold fact, but the answer is still wrong | judge label is not `correct` while `all_facts` = 1 | the right chunk is retrieved, but the model refuses, copies the wrong column, or states a number the cited chunk does not hold |

Details for stage 4 (`generation_subtype()` in the same file): `refused_or_incomplete` (judge `missing`),
`unsupported_number` (a number in none of its cited chunks), `wrong_citation` (the cited chunk does not hold the number, or
is from the wrong filing), `wrong_value_or_reasoning` (cited correctly but the value or arithmetic is wrong).

Notes
- The vector-RAG baseline has no graph and no linking step, so only `retrieval` and `generation` can occur for it
  (the wrong-fiscal-year problem is counted as `retrieval`: the evidence is from the wrong filing).
- Graph systems call `tag(verdict, hit, graph_has_fact=..., entities_linked=...)`; the default for both is True.
- "First failure" means an answer is never counted twice: a missing graph edge is `graph` even if retrieval also missed.
- `all_facts` is a property of the evidence, not of the answer: a correct answer with `all_facts` = 0 (the model knew it) is tagged `ok`.
  Such answers are visible as `ok` with `all_facts = 0` and are flagged in the report as possible leakage from model memory.

## Two measures for the hallucination study (`rag/metrics.py`)

| Measure | Definition |
|---|---|
| **Unsupported-number rate** | share of numbers in the answers that appear in none of the chunks the answer cites. Numbers are matched after removing commas, allowing the rounding the answer used and a thousand/million rescale ($416.2 billion vs 416,161 million); years and numbers already in the question are ignored. `allow_derived=True` also accepts a sum, difference, ratio or percent change of two cited numbers. |
| **Citation accuracy** | the answer is split into sentences; a sentence with a number is a claim. A claim is correct if it cites at least one chunk, every number in it is found in one of *its* cited chunks, and every cited chunk is from a filing the question needs. Also reported: **citation rate** (claims that cite anything). |

The generator prompt (`rag/generate.py`) now asks for `[chunk_id]` after every number and for the fiscal year of each number.
