# Answer step: all systems (golden set v2)

| System | k | n | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. | Value-cite acc. | Retrieval | Generation |
|---|---|---|---|---|---|---|---|---|---|---|
| g_reasoner_finetuned | 10 | 39 | 51% | 3% | 46% | 8% | 84% | - | 18 | 1 |
| g_reasoner_finetuned_rule | 10 | 39 | 54% | 3% | 44% | 11% | 83% | 100% | 17 | 1 |
| g_reasoner_zero_shot | 10 | 39 | 15% | 0% | 85% | 0% | 100% | 100% | 31 | 2 |
| hybrid_finetuned | 10 | 39 | 77% | 3% | 21% | 8% | 89% | 0% | 8 | 1 |
| hybrid_finetuned_rule | 10 | 39 | 77% | 3% | 21% | 8% | 89% | 90% | 8 | 1 |
| hybrid_ppr_rule | 10 | 39 | 69% | 0% | 31% | 5% | 93% | 92% | 12 | 0 |
| ppr | 10 | 39 | 51% | 3% | 46% | 6% | 92% | 100% | 19 | 0 |
| ppr_rule | 10 | 39 | 51% | 8% | 41% | 15% | 79% | 96% | 18 | 1 |
| vector_rag | 10 | 39 | 69% | 0% | 31% | 23% | 86% | - | 11 | 1 |

**Correct answers by question type**

| System | single | relation | relation_text | relation_deep | cross_year | cross_company |
|---|---|---|---|---|---|---|
| g_reasoner_finetuned | 100% (n=9) | 33% (n=6) | 42% (n=12) | 40% (n=5) | 0% (n=4) | 67% (n=3) |
| g_reasoner_finetuned_rule | 100% (n=9) | 33% (n=6) | 42% (n=12) | 40% (n=5) | 25% (n=4) | 67% (n=3) |
| g_reasoner_zero_shot | 33% (n=9) | 0% (n=6) | 17% (n=12) | 0% (n=5) | 25% (n=4) | 0% (n=3) |
| hybrid_finetuned | 100% (n=9) | 50% (n=6) | 83% (n=12) | 80% (n=5) | 50% (n=4) | 67% (n=3) |
| hybrid_finetuned_rule | 100% (n=9) | 50% (n=6) | 83% (n=12) | 80% (n=5) | 50% (n=4) | 67% (n=3) |
| hybrid_ppr_rule | 100% (n=9) | 50% (n=6) | 83% (n=12) | 20% (n=5) | 50% (n=4) | 67% (n=3) |
| ppr | 100% (n=9) | 17% (n=6) | 33% (n=12) | 60% (n=5) | 25% (n=4) | 67% (n=3) |
| ppr_rule | 100% (n=9) | 17% (n=6) | 33% (n=12) | 40% (n=5) | 25% (n=4) | 100% (n=3) |
| vector_rag | 100% (n=9) | 67% (n=6) | 83% (n=12) | 40% (n=5) | 50% (n=4) | 0% (n=3) |

Retrieval / generation columns: error stages (rules in vector_rag_baseline/docs/ERROR_STAGES.md); facts checked with: fact_chunks.
