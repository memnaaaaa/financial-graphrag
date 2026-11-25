# Retrieval on golden set v2, E1 to E4, by question type

39 questions, same for every system. Systems: Vector = E1 (`bge-small`); Vector+rerank = E1 (`bge-small+rerank`); G-r zero-shot = E2 (`g-reasoner`); G-r fine-tuned = E3 (`g-reasoner-ft`); PageRank = E4 (`ppr`).
Vector RAG retrieves from the chunk index; the graph systems rank document nodes of `fin10k_v1` from the same rule-based start nodes. Best value in each row in bold.
AllFacts is not shown: only the vector run had `fact_chunks` (see compare_by_type.py).

**Hit@5**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | 0.78 | 0.89 | 0.11 | **1.00** | **1.00** |
| Relation | 6 | **0.83** | 0.67 | 0.00 | 0.67 | **0.83** |
| Relation, descriptive | 12 | 0.75 | **0.83** | 0.08 | 0.33 | 0.42 |
| Deep chain (3-5 hops) | 5 | 0.80 | **1.00** | 0.60 | 0.60 | 0.80 |
| Cross-year | 4 | **0.50** | **0.50** | 0.25 | 0.00 | 0.25 |
| Cross-company | 3 | 0.67 | 0.67 | 0.00 | **1.00** | **1.00** |
| **ALL** | 39 | 0.74 | **0.79** | 0.15 | 0.59 | 0.69 |

**Hit@10**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | **1.00** | 0.89 | 0.33 | **1.00** | **1.00** |
| Relation | 6 | **1.00** | 0.83 | 0.17 | **1.00** | **1.00** |
| Relation, descriptive | 12 | **0.83** | **0.83** | 0.17 | 0.42 | 0.42 |
| Deep chain (3-5 hops) | 5 | 0.80 | **1.00** | 0.60 | 0.80 | 0.80 |
| Cross-year | 4 | **0.50** | **0.50** | **0.50** | 0.00 | 0.25 |
| Cross-company | 3 | 0.67 | 0.67 | 0.00 | **1.00** | **1.00** |
| **ALL** | 39 | **0.85** | 0.82 | 0.28 | 0.69 | 0.72 |

**Precision@5**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | 0.24 | 0.33 | 0.02 | **0.62** | 0.42 |
| Relation | 6 | **0.23** | 0.17 | 0.00 | 0.17 | 0.20 |
| Relation, descriptive | 12 | **0.23** | **0.23** | 0.02 | 0.08 | 0.10 |
| Deep chain (3-5 hops) | 5 | 0.24 | **0.32** | 0.12 | 0.24 | 0.24 |
| Cross-year | 4 | 0.10 | **0.15** | 0.10 | 0.00 | 0.10 |
| Cross-company | 3 | 0.13 | 0.13 | 0.00 | **0.67** | 0.27 |
| **ALL** | 39 | 0.22 | 0.24 | 0.04 | **0.28** | 0.22 |

**Precision@10**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | 0.20 | 0.26 | 0.03 | **0.39** | 0.31 |
| Relation | 6 | **0.17** | **0.17** | 0.03 | 0.15 | 0.13 |
| Relation, descriptive | 12 | **0.13** | **0.13** | 0.03 | 0.06 | 0.07 |
| Deep chain (3-5 hops) | 5 | 0.16 | **0.20** | 0.06 | 0.14 | 0.14 |
| Cross-year | 4 | 0.05 | **0.08** | **0.08** | 0.00 | 0.05 |
| Cross-company | 3 | 0.07 | 0.10 | 0.00 | **0.43** | 0.33 |
| **ALL** | 39 | 0.14 | 0.16 | 0.04 | **0.18** | 0.16 |

**Recall@5**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | 0.34 | 0.46 | 0.02 | **0.87** | 0.60 |
| Relation | 6 | **0.42** | 0.36 | 0.00 | 0.28 | 0.33 |
| Relation, descriptive | 12 | 0.72 | **0.78** | 0.04 | 0.29 | 0.29 |
| Deep chain (3-5 hops) | 5 | 0.42 | **0.48** | 0.13 | 0.40 | 0.37 |
| Cross-year | 4 | 0.25 | **0.38** | 0.25 | 0.00 | 0.25 |
| Cross-company | 3 | 0.18 | 0.18 | 0.00 | **0.80** | 0.31 |
| **ALL** | 39 | 0.46 | **0.51** | 0.06 | 0.45 | 0.38 |

**Recall@10**

| Question type | n | Vector | Vector+rerank | G-r zero-shot | G-r fine-tuned | PageRank |
|---|---|---|---|---|---|---|
| Single fact | 9 | 0.51 | 0.65 | 0.07 | **1.00** | 0.87 |
| Relation | 6 | 0.54 | **0.58** | 0.08 | 0.47 | 0.44 |
| Relation, descriptive | 12 | **0.81** | **0.81** | 0.12 | 0.38 | 0.38 |
| Deep chain (3-5 hops) | 5 | 0.53 | **0.63** | 0.13 | 0.43 | 0.43 |
| Cross-year | 4 | 0.25 | **0.38** | 0.31 | 0.00 | 0.25 |
| Cross-company | 3 | 0.18 | 0.24 | 0.00 | **1.00** | 0.71 |
| **ALL** | 39 | 0.56 | **0.63** | 0.12 | 0.55 | 0.52 |
