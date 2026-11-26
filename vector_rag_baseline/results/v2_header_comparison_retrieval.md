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
