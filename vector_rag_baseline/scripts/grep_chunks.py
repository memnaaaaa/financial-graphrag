"""Keyword search over chunks for finding gold evidence: grep_chunks.py TICKER FY 'regex' [width]"""
import json, re, sys
t, fy, pat = sys.argv[1], sys.argv[2], sys.argv[3]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 220
for l in open("data/chunks.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r["ticker"] != t or (fy != "*" and r["fiscal_year"] != fy): continue
    for m in re.finditer(pat, r["text"], re.I):
        s = max(0, m.start() - w // 3); print(f'{r["chunk_id"]} :: ...{r["text"][s:s+w].replace(chr(10)," | ")}...'); break
