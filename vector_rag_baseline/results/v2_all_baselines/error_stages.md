# Error stages (golden set v2, 39 questions)

Every wrong answer gets the first pipeline stage that failed (rules in README.md and docs/ERROR_STAGES.md). Vector RAG has no graph or entity-linking step, so only `retrieval` and `generation` can occur. `ok` = judged correct.

**Count of questions per stage**

| Configuration | k | ok | graph | entity_linking | retrieval | generation |
|---|---|---|---|---|---|---|
| bge-small | 5 | 23 | 0 | 0 | 16 | 0 |
| bge-small | 10 | 26 | 0 | 0 | 12 | 1 |
| bge-small + rerank | 5 | 22 | 0 | 0 | 17 | 0 |
| bge-small + rerank | 10 | 27 | 0 | 0 | 11 | 1 |
| DistilBERT | 5 | 19 | 0 | 0 | 20 | 0 |
| DistilBERT | 10 | 20 | 0 | 0 | 18 | 1 |
| DistilBERT + rerank | 5 | 23 | 0 | 0 | 16 | 0 |
| DistilBERT + rerank | 10 | 25 | 0 | 0 | 13 | 1 |

**Wrong answers by question type and stage, k = 10** (retrieval / generation, out of n questions)

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 0 / 0 | 0 / 0 | 3 / 0 | 1 / 0 |
| Relation | 6 | 2 / 1 | 2 / 0 | 3 / 0 | 3 / 0 |
| Relation, descriptive | 12 | 1 / 0 | 2 / 0 | 2 / 1 | 2 / 0 |
| Deep | 5 | 3 / 0 | 3 / 0 | 3 / 0 | 3 / 0 |
| Cross-year | 4 | 3 / 0 | 2 / 0 | 4 / 0 | 2 / 0 |
| Cross-company | 3 | 3 / 0 | 2 / 1 | 3 / 0 | 2 / 1 |

**Wrong answers by question type and stage, k = 5** (retrieval / generation, out of n questions)

| Question type | n | bge-small | bge-small + rerank | DistilBERT | DistilBERT + rerank |
|---|---|---|---|---|---|
| Single-hop | 9 | 1 / 0 | 0 / 0 | 3 / 0 | 1 / 0 |
| Relation | 6 | 3 / 0 | 5 / 0 | 3 / 0 | 5 / 0 |
| Relation, descriptive | 12 | 2 / 0 | 3 / 0 | 3 / 0 | 2 / 0 |
| Deep | 5 | 4 / 0 | 4 / 0 | 5 / 0 | 4 / 0 |
| Cross-year | 4 | 3 / 0 | 2 / 0 | 3 / 0 | 2 / 0 |
| Cross-company | 3 | 3 / 0 | 3 / 0 | 3 / 0 | 2 / 0 |

Per-answer detail (stage, verdict, which gold fact was missing) for every wrong answer: `error_cases.csv`.
