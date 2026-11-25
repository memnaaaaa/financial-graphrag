# G-reasoner: graph retriever (workstream C)

Owner: Rida. This folder runs the **G-reasoner-34M** graph retriever (gfmrag 2.0.0) on the team's
knowledge graph (`data/graph/fin10k_v1`). It covers the retriever experiments:
- **E2:** zero-shot
- **E3:** fine-tuned on synthetic pairs
- **E4:** the non-learned Personalized PageRank baseline
- **E7:** the per-layer hop analysis

All of these are scored on golden set v2 (`vector_rag_baseline/data/questions_v2.jsonl`, 39 questions)
with the vector baseline's metrics.

**Status (Nov 25, 2026):** E2, E3, E4 and E7 are done on `fin10k_v1`. The results are in `results/`,
and the E1–E4 table by question type is in [`results/e1_e4_by_type.md`](results/e1_e4_by_type.md).
Still open:
- E8, G-reasoner's own graph built from the 10-K text
- E9, `fin10k_v0` vs `fin10k_v1`
- failure tagging with the answer step (E6)

- **Using the retrievals in the answer step?** Use the per-question files under [Per-question files](#per-question-files-for-the-answer-step).
- **Writing the report?** Use the [headline result](#headline-result-golden-set-v2-fin10k_v1) and the
  [hop analysis](#hop-analysis-e7). Earlier notes on `fin10k_v0` are in [`REPORT_NOTES.md`](REPORT_NOTES.md).
- **Running the code?** Follow [Setup and how to run it](#setup-and-how-to-run-it). Open `g_reasoner_fin10k.ipynb` in Colab on a T4 and run all.
- **Input format** and how our graph maps onto it: [`docs/INPUT_FORMAT.md`](docs/INPUT_FORMAT.md).

## Headline result (golden set v2, `fin10k_v1`)

The same 39 questions are used for every system. All graph systems start from the same rule-based start nodes (`entity_index.py`).

| System | Exp. | Hit@5 | P@5 | R@5 | Hit@10 | R@10 |
| --- | --- | --- | --- | --- | --- | --- |
| Vector RAG, bge-small (Mahua, `v2_all_baselines`) | E1 | 0.74 | 0.22 | 0.46 | **0.85** | 0.56 |
| Vector RAG, bge-small + rerank | E1 | **0.79** | 0.24 | **0.51** | 0.82 | **0.63** |
| G-reasoner-34M, zero-shot | E2 | 0.15 | 0.04 | 0.06 | 0.28 | 0.12 |
| G-reasoner-34M, fine-tuned | E3 | 0.59 | **0.28** | 0.45 | 0.69 | 0.55 |
| Personalized PageRank | E4 | 0.69 | 0.22 | 0.38 | 0.72 | 0.52 |

The breakdown by question type, for Hit, P and R at k=5 and 10, is in `results/e1_e4_by_type.md`. In short:

- **Fine-tuning helps a lot.** Hit@5 rises from 0.15 to 0.59. On the held-out relation questions (`relation_dev`, 9 q), Hit@5 rises from 0.56 to 0.89 and R@10 from 0.32 to 0.88.
- **The graph methods win on single-fact and cross-company questions.** Fine-tuned and PageRank both reach Hit@10 = 1.00 there.
- **They lose on descriptive relations and cross-year questions.** Fine-tuned gets 0 of 4 cross-year questions. The question's topic (headcount, patents, a lawsuit, remaining performance obligations) is not a node in the graph. So the start nodes are just the company and the fiscal year, which are hubs linked to hundreds of chunks. Vector RAG reads the text and finds most of these. This is a graph-coverage limit, to be tagged in E6.
- **AllFacts is not compared.** Only the vector run had `fact_chunks`. In the graph runs AllFacts equals Hit until `questions_v2.jsonl` carries that field.

Earlier result on `fin10k_v0` (Oct 21, 11 questions): zero-shot Hit@5 was 0.18. Using Gemini instead of the rule-based matcher to pick start nodes gave the same results. Details are in `REPORT_NOTES.md` and in `results/zero_shot_fin10k_v0/`, `results/gemini_ner_fin10k_v0/` and `results/ner_ablation_fin10k_v0/`.

## Fine-tuning (E3)

- **Starting point:** `rmanluo/G-reasoner-34M`.
- **Data:** synthetic pairs from `fin10k_v1` (`synthetic/fin10k_v1/`, see [Synthetic data](#synthetic-data-syntheticfin10k_v1)).
  - Train on J&J and Apple.
  - Pick the best epoch by document MRR on the held-out Microsoft pairs.
  - Golden questions never appear in training (the overlap guard enforces this).
- **Settings:** float32, lr 1e-4, 10 epochs. The best epoch was 9, with validation document MRR 0.948. The run took about 50 minutes on a T4.
- **Config:** `configs/finetune_fin10k.yaml`. It explains why each setting differs from gfmrag's default. Short version: the T4 has no bfloat16, and gfmrag's float16 path cannot train.
- **Training files:** the log, Hydra config and model config are in `results/finetuned_fin10k_v1/training/`. The curves are in `results/finetuned_fin10k_v1/plots/`.
- **Weights:** `model_best.pth` (415 MB) stays on Drive at `fin_greasoner_cache/finetune/20261124-113036/`. It is not in git.

## Personalized PageRank (E4)

`ppr.py` is the fixed graph walk used in HippoRAG:
- Every edge counts as undirected.
- Damping is 0.5.
- Restart is uniform over the question's start nodes.
- Documents are ranked by their PageRank score.

It uses the same graph, start nodes, questions and metrics as `evaluate.py`, so it compares with G-reasoner question by question. It needs only the standard library and runs locally in a few seconds. It was checked against `networkx.pagerank`: the largest difference was 2.4e-10, and the top 10 was the same on 39 of 39 questions.

## Hop analysis (E7)

Case study: `v2_q10`, "Which Johnson & Johnson segment sells the drug licensed from Genmab, and what were that segment's sales in fiscal 2025?"

The chain in the graph is Genmab A/S → DARZALEX → Oncology → Innovative Medicine → "$60,401 million" → its source chunks.

- `hop_case.py` (Colab) records each node's rank after every one of the 6 GNN layers, for chain nodes, gold chunks and one distractor. It reads them out with `layer_trace.py`.
- `plot_hop_case.py` draws the zero-shot and fine-tuned heatmaps side by side.

Outputs are in `results/hop_case/`, as `fig_hop_case_v2_q10.{png,pdf,md}` and the raw JSON.

Findings:
- **About one hop per layer.** The signal moves along the chain: DARZALEX rises at layers 2–3 and the segment at layers 4–5.
- **Fine-tuning keeps the gold chunks at the output.** Segment earnings rank 2 after fine-tuning vs 209 zero-shot, and the DARZALEX licence chunk ranks 7.
- **Zero-shot loses ground at the last layer.** It drops the sales note from rank 5 at layer 5 to rank 26 at layer 6.
- **The answer's Value node never ranks high**, at about rank 600–1,000 among Values. Retrieved Values should not be used as evidence on their own.
- **The readout matches the model's own output.** Its last layer equals the model output exactly (difference 0.0) for both models.

Caveat for the write-up: J&J, FY2025 and Revenue are also start nodes, and each is 1 hop from every gold chunk. So the figure gives two distances: hops from Genmab, which is the chain, and hops from the nearest start node, which is the shortcut.

## Per-question files (for the answer step)

Use the rows with `"k": 10`. Each file has 39 questions × k = 5 and 10.

| Exp. | File | `config` |
| --- | --- | --- |
| E2 | `results/zero_shot_fin10k_v1/per_question.jsonl` | `g-reasoner` |
| E3 | `results/finetuned_fin10k_v1/per_question.jsonl` | `g-reasoner-ft` |
| E4 | `results/ppr_fin10k_v1/per_question.jsonl` | `ppr` |

Each row has these fields:
- `retrieved`: the top-k chunk ids
- `start_nodes`
- `top_entities` and `top_attributes`: the top 5 each
- `hops`: gold-chunk distance from the start nodes
- `missing_facts`
- the per-question P, R, Hit and AllFacts
- timings

This is the same format as the vector baseline, so `answer_step/retrievals.py` reads the files directly.

## Files

| File | Runs on | What it does |
| --- | --- | --- |
| `g_reasoner_fin10k.ipynb` | Colab (T4) | The notebook: install, prepare, index, query, evaluate, diagnose, fine-tune, score the fine-tuned model, hop case |
| `prepare_data.py` | anywhere (stdlib) | Copies `data/graph/<graph>/processed/stage1` into a gfmrag data root and writes the `raw/documents.json` gfmrag requires |
| `entity_index.py` | anywhere (stdlib) | Rule-based start-node matcher, no LLM. Handles company aliases, Organization nodes, "fiscal 2025" and relative years ("last fiscal year"), and metric aliases; it skips generic nodes |
| `gfm_components.py` | Colab | Wraps `entity_index` as gfmrag's NER and entity-linking models |
| `vllm_limits.py` | Colab | Caps the vLLM embedding model's GPU memory (needed on a T4) |
| `index_graph.py` | Colab | Builds gfmrag's stage2 cache (node and relation embeddings) once per graph; prints the SFT pair count for a fine-tuning dataset |
| `query.py` | Colab | Loads G-reasoner (pretrained or a fine-tuned `--model` dir) and retrieves documents, entities and Values |
| `evaluate.py` | Colab | Scores retrieval on golden set v2 with `vector_rag_baseline/rag/metrics.py` and writes `per_question.jsonl` / `summary.json`. `--layer-log` writes the per-layer readout to `layers.jsonl` |
| `layer_trace.py` | Colab | Per-layer node scores (logit-lens readout through forward hooks, gfmrag unchanged), checked against the model output. `track()` follows named nodes |
| `diagnose.py` | Colab | Runs the golden questions four ways (all start nodes, no hub nodes, hubs only, dense only) in one model load |
| `make_synthetic_questions.py` | anywhere (stdlib) | Generates question / gold-subgraph pairs from the graph for fine-tuning (templates below) |
| `prepare_sft.py` | anywhere (stdlib) | Builds the `fin10k_v1_sft` gfmrag dataset (graph + synthetic train/test) and repeats relation pairs (`--relation-repeat`) |
| `configs/finetune_fin10k.yaml` | Colab | gfmrag SFT config for E3 |
| `plot_training.py` | anywhere (matplotlib) | E3 plots: training curves, golden Hit@10 by type, per-layer gold rank, generalization |
| `ppr.py` | anywhere (stdlib) | E4 Personalized PageRank, same inputs and output format as `evaluate.py` |
| `hop_case.py` | Colab | E7: per-layer rank of a question's chain nodes, gold chunks and distractors |
| `plot_hop_case.py` | anywhere (matplotlib) | E7 figure (zero-shot vs fine-tuned heatmap) and the same numbers as a markdown table |
| `compare_by_type.py` | anywhere (stdlib) | E1–E4 table by question type (Hit, P, R at k=5, 10); stops if the systems cover different questions |
| `gemini_ner.py`, `g_reasoner_gemini_ner_ablation.ipynb` | local / Colab | Oct ablation: Gemini picks the start nodes instead of the rules (`fin10k_v0`) |
| `requirements-colab.txt` | Colab | Pinned gfmrag version for the Python 3.12 venv |

**Results** (`results/`):

| Folder | What |
| --- | --- |
| `zero_shot_fin10k_v1/` | E2: per-question, summary, by type, `layers.jsonl` |
| `diagnose_fin10k_v1/` | E2 diagnosis, four start-node settings |
| `finetuned_fin10k_v1/` | E3: per-question, summary, by type, `layers.jsonl`, `relation_dev_{zero_shot,finetuned}/`, `training/`, `plots/` |
| `ppr_fin10k_v1/` | E4: per-question, summary, by type (with the zero-shot rows for comparison) |
| `hop_case/` | E7: per-model JSON and the figure |
| `e1_e4_by_type.md` | E1–E4 comparison table for the poster |
| `*_fin10k_v0/` | October runs on `fin10k_v0` (zero-shot, diagnose, probe, Gemini ablation) |

## Setup and how to run it

Everything that uses gfmrag (G-reasoner) runs on **Google Colab with a T4 GPU**. gfmrag needs Python 3.12, vLLM and CUDA, so the notebook installs it in its own Python 3.12 venv. Scripts marked "stdlib" or "matplotlib" in the file table run anywhere with plain Python 3.10+.

### What you need

- A Google account with Colab (the free T4 is enough) and some free space in Google Drive.
- Access to this GitHub repo.
- No paid API. The checkpoint (`rmanluo/G-reasoner-34M`) and the embedding model (Qwen3-Embedding-0.6B) download from Hugging Face without a token. E2, E3, E4 and E7 make no LLM calls. Only the optional Gemini ablation needs a key, see step 4.

### Step 1: put the repo in your Google Drive

Colab reads the code and the graph from Drive. Pick one:

| Option | How | Good for |
| --- | --- | --- |
| A. Upload | Clone or download the repo (`git clone https://github.com/memnaaaaa/financial-graphrag.git`), then upload the `financial-graphrag` folder to **My Drive** | simplest, one-off runs |
| B. Sync | Clone the repo and add its parent folder to **Google Drive for desktop** ("Folders from your computer"). It appears in Colab under `/content/drive/Othercomputers/` | editing locally and running on Colab (how this folder was developed) |
| C. Clone in Colab | The repo is private, so you need your own GitHub personal access token. Add it in Colab's **Secrets** panel as `GITHUB_TOKEN`. Then, in a new cell before section 5, run `from google.colab import userdata; tok = userdata.get("GITHUB_TOKEN")` and `!git clone https://{tok}@github.com/memnaaaaa/financial-graphrag.git /content/financial-graphrag`. Never paste the token into the notebook | no Drive copy of the code |

Notebook section 5 finds the repo automatically. If it finds none or several copies, set `REPO = "..."` at the top of that cell.

### Step 2: run the notebook (`g_reasoner_fin10k.ipynb`)

1. In Drive, right-click the notebook, then choose **Open with → Google Colaboratory**.
2. Choose **Runtime → Change runtime type → T4 GPU**.
3. Choose **Runtime → Run all**. Colab asks once for permission to mount Drive.

| Section | What it does | Time |
| --- | --- | --- |
| 1-4 | Python 3.12, venv with `gfmrag==2.0.0` + ninja, patch for gfmrag's PyG version check | ~5 min per new runtime |
| 5 | Mount Drive, find the repo | seconds |
| 6 | `prepare_data.py`: copy `fin10k_v1` into `My Drive/fin_greasoner_cache/data/` | seconds |
| 7 | `index_graph.py`: embed all 3,841 nodes with Qwen3 (stage2) | ~8 min the first time, then cached |
| 8 | `query.py`: load G-reasoner, retrieve for example questions | ~1-2 min |
| 9 | `evaluate.py`: zero-shot on golden v2 (E2), with `--layer-log` | ~2 min |
| 10 | `diagnose.py`: four start-node settings | ~2 min |
| 11 | `prepare_sft.py` + `index_graph.py`: fine-tuning dataset `fin10k_v1_sft` | ~1 min (reuses the embeddings) |
| 12 | Fine-tune with `configs/finetune_fin10k.yaml` (E3) | ~50 min |
| 13 | Score the fine-tuned model on golden v2 and on `relation_dev`; plots; hop case (E7) | ~5 min |

Results go to `My Drive/fin_greasoner_cache/results/<timestamp>/` and the fine-tuning run to `.../finetune/<timestamp>/`. Nothing is written into the repo automatically. To keep a run, copy its folder into `G-reasoner/results/<name>/` and commit it. Leave out the `.pth` weights.

To run a single step (after sections 1-5 in the same runtime), for example a new question:
`!{PYTHON} "{CODE}/query.py" --root "{DATA}" -q "What was Apple's R&D expense in fiscal 2025?"`
Add `--model <finetune dir>/pretrained` to use the fine-tuned model.

Note: from section 3 on, `!python` is the gfmrag venv, which has no matplotlib. Plot cells therefore call `/usr/bin/python3`.

### Step 3: scripts that run locally (no GPU)

```bash
cd G-reasoner
python3 ppr.py --out results/ppr_fin10k_v1                       # E4 (seconds)
python3 compare_by_type.py                                       # E1-E4 table -> results/e1_e4_by_type.md
python3 plot_hop_case.py results/hop_case/zero_shot_v2_q10.json results/hop_case/finetuned_v2_q10.json \
    --out results/hop_case/fig_hop_case_v2_q10                   # E7 figure (needs matplotlib)
python3 make_synthetic_questions.py --repo .. --graph fin10k_v1 --out synthetic/fin10k_v1
python3 entity_index.py ../data/graph/fin10k_v1/processed/stage1 "What were Apple's total net sales in fiscal 2025?"
```

`make_synthetic_questions.py` takes these options: `--graph`, `--test-tickers` (default MSFT), `--max-per-template` (default 600) and `--seed`. The same inputs always give byte-identical files.

### Step 4 (optional): the Gemini entity-matching ablation (`fin10k_v0`, Oct)

1. Get a free-tier key at https://aistudio.google.com/apikey. Do not add billing.
2. Put it in the repo-root `.env` as `GEMINI_API_KEY=<key>`. `.env` is git-ignored; `git check-ignore .env` should print `.env`. Never commit it.
3. Run `cd G-reasoner && python3 gemini_ner.py --repo .. --repeat 3`. It writes `results/gemini_ner_fin10k_v0/`.
4. Run `g_reasoner_gemini_ner_ablation.ipynb` on Colab. This step makes no Gemini calls.

### Running on another graph version (E8, E9)

Every script takes the graph name:
- `prepare_data.py --graph <name>`
- `--data-name <name>` for `index_graph.py`, `query.py`, `evaluate.py`, `diagnose.py` and `hop_case.py`
- `--graph <name>` for `ppr.py` and `make_synthetic_questions.py`

`prepare_data.py` deletes the cached embeddings when the graph changed. For E9, run `python3 ppr.py --graph fin10k_v0 --out results/ppr_fin10k_v0` locally. The G-reasoner part needs the notebook with `fin10k_v0`.

### Troubleshooting

| Symptom | Fix |
| --- | --- |
| Section 5: `repo copies found: NONE` | Drive may still be uploading; wait, or set `REPO` by hand |
| `CUDA out of memory` in section 7 | Check the runtime is a T4; `vllm_limits.py` caps vLLM at 35% (`GFM_VLLM_GPU_UTIL`, `GFM_VLLM_MAX_LEN`) |
| `No module named gfmrag` or PyG errors | Rerun sections 1-4 (a new runtime loses the venv) |
| `No module named matplotlib` in a plot cell | That cell ran the venv's python; use `/usr/bin/python3` |
| `no stage2 cache ... run index_graph.py first` | Run section 7 |
| `Attempting to unscale FP16 gradients` | Use `configs/finetune_fin10k.yaml` (float32); gfmrag's float16 path cannot train |
| Fine-tuning ignores new synthetic pairs | gfmrag reuses `train.pt`; rerun `prepare_sft.py`, which deletes it |
| First question very slow | Normal: the CUDA kernel compiles once per runtime |

## Problems found and how they were fixed

| Problem | Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError: raw/documents.json` | gfmrag always opens it, even when stage1 CSVs exist | `prepare_data.py` writes it from the document nodes |
| CUDA out of memory while embedding | vLLM reserves 90% of the GPU | `vllm_limits.py`: `gpu_memory_utilization=0.35`, `max_model_len=8192` |
| gfmrag crashes on PyG `2.8.0.post1` | Version parsed as integers | Notebook cell 4 patches the parser |
| Stale embeddings after a graph update | stage2 is keyed by embedding config, not graph contents | `prepare_data.py` deletes stage2 when stage1 changes |
| `IndexError` when a question names no entity | gfmrag reads `linked[mention][0]` | `PassThroughEL` returns a placeholder gfmrag skips |
| Fine-tuning fails on a T4 | No bfloat16; gfmrag's float16 path breaks the gradient scaler | float32 in `configs/finetune_fin10k.yaml` |
| Fine-tuned `config.json` rebuilds the graph cache without node features | `save_pretrained` writes missing dataset keys as null | The dataset keys are written out in the config |
| "Genmab A/S" not matched | The `/` split the name | Fixed in `entity_index.py` |
| `layers.jsonl` keeps only the top 10 per type, so chain nodes are missing | Size | `layer_trace.track()` + `hop_case.py` follow named nodes |
| First question's latency 2 to 23 s | The GNN kernel compiled on the first real question | Warm-up with the first golden question |

## Synthetic data (`synthetic/fin10k_v1/`)

Generated from graph paths with templates. Answers are computed from graph values.

| Template | Path | Pairs |
| --- | --- | --- |
| lookup | subject → Value → chunk | 600 |
| change | same subject and metric, two consecutive years | 600 |
| hierarchy | segment/business line → product → Value → chunk | 171 |
| share | product or segment revenue / company revenue | 266 |
| compare | same metric, two companies, same fiscal year | 164 |
| subsidiary | company → subsidiary → jurisdiction (Exhibit 21) | 446 |
| relation | one LLM-extracted relation (acquired, licensed_from, partners_with, ...) | 82 |
| relation_chain | two relations in a row | 15 |

The 2,344 pairs fall into four splits:

| Split | Pairs | What it holds |
| --- | --- | --- |
| train | 1,838 | J&J and Apple |
| test | 377 | anything involving Microsoft, held out and used to pick the epoch |
| relation_dev | 9 | relation questions on 10 held-out edges, the E3 dev check |
| golden_overlap | 117 | asks for a number or relation that is in a golden-set answer for the same company; kept out of everything |

Each record has gfmrag's SFT fields (`id`, `question`, `start_nodes`, `target_nodes`) plus `answer`, `template`, `hops`, `path`, `tickers` and `split`. `review.md` has sample pairs with their evidence line for hand checking. The older `fin10k_v0` set (2,135 pairs) is kept in `synthetic/fin10k_v0/`.

## Known issues

- **`fact_chunks` is missing** from `questions_v2.jsonl` on main, so AllFacts equals Hit in the graph runs. Mahua's baseline was scored with the field. Rerun `evaluate.py` and `ppr.py` once it is pushed.
- **Topics that are not in the graph.** Headcount, patents, litigation, the EU DMA, outsourcing and remaining performance obligations have no node. Those questions start only from company and year hubs, which explains most graph misses on descriptive-relation and cross-year questions. Tag them as "graph" failures in E6.
- **Value nodes rank poorly** even after fine-tuning (see E7). Retrieved Values should not be used as evidence on their own.
- **Small test set.** 39 questions, so one question moves Hit by 0.03 overall and by 0.25 on cross-year (n = 4). Do not tune settings on the golden set.
- **No dense fallback in PPR.** HippoRAG falls back to dense retrieval when a question has no start nodes; `ppr.py` does not. On v2 every question has at least one start node.

## Next steps (plan `pp_2`)

1. **Nov 24:** decide on E8 (G-reasoner's own graph from the 10-K text); otherwise it goes to the final report.
2. **Nov 25-26:** answer step on E2–E4 (Mohini), then failure tagging (E6, with Mohini); E9 `fin10k_v0` vs `v1`.
3. **Nov 25-30:** poster (draft Nov 25, numbers in Nov 27, freeze Nov 28, rehearsal Nov 29, poster Nov 30).
4. **Dec 2-7:** report sections: retriever, fine-tuning, PageRank, hop analysis.
