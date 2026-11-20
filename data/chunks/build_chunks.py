"""Build chunks.jsonl from the downloaded 10-K filings (main document + Exhibit 21).

Each line of chunks.jsonl is one passage of about 350 tokens that never crosses a 10-K
section boundary. The same file feeds the vector-RAG baseline (embed `text`) and the
graph's document layer (one document node per `chunk_id`).

Usage (from the repo root):
    python data/chunks/build_chunks.py                      # J&J, Apple, Microsoft (default)
    python data/chunks/build_chunks.py --tickers JNJ AAPL MSFT JPM

Each chunk starts with one header line naming the company, the fiscal year and its end date,
and the section, e.g.
    Apple Inc. (AAPL) | Form 10-K annual report for fiscal year 2025 (FY2025), fiscal year ended
    September 27, 2025 | Item 7. Management's Discussion and Analysis ...
Chunks are packed as if the header were the short one used before Nov 2026
("Apple Inc. (AAPL) | FY2025 Form 10-K | Item 7. ..."), so chunk IDs and chunk bodies stay
exactly the same as in earlier builds; only the header line is longer. If chunks.jsonl already
exists, the script checks that every chunk ID and body is unchanged before overwriting it.

Outputs in data/chunks/:
    chunks.jsonl          one JSON object per chunk (schema in README.md)
    documents.json        {chunk_id: text}, the raw/documents.json format G-reasoner (gfmrag) reads
    chunk_stats.csv       chunk and token counts per filing and section
    section_spans.csv     where each section was found in each filing (for checking)

Token counts use the bge-small-en-v1.5 tokenizer (BERT uncased WordPiece). If the Hugging
Face Hub is reachable the official tokenizer is used; otherwise the bundled vocab file
bert-base-uncased-vocab.txt (same 30,522-token vocabulary) is used.
"""
import argparse, csv, json, os, re, sys
from collections import Counter, defaultdict

import lxml.html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

COMPANY = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "JPM": "JPMorgan Chase & Co.",
    "JNJ": "Johnson & Johnson", "XOM": "Exxon Mobil Corporation", "PG": "The Procter & Gamble Company",
    "WMT": "Walmart Inc.", "CAT": "Caterpillar Inc.",
}

ITEM_TITLES = {
    "1": "Business", "1A": "Risk Factors", "1B": "Unresolved Staff Comments", "1C": "Cybersecurity",
    "2": "Properties", "3": "Legal Proceedings", "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    "6": "[Reserved]", "7": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk", "8": "Financial Statements and Supplementary Data",
    "9": "Changes in and Disagreements with Accountants on Accounting and Financial Disclosure",
    "9A": "Controls and Procedures", "9B": "Other Information",
    "9C": "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections",
    "10": "Directors, Executive Officers and Corporate Governance", "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters",
    "13": "Certain Relationships and Related Transactions, and Director Independence",
    "14": "Principal Accountant Fees and Services", "15": "Exhibits and Financial Statement Schedules",
    "16": "Form 10-K Summary",
}
ITEM_ORDER = list(ITEM_TITLES)

# ---------------------------------------------------------------- HTML -> blocks
BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table", "ul", "ol", "center", "section"}
JOIN_LEFT = {"%", ")", "%)", "*"}
JOIN_RIGHT = {"$", "(", "($", "$(", "€", "£"}


def _clean(s):
    s = s.replace(" ", " ").replace("​", "").replace(" ", " ").replace("’", "'")
    return re.sub(r"[ \t\r\n\f\v]+", " ", s).strip()


def _row_cells(tr):
    out = []
    for td in tr.iter("td", "th"):
        c = _clean(td.text_content())
        if not c:
            continue
        if out and (c in JOIN_LEFT or c.startswith(")")):
            out[-1] += c
        elif out and out[-1] in JOIN_RIGHT:
            out[-1] += c
        else:
            out.append(c)
    return out


PAGE_NUM = re.compile(r"^\d{1,3}(\s*[-\u2013]\s*\d{1,3})?$")


def _is_toc_table(rows):
    """A table of contents: mostly rows of the form 'Title | 12' with small page numbers and no financial figures."""
    if len(rows) < 4:
        return False
    flat = [c.lower() for cells in rows for c in cells]
    if not any(c == "page" or "table of contents" in c for c in flat):
        return False  # real tables of contents carry a "Page" column header or a "Table of Contents" title
    toc = 0
    for cells in rows:
        text = " ".join(cells)
        if re.search(r"[$%]|\d,\d{3}|\d\.\d", text) or not re.search(r"[A-Za-z]{3}", text):
            continue
        if PAGE_NUM.match(cells[-1]) or re.match(r"^\d{1,3} [A-Z]", cells[0]):
            toc += 1  # page number at the end of the row (or leading each entry)
    return toc / len(rows) >= 0.5


def _fact_ids(el):
    """ids of the inline-XBRL numbers (ix:nonFraction) inside an element, in document order."""
    return [e.get("id") for e in el.iter() if isinstance(e.tag, str)
            and e.tag.lower() == "ix:nonfraction" and e.get("id")]


def html_to_blocks(path, track_facts=False):
    """Ordered list of blocks {"kind": "text" | "row" | "table_end", "text": str}.

    With track_facts=True, a block that shows inline-XBRL numbers also gets "fact_ids" (the ids of
    its ix:nonFraction tags), so the graph can say in which section and chunk a number is printed.
    The block texts are the same either way."""
    raw = open(path, "rb").read()
    # strip the SEC SGML wrapper some files carry (<DOCUMENT><TYPE>EX-21 ...<TEXT>); its unclosed tags confuse HTML parsing
    raw = re.sub(rb"(?i)<(type|sequence|filename|description)>[^<\n]*", b"", raw)
    raw = re.sub(rb"(?i)</?(document|text)>", b"", raw)
    doc = lxml.html.fromstring(raw)
    for el in [e for e in doc.iter() if isinstance(e.tag, str) and e.tag.lower() == "ix:header"]:
        el.drop_tree()  # hidden inline-XBRL facts
    for el in doc.xpath("//*[@style]"):
        if "display:none" in el.get("style", "").replace(" ", "").lower():
            el.drop_tree()
    for el in doc.xpath("//script|//style|//head|//title"):
        el.drop_tree()

    blocks, buf = [], []
    pending = []  # fact ids seen since the last text block (track_facts only)

    def flush():
        t = _clean(" ".join(buf))
        buf.clear()
        if t:
            blocks.append({"kind": "text", "text": t})
            if pending:
                blocks[-1]["fact_ids"] = pending[:]
                pending.clear()

    def walk(el):
        if not isinstance(el.tag, str):  # comments / processing instructions: keep only their tail
            if el.tail:
                buf.append(el.tail)
            return
        tag = el.tag.split("}")[-1].lower()
        if tag == "table":
            flush()
            trs = [(cells, tr) for cells, tr in ((_row_cells(tr), tr) for tr in el.iter("tr")) if cells]
            rows = [cells for cells, _ in trs]
            if not _is_toc_table(rows):
                for cells, tr in trs:
                    blocks.append({"kind": "row", "text": " | ".join(cells)})
                    if track_facts and _fact_ids(tr):
                        blocks[-1]["fact_ids"] = _fact_ids(tr)
                blocks.append({"kind": "table_end", "text": ""})
            if el.tail:
                buf.append(el.tail)
            return
        is_block = tag in BLOCK_TAGS
        if is_block:
            flush()
        if track_facts and tag == "ix:nonfraction" and el.get("id"):
            pending.append(el.get("id"))
        if el.text:
            buf.append(el.text)
        for ch in el:
            walk(ch)
        if is_block:
            flush()
        if el.tail:
            buf.append(el.tail)

    body = doc.find("body")
    walk(body if body is not None else doc)
    flush()
    out = []
    for b in blocks:
        t = b["text"]
        if re.fullmatch(r".{0,60}(annual report|form 10-k)( \| ?| )\d{1,3}", t, re.I) and len(t) < 70:
            continue  # page footers such as "2025 Annual Report | 1", "JPMorgan Chase & Co./2025 Form 10-K | 43"
        if b["kind"] == "text" and (re.fullmatch(r"(page )?\d{1,3}", t, re.I)
                                    or t.lower() in {"table of contents", "index"}
                                    or re.fullmatch(r"\d{4} annual report( \d{1,3})?", t, re.I)
                                    or re.fullmatch(r"(part [iv]+ )?item \d{1,2}[a-c]?(, ?\d{1,2}[a-c]?)*", t, re.I)):
            continue  # page numbers, running headers ("Item 7", "2025 Annual Report 23")
        out.append(b)
    return out


# ---------------------------------------------------------------- sections
HEAD_RE = re.compile(r"^item\s*(\d{1,2})\s*([a-c])?\s*[\.:—\-]?\s*(\|\s*)?(.{3,})$", re.I)
TOC_ROW_RE = re.compile(r"\|\s*\d{1,3}(\s*[-–,]\s*\d{1,3})*$")
TAIL_START_RE = re.compile(r"^(financial section|management.s discussion and analysis)", re.I)
FS_START_RE = re.compile(r"^(management.s report on internal control|report of independent registered public accounting firm"
                         r"|consolidated (statements?|statement) of (income|earnings|operations))", re.I)


def find_sections(blocks):
    """Return [(start, end, code)] spans; code is an item number, 'COVER', or 'EX21'."""
    heads = {}
    for i, b in enumerate(blocks):
        if b["kind"] == "table_end" or len(b["text"]) > 250 or TOC_ROW_RE.search(b["text"]):
            continue
        m = HEAD_RE.match(b["text"])
        if not m:
            continue
        code = m.group(1) + (m.group(2) or "").upper()
        title = m.group(4)
        if code in ITEM_TITLES and code not in heads and re.search(r"[A-Za-z]{3}", title) \
                and not re.match(r"^(of|in|above|below|to|and)\b", title.strip(), re.I):
            heads[code] = i
    # keep headings in document order and in form order (drops stray matches)
    ordered, last = [], -1
    for code in ITEM_ORDER:
        if code in heads and heads[code] > last:
            ordered.append((heads[code], code))
            last = heads[code]
    spans = []
    if not ordered:
        return [(0, len(blocks), "COVER")], "no item headings found"
    spans.append((0, ordered[0][0], "COVER"))
    for k, (start, code) in enumerate(ordered):
        end = ordered[k + 1][0] if k + 1 < len(ordered) else len(blocks)
        spans.append((start, end, code))

    # Some filers (e.g. JPM, XOM) put MD&A and the financial statements in a separate
    # "financial section" / annual report after Item 15/16, and Items 7 and 8 only point to it.
    note = ""
    span7 = next((s for s in spans if s[2] == "7"), None)
    if span7 and span7[1] - span7[0] < 8:
        last_start = ordered[-1][0]
        tail = next((i for i in range(last_start + 1, len(blocks))
                     if TAIL_START_RE.match(blocks[i]["text"]) and len(blocks[i]["text"]) < 160), None)
        if tail is not None:
            fs = next((i for i in range(tail + 1, len(blocks))
                       if blocks[i]["kind"] == "text" and FS_START_RE.match(blocks[i]["text"]) and len(blocks[i]["text"]) < 160), None)
            new = []
            for s, e, c in spans:
                if s < tail < e:
                    e = tail
                new.append((s, e, c))
            if fs is not None:
                new += [(tail, fs, "7"), (fs, len(blocks), "8")]
            else:
                new += [(tail, len(blocks), "7")]
            spans = new
            note = f"Items 7/8 relocated: MD&A from block {tail}, financial statements from block {fs}"
    return spans, note


def section_label(code):
    if code == "COVER":
        return "Cover", "Cover Page, Table of Contents and Introductory Statements"
    if code == "EX21":
        return "Exhibit 21", "Subsidiaries of the Registrant"
    return f"Item {code}", ITEM_TITLES[code]


# ---------------------------------------------------------------- tokenizer
def load_tokenizer(vocab_path):
    try:
        from tokenizers import Tokenizer
        tok = Tokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
        tok.no_truncation()
        return tok, "BAAI/bge-small-en-v1.5 (Hugging Face Hub)"
    except Exception:
        from tokenizers import BertWordPieceTokenizer
        return BertWordPieceTokenizer(vocab_path, lowercase=True), f"local {os.path.basename(vocab_path)} (BERT uncased WordPiece)"


class Counter_:
    def __init__(self, tok):
        self.tok, self.cache = tok, {}

    def __call__(self, text):
        if text not in self.cache:
            self.cache[text] = len(self.tok.encode(text, add_special_tokens=False).ids)
        return self.cache[text]


# ---------------------------------------------------------------- chunking
SENT_SPLIT = re.compile(r"(?<=[\.\?!;])\s+(?=[A-Z0-9\(\"'])")


def split_long(text, limit, ntok):
    """Split a unit that is longer than `limit` tokens into sentence- then word-sized pieces."""
    if ntok(text) <= limit:
        return [text]
    pieces = []
    for sent in SENT_SPLIT.split(text):
        if ntok(sent) <= limit:
            pieces.append(sent)
            continue
        words, cur = sent.split(" "), []
        for w in words:
            if cur and ntok(" ".join(cur + [w])) > limit:
                pieces.append(" ".join(cur))
                cur = []
            cur.append(w)
        if cur:
            pieces.append(" ".join(cur))
    # re-pack short sentences together up to the limit
    packed, cur = [], ""
    for p in pieces:
        cand = (cur + " " + p).strip()
        if cur and ntok(cand) > limit:
            packed.append(cur)
            cur = p
        else:
            cur = cand
    if cur:
        packed.append(cur)
    return packed


def tail_words(text, budget, ntok):
    """Last words of `text` that fit in `budget` tokens (the overlap carried into the next chunk)."""
    words = text.split()
    out = []
    for w in reversed(words):
        if ntok(" ".join([w] + out)) > budget:
            break
        out.insert(0, w)
    return " ".join(out)


def chunk_section(blocks, header, max_tokens, overlap, ntok, out_header=None):
    """Pack whole lines (paragraphs, table rows) into chunks of at most `max_tokens`, header included.

    Overlap: each new chunk repeats about `overlap` tokens from the end of the previous one
    (whole table rows when the previous chunk ended inside a table, otherwise its last words).
    A chunk that starts in the middle of a table also repeats that table's first (column header) row.
    `header` sizes the chunks; `out_header` (default: `header`) is the line written on top of each chunk,
    so a longer header can be written without moving any chunk boundary.
    """
    body_limit = max_tokens - ntok(header) - 1
    units, table_id, first_row = [], 0, None   # unit = (text, table_id or None, table's first row)
    for b in blocks:
        if b["kind"] == "table_end":
            table_id, first_row = table_id + 1, None
            continue
        if b["kind"] == "row":
            if first_row is None:
                first_row = b["text"] if ntok(b["text"]) <= 60 else None
                first_row = first_row or ""
            units.append((b["text"] if ntok(b["text"]) <= body_limit - overlap - 60 else
                          split_long(b["text"], body_limit - overlap - 60, ntok), table_id, first_row))
        else:
            for piece in split_long(b["text"], body_limit - overlap, ntok):
                units.append((piece, None, None))
    flat = []
    for text, tid, hdr in units:  # long rows were split into pieces above
        for t in (text if isinstance(text, list) else [text]):
            flat.append((t, tid, hdr))

    chunks, cur = [], []          # cur = list of (text, table_id)
    def body(lines):
        return "\n".join(t for t, _ in lines)

    for text, tid, hdr in flat:
        if cur and ntok(body(cur + [(text, tid)])) > body_limit:
            chunks.append(cur)
            prev_text, prev_tid = cur[-1]
            carry = []
            if overlap and prev_tid is not None:          # carry whole rows of the same table
                for t, ptid in reversed(cur):
                    if ptid != prev_tid or ntok(body([(t, ptid)] + carry)) > overlap:
                        break
                    carry.insert(0, (t, ptid))
            elif overlap:
                tail = tail_words(body(cur), overlap, ntok)
                carry = [(tail, None)] if tail else []
            if tid is not None and hdr and (not carry or carry[0][0] != hdr):
                carry.insert(0, (hdr, tid))               # repeat the column header row
            cur = carry if ntok(body(carry + [(text, tid)])) <= body_limit else []
        cur.append((text, tid))
    if cur:
        if chunks and ntok(body(cur)) < 40 and ntok(body(chunks[-1] + cur)) <= body_limit:
            chunks[-1] = chunks[-1] + cur                 # fold a tiny last piece into the previous chunk
        else:
            chunks.append(cur)
    top = out_header or header
    return [(top + "\n" + body(c), any(t is not None for _, t in c)) for c in chunks]


# ---------------------------------------------------------------- header and twins
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def long_header(ticker, fy, period_end, sec, sec_title):
    """Header that states the fiscal year in words and dates, so text from the two filings of a
    company (which is often word for word the same) carries a clear year signal."""
    y, m, d = (int(x) for x in period_end.split("-"))
    year = fy[2:] if fy.upper().startswith("FY") else fy
    return (f"{COMPANY[ticker]} ({ticker}) | Form 10-K annual report for fiscal year {year} ({fy}), "
            f"fiscal year ended {MONTHS[m - 1]} {d}, {y} | {sec}. {sec_title}")


def body_of(text):
    return text.split("\n", 1)[1] if "\n" in text else ""


def add_twins(recs, threshold):
    """For each chunk, the most similar chunk of the same company and section in the other fiscal
    year (word-set Jaccard similarity of the bodies). Chunks at or above `threshold` get
    `twin_chunk_id` and `twin_similarity`; the rest get None. Twins are kept: questions need both years."""
    words = {r["chunk_id"]: set(re.findall(r"[a-z0-9]+", body_of(r["text"]).lower())) for r in recs}
    groups = defaultdict(list)
    for r in recs:
        groups[(r["ticker"], r["section"])].append(r)
    n = 0
    for grp in groups.values():
        for r in grp:
            best, best_sim = None, 0.0
            a = words[r["chunk_id"]]
            for o in grp:
                if o["fiscal_year"] == r["fiscal_year"]:
                    continue
                b = words[o["chunk_id"]]
                sim = len(a & b) / len(a | b) if a and b else 0.0
                if sim > best_sim:
                    best, best_sim = o["chunk_id"], sim
            ok = best is not None and best_sim >= threshold
            r["twin_chunk_id"] = best if ok else None
            r["twin_similarity"] = round(best_sim, 3) if ok else None
            n += ok
    return n


def check_same_chunks(old_path, recs):
    """Compare with the previous chunks.jsonl: same IDs and same bodies for the companies built now."""
    tickers = {r["ticker"] for r in recs}
    old = {}
    for line in open(old_path, encoding="utf-8"):
        if line.strip():
            o = json.loads(line)
            if o["ticker"] in tickers:
                old[o["chunk_id"]] = body_of(o["text"])
    new = {r["chunk_id"]: body_of(r["text"]) for r in recs}
    missing = sorted(set(old) - set(new))
    extra = sorted(set(new) - set(old))
    changed = sorted(c for c in set(old) & set(new) if old[c] != new[c])
    return len(old), missing, extra, changed


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(REPO, "data", "edgar_10k", "filings_manifest.csv"))
    ap.add_argument("--raw-dir", default=os.path.join(REPO, "data", "edgar_10k", "raw"))
    ap.add_argument("--out-dir", default=HERE)
    ap.add_argument("--max-tokens", type=int, default=350, help="max tokens per chunk, header included")
    ap.add_argument("--overlap", type=int, default=50, help="tokens repeated from the end of the previous chunk")
    ap.add_argument("--vocab", default=os.path.join(HERE, "bert-base-uncased-vocab.txt"))
    ap.add_argument("--tickers", nargs="+", default=["JNJ", "AAPL", "MSFT"],
                    help="companies to build (default: the 3 used in the project)")
    ap.add_argument("--twin-threshold", type=float, default=0.8,
                    help="word-set Jaccard similarity at which a chunk in the other fiscal year counts as a twin")
    ap.add_argument("--no-check", action="store_true",
                    help="skip the check that chunk IDs and bodies match the existing chunks.jsonl")
    a = ap.parse_args()

    tok, tok_name = load_tokenizer(a.vocab)
    ntok = Counter_(tok)
    rows = [r for r in csv.DictReader(open(a.manifest, newline="", encoding="utf-8")) if r["ticker"] in a.tickers]
    if not rows:
        sys.exit(f"no filings for {a.tickers} in {a.manifest}")
    out_path = os.path.join(a.out_dir, "chunks.jsonl")
    recs = []
    stats = defaultdict(lambda: [0, 0, 0])  # chunks, tokens, max tokens
    spans_log, docs, n_total = [], {}, 0
    seen_ids = set()
    for r in rows:
        fy = r["fiscal_year"]
        folder = os.path.join(a.raw_dir, r["ticker"], fy)
        next_idx = Counter()  # chunk numbering continues if a section has two spans (relocated Items 7/8)
        for kind in ("tenk", "ex21"):
            path = os.path.join(folder, r[f"{kind}_file"])
            if not os.path.exists(path):
                sys.exit(f"missing {path}; run data/edgar_10k/download_edgar_10k.py first")
            blocks = html_to_blocks(path)
            if kind == "tenk":
                spans, note = find_sections(blocks)
                doc_type = "10-K"
            else:
                spans, note, doc_type = [(0, len(blocks), "EX21")], "", r["ex21_type"]
            for s, e, code in spans:
                spans_log.append({"ticker": r["ticker"], "fiscal_year": fy, "document": doc_type,
                                  "section": section_label(code)[0], "start_block": s, "end_block": e,
                                  "n_blocks": e - s, "note": note})
                if e <= s:
                    continue
                sec, sec_title = section_label(code)
                header = f"{COMPANY[r['ticker']]} ({r['ticker']}) | {fy} Form 10-K | {sec}. {sec_title}"
                top = long_header(r["ticker"], fy, r["period_end"], sec, sec_title)
                for text, has_tab in chunk_section(blocks[s:e], header, a.max_tokens, a.overlap, ntok, top):
                    idx = next_idx[code]
                    next_idx[code] += 1
                    cid = f"{r['ticker']}_{fy}_{code if code in ('COVER', 'EX21') else 'ITEM' + code}_{idx:04d}"
                    assert cid not in seen_ids, cid
                    seen_ids.add(cid)
                    n = ntok(text)
                    rec = {
                        "chunk_id": cid, "ticker": r["ticker"], "company": COMPANY[r["ticker"]], "cik": r["cik"],
                        "fiscal_year": fy, "period_end": r["period_end"], "filing_date": r["filing_date"],
                        "accession": r["accession"], "document": doc_type, "section": sec,
                        "section_title": sec_title, "chunk_index": idx, "n_tokens": n, "has_table": has_tab,
                        "source_url": r[f"{kind}_url"], "text": text,
                    }
                    recs.append(rec)
                    docs[cid] = text
                    st = stats[(r["ticker"], fy, sec)]
                    st[0] += 1; st[1] += n; st[2] = max(st[2], n)
                    n_total += 1
    if os.path.exists(out_path) and not a.no_check:
        n_old, missing, extra, changed = check_same_chunks(out_path, recs)
        print(f"check against the existing chunks.jsonl: {n_old} old chunks for {', '.join(a.tickers)}, "
              f"{len(missing)} missing, {len(extra)} new, {len(changed)} with a different body")
        if missing or extra or changed:
            for c in (missing + extra + changed)[:10]:
                print("   ", c)
            sys.exit("chunk IDs or bodies changed: nothing was written (rerun with --no-check to overwrite anyway)")
    n_twins = add_twins(recs, a.twin_threshold)
    with open(out_path, "w", encoding="utf-8") as out:
        for rec in recs:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump(docs, open(os.path.join(a.out_dir, "documents.json"), "w", encoding="utf-8"), ensure_ascii=False)
    with open(os.path.join(a.out_dir, "chunk_stats.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "fiscal_year", "section", "chunks", "tokens", "max_chunk_tokens"])
        for (t, fy, sec), (c, n, mx) in stats.items():
            w.writerow([t, fy, sec, c, n, mx])
    with open(os.path.join(a.out_dir, "section_spans.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(spans_log[0]))
        w.writeheader(); w.writerows(spans_log)
    print(f"{n_total} chunks from {len(rows)} filings -> {out_path}")
    print(f"tokenizer: {tok_name}; chunks sized to {a.max_tokens} tokens with the short header, overlap {a.overlap}; "
          f"longest chunk with the new header: {max(r['n_tokens'] for r in recs)} tokens")
    print(f"{n_twins} of {len(recs)} chunks have a twin in the other fiscal year (Jaccard >= {a.twin_threshold})")


if __name__ == "__main__":
    main()
