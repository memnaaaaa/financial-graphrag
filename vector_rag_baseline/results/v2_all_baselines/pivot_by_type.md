**Precision, k = 10**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0.20 | 0.26 | 0.11 | 0.16 |
| Relation | 6 | 0.17 | 0.17 | 0.10 | 0.12 |
| Relation, descriptive | 12 | 0.12 | 0.12 | 0.14 | 0.13 |
| Deep | 5 | 0.16 | 0.20 | 0.22 | 0.24 |
| Cross-year | 4 | 0.05 | 0.08 | 0.08 | 0.12 |
| Cross-company | 3 | 0.07 | 0.10 | 0.03 | 0.10 |
| **ALL** | 39 | 0.14 | 0.16 | 0.12 | 0.15 |

**Recall, k = 10**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0.51 | 0.65 | 0.30 | 0.39 |
| Relation | 6 | 0.54 | 0.58 | 0.36 | 0.44 |
| Relation, descriptive | 12 | 0.81 | 0.81 | 0.83 | 0.81 |
| Deep | 5 | 0.53 | 0.63 | 0.60 | 0.71 |
| Cross-year | 4 | 0.25 | 0.38 | 0.38 | 0.62 |
| Cross-company | 3 | 0.18 | 0.24 | 0.07 | 0.20 |
| **ALL** | 39 | 0.56 | 0.63 | 0.50 | 0.58 |

**Correct, k = 10**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 100% | 100% | 67% | 89% |
| Relation | 6 | 50% | 67% | 50% | 50% |
| Relation, descriptive | 12 | 92% | 83% | 75% | 83% |
| Deep | 5 | 40% | 40% | 40% | 40% |
| Cross-year | 4 | 25% | 50% | 0% | 50% |
| Cross-company | 3 | 0% | 0% | 0% | 0% |
| **ALL** | 39 | 67% | 69% | 51% | 64% |

**Missing, k = 10**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0% | 0% | 33% | 11% |
| Relation | 6 | 50% | 33% | 50% | 50% |
| Relation, descriptive | 12 | 8% | 17% | 17% | 17% |
| Deep | 5 | 40% | 60% | 60% | 60% |
| Cross-year | 4 | 75% | 50% | 100% | 50% |
| Cross-company | 3 | 100% | 67% | 100% | 67% |
| **ALL** | 39 | 31% | 28% | 46% | 33% |

**Hallucination, k = 10**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0% | 0% | 0% | 0% |
| Relation | 6 | 0% | 0% | 0% | 0% |
| Relation, descriptive | 12 | 0% | 0% | 8% | 0% |
| Deep | 5 | 20% | 0% | 0% | 0% |
| Cross-year | 4 | 0% | 0% | 0% | 0% |
| Cross-company | 3 | 0% | 33% | 0% | 33% |
| **ALL** | 39 | 3% | 3% | 3% | 3% |

**Precision, k = 5**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0.24 | 0.33 | 0.13 | 0.22 |
| Relation | 6 | 0.23 | 0.17 | 0.13 | 0.13 |
| Relation, descriptive | 12 | 0.23 | 0.23 | 0.25 | 0.27 |
| Deep | 5 | 0.24 | 0.32 | 0.24 | 0.36 |
| Cross-year | 4 | 0.10 | 0.15 | 0.10 | 0.20 |
| Cross-company | 3 | 0.13 | 0.13 | 0.00 | 0.13 |
| **ALL** | 39 | 0.22 | 0.24 | 0.17 | 0.23 |

**Recall, k = 5**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0.34 | 0.46 | 0.21 | 0.28 |
| Relation | 6 | 0.42 | 0.36 | 0.28 | 0.31 |
| Relation, descriptive | 12 | 0.72 | 0.78 | 0.78 | 0.81 |
| Deep | 5 | 0.42 | 0.48 | 0.32 | 0.53 |
| Cross-year | 4 | 0.25 | 0.38 | 0.25 | 0.50 |
| Cross-company | 3 | 0.18 | 0.18 | 0.00 | 0.13 |
| **ALL** | 39 | 0.46 | 0.51 | 0.40 | 0.49 |

**Correct, k = 5**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 89% | 100% | 67% | 89% |
| Relation | 6 | 50% | 17% | 50% | 17% |
| Relation, descriptive | 12 | 83% | 75% | 75% | 83% |
| Deep | 5 | 20% | 20% | 0% | 20% |
| Cross-year | 4 | 25% | 50% | 25% | 50% |
| Cross-company | 3 | 0% | 0% | 0% | 33% |
| **ALL** | 39 | 59% | 56% | 49% | 59% |

**Missing, k = 5**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 11% | 0% | 33% | 11% |
| Relation | 6 | 50% | 83% | 50% | 67% |
| Relation, descriptive | 12 | 17% | 25% | 25% | 17% |
| Deep | 5 | 80% | 80% | 100% | 80% |
| Cross-year | 4 | 75% | 50% | 75% | 50% |
| Cross-company | 3 | 100% | 67% | 100% | 67% |
| **ALL** | 39 | 41% | 41% | 51% | 38% |

**Hallucination, k = 5**

| Question type | n | bge | bge+rr | Distil | Distil+rr |
|---|---|---|---|---|---|
| Single-hop | 9 | 0% | 0% | 0% | 0% |
| Relation | 6 | 0% | 0% | 0% | 17% |
| Relation, descriptive | 12 | 0% | 0% | 0% | 0% |
| Deep | 5 | 0% | 0% | 0% | 0% |
| Cross-year | 4 | 0% | 0% | 0% | 0% |
| Cross-company | 3 | 0% | 33% | 0% | 0% |
| **ALL** | 39 | 0% | 3% | 0% | 3% |
