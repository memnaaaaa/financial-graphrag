# Text chunks of the 10-K corpus (`chunks.jsonl`)

Built Oct 8, 2026 from the 16 filings in `data/edgar_10k/` (8 companies x 2 fiscal years: the
10-K main document plus Exhibit 21). **7,339 chunks, about 2.19 million tokens.** The same
file is shared by every system:

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
5. **Header line.** Every `text` begins with a line naming the company, year and section,
   e.g. `Johnson & Johnson (JNJ) | FY2025 Form 10-K | Item 7. Management's Discussion and
   Analysis of ...`. Many passages never name the company themselves, so this keeps
   retrieval from mixing up companies. It counts toward the 350 tokens.

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
| `n_tokens` | `332` | Tokens in `text` without [CLS]/[SEP]; max 349 in this build |
| `has_table` | `true` | Chunk contains table rows |
| `source_url` | EDGAR link | Original document |
| `text` | header line + passage | What to embed / show the LLM |

## Counts

| Ticker | FY | Chunks | Tokens | Chunks with tables |
| --- | --- | --- | --- | --- |
| AAPL | FY2025 | 198 | 56,385 | 73 |
| AAPL | FY2024 | 194 | 55,442 | 73 |
| MSFT | FY2026 | 300 | 86,938 | 103 |
| MSFT | FY2025 | 290 | 83,946 | 100 |
| JPM | FY2025 | 1,168 | 360,262 | 708 |
| JPM | FY2024 | 1,195 | 368,512 | 714 |
| JNJ | FY2025 | 433 | 128,043 | 210 |
| JNJ | FY2024 | 440 | 129,056 | 198 |
| XOM | FY2025 | 440 | 134,040 | 322 |
| XOM | FY2024 | 467 | 141,204 | 292 |
| PG | FY2026 | 302 | 89,273 | 139 |
| PG | FY2025 | 301 | 88,586 | 134 |
| WMT | FY2026 | 354 | 100,128 | 142 |
| WMT | FY2025 | 365 | 103,134 | 141 |
| CAT | FY2025 | 449 | 134,625 | 221 |
| CAT | FY2024 | 443 | 133,936 | 216 |
| **Total** | | **7,339** | **2,193,510** | **3,786** |

`chunk_stats.csv` breaks this down by section. `section_spans.csv` shows where each section
was found in each filing.

Known gaps and quirks:
- **Missing items:** JPMorgan's 10-K has no Item 16 and Exxon's has no Item 6. Every other
  filing has all 23 items.
- **Content after the relocated sections:** for JPMorgan and Exxon, anything that follows the
  financial statements at the end of the filing (e.g. JPMorgan's glossary) is also labeled
  Item 8.
- **Spacing:** some numbers keep odd spacing from the source HTML, e.g. `$( 651 ) million`.

## Rebuilding

Needs Python 3.8+, `lxml` and `tokenizers` (`pip install lxml tokenizers`), plus the raw
filings (`python data/edgar_10k/download_edgar_10k.py ...` first). From the repo root:

```
python data/chunks/build_chunks.py              # defaults: 350 tokens, 50 overlap
python data/chunks/build_chunks.py --max-tokens 300 --overlap 40
```

If the Hugging Face Hub is reachable, the official `BAAI/bge-small-en-v1.5` tokenizer is used.
Otherwise the script uses the bundled `bert-base-uncased-vocab.txt`, the same 30,522-token
vocabulary (copied from microsoft/SDNet on GitHub, sha256 `07eced37...38a3`).

`documents.json` is git-ignored because it duplicates `chunks.jsonl`. To recreate it without
rebuilding:

```
python -c "import json; json.dump({c['chunk_id']: c['text'] for c in map(json.loads, open('data/chunks/chunks.jsonl'))}, open('documents.json', 'w'))"
```
