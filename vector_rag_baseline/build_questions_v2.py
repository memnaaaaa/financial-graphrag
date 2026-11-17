"""Golden set v2: 35 questions on three companies (30 + 5 deeper 3-5 hop chains) (J&J, Apple, Microsoft; 6 filings).

  12 single-hop   (4 per company)
  10 relation-chain multi-hop  (entity -> related entity -> value, e.g. Genmab -> DARZALEX -> segment -> sales)
   4 cross-year   (same company, two filings)
   4 cross-company
   5 deep relation chains (3-5 hops, type "relation_deep")

Gold chunks = every chunk of the named filing whose text matches the fact pattern (so MD&A / financial-statement
duplicates and overlapping chunks all count). Derived numbers are computed here, not typed by hand.
Also writes data/golden_v2_review.md: for every fact, the matched snippet + filing URL, for the by-hand check.

Run:  python scripts/build_questions_v2.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chunks = [json.loads(l) for l in open(ROOT / "data/chunks.jsonl", encoding="utf-8")]
chunks = [c for c in chunks if c["ticker"] in ("AAPL", "MSFT", "JNJ")]
BY_ID = {c["chunk_id"]: c for c in chunks}

# fact name -> (ticker, fiscal_year, regex). \s+ is used for spaces because chunk text contains line breaks.
F = {
    # ---- Apple ----
    "a_sales25": ("AAPL", "FY2025", r"Total net sales\s*\|\s*\$?416,161"),
    "a_rd25": ("AAPL", "FY2025", r"Research and development\s*\|\s*\$?34,550"),
    "a_rdpct25": ("AAPL", "FY2025", r"Research and development\s*\|\s*\$34,550.{0,60}Percentage of total net sales\s*\|\s*8%"),
    "a_fte25": ("AAPL", "FY2025", r"approximately\s+166,000\s+full-time\s+equivalent\s+employees"),
    "a_fte24": ("AAPL", "FY2024", r"approximately\s+164,000\s+full-time\s+equivalent\s+employees"),
    "a_serv25": ("AAPL", "FY2025", r"Services\s*(\(1\)\s*)?\|\s*\$?109,158"),
    "a_beats": ("AAPL", "FY2025", r"Wearables,\s+Home\s+and\s+Accessories\s+Wearables\s+includes.{0,900}Beats"),
    "a_wha25": ("AAPL", "FY2025", r"Wearables,\s+Home\s+and\s+Accessories\s*\|\s*\$?35,686"),
    "a_mfg25": ("AAPL", "FY2025", r"outsourcing\s+partners\s+located\s+primarily\s+in\s+China\s+mainland"),
    "a_ex21": ("AAPL", "FY2025", r"Apple\s+Asia\s+Limited\s*\|\s*Hong\s+Kong"),
    "a_gc_def": ("AAPL", "FY2025", r"Greater\s+China\s+includes\s+China\s+mainland,\s+Hong\s+Kong\s+and\s+Taiwan"),
    "a_gc25": ("AAPL", "FY2025", r"Greater\s+China\s*\|\s*\$?64,377"),
    "a_ni25": ("AAPL", "FY2025", r"Net\s+income\s*\|\s*\$112,010"),
    # ---- Microsoft ----
    "m_rev26": ("MSFT", "FY2026", r"(Total revenue|Revenue)\s*\|\s*\$?331,839"),
    "m_ni26": ("MSFT", "FY2026", r"Net\s+income\s*\|\s*\$?133,749"),
    "m_emp26": ("MSFT", "FY2026", r"employed\s+approximately\s+223,000"),
    "m_emp25": ("MSFT", "FY2025", r"employed\s+approximately\s+228,000"),
    "m_rd26": ("MSFT", "FY2026", r"Research\s+and\s+development\s*\|\s*\$?35,562"),
    "m_rdpct26": ("MSFT", "FY2026", r"Research and development\s*\|\s*\$35,562\s*\|\s*\$?32,488\s*\|\s*9%\s*As a percent of revenue\s*\|\s*11%"),
    "m_ic_def": ("MSFT", "FY2026", r"Our\s+Intelligent\s+Cloud\s+segment\s+consists\s+of.{0,300}Azure"),
    "m_ic26": ("MSFT", "FY2026", r"Intelligent\s+Cloud\s+Revenue\s*\|\s*\$137,791"),
    "m_ic25": ("MSFT", "FY2025", r"Intelligent\s+Cloud\s+Revenue\s*\|\s*\$106,265"),
    "m_act_acq": ("MSFT", "FY2026", r"Goodwill\s+was\s+assigned\s+to\s+our\s+More\s+Personal\s+Computing\s+segment"),
    "m_mpc26": ("MSFT", "FY2026", r"More\s+Personal\s+Computing\s+Revenue\s*\|\s*\$54,052"),
    "m_openai_recap": ("MSFT", "FY2026", r"OpenAI\s+Recapitalization.{0,200}dilution\s+gains"),
    "m_openai_gain": ("MSFT", "FY2026", r"\$6\.5\s+billion\s+of\s+net\s+gains\s+and\s+\$4\.8\s+billion\s+of\s+net\s+losses.{0,200}OpenAI"),
    "m_li_sub": ("MSFT", "FY2026", r"LinkedIn\s+Ireland\s+Unlimited\s+Company\s*\|\s*Ireland"),
    "m_li_growth": ("MSFT", "FY2026", r"LinkedIn\s+revenue\s+increased\s+11%"),
    # ---- Johnson & Johnson ----
    "j_rd25": ("JNJ", "FY2025", r"Total\s+research\s+and\s+development\s+expense\s*\|\s*\$14,665"),
    "j_rdpct25": ("JNJ", "FY2025", r"Total\s+research\s+and\s+development\s+expense\s*\|\s*\$14,665\s*\|\s*15\.6%"),
    "j_emp25": ("JNJ", "FY2025", r"approximately\s+138,200\s+employees"),
    "j_im25": ("JNJ", "FY2025", r"Total\s+Innovative\s+Medicine\s+Sales\s*\|\s*\$60,401|Sales\s+to\s+customers\s*\|\s*\$60,401"),
    "j_ne25": ("JNJ", "FY2025", r"Net\s+earnings\s*\|\s*\$26,804"),
    "j_genmab": ("JNJ", "FY2025", r"Genmab\s+A/S\s+owns\s+two\s+patent\s+families\s+related\s+to\s+DARZALEX,\s+and\s+Janssen\s+Biotech"),
    "j_darz_im": ("JNJ", "FY2025", r"Key\s+products\s+in\s+the\s+Innovative\s+Medicine\s+segment\s+include.{0,400}DARZALEX\s+\(daratumumab\)"),
    "j_janssen_pa": ("JNJ", "FY2025", r"Janssen\s+Biotech,\s+Inc\.\s*\|\s*Pennsylvania"),
    "j_shock_acq": ("JNJ", "FY2025", r"acquired\s+all\s+the\s+outstanding\s+shares\s+of\s+Shockwave\s+Medical"),
    "j_shock_mt": ("JNJ", "FY2025", r"circulatory\s+restoration\s+products\s+\(Shockwave\)"),
    "j_shock_sales": ("JNJ", "FY2025", r"Shockwave\(1\)\s*\|\s*1,146"),
    "j_darz25": ("JNJ", "FY2025", r"approximately\s+15\.0%\s+of\s+the\s+Company's\s+total\s+revenues\s+for\s+fiscal\s+2025"),
    "j_darz24": ("JNJ", "FY2024", r"approximately\s+13\.1%\s+of\s+the\s+Company's\s+total\s+revenues\s+for\s+fiscal\s+2024"),
    # ---- facts for the deeper (3-5 hop) chains ----
    "j_darz_sales": ("JNJ", "FY2025", r"DARZALEX\s*\|\s*14,351"),
    "j_royalty": ("JNJ", "FY2025", r"royalty\s+amounts\s+to\s+Genmab\s+were\s+approximately\s+\$2\.4\s+billion"),
    "j_cardio": ("JNJ", "FY2025", r"Cardiovascular\s*\|\s*8,928.{0,200}Shockwave\(1\)\s*\|\s*1,146"),
    "j_shock_de": ("JNJ", "FY2025", r"Shockwave\s+Medical,\s+Inc\.\s*\|\s*Delaware"),
    "m_gw_mpc": ("MSFT", "FY2026", r"More\s+Personal\s+Computing\s*\|\s*\$?62,211.{0,40}62,340"),
    "m_act_pub": ("MSFT", "FY2026", r"Activision\s+Publishing,\s+Inc\.\s*\|\s*United\s+States"),
    "m_openai_ni": ("MSFT", "FY2026", r"net\s+gains\s+from\s+investments\s+in\s+OpenAI,\s+which\s+resulted\s+in\s+an\s+increase\s+in\s+net\s+income\s+and\s+diluted\s+EPS\s+of\s+\$5\.0\s+billion"),
    "a_eur_def": ("AAPL", "FY2025", r"Europe\s+includes\s+European\s+countries,\s+as\s+well\s+as\s+India"),
    "a_seg_sales": ("AAPL", "FY2025", r"Europe\s*\|\s*\$?111,032.{0,200}Japan\s*\|\s*\$?28,703"),
}

SNIP = {}  # fact -> list of (chunk_id, snippet) for the review file


def gold(name):
    tk, fy, pat = F[name]
    ids, snips = [], []
    for c in chunks:
        if c["ticker"] == tk and c["fiscal_year"] == fy:
            m = re.search(pat, c["text"], re.S)
            if m:
                ids.append(c["chunk_id"])
                a = max(0, m.start() - 60)
                snips.append((c["chunk_id"], re.sub(r"\s+", " ", c["text"][a:m.end() + 60])))
    assert ids, f"no chunk matches {name}: {tk} {fy} {pat!r}"
    SNIP[name] = snips
    return ids


G = {k: gold(k) for k in F}


def g(*names):
    out = []
    for n in names:
        out += [i for i in G[n] if i not in out]
    return out


def fil(*names):
    return sorted({f"{F[n][0]} {F[n][1]}" for n in names})


# derived numbers
sales_a, rd_a, rd_m = 416161, 34550, 35562
ic25, ic26 = 106265, 137791
ni_a, ni_j = 112010, 26804
rd_j, sales_j = 14665, 94193

# (qid, hops, type, question, fact names, gold answer, relation chain or None)
Q = [
    # ===== single-hop: Apple =====
    ("single", "What were Apple's total net sales in fiscal 2025 (fiscal year ended September 27, 2025)?", ["a_sales25"],
     "$416,161 million (about $416.2 billion).", None),
    ("single", "How much did Apple spend on research and development in fiscal 2025?", ["a_rd25"],
     "$34,550 million.", None),
    ("single", "How many full-time equivalent employees did Apple have as of September 27, 2025?", ["a_fte25"],
     "Approximately 166,000.", None),
    ("single", "What were Apple's Services net sales in fiscal 2025?", ["a_serv25"],
     "$109,158 million.", None),
    # ===== single-hop: Microsoft =====
    ("single", "What was Microsoft's total revenue in fiscal 2026 (fiscal year ended June 30, 2026)?", ["m_rev26"],
     "$331,839 million (about $331.8 billion).", None),
    ("single", "What was Microsoft's net income in fiscal 2026?", ["m_ni26"],
     "$133,749 million.", None),
    ("single", "How many people did Microsoft employ on a full-time basis as of June 30, 2026?", ["m_emp26"],
     "Approximately 223,000 (121,000 in the U.S. and 102,000 internationally).", None),
    ("single", "How much did Microsoft spend on research and development in fiscal 2026?", ["m_rd26"],
     "$35,562 million.", None),
    # ===== single-hop: J&J =====
    ("single", "What was Johnson & Johnson's total research and development expense in fiscal 2025?", ["j_rd25"],
     "$14,665 million.", None),
    ("single", "How many employees does Johnson & Johnson have worldwide, according to its fiscal 2025 10-K?", ["j_emp25"],
     "Approximately 138,200.", None),
    ("single", "What were Johnson & Johnson's Innovative Medicine segment sales in fiscal 2025?", ["j_im25"],
     "$60,401 million (about $60.4 billion).", None),
    ("single", "What were Johnson & Johnson's net earnings in fiscal 2025?", ["j_ne25"],
     "$26,804 million.", None),

    # ===== relation-chain multi-hop =====
    ("relation", "Which Johnson & Johnson segment sells the drug licensed from Genmab, and what were that segment's sales in fiscal 2025?",
     ["j_genmab", "j_darz_im", "j_im25"],
     "DARZALEX is licensed from Genmab A/S and sold by the Innovative Medicine segment, whose fiscal 2025 sales were $60,401 million.",
     "Genmab -> DARZALEX (licensed) -> Innovative Medicine segment -> segment sales"),
    ("relation", "Which Johnson & Johnson subsidiary holds the exclusive license to Genmab's DARZALEX patent families, and in which U.S. state is it incorporated?",
     ["j_genmab", "j_janssen_pa"],
     "Janssen Biotech, Inc., incorporated in Pennsylvania.",
     "Genmab -> Janssen Biotech, Inc. (10-K Item 1) -> Exhibit 21 jurisdiction"),
    ("relation", "Johnson & Johnson acquired Shockwave Medical in 2024. Which segment reports Shockwave's sales, and how much were they in fiscal 2025?",
     ["j_shock_acq", "j_shock_mt", "j_shock_sales"],
     "Shockwave is reported in the MedTech segment (circulatory restoration products); its fiscal 2025 sales were $1,146 million (vs $564 million in 2024).",
     "Shockwave Medical (acquired May 31, 2024) -> MedTech segment -> Shockwave sales"),
    ("relation", "What effect did the OpenAI Recapitalization have on Microsoft's other income in fiscal 2026, and how large were the net gains from its OpenAI investments?",
     ["m_openai_recap", "m_openai_gain"],
     "Microsoft's ownership of OpenAI was diluted and it recorded dilution gains in other income (expense), net; net gains from OpenAI investments were $6.5 billion in fiscal 2026 (vs $4.8 billion of net losses in fiscal 2025).",
     "Microsoft -> OpenAI (equity-method investment) -> OpenAI Recapitalization -> dilution gain -> other income"),
    ("relation", "Which Microsoft segment received the goodwill from the Activision Blizzard acquisition, and what was that segment's revenue in fiscal 2026?",
     ["m_act_acq", "m_mpc26"],
     "The goodwill was assigned to the More Personal Computing segment, whose fiscal 2026 revenue was $54,052 million.",
     "Activision Blizzard acquisition -> goodwill -> More Personal Computing segment -> segment revenue"),
    ("relation", "Which Microsoft segment includes Azure, and what was that segment's revenue in fiscal 2026?",
     ["m_ic_def", "m_ic26"],
     "Azure is part of the Intelligent Cloud segment, whose fiscal 2026 revenue was $137,791 million.",
     "Azure -> Intelligent Cloud segment -> segment revenue"),
    ("relation", "Which Microsoft subsidiary named after the professional network is incorporated in Ireland, and by what percent did that network's revenue grow in fiscal 2026?",
     ["m_li_sub", "m_li_growth"],
     "LinkedIn Ireland Unlimited Company (Ireland); LinkedIn revenue increased 11%.",
     "LinkedIn -> Exhibit 21 subsidiary (Ireland) -> LinkedIn revenue growth (MD&A)"),
    ("relation", "Which Apple product category includes Beats products, and what were that category's net sales in fiscal 2025?",
     ["a_beats", "a_wha25"],
     "Beats headphones are part of Wearables, Home and Accessories, whose fiscal 2025 net sales were $35,686 million.",
     "Beats -> Wearables, Home and Accessories category -> category net sales"),
    ("relation", "Apple's 10-K lists the countries where its outsourcing partners are mainly located. Which of those countries also have an Apple subsidiary named in Exhibit 21?",
     ["a_mfg25", "a_ex21"],
     "China mainland (Apple Computer Trading (Shanghai) Co., Ltd.), India (Apple India Private Limited), Japan (Apple Japan, Inc.), South Korea (Apple Korea Limited) and Vietnam (Apple Vietnam Limited Liability Company); Taiwan has no listed subsidiary.",
     "Outsourcing-partner countries (Item 1A) -> Exhibit 21 subsidiary jurisdictions -> intersection"),
    ("relation", "Apple Asia Limited is incorporated in Hong Kong. Which Apple reportable segment includes Hong Kong, and what were that segment's net sales in fiscal 2025?",
     ["a_ex21", "a_gc_def", "a_gc25"],
     "Hong Kong is in the Greater China segment, whose fiscal 2025 net sales were $64,377 million.",
     "Apple Asia Limited -> Hong Kong -> Greater China segment -> segment net sales"),

    # ===== cross-year (same company, two filings) =====
    ("cross_year", "How did Apple's full-time equivalent headcount change between its fiscal 2024 and fiscal 2025 10-Ks?",
     ["a_fte24", "a_fte25"],
     "It rose by about 2,000, from approximately 164,000 (Sept 28, 2024) to approximately 166,000 (Sept 27, 2025).", None),
    ("cross_year", "How did Microsoft's full-time headcount change between June 30, 2025 and June 30, 2026?",
     ["m_emp25", "m_emp26"],
     "It fell by about 5,000, from approximately 228,000 to approximately 223,000.", None),
    ("cross_year", "What share of Johnson & Johnson's total revenues came from DARZALEX (with DARZALEX FASPRO) in fiscal 2024 versus fiscal 2025?",
     ["j_darz24", "j_darz25"],
     "About 13.1% in fiscal 2024 and 15.0% in fiscal 2025 (up about 1.9 percentage points).", None),
    ("cross_year", "How much did Microsoft's Intelligent Cloud segment revenue grow from fiscal 2025 to fiscal 2026?",
     ["m_ic25", "m_ic26"],
     f"By ${ic26 - ic25:,} million (about {(ic26 / ic25 - 1) * 100:.1f}%), from ${ic25:,} million to ${ic26:,} million.", None),

    # ===== cross-company =====
    ("cross_company", "Which spent more on research and development, Apple in fiscal 2025 or Microsoft in fiscal 2026, and by how much?",
     ["a_rd25", "m_rd26"],
     f"Microsoft, by ${rd_m - rd_a:,} million (${rd_m:,} million vs Apple's ${rd_a:,} million).", None),
    ("cross_company", "Rank Apple (as of September 27, 2025), Microsoft (as of June 30, 2026) and Johnson & Johnson (fiscal 2025 10-K) by number of employees.",
     ["a_fte25", "m_emp26", "j_emp25"],
     "Microsoft (about 223,000), then Apple (about 166,000), then Johnson & Johnson (about 138,200).", None),
    ("cross_company", "Which of Johnson & Johnson (2025), Microsoft (fiscal 2026) and Apple (fiscal 2025) spent the highest share of revenue on research and development, and what were the shares?",
     ["j_rdpct25", "m_rdpct26", "a_rdpct25"],
     "Johnson & Johnson at 15.6% of sales, then Microsoft at 11% of revenue, then Apple at 8% of net sales.", None),
    ("cross_company", "Which earned more net income, Apple in fiscal 2025 or Johnson & Johnson in 2025, and roughly how many times as much?",
     ["a_ni25", "j_ne25"],
     f"Apple: ${ni_a:,} million versus Johnson & Johnson's ${ni_j:,} million, about {ni_a / ni_j:.1f} times as much.", None),
]

# ===== deeper relation chains: 3-5 hops =====  (hops, question, facts, gold answer, chain)
DEEP = [
    (4, "Which company licenses J&J's largest product to it, and how large was the royalty J&J paid that company in 2025 as a share of that product's 2025 sales?",
     ["j_darz25", "j_genmab", "j_royalty", "j_darz_sales"],
     f"Genmab A/S (DARZALEX, about 15.0% of J&J revenue); royalties were about $2.4 billion on DARZALEX sales of $14,351 million, roughly {2400 / 14351 * 100:.1f}% (within the 12% to 20% royalty range).",
     "largest product (DARZALEX) -> licensed from Genmab -> 2025 royalty paid -> DARZALEX 2025 sales -> royalty share"),
    (4, "J&J acquired Shockwave Medical in 2024. Which franchise reports Shockwave sales, what share of that franchise's 2025 sales was Shockwave, and where is Shockwave Medical, Inc. incorporated?",
     ["j_shock_acq", "j_shock_mt", "j_cardio", "j_shock_de"],
     f"Shockwave is in the Cardiovascular franchise of MedTech; its $1,146 million was about {1146 / 8928 * 100:.1f}% of Cardiovascular sales of $8,928 million. Shockwave Medical, Inc. is incorporated in Delaware.",
     "Shockwave acquisition -> MedTech segment -> Cardiovascular franchise -> franchise sales -> Exhibit 21 jurisdiction"),
    (3, "Which Microsoft segment received the Activision Blizzard goodwill, what was that segment's goodwill balance at June 30, 2026, and in which country is the subsidiary Activision Publishing, Inc. incorporated?",
     ["m_act_acq", "m_gw_mpc", "m_act_pub"],
     "The More Personal Computing segment; its goodwill was $62,340 million at June 30, 2026. Activision Publishing, Inc. is incorporated in the United States.",
     "Activision Blizzard acquisition -> goodwill -> More Personal Computing segment -> segment goodwill balance; Exhibit 21 subsidiary -> jurisdiction"),
    (4, "What happened to Microsoft's ownership of OpenAI in the October 2025 recapitalization, how large were the net gains from OpenAI investments in other income, and by how much did they raise fiscal 2026 net income and diluted EPS?",
     ["m_openai_recap", "m_openai_gain", "m_openai_ni"],
     "Its proportionate ownership decreased and it recorded dilution gains; net gains from OpenAI investments were $6.5 billion in other income (expense), net, and raised net income by $5.0 billion and diluted EPS by $0.67.",
     "OpenAI Recapitalization -> ownership dilution -> dilution gain -> other income ($6.5B) -> net income (+$5.0B) and EPS (+$0.67)"),
    (5, "Apple's Exhibit 21 lists subsidiaries in India and in Japan. Which reportable segment contains each country, and which of the two segments had higher net sales in fiscal 2025?",
     ["a_ex21", "a_eur_def", "a_seg_sales"],
     "India is in the Europe segment ($111,032 million) and Japan is its own segment ($28,703 million); Europe was higher, by $82,329 million.",
     "Apple India Private Limited -> India -> Europe segment -> net sales; Apple Japan, Inc. -> Japan segment -> net sales; compare"),
]

assert len(Q) == 30
types = [q[0] for q in Q]
assert types.count("single") == 12 and types.count("relation") == 10
assert types.count("cross_year") == 4 and types.count("cross_company") == 4
# 4 single-hop per company
assert [sum(1 for q, t in zip(Q[:12], [0] * 12) if f"{k}_" in q[2][0]) for k in "amj"] == [4, 4, 4]

out = ROOT / "data/questions_v2.jsonl"
rows = []
n_base = len(Q)
for h, q, facts, ans, chain in DEEP:
    Q.append(("relation_deep", q, facts, ans, chain, h))
for n, (typ, q, facts, ans, chain, *hh) in enumerate(Q, 1):
    ids = g(*facts)
    cos = sorted({F[f][0] for f in facts})
    row = {
        "qid": f"v2_q{n:02d}", "hops": hh[0] if hh else (1 if typ == "single" else 2), "type": typ,
        "companies": cos, "filings": fil(*facts), "question": q,
        "gold_chunk_ids": ids, "gold_answer": ans, "gold_facts": facts,
        "gold_source": "pattern-match (unverified)",
    }
    if chain:
        row["relation_chain"] = chain
    rows.append(row)
with open(out, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# review file for the by-hand check
L = ["# Golden set v2: by-hand check sheet", "",
     "For every question: the question, the gold answer, and for each fact the chunk(s) it was matched in with a snippet.",
     "Open the filing URL, find the passage, and tick the box if the chunk and the answer are right.", ""]
for r in rows:
    L += [f"## {r['qid']}  [{r['type']}]  {', '.join(r['filings'])}", f"**Q:** {r['question']}", f"**Gold answer:** {r['gold_answer']}"]
    if r.get("relation_chain"):
        L.append(f"**Chain:** {r['relation_chain']}")
    for fn in r["gold_facts"]:
        L.append(f"- [ ] `{fn}` ({F[fn][0]} {F[fn][1]}), {len(SNIP[fn])} chunk(s)")
        for cid, sn in SNIP[fn][:3]:
            L.append(f"    - `{cid}`: ...{sn[:260]}...  ({BY_ID[cid]['source_url']})")
    L.append("")
(ROOT / "data/golden_v2_review.md").write_text("\n".join(L), encoding="utf-8")

for r in rows:
    print(f"{r['qid']} [{r['type']:13}] gold={len(r['gold_chunk_ids']):2} {r['question'][:90]}")
print("types:", {t: types.count(t) for t in dict.fromkeys(types)}, "+ deep:", len(DEEP))
