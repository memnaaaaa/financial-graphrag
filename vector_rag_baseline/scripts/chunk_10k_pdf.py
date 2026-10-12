"""Turn a 10-K PDF into a chunks.jsonl with the same fields Mohini's file should have.
Stand-in for realistic-scale testing only. Usage:
  python scripts/chunk_10k_pdf.py ~/Downloads/aapl-20250927.pdf data/aapl_chunks.jsonl --company Apple --year 2025
"""
import argparse
import json
import re

from pypdf import PdfReader

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("out")
ap.add_argument("--company", default="Apple")
ap.add_argument("--year", type=int, default=2025)
ap.add_argument("--words", type=int, default=200)
ap.add_argument("--overlap", type=int, default=40)
a = ap.parse_args()

slug = a.company.lower().replace(" ", "")
n = 0
with open(a.out, "w", encoding="utf-8") as f:
    for p, page in enumerate(PdfReader(a.pdf).pages, 1):
        words = re.sub(r"\s+", " ", page.extract_text() or "").split()
        step = a.words - a.overlap
        for j, s in enumerate(range(0, max(len(words), 1), step)):
            piece = words[s : s + a.words]
            if len(piece) < 30:  # skip tiny tails / blank pages
                continue
            f.write(json.dumps({
                "chunk_id": f"{slug}_{a.year}_p{p:03d}_c{j}",
                "company": a.company, "fiscal_year": a.year, "page": p,
                "text": " ".join(piece),
            }) + "\n")
            n += 1
print(f"wrote {n} chunks to {a.out}")
