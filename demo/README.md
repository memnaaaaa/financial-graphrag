# Poster demo: "Follow the Number"

A single offline web page for the poster session. Pick a question, see the start nodes, the graph around them,
what each system retrieved and answered, and click any cited number to follow it to the Value node, the line
of the passage that prints it, the filing and the SEC EDGAR link. No server and no Gemini calls: every answer
is precomputed in `answer_step/results/`.

**Live page:** https://memnaaaaa.github.io/financial-graphrag/demo/ (GitHub Pages, served from `main`; the empty `.nojekyll` file at the repo root tells
Pages to serve the files as they are).

```bash
python demo/build_data.py     # rebuild demo_data.json and index.html from the repo's results
# then open demo/index.html in a browser (works with Wi-Fi off)
```

**Showcase questions** (one per kind of outcome, from `answer_step/results/`):

| Card | Question | Vector RAG | Graph (fine-tuned G-reasoner) | Hybrid |
| --- | --- | --- | --- | --- |
| Single fact | v2_q01 Apple net sales FY2025 | correct | correct | correct (cites a Value) |
| Graph wins | v2_q39 Apple vs J&J net income | refused | correct | correct (cites Values) |
| Wrong answer | v2_q12 OpenAI gains at Microsoft | correct | wrong ($5.0B, not $6.5B) | correct |
| Missing | v2_q16 who owns J&J's top drug's patents | correct | refused | correct |
| Everyone fails | v2_q33 Apple headcount, two years | refused | refused | refused |

| File | What it is |
| --- | --- |
| `build_data.py` | Reads the results, graph, chunks and golden set; writes `demo_data.json` and `index.html` |
| `template.html` | The page (HTML, CSS, JavaScript); `build_data.py` inlines the data into it |
| `index.html`, `demo_data.json` | Generated; open `index.html` |
| `vendor/vis-network.min.js` | Graph library, inlined into `index.html` by `build_data.py` |

Status (Nov 26): all parts work.

`vendor/vis-network.min.js` is vis-network 9.1.9 (Apache-2.0 or MIT), unchanged.
