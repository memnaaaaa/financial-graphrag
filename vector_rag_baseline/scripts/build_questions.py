"""Build data/questions.jsonl. Gold chunks = every chunk in the stated company+fiscal-year filing whose text
matches a fact pattern (label + number), so duplicated statements (MD&A vs financial statements) all count.
Derived answers are computed here, not typed by hand."""
import json, re

chunks = [json.loads(l) for l in open("data/chunks.jsonl", encoding="utf-8")]


def gold(tk, fy, pat):
    ids = [c["chunk_id"] for c in chunks if c["ticker"] == tk and c["fiscal_year"] == fy and re.search(pat, c["text"])]
    assert ids, f"no chunk matches {tk} {fy} {pat!r}"
    return ids


F = {  # fact name -> (ticker, fiscal_year, pattern)
    "aapl_sales25": ("AAPL", "FY2025", r"Total net sales \| \$416,161"),
    "aapl_iphone25": ("AAPL", "FY2025", r"iPhone \| \$209,586"),
    "aapl_rd25": ("AAPL", "FY2025", r"Research and development \| \$?34,550"),
    "wmt_rev26": ("WMT", "FY2026", r"Total revenues \| 713,163|total revenues of \$713\.2 billion"),
    "wmt_growth26": ("WMT", "FY2026", r"total revenues increased \$32\.2 billion"),
    "wmt_ni26": ("WMT", "FY2026", r"Consolidated net income attributable to Walmart \| \$21,893"),
    "wmt_assoc26": ("WMT", "FY2026", r"approximately 2\.1 million associates"),
    "msft_rd25": ("MSFT", "FY2025", r"Research and development \| \$32,488"),
    "msft_rev25": ("MSFT", "FY2025", r"Total revenue \| 281,724"),
    "msft_rdpct25": ("MSFT", "FY2025", r"As a percent of revenue \| 12%"),
    "jpm_emp25": ("JPM", "FY2025", r"318,512 employees globally"),
    "jpm_ni25": ("JPM", "FY2025", r"Provision for credit losses \| 14,212 \| 10,678 \| 33\s+Net income \| 57,048|Income tax expense \| 15,547 \| 16,610 \| 12,060\s+Net income \| \$57,048"),
    "cat_pps25": ("CAT", "FY2025", r"[Pp]rofit per share (was|for 2025 was) \$18\.81"),
    "cat_rev25": ("CAT", "FY2025", r"Total sales and revenues for 2025 were \$67\.589 billion"),
    "cat_emp25": ("CAT", "FY2025", r"employed about 118,000 full-time"),
    "jnj_rd25": ("JNJ", "FY2025", r"Total research and development expense \| \$14,665"),
    "jnj_rdpct25": ("JNJ", "FY2025", r"Total research and development expense \| \$14,665 \| 15\.6%"),
    "jnj_im_sales25": ("JNJ", "FY2025", r"Total Innovative Medicine Sales \| \$60,401|Innovative Medicine segment sales in 2025 were \$60\.4 billion"),
    "jnj_im_rd25": ("JNJ", "FY2025", r"Innovative Medicine \| \$11,827"),
    "jnj_talc25": ("JNJ", "FY2025", r"lawsuits arising out of the use of body powders containing talc"),
    "xom_ni25": ("XOM", "FY2025", r"Net income \(loss\) attributable to ExxonMobil \| 28,844 \| 33,680 \| 36,010\s+Earnings \(loss\) per common share"),
    "aapl_mfg25": ("AAPL", "FY2025", r"significant majority of the Company's manufacturing is performed"),
}
G = {k: gold(*v) for k, v in F.items()}


def g(*names):
    out = []
    for n in names:
        out += [i for i in G[n] if i not in out]
    return out


s1, s0 = 416161, 391035
Q = [
 ("q01", 1, "single", "What were Apple's total net sales in fiscal 2025 (fiscal year ended September 27, 2025)?", g("aapl_sales25"), "$416,161 million (about $416.2 billion)."),
 ("q02", 1, "single", "What were Walmart's total revenues in fiscal 2026 (fiscal year ended January 31, 2026)?", g("wmt_rev26"), "$713.2 billion (713,163 million)."),
 ("q03", 1, "single", "How much did Microsoft spend on research and development in fiscal 2025 (fiscal year ended June 30, 2025)?", g("msft_rd25"), "$32,488 million."),
 ("q04", 1, "single", "How many employees did JPMorgan Chase have globally as of December 31, 2025?", g("jpm_emp25"), "318,512 employees."),
 ("q05", 1, "single", "What was Caterpillar's profit per share for 2025?", g("cat_pps25"), "$18.81 per share."),
 ("q06", 1, "single", "What was Johnson & Johnson's total research and development expense in fiscal 2025, and what percent of sales was it?", g("jnj_rd25"), "$14,665 million, which was 15.6% of sales."),
 ("q07", 1, "single", "What was ExxonMobil's net income attributable to ExxonMobil in 2025?", g("xom_ni25"), "$28,844 million."),
 ("q08", 1, "single", "In its 2025 10-K, what consumer product does Johnson & Johnson say it is a defendant in numerous lawsuits over, involving talc?", g("jnj_talc25"), "Body powders containing talc, primarily JOHNSON'S Baby Powder."),
 ("q09", 1, "single", "In which countries are Apple's outsourcing partners located, according to its fiscal 2025 10-K risk factors?", g("aapl_mfg25"), "Primarily China mainland, India, Japan, South Korea, Taiwan and Vietnam (plus some U.S. partners and facilities)."),
 ("q10", 2, "within", "By how much did Apple's total net sales grow from fiscal 2024 to fiscal 2025, and what share of fiscal 2025 net sales came from iPhone?", g("aapl_sales25", "aapl_iphone25"),
  f"Net sales grew ${s1-s0:,} million ({(s1/s0-1)*100:.0f}%) from $391,035 million to $416,161 million; iPhone net sales of $209,586 million were {209586/s1*100:.1f}% of the total."),
 ("q11", 2, "within", "What was Microsoft's fiscal 2025 research and development expense as a percent of its total revenue?", g("msft_rd25", "msft_rev25"),
  f"About {32488/281724*100:.1f}% ($32,488 million of $281,724 million total revenue); the filing rounds this to 12%."),
 ("q12", 2, "within", "By how much did Walmart's total revenues increase in fiscal 2026, and what was its consolidated net income attributable to Walmart?", g("wmt_growth26", "wmt_ni26"),
  "Total revenues increased $32.2 billion (4.7%); consolidated net income attributable to Walmart was $21,893 million."),
 ("q13", 2, "within", "Roughly how much did Caterpillar earn in total sales and revenues per full-time employee in 2025?", g("cat_rev25", "cat_emp25"),
  f"About ${67.589e9/118000/1000:,.0f} thousand per employee ($67.589 billion in sales and revenues over about 118,000 full-time employees)."),
 ("q14", 2, "within", "What were Johnson & Johnson's Innovative Medicine segment sales in 2025, and how much did that segment spend on research and development?", g("jnj_im_sales25", "jnj_im_rd25"),
  "Innovative Medicine sales were $60,401 million (about $60.4 billion); its R&D expense was $11,827 million (19.6% of segment sales)."),
 ("q15", 2, "cross", "Which spent more on research and development in fiscal 2025, Apple or Microsoft, and by how much?", g("aapl_rd25", "msft_rd25"),
  f"Apple, by ${34550-32488:,} million (Apple $34,550 million vs Microsoft $32,488 million)."),
 ("q16", 2, "cross", "Which had higher revenue in fiscal 2025, Apple or Microsoft, and by how much?", g("aapl_sales25", "msft_rev25"),
  f"Apple, by ${s1-281724:,} million (Apple $416,161 million vs Microsoft $281,724 million)."),
 ("q17", 2, "cross", "How many more employees did Walmart have than JPMorgan Chase at their most recent fiscal year ends in this data (Walmart January 31, 2026; JPMorgan December 31, 2025)?", g("wmt_assoc26", "jpm_emp25"),
  f"Walmart had about 2.1 million associates versus 318,512 at JPMorgan Chase, roughly {2100000-318512:,} more (about {2100000/318512:.1f} times as many)."),
 ("q18", 2, "cross", "Which had higher research and development spending as a percent of revenue in its latest 10-K year, Johnson & Johnson (2025) or Microsoft (fiscal 2025)?", g("jnj_rdpct25", "msft_rdpct25"),
  "Johnson & Johnson at 15.6% of sales, versus Microsoft at 12% of revenue."),
 ("q19", 2, "cross", "Which earned more net income in 2025, JPMorgan Chase or ExxonMobil, and roughly how many times as much?", g("jpm_ni25", "xom_ni25"),
  f"JPMorgan Chase: $57,048 million versus ExxonMobil's $28,844 million, about {57048/28844:.1f} times as much."),
]
with open("data/questions.jsonl", "w", encoding="utf-8") as f:
    for qid, hops, typ, q, ids, ans in Q:
        f.write(json.dumps({"qid": qid, "hops": hops, "type": typ, "question": q, "gold_chunk_ids": ids, "gold_answer": ans}) + "\n")
        print(f"{qid} [{typ}] gold={len(ids)} {ids}\n    A: {ans}")
