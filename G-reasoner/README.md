# G-reasoner: graph retriever (workstream C)

Owner: Rida. This folder runs the pretrained **G-reasoner-34M** graph retriever (gfmrag 2.0.0) on the
team's knowledge graph (`data/graph/fin10k_v0`), scores it on the team's golden questions with the
vector baseline's metrics, explains why zero-shot retrieval fails, and generates the synthetic
question/subgraph pairs for fine-tuning.

**Status (Oct 21, 2026):** zero-shot pipeline runs end to end on a Colab T4; zero-shot results and a
diagnosis are in `results/`; 2,135 synthetic training/test pairs are in `synthetic/fin10k_v0/`; an
ablation with Gemini choosing the start nodes (instead of the rule-based matcher) is in
`results/gemini_ner_fin10k_v0/` and `results/ner_ablation_fin10k_v0/`.
Fine-tuning, subgraph pruning and LLM answer generation are next (plan window Oct 22 to Nov 11).

- **Writing the report?** Facts, tables, the pipeline figure and ready-to-paste method text:
  [`report/`](report/) (start with `report/README.md`)
- **Running the code?** [Setup and how to run it](#setup-and-how-to-run-it): put the repo in Google
  Drive, open `g_reasoner_fin10k.ipynb` in Colab on a T4, Run all (~15 min the first time).
- **Input format** and how our graph maps onto it: [`docs/INPUT_FORMAT.md`](docs/INPUT_FORMAT.md)

## Headline result

On the 11 golden questions whose gold chunks are in `fin10k_v0` (J&J, Apple, Microsoft):

| System | Hit@5 | R@5 | Hit@10 | R@10 |
| --- | --- | --- | --- | --- |
| Vector RAG, bge-small (Mahua, `full_run_2`, re-scored on the same 11) | 0.91 | 0.41 | 1.00 | 0.56 |
| Vector RAG, bge-small + rerank (same) | 0.82 | 0.42 | 0.91 | 0.60 |
| Dense similarity on G-reasoner's own node features (Qwen3-Embedding-0.6B) | 0.82 | 0.60 | 0.91 | 0.76 |
| **G-reasoner-34M, zero-shot** | **0.18** | **0.04** | **0.18** | **0.04** |

Zero-shot G-reasoner finds the right company but ranks generic chunks first. The node embeddings
alone work well, so the data pipeline is sound; the pretrained GNN's ranking does not transfer to
this graph. This motivates fine-tuning. Details and caveats: `report/REPORT_NOTES.md`.

### Ablation: rule-based vs Gemini start nodes

gfmrag's default finds start nodes with an LLM. We tested whether that would change anything by
letting Gemini (`gemini-3.5-flash-lite`, temperature 0) pick the start nodes from the list of all 669
entity names, with everything else unchanged.

| | Rule-based (`entity_index.py`) | Gemini |
| --- | --- | --- |
| Same start nodes as the other, 11 golden questions | 11 / 11 | 11 / 11 |
| Hit@5 / Hit@10 (G-reasoner, 11 golden questions) | 0.18 / 0.18 | 0.18 / 0.18 (identical retrieved lists, 22 of 22) |
| Matching time per question (Colab) | 3.5 ms | 1,290 ms (one API call) |
| Matching + retrieval per question | ~110 ms | ~1,410 ms (about 13x slower) |
| Same answer on 3 repeated calls | always | 11/11 golden, 7/9 paraphrases |
| 9 paraphrased probe questions | Gemini better on 2, rules better on 2, mixed 2, same 3 | |

So the rule-based matcher is not what limits zero-shot retrieval, and Gemini adds about 1.3 s per
question plus rate limits and some run-to-run variation. We keep the rule-based matcher (training and
test questions are matched the same way, reproducibly). Source: `results/gemini_ner_fin10k_v0/`
(matching), `results/ner_ablation_fin10k_v0/` (retrieval), notebook `g_reasoner_gemini_ner_ablation.ipynb`.

## Files

| File | Runs on | What it does |
| --- | --- | --- |
| `g_reasoner_fin10k.ipynb` | Colab (T4) | The notebook: install, mount Drive, prepare, index, query, evaluate, diagnose |
| `prepare_data.py` | anywhere (stdlib) | Copies `data/graph/<graph>/processed/stage1` into a gfmrag data root and writes the `raw/documents.json` gfmrag requires |
| `entity_index.py` | anywhere (stdlib) | Finds graph entities named in a question ("Apple" → `Apple Inc.`, "fiscal 2025" → `FY2025 (AAPL)`, "net sales" → `Revenue`). No LLM |
| `gfm_components.py` | Colab | Wraps `entity_index` as gfmrag's NER and entity-linking models |
| `vllm_limits.py` | Colab | Caps the vLLM embedding model's GPU memory (needed on a T4, see below) |
| `index_graph.py` | Colab | Builds gfmrag's stage2 cache (node and relation embeddings) once per graph |
| `query.py` | Colab | Loads G-reasoner once and retrieves documents, entities and numbers for questions |
| `evaluate.py` | Colab | Scores document retrieval on the golden set with `vector_rag_baseline/rag/metrics.py`; writes the baseline's `per_question.jsonl` / `summary.json` format |
| `diagnose.py` | Colab | Runs the golden questions four ways (all start nodes, no hub nodes, hubs only, dense only) in one model load |
| `gemini_ner.py` | locally (stdlib, Gemini API) | Ablation: Gemini picks the start nodes for the golden and probe questions; compares with the rule matcher and times both. Needs `GEMINI_API_KEY` in the repo-root `.env` |
| `g_reasoner_gemini_ner_ablation.ipynb` | Colab (T4) | Runs the golden-set evaluation with rule-based and with Gemini start nodes in one runtime and compares them |
| `make_synthetic_questions.py` | anywhere (stdlib) | Generates question / gold-subgraph pairs from the graph for fine-tuning |
| `requirements-colab.txt` | Colab | Pinned gfmrag version for the Python 3.12 venv |
| `results/` | | Zero-shot, diagnose, probe and Gemini-matching ablation outputs (copied from Drive) |
| `synthetic/fin10k_v0/` | | `train.json`, `test.json`, `golden_overlap.json`, `stats.json`, `review.md` |

## Setup and how to run it

Everything that uses gfmrag (G-reasoner) runs on **Google Colab with a T4 GPU**: gfmrag needs
Python 3.12, vLLM and CUDA, so the notebooks install it in their own Python 3.12 venv. The scripts
marked "stdlib" in the file table run anywhere with plain Python 3.10+ and need no install.

### What you need

- A Google account with Colab (the free T4 GPU is enough) and some free space in Google Drive.
- Access to this GitHub repo.
- Only for the Gemini ablation: a Gemini API key (free tier), see step 4.
- No OpenAI or other paid API. The G-reasoner checkpoint (`rmanluo/G-reasoner-34M`) and the embedding
  model (Qwen3-Embedding-0.6B) download from Hugging Face automatically, without a token.

### Step 1: put the repo in your Google Drive

Colab reads the code and the graph from Drive. Pick one:

| Option | How | Good for |
| --- | --- | --- |
| A. Upload | Clone or download the repo on your computer (`git clone https://github.com/memnaaaaa/financial-graphrag.git`), then upload the `financial-graphrag` folder to **My Drive** | simplest, one-off runs |
| B. Sync | Clone the repo on your computer and add its parent folder to **Google Drive for desktop** ("Folders from your computer"); it appears in Colab under `/content/drive/Othercomputers/` | editing code locally and running on Colab (how this folder was developed) |
| C. Clone in Colab | The repo is private, so you need your own GitHub personal access token. Add it in Colab's **Secrets** panel (key icon) as `GITHUB_TOKEN`, then in a new cell before section 5: `from google.colab import userdata; tok = userdata.get("GITHUB_TOKEN")` and `!git clone https://{tok}@github.com/memnaaaaa/financial-graphrag.git /content/financial-graphrag`. Never paste the token into the notebook itself | no Drive copy of the code (the clone is lost when the runtime resets) |

Notebook section 5 finds the repo automatically in all three places. If it finds none or several
copies, set `REPO = "..."` at the top of that cell.

### Step 2: run the main notebook (`g_reasoner_fin10k.ipynb`)

1. Open the notebook from Drive in Colab: right-click it, then **Open with → Google Colaboratory**.
2. **Runtime → Change runtime type → T4 GPU**.
3. **Runtime → Run all.** Colab asks once for permission to mount Drive.

| Section | What it does | Time |
| --- | --- | --- |
| 1-4 | Installs Python 3.12, a venv with `gfmrag==2.0.0` + ninja, and patches gfmrag's PyG version check | ~5 min per new runtime |
| 5 | Mounts Drive, finds the repo, checks the files are there | seconds |
| 6 | `prepare_data.py`: copies the graph into `My Drive/fin_greasoner_cache/data/` and writes the `raw/documents.json` gfmrag needs | seconds |
| 7 | `index_graph.py`: embeds all 3,618 nodes with Qwen3 (stage2) | ~8 min the first time, then cached (seconds) |
| 8 | `query.py`: loads G-reasoner and retrieves for 4 example questions | ~1-2 min (first query loads a CUDA kernel) |
| 9 | `evaluate.py`: scores the 11 golden questions the graph covers | ~2 min |
| 10 | `diagnose.py`: the same questions four ways (all start nodes, no hub nodes, hubs only, dense only) | ~2 min |

**Results** go to `My Drive/fin_greasoner_cache/results/<timestamp>/` (`per_question.jsonl`,
`summary.json`), never into the repo automatically. To keep a run, copy that folder into
`G-reasoner/results/<name>/` and commit it. Expected numbers: Hit@5 0.18 / Hit@10 0.18 (section 9),
the diagnose table in `report/REPORT_NOTES.md` (section 8).

**Run a single step instead** (after sections 1-5 in the same runtime), e.g. a new question:
`!{PYTHON} "{CODE}/query.py" --root "{DATA}" -q "What was Apple's R&D expense in fiscal 2025?"`

### Step 3: scripts that run locally (no GPU)

```bash
cd G-reasoner
python3 prepare_data.py --repo .. --root /tmp/gfm_data          # check the graph converts
python3 entity_index.py ../data/graph/fin10k_v0/processed/stage1 "What were Apple's total net sales in fiscal 2025?"
python3 make_synthetic_questions.py --repo .. --out synthetic/fin10k_v0   # regenerate synthetic pairs (seconds)
```

`make_synthetic_questions.py` options: `--graph` (folder under `data/graph/`), `--test-tickers`
(companies held out for test, default MSFT), `--max-per-template` (default 600), `--seed`. The same
inputs always give byte-identical files.

### Step 4 (optional): the Gemini entity-matching ablation

1. **Get a key:** go to https://aistudio.google.com/apikey, sign in, **Create API key**. Do not add
   billing; the free tier is enough (the run is 60 calls). Use your own key, not a teammate's, so you
   do not share their rate limit.
2. **Save it** in a file named `.env` in the repo root (the folder with the main `README.md`), with
   one line `GEMINI_API_KEY=<your key>` (no spaces or quotes). Use an editor or `nano .env` in a
   normal terminal, not a shared chat or notebook. `.env` is git-ignored; check with
   `git check-ignore .env`, which should print `.env`.
3. **Run on your computer:** `cd G-reasoner && python3 gemini_ner.py --repo .. --repeat 3`
   (about 1-3 min, longer if the free tier rate-limits; answers are saved after every question, so a
   rerun continues where it stopped). It writes `results/gemini_ner_fin10k_v0/`.
4. **Run `g_reasoner_gemini_ner_ablation.ipynb` on Colab** (T4, Run all, ~15 min). It makes no Gemini
   calls and needs no key: it reads the saved start nodes and evaluates G-reasoner with both matchers
   in one runtime. Section 11 prints the comparison.

Model: `gemini-3.5-flash-lite` (`--model` to change). `gemini-2.5-flash-lite` returns HTTP 404 for new
API keys.

### Running on a new graph version (e.g. `fin10k_v1` or the 8-company graph)

Every script takes the graph name: `prepare_data.py --graph <name>`, then `--data-name <name>` for
`index_graph.py`, `query.py`, `evaluate.py`, `diagnose.py`, and `--graph <name>` for
`make_synthetic_questions.py` and `gemini_ner.py`. In the notebooks, replace `fin10k_v0` in the
cells. `prepare_data.py` deletes the cached embeddings when the graph changed, so section 7 re-embeds
it. Rerun zero-shot on the new graph before comparing it with anything trained on that graph.

### Troubleshooting

| Symptom | Fix |
| --- | --- |
| Section 5: `repo copies found: NONE` | Drive may still be uploading; wait, or set `REPO` by hand |
| Section 5: several copies found | set `REPO` to the one you want |
| `CUDA out of memory` in section 7 | make sure the runtime is a T4 and nothing else uses the GPU; `vllm_limits.py` caps vLLM at 35% (env vars `GFM_VLLM_GPU_UTIL`, `GFM_VLLM_MAX_LEN`) |
| `No module named gfmrag` or PyG errors | rerun sections 1-4 (a new runtime loses the venv) |
| `no stage2 cache ... run index_graph.py first` | run section 7 |
| First question very slow | normal: G-reasoner loads (or compiles) its CUDA kernel once per runtime |
| `GEMINI_API_KEY not set` | `.env` missing, empty or not in the repo root (`wc -c .env` should not be 0) |
| Gemini HTTP 429 / 403 | free-tier rate limit; the script waits and retries |

## Problems found and how they were fixed

| Problem | Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError: raw/documents.json` | gfmrag always opens `<data>/<name>/raw/documents.json`, even when stage1 CSVs exist | `prepare_data.py` writes it from the document nodes (`{chunk_id: content}`) |
| CUDA out of memory while embedding the graph | vLLM reserves 90% of the GPU; on a T4 it uses FlexAttention, whose block mask grows with the KV cache | `vllm_limits.py` sets `gpu_memory_utilization=0.35`, `max_model_len=8192` (longest node text is about 750 tokens) |
| gfmrag crashes on PyG versions like `2.8.0.post1` | version string parsed as integers | notebook cell 4 patches the parser |
| Possible double vLLM instance (out of memory) | `from_index` builds stage2 and then starts a second embedding model | `index_graph.py` builds stage2 in its own process first |
| Stale embeddings after a graph update | stage2 cache is keyed by the embedding config, not by graph contents | `prepare_data.py` deletes stage2 when stage1 changes |
| `IndexError` when a question names no known entity | gfmrag reads `linked[mention][0]` | `PassThroughEL` returns a placeholder that gfmrag skips, so the query runs without start nodes |
| Paths with spaces (`Othercomputers/My Mac/...`) | unquoted shell arguments | quoted paths in the notebook |
| First question's latency 2 to 23 s | the warm-up query had no entities, so the GNN (and its CUDA kernel) only ran on the first real question | `evaluate.py` / `diagnose.py` warm up with the first golden question. Runs before this fix: leave out the first question's time |
| `gemini-2.5-flash-lite` returns HTTP 404 | no longer offered to new API keys (Oct 2026) | `gemini_ner.py` uses `gemini-3.5-flash-lite` (as `data/graph/extract_relations_llm.py` does) |

## Synthetic data (`synthetic/fin10k_v0/`)

Generated from graph paths with templates, answers computed from graph values:

| Template | Path | Pairs |
| --- | --- | --- |
| lookup | subject → Value → chunk | 600 |
| change | same subject and metric, two consecutive years | 600 |
| hierarchy | segment/business line → product → Value → chunk | 123 |
| share | product or segment revenue / company revenue | 219 |
| compare | same metric, two companies, same fiscal year | 147 |
| subsidiary | company → subsidiary → jurisdiction (Exhibit 21) | 446 |

Splits: **train 1,734** (J&J and Apple only), **test 350** (anything involving Microsoft, which is
held out), **golden_overlap 51** (questions asking for a number that is in a golden-set answer for
the same company; kept out of both, so golden questions stay unseen). Each record has gfmrag's SFT
fields (`id`, `question`, `start_nodes`, `target_nodes`) plus `answer`, `template`, `hops`, `path`
(the gold edges), `tickers`, `split`. `review.md` has 40 pairs with the evidence line for hand
checking; a first review pass found and fixed wording problems and the J&J R&D data error below.

## Known issues to share with the team

- **Graph data error (Mohini):** in `fin10k_v0`, J&J's "research and development expense" Values are
  really "Charges for acquired in-process research and development" ($109M FY2025, $1,841M FY2024;
  `JNJ_FY2025_ITEM8_0008`). J&J's actual total R&D ($14,665M in 2025) is missing. Excluded from the
  synthetic data via `KNOWN_BAD_VALUES`; affects golden questions q06, q14, q18.
- **Coverage:** `fin10k_v0` has 3 of 8 companies, so 8 of 19 golden questions (q02, q04, q05, q07,
  q12, q13, q17, q19) cannot be scored for G-reasoner yet.
- **Golden labels:** only q01 is validated (see `vector_rag_baseline/GOLDEN_SET.md`); all numbers are
  preliminary, and 11 questions means one question moves hit@k by 0.09.
- **Rule matcher limits:** it picks the expected start nodes on the 11 golden questions, but on 9
  paraphrases written to stress it, it mapped "sales and marketing" to Revenue and "operating profit"
  to Net income, and does not resolve "last year" / "most recent fiscal year"
  (`results/gemini_ner_fin10k_v0/start_nodes.jsonl`). Fix the alias table before regenerating the
  synthetic data. Gemini fixes some of these but picks wrong fiscal years for relative dates.
- **Gemini model versions:** the vector baseline generates answers with `gemini-2.5-flash-lite`,
  which new API keys can no longer use. Agree on one model before comparing answer correctness.
- **Value nodes rank poorly:** G-reasoner's top `attribute` results barely depend on the question,
  so retrieved numbers should not be used as evidence until after fine-tuning.

## Next steps (plan windows)

1. **Oct 22 to 28:** regenerate synthetic pairs when the 8-company graph is ready (hold out 2
   companies); optionally reword questions with an LLM; write the fine-tuning config (float16/32 on a
   T4 instead of bfloat16, start from `rmanluo/G-reasoner-34M`).
2. **Oct 29 to Nov 11:** fine-tune; compare zero-shot vs fine-tuned on dev; tune learning rate and
   number of pairs; ablate the dense-distillation loss and the chunk-header links.
3. **Nov 12 to 20:** amount-of-data ablation, error analysis of about 30 failures.
4. **LLM interface:** subgraph from the retrieved nodes and their edges, passed to the generator with
   an evidence trail, answered by Gemini (team decision; model version to agree with the baseline, see
   known issues). The plan lists this under Mohini for Oct 29 to Nov 11; confirm who builds it.
