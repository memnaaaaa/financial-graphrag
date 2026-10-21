# financial-graphrag

CSC 8851 (Deep Learning) course project - a GraphRAG system over financial filings (SEC 10-Ks).

## Current state (Oct 21, 2026)

The pipeline runs end to end from raw filings to retrieval scores. Fine-tuning G-reasoner and
generating answers from the graph are next.

| Part | Folder | Status |
| --- | --- | --- |
| Filings and chunks (8 companies, 16 filings, 7,339 chunks) | `data/edgar_10k/`, `data/chunks/` | Done |
| Knowledge graph `fin10k_v0` (J&J, Apple, Microsoft; 3,618 nodes, 14,431 edges) | `data/graph/` | Done; 29 of 30 hand-checked edges correct |
| LLM-extracted relations (`fin10k_v1`) | `data/graph/` | All 623 chunks extracted; not yet merged into the graph |
| Vector-RAG baseline and 19-question golden set | `vector_rag_baseline/` | Runs end to end; 1 of 19 gold labels validated |
| G-reasoner retriever (zero-shot) and synthetic training pairs | `G-reasoner/` | Runs end to end; 2,135 training/test pairs ready |
| Preliminary report (CVPR format) | `report/` | Done (Oct 21) |

**Results so far** (11 golden questions covered by the graph): vector RAG (bge-small) Hit@5 0.91,
dense search over the graph's node embeddings 0.82, G-reasoner zero-shot 0.18. The pretrained graph
retriever finds the right filing but not the right passage, which is why fine-tuning comes next.
On all 19 questions, the vector baseline reaches Hit@10 0.79 with 42-47% of answers judged correct.
All numbers are preliminary until the golden set is validated.

**Known issues** (details in the folder READMEs and the preliminary report):
- `fin10k_v0` gives J&J's acquired in-process R&D charge ($109M in FY2025) instead of total R&D
  ($14,665M): two XBRL concepts were mapped to one metric. Affects golden questions q06, q14, q18.
- The graph covers 3 of 8 companies, so 8 of 19 golden questions cannot be scored on it yet.
- The golden set has no relation-chain questions (e.g. subsidiary -> license -> product) yet.
- The baseline answers with `gemini-2.5-flash-lite`, which new API keys can no longer use; the team
  needs to agree on one Gemini model.

### `data/edgar_10k/` - raw filings

10-K filings pulled from SEC EDGAR, plus the script used to fetch them.

- **Scope:** 8 companies in 8 industries (AAPL, MSFT, JPM, JNJ, XOM, PG, WMT, CAT), each with its two most recent 10-Ks as of 2026-10-05. That is 16 filings, 32 files (10-K main document + Exhibit 21 for each).
- **`filings_manifest.csv`** - files to download, with ticker, CIK, fiscal year, accession number, and URLs.
- **`download_edgar_10k.py`** - downloads and checks every file in the manifest into `raw/<TICKER>/<FY>/`, and logs results to `download_log.csv`.
- **`SOURCES.md`** - how filings were selected, links to EDGAR, and edge-case notes.
- **`raw/`** - the downloaded filings (~84 MB). Git-ignored; regenerate with the script.

```bash
cd data/edgar_10k
python download_edgar_10k.py --user-agent "Your Name your.email@example.edu"
```

### `data/chunks/` - text chunks

The filings split into **7,339 chunks (~2.19M tokens)**. One shared file feeds both the vector-RAG baseline and the graph.

- **`chunks.jsonl`** - one chunk per line, with metadata (ticker, fiscal year, section, etc.). Use this for the vector-RAG baseline.
- **`documents.json`** - same text as `{chunk_id: text}`, the input format G-reasoner expects. Git-ignored; it duplicates `chunks.jsonl`.
- **`build_chunks.py`** - builds the chunks from `raw/`.
- **`chunk_stats.csv`, `section_spans.csv`** - counts by section and where each section was found.

How chunks are made:

- HTML is cleaned, and table rows become one line each.
- Text is split by 10-K section (Item 1 to Item 16), and chunks never cross a section.
- Each chunk is at most 350 tokens (bge-small-en-v1.5 tokenizer), with about 50 tokens of overlap.
- Each chunk starts with a header naming the company, year, and section.

See `data/chunks/README.md` for fields, counts, known quirks, and rebuild steps.

### `data/graph/` - knowledge graph

The graph in gfmrag's "bring your own graph" format (`nodes.csv`, `relations.csv`, `edges.csv`),
which G-reasoner loads directly.

- **`fin10k_v0/`** - rule-based graph for J&J, Apple and Microsoft: subsidiaries from Exhibit 21;
  segments, products, regions and reported numbers from the inline XBRL tags (every number is its
  own "attribute" node); the chunks as document nodes; `is_mentioned_in` links to the chunks.
- **`build_graph.py`** / **`validate_graph.py`** - build the graph and check it the way gfmrag reads it.
- **`extract_relations_llm.py`** - Phase 2: Gemini extracts relations written in prose (licences,
  acquisitions, investments, ...) and adds them as `fin10k_v1`. The Gemini cache and `fin10k_v1`
  are git-ignored until the run is merged and checked.
- **`edge_check.csv`** - hand check of 30 random edges (29 correct).

See `data/graph/README.md` for the schema, counts and how to rebuild.

### `vector_rag_baseline/` - vector-RAG baseline

Dense retrieval (bge-small or DistilBERT, FAISS), optional cross-encoder reranking, Gemini answer
generation and an LLM judge, evaluated on a 19-question golden set with precision@k, recall@k,
hit@k and answer correctness. See `vector_rag_baseline/README.md` and `GOLDEN_SET.md`.

### `G-reasoner/` - graph retriever (G-reasoner-34M)

Runs the pretrained G-reasoner graph retriever (gfmrag 2.0.0) on `data/graph/fin10k_v0` in Colab, scores it on the golden questions with the vector baseline's metrics, and generates synthetic question/subgraph pairs for fine-tuning. Zero-shot it reaches hit@5 0.18 on the 11 covered golden questions (dense similarity on the same features: 0.82); choosing its start nodes with Gemini instead of rules gives identical results.

See `G-reasoner/README.md` (how to run, files, fixes, synthetic data).

### `report/` - report drafts

- **`prelim/`** - the preliminary report (CVPR format): `.tex`, `.pdf`, `refs.bib`, the CVPR style
  files and the schema figure. Build with pdflatex, bibtex, pdflatex, pdflatex.
- **`prelim_sections.tex`, `refs.bib`, `schema_figure.*`** - the Related Work, Method and graph
  tables as standalone sections, and the schema figure (TikZ source, PDF and PNG).

## Setup

```bash
pip install -r requirements.txt
python data/chunks/build_chunks.py
```

The download script uses only the standard library. Chunking needs `lxml` and `tokenizers`, plus the raw filings.

## Repo layout

```
.
├── README.md
├── CONTRIBUTIONS.md
├── requirements.txt
├── data/
│   ├── edgar_10k/
│   │   ├── download_edgar_10k.py
│   │   ├── filings_manifest.csv
│   │   ├── download_log.csv
│   │   ├── SOURCES.md
│   │   └── raw/                  # git-ignored
│   ├── chunks/
│   │   ├── README.md
│   │   ├── build_chunks.py
│   │   ├── chunks.jsonl
│   │   ├── documents.json        # git-ignored
│   │   ├── chunk_stats.csv
│   │   ├── section_spans.csv
│   │   └── bert-base-uncased-vocab.txt   # fallback tokenizer vocab
│   └── graph/                    # knowledge graph (see data/graph/README.md)
│       ├── build_graph.py, validate_graph.py, extract_relations_llm.py
│       ├── edge_check.csv        # hand check of 30 edges
│       ├── fin10k_v0/processed/stage1/   # nodes.csv, relations.csv, edges.csv
│       ├── fin10k_v1/            # git-ignored until finished
│       └── llm_cache/            # git-ignored (Gemini answers)
├── vector_rag_baseline/          # vector RAG + reranking baseline, golden questions, metrics
├── G-reasoner/                   # graph retriever: scripts, Colab notebooks, results, synthetic data
│   ├── README.md
│   └── docs/                     # INPUT_FORMAT.md (technical notes)
└── report/                       # report drafts and the preliminary report (prelim/)
```

## Next steps

1. Fix the J&J R&D mapping in `build_graph.py` and rebuild the graph; regenerate the synthetic pairs.
2. Merge the LLM-extracted relations (`fin10k_v1`) and hand-check 30 of them.
3. Extend the graph to all 8 companies.
4. Validate the golden set and add relation-chain questions.
5. Fine-tune G-reasoner on the synthetic pairs; compare zero-shot vs fine-tuned.
6. Build the subgraph-to-LLM answer step with an evidence trail; compare against vector RAG,
   reranking, LightRAG and HippoRAG 2.
