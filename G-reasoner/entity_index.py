"""Find graph entities named in a question, for G-reasoner's start nodes.

Node names in the team graph look like "Apple Inc.", "DARZALEX (JNJ)", "Innovative Medicine (JNJ)"
and "FY2025 (AAPL)", so a question saying "Apple" or "DARZALEX" has to be mapped to them. This
builds an alias table from nodes.csv (no LLM, no model download) and returns node names directly.

Standard library only, so it can be tested without gfmrag:
    python entity_index.py <stage1 dir> "What were Apple's total net sales in fiscal 2025?"
"""
from __future__ import annotations

import ast
import csv
import re
import sys
from collections import defaultdict

csv.field_size_limit(sys.maxsize)

# Kinds that can be start nodes. Value (attribute) and document nodes are what we retrieve.
# Organization: other companies named in prose (e.g. Genmab A/S), added by the phase 2 graph (fin10k_v1).
LINKABLE = {"Company", "Segment", "BusinessLine", "Product", "Metric", "Subsidiary", "Location", "Organization"}
# When one alias fits several nodes, keep only the highest-priority kind.
PRIORITY = ["Company", "Segment", "BusinessLine", "Product", "Metric", "Location", "Subsidiary", "Organization"]
GENERIC = {"products", "services", "other services", "other", "other products and services", "total"}

COMPANY_ALIASES = {
    "AAPL": ["Apple", "AAPL"],
    "MSFT": ["Microsoft", "MSFT"],
    "JNJ": ["J&J", "JNJ", "Johnson and Johnson"],
    "JPM": ["JPMorgan", "JPMorgan Chase", "JPM"],
    "XOM": ["ExxonMobil", "Exxon Mobil", "Exxon", "XOM"],
    "PG": ["Procter & Gamble", "P&G"],
    "WMT": ["Walmart", "WMT"],
    "CAT": ["Caterpillar", "CAT"],
}
# Question wording -> metric node name (only names that exist in the graph are used).
# Longer aliases win over shorter ones ("operating profit" before "profit", "sales and marketing"
# before "sales"), so a multi-word phrase only needs to be listed here to stop the short match.
METRIC_ALIASES = {
    "Revenue": ["revenue", "revenues", "net sales", "total net sales", "sales", "top line", "top-line"],
    "Research and development expense": ["research and development", "R&D"],
    "Acquired in-process research and development": ["in-process research and development", "in-process R&D",
                                                      "IPR&D", "acquired IPR&D"],
    "Net income": ["net income", "net earnings", "profit", "bottom line", "bottom-line"],
    "Diluted earnings per share": ["diluted earnings per share", "diluted EPS", "earnings per share", "EPS"],
    "Basic earnings per share": ["basic earnings per share", "basic EPS"],
    "Operating income": ["operating income", "operating profit", "operating earnings", "income from operations"],
    "Gross margin": ["gross margin", "gross profit"],
    "Cost of sales": ["cost of sales", "cost of revenue"],
    # Apple and J&J report marketing inside SG&A. Microsoft reports "Sales and marketing" as its own
    # line, which the graph does not hold, so for MSFT this is the closest metric node, not an exact one.
    "Selling, general and administrative expense": ["selling, general and administrative", "SG&A",
                                                    "sales and marketing", "selling and marketing",
                                                    "selling, marketing and administrative",
                                                    "general and administrative", "marketing expense",
                                                    "marketing expenses"],
    "Income before income taxes": ["income before income taxes", "income before taxes", "pretax income",
                                   "pre-tax income", "earnings before income taxes",
                                   "earnings before provision for taxes on income"],
    "Income tax expense": ["income tax expense", "provision for income taxes", "provision for taxes on income",
                           "income taxes", "tax expense"],
    "Total assets": ["total assets"],
    "Total liabilities": ["total liabilities"],
    "Long-term debt": ["long-term debt"],
    "Shareholders' equity": ["shareholders' equity", "stockholders' equity", "total equity"],
    "Goodwill": ["goodwill"],
    "Cash and cash equivalents": ["cash and cash equivalents"],
    "Operating cash flow": ["operating cash flow", "cash from operations"],
    "Capital expenditures": ["capital expenditures", "capex"],
    "Share repurchases": ["share repurchases", "buybacks"],
    "Dividends paid": ["dividends paid", "dividends"],
}
LEGAL_SUFFIX = re.compile(r",?\s+(Inc\.?|LLC|L\.L\.C\.|Ltd\.?|Limited|Corp\.?|Corporation|Co\.|Company|"
                          r"plc|PLC|AG|GmbH|B\.V\.|N\.V\.|S\.A\.|SARL|A/S|Pty\.? Ltd\.?|Pte\.? Ltd\.?)$")
TICKER_TAG = re.compile(r"\s\(([A-Z]{1,5})\)$")
YEAR = re.compile(r"\b(?:FY\s?|fiscal(?:\s+year)?\s+)?(20\d\d)\b", re.I)
# Relative years. "Latest" means the company's newest filing year (the max FiscalYear node, which is
# FY2025 for AAPL and JNJ and FY2026 for MSFT); "last year" in a question means the last completed
# fiscal year, i.e. the same. "Prior year" is one year before the latest, or before the latest year the
# question names. Both are only used when the question gives no explicit year for "latest".
REL_LATEST = re.compile(r"\b(?:most recent|latest|last|current|this)\s+(?:fiscal\s+)?(?:year|10-K)\b", re.I)
REL_PRIOR = re.compile(r"\b(?:prior|previous|preceding)\s+(?:fiscal\s+)?year\b|\byear before\b", re.I)


class EntityIndex:
    def __init__(self, nodes_csv: str):
        self.kind, self.ticker = {}, {}
        self.fiscal_years = {}                       # (ticker, "FY2025") -> node name
        aliases = defaultdict(set)                   # alias -> node names
        generic = defaultdict(set)                   # common-word alias ("Services") -> ticker-tagged nodes
        for r in csv.DictReader(open(nodes_csv, encoding="utf-8")):
            if r["type"] != "entity":
                continue
            name = r["name"]
            attrs = ast.literal_eval(r["attributes"]) if r["attributes"] else {}
            kind = attrs.get("kind", "entity")
            self.kind[name] = kind
            self.ticker[name] = attrs.get("ticker") or attrs.get("parent_ticker")
            if kind == "FiscalYear":
                m = re.match(r"(FY\d{4}) \((\w+)\)$", name)
                if m:
                    self.fiscal_years[(m.group(2), m.group(1))] = name
                continue
            if kind not in LINKABLE:
                continue
            base = TICKER_TAG.sub("", name)
            # Split "A/B" names into both parts, but not a legal suffix like "Genmab A/S".
            forms = {name, base} | (set(base.split("/")) if not LEGAL_SUFFIX.search(base) else set())
            if kind in ("Company", "Subsidiary", "Organization"):
                forms.add(LEGAL_SUFFIX.sub("", base))
            if kind == "Company":
                forms |= set(COMPANY_ALIASES.get(self.ticker[name], []))
            if kind == "Metric":
                forms |= set(METRIC_ALIASES.get(name, []))
            for f in forms:
                f = f.strip()
                if len(f) < 2:
                    continue
                if f.lower() not in GENERIC:
                    aliases[f].add(name)
                elif f == base and self.ticker[name]:
                    # "Services (AAPL)": too common a word to match freely; matched case-sensitively
                    # and only when the question names that node's company (see find()).
                    generic[f].add(name)
        self.names = set(self.kind)
        self.latest_fy = {}                          # ticker -> newest fiscal year number
        for t, fy in self.fiscal_years:
            self.latest_fy[t] = max(self.latest_fy.get(t, 0), int(fy[2:]))
        # Longest aliases first, so "Innovative Medicine" wins over "Medicine".
        self.aliases = sorted(aliases.items(), key=lambda x: -len(x[0]))
        self.patterns = [(re.compile(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])",
                                     0 if len(a) < 5 or a.isupper() else re.I), ns, False)
                         for a, ns in self.aliases]
        self.patterns += [(re.compile(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])"), ns, True)
                          for a, ns in sorted(generic.items(), key=lambda x: -len(x[0]))]

    def find(self, question: str) -> list[str]:
        """Node names mentioned in the question (companies, products, segments, metrics, fiscal years)."""
        q = question.replace("’", "'")
        taken, hits = [], []                         # taken = matched character spans
        for pat, nodes, is_generic in self.patterns:
            for m in pat.finditer(q):
                if any(m.start() < e and s < m.end() for s, e in taken):
                    continue                         # inside a longer match already used
                taken.append((m.start(), m.end()))
                hits.append((nodes, is_generic))
        tickers = {self.ticker[n] for ns, _ in hits for n in ns if self.kind[n] == "Company"}
        out = []
        for nodes, is_generic in hits:
            if is_generic:                           # only for a company the question names
                nodes = [n for n in nodes if self.ticker[n] in tickers]
                if not nodes:
                    continue
            nodes = [n for n in nodes if not tickers or self.ticker[n] in (None, *tickers)] or list(nodes)
            best = min(PRIORITY.index(self.kind[n]) for n in nodes)
            out += sorted(n for n in nodes if PRIORITY.index(self.kind[n]) == best)
        # Fiscal years are per company ("FY2025 (AAPL)"); link the year for each company named. With no
        # company named, use the companies of the matched nodes ("iPhone (AAPL)" -> AAPL), else all.
        year_tickers = (sorted(tickers)
                        or sorted({self.ticker[n] for n in out if self.ticker.get(n)} & set(self.latest_fy))
                        or sorted(self.latest_fy))
        years = {int(m.group(1)) for m in YEAR.finditer(q)}
        wanted = set()                               # (ticker, year)
        for t in year_tickers:
            wanted |= {(t, y) for y in years}
            if not years and REL_LATEST.search(q):
                wanted.add((t, self.latest_fy[t]))
            if REL_PRIOR.search(q):
                wanted.add((t, (max(years) if years else self.latest_fy[t]) - 1))
        for t, y in sorted(wanted, key=lambda x: (x[1], x[0])):    # sorted: same output on every run
            n = self.fiscal_years.get((t, f"FY{y}"))
            if n:
                out.append(n)
        return list(dict.fromkeys(out))              # dedupe, keep order


if __name__ == "__main__":
    idx = EntityIndex(sys.argv[1].rstrip("/") + "/nodes.csv")
    for q in sys.argv[2:]:
        print(q, "->", idx.find(q))
