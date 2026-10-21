# financial-graphrag

CSC 8851 (Deep Learning) course project - a GraphRAG system over financial filings (SEC 10-Ks).

## Current state

Data collection and chunking are done. The vector-RAG baseline (`vector_rag_baseline/`), the first
knowledge graph for 3 companies (`data/graph/fin10k_v0`, see `data/graph/README.md`) and zero-shot
G-reasoner retrieval (`G-reasoner/`) run end to end. Fine-tuning and LLM answer generation are next.

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

### `G-reasoner/` - graph retriever (G-reasoner-34M)

Runs the pretrained G-reasoner graph retriever (gfmrag 2.0.0) on `data/graph/fin10k_v0` in Colab, scores it on the golden questions with the vector baseline's metrics, and generates synthetic question/subgraph pairs for fine-tuning. Zero-shot it reaches hit@5 0.18 on the 11 covered golden questions (dense similarity on the same features: 0.82); choosing its start nodes with Gemini instead of rules gives identical results.

See `G-reasoner/README.md` (how to run, files, fixes) and `G-reasoner/report/` (tables, pipeline figure and method text for the report).

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
│       └── fin10k_v0/processed/stage1/   # nodes.csv, relations.csv, edges.csv
├── vector_rag_baseline/          # vector RAG + reranking baseline, golden questions, metrics
└── G-reasoner/                   # graph retriever: scripts, Colab notebooks, results, synthetic data
    ├── README.md
    ├── docs/                     # INPUT_FORMAT.md (technical notes)
    └── report/                   # report drafts: intro_method.md/.tex, REPORT_NOTES.md
```

## Next steps

Extend the graph to all 8 companies and LLM-extracted relations (`fin10k_v1`), fine-tune G-reasoner
on synthetic questions, build subgraph pruning and LLM answers with an evidence trail, and compare
against the baselines (see each folder's README).
