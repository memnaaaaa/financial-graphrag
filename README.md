# financial-graphrag

CSC 8851 (Deep Learning) course project: answering questions about SEC 10-K filings with a
knowledge graph and a learned graph retriever (G-reasoner), compared against plain vector RAG.
Every number in an answer should be traceable to the filing, section and passage it came from.

**Scope:** Johnson & Johnson, Apple and Microsoft, two fiscal years each (6 annual reports),
split into 1,855 text chunks, and a golden set of 39 hand-checked questions.

## Research questions

1. **Retrieval:** does a learned graph retriever (G-reasoner, zero-shot and fine-tuned) beat vector
   RAG and a fixed graph walk (Personalized PageRank), and on which question types?
2. **Graph construction:** does it matter how the graph is built (our structured graph vs the
   graph G-reasoner builds from the same text on its own)?
3. **Traceability and errors:** can each number in an answer be traced to its source, how often do
   answers state numbers their evidence does not hold, and at which stage do errors start?

## Current state (Nov 20, 2026)

| Part | Folder | Status | Owner |
| --- | --- | --- | --- |
| Filings | `data/edgar_10k/` | Done: 10-K + Exhibit 21 from SEC EDGAR | Mohini |
| Chunks | `data/chunks/` | Done: 1,855 chunks with a full filing header (fixed Nov 18) | Mohini |
| Graph `fin10k_v0` | `data/graph/` | Done: rule-based, 3,622 nodes; every number tied to its filing, section, chunk and XBRL tag | Mohini |
| Graph `fin10k_v1` | `data/graph/` | Done: `fin10k_v0` + 382 LLM-extracted relation edges (3,841 nodes); hand check of 30 LLM edges on Nov 22 | Mohini |
| Vector-RAG baseline, golden set v2 | `vector_rag_baseline/` | Done on golden set v2 | Mahua |
| G-reasoner | `G-reasoner/` | Zero-shot runs on `fin10k_v0`; re-index on `fin10k_v1` and fine-tuning next | Rida |
| Report | `report/` | Preliminary report done (Oct 21); poster Nov 30, final report Dec 7 | All |

**Results so far (vector RAG, golden set v2, k = 10):** the best setup (bge-small + reranking)
answers 69% of questions correctly and hallucinates in 0-3%. Almost every wrong answer is a
retrieval miss: the passage holding a needed fact is not in the top 10, so Gemini declines to
answer. Single-fact questions are near 100% correct; cross-company questions fail in every setup.
Details: `vector_rag_baseline/results/v2_all_baselines/summary.md`.

## Folders

| Folder | What it holds | Read more |
| --- | --- | --- |
| `data/edgar_10k/` | Download script, manifest (accession numbers, URLs); raw filings are git-ignored | `SOURCES.md` |
| `data/chunks/` | `chunks.jsonl`: the text chunks every system retrieves from | `README.md` |
| `data/graph/` | The knowledge graph in gfmrag's format (`fin10k_v0`, `fin10k_v1`), build and check scripts | `README.md` |
| `vector_rag_baseline/` | Vector RAG (bge-small, FAISS, reranker, Gemini), golden set v2, metrics, results | `README.md` |
| `G-reasoner/` | G-reasoner retriever on the graph (Colab), evaluation, synthetic training pairs | `README.md` |
| `report/` | Preliminary report (CVPR format) and the schema figure | |

## Rebuild the data and the graph

```bash
pip install -r requirements.txt
cd data/edgar_10k && python download_edgar_10k.py --user-agent "Your Name your.email@example.edu" && cd ../..
python data/chunks/build_chunks.py                  # chunks.jsonl (checks that chunk ids are unchanged)
python data/graph/build_graph.py                    # fin10k_v0 (~1 min)
python data/graph/extract_relations_llm.py build    # fin10k_v1 from the Gemini answers
python data/graph/validate_graph.py data/graph/fin10k_v1/processed/stage1
```

`extract_relations_llm.py build` needs the cached Gemini answers (`data/graph/llm_cache/`, kept
local). Without them, use the committed `fin10k_v1`. To run the baseline or G-reasoner, follow
the README in their folders.

## Next steps

- Nov 22: hand-check 30 LLM edges; G-reasoner zero-shot on `fin10k_v1` (Rida)
- Nov 22-25: Personalized PageRank; G-reasoner fine-tuning (Rida); answer step that cites Value
  and chunk ids, then answers for every system (Mohini)
- Nov 25-26: tag the failure stage of every wrong answer (Mohini, Rida)
- Nov 30: poster; Dec 7: final report and open-source release

Contribution log: `CONTRIBUTIONS.md`.
