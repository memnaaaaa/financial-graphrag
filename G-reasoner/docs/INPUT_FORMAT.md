# G-reasoner input format and how our graph maps onto it

Checked against the gfmrag 2.0.0 source (`gfmrag_retriever.py`, `graph_index_datasets/graph_index_dataset.py`)
and the `rmanluo/G-reasoner-34M` checkpoint config, Oct 2026.

## What G-reasoner reads

A dataset is a folder `<data_dir>/<data_name>/`:

```
<data_name>/
├── raw/documents.json            {document name: text}. Always opened, even when stage1 exists.
└── processed/
    ├── stage1/                   the graph ("bring your own graph"); we provide these
    │   ├── nodes.csv             name, type, attributes
    │   ├── relations.csv         name, attributes
    │   ├── edges.csv             source, relation, target, attributes
    │   ├── train.json, test.json optional, only for fine-tuning (format below)
    └── stage2/<hash>/            built by gfmrag: graph.pt, node2id.json, rel2id.json (+ train.pt, test.pt)
```

- `attributes` are Python dict literals (`{'kind': 'Product'}`), read with `ast.literal_eval`.
- Node names must be unique (or a `uid` column is used instead). Edges whose source, target or
  relation is unknown are dropped with a warning.
- `type` is free text. G-reasoner scores every node, and `retrieve(query, top_k, target_types)`
  returns the top k nodes of each requested type (default `["document"]`).
- `<hash>` comes from the embedding settings only, not from the graph contents, so a changed graph
  needs its stage2 folder deleted (our `prepare_data.py` does this).

## How the graph becomes model input (stage2)

- **Node features:** each node becomes the text `name: …\ntype: …\n<attribute>: <value>…` and is
  embedded with **Qwen3-Embedding-0.6B** (1024 dimensions, run through vLLM). The embedding model
  and its settings come from the checkpoint's `dataset_config`, so they match what G-reasoner was
  trained with.
- **Relation features:** each relation's name and description is embedded, plus a text embedding for
  `inverse_<name>`. Every edge is added in both directions (22 relation types for our 11).
- **Edge attributes are not used** (`use_edge_feat: false`).

## What a query looks like

1. **Start nodes:** an NER model returns entity mentions, and an entity-linking model maps each to a
   graph node name. These become a 0/1 mask over all nodes. With no start nodes the model has
   almost no signal (see `results/diagnose_fin10k_v0`).
2. **Question embedding:** the same Qwen3 model, with the instruction prefix
   `Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: `.
3. **Model:** `GraphReasoner` with a `QueryNBFNet` (6 layers of width 1024, DistMult messages, sum
   aggregation, layer norm, shortcut connections) and early-late fusion of the node embeddings. It
   outputs one score per node.

Our NER/EL is `entity_index.py` + `gfm_components.py` (alias matching on node names, no LLM).
gfmrag's default NER uses an LLM (`gpt-4o-mini` via OpenAI); we do not use it. Letting Gemini pick
the start nodes instead gave the same start nodes on the golden questions (`gemini_ner.py`, see README).

## Fine-tuning data (`stage1/train.json`, `test.json`)

A JSON list; gfmrag reads `id`, `question`, `start_nodes` and `target_nodes` (extra keys are ignored):

```json
{"id": "fin10k_v0-lookup-00012",
 "question": "What was Johnson & Johnson's DARZALEX revenue in fiscal 2025?",
 "start_nodes": {"entity": ["DARZALEX (JNJ)", "Johnson & Johnson", "Revenue", "FY2025 (JNJ)"]},
 "target_nodes": {"document": ["JNJ_FY2025_ITEM7_0009", "JNJ_FY2025_ITEM8_0111"],
                  "attribute": ["DARZALEX (JNJ) revenue FY2025 = $14,351 million"], "entity": []}}
```

Samples whose start nodes are all unknown are skipped (and those with no targets, by default).
`make_synthetic_questions.py` writes this format.

## How our schema maps onto it

| Our graph (`data/graph/README.md`) | G-reasoner |
| --- | --- |
| Company, Subsidiary, Location, Segment, BusinessLine, Product, Metric, FiscalYear (`attributes['kind']`) | `type = entity` |
| Value (one node per reported number) | `type = attribute` |
| Chunk from `data/chunks/chunks.jsonl`, named by `chunk_id`, text in `content` | `type = document` |
| 11 relations with a `description` attribute | relations, plus 11 inverse relations |
| `is_mentioned_in` (entity or Value → chunk) | the same relation name gfmrag's own graph builder uses for entity → document |
| (missing) | `raw/documents.json`, written by `prepare_data.py` from the document nodes |

Because document nodes are named by `chunk_id`, G-reasoner's retrieved documents can be scored
directly against the golden set's `gold_chunk_ids`.

## Differences from the graphs G-reasoner was pretrained on

gfmrag's own graph builder extracts triples from each passage with an LLM (OpenIE), so every
passage links to its own entities, entity attributes are empty and relations have no descriptions.
Our graph is built by rules from XBRL tags and Exhibit 21:

- entities carry typed attributes and relations carry descriptions;
- numbers are separate `attribute` nodes;
- **56% of the 1,855 chunks link only to their company and fiscal-year nodes** (through the chunk
  header), because rule-based extraction finds no other entity in prose.

The last point is the most likely reason the pretrained model ranks generic chunks first; the LLM
relation extraction in phase 2 (`fin10k_v1`) adds links to prose chunks.
