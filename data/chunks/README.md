# Text chunks of the 10-K corpus (`chunks.jsonl`)

Rebuilt Nov 18, 2026 from 6 filings in `data/edgar_10k/` (Johnson & Johnson, Apple and
Microsoft x 2 fiscal years: the 10-K main document plus Exhibit 21). **1,855 chunks, 573,200
tokens.** The other five downloaded companies are no longer chunked (the project now covers
these 3; `--tickers` brings them back). The same file is shared by every system:

- **Vector-RAG baseline:** embed the `text` field (bge-small-en-v1.5, max 512 tokens).
- **Graph (G-reasoner / QuadGraph document layer):** each chunk is one document node, named
  by its `chunk_id`. `documents.json` is the same chunks in the `raw/documents.json` format
  that gfmrag reads (`{chunk_id: text}`).

> `documents.json` has the same chunk text as `chunks.jsonl` but in G-reasoner’s `{chunk_id: text}` input format (no metadata): use `chunks.jsonl` for the vector-RAG baseline and `documents.json` as G-reasoner’s `raw/documents.json`.

## How chunks are made

1. **Clean the HTML.** Hidden inline-XBRL data, scripts, page numbers, running headers
   ("Item 7", "2025 Annual Report | 23") and tables of contents are removed. Each table row
   becomes one line with cells separated by ` | ` (e.g. `DARZALEX | 14,351 | 11,670 | 23.0`).
2. **Split by 10-K section.** The text is cut at the "Item 1." to "Item 16." headings. Text
   before Item 1 is `Cover`. JPMorgan and Exxon put their MD&A and financial statements in
   a separate section at the end of the filing; those parts are labeled Item 7 and Item 8.
   Chunks never cross a section boundary.
3. **Pack into chunks of at most 350 tokens**, counting the header line, measured with the
   bge-small-en-v1.5 tokenizer (BERT uncased WordPiece). Whole paragraphs and table rows
   are kept together. Only a paragraph too long for one chunk is split, at sentence ends.
4. **Overlap of about 50 tokens.** Each chunk starts by repeating the last ~50 tokens of the
   chunk before it, in the same section. That way a fact that falls right at a cut, like a
   sentence or table row split across two chunks, appears whole in at least one of them.
   Inside tables, whole rows are repeated rather than half rows. A chunk that starts in the
   middle of a table also repeats the table's column-header row, so numbers keep their years.
5. **Header line.** Every `text` begins with one line naming the company, the fiscal year,
   when that year ended, and the section, e.g. `Apple Inc. (AAPL) | Form 10-K annual report
   for fiscal year 2025 (FY2025), fiscal year ended September 27, 2025 | Item 7.
   Management's Discussion and Analysis of ...`. Many passages never name the company or
   the year themselves; the year and end date in words keep retrieval from mixing up
   companies and, especially, the two years of the same company (Nov 18 fix).
6. **Chunk ids and bodies are frozen.** Chunks are still cut using the short Oct header
   (`Apple Inc. (AAPL) | FY2025 Form 10-K | Item 7. ...`); only the written header is the long
   one. So every `chunk_id` and every passage below the header is the same as in the Oct
   build, and the questions' `gold_chunk_ids` stay valid. Before writing, the script compares
   with the existing `chunks.jsonl` and stops without writing anything if any id or body
   changed (`--no-check` skips this, e.g. when you change the chunk size on purpose). With
   the longer header a chunk can be up to 367 tokens, still under the 512 limit of bge-small.
7. **Year twins.** Most 10-K text is repeated almost word for word the next year. Each chunk
   gets `twin_chunk_id`: the most similar chunk of the same company and section in the other
   fiscal year, if their bodies share at least 80% of their words (Jaccard on word sets;
   `--twin-threshold`). 750 of 1,855 chunks have a twin. Use it to see whether a retrieval or
   answer error was a wrong-year mix-up.

**Used by the graph:** `data/graph/build_graph.py` calls `html_to_blocks(path, track_facts=True)`
and `find_sections` from this script to find the section and chunk where each inline-XBRL number
is printed (the Value source fields). The flag only records the tags' ids; the chunks are the same.

## Fields (one JSON object per line)

| Field | Example | Meaning |
| --- | --- | --- |
| `chunk_id` | `JNJ_FY2025_ITEM7_0009` | Unique id: ticker, fiscal year, section, running number. Also the document-node name in the graph |
| `ticker`, `company`, `cik` | `JNJ`, `Johnson & Johnson`, `200406` | Filer |
| `fiscal_year`, `period_end`, `filing_date` | `FY2025`, `2025-12-28`, `2026-02-11` | Company's own fiscal-year label and dates |
| `accession` | `0000200406-26-000016` | EDGAR filing id |
| `document` | `10-K` or `EX-21` / `EX-21.1` | Which file in the filing |
| `section`, `section_title` | `Item 7`, `Management's Discussion and Analysis of ...` | 10-K section (`Cover`, `Item 1` ... `Item 16`, `Exhibit 21`) |
| `chunk_index` | `9` | Position within the section, from 0 |
| `n_tokens` | `332` | Tokens in `text` (long header included) without [CLS]/[SEP]; max 367 in this build |
| `has_table` | `true` | Chunk contains table rows |
| `source_url` | EDGAR link | Original document |
| `twin_chunk_id`, `twin_similarity` | `JNJ_FY2024_ITEM7_0009`, `0.93` | Near-identical chunk of the other fiscal year (Jaccard >= 0.8), else `null` |
| `text` | header line + passage | What to embed / show the LLM |

## Counts

| Ticker | FY | Chunks | Tokens | Chunks with tables | Chunks with a year twin |
| --- | --- | --- | --- | --- | --- |
| AAPL | FY2025 | 198 | 59,949 | 73 | 77 |
| AAPL | FY2024 | 194 | 58,934 | 73 | 77 |
| MSFT | FY2026 | 300 | 92,338 | 103 | 127 |
| MSFT | FY2025 | 290 | 89,166 | 100 | 127 |
| JNJ | FY2025 | 433 | 135,837 | 210 | 171 |
| JNJ | FY2024 | 440 | 136,976 | 198 | 171 |
| **Total** | | **1,855** | **573,200** | **757** | **750** |

Chunk counts are the same as in the Oct build; token counts are higher only because of the
longer header.

`chunk_stats.csv` breaks this down by section. `section_spans.csv` shows where each section
was found in each filing.

Known gaps and quirks:
- **Spacing:** some numbers keep odd spacing from the source HTML, e.g. `$( 651 ) million`.

## Rebuilding

Needs Python 3.8+, `lxml` and `tokenizers` (`pip install lxml tokenizers`), plus the raw
filings (`python data/edgar_10k/download_edgar_10k.py ...` first). From the repo root:

```
python data/chunks/build_chunks.py              # defaults: JNJ AAPL MSFT, 350 tokens, 50 overlap
python data/chunks/build_chunks.py --tickers JNJ AAPL MSFT JPM XOM PG WMT CAT --no-check   # all 8
python data/chunks/build_chunks.py --max-tokens 300 --overlap 40 --no-check
```

If the Hugging Face Hub is reachable, the official `BAAI/bge-small-en-v1.5` tokenizer is used.
Otherwise the script uses the bundled `bert-base-uncased-vocab.txt`, the same 30,522-token
vocabulary (copied from microsoft/SDNet on GitHub, sha256 `07eced37...38a3`).

`documents.json` is git-ignored because it duplicates `chunks.jsonl`. To recreate it without
rebuilding:

```
python -c "import json; json.dump({c['chunk_id']: c['text'] for c in map(json.loads, open('data/chunks/chunks.jsonl'))}, open('documents.json', 'w'))"
```
