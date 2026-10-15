# Knowledge graph for G-reasoner (`fin10k_v0`)

Built Oct 14, 2026 for **Johnson & Johnson, Apple and Microsoft** (both fiscal years each, 6 filings).
It uses rules only, with no LLM. The files follow gfmrag's
["bring your own graph"](https://rmanluo.github.io/gfm-rag/latest/workflow/data_format/) format:

```
data/graph/fin10k_v0/
├── graph_stats.json
└── processed/stage1/
    ├── nodes.csv       name,type,attributes   (3,618 nodes)
    ├── relations.csv   name,attributes        (11 relations)
    └── edges.csv       source,relation,target,attributes   (14,431 edges)
```

**To use it with gfmrag:** copy the `fin10k_v0` folder into gfmrag's data root and use
`data_name=fin10k_v0`. Because `processed/stage1/` already exists, gfmrag skips its own
LLM graph construction. `attributes` are Python dict literals (`{'kind': 'Product', ...}`),
which is what gfmrag's loader (`ast.literal_eval`) expects.

## What is in the graph

`type` is one of gfmrag's three groups: `entity`, `attribute` or `document`. The finer kind is
in `attributes['kind']`.

| type | kind | Count | Where it comes from | Example name |
| --- | --- | ---: | --- | --- |
| document | (chunk) | 1,855 | `data/chunks/chunks.jsonl`, all chunks of the 6 filings | `JNJ_FY2025_ITEM7_0009` (attributes: content, ticker, fiscal_year, section) |
| attribute | Value | 1,094 | Inline XBRL numbers in the 10-K | `DARZALEX (JNJ) revenue FY2025 = $14,351 million` |
| entity | Company | 3 | Filings manifest | `Johnson & Johnson` |
| entity | Subsidiary | 450 | Exhibit 21 | `Janssen Biotech, Inc.` |
| entity | Location | 101 | Exhibit 21 jurisdictions + XBRL geography | `United States`, `Delaware`, `Europe` |
| entity | Segment | 11 | XBRL segment axis | `Innovative Medicine (JNJ)`, `Intelligent Cloud (MSFT)` |
| entity | BusinessLine | 10 | XBRL sub-segment axis (J&J franchises) | `Oncology (JNJ)` |
| entity | Product | 60 | XBRL product/service axis | `DARZALEX (JNJ)`, `iPhone (AAPL)`, `LinkedIn (MSFT)` |
| entity | Metric | 21 | Curated list of XBRL concepts | `Revenue`, `Research and development expense` |
| entity | FiscalYear | 13 | Fact periods / chunk headers | `FY2025 (JNJ)` |

Segment, product and fiscal-year names carry the ticker in brackets because companies reuse
words (Apple's "Europe" segment is not the place Europe, and fiscal years end on different dates).

| Relation | Count | Meaning |
| --- | ---: | --- |
| `has_subsidiary` | 450 | Company → Subsidiary |
| `incorporated_in` | 455 | Subsidiary (or Company) → Location |
| `part_of` | 19 | U.S. state → `United States` |
| `has_segment` | 11 | Company → Segment |
| `has_business_line` | 11 | Segment → BusinessLine |
| `has_product` | 60 | Segment / BusinessLine / Company → Product |
| `has_value` | 1,094 | Company / Segment / BusinessLine / Product → Value |
| `of_metric` | 1,094 | Value → Metric |
| `for_period` | 1,094 | Value → FiscalYear |
| `in_location` | 432 | Value → Location (e.g. U.S. vs outside-U.S. sales) |
| `is_mentioned_in` | 9,711 | Entity or Value → document chunk |

### Numbers are Value nodes

Each reported number is its own node of type `attribute`. Its name is a short sentence, so
entity linking and the GNN can both use it. Its attributes hold the details:

```
name:       DARZALEX (JNJ) revenue FY2025 = $14,351 million
attributes: {'kind': 'Value', 'value': 14351000000.0, 'display': '$14,351 million', 'unit': 'USD',
             'metric': 'Revenue', 'xbrl_concept': 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
             'ticker': 'JNJ', 'fiscal_year': 'FY2025', 'period_end': '2025-12-28', 'source': 'xbrl',
             'source_filings': ['JNJ FY2025'], 'period_start': '2024-12-30'}
edges:      DARZALEX (JNJ) -has_value-> it;  it -of_metric-> Revenue;  it -for_period-> FY2025 (JNJ);
            it -is_mentioned_in-> JNJ_FY2025_ITEM7_0009, JNJ_FY2025_ITEM8_0111
```

Example multi-hop path: `Johnson & Johnson → Innovative Medicine (JNJ) → Oncology (JNJ) → DARZALEX (JNJ) → DARZALEX revenue FY2025 → chunk JNJ_FY2025_ITEM7_0009`.

## How it is built (`build_graph.py`)

1. **Companies** come from `data/edgar_10k/filings_manifest.csv`.
2. **Subsidiaries:** every two-cell row of the Exhibit 21 table (name, jurisdiction).
   Jurisdictions are normalised ("Delaware, U.S." → `Delaware`, "Korea, Republic of" → `South Korea`),
   and U.S. states get a `part_of` edge to `United States`.
3. **Numbers (inline XBRL):** the 10-K HTML has hidden tags on every number in the financial
   statements. The script keeps:
   - a curated list of 26 concepts (revenue, net income, R&D, EPS, total assets, cash flow, ...);
   - only full fiscal years (duration 350–380 days) or fiscal-year-end balances;
   - only facts with no dimension or with segment / sub-segment / product / geography
     dimensions. Facts with other dimensions (debt tranches, equity components) are dropped,
     and so are zero values.

   A fact's dimensions create the Segment → BusinessLine → Product chain, and its geography
   becomes an `in_location` edge. The same fact appears in both filings of a company (as the
   current year in one and the prior year in the other). It is stored once, with the newer
   filing's value; if the older filing showed a different number, that is kept as
   `earlier_reported_value`.
4. **Documents:** every chunk of the 6 filings, named by `chunk_id`, with its text in `content`.
5. **`is_mentioned_in` links:**
   - **Entities:** an entity links to a chunk when its name appears in the chunk text (after
     the header line). Matching is whole-word, case-insensitive for names of 5+ characters,
     and limited to the same company's chunks except for locations.
   - **Header line:** every chunk's header names the company and the filing year, so the
     Company and FiscalYear nodes link to all chunks of that filing. This also means no
     chunk is left without a link.
   - **Values:** a Value links to a chunk of the same company that shows the number exactly
     as printed (e.g. `14,351`) and also names the product or segment. For company totals,
     the chunk must contain the metric's keyword instead, e.g. "sales" or "per share".

## Rebuild and check

```
python data/graph/build_graph.py                           # JNJ AAPL MSFT -> fin10k_v0 (~30 s)
python data/graph/build_graph.py --tickers JNJ AAPL MSFT JPM --name fin10k_v1
python data/graph/validate_graph.py data/graph/fin10k_v0/processed/stage1
```

Needs `lxml` plus the raw filings and `data/chunks/chunks.jsonl`. `validate_graph.py` reads the
files the way gfmrag does. It checks for unique node names, dict-literal attributes, and edges
that point only to existing nodes and relations. It also prints coverage by kind.

Hand check: 30 randomly sampled edges were checked against the filings, and 29 were correct
(97%). The one error was a place name matched inside a court name ("United States District
Court"). Results are in `edge_check.csv`.

Spot checks against the filings (all match): DARZALEX revenue FY2025 $14,351M and FY2024
$11,670M; Apple revenue FY2024 $391,035M and FY2025 $416,161M; Microsoft revenue FY2025 $281,724M.

## Known gaps

- **Only structured facts so far.** Relations written in prose are not in the graph yet,
  e.g. "DARZALEX is licensed from Genmab", acquisitions, partners and competitors. That is
  phase 2 (below).
- **XBRL member names are turned into readable names by rule** (`MEMBER_NAMES` in the script
  fixes the ones the rule gets wrong). New companies may need a few more entries.
- **Products and subsidiaries are not merged** (`Abiomed (JNJ)` the product line vs
  `ABIOMED, Inc.` the subsidiary).
- **Some Values have no chunk link** (16%), mostly balance-sheet items printed in a different
  rounding. Generic product names ("Products", "Services", "Other services") are not
  text-matched, so those 5 product nodes reach chunks only through their Values.

## Phase 2 (in progress): LLM extraction of prose relations

`extract_relations_llm.py` asks Gemini (`gemini-3.5-flash-lite`) for relationships that are
written in sentences rather than tables, then adds them to the graph as a new version,
`fin10k_v1`. `fin10k_v0` stays unchanged.

**Input:** the text chunks (no tables) of Items 1, 7 and 8 for JNJ, AAPL and MSFT: 623 chunks.

**Relations (9):** licensed_from, acquired, partners_with, competes_with, manufactures,
supplies_to, has_product, subsidiary_of, invests_in.

**Run it** (needs `GEMINI_API_KEY` in the repo-root `.env`):

```
python data/graph/extract_relations_llm.py extract --test --redo   # 5 test chunks only
python data/graph/extract_relations_llm.py extract                 # all 623 chunks
python data/graph/extract_relations_llm.py build                   # writes data/graph/fin10k_v1/
python data/graph/validate_graph.py data/graph/fin10k_v1/processed/stage1
```

`extract` saves every answer in `data/graph/llm_cache/<model>.jsonl`. If it stops (for example at
the daily free-tier limit), run the same command again; finished chunks are skipped.

**What `build` does with the answers:**
- keeps a triple only if its evidence quote is really in the chunk (ignoring punctuation),
- drops triples with generic names such as "security solution vendors" (no capital letter),
- flips has_product triples written backwards ("DARZALEX has_product J&J"),
- merges names into existing nodes: exact match first, then a unique short form
  ("Intra-Cellular" -> "Intra-Cellular Therapies, Inc."). Names that could match several nodes
  ("Shockwave") become new nodes. Every decision is listed in `fin10k_v1/merge_report.csv`,
- tags each new edge with `source: 'llm'`, the chunk_ids and the evidence quote.

**Test on 5 chunks:** after three prompt rounds, the output has the key DARZALEX chain
(Janssen Biotech licensed_from Genmab A/S; DARZALEX licensed_from Genmab A/S), the
J&J acquisitions (Intra-Cellular, Halda, Shockwave), Microsoft invests_in OpenAI, and the
Intelligent Cloud products. Known weak spots: patent ownership is sometimes read as has_product,
and one acquisition (Abiomed) was inferred rather than stated.

**Status (Oct 15):** 476 of 623 chunks done before the free-tier daily limit; the other 147 will run
next. The cache and `fin10k_v1` are git-ignored until the run is finished and 30 LLM edges are
hand-checked. A later rerun with a stronger Gemini model is planned (see Notion).
