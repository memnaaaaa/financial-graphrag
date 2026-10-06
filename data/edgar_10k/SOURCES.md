# 10-K corpus: sources and provenance

Selected Oct 5, 2026 by Mohini Tiwari for CSC 8851 (Financial GraphRAG project).
Every filing below was looked up on SEC EDGAR on Oct 5, 2026: company and CIK from
[company_tickers.json](https://www.sec.gov/files/company_tickers.json), filing list from the
EDGAR submissions API (`data.sec.gov/submissions/CIK##########.json`), and document names, types
and sizes from each filing's index page (linked below).

## Selection rule

- **8 companies, 8 different industries** (SEC SIC codes), mixing short and very long subsidiary lists.
- **The two most recent annual 10-K filings per company as of Oct 5, 2026** (16 filings). Amended filings (10-K/A) are excluded.
- **Fiscal years follow each company's own label** (the `dei:DocumentFiscalYearFocus` tag on the 10-K cover). Fiscal years end in different months, so FY2025 means Sep 2025 for Apple, Jun 2025 for Microsoft and P&G, Jan 2025 for Walmart, and Dec 2025 for the rest.
- **Two files per filing:** the 10-K main document (inline XBRL HTML) and Exhibit 21 (list of subsidiaries).

## Companies

| Ticker | Company (EDGAR name) | CIK | SIC industry (EDGAR) | Fiscal years | Exhibit 21 table rows* |
| --- | --- | --- | --- | --- | --- |
| AAPL | Apple Inc. | [320193](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K) | Electronic Computers | FY2025, FY2024 | 21 / 20 |
| MSFT | Microsoft Corp | [789019](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=10-K) | Services-Prepackaged Software | FY2026, FY2025 | 13 / 13 |
| JPM | JPMorgan Chase & Co | [19617](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000019617&type=10-K) | National Commercial Banks | FY2025, FY2024 | 23 / 23 |
| JNJ | Johnson & Johnson | [200406](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000200406&type=10-K) | Pharmaceutical Preparations | FY2025, FY2024 | 433 / 438 |
| XOM | Exxon Mobil Corp | [34088](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000034088&type=10-K) | Petroleum Refining | FY2025, FY2024 | 122 / 130 |
| PG | Procter & Gamble Co | [80424](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000080424&type=10-K) | Soap, Detergents, Cleaning Preparations, Perfumes, Cosmetics | FY2026, FY2025 | 246 / 248 |
| WMT | Walmart Inc. | [104169](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000104169&type=10-K) | Retail-Variety Stores | FY2026, FY2025 | 15 / 15 |
| CAT | Caterpillar Inc. | [18230](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000018230&type=10-K) | Construction Machinery & Equipment | FY2025, FY2024 | 460 / 454 |

\*HTML table rows in Exhibit 21 (newer / older filing), counted Oct 5, 2026. This is a rough size indicator, not an exact subsidiary count: it includes header rows, and some exhibits list several subsidiaries per row.

## Filings (16)

| Ticker | FY | Period end | Filed | Accession | Filing index | 10-K | Exhibit 21 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | FY2025 | 2025-09-27 | 2025-10-31 | 0000320193-25-000079 | [index](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm) | [aapl-20250927.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm) | [EX-21.1](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm) |
| AAPL | FY2024 | 2024-09-28 | 2024-11-01 | 0000320193-24-000123 | [index](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm) | [aapl-20240928.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) | [EX-21.1](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/a10-kexhibit21109282024.htm) |
| MSFT | FY2026 | 2026-06-30 | 2026-07-29 | 0001193125-26-323660 | [index](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/0001193125-26-323660-index.htm) | [msft-20260630.htm](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-ex21.htm) |
| MSFT | FY2025 | 2025-06-30 | 2025-07-30 | 0000950170-25-100235 | [index](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/0000950170-25-100235-index.htm) | [msft-20250630.htm](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-ex21.htm) |
| JPM | FY2025 | 2025-12-31 | 2026-02-13 | 0001628280-26-008131 | [index](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/0001628280-26-008131-index.htm) | [jpm-20251231.htm](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/corp10k2025exhibit21.htm) |
| JPM | FY2024 | 2024-12-31 | 2025-02-14 | 0000019617-25-000270 | [index](https://www.sec.gov/Archives/edgar/data/19617/000001961725000270/0000019617-25-000270-index.htm) | [jpm-20241231.htm](https://www.sec.gov/Archives/edgar/data/19617/000001961725000270/jpm-20241231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/19617/000001961725000270/corp10k2024exhibit21.htm) |
| JNJ | FY2025 | 2025-12-28 | 2026-02-11 | 0000200406-26-000016 | [index](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/0000200406-26-000016-index.htm) | [jnj-20251228.htm](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/ex21-subsidiariesxform10xk.htm) |
| JNJ | FY2024 | 2024-12-29 | 2025-02-13 | 0000200406-25-000038 | [index](https://www.sec.gov/Archives/edgar/data/200406/000020040625000038/0000200406-25-000038-index.htm) | [jnj-20241229.htm](https://www.sec.gov/Archives/edgar/data/200406/000020040625000038/jnj-20241229.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/200406/000020040625000038/ex21-subsidiariesxform10xk.htm) |
| XOM | FY2025 | 2025-12-31 | 2026-02-18 | 0000034088-26-000045 | [index](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/0000034088-26-000045-index.htm) | [xom-20251231.htm](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/xom-20251231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/xomexhibit21123125.htm) |
| XOM | FY2024 | 2024-12-31 | 2025-02-19 | 0000034088-25-000010 | [index](https://www.sec.gov/Archives/edgar/data/34088/000003408825000010/0000034088-25-000010-index.htm) | [xom-20241231.htm](https://www.sec.gov/Archives/edgar/data/34088/000003408825000010/xom-20241231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/34088/000003408825000010/xomexhibit21123124.htm) |
| PG | FY2026 | 2026-06-30 | 2026-08-04 | 0000080424-26-000103 | [index](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/0000080424-26-000103-index.htm) | [pg-20260630.htm](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/fy252610-kexhibit21.htm) |
| PG | FY2025 | 2025-06-30 | 2025-08-04 | 0000080424-25-000076 | [index](https://www.sec.gov/Archives/edgar/data/80424/000008042425000076/0000080424-25-000076-index.htm) | [pg-20250630.htm](https://www.sec.gov/Archives/edgar/data/80424/000008042425000076/pg-20250630.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/80424/000008042425000076/fy242510-kexhibit21.htm) |
| WMT | FY2026 | 2026-01-31 | 2026-03-13 | 0000104169-26-000055 | [index](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/0000104169-26-000055-index.htm) | [wmt-20260131.htm](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/wmt-20260131.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/wmtexhibit21fy26.htm) |
| WMT | FY2025 | 2025-01-31 | 2025-03-14 | 0000104169-25-000021 | [index](https://www.sec.gov/Archives/edgar/data/104169/000010416925000021/0000104169-25-000021-index.htm) | [wmt-20250131.htm](https://www.sec.gov/Archives/edgar/data/104169/000010416925000021/wmt-20250131.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/104169/000010416925000021/wmtexhibit21fy25.htm) |
| CAT | FY2025 | 2025-12-31 | 2026-02-13 | 0000018230-26-000008 | [index](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/0000018230-26-000008-index.htm) | [cat-20251231.htm](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat_exx21x12312025subsidia.htm) |
| CAT | FY2024 | 2024-12-31 | 2025-02-14 | 0000018230-25-000008 | [index](https://www.sec.gov/Archives/edgar/data/18230/000001823025000008/0000018230-25-000008-index.htm) | [cat-20241231.htm](https://www.sec.gov/Archives/edgar/data/18230/000001823025000008/cat-20241231.htm) | [EX-21](https://www.sec.gov/Archives/edgar/data/18230/000001823025000008/cat_exx21x12312024subsidia.htm) |

## How the data was checked (Oct 5, 2026)

For all 16 filings, the live EDGAR documents were checked as follows:

- **10-K cover tags:** the main document's inline-XBRL cover says `dei:DocumentType` = 10-K and `dei:DocumentFiscalYearFocus` equals the fiscal year in this table.
- **Company identity:** the company's 10-digit CIK appears in the main document.
- **Exhibit 21 content:** every Exhibit 21 mentions subsidiaries.

`download_edgar_10k.py` repeats these checks on downloaded copies. It also writes a SHA-256 for each file to `download_log.csv`, so anyone can confirm later that the files have not changed since download.

## Notes

- **Exxon Mobil:** the ticker XOM now maps on EDGAR to *ExxonMobil Holdings Corp* (CIK 2115436), which had filed no 10-K as of Oct 5, 2026. Both filings here come from *Exxon Mobil Corp*, CIK 34088.
- **JPMorgan:** JPMorgan files so often that its FY2024 10-K is not in the recent-filings list of the submissions API. It was found in the paged history file `CIK0000019617-submissions-001.json`.
- **File sizes:** downloaded files can be a few hundred bytes larger than the size on the EDGAR index page. In browser fetches every file was 111 bytes larger. The content checks are therefore what decides pass or fail, not the byte count.

## How to download

From this folder, with any Python 3.8+:

```
python download_edgar_10k.py --user-agent "Mohini Tiwari your.email@student.gsu.edu"
```

The script downloads 32 files (about 88 MB) into `raw/<TICKER>/<FY>/`, waits 0.25 s between requests (SEC asks for at most 10 per second), and prints one line per file. `raw/` is git-ignored. Commit the manifest, this file and `download_log.csv`, not the raw HTML.
