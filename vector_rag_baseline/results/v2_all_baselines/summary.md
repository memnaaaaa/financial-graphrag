# Summary: bge-small and DistilBERT, golden set v2 (39 questions)

Generator and judge: gemini-3.5-flash-lite (T = 0). Fixed chunks, 6 filings.

| Configuration | k | P@k | R@k | Hit@k | AllFacts | Correct | Halluc. | Missing | Unsupp. numbers | Citation acc. | Answer support | Retrieval ms | End-to-end ms (mean / p95) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | 0.215 | 0.457 | 0.74 | 0.49 | 59.0% | 0.0% | 41.0% | 0.0% | 83.3% | 73.1% | 61 | 815 / 1151 |
| bge-small | 10 | 0.141 | 0.557 | 0.85 | 0.56 | 66.7% | 2.6% | 30.8% | 3.6% | 81.8% | 78.1% | 62 | 901 / 1427 |
| bge-small + rerank | 5 | 0.241 | 0.514 | 0.79 | 0.51 | 56.4% | 2.6% | 41.0% | 3.7% | 90.5% | 82.5% | 155 | 874 / 1304 |
| bge-small + rerank | 10 | 0.164 | 0.625 | 0.82 | 0.64 | 69.2% | 2.6% | 28.2% | 0.0% | 95.5% | 77.4% | 159 | 921 / 1220 |
| DistilBERT | 5 | 0.169 | 0.397 | 0.67 | 0.36 | 48.7% | 0.0% | 51.3% | 0.0% | 100.0% | 85.4% | 84 | 808 / 1186 |
| DistilBERT | 10 | 0.123 | 0.503 | 0.74 | 0.46 | 51.3% | 2.6% | 46.2% | 18.8% | 78.6% | 69.1% | 48 | 858 / 1218 |
| DistilBERT + rerank | 5 | 0.231 | 0.489 | 0.72 | 0.54 | 59.0% | 2.6% | 38.5% | 3.6% | 85.7% | 80.0% | 137 | 791 / 1111 |
| DistilBERT + rerank | 10 | 0.146 | 0.577 | 0.79 | 0.56 | 64.1% | 2.6% | 33.3% | 3.4% | 95.0% | 81.8% | 131 | 922 / 1128 |
