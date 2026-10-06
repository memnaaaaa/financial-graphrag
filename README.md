# financial-graphrag

CSC 8851 (Deep Learning) course project — a GraphRAG system over financial filings (SEC 10-Ks).

## Current state

The project is in the data-collection stage. Nothing else (graph construction, retrieval, modeling) has been built yet.

### `data/edgar_10k/`

A corpus of 10-K filings pulled from SEC EDGAR, plus the script used to fetch them.

- **Scope:** 8 companies across 8 different industries (AAPL, MSFT, JPM, JNJ, XOM, PG, WMT, CAT), each with its two most recent annual 10-K filings as of 2026-10-05 (16 filings, 32 files total: the 10-K main document + Exhibit 21 subsidiary list for each).
- **`filings_manifest.csv`** — the list of files to download, with ticker, CIK, fiscal year, accession number, and source URLs for each.
- **`download_edgar_10k.py`** — standard-library-only script that downloads every file in the manifest into `raw/<TICKER>/<FY>/`, verifies each one (10-K cover tags match the expected form/fiscal year/CIK; Exhibit 21 mentions subsidiaries), and logs the result (including a SHA-256 per file) to `download_log.csv`.
- **`download_log.csv`** — one row per downloaded file: expected vs. actual byte count, content-check result, hash, and timestamp.
- **`SOURCES.md`** — full provenance: how the companies and filings were selected, the filing table with links to EDGAR, and notes on edge cases (e.g. the XOM/ExxonMobil Holdings naming quirk, JPMorgan's paged filing history).
- **`raw/`** — the downloaded filings themselves (~84 MB). **Not committed** — git-ignored, since it's regenerable from the manifest.

To (re-)download the raw filings:

```bash
cd data/edgar_10k
python download_edgar_10k.py --user-agent "Your Name your.email@example.edu"
```

See `data/edgar_10k/SOURCES.md` for full details on what's in the corpus and why.

## Repo layout

```
.
├── README.md
└── data/
    └── edgar_10k/
        ├── download_edgar_10k.py
        ├── filings_manifest.csv
        ├── download_log.csv
        ├── SOURCES.md
        ├── .gitignore         # ignores raw/
        └── raw/               # downloaded filings (git-ignored, not committed)
```

## Next steps

Not yet started: document parsing/chunking, graph construction, retrieval, and the GraphRAG pipeline itself.
