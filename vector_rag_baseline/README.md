# seed_question_v2

Updated seed questions (golden set v2) on three companies: Johnson & Johnson, Apple, Microsoft (6 filings: JNJ FY2024/FY2025, AAPL FY2024/FY2025, MSFT FY2025/FY2026).

| Type | Count |
|---|---|
| single-hop (4 per company) | 12 |
| relation-chain multi-hop (2 hops) | 10 |
| cross-year (same company, two filings) | 4 |
| cross-company | 4 |
| deep relation chains (3-5 hops) | 5 |
| **Total** | **35** |

Gold chunk ids are pattern-matched; numbers and key terms in every gold answer were checked automatically against the gold chunks. A by-hand spot-check against the 10-Ks is still pending (`golden_v2_review.md`).

Files: `questions_v2.jsonl`, `golden_v2_review.md`, `build_questions_v2.py` (rebuilds both from `data/chunks.jsonl`).

| ID | Type | Hops | Question | Gold answer |
|---|---|---|---|---|
| v2_q01 | single | 1 | What were Apple's total net sales in fiscal 2025 (fiscal year ended September 27, 2025)? | $416,161 million (about $416.2 billion). |
| v2_q02 | single | 1 | How much did Apple spend on research and development in fiscal 2025? | $34,550 million. |
| v2_q03 | single | 1 | How many full-time equivalent employees did Apple have as of September 27, 2025? | Approximately 166,000. |
| v2_q04 | single | 1 | What were Apple's Services net sales in fiscal 2025? | $109,158 million. |
| v2_q05 | single | 1 | What was Microsoft's total revenue in fiscal 2026 (fiscal year ended June 30, 2026)? | $331,839 million (about $331.8 billion). |
| v2_q06 | single | 1 | What was Microsoft's net income in fiscal 2026? | $133,749 million. |
| v2_q07 | single | 1 | How many people did Microsoft employ on a full-time basis as of June 30, 2026? | Approximately 223,000 (121,000 in the U.S. and 102,000 internationally). |
| v2_q08 | single | 1 | How much did Microsoft spend on research and development in fiscal 2026? | $35,562 million. |
| v2_q09 | single | 1 | What was Johnson & Johnson's total research and development expense in fiscal 2025? | $14,665 million. |
| v2_q10 | single | 1 | How many employees does Johnson & Johnson have worldwide, according to its fiscal 2025 10-K? | Approximately 138,200. |
| v2_q11 | single | 1 | What were Johnson & Johnson's Innovative Medicine segment sales in fiscal 2025? | $60,401 million (about $60.4 billion). |
| v2_q12 | single | 1 | What were Johnson & Johnson's net earnings in fiscal 2025? | $26,804 million. |
| v2_q13 | relation | 2 | Which Johnson & Johnson segment sells the drug licensed from Genmab, and what were that segment's sales in fiscal 2025? | DARZALEX is licensed from Genmab A/S and sold by the Innovative Medicine segment, whose fiscal 2025 sales were $60,401 million. |
| v2_q14 | relation | 2 | Which Johnson & Johnson subsidiary holds the exclusive license to Genmab's DARZALEX patent families, and in which U.S. state is it incorporated? | Janssen Biotech, Inc., incorporated in Pennsylvania. |
| v2_q15 | relation | 2 | Johnson & Johnson acquired Shockwave Medical in 2024. Which segment reports Shockwave's sales, and how much were they in fiscal 2025? | Shockwave is reported in the MedTech segment (circulatory restoration products); its fiscal 2025 sales were $1,146 million (vs $564 million in 2024). |
| v2_q16 | relation | 2 | What effect did the OpenAI Recapitalization have on Microsoft's other income in fiscal 2026, and how large were the net gains from its OpenAI investments? | Microsoft's ownership of OpenAI was diluted and it recorded dilution gains in other income (expense), net; net gains from OpenAI investments were $6.5 billion in fiscal 2026 (vs $4.8 billion of net losses in fiscal 2025). |
| v2_q17 | relation | 2 | Which Microsoft segment received the goodwill from the Activision Blizzard acquisition, and what was that segment's revenue in fiscal 2026? | The goodwill was assigned to the More Personal Computing segment, whose fiscal 2026 revenue was $54,052 million. |
| v2_q18 | relation | 2 | Which Microsoft segment includes Azure, and what was that segment's revenue in fiscal 2026? | Azure is part of the Intelligent Cloud segment, whose fiscal 2026 revenue was $137,791 million. |
| v2_q19 | relation | 2 | Which Microsoft subsidiary named after the professional network is incorporated in Ireland, and by what percent did that network's revenue grow in fiscal 2026? | LinkedIn Ireland Unlimited Company (Ireland); LinkedIn revenue increased 11%. |
| v2_q20 | relation | 2 | Which Apple product category includes Beats products, and what were that category's net sales in fiscal 2025? | Beats headphones are part of Wearables, Home and Accessories, whose fiscal 2025 net sales were $35,686 million. |
| v2_q21 | relation | 2 | Apple's 10-K lists the countries where its outsourcing partners are mainly located. Which of those countries also have an Apple subsidiary named in Exhibit 21? | China mainland (Apple Computer Trading (Shanghai) Co., Ltd.), India (Apple India Private Limited), Japan (Apple Japan, Inc.), South Korea (Apple Korea Limited) and Vietnam (Apple Vietnam Limited Liability Company); Taiwan has no listed subsidiary. |
| v2_q22 | relation | 2 | Apple Asia Limited is incorporated in Hong Kong. Which Apple reportable segment includes Hong Kong, and what were that segment's net sales in fiscal 2025? | Hong Kong is in the Greater China segment, whose fiscal 2025 net sales were $64,377 million. |
| v2_q23 | cross_year | 2 | How did Apple's full-time equivalent headcount change between its fiscal 2024 and fiscal 2025 10-Ks? | It rose by about 2,000, from approximately 164,000 (Sept 28, 2024) to approximately 166,000 (Sept 27, 2025). |
| v2_q24 | cross_year | 2 | How did Microsoft's full-time headcount change between June 30, 2025 and June 30, 2026? | It fell by about 5,000, from approximately 228,000 to approximately 223,000. |
| v2_q25 | cross_year | 2 | What share of Johnson & Johnson's total revenues came from DARZALEX (with DARZALEX FASPRO) in fiscal 2024 versus fiscal 2025? | About 13.1% in fiscal 2024 and 15.0% in fiscal 2025 (up about 1.9 percentage points). |
| v2_q26 | cross_year | 2 | How much did Microsoft's Intelligent Cloud segment revenue grow from fiscal 2025 to fiscal 2026? | By $31,526 million (about 29.7%), from $106,265 million to $137,791 million. |
| v2_q27 | cross_company | 2 | Which spent more on research and development, Apple in fiscal 2025 or Microsoft in fiscal 2026, and by how much? | Microsoft, by $1,012 million ($35,562 million vs Apple's $34,550 million). |
| v2_q28 | cross_company | 2 | Rank Apple (as of September 27, 2025), Microsoft (as of June 30, 2026) and Johnson & Johnson (fiscal 2025 10-K) by number of employees. | Microsoft (about 223,000), then Apple (about 166,000), then Johnson & Johnson (about 138,200). |
| v2_q29 | cross_company | 2 | Which of Johnson & Johnson (2025), Microsoft (fiscal 2026) and Apple (fiscal 2025) spent the highest share of revenue on research and development, and what were the shares? | Johnson & Johnson at 15.6% of sales, then Microsoft at 11% of revenue, then Apple at 8% of net sales. |
| v2_q30 | cross_company | 2 | Which earned more net income, Apple in fiscal 2025 or Johnson & Johnson in 2025, and roughly how many times as much? | Apple: $112,010 million versus Johnson & Johnson's $26,804 million, about 4.2 times as much. |
| v2_q31 | relation_deep | 4 | Which company licenses J&J's largest product to it, and how large was the royalty J&J paid that company in 2025 as a share of that product's 2025 sales? | Genmab A/S (DARZALEX, about 15.0% of J&J revenue); royalties were about $2.4 billion on DARZALEX sales of $14,351 million, roughly 16.7% (within the 12% to 20% royalty range). |
| v2_q32 | relation_deep | 4 | J&J acquired Shockwave Medical in 2024. Which franchise reports Shockwave sales, what share of that franchise's 2025 sales was Shockwave, and where is Shockwave Medical, Inc. incorporated? | Shockwave is in the Cardiovascular franchise of MedTech; its $1,146 million was about 12.8% of Cardiovascular sales of $8,928 million. Shockwave Medical, Inc. is incorporated in Delaware. |
| v2_q33 | relation_deep | 3 | Which Microsoft segment received the Activision Blizzard goodwill, what was that segment's goodwill balance at June 30, 2026, and in which country is the subsidiary Activision Publishing, Inc. incorporated? | The More Personal Computing segment; its goodwill was $62,340 million at June 30, 2026. Activision Publishing, Inc. is incorporated in the United States. |
| v2_q34 | relation_deep | 4 | What happened to Microsoft's ownership of OpenAI in the October 2025 recapitalization, how large were the net gains from OpenAI investments in other income, and by how much did they raise fiscal 2026 net income and diluted EPS? | Its proportionate ownership decreased and it recorded dilution gains; net gains from OpenAI investments were $6.5 billion in other income (expense), net, and raised net income by $5.0 billion and diluted EPS by $0.67. |
| v2_q35 | relation_deep | 5 | Apple's Exhibit 21 lists subsidiaries in India and in Japan. Which reportable segment contains each country, and which of the two segments had higher net sales in fiscal 2025? | India is in the Europe segment ($111,032 million) and Japan is its own segment ($28,703 million); Europe was higher, by $82,329 million. |
