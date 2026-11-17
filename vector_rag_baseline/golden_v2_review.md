# Golden set v2: by-hand check sheet

For every question: the question, the gold answer, and for each fact the chunk(s) it was matched in with a snippet.
Open the filing URL, find the passage, and tick the box if the chunk and the answer are right.

## v2_q01  [single]  AAPL FY2025
**Q:** What were Apple's total net sales in fiscal 2025 (fiscal year ended September 27, 2025)?
**Gold answer:** $416,161 million (about $416.2 billion).
- [ ] `a_sales25` (AAPL FY2025), 5 chunk(s)
    - `AAPL_FY2025_ITEM7_0004`: ... Rest of Asia Pacific | 33,696 | 10% | 30,658 | 4% | 29,615 Total net sales | $416,161 | 6% | $391,035 | 2% | $383,285 Americas Americas net sales...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM7_0005`: ...39,845 Services (1) | 109,158 | 14% | 96,169 | 13% | 85,200 Total net sales | $416,161 | 6% | $391,035 | 2% | $383,285 (1) Services net sales incl...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0000`: ... | $294,866 | $298,085 Services | 109,158 | 96,169 | 85,200 Total net sales | 416,161 | 391,035 | 383,285 Cost of sales: Products | 194,116 | 185...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q02  [single]  AAPL FY2025
**Q:** How much did Apple spend on research and development in fiscal 2025?
**Gold answer:** $34,550 million.
- [ ] `a_rd25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM7_0007`: ...(dollars in millions): 2025 | Change | 2024 | Change | 2023 Research and development | $34,550 | 10% | $31,370 | 5% | $29,915 Percentage of total net sale...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0000`: ...ss margin | 195,201 | 180,683 | 169,148 Operating expenses: Research and development | 34,550 | 31,370 | 29,915 Selling, general and administrative | 27,...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q03  [single]  AAPL FY2025
**Q:** How many full-time equivalent employees did Apple have as of September 27, 2025?
**Gold answer:** Approximately 166,000.
- [ ] `a_fte25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM1_0010`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees....  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM1_0011`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees. The Company believes that compensation should be competiti...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q04  [single]  AAPL FY2025
**Q:** What were Apple's Services net sales in fiscal 2025?
**Gold answer:** $109,158 million.
- [ ] `a_serv25` (AAPL FY2025), 3 chunk(s)
    - `AAPL_FY2025_ITEM7_0005`: ...me and Accessories | 35,686 | (4)% | 37,005 | (7)% | 39,845 Services (1) | 109,158 | 14% | 96,169 | 13% | 85,200 Total net sales | $416,161 | ...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0000`: ...0,2023 Net sales: Products | $307,003 | $294,866 | $298,085 Services | 109,158 | 96,169 | 85,200 Total net sales | 416,161 | 391,035 | 383...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0015`: ... Wearables, Home and Accessories | 35,686 | 37,005 | 39,845 Services (1) | 109,158 | 96,169 | 85,200 Total net sales | $416,161 | $391,035 | $...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q05  [single]  MSFT FY2026
**Q:** What was Microsoft's total revenue in fiscal 2026 (fiscal year ended June 30, 2026)?
**Gold answer:** $331,839 million (about $331.8 billion).
- [ ] `m_rev26` (MSFT FY2026), 5 chunk(s)
    - `MSFT_FY2026_ITEM7_0009`: ...ges and per share amounts) | 2026 | 2025 | PercentageChange Revenue | $331,839 | $281,724 | 18% Gross margin | 225,465 | 193,893 | 16% Ope...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM7_0012`: ...15,245 | 6% Operating income | $14,386 | $14,166 | 2% Total Revenue | $331,839 | $281,724 | 18% Cost of revenue | 106,374 | 87,831 | 21%...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM7_0013`: ...ntageChange Operating income | $14,386 | $14,166 | 2% Total Revenue | $331,839 | $281,724 | 18% Cost of revenue | 106,374 | 87,831 | 21% O...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q06  [single]  MSFT FY2026
**Q:** What was Microsoft's net income in fiscal 2026?
**Gold answer:** $133,749 million.
- [ ] `m_ni26` (MSFT FY2026), 7 chunk(s)
    - `MSFT_FY2026_ITEM7_0009`: ... | 193,893 | 16% Operating income | 155,237 | 128,528 | 21% Net income | 133,749 | 101,832 | 31% Diluted earnings per share | 17.95 | 13.64 ...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM7_0010`: ...PercentageChange Operating income | 155,237 | 128,528 | 21% Net income | 133,749 | 101,832 | 31% Diluted earnings per share | 17.95 | 13.64 ...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM7_0023`: ...), net (non-GAAP) | $4,167 | $(138) | $(164) | 3,120% | 16% Net income | $133,749 | $101,832 | $88,136 | 31% | 16% Net (gains) losses from in...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q07  [single]  MSFT FY2026
**Q:** How many people did Microsoft employ on a full-time basis as of June 30, 2026?
**Gold answer:** Approximately 223,000 (121,000 in the U.S. and 102,000 internationally).
- [ ] `m_emp26` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM1_0019`: ... end users. HUMAN CAPITAL RESOURCES As of June 30, 2026, we employed approximately 223,000 people on a full-time basis, 121,000 in the U.S. and 102,00...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q08  [single]  MSFT FY2026
**Q:** How much did Microsoft spend on research and development in fiscal 2026?
**Gold answer:** $35,562 million.
- [ ] `m_rd26` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM7_0017`: ...lions, except percentages) | 2026 | 2025 | PercentageChange Research and development | $35,562 | $32,488 | 9% As a percent of revenue | 11% | 12% | (1)ppt...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0000`: ... 87,831 | 74,114 Gross margin | 225,465 | 193,893 | 171,008 Research and development | 35,562 | 32,488 | 29,510 Sales and marketing | 26,710 | 25,654 | 2...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q09  [single]  JNJ FY2025
**Q:** What was Johnson & Johnson's total research and development expense in fiscal 2025?
**Gold answer:** $14,665 million.
- [ ] `j_rd25` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM7_0027`: ...9.6% | $13,529 | 23.8% MedTech | 2,838 | 8.4 | 3,703 | 11.6 Total research and development expense | $14,665 | 15.6% | $17,232 | 19.4% Percent increase/(decrease) over ...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q10  [single]  JNJ FY2025
**Q:** How many employees does Johnson & Johnson have worldwide, according to its fiscal 2025 10-K?
**Gold answer:** Approximately 138,200.
- [ ] `j_emp25` (JNJ FY2025), 4 chunk(s)
    - `JNJ_FY2025_ITEM1_0000`: ...l Johnson & Johnson and its subsidiaries (the Company) have approximately 138,200 employees worldwide engaged in the research and development, manufact...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM7_0000`: ...s Johnson & Johnson and its subsidiaries (the Company) have approximately 138,200 employees worldwide engaged in the research and development, manufact...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM7_0003`: ...ips that will profoundly impact of health for humanity. Our approximately 138,200 employees are critical drivers of the Company's success. Employees ar...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q11  [single]  JNJ FY2025
**Q:** What were Johnson & Johnson's Innovative Medicine segment sales in fiscal 2025?
**Gold answer:** $60,401 million (about $60.4 billion).
- [ ] `j_im25` (JNJ FY2025), 2 chunk(s)
    - `JNJ_FY2025_ITEM7_0012`: ...11.0 | 11.0 | — Other | 1,145 | 1,189 | (3.7) | (4.0) | 0.3 Total Innovative Medicine Sales | $60,401 | 56,964 | 6.0% | 5.3% | 0.7% (1) Previously in Other Oncol...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0126`: ...ne | MedTech | Total | InnovativeMedicine | MedTech | Total Sales to customers | $60,401 | 33,792 | 56,964 | 31,857 | 54,759 | 30,400 Cost of produc...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q12  [single]  JNJ FY2025
**Q:** What were Johnson & Johnson's net earnings in fiscal 2025?
**Gold answer:** $26,804 million.
- [ ] `j_ne25` (JNJ FY2025), 3 chunk(s)
    - `JNJ_FY2025_ITEM8_0003`: ...continued operations, net of tax (Note 21) | — | — | 21,827 Net earnings | $26,804 | 14,066 | 35,153 Net earnings per share (Notes 1 and 15) C...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0004`: ...ve income (Dollars in Millions) (Note 1) 2025 | 2024 | 2023 Net earnings | $26,804 | 14,066 | 35,153 Other comprehensive income (loss), net of...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0008`: ... 1) 2025 | 2024 | 2023 Cash flows from operating activities Net earnings | $26,804 | 14,066 | 35,153 Adjustments to reconcile net earnings to ...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q13  [relation]  JNJ FY2025
**Q:** Which Johnson & Johnson segment sells the drug licensed from Genmab, and what were that segment's sales in fiscal 2025?
**Gold answer:** DARZALEX is licensed from Genmab A/S and sold by the Innovative Medicine segment, whose fiscal 2025 sales were $60,401 million.
**Chain:** Genmab -> DARZALEX (licensed) -> Innovative Medicine segment -> segment sales
- [ ] `j_genmab` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM1_0011`: ...tely 15.0% of the Company's total revenues for fiscal 2025. Genmab A/S owns two patent families related to DARZALEX, and Janssen Biotech, Inc. (a wholly-owned subsidiary of the Company) has an exc...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `j_darz_im` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM1_0001`: ...ospitals and healthcare professionals for prescription use. Key products in the Innovative Medicine segment include: CARVYKTI (ciltacabtagene autoleucel), a chimeric antigen receptor (CAR)-T-cell therapy for the treatment of patients with relapsed/refractory m...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `j_im25` (JNJ FY2025), 2 chunk(s)
    - `JNJ_FY2025_ITEM7_0012`: ...11.0 | 11.0 | — Other | 1,145 | 1,189 | (3.7) | (4.0) | 0.3 Total Innovative Medicine Sales | $60,401 | 56,964 | 6.0% | 5.3% | 0.7% (1) Previously in Other Oncol...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0126`: ...ne | MedTech | Total | InnovativeMedicine | MedTech | Total Sales to customers | $60,401 | 33,792 | 56,964 | 31,857 | 54,759 | 30,400 Cost of produc...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q14  [relation]  JNJ FY2025
**Q:** Which Johnson & Johnson subsidiary holds the exclusive license to Genmab's DARZALEX patent families, and in which U.S. state is it incorporated?
**Gold answer:** Janssen Biotech, Inc., incorporated in Pennsylvania.
**Chain:** Genmab -> Janssen Biotech, Inc. (10-K Item 1) -> Exhibit 21 jurisdiction
- [ ] `j_genmab` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM1_0011`: ...tely 15.0% of the Company's total revenues for fiscal 2025. Genmab A/S owns two patent families related to DARZALEX, and Janssen Biotech, Inc. (a wholly-owned subsidiary of the Company) has an exc...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `j_janssen_pa` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_EX21_0001`: ...ra-Cellular Therapies, Inc. | Delaware ITI, Inc. | Delaware Janssen Biotech, Inc. | Pennsylvania Janssen Global Services, LLC | New Jersey Janssen Oncology,...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/ex21-subsidiariesxform10xk.htm)

## v2_q15  [relation]  JNJ FY2025
**Q:** Johnson & Johnson acquired Shockwave Medical in 2024. Which segment reports Shockwave's sales, and how much were they in fiscal 2025?
**Gold answer:** Shockwave is reported in the MedTech segment (circulatory restoration products); its fiscal 2025 sales were $1,146 million (vs $564 million in 2024).
**Chain:** Shockwave Medical (acquired May 31, 2024) -> MedTech segment -> Shockwave sales
- [ ] `j_shock_acq` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM8_0141`: ...25 and 2024 were not material. On May 31, 2024, the Company acquired all the outstanding shares of Shockwave Medical Inc. (SWAV), a leading, first-to-market provider of innovat...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `j_shock_mt` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM1_0007`: ...going a high-risk percutaneous coronary intervention (PCI), circulatory restoration products (Shockwave) for the treatment of calcified coronary artery disease (CAD...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `j_shock_sales` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM7_0022`: ...7.0 | 6.4 | 0.6 Abiomed | 1,751 | 1,496 | 17.1 | 16.2 | 0.9 Shockwave(1) | 1,146 | 564*** Other Cardiovascular | 397 | 380 | 4.3 | 3.8 | 0.5...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q16  [relation]  MSFT FY2026
**Q:** What effect did the OpenAI Recapitalization have on Microsoft's other income in fiscal 2026, and how large were the net gains from its OpenAI investments?
**Gold answer:** Microsoft's ownership of OpenAI was diluted and it recorded dilution gains in other income (expense), net; net gains from OpenAI investments were $6.5 billion in fiscal 2026 (vs $4.8 billion of net losses in fiscal 2025).
**Chain:** Microsoft -> OpenAI (equity-method investment) -> OpenAI Recapitalization -> dilution gain -> other income
- [ ] `m_openai_recap` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM8_0026`: ...blic benefit corporation and completed a recapitalization (“OpenAI Recapitalization”). During fiscal year 2026, our proportionate ownership of OpenAI decreased due to the OpenAI Recapitalization and other funding activity, and we recorded dilution gains in oth...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
- [ ] `m_openai_gain` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM7_0019`: ...income (expense), net. Other income (expense), net included $6.5 billion of net gains and $4.8 billion of net losses for fiscal years 2026 and 2025, respectively, from investments in OpenAI, primarily net recognized gains (losses) on our equity meth...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q17  [relation]  MSFT FY2026
**Q:** Which Microsoft segment received the goodwill from the Activision Blizzard acquisition, and what was that segment's revenue in fiscal 2026?
**Gold answer:** The goodwill was assigned to the More Personal Computing segment, whose fiscal 2026 revenue was $54,052 million.
**Chain:** Activision Blizzard acquisition -> goodwill -> More Personal Computing segment -> segment revenue
- [ ] `m_act_acq` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM8_0052`: ... Other liabilities | (3,620) Total purchase price | $75,408 Goodwill was assigned to our More Personal Computing segment. The goodwill was primarily attributed to increased synergi...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
- [ ] `m_mpc26` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM7_0012`: ...43 | 21,505 | 7% Operating income | $56,972 | $44,589 | 28% More Personal Computing Revenue | $54,052 | $54,649 | (1)% Cost of revenue | 23,481 | 25,238 | (7)% O...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0090`: ...505 | 20,040 Operating income | $56,972 | $44,589 | $37,813 More Personal Computing Revenue | $54,052 | $54,649 | $50,838 Cost of revenue | 23,481 | 25,238 | 24,...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q18  [relation]  MSFT FY2026
**Q:** Which Microsoft segment includes Azure, and what was that segment's revenue in fiscal 2026?
**Gold answer:** Azure is part of the Intelligent Cloud segment, whose fiscal 2026 revenue was $137,791 million.
**Chain:** Azure -> Intelligent Cloud segment -> segment revenue
- [ ] `m_ic_def` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM1_0010`: ... on-premises business solution providers. Intelligent Cloud Our Intelligent Cloud segment consists of our public, private, and hybrid server products and cloud services that power modern business and developers. This segment primarily comprises: • Server produ...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0087`: ...and on-premises ERP and CRM applications. Intelligent Cloud Our Intelligent Cloud segment consists of our public, private, and hybrid server products and cloud services that power modern business and developers. This segment primarily comprises: • Server produ...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
- [ ] `m_ic26` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM7_0012`: ...00 | 28,615 | 9% Operating income | $83,879 | $69,773 | 20% Intelligent Cloud Revenue | $137,791 | $106,265 | 30% Cost of revenue | 57,876 | 40,171 | 44% Op...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0089`: ...615 | 27,548 Operating income | $83,879 | $69,773 | $59,661 Intelligent Cloud Revenue | $137,791 | $106,265 | $87,464 Cost of revenue | 57,876 | 40,171 | 29...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q19  [relation]  MSFT FY2026
**Q:** Which Microsoft subsidiary named after the professional network is incorporated in Ireland, and by what percent did that network's revenue grow in fiscal 2026?
**Gold answer:** LinkedIn Ireland Unlimited Company (Ireland); LinkedIn revenue increased 11%.
**Chain:** LinkedIn -> Exhibit 21 subsidiary (Ireland) -> LinkedIn revenue growth (MD&A)
- [ ] `m_li_sub` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_EX21_0000`: ..., Inc. | United States LinkedIn Corporation | United States LinkedIn Ireland Unlimited Company | Ireland Activision Blizzard, Inc. | United States Activision Publis...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-ex21.htm)
- [ ] `m_li_growth` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM7_0001`: ...7%. • Microsoft 365 Consumer cloud revenue increased 28%. • LinkedIn revenue increased 11%. • Dynamics 365 revenue increased 18%. • Azure and other cl...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q20  [relation]  AAPL FY2025
**Q:** Which Apple product category includes Beats products, and what were that category's net sales in fiscal 2025?
**Gold answer:** Beats headphones are part of Wearables, Home and Accessories, whose fiscal 2025 net sales were $35,686 million.
**Chain:** Beats -> Wearables, Home and Accessories category -> category net sales
- [ ] `a_beats` (AAPL FY2025), 1 chunk(s)
    - `AAPL_FY2025_ITEM1_0000`: ...e includes iPad Pro ® , iPad Air ® , iPad and iPad mini ® . Wearables, Home and Accessories Wearables includes smartwatches, wireless headphones and spatial computers. The Company's line of smartwatches, based on its watchOS ® operating system, includes Apple ...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `a_wha25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM7_0005`: ...4 | 2% | 29,357 iPad | 28,023 | 5% | 26,694 | (6)% | 28,300 Wearables, Home and Accessories | 35,686 | (4)% | 37,005 | (7)% | 39,845 Services (1) | 109,158 | 14...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0015`: ... | 33,708 | 29,984 | 29,357 iPad | 28,023 | 26,694 | 28,300 Wearables, Home and Accessories | 35,686 | 37,005 | 39,845 Services (1) | 109,158 | 96,169 | 85,200 ...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q21  [relation]  AAPL FY2025
**Q:** Apple's 10-K lists the countries where its outsourcing partners are mainly located. Which of those countries also have an Apple subsidiary named in Exhibit 21?
**Gold answer:** China mainland (Apple Computer Trading (Shanghai) Co., Ltd.), India (Apple India Private Limited), Japan (Apple Japan, Inc.), South Korea (Apple Korea Limited) and Vietnam (Apple Vietnam Limited Liability Company); Taiwan has no listed subsidiary.
**Chain:** Outsourcing-partner countries (Item 1A) -> Exhibit 21 subsidiary jurisdictions -> intersection
- [ ] `a_mfg25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM1A_0003`: ...Company's manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, in addition...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM1A_0014`: ...Company's manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, in addition...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `a_ex21` (AAPL FY2025), 1 chunk(s)
    - `AAPL_FY2025_EX21_0000`: ....1 Subsidiaries of Apple Inc.* Jurisdictionof Incorporation Apple Asia Limited | Hong Kong Apple Asia LLC | Delaware, U.S. Apple Canada Inc. | Canada ...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm)

## v2_q22  [relation]  AAPL FY2025
**Q:** Apple Asia Limited is incorporated in Hong Kong. Which Apple reportable segment includes Hong Kong, and what were that segment's net sales in fiscal 2025?
**Gold answer:** Hong Kong is in the Greater China segment, whose fiscal 2025 net sales were $64,377 million.
**Chain:** Apple Asia Limited -> Hong Kong -> Greater China segment -> segment net sales
- [ ] `a_ex21` (AAPL FY2025), 1 chunk(s)
    - `AAPL_FY2025_EX21_0000`: ....1 Subsidiaries of Apple Inc.* Jurisdictionof Incorporation Apple Asia Limited | Hong Kong Apple Asia LLC | Delaware, U.S. Apple Canada Inc. | Canada ...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm)
- [ ] `a_gc_def` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM1_0002`: ...an countries, as well as India, the Middle East and Africa. Greater China includes China mainland, Hong Kong and Taiwan. Rest of Asia Pacific includes Australia, New Zealand and t...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0047`: ...an countries, as well as India, the Middle East and Africa. Greater China includes China mainland, Hong Kong and Taiwan. Rest of Asia Pacific includes Australia, New Zealand and t...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `a_gc25` (AAPL FY2025), 1 chunk(s)
    - `AAPL_FY2025_ITEM7_0003`: ...% | $162,560 Europe | 111,032 | 10% | 101,328 | 7% | 94,294 Greater China | 64,377 | (4)% | 66,952 | (8)% | 72,559 Japan | 28,703 | 15% | 25,0...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q23  [cross_year]  AAPL FY2024, AAPL FY2025
**Q:** How did Apple's full-time equivalent headcount change between its fiscal 2024 and fiscal 2025 10-Ks?
**Gold answer:** It rose by about 2,000, from approximately 164,000 (Sept 28, 2024) to approximately 166,000 (Sept 27, 2025).
- [ ] `a_fte24` (AAPL FY2024), 2 chunk(s)
    - `AAPL_FY2024_ITEM1_0009`: ...k of their lives. As of September 28, 2024, the Company had approximately 164,000 full-time equivalent employees. Compensation and Benefits...  (https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)
    - `AAPL_FY2024_ITEM1_0010`: ...k of their lives. As of September 28, 2024, the Company had approximately 164,000 full-time equivalent employees. Compensation and Benefits The Company believes that compen...  (https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)
- [ ] `a_fte25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM1_0010`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees....  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM1_0011`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees. The Company believes that compensation should be competiti...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q24  [cross_year]  MSFT FY2025, MSFT FY2026
**Q:** How did Microsoft's full-time headcount change between June 30, 2025 and June 30, 2026?
**Gold answer:** It fell by about 5,000, from approximately 228,000 to approximately 223,000.
- [ ] `m_emp25` (MSFT FY2025), 1 chunk(s)
    - `MSFT_FY2025_ITEM1_0019`: ... end users. HUMAN CAPITAL RESOURCES As of June 30, 2025, we employed approximately 228,000 people on a full-time basis, 125,000 in the U.S. and 103,00...  (https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm)
- [ ] `m_emp26` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM1_0019`: ... end users. HUMAN CAPITAL RESOURCES As of June 30, 2026, we employed approximately 223,000 people on a full-time basis, 121,000 in the U.S. and 102,00...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q25  [cross_year]  JNJ FY2024, JNJ FY2025
**Q:** What share of Johnson & Johnson's total revenues came from DARZALEX (with DARZALEX FASPRO) in fiscal 2024 versus fiscal 2025?
**Gold answer:** About 13.1% in fiscal 2024 and 15.0% in fiscal 2025 (up about 1.9 percentage points).
- [ ] `j_darz24` (JNJ FY2024), 1 chunk(s)
    - `JNJ_FY2024_ITEM1_0010`: ... FASPRO (daratumumab and hyaluronidase-fihj), accounted for approximately 13.1% of the Company's total revenues for fiscal 2024. Accordingly, the patents related to these products are bel...  (https://www.sec.gov/Archives/edgar/data/200406/000020040625000038/jnj-20241229.htm)
- [ ] `j_darz25` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM1_0011`: ... FASPRO (daratumumab and hyaluronidase-fihj), accounted for approximately 15.0% of the Company's total revenues for fiscal 2025. Genmab A/S owns two patent families related to DARZALEX, a...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q26  [cross_year]  MSFT FY2025, MSFT FY2026
**Q:** How much did Microsoft's Intelligent Cloud segment revenue grow from fiscal 2025 to fiscal 2026?
**Gold answer:** By $31,526 million (about 29.7%), from $106,265 million to $137,791 million.
- [ ] `m_ic25` (MSFT FY2025), 2 chunk(s)
    - `MSFT_FY2025_ITEM7_0011`: ...15 | 27,548 | 4% Operating Income | $69,773 | $59,661 | 17% Intelligent Cloud Revenue | $106,265 | $87,464 | 21% Cost of revenue | 40,171 | 29,611 | 36% Ope...  (https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm)
    - `MSFT_FY2025_ITEM8_0086`: ...548 | 26,875 Operating Income | $69,773 | $59,661 | $50,074 Intelligent Cloud Revenue | $106,265 | $87,464 | $72,944 Cost of revenue | 40,171 | 29,611 | 24,...  (https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm)
- [ ] `m_ic26` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM7_0012`: ...00 | 28,615 | 9% Operating income | $83,879 | $69,773 | 20% Intelligent Cloud Revenue | $137,791 | $106,265 | 30% Cost of revenue | 57,876 | 40,171 | 44% Op...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0089`: ...615 | 27,548 Operating income | $83,879 | $69,773 | $59,661 Intelligent Cloud Revenue | $137,791 | $106,265 | $87,464 Cost of revenue | 57,876 | 40,171 | 29...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q27  [cross_company]  AAPL FY2025, MSFT FY2026
**Q:** Which spent more on research and development, Apple in fiscal 2025 or Microsoft in fiscal 2026, and by how much?
**Gold answer:** Microsoft, by $1,012 million ($35,562 million vs Apple's $34,550 million).
- [ ] `a_rd25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM7_0007`: ...(dollars in millions): 2025 | Change | 2024 | Change | 2023 Research and development | $34,550 | 10% | $31,370 | 5% | $29,915 Percentage of total net sale...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0000`: ...ss margin | 195,201 | 180,683 | 169,148 Operating expenses: Research and development | 34,550 | 31,370 | 29,915 Selling, general and administrative | 27,...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `m_rd26` (MSFT FY2026), 2 chunk(s)
    - `MSFT_FY2026_ITEM7_0017`: ...lions, except percentages) | 2026 | 2025 | PercentageChange Research and development | $35,562 | $32,488 | 9% As a percent of revenue | 11% | 12% | (1)ppt...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
    - `MSFT_FY2026_ITEM8_0000`: ... 87,831 | 74,114 Gross margin | 225,465 | 193,893 | 171,008 Research and development | 35,562 | 32,488 | 29,510 Sales and marketing | 26,710 | 25,654 | 2...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

## v2_q28  [cross_company]  AAPL FY2025, JNJ FY2025, MSFT FY2026
**Q:** Rank Apple (as of September 27, 2025), Microsoft (as of June 30, 2026) and Johnson & Johnson (fiscal 2025 10-K) by number of employees.
**Gold answer:** Microsoft (about 223,000), then Apple (about 166,000), then Johnson & Johnson (about 138,200).
- [ ] `a_fte25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM1_0010`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees....  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM1_0011`: ...r discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees. The Company believes that compensation should be competiti...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `m_emp26` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM1_0019`: ... end users. HUMAN CAPITAL RESOURCES As of June 30, 2026, we employed approximately 223,000 people on a full-time basis, 121,000 in the U.S. and 102,00...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
- [ ] `j_emp25` (JNJ FY2025), 4 chunk(s)
    - `JNJ_FY2025_ITEM1_0000`: ...l Johnson & Johnson and its subsidiaries (the Company) have approximately 138,200 employees worldwide engaged in the research and development, manufact...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM7_0000`: ...s Johnson & Johnson and its subsidiaries (the Company) have approximately 138,200 employees worldwide engaged in the research and development, manufact...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM7_0003`: ...ips that will profoundly impact of health for humanity. Our approximately 138,200 employees are critical drivers of the Company's success. Employees ar...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

## v2_q29  [cross_company]  AAPL FY2025, JNJ FY2025, MSFT FY2026
**Q:** Which of Johnson & Johnson (2025), Microsoft (fiscal 2026) and Apple (fiscal 2025) spent the highest share of revenue on research and development, and what were the shares?
**Gold answer:** Johnson & Johnson at 15.6% of sales, then Microsoft at 11% of revenue, then Apple at 8% of net sales.
- [ ] `j_rdpct25` (JNJ FY2025), 1 chunk(s)
    - `JNJ_FY2025_ITEM7_0027`: ...9.6% | $13,529 | 23.8% MedTech | 2,838 | 8.4 | 3,703 | 11.6 Total research and development expense | $14,665 | 15.6% | $17,232 | 19.4% Percent increase/(decrease) over the prio...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
- [ ] `m_rdpct26` (MSFT FY2026), 1 chunk(s)
    - `MSFT_FY2026_ITEM7_0017`: ...lions, except percentages) | 2026 | 2025 | PercentageChange Research and development | $35,562 | $32,488 | 9% As a percent of revenue | 11% | 12% | (1)ppt Research and development expenses include pa...  (https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)
- [ ] `a_rdpct25` (AAPL FY2025), 1 chunk(s)
    - `AAPL_FY2025_ITEM7_0007`: ...(dollars in millions): 2025 | Change | 2024 | Change | 2023 Research and development | $34,550 | 10% | $31,370 | 5% | $29,915 Percentage of total net sales | 8% | 8% | 8% Selling, general and administrative | $27,601 | 6...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

## v2_q30  [cross_company]  AAPL FY2025, JNJ FY2025
**Q:** Which earned more net income, Apple in fiscal 2025 or Johnson & Johnson in 2025, and roughly how many times as much?
**Gold answer:** Apple: $112,010 million versus Johnson & Johnson's $26,804 million, about 4.2 times as much.
- [ ] `a_ni25` (AAPL FY2025), 2 chunk(s)
    - `AAPL_FY2025_ITEM8_0001`: ...3,736 Provision for income taxes | 20,719 | 29,749 | 16,741 Net income | $112,010 | $93,736 | $96,995 Earnings per share: Basic | $7.49 | $6....  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
    - `AAPL_FY2025_ITEM8_0016`: ...ons and shares in thousands): 2025 | 2024 | 2023 Numerator: Net income | $112,010 | $93,736 | $96,995 Denominator: Weighted-average basic sha...  (https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [ ] `j_ne25` (JNJ FY2025), 3 chunk(s)
    - `JNJ_FY2025_ITEM8_0003`: ...continued operations, net of tax (Note 21) | — | — | 21,827 Net earnings | $26,804 | 14,066 | 35,153 Net earnings per share (Notes 1 and 15) C...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0004`: ...ve income (Dollars in Millions) (Note 1) 2025 | 2024 | 2023 Net earnings | $26,804 | 14,066 | 35,153 Other comprehensive income (loss), net of...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
    - `JNJ_FY2025_ITEM8_0008`: ... 1) 2025 | 2024 | 2023 Cash flows from operating activities Net earnings | $26,804 | 14,066 | 35,153 Adjustments to reconcile net earnings to ...  (https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)
