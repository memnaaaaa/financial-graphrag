# Vector-RAG baseline for multi-hop financial QA

Baseline retrieval-augmented generation pipeline over SEC 10-K filings, built to compare against a GNN retriever
(G-Reasoner fine-tuned on a graph of the same filings). It covers the vector-RAG baseline, a hand-built golden question set,
the evaluation metrics, and the first results.

> **Golden set status: 1 of 19 questions validated.** Gold chunk labels for the other
> 18 questions come from pattern matching and are not yet verified, so all numbers below are preliminary.
> See [GOLDEN_SET.md](GOLDEN_SET.md) for how the golden set was built, its status per question, and its limitations.

## Pipeline

```
chunks.jsonl -> embed (bge-small / DistilBERT) -> FAISS IndexFlatIP -> dense top-k -> optional cross-encoder rerank (top 20)
             -> generate (Gemini 2.5 Flash-Lite, T=0) -> judge (Gemini 2.5 Flash, T=0) -> metrics + latency
```

| Component | Choice |
|---|---|
| Embedding | `BAAI/bge-small-en-v1.5` (33M) and `sentence-transformers/multi-qa-distilbert-cos-v1` (66M) |
| Index | FAISS `IndexFlatIP`, L2-normalized vectors (exact cosine search) |
| Retrieval | Dense top-k, k = 5 and 10 |
| Rerank | `cross-encoder/ms-marco-MiniLM-L-6-v2` over the top 20 (optional) |
| Generator / judge | Gemini 2.5 Flash-Lite / Gemini 2.5 Flash, temperature 0 |
| Metrics | precision@k, recall@k, hit@k, judge accuracy / hallucination / missing rate, latency |

## Results (run `full_run_2`, 19 questions, 7,339 chunks)

| Config | k | P@k | R@k | Hit@k | Correct | Halluc. | Missing | Retrieval ms | End-to-end ms |
|---|---|---|---|---|---|---|---|---|---|
| bge-small | 5 | 0.189 | 0.385 | 0.74 | 42.1% | 5.3% | 52.6% | 13 | 501 |
| bge-small | 10 | 0.126 | 0.503 | 0.79 | 47.4% | 10.5% | 42.1% | 13 | 477 |
| bge-small + rerank | 5 | 0.189 | 0.375 | 0.68 | 47.4% | 21.1% | 31.6% | 50 | 488 |
| bge-small + rerank | 10 | 0.132 | 0.514 | 0.84 | 47.4% | 21.1% | 31.6% | 51 | 591 |
| DistilBERT | 5 | 0.158 | 0.319 | 0.63 | 31.6% | 5.3% | 63.2% | 9 | 408 |
| DistilBERT | 10 | 0.116 | 0.408 | 0.68 | 36.8% | 10.5% | 52.6% | 9 | 503 |
| DistilBERT + rerank | 5 | 0.158 | 0.304 | 0.58 | 47.4% | 10.5% | 42.1% | 46 | 507 |
| DistilBERT + rerank | 10 | 0.116 | 0.453 | 0.79 | 42.1% | 15.8% | 42.1% | 46 | 511 |

Definitions of every metric are in `docs/baseline_report_v2.docx` (Appendix A). Main findings: retrieval never picks the wrong
company but picks the wrong fiscal year of the right company 43% of the time; cross-company questions almost never retrieve
both companies' answer chunks; generation is about 94% of end-to-end latency. Raw per-question results are in
`results/full_run_1/` and `results/full_run_2/`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add GEMINI_API_KEY, or use Vertex AI (see below)
python -m pytest -q tests        # unit tests, no network needed
python scripts/smoke_test.py     # checks each tool: encoders, FAISS, reranker, generator, judge

# put the shared chunks file at data/chunks.jsonl (it is not stored in this folder), then:
python scripts/run_eval.py --chunks data/chunks.jsonl --questions data/questions.jsonl \
    --encoders bge-small distilbert --rerank --out results/my_run
```

**Generator and judge access.** Set `GEMINI_API_KEY` to use Google AI Studio, or leave it unset and call Gemini through Vertex AI
by setting `GOOGLE_CLOUD_PROJECT` (and signing in with `gcloud auth login`). Machine-specific values can go in the git-ignored
`rag/local_config.py` (see `rag/local_config.example.py`).

`data/chunks.jsonl` needs the fields `chunk_id` and `text` (aliases in `rag/config.py`); other fields are kept as metadata.

## Layout

| Path | Contents |
|---|---|
| `rag/` | data loading, embedding, FAISS index, retrieval and rerank, generation, judge, metrics |
| `scripts/` | `run_eval.py`, `smoke_test.py`, `build_questions.py`, `build_label_pools.py`, `ingest_labels.py`, `make_docs.py` |
| `data/` | `questions.jsonl` (golden set), `questions_pattern_gold.jsonl`, `labeling/` (labeler pools, prompt, replies), `dummy_*` stand-ins |
| `results/` | `full_run_1/`, `full_run_2/` (`per_question.jsonl` and `summary.json`) |
| `docs/` | `baseline_report_v2.docx`: flow, results, explanations, metric definitions |
| `tests/` | unit tests for metrics, the judge parser and the data loader |

## Known limitations

* Golden set mostly unverified (see above); 19 questions is small.
* The LLM judge is noisy: it flipped one verdict between two identical runs and mislabeled some answers, so judge-based rates
  are rough.
* Retrieval picks the wrong fiscal year of the right company often; a year filter and a BM25 or hybrid baseline are the
  next experiments.
