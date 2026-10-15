# Contribution log

| Date | Who | What was done | Link (commit / file / Notion) | Hours |
| --- | --- | --- | --- | --- |
| 2026-10-05 | Mohini | Picked 8 companies; EDGAR download script + manifest | data/edgar_10k/ | 3 |
| 2026-10-06 | Mohini | Read J&J 10-K; draft graph schema v0 | Notion: Draft schema v0 | 4 |
| 2026-10-08 | Mohini | Built chunks.jsonl (7,339 section-aware chunks of ≤350 tokens with ~50-token overlap from all 16 filings) plus documents.json for G-reasoner, with the build script and README | data/chunks/ | 2.5 |
| 2026-10-14 | Mohini | Reviewed Mahua's vector-RAG baseline code; built the rule-based graph fin10k_v0 for JNJ, AAPL and MSFT (subsidiaries from Exhibit 21, segments/products/numbers from XBRL with numbers as Value attribute nodes, chunk document nodes, is_mentioned_in links) in gfmrag nodes/relations/edges.csv format, with build and validation scripts and README | data/graph/ | 3 |
| 2026-10-14 | Mohini | Hand-checked 30 random edges of fin10k_v0 (29/30 correct, data/graph/edge_check.csv); wrote the Phase 2 LLM relation extraction script (Gemini, 9 relation types, quote check, name merging into the graph), tested and fixed the prompt on 5 chunks, and ran 476 of 623 chunks before the free-tier limit | data/graph/extract_relations_llm.py, data/graph/edge_check.csv | 3 |
