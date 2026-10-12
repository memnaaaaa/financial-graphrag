# Golden set

The golden set is the list of questions used to evaluate retrieval, with the **gold chunk ids** that a retriever should
find and a **gold answer** that the LLM judge compares generated answers against.

## Status: 1 of 19 questions validated

| | Count |
|---|---|
| Questions | 19 (9 single-fact, 5 multi-hop within one company, 5 cross-company) |
| Gold labels validated by an independent LLM labeler | **1** (q01) |
| Gold labels from pattern matching, **not yet verified** | **18** |
| Labeler replies received so far | 1 (q01) |

Treat every retrieval number in this repo as **preliminary** until all questions are validated and checked by a human
against the filings.

## Files

| File | What it is |
|---|---|
| `data/questions.jsonl` | The golden set currently used by the evaluation. One JSON object per question. |
| `data/questions_pattern_gold.jsonl` | The original pattern-matched labels, kept as a backup and for comparison. |
| `data/labeling/q01.txt` ... `q19.txt` | **Not stored in this repo** (they contain chunk text). Candidate-chunk pools sent to the labeler (40 chunks for single-filing questions, 72 for two-filing questions, shuffled, no reference answer). Regenerate them with `python scripts/build_label_pools.py` once `data/chunks.jsonl` is in place. |
| `data/labeling/PROMPT.txt` | The fixed labeler prompt. |
| `data/labeling/replies/qNN.json` | Labeler replies (saved with the per-chunk `reason` text omitted). |
| `scripts/build_questions.py` | Builds the pattern-based gold labels. |
| `scripts/build_label_pools.py` | Builds the candidate pools for labeling. |
| `scripts/ingest_labels.py` | Validates labeler replies and applies them to `questions.jsonl`. |

## Row format (`data/questions.jsonl`)

```json
{"qid": "q01", "hops": 1, "type": "single", "question": "...", "gold_chunk_ids": ["AAPL_FY2025_ITEM7_0004", "..."],
 "gold_answer": "...", "gold_source": "llm-labeler (validated)"}
```

`type` is `single`, `within` (multi-hop inside one company) or `cross` (two companies). `gold_source` is
`llm-labeler (validated)` or `pattern-match (unverified)`.

## How the gold chunks were made

1. **Pattern matching (all questions).** For each fact, every chunk in the filing the question names whose text matches a
   label-plus-number pattern (for example `Total net sales | $416,161`) is gold. This counts duplicates across MD&A and the
   financial statements as gold, because any of them answers the question. A pattern can miss a valid chunk.
2. **Independent LLM labeling.** For each question, a pool of candidate chunks is built from bge-small, DistilBERT and BM25
   results restricted to the named filings, plus 8 off-target chunks from other filings and years. The pool is shuffled,
   contains no reference answer, and goes to a labeler from a different model family together with `PROMPT.txt`. The labeler
   marks each chunk `answer`, `supporting` or `irrelevant` and must quote the supporting text verbatim.
3. **Validation (`scripts/ingest_labels.py`).** A reply is accepted only if every candidate chunk is labeled exactly once,
   every `answer` quote appears verbatim in its chunk and contains a figure (a bare column header does not count), and the
   chunk is from the company and fiscal year the question names. Rejected labels are reported, and only validated answers
   replace the gold set. The original file is kept as `data/questions_pattern_gold.jsonl`.

### Rules for what counts as gold

* The company **and fiscal year** must match the question. A prior-year column inside a later filing does not make that
  later filing's chunk an answer for the earlier year.
* A question that needs several facts needs gold chunks for each fact.
* Scope and units must match (for example "net income attributable to X" is not "consolidated net income").

## Questions and gold chunks

| Q | Type | Question | Gold chunks | Source |
|---|---|---|---|---|
| q01 | single | What were Apple's total net sales in fiscal 2025 (fiscal year ended September 27, 2025)? | `AAPL_FY2025_ITEM8_0000`<br>`AAPL_FY2025_ITEM8_0051`<br>`AAPL_FY2025_ITEM8_0015`<br>`AAPL_FY2025_ITEM7_0004`<br>`AAPL_FY2025_ITEM7_0005` | llm-labeler |
| q02 | single | What were Walmart's total revenues in fiscal 2026 (fiscal year ended January 31, 2026)? | `WMT_FY2026_ITEM1_0001`<br>`WMT_FY2026_ITEM7_0020`<br>`WMT_FY2026_ITEM8_0008`<br>`WMT_FY2026_ITEM8_0104` | pattern-match |
| q03 | single | How much did Microsoft spend on research and development in fiscal 2025 (fiscal year ended June 30, 2025)? | `MSFT_FY2025_ITEM7_0015`<br>`MSFT_FY2025_ITEM7_0016` | pattern-match |
| q04 | single | How many employees did JPMorgan Chase have globally as of December 31, 2025? | `JPM_FY2025_ITEM1_0033` | pattern-match |
| q05 | single | What was Caterpillar's profit per share for 2025? | `CAT_FY2025_ITEM7_0001`<br>`CAT_FY2025_ITEM7_0002` | pattern-match |
| q06 | single | What was Johnson & Johnson's total research and development expense in fiscal 2025, and what percent of sales was it? | `JNJ_FY2025_ITEM7_0027` | pattern-match |
| q07 | single | What was ExxonMobil's net income attributable to ExxonMobil in 2025? | `XOM_FY2025_ITEM7_0005`<br>`XOM_FY2025_ITEM8_0011` | pattern-match |
| q08 | single | In its 2025 10-K, what consumer product does Johnson & Johnson say it is a defendant in numerous lawsuits over, involving talc? | `JNJ_FY2025_ITEM1A_0011` | pattern-match |
| q09 | single | In which countries are Apple's outsourcing partners located, according to its fiscal 2025 10-K risk factors? | `AAPL_FY2025_ITEM1A_0003`<br>`AAPL_FY2025_ITEM1A_0014` | pattern-match |
| q10 | within | By how much did Apple's total net sales grow from fiscal 2024 to fiscal 2025, and what share of fiscal 2025 net sales came from iPhone? | `AAPL_FY2025_ITEM7_0004`<br>`AAPL_FY2025_ITEM7_0005`<br>`AAPL_FY2025_ITEM8_0015`<br>`AAPL_FY2025_ITEM8_0051` | pattern-match |
| q11 | within | What was Microsoft's fiscal 2025 research and development expense as a percent of its total revenue? | `MSFT_FY2025_ITEM7_0015`<br>`MSFT_FY2025_ITEM7_0016`<br>`MSFT_FY2025_ITEM8_0000` | pattern-match |
| q12 | within | By how much did Walmart's total revenues increase in fiscal 2026, and what was its consolidated net income attributable to Walmart? | `WMT_FY2026_ITEM7_0022`<br>`WMT_FY2026_ITEM8_0009`<br>`WMT_FY2026_ITEM8_0050`<br>`WMT_FY2026_ITEM8_0051` | pattern-match |
| q13 | within | Roughly how much did Caterpillar earn in total sales and revenues per full-time employee in 2025? | `CAT_FY2025_ITEM7_0002`<br>`CAT_FY2025_ITEM7_0011`<br>`CAT_FY2025_ITEM1_0028` | pattern-match |
| q14 | within | What were Johnson & Johnson's Innovative Medicine segment sales in 2025, and how much did that segment spend on research and development? | `JNJ_FY2025_ITEM7_0008`<br>`JNJ_FY2025_ITEM7_0012`<br>`JNJ_FY2025_ITEM7_0027` | pattern-match |
| q15 | cross | Which spent more on research and development in fiscal 2025, Apple or Microsoft, and by how much? | `AAPL_FY2025_ITEM7_0007`<br>`AAPL_FY2025_ITEM8_0000`<br>`MSFT_FY2025_ITEM7_0015`<br>`MSFT_FY2025_ITEM7_0016` | pattern-match |
| q16 | cross | Which had higher revenue in fiscal 2025, Apple or Microsoft, and by how much? | `AAPL_FY2025_ITEM7_0004`<br>`AAPL_FY2025_ITEM7_0005`<br>`AAPL_FY2025_ITEM8_0015`<br>`AAPL_FY2025_ITEM8_0051`<br>`MSFT_FY2025_ITEM8_0000` | pattern-match |
| q17 | cross | How many more employees did Walmart have than JPMorgan Chase at their most recent fiscal year ends in this data (Walmart January 31, 2026; JPMorgan December 31, 2025)? | `WMT_FY2026_ITEM1_0004`<br>`WMT_FY2026_ITEM1_0024`<br>`JPM_FY2025_ITEM1_0033` | pattern-match |
| q18 | cross | Which had higher research and development spending as a percent of revenue in its latest 10-K year, Johnson & Johnson (2025) or Microsoft (fiscal 2025)? | `JNJ_FY2025_ITEM7_0027`<br>`MSFT_FY2025_ITEM7_0015`<br>`MSFT_FY2025_ITEM7_0016` | pattern-match |
| q19 | cross | Which earned more net income in 2025, JPMorgan Chase or ExxonMobil, and roughly how many times as much? | `JPM_FY2025_ITEM15_0014`<br>`JPM_FY2025_ITEM7_0007`<br>`JPM_FY2025_ITEM8_0015`<br>`JPM_FY2025_ITEM8_0016`<br>`XOM_FY2025_ITEM7_0005`<br>`XOM_FY2025_ITEM8_0011` | pattern-match |

## Known limitations

* **Mostly unverified.** Only 1 of 19 questions have validated labels.
* **Pattern labels can miss chunks.** For q01 the pattern missed `AAPL_FY2025_ITEM8_0000` (a valid income-statement chunk
  that writes the figure without a `$`), which the labeler found.
* **Pooling limit.** A labeler can only label chunks it is shown. The pools contained 51 of the 57 pattern-based gold chunks, so
  facts phrased very differently from the question (for example "associates" for "employees") may need a second pool.
* **Duplicates are counted.** A fact repeated in several chunks gives a question several gold chunks, which lowers recall and
  precision even when a correct chunk is found. Use hit@k alongside recall@k.
* **Small set.** 19 questions; one question moves a percentage by 5.3 points.
* **Different fiscal year-ends.** Apple (September), Microsoft (June) and Walmart (January) differ, which affects the
  cross-company questions.

## Adding or replacing labels

1. Put the shared chunks file at `data/chunks.jsonl` and run `python scripts/build_label_pools.py` to create `data/labeling/qNN.txt`. Send `data/labeling/PROMPT.txt` and one `qNN.txt` per chat to a labeler from a different model family.
2. Save each JSON reply as `data/labeling/replies/qNN.json`.
3. Run `python scripts/ingest_labels.py` to validate and compare with the current gold, then `--apply` to write the validated
   answers into `data/questions.jsonl` (a backup is kept).
4. Spot-check a few questions against the SEC filings (every chunk has a `source_url`), then rerun the evaluation.
