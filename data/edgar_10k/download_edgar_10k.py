"""Download the 10-K main documents and Exhibit 21 files listed in filings_manifest.csv from SEC EDGAR.

Usage (from this folder):
    python download_edgar_10k.py --user-agent "Your Name your.email@example.edu"

SEC's fair-access policy asks automated clients to send a User-Agent naming who you are and a
contact email, and to stay under 10 requests per second. This script waits 0.25 s between requests.

Output:
    raw/<TICKER>/<FISCAL_YEAR>/<file>   the files exactly as served by EDGAR
    download_log.csv                    one row per file: URL, expected vs. actual bytes, SHA-256, time
Each file is checked for content, not just presence:
  10-K:  the inline-XBRL cover tags must say dei:DocumentType = 10-K and dei:DocumentFiscalYearFocus =
         the manifest's fiscal year, and the company's 10-digit CIK must appear in the document.
  EX-21: the text must mention "subsidiar".
The byte count is also compared with the size on EDGAR's filing index page. Served files can differ
from that listing by a few hundred bytes, so a size difference alone is reported but not failed.
The script exits with code 1 if any file is missing or fails a content check. Standard library only.
"""
import argparse, csv, datetime, hashlib, os, re, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = "https://www.sec.gov"


def fetch(url, ua, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503) and attempt < retries:
                time.sleep(5 * attempt)  # back off; 403 usually means a missing/invalid User-Agent
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries:
                time.sleep(5 * attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def dei(text, tag):
    """Value of an inline-XBRL dei:<tag> cover fact, with nested HTML stripped."""
    m = re.search(r'name="dei:%s"[^>]*>(.*?)</ix:nonNumeric>' % tag, text, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else None


def check(kind, data, row):
    """Return (passed, note) for a downloaded file."""
    if not data:
        return False, "no data"
    text = data.decode("utf-8", errors="replace")
    if kind == "ex21":
        return (bool(re.search("subsidiar", text, re.I)), "mentions subsidiaries")
    doc_type, fy = dei(text, "DocumentType"), dei(text, "DocumentFiscalYearFocus")
    cik_ok = row["cik"].zfill(10) in text
    ok = doc_type == "10-K" and fy == row["fiscal_year"][2:] and cik_ok
    return ok, f"DocumentType={doc_type}; FiscalYearFocus={fy}; CIK found={cik_ok}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--user-agent", default=os.environ.get("SEC_USER_AGENT"),
                   help='"Name email@domain" (or set SEC_USER_AGENT)')
    p.add_argument("--manifest", default=os.path.join(HERE, "filings_manifest.csv"))
    p.add_argument("--out", default=os.path.join(HERE, "raw"))
    p.add_argument("--only", nargs="*", help="limit to these tickers, e.g. --only JNJ CAT")
    p.add_argument("--base-url", default=SEC, help=argparse.SUPPRESS)  # for offline testing only
    a = p.parse_args()
    if not a.user_agent or "@" not in a.user_agent:
        sys.exit('Give --user-agent "Your Name your.email@example.edu" (SEC requires a contact email).')

    with open(a.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if a.only:
        rows = [r for r in rows if r["ticker"] in {t.upper() for t in a.only}]

    log, bad = [], 0
    for r in rows:
        folder = os.path.join(a.out, r["ticker"], r["fiscal_year"])
        os.makedirs(folder, exist_ok=True)
        for kind in ("tenk", "ex21"):
            name, url, expected = r[f"{kind}_file"], r[f"{kind}_url"], int(r[f"{kind}_bytes"])
            url = url.replace(SEC, a.base_url.rstrip("/"), 1)
            path = os.path.join(folder, name)
            existing = open(path, "rb").read() if os.path.exists(path) else b""
            if existing and check(kind, existing, r)[0]:
                data, status = existing, "already present"
            else:
                try:
                    data = fetch(url, a.user_agent)
                    with open(path, "wb") as out:
                        out.write(data)
                    status = "downloaded"
                except Exception as e:  # keep going, report at the end
                    data, status = b"", f"FAILED: {e}"
                time.sleep(0.25)
            ok, note = check(kind, data, r)
            bad += not ok
            size_diff = len(data) - expected
            log.append({
                "ticker": r["ticker"], "fiscal_year": r["fiscal_year"], "accession": r["accession"],
                "document": "10-K" if kind == "tenk" else r["ex21_type"], "file": name,
                "source_url": r[f"{kind}_url"], "expected_bytes": expected, "actual_bytes": len(data),
                "size_diff_vs_index": size_diff,
                "content_check_passed": ok, "content_check": note, "sha256": hashlib.sha256(data).hexdigest() if data else "",
                "status": status,
                "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })
            print(f"{'OK ' if ok else 'BAD'} {r['ticker']:5} {r['fiscal_year']} {name:32} {len(data):>11,} bytes  {status}; {note}")

    with open(os.path.join(HERE, "download_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0]))
        w.writeheader()
        w.writerows(log)
    print(f"\n{len(log) - bad}/{len(log)} files passed the content checks. Log: download_log.csv")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
