| Config | k | Question type | n | P@k | R@k | Hit@k | AllFacts@k | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. | Answer support |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | single | 9 | 0.244 | 0.339 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 88% of 8 |
| bge-small | 5 | relation | 6 | 0.233 | 0.417 | 0.83 | 0.33 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 67% of 6 |
| bge-small | 5 | relation_text | 12 | 0.233 | 0.722 | 0.75 | 0.75 | 83% | 0% | 17% | 0% of 4 | 25% of 4 | 78% of 27 |
| bge-small | 5 | relation_deep | 5 | 0.240 | 0.417 | 0.80 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 67% of 6 |
| bge-small | 5 | cross_year | 4 | 0.100 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 0% of 3 | 100% of 2 | 67% of 3 |
| bge-small | 5 | cross_company | 3 | 0.133 | 0.178 | 0.67 | 0.00 | 0% | 0% | 100% | n/a | n/a | 0% of 2 |
| bge-small | 5 | **ALL** | 39 | 0.215 | 0.457 | 0.74 | 0.49 | 59% | 0% | 41% | 0% of 20 | 83% of 18 | 73% of 52 |
| bge-small | 10 | single | 9 | 0.200 | 0.512 | 1.00 | 1.00 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 78% of 9 |
| bge-small | 10 | relation | 6 | 0.167 | 0.542 | 1.00 | 0.33 | 50% | 0% | 50% | 0% of 4 | 100% of 4 | 83% of 12 |
| bge-small | 10 | relation_text | 12 | 0.125 | 0.806 | 0.83 | 0.83 | 92% | 0% | 8% | 0% of 4 | 0% of 3 | 83% of 30 |
| bge-small | 10 | relation_deep | 5 | 0.160 | 0.533 | 0.80 | 0.20 | 40% | 20% | 40% | 0% of 6 | 100% of 4 | 64% of 11 |
| bge-small | 10 | cross_year | 4 | 0.050 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 20% of 5 | 50% of 2 | 50% of 2 |
| bge-small | 10 | cross_company | 3 | 0.067 | 0.178 | 0.67 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| bge-small | 10 | **ALL** | 39 | 0.141 | 0.557 | 0.85 | 0.56 | 67% | 3% | 31% | 4% of 28 | 82% of 22 | 78% of 64 |
| bge-small+rerank | 5 | single | 9 | 0.333 | 0.460 | 0.89 | 0.89 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 89% of 9 |
| bge-small+rerank | 5 | relation | 6 | 0.167 | 0.361 | 0.67 | 0.17 | 17% | 0% | 83% | 0% of 1 | 100% of 1 | 75% of 4 |
| bge-small+rerank | 5 | relation_text | 12 | 0.233 | 0.778 | 0.83 | 0.75 | 75% | 0% | 25% | 0% of 5 | 67% of 3 | 87% of 31 |
| bge-small+rerank | 5 | relation_deep | 5 | 0.320 | 0.479 | 1.00 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 80% of 5 |
| bge-small+rerank | 5 | cross_year | 4 | 0.150 | 0.375 | 0.50 | 0.25 | 50% | 0% | 50% | 0% of 4 | 100% of 3 | 100% of 3 |
| bge-small+rerank | 5 | cross_company | 3 | 0.133 | 0.178 | 0.67 | 0.00 | 0% | 33% | 67% | 20% of 5 | 67% of 3 | 40% of 5 |
| bge-small+rerank | 5 | **ALL** | 39 | 0.241 | 0.514 | 0.79 | 0.51 | 56% | 3% | 41% | 4% of 27 | 90% of 21 | 82% of 57 |
| bge-small+rerank | 10 | single | 9 | 0.256 | 0.650 | 0.89 | 0.89 | 100% | 0% | 0% | 0% of 9 | 100% of 9 | 89% of 9 |
| bge-small+rerank | 10 | relation | 6 | 0.167 | 0.583 | 0.83 | 0.50 | 67% | 0% | 33% | 0% of 4 | 100% of 4 | 78% of 9 |
| bge-small+rerank | 10 | relation_text | 12 | 0.125 | 0.806 | 0.83 | 0.83 | 83% | 0% | 17% | 0% of 3 | 50% of 2 | 77% of 30 |
| bge-small+rerank | 10 | relation_deep | 5 | 0.200 | 0.629 | 1.00 | 0.40 | 40% | 0% | 60% | 0% of 6 | 100% of 4 | 60% of 10 |
| bge-small+rerank | 10 | cross_year | 4 | 0.075 | 0.375 | 0.50 | 0.25 | 50% | 0% | 50% | 0% of 4 | 100% of 2 | 100% of 2 |
| bge-small+rerank | 10 | cross_company | 3 | 0.100 | 0.244 | 0.67 | 0.33 | 0% | 33% | 67% | 0% of 2 | 100% of 1 | 100% of 2 |
| bge-small+rerank | 10 | **ALL** | 39 | 0.164 | 0.625 | 0.82 | 0.64 | 69% | 3% | 28% | 0% of 28 | 95% of 22 | 77% of 62 |
| distilbert | 5 | single | 9 | 0.133 | 0.207 | 0.56 | 0.56 | 67% | 0% | 33% | 0% of 6 | 100% of 6 | 100% of 6 |
| distilbert | 5 | relation | 6 | 0.133 | 0.278 | 0.67 | 0.00 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 90% of 10 |
| distilbert | 5 | relation_text | 12 | 0.250 | 0.778 | 0.83 | 0.75 | 75% | 0% | 25% | 0% of 4 | 100% of 2 | 85% of 20 |
| distilbert | 5 | relation_deep | 5 | 0.240 | 0.324 | 1.00 | 0.00 | 0% | 0% | 100% | 0% of 1 | 100% of 1 | 50% of 2 |
| distilbert | 5 | cross_year | 4 | 0.100 | 0.250 | 0.50 | 0.00 | 25% | 0% | 75% | 0% of 3 | 100% of 2 | 67% of 3 |
| distilbert | 5 | cross_company | 3 | 0.000 | 0.000 | 0.00 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| distilbert | 5 | **ALL** | 39 | 0.169 | 0.397 | 0.67 | 0.36 | 49% | 0% | 51% | 0% of 16 | 100% of 13 | 85% of 41 |
| distilbert | 10 | single | 9 | 0.111 | 0.304 | 0.56 | 0.56 | 67% | 0% | 33% | 0% of 6 | 100% of 6 | 83% of 6 |
| distilbert | 10 | relation | 6 | 0.100 | 0.361 | 0.83 | 0.17 | 50% | 0% | 50% | 0% of 2 | 100% of 2 | 64% of 11 |
| distilbert | 10 | relation_text | 12 | 0.142 | 0.833 | 0.83 | 0.83 | 75% | 8% | 17% | 0% of 2 | 50% of 2 | 77% of 26 |
| distilbert | 10 | relation_deep | 5 | 0.220 | 0.602 | 1.00 | 0.40 | 40% | 0% | 60% | 60% of 5 | 33% of 3 | 45% of 11 |
| distilbert | 10 | cross_year | 4 | 0.075 | 0.375 | 0.75 | 0.00 | 0% | 0% | 100% | 0% of 1 | 100% of 1 | 100% of 1 |
| distilbert | 10 | cross_company | 3 | 0.033 | 0.067 | 0.33 | 0.00 | 0% | 0% | 100% | n/a | n/a | n/a |
| distilbert | 10 | **ALL** | 39 | 0.123 | 0.503 | 0.74 | 0.46 | 51% | 3% | 46% | 19% of 16 | 79% of 14 | 69% of 55 |
| distilbert+rerank | 5 | single | 9 | 0.222 | 0.280 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 75% of 8 |
| distilbert+rerank | 5 | relation | 6 | 0.133 | 0.306 | 0.50 | 0.17 | 17% | 17% | 67% | 0% of 2 | 100% of 2 | 100% of 4 |
| distilbert+rerank | 5 | relation_text | 12 | 0.267 | 0.806 | 0.83 | 0.75 | 83% | 0% | 17% | 0% of 5 | 33% of 3 | 76% of 29 |
| distilbert+rerank | 5 | relation_deep | 5 | 0.360 | 0.529 | 1.00 | 0.20 | 20% | 0% | 80% | 0% of 3 | 100% of 2 | 100% of 3 |
| distilbert+rerank | 5 | cross_year | 4 | 0.200 | 0.500 | 0.50 | 0.50 | 50% | 0% | 50% | 0% of 5 | 100% of 4 | 100% of 4 |
| distilbert+rerank | 5 | cross_company | 3 | 0.133 | 0.133 | 0.33 | 0.33 | 33% | 0% | 67% | 20% of 5 | 50% of 2 | 50% of 2 |
| distilbert+rerank | 5 | **ALL** | 39 | 0.231 | 0.489 | 0.72 | 0.54 | 59% | 3% | 38% | 4% of 28 | 86% of 21 | 80% of 50 |
| distilbert+rerank | 10 | single | 9 | 0.156 | 0.391 | 0.78 | 0.78 | 89% | 0% | 11% | 0% of 8 | 100% of 8 | 88% of 8 |
| distilbert+rerank | 10 | relation | 6 | 0.117 | 0.444 | 0.83 | 0.17 | 50% | 0% | 50% | 0% of 3 | 100% of 3 | 80% of 5 |
| distilbert+rerank | 10 | relation_text | 12 | 0.133 | 0.806 | 0.83 | 0.75 | 83% | 0% | 17% | 0% of 3 | 100% of 2 | 83% of 29 |
| distilbert+rerank | 10 | relation_deep | 5 | 0.240 | 0.707 | 1.00 | 0.40 | 40% | 0% | 60% | 0% of 6 | 100% of 4 | 80% of 10 |
| distilbert+rerank | 10 | cross_year | 4 | 0.125 | 0.625 | 0.75 | 0.50 | 50% | 0% | 50% | 0% of 4 | 100% of 2 | 100% of 2 |
| distilbert+rerank | 10 | cross_company | 3 | 0.100 | 0.200 | 0.33 | 0.33 | 0% | 33% | 67% | 20% of 5 | 0% of 1 | 0% of 1 |
| distilbert+rerank | 10 | **ALL** | 39 | 0.146 | 0.577 | 0.79 | 0.56 | 64% | 3% | 33% | 3% of 29 | 95% of 20 | 82% of 55 |
