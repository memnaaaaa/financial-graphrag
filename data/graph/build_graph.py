"""Build a rule-based knowledge graph from 10-K filings, in the gfmrag "bring your own graph"
format (nodes.csv, relations.csv, edges.csv).

Phase 1 (this script, no LLM):
  - Company nodes from data/edgar_10k/filings_manifest.csv
  - Subsidiaries + jurisdictions from Exhibit 21
  - Segments, business lines, products, geographies and reported numbers from the inline XBRL
    tags inside the 10-K. Every number becomes its own Value node (type "attribute").
  - Document nodes = the chunks in data/chunks/chunks.jsonl (named by chunk_id)
  - is_mentioned_in edges from entities and Values to the chunks whose text contains them
  - Source fields on every Value (filing, accession, URL, section, chunk, XBRL fact id): where the
    number is printed in the 10-K. All places it is printed go to <name>/value_sources.csv.

Run from the repo root:
    python data/graph/build_graph.py                       # JNJ AAPL MSFT, both fiscal years
    python data/graph/build_graph.py --tickers JNJ AAPL MSFT JPM --name fin10k_v1

Output: data/graph/<name>/processed/stage1/{nodes,relations,edges}.csv plus graph_stats.json
and value_sources.csv.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import sys

from lxml import etree, html

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chunks"))
import build_chunks  # noqa: E402  (same HTML walk and sections as the chunks, to place each number)

NS = {
    "ix": "http://www.xbrl.org/2013/inlineXBRL",
    "xbrli": "http://www.xbrl.org/2003/instance",
    "xbrldi": "http://xbrl.org/2006/xbrldi",
}

# ---------------------------------------------------------------- curated XBRL concepts
# local concept name -> (metric node name, words that must appear in a chunk to link a
# company-level number to it)
METRICS = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": ("Revenue", ["sales", "revenue"]),
    "Revenues": ("Revenue", ["sales", "revenue"]),
    "CostOfGoodsAndServicesSold": ("Cost of sales", ["cost of"]),
    "CostOfRevenue": ("Cost of sales", ["cost of"]),
    "GrossProfit": ("Gross margin", ["gross"]),
    # Total R&D. Companies that also tag acquired in-process R&D separately (J&J) report their
    # total under ...ExcludingAcquiredInProcessCost and use ResearchAndDevelopmentExpense for the
    # in-process charges alone, so the "Excluding" concept is listed first and wins (see IPRD_METRIC).
    "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost": (
        "Research and development expense", ["research"]),
    "ResearchAndDevelopmentExpense": ("Research and development expense", ["research"]),
    "SellingGeneralAndAdministrativeExpense": ("Selling, general and administrative expense",
                                               ["general and administrative"]),
    "OperatingIncomeLoss": ("Operating income", ["operating income"]),
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": (
        "Income before income taxes", ["before"]),
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments": (
        "Income before income taxes", ["before"]),
    "IncomeTaxExpenseBenefit": ("Income tax expense", ["tax"]),
    "NetIncomeLoss": ("Net income", ["net income", "net earnings"]),
    "EarningsPerShareBasic": ("Basic earnings per share", ["per share"]),
    "EarningsPerShareDiluted": ("Diluted earnings per share", ["per share"]),
    "Assets": ("Total assets", ["total assets"]),
    "Liabilities": ("Total liabilities", ["total liabilities"]),
    "StockholdersEquity": ("Shareholders' equity", ["equity"]),
    "CashAndCashEquivalentsAtCarryingValue": ("Cash and cash equivalents", ["cash"]),
    "LongTermDebtNoncurrent": ("Long-term debt", ["debt"]),
    "Goodwill": ("Goodwill", ["goodwill"]),
    "NetCashProvidedByUsedInOperatingActivities": ("Operating cash flow", ["operating activities"]),
    "PaymentsToAcquirePropertyPlantAndEquipment": ("Capital expenditures", ["property", "capital"]),
    "PaymentsOfDividends": ("Dividends paid", ["dividend"]),
    "PaymentsOfDividendsCommonStock": ("Dividends paid", ["dividend"]),
    "PaymentsForRepurchaseOfCommonStock": ("Share repurchases", ["repurchase"]),
}
# When a company tags ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost, its
# ResearchAndDevelopmentExpense facts are the acquired in-process R&D charges, kept as this metric.
IPRD_METRIC = ("Acquired in-process research and development", ["in-process"])
# Concept order in METRICS = priority when two concepts give the same metric for the same period.
PRIORITY = {c: i for i, c in enumerate(METRICS)}
# Dimensions we keep. A fact with any other dimension (debt instrument, equity component...)
# is skipped.
SEG_AXIS = "StatementBusinessSegmentsAxis"
SUB_AXIS = "SubsegmentsAxis"            # J&J franchises (Oncology, Immunology, ...)
PROD_AXIS = "ProductOrServiceAxis"
GEO_AXIS = "StatementGeographicalAxis"
CONS_AXIS = "ConsolidationItemsAxis"    # kept only when the member is OperatingSegmentsMember
KEEP_AXES = {SEG_AXIS, SUB_AXIS, PROD_AXIS, GEO_AXIS, CONS_AXIS}

# Readable names for XBRL members the CamelCase splitter gets wrong. Anything not listed is
# split automatically ("InnovativeMedicineMember" -> "Innovative Medicine").
MEMBER_NAMES = {
    "IPhoneMember": "iPhone", "IPadMember": "iPad", "MacMember": "Mac",
    "WearablesHomeandAccessoriesMember": "Wearables, Home and Accessories",
    "ProductMember": "Products", "ServiceMember": "Services",
    "ServiceOtherMember": "Other services",
    "XBOXMember": "Xbox", "LinkedInCorporationMember": "LinkedIn",
    "MicrosoftThreeSixFiveCommercialProductsAndCloudServicesMember":
        "Microsoft 365 Commercial products and cloud services",
    "MicrosoftThreeSixFiveConsumerProductsAndCloudServicesMember":
        "Microsoft 365 Consumer products and cloud services",
    "ServerProductsAndCloudServicesMember": "Server products and cloud services",
    "DynamicsProductsAndCloudServicesMember": "Dynamics products and cloud services",
    "AmericasSegmentMember": "Americas", "EuropeSegmentMember": "Europe",
    "GreaterChinaSegmentMember": "Greater China", "JapanSegmentMember": "Japan",
    "RestOfAsiaPacificSegmentMember": "Rest of Asia Pacific",
    "ShockwaveMedicalInc.Member": "Shockwave Medical",
    # J&J tags several brands as one run-together member; "/" separates names used for text matching
    "MedTechMember": "MedTech",
    "CardiovascularMetabolismOtherMember": "Cardiovascular, Metabolism & Other",
    "OtherMember": "Other Cardiovascular, Metabolism & Other products",
    "CONTACTLENSESOTHERMember": "Contact Lenses/Other",
    "INVEGASUSTENNAXEPLIONTRINZATREVICTAMember": "INVEGA SUSTENNA/XEPLION/INVEGA TRINZA/TREVICTA",
    "PREZISTAPREZCOBIXREZOLSTASYMTUZAMember": "PREZISTA/PREZCOBIX/REZOLSTA/SYMTUZA",
    "RYBREVANTLAZCLUZEMember": "RYBREVANT/LAZCLUZE",
    "SPINESPORTSOTHERMember": "Spine, Sports & Other",
    "OTHERNEUROSCIENCEMember": "Other Neuroscience",
    "ADVANCEDMember": "Advanced Surgery", "GENERALMember": "General Surgery",
    "SURGICALMember": "Surgical Vision", "HIPSMember": "Hips", "KNEESMember": "Knees",
    "TRAUMAMember": "Trauma", "ELECTROPHYSIOLOGYMember": "Electrophysiology",
    "EDURANTrilpivirineMember": "EDURANT/rilpivirine",
    "CONCERTAMethylphenidateMember": "CONCERTA/methylphenidate",
    "SimponiSimponiAriaMember": "SIMPONI/SIMPONI ARIA",
    "COVID19Member": "COVID-19 vaccine", "UNITEDSTATESExportsMember": "U.S. exports",
}
# Members that are totals or not a business (dimension dropped / fact skipped).
TOTAL_MEMBERS = {"SegmentsTotalMember"}
SKIP_MEMBERS = {"ShippingAndHandlingMember"}
GEO_NAMES = {
    "US": "United States", "CN": "China", "NonUsMember": "Outside the United States",
    "EuropeMember": "Europe",
    "WesternHemisphereExcludingUSMember": "Western Hemisphere excluding United States",
    "AsiaPacificAfricaMember": "Asia-Pacific and Africa",
}
# Member names too generic to string-match in text.
NO_TEXT_MATCH = {"Products", "Services", "Other services", "Other", "Other products and services"}

US_STATES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "District of Columbia", "Puerto Rico",
}
LOCATION_ALIASES = {
    "u.s.": "United States", "us": "United States", "usa": "United States",
    "united states of america": "United States", "the netherlands": "Netherlands",
    "england": "United Kingdom", "england and wales": "United Kingdom",
    "england & wales": "United Kingdom", "uk": "United Kingdom", "great britain": "United Kingdom",
    "scotland": "United Kingdom", "republic of korea": "South Korea", "korea": "South Korea",
    "people's republic of china": "China", "prc": "China", "korea, republic of": "South Korea",
    "taiwan (province of china)": "Taiwan", "venezuela, bolivarian republic of": "Venezuela",
    "russian federation": "Russia",
}

RELATIONS = {
    "has_subsidiary": "A company owns the subsidiary (Exhibit 21 of the 10-K).",
    "incorporated_in": "A subsidiary is incorporated or organized in this jurisdiction.",
    "part_of": "A location (e.g. a U.S. state) is part of a larger location.",
    "has_segment": "A company reports this operating segment.",
    "has_business_line": "A segment contains this business line or franchise.",
    "has_product": "A company, segment or business line sells this product or product line.",
    "has_value": "An entity has this reported number (a Value node).",
    "of_metric": "A Value node measures this financial metric.",
    "for_period": "A Value node covers this fiscal year (or is measured at its end).",
    "in_location": "A Value node is limited to this geographic area.",
    "is_mentioned_in": "An entity or number appears in the document chunk.",
}


# ---------------------------------------------------------------- helpers
def humanize(member):
    local = member.split(":")[-1]
    if local in MEMBER_NAMES:
        return MEMBER_NAMES[local]
    s = re.sub(r"Member$", "", local)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)      # camelCase -> camel Case
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)    # ABCDef -> ABC Def
    s = s.replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ")
    return s.strip(" .")


def norm_location(raw):
    s = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip(" ,;*")
    s = re.sub(r",?\s*(U\.\s?S\.(\s?A\.?)?|USA|United States)$", "", s).strip(" ,.")
    if not s:
        return "United States"
    key = s.lower()
    if key in LOCATION_ALIASES:
        return LOCATION_ALIASES[key]
    return s


def fiscal_label(end):
    """52/53-week years can end in the first days of January (J&J FY2020 ended 2021-01-03)."""
    d = dt.date.fromisoformat(end)
    year = d.year - 1 if (d.month == 1 and d.day <= 7) else d.year
    return f"FY{year}"


def fmt_value(v, unit):
    if unit == "USD/shares":
        return f"${v:,.2f} per share"
    if unit == "USD":
        m = v / 1e6
        sign = "-" if m < 0 else ""
        m = abs(m)
        body = f"{m:,.0f}" if abs(m - round(m)) < 1e-9 else f"{m:,.1f}"
        return f"{sign}${body} million"
    return f"{v:,} {unit}"


def ix_number(el):
    text = "".join(el.itertext()).strip()
    fmt = (el.get("format") or "").split(":")[-1]
    if fmt in ("fixed-zero", "zerodash", "numwordsen") or text in ("-", "—", "–", ""):
        num = 0.0
    else:
        num = float(re.sub(r"[^\d.]", "", text) or 0)
    num *= 10 ** int(el.get("scale") or 0)
    if el.get("sign") == "-":
        num = -num
    return num, text


# ---------------------------------------------------------------- graph container
class Graph:
    def __init__(self):
        self.nodes = {}          # name -> (type, attributes)
        self.edges = {}          # (source, relation, target) -> attributes
        self.aliases = {}        # name -> (list of text aliases, scope ticker or None)
        self.value_sources = []  # one row per place a Value's number is printed (value_sources.csv)

    def node(self, name, ntype, **attrs):
        if name in self.nodes:
            old_type, old = self.nodes[name]
            assert old_type == ntype, f"type clash for {name!r}: {old_type} vs {ntype}"
            for k, v in attrs.items():
                old.setdefault(k, v)
        else:
            self.nodes[name] = (ntype, dict(attrs))
        return name

    def edge(self, s, r, t, **attrs):
        assert r in RELATIONS, r
        cur = self.edges.setdefault((s, r, t), {})
        for k, v in attrs.items():
            if isinstance(v, list):
                cur[k] = sorted(set(cur.get(k, [])) | set(v))
            else:
                cur.setdefault(k, v)


# ---------------------------------------------------------------- Exhibit 21
def parse_ex21(path):
    raw = open(path, "rb").read()
    raw = re.sub(rb"(?is)^.*?(<html)", rb"\1", raw, count=1)
    doc = html.fromstring(raw)
    out = []
    for tr in doc.xpath("//tr"):
        cells = [re.sub(r"\s+", " ", c.text_content().replace("\xa0", " ")).strip()
                 for c in tr.xpath("./td|./th")]
        cells = [c for c in cells if c]
        if len(cells) != 2:
            continue
        name, juris = cells
        if re.search(r"(?i)name of|jurisdiction|incorporat|^name$|subsidiar(y|ies):?$", name + " " + juris) \
                and not re.search(r"(?i)\b(inc|llc|ltd|limited|gmbh|b\.v|s\.a|corp|co\.)", name):
            continue
        out.append((name, juris))
    return out


# ---------------------------------------------------------------- inline XBRL
def parse_xbrl(path):
    doc = etree.fromstring(open(path, "rb").read(),
                           etree.XMLParser(huge_tree=True, recover=True))
    ctx = {}
    for c in doc.iterfind(".//xbrli:context", NS):
        per = c.find("xbrli:period", NS)
        dims = {}
        for m in c.iterfind(".//xbrldi:explicitMember", NS):
            dims[m.get("dimension").split(":")[-1]] = m.text.strip()
        ctx[c.get("id")] = (per.findtext("xbrli:startDate", namespaces=NS),
                            per.findtext("xbrli:endDate", namespaces=NS),
                            per.findtext("xbrli:instant", namespaces=NS), dims)
    units = {}
    for u in doc.iterfind(".//xbrli:unit", NS):
        num = [m.text.strip().split(":")[-1] for m in u.iterfind(".//xbrli:unitNumerator/xbrli:measure", NS)]
        den = [m.text.strip().split(":")[-1] for m in u.iterfind(".//xbrli:unitDenominator/xbrli:measure", NS)]
        plain = [m.text.strip().split(":")[-1] for m in u.findall("xbrli:measure", NS)]
        units[u.get("id")] = "/".join(num + den) if den else "".join(plain)
    facts = []
    for f in doc.iterfind(".//ix:nonFraction", NS):
        concept = f.get("name").split(":")[-1]
        if concept not in METRICS or f.get("contextRef") not in ctx:
            continue
        start, end, instant, dims = ctx[f.get("contextRef")]
        if set(dims) - KEEP_AXES or any(v.split(":")[-1] in SKIP_MEMBERS for v in dims.values()):
            continue
        dims = {k: v for k, v in dims.items() if v.split(":")[-1] not in TOTAL_MEMBERS}
        if CONS_AXIS in dims:
            if not dims[CONS_AXIS].endswith("OperatingSegmentsMember"):
                continue
            dims = {k: v for k, v in dims.items() if k != CONS_AXIS}
        if start:                                   # duration: keep full fiscal years only
            days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days
            if not 350 <= days <= 380:
                continue
        value, text = ix_number(f)
        if value == 0:                              # dashes in tables ("—") carry no information
            continue
        unit = units.get(f.get("unitRef"))
        if unit not in ("USD", "USD/shares"):
            continue
        facts.append(dict(concept=concept, start=start, end=end or instant,
                          instant=bool(instant), dims=dims, value=value, text=text, unit=unit,
                          fact_id=f.get("id"), context_ref=f.get("contextRef")))
    return facts


# ---------------------------------------------------------------- where each number is printed
def locate_facts(tenk_path, filing_chunks, printed):
    """Place inline-XBRL facts in the filing's sections and chunks.

    Walks the 10-K exactly as build_chunks.py does (same blocks, same sections), so each fact's
    paragraph or table row is known. The chunk is the first one of that section, at or after the
    previous fact's chunk (blocks and chunks run in the same order), that has a line taken from that
    block and showing the printed number; following chunks that repeat the line (overlap) are added.

    filing_chunks: {section: [(chunk_id, [body lines])]} in chunk order.
    printed: {fact_id: text as printed}, the facts to place.
    Returns {fact_id: (section, section_title, [chunk_ids])}; chunk_ids is empty if no chunk matched.
    Facts hidden from the reader (not in the text) are left out.
    """
    blocks = build_chunks.html_to_blocks(tenk_path, track_facts=True)
    spans, _ = build_chunks.find_sections(blocks)
    out, ptr = {}, collections.Counter()

    def holds(lines, block_text, num):
        return any(num in ln and ln in block_text for ln in lines)

    for s, e, code in spans:
        sec, title = build_chunks.section_label(code)
        cks = filing_chunks.get(sec, [])
        for b in blocks[s:e]:
            for fid in b.get("fact_ids", []):
                if fid not in printed:
                    continue
                num = printed[fid]
                hit = next((i for i in range(ptr[sec], len(cks)) if holds(cks[i][1], b["text"], num)), None)
                if hit is None:   # out of order (should be rare): search the whole section
                    hit = next((i for i in range(len(cks)) if holds(cks[i][1], b["text"], num)), None)
                ids = []
                if hit is not None:
                    ptr[sec] = max(ptr[sec], hit)
                    j = hit
                    while j < len(cks) and holds(cks[j][1], b["text"], num):
                        ids.append(cks[j][0])
                        j += 1
                out[fid] = (sec, title, ids)
    return out


SECTION_RANK = {"Item 8": 0, "Item 7": 1}   # primary source: audited statements first, then MD&A


# ---------------------------------------------------------------- build
def build(repo, tickers):
    g = Graph()
    manifest = [r for r in csv.DictReader(open(os.path.join(repo, "data/edgar_10k/filings_manifest.csv"),
                                               encoding="utf-8")) if r["ticker"] in tickers]
    chunks = [json.loads(l) for l in open(os.path.join(repo, "data/chunks/chunks.jsonl"), encoding="utf-8")]
    chunks = [c for c in chunks if c["ticker"] in tickers]
    company_name = {c["ticker"]: c["company"] for c in chunks}

    # Companies
    for r in manifest:
        t = r["ticker"]
        name = g.node(company_name[t], "entity", kind="Company", ticker=t, cik=r["cik"],
                      industry=r["sic_description"])
        g.aliases[name] = ([re.sub(r"(,? Inc\.?| Corporation)$", "", company_name[t])], t)

    def location(raw):
        loc = norm_location(raw)
        g.node(loc, "entity", kind="Location")
        g.aliases.setdefault(loc, ([loc], None))
        if loc in US_STATES:
            g.node("United States", "entity", kind="Location")
            g.aliases.setdefault("United States", (["United States"], None))
            g.edge(loc, "part_of", "United States")
        return loc

    # Subsidiaries (Exhibit 21)
    for r in manifest:
        t, fy = r["ticker"], r["fiscal_year"]
        path = os.path.join(repo, "data/edgar_10k/raw", t, fy, r["ex21_file"])
        for sub, juris in parse_ex21(path):
            if sub.lower() == company_name[t].lower():          # the parent itself is listed
                g.edge(company_name[t], "incorporated_in", location(juris))
                continue
            if sub in g.nodes and g.nodes[sub][1].get("kind") != "Subsidiary":
                sub = f"{sub} (subsidiary of {t})"
            g.node(sub, "entity", kind="Subsidiary", parent_ticker=t)
            g.aliases[sub] = ([re.sub(r"\s*\(.*?subsidiary of.*\)$", "", sub)], t)
            g.edge(company_name[t], "has_subsidiary", sub, source_filings=[f"{t} {fy}"])
            g.edge(sub, "incorporated_in", location(juris))

    # XBRL facts, deduplicated across the two filings of each company (newest filing wins).
    # When two different concepts give the same metric for the same period and dimensions, the one
    # listed first in METRICS wins and the other is reported as a conflict (never silently mixed).
    facts_by_filing = []
    for r in sorted(manifest, key=lambda r: r["period_end"]):          # oldest first
        path = os.path.join(repo, "data/edgar_10k/raw", r["ticker"], r["fiscal_year"], r["tenk_file"])
        facts_by_filing.append((r, parse_xbrl(path)))
    iprd_tickers = {r["ticker"] for r, facts in facts_by_filing
                    if any(f["concept"] == "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost" for f in facts)}
    filing_row = {(r["ticker"], r["fiscal_year"]): r for r in manifest}

    # Where each kept fact is printed: section and chunk(s) of its own filing
    located = {}
    for r, facts in facts_by_filing:
        t, fy = r["ticker"], r["fiscal_year"]
        by_sec = collections.defaultdict(list)
        for c in sorted((c for c in chunks if c["ticker"] == t and c["fiscal_year"] == fy
                         and c["document"] == "10-K"), key=lambda c: (c["section"], c["chunk_index"])):
            by_sec[c["section"]].append((c["chunk_id"], c["text"].split("\n")[1:]))
        path = os.path.join(repo, "data/edgar_10k/raw", t, fy, r["tenk_file"])
        printed = {f["fact_id"]: f["text"] for f in facts if f["fact_id"]}
        for fid, loc in locate_facts(path, by_sec, printed).items():
            located[(t, fy, fid)] = loc

    merged, conflicts = {}, []
    for r, facts in facts_by_filing:
        t, fy = r["ticker"], r["fiscal_year"]
        for f in facts:
            if f["concept"] == "ResearchAndDevelopmentExpense" and t in iprd_tickers:
                metric = IPRD_METRIC[0]
            else:
                metric = METRICS[f["concept"]][0]
            key = (t, metric, f["start"], f["end"], tuple(sorted(f["dims"].items())))
            prev = merged.get(key)
            f.update(ticker=t, metric=metric, filings=[fy])
            sec, title, cids = located.get((t, fy, f["fact_id"]), (None, None, []))
            occ = dict(filing=fy, fact_id=f["fact_id"], context_ref=f["context_ref"], concept=f["concept"],
                       text=f["text"], value=f["value"], section=sec, section_title=title, chunk_ids=cids)
            if prev and prev["concept"] != f["concept"]:
                if abs(prev["value"] - f["value"]) > 0.5:
                    conflicts.append((t, metric, f["end"], prev["concept"], prev["value"], f["concept"], f["value"]))
                if PRIORITY[prev["concept"]] <= PRIORITY[f["concept"]]:
                    prev["filings"] = sorted(set(prev["filings"]) | {fy})
                    continue
                f["texts"] = {f["text"]}
                f["occ"] = [occ]
                merged[key] = f
                continue
            if prev:
                f["filings"] = sorted(set(prev["filings"]) | {fy})
                if abs(prev["value"] - f["value"]) > 0.5:
                    f["earlier_reported"] = prev["value"]
                f["texts"] = prev["texts"] | {f["text"]}
                f["occ"] = prev["occ"] + [occ]
            else:
                f["texts"] = {f["text"]}
                f["occ"] = [occ]
            merged[key] = f

    n_values = 0
    for f in merged.values():
        t = f["ticker"]
        comp = company_name[t]
        fy = fiscal_label(f["end"])
        period = g.node(f"{fy} ({t})", "entity", kind="FiscalYear", ticker=t,
                        end_date=f["end"], **({} if f["instant"] else {"start_date": f["start"]}))
        d = f["dims"]
        chain, subject = [comp], comp
        if SEG_AXIS in d:
            seg = g.node(f"{humanize(d[SEG_AXIS])} ({t})", "entity", kind="Segment", ticker=t)
            g.aliases[seg] = (humanize(d[SEG_AXIS]).split("/"), t)
            g.edge(comp, "has_segment", seg)
            chain.append(seg); subject = seg
        if SUB_AXIS in d:
            bl = g.node(f"{humanize(d[SUB_AXIS])} ({t})", "entity", kind="BusinessLine", ticker=t)
            g.aliases[bl] = (humanize(d[SUB_AXIS]).split("/"), t)
            g.edge(chain[-1], "has_business_line", bl)
            chain.append(bl); subject = bl
        if PROD_AXIS in d:
            pname = humanize(d[PROD_AXIS])
            prod = g.node(f"{pname} ({t})", "entity", kind="Product", ticker=t)
            g.aliases[prod] = (pname.split("/"), t)
            g.edge(chain[-1], "has_product", prod)
            subject = prod
        geo = None
        if GEO_AXIS in d:
            mem = d[GEO_AXIS].split(":")[-1]
            geo = GEO_NAMES.get(mem) or (humanize(mem) + f" ({t})")
            g.node(geo, "entity", kind="Location")
            g.aliases.setdefault(geo, ([re.sub(r" \(\w+\)$", "", geo)], None))

        display = fmt_value(f["value"], f["unit"])
        metric = f["metric"]
        when = f"at end of {fy}" if f["instant"] else fy
        where = "" if not geo else (f" {geo[0].lower()}{geo[1:]}" if geo.startswith("Outside") else f" in {geo}")
        vname = f"{subject} {metric[0].lower() + metric[1:]}{where} {when} = {display}"
        attrs = dict(kind="Value", value=f["value"], display=display, unit=f["unit"],
                     metric=metric, xbrl_concept="us-gaap:" + f["concept"], ticker=t,
                     fiscal_year=fy, period_end=f["end"], source="xbrl",
                     source_filings=[f"{t} {x}" for x in f["filings"]],
                     source_accessions=[filing_row[(t, x)]["accession"] for x in f["filings"]],
                     source_urls=[filing_row[(t, x)]["tenk_url"] for x in f["filings"]])
        if not f["instant"]:
            attrs["period_start"] = f["start"]
        if "earlier_reported" in f:
            attrs["earlier_reported_value"] = f["earlier_reported"]
        # Source: one place where this exact number is printed. Only occurrences showing the value
        # kept in the graph count (a restated older figure does not). Newest filing first, then
        # Item 8 (audited statements), then Item 7, then document order.
        same = [o for o in f["occ"] if abs(o["value"] - f["value"]) <= 0.5]
        order = sorted(range(len(same)), key=lambda i: (
            -int(same[i]["filing"][2:]), same[i]["section"] is None,
            SECTION_RANK.get(same[i]["section"], 2), not same[i]["chunk_ids"], i))
        top = same[order[0]]
        row = filing_row[(t, top["filing"])]
        chunk_ids = list(top["chunk_ids"])
        for i in order[1:]:
            chunk_ids += [c for c in same[i]["chunk_ids"] if c not in chunk_ids]
        attrs.update(source_filing=f"{t} {top['filing']}", source_accession=row["accession"],
                     source_url=row["tenk_url"],
                     source_fact_url=f"{row['tenk_url']}#{top['fact_id']}" if top["fact_id"] else None,
                     source_section=top["section"], source_chunk_id=(top["chunk_ids"] or [None])[0],
                     source_chunk_ids=chunk_ids, xbrl_fact_id=top["fact_id"],
                     xbrl_context_ref=top["context_ref"], printed_value=top["text"])
        assert vname not in g.nodes, f"duplicate value name {vname}"
        g.node(vname, "attribute", **attrs)
        n_values += 1
        g.node(metric, "entity", kind="Metric")
        g.edge(subject, "has_value", vname)
        g.edge(vname, "of_metric", metric)
        g.edge(vname, "for_period", period)
        if geo:
            g.edge(vname, "in_location", geo)
        f["vname"], f["subject"] = vname, subject
        for o in f["occ"]:
            row = filing_row[(t, o["filing"])]
            g.value_sources.append(dict(
                value_node=vname, is_primary=o is top, filing=f"{t} {o['filing']}",
                accession=row["accession"], section=o["section"] or "",
                chunk_ids=";".join(o["chunk_ids"]), xbrl_concept="us-gaap:" + o["concept"],
                xbrl_fact_id=o["fact_id"] or "", xbrl_context_ref=o["context_ref"] or "",
                printed_value=o["text"], reported_value=o["value"],
                same_as_graph_value=abs(o["value"] - f["value"]) <= 0.5,
                fact_url=f"{row['tenk_url']}#{o['fact_id']}" if o["fact_id"] else ""))

    # Document nodes
    for c in chunks:
        g.node(c["chunk_id"], "document", content=c["text"], ticker=c["ticker"],
               fiscal_year=c["fiscal_year"], section=c["section"])

    # is_mentioned_in: entities
    bodies = {c["chunk_id"]: c["text"].split("\n", 1)[-1] for c in chunks}   # drop header line
    by_ticker = collections.defaultdict(list)
    for c in chunks:
        by_ticker[c["ticker"]].append(c["chunk_id"])
    for name, (aliases, scope) in g.aliases.items():
        aliases = [a for a in aliases if a not in NO_TEXT_MATCH and len(a) >= 3]
        if not aliases:
            continue
        flags = 0 if any(len(a) < 5 for a in aliases) else re.I
        pat = re.compile(r"(?<![\w-])(" + "|".join(re.escape(a) for a in aliases) + r")(?![\w-])", flags)
        for cid in (by_ticker[scope] if scope else bodies):
            if pat.search(bodies[cid]):
                g.edge(name, "is_mentioned_in", cid)

    # Every chunk starts with a header line naming the company and the filing's fiscal year
    # ("Johnson & Johnson (JNJ) | FY2025 Form 10-K | Item 7. ..."), so both are mentioned in
    # every chunk. These links also keep chunks from being isolated in the graph.
    for c in chunks:
        t = c["ticker"]
        period = g.node(f"{c['fiscal_year']} ({t})", "entity", kind="FiscalYear", ticker=t,
                        end_date=c["period_end"])
        g.edge(company_name[t], "is_mentioned_in", c["chunk_id"])
        g.edge(period, "is_mentioned_in", c["chunk_id"])

    # is_mentioned_in: Value nodes -> chunks of the same company that show the same number
    # (as printed in the filing) and name the subject, or for company totals the metric.
    for f in merged.values():
        nums = [x for x in f["texts"] if len(re.sub(r"\D", "", x)) >= 3]
        if not nums:
            continue
        num_pat = re.compile(r"(?<![\d.,])(" + "|".join(re.escape(x) for x in nums) + r")(?![\d]|\.\d|,\d)")
        subj = f["subject"]
        if g.nodes[subj][1].get("kind") == "Company":
            words = IPRD_METRIC[1] if f["metric"] == IPRD_METRIC[0] else METRICS[f["concept"]][1]
            need = re.compile("|".join(re.escape(w) for w in words), re.I)
        else:
            al = [a for a in g.aliases.get(subj, ([], None))[0] if a not in NO_TEXT_MATCH]
            if not al:
                continue
            need = re.compile(r"(?<!\w)(" + "|".join(re.escape(a) for a in al) + r")(?!\w)", re.I)
        for cid in by_ticker[f["ticker"]]:
            b = bodies[cid]
            if num_pat.search(b) and need.search(b):
                g.edge(f["vname"], "is_mentioned_in", cid)

    # is_mentioned_in: Value nodes -> the chunks where their XBRL tag is printed (exact location,
    # so this also links numbers the text rule above misses, e.g. a table without the product name)
    n_loc_edges = 0
    for f in merged.values():
        for cid in g.nodes[f["vname"]][1]["source_chunk_ids"]:
            n_loc_edges += (f["vname"], "is_mentioned_in", cid) not in g.edges
            g.edge(f["vname"], "is_mentioned_in", cid)
    print(f"{n_loc_edges} Value -> chunk links added from the XBRL tag locations", file=sys.stderr)

    for c in conflicts:
        print("concept conflict (kept the first): %s %s %s: %s=%s vs %s=%s" % c, file=sys.stderr)
    print(f"{len(conflicts)} concept conflicts; acquired IPR&D split out for: {sorted(iprd_tickers) or 'none'}",
          file=sys.stderr)
    return g, n_values


def write(g, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "nodes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "type", "attributes"])
        for name, (ntype, attrs) in sorted(g.nodes.items(), key=lambda x: (x[1][0], x[0])):
            w.writerow([name, ntype, repr(attrs)])
    with open(os.path.join(out_dir, "relations.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "attributes"])
        for r, desc in RELATIONS.items():
            w.writerow([r, repr({"description": desc})])
    with open(os.path.join(out_dir, "edges.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "relation", "target", "attributes"])
        for (s, r, t), attrs in sorted(g.edges.items()):
            w.writerow([s, r, t, repr(attrs)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repo root (default: current folder)")
    ap.add_argument("--tickers", nargs="+", default=["JNJ", "AAPL", "MSFT"])
    ap.add_argument("--name", default="fin10k_v0", help="dataset name (folder under data/graph)")
    a = ap.parse_args()
    g, n_values = build(a.repo, set(a.tickers))
    out = os.path.join(a.repo, "data/graph", a.name, "processed/stage1")
    write(g, out)
    # Outside stage1 on purpose: gfmrag only reads nodes/relations/edges.csv there.
    with open(os.path.join(a.repo, "data/graph", a.name, "value_sources.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(g.value_sources[0]))
        w.writeheader()
        w.writerows(sorted(g.value_sources, key=lambda r: (r["value_node"], not r["is_primary"],
                                                            r["filing"], r["xbrl_fact_id"])))
    kinds = collections.Counter(attrs.get("kind", ntype) for ntype, attrs in g.nodes.values())
    types = collections.Counter(ntype for ntype, _ in g.nodes.values())
    rels = collections.Counter(r for _, r, _ in g.edges)
    stats = {"tickers": sorted(a.tickers), "nodes": len(g.nodes), "edges": len(g.edges),
             "node_types": dict(types), "node_kinds": dict(kinds.most_common()),
             "relations": dict(rels.most_common())}
    vals = [attrs for _, attrs in g.nodes.values() if attrs.get("kind") == "Value"]
    stats["value_sources"] = {
        "values": len(vals),
        "with_section": sum(1 for v in vals if v["source_section"]),
        "with_chunk": sum(1 for v in vals if v["source_chunk_id"]),
        "primary_section": dict(collections.Counter(v["source_section"] or "not printed" for v in vals).most_common()),
        "printed_occurrences": len(g.value_sources),
    }
    json.dump(stats, open(os.path.join(a.repo, "data/graph", a.name, "graph_stats.json"), "w"), indent=2)
    print(json.dumps(stats, indent=2))
    print("wrote", out, file=sys.stderr)


if __name__ == "__main__":
    main()
