# Hand check of 30 LLM edges (fin10k_v1)

For each edge: is the relation stated in the quote, in this direction, between these two entities, and was each name matched to the right node? Mark Y or N in `edge_check_llm.csv` (error types: wrong_direction, wrong_relation, not_stated, wrong_merge, generic).

## 1. `Ethicon` --has_product--> `Physiomesh Flexible Composite Mesh`

- **Chunk:** `JNJ_FY2025_ITEM8_0171`
- **Quote:** "product liability litigation associated with Ethicon Physiomesh Flexible Composite Mesh"
- **Name matching:** "Ethicon" -> Ethicon [ambiguous]; "Physiomesh Flexible Composite Mesh" -> Physiomesh Flexible Composite Mesh [new]

```
The Company has established accruals with respect to product liability litigation associated with Ethicon Physiomesh Flexible Composite Mesh, PROCEED Mesh and PROCEED Ventral Patch, and PROLENE Polypropylene Hernia System products. Innovative Medicine ELMIRON
Claims for personal injury have been made against a number of Johnson & Johnson companies, including Janssen Pharmaceuticals, Inc. and the Company, arising out of the use of ELMIRON, a prescription medication indicated for the relief of bladder pain or discomfort associated with
```

**Correct (Y/N):** ___   **Error type:** ___

## 2. `Johnson & Johnson` --has_product--> `EDURANT/rilpivirine (JNJ)`

- **Chunk:** `JNJ_FY2025_ITEM1_0005` (+2 more)
- **Quote:** "EDURANT (rilpivirine), PREZISTA (darunavir) and PREZCOBIX/REZOLSTA (darunavir/cobicistat), antiretroviral medicines"
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "EDURANT" -> EDURANT/rilpivirine (JNJ) [exact]

```
aliperidone palmitate), for the treatment of schizophrenia in patients after they have been adequately treated with INVEGA SUSTENNA for at least four months;
SPRAVATO (Esketamine), a nasal spray, used along with an oral antidepressant, to treat adults with treatment-resistant depression (TRD) and depressive symptoms in adults with major depressive disorder (MDD) with suicidal thoughts or actions; EDURANT (rilpivirine), PREZISTA (darunavir) and PREZCOBIX/REZOLSTA (darunavir/cobicistat), antiretroviral medicines for the treatment of human immunodeficiency virus (HIV) in combination with other antiretroviral products and SYMTUZA (darunavir/cobicistat/emtricitabine/tenofovir alafenamide), a once-daily single tablet regimen for the treatment of HIV; OPSUMIT (macitentan)/OPSYNVI (macitentan/tadalafil) as monotherapy or in combination, indicated for the long-term treatment of pulmonary arterial hypertension (
```

**Correct (Y/N):** ___   **Error type:** ___

## 3. `Apple Inc.` --has_product--> `App Store`

- **Chunk:** `AAPL_FY2025_ITEM1_0001` (+4 more)
- **Quote:** "The Company operates various platforms, including the App Store ® , that allow customers to discover and download applications and digital content"
- **Name matching:** "Apple Inc." -> Apple Inc. [exact]; "App Store" -> App Store [new]

```
the global Apple authorized service network for repair and replacement services, and in many cases additional coverage for instances of accidental damage or theft and loss, depending on the country and type of product.
Cloud Services
The Company's cloud services store and keep customers' content up-to-date and available across multiple Apple devices and Windows personal computers.
Digital Content
The Company operates various platforms, including the App Store ® , that allow customers to discover and download applications and digital content, such as books, music, video, games and podcasts.
```

**Correct (Y/N):** ___   **Error type:** ___

## 4. `Microsoft Corporation` --has_product--> `Outlook.com`

- **Chunk:** `MSFT_FY2026_ITEM1_0007` (+3 more)
- **Quote:** "Microsoft 365 Consumer cloud revenue is also affected by the demand for communication and storage through Outlook.com and OneDrive, which is largely driven by subscriptions and advertising."
- **Name matching:** "Microsoft Corporation" -> Microsoft Corporation [exact]; "Outlook.com" -> Outlook.com [new]

```
remises to Microsoft 365. Microsoft 365 Consumer Products and Cloud Services
Microsoft 365 Consumer is designed to increase personal productivity and creativity through a range of products and services. Growth depends on our ability to reach new users, add value to our core product set with new features including AI tools, and continue to expand our product and service offerings into new markets. Microsoft 365 Consumer cloud revenue and Office Consumer products revenue is mainly affected by the percentage of customers that buy Office with their new devices and the continued shift from Office licensed on-premises to Microsoft 365 Consumer subscriptions. Microsoft 365 Consumer cloud revenue is also affected by the demand for communication and storage through Outlook.com and OneDrive, which is largely driven by subscriptions and advertising.
PART I
LinkedIn
```

**Correct (Y/N):** ___   **Error type:** ___

## 5. `Janssen Inc.` --has_product--> `ZYTIGA (JNJ)`

- **Chunk:** `JNJ_FY2025_ITEM8_0196`
- **Quote:** "The complaint alleges that Janssen violated the federal False Claims Act and state law when providing pricing information for ZYTIGA to the government in connection with direct sales and reimbursement programs."
- **Name matching:** "Janssen" -> Janssen Inc. [exact]; "ZYTIGA" -> ZYTIGA (JNJ) [exact]

```
y judgment for Janssen on plaintiffs' claim regarding patents obtained through the acquisition of Momenta Pharmaceuticals, Inc. in 2020.
In December 2018, Janssen Biotech, Inc., Janssen Oncology, Inc., Janssen Research & Development, LLC, and Johnson & Johnson (collectively, Janssen) were served with a qui tam complaint on behalf of the United States, certain states, and the District of Columbia. The complaint alleges that Janssen violated the federal False Claims Act and state law when providing pricing information for ZYTIGA to the government in connection with direct sales and reimbursement programs. At this time, the federal and state governments have declined to intervene. In December 2021, the United States District Court for the District of New Jersey denied Janssen's motion to dismiss.
In August 2025, Xoma Corporation (Xoma) filed a complaint against Janssen Biotech, Inc. (Janssen) in the United States District Court for the Eastern District of Pennsylvania. The complaint alleges breach
```

**Correct (Y/N):** ___   **Error type:** ___

## 6. `Apple Inc.` --has_product--> `visionOS 26`

- **Chunk:** `AAPL_FY2025_ITEM7_0000` (+1 more)
- **Quote:** "Third Quarter 2025: • iOS 26, macOS Tahoe 26, iPadOS 26, watchOS 26, visionOS 26 and tvOS 26"
- **Name matching:** "Apple Inc." -> Apple Inc. [exact]; "visionOS 26" -> visionOS 26 [new]

```
Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
The following discussion should be read in conjunction with the consolidated financial statements and accompanying notes included in Part II, Item 8 of this Form 10-K. This Item generally discusses 2025 and 2024 items and year-to-year comparisons between 2025 and 2024. Discussions of 2023 items and year-to-year comparisons between 2024 and 2023 are not included, and can be found in “Management's Discussion and Analysis of Financial Condition and Results of Operations” in Part II, Item 7 of the Company's Annual Report on Form 10-K for the fiscal year ended September 28, 2024.
Product, Service and Software Announcements
The Company announces new product, service and software offerings at various times during the year. Significant announcements during fiscal year 2025 included the following:
First Quarter 2025:
• MacBook Pro
• Mac mini
• iMac
• iPad mini
Second Quarter 2025:
• iPhone 16e
• iPad Air
• iPad
• MacBook Air
• Mac Studio
Third Quarter 2025:
• iOS 26, macOS Tahoe 26, iPadOS 26, watchOS 26, visionOS 26 and tvOS 26
Fourth Quarter 2025:
• iPhone 17, iPhone Air, iPhone 17 Pro and iPhone 17 Pro Max
• Apple Watch Series 11, Apple Watch SE 3 and Apple Watch Ultra 3
• AirPods Pro 3
Fiscal Period
```

**Correct (Y/N):** ___   **Error type:** ___

## 7. `Johnson & Johnson` --has_product--> `ZYTIGA (JNJ)`

- **Chunk:** `JNJ_FY2025_ITEM1_0003` (+6 more)
- **Quote:** "ZYTIGA (abiraterone acetate), a treatment for patients with prostate cancer"
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "ZYTIGA" -> ZYTIGA (JNJ) [exact]

```
cell lung cancer; TALVEY (talquetamab-tgvs) a bispecific antibody for adults with relapsed or refractory multiple myeloma who have received at least four prior lines of therapy;
TECVAYLI (teclistamab-cqyv), a bispecific antibody for adults with relapsed or refractory multiple myeloma who have received at least four prior lines of therapy; ZYTIGA (abiraterone acetate), a treatment for patients with prostate cancer; REMICADE (infliximab), a treatment for a number of immune-mediated inflammatory diseases; SIMPONI (golimumab), a subcutaneous treatment for adults with moderate to severe rheumatoid arthritis, active psoriatic arthritis, active ankylosing spondylitis and moderately active to severely active ulcerative colitis; SIMPONI ARIA (golimumab), an intravenous treatment for adults with moderate to severe
```

**Correct (Y/N):** ___   **Error type:** ___

## 8. `Apple Inc.` --has_product--> `MacBook Pro 14-in.`

- **Chunk:** `AAPL_FY2024_ITEM7_0000`
- **Quote:** "Significant announcements during fiscal year 2024 included the following: First Quarter 2024: • MacBook Pro 14-in."
- **Name matching:** "Apple Inc." -> Apple Inc. [exact]; "MacBook Pro 14-in." -> MacBook Pro 14-in. [new]

```
etween 2023 and 2022 are not included, and can be found in “Management's Discussion and Analysis of Financial Condition and Results of Operations” in Part II, Item 7 of the Company's Annual Report on Form 10-K for the fiscal year ended September 30, 2023.
Product, Service and Software Announcements
The Company announces new product, service and software offerings at various times during the year. Significant announcements during fiscal year 2024 included the following:
First Quarter 2024:
• MacBook Pro 14-in.;
• MacBook Pro 16-in.; and
• iMac.
Second Quarter 2024:
• MacBook Air 13-in.; and
• MacBook Air 15-in.
Third Quarter 2024:
• iPad Air;
• iPad Pro;
• iOS 18, macOS Sequoia, iPadOS 18, watchOS 11, visionOS 2 and tvOS 18, updates to the Company's operating systems; and
• Apple Intelligence™, a personal intelligence system that uses generative models.
Fourth Quarter 2024:
• iPhone 16, iPhone 16 Plus,
```

**Correct (Y/N):** ___   **Error type:** ___

## 9. `Johnson & Johnson` --has_product--> `COVID-19 vaccine (JNJ)`

- **Chunk:** `JNJ_FY2024_ITEM7_0005`
- **Quote:** "In fiscal 2024, the impact of the Covid-19 Vaccine sales decline on the international operational sales was a negative 2.6%."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Covid-19 Vaccine" -> COVID-19 vaccine (JNJ) [exact]

```
l 2024, acquisitions and divestitures had a net positive impact of 0.7% on the U.S. operational sales growth. Sales by international companies were $38.5 billion in 2024 and $38.7 billion in 2023. This represents a decrease of 0.5% in 2024 and an increase of 1.9% in 2023. In fiscal 2024, acquisitions and divestitures had a net positive impact of 0.2% on the international operational sales growth. In fiscal 2024, the impact of the Covid-19 Vaccine sales decline on the international operational sales was a negative 2.6%.
The five-year compound annual growth rates for worldwide, U.S. and international sales were 5.4%, 6.8% and 3.8%, respectively. The ten-year compound annual growth rates for worldwide, U.S. and international sales were 4.0%, 5.4% and 2.5%, respectively.
```

**Correct (Y/N):** ___   **Error type:** ___

## 10. `Johnson & Johnson` --has_product--> `Innovative Medicine (JNJ)`

- **Chunk:** `JNJ_FY2025_ITEM1_0000` (+7 more)
- **Quote:** "The Company is organized into two business segments: Innovative Medicine and MedTech."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Innovative Medicine" -> Innovative Medicine (JNJ) [exact]

```
son's senior leadership team responsible for setting the strategy and priorities of the Company and driving accountability at all levels. Within the strategic parameters provided by the Executive Committee, senior management groups at U.S. and international operating companies are each responsible for their own strategic plans and the day-to-day operations of those companies.
Segments of business
The Company is organized into two business segments: Innovative Medicine and MedTech. Additional information required by this item is incorporated herein by reference to the narrative and tabular descriptions of segments and operating results under: Item 7. Management's discussion and analysis of results of operations and financial condition of this Report; and Note 17 Segments of business and geographic areas of the notes to consolidated financial statements included in Item 8 of
```

**Correct (Y/N):** ___   **Error type:** ___

## 11. `Apple Inc.` --has_product--> `Apple Watch SE 3`

- **Chunk:** `AAPL_FY2025_ITEM7_0001`
- **Quote:** "Apple Watch Series 11, Apple Watch SE 3 and Apple Watch Ultra 3"
- **Name matching:** "Apple Inc." -> Apple Inc. [exact]; "Apple Watch SE 3" -> Apple Watch SE 3 [new]

```
visionOS 26 and tvOS 26 Fourth Quarter 2025: • iPhone 17, iPhone Air, iPhone 17 Pro and iPhone 17 Pro Max • Apple Watch Series 11, Apple Watch SE 3 and Apple Watch Ultra 3 • AirPods Pro 3 Fiscal Period
The Company's fiscal year is the 52- or 53-week period that ends on the last Saturday of September. An additional week is included in the first fiscal quarter every five or six years to realign the Company's fiscal quarters with calendar quarters, which occurred in the first quarter of 2023. The Company's fiscal years 2025 and 2024 spanned 52 weeks each, whereas fisc
```

**Correct (Y/N):** ___   **Error type:** ___

## 12. `Johnson & Johnson` --has_product--> `Remicade (JNJ)`

- **Chunk:** `JNJ_FY2025_ITEM1_0003` (+6 more)
- **Quote:** "REMICADE (infliximab), a treatment for a number of immune-mediated inflammatory diseases"
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "REMICADE" -> Remicade (JNJ) [exact]

```
TALVEY (talquetamab-tgvs) a bispecific antibody for adults with relapsed or refractory multiple myeloma who have received at least four prior lines of therapy;
TECVAYLI (teclistamab-cqyv), a bispecific antibody for adults with relapsed or refractory multiple myeloma who have received at least four prior lines of therapy; ZYTIGA (abiraterone acetate), a treatment for patients with prostate cancer; REMICADE (infliximab), a treatment for a number of immune-mediated inflammatory diseases; SIMPONI (golimumab), a subcutaneous treatment for adults with moderate to severe rheumatoid arthritis, active psoriatic arthritis, active ankylosing spondylitis and moderately active to severely active ulcerative colitis; SIMPONI ARIA (golimumab), an intravenous treatment for adults with moderate to severe rheumatoid arthritis, active psoriatic arthritis and active ankylosing spondylitis and act
```

**Correct (Y/N):** ___   **Error type:** ___

## 13. `Lupin Limited` --competes_with--> `Xarelto (JNJ)`

- **Chunk:** `JNJ_FY2024_ITEM8_0183`
- **Quote:** "The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited."
- **Name matching:** "Lupin Limited" -> Lupin Limited [new]; "XARELTO" -> Xarelto (JNJ) [exact]

```
its to challenge the applicable patents. XARELTO
Beginning in March 2021, Janssen Pharmaceuticals, Inc.; Bayer Pharma AG; Bayer AG; and Bayer Intellectual Property GmbH filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of XARELTO before expiration of certain Orange Book Listed Patents. The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited. In October 2024, the Company entered into a confidential settlement agreement with Auson Pharmaceuticals Inc. and Shanghai Auson Pharmaceuticals Co., Ltd. and the case was dismissed.
```

**Correct (Y/N):** ___   **Error type:** ___

## 14. `Cipla Ltd.` --competes_with--> `Xarelto (JNJ)`

- **Chunk:** `JNJ_FY2024_ITEM8_0183`
- **Quote:** "The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited."
- **Name matching:** "Cipla Ltd." -> Cipla Ltd. [new]; "XARELTO" -> Xarelto (JNJ) [exact]

```
its to challenge the applicable patents. XARELTO
Beginning in March 2021, Janssen Pharmaceuticals, Inc.; Bayer Pharma AG; Bayer AG; and Bayer Intellectual Property GmbH filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of XARELTO before expiration of certain Orange Book Listed Patents. The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited. In October 2024, the Company entered into a confidential settlement agreement with Auson Pharmaceuticals Inc. and Shanghai Auson Pharmaceuticals Co., Ltd. and the case was dismissed.
```

**Correct (Y/N):** ___   **Error type:** ___

## 15. `Impella` --competes_with--> `Maquet Cardiovascular LLC`

- **Chunk:** `JNJ_FY2025_ITEM8_0185`
- **Quote:** "In March 2016, Abiomed, Inc. filed a declaratory judgment action against Maquet Cardiovascular LLC (Maquet) in the U.S. District Court for the District of Massachusetts seeking a declaration that certain Impella products do not infringe Maquet patents"
- **Name matching:** "Impella" -> Impella [new]; "Maquet Cardiovascular LLC" -> Maquet Cardiovascular LLC [new]

```
Biotech Belgium BV. alleging that the manufacture and sale of CARVYKTI infringes EU Patent No. 3 689 383. In the suit, 2seventy bio, Inc. seeks damages and an injunction. MedTech
In March 2016, Abiomed, Inc. filed a declaratory judgment action against Maquet Cardiovascular LLC (Maquet) in the U.S. District Court for the District of Massachusetts seeking a declaration that certain Impella products do not infringe Maquet patents, including U.S. Patent Nos. 7,022,100 ('100 patent); 8,888,728; and 9,327,068. Maquet counterclaimed for infringement of those patents against Abiomed, Inc., Abiomed Europe GmbH, and Abiomed R&D, Inc. (collectively, Abiomed), and later added claims for infringement of U.S. Patent Nos. 9,545,468; 9,561,314; and 9,597,437. After claim construction, Maquet alleged infringement of only the '100 paten
```

**Correct (Y/N):** ___   **Error type:** ___

## 16. `Mankind Pharma Limited` --competes_with--> `Xarelto (JNJ)`

- **Chunk:** `JNJ_FY2024_ITEM8_0183`
- **Quote:** "The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited."
- **Name matching:** "Mankind Pharma Limited" -> Mankind Pharma Limited [new]; "XARELTO" -> Xarelto (JNJ) [exact]

```
its to challenge the applicable patents. XARELTO
Beginning in March 2021, Janssen Pharmaceuticals, Inc.; Bayer Pharma AG; Bayer AG; and Bayer Intellectual Property GmbH filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of XARELTO before expiration of certain Orange Book Listed Patents. The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pharmaceuticals Inc.; Mylan Inc.; Mankind Pharma Limited; Apotex Inc.; Apotex Corp.; Auson Pharmaceuticals Inc.; Shanghai Auson Pharmaceuticals Co. Ltd.; Cipla Ltd.; Cipla USA Inc.; InvaGen Pharmaceuticals, Inc.; Prinston Pharmaceuticals, Inc.; Ascent Pharmaceuticals, Inc.; and Hetero Labs Limited. In October 2024, the Company entered into a confidential settlement agreement with Auson Pharmaceuticals Inc. and Shanghai Auson Pharmaceuticals Co., Ltd. and the case was dismissed.
```

**Correct (Y/N):** ___   **Error type:** ___

## 17. `Johnson & Johnson` --acquired--> `Shockwave Medical, Inc.`

- **Chunk:** `JNJ_FY2025_ITEM8_0139` (+6 more)
- **Quote:** "The fiscal year 2024 acquisitions primarily included; Ambrx Biopharma, Inc., Shockwave Medical Inc., and Proteologix, Inc."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Shockwave Medical Inc." -> Shockwave Medical, Inc. [exact]

```
(depending on indication being studied), respectively.
(2) Goodwill is primarily attributable to intangible assets that did not qualify for separate recognition and future projects or products currently unidentified. Goodwill is not expected to be deductible for tax purposes.
2024 Transactions
During the fiscal year 2024, certain businesses were acquired for $ 15.1 billion, net of cash acquired. The fiscal year 2024 acquisitions primarily included; Ambrx Biopharma, Inc., Shockwave Medical Inc., and Proteologix, Inc. The remaining acquisitions were not material.
```

**Correct (Y/N):** ___   **Error type:** ___

## 18. `Johnson & Johnson` --acquired--> `ABIOMED, Inc.`

- **Chunk:** `JNJ_FY2024_ITEM8_0138` (+1 more)
- **Quote:** "The fiscal year 2022 acquisitions primarily included Abiomed, Inc. (Abiomed)."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Abiomed, Inc." -> ABIOMED, Inc. [exact]

```
xpected to arise from the business acquisition and is not expected to be deductible for tax purposes. Acquisition related costs before tax for the fiscal year 2024 were not material.
During the fiscal year 2023, the Company did not make any acquisitions that qualified as a business combination.
During the fiscal year 2022, certain businesses were acquired for $ 17.7 billion, net of cash acquired. The fiscal year 2022 acquisitions primarily included Abiomed, Inc. (Abiomed). The remaining acquisitions were not material.
```

**Correct (Y/N):** ___   **Error type:** ___

## 19. `Ethicon, Inc.` --acquired--> `Auris Health, Inc.`

- **Chunk:** `JNJ_FY2025_ITEM8_0192` (+1 more)
- **Quote:** "In connection with Ethicon's acquisition of Auris in 2019."
- **Name matching:** "Ethicon Inc." -> Ethicon, Inc. [exact]; "Auris Health Inc." -> Auris Health, Inc. [exact]

```
fiduciary duty claims. Plaintiffs voluntarily withdrew their remaining claim, and the court entered final judgment in defendants' favor in January 2026. Plaintiffs have filed a notice of appeal to the United States Court of Appeals for the Third Circuit. MedTech
In October 2020, Fortis Advisors LLC (Fortis), in its capacity as representative of the former stockholders of Auris Health Inc. (Auris), filed a complaint against the Company, Ethicon Inc., and certain named officers and employees (collectively, Ethicon) in the Court of Chancery of the State of Delaware. The complaint alleges breach of contract, fraud, and other causes of action against Ethicon in connection with Ethicon's acquisition of Auris in 2019. The complaint seeks damages and other relief. In December 2021, the court granted in part and denied in part defendants' motion to dismiss certain causes of action. All claims against the individual defendants were dismissed. Trial occurred in January 2024. In September 2024, the court found liability with respect to certain claims and no liability with respect to other claims. In January 2026, the Delaware Supreme Court reversed in part and affirmed in part the Chancery Court's decision, including a $ 0.8 billion judgment against the Company that was accrued in the fiscal fourth quarter of 2025 and subsequently paid in January 2026.
```

**Correct (Y/N):** ___   **Error type:** ___

## 20. `Janssen Pharmaceuticals, Inc.` --partners_with--> `Bayer Pharma AG`

- **Chunk:** `JNJ_FY2024_ITEM8_0183`
- **Quote:** "Beginning in March 2021, Janssen Pharmaceuticals, Inc.; Bayer Pharma AG; Bayer AG; and Bayer Intellectual Property GmbH filed patent infringement lawsuits in United States district courts against generic manufacturers"
- **Name matching:** "Janssen Pharmaceuticals, Inc." -> Janssen Pharmaceuticals, Inc. [exact]; "Bayer Pharma AG" -> Bayer Pharma AG [new]

```
process with the United States Patent and Trademark Office (USPTO), created under the 2011 America Invents Act, is also being used at times by generic companies in conjunction with ANDAs and lawsuits to challenge the applicable patents. XARELTO
Beginning in March 2021, Janssen Pharmaceuticals, Inc.; Bayer Pharma AG; Bayer AG; and Bayer Intellectual Property GmbH filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of XARELTO before expiration of certain Orange Book Listed Patents. The following entities are named defendants: Dr. Reddy's Laboratories, Inc.; Dr. Reddy's Laboratories, Ltd.; Lupin Limited; Lupin Pharmaceuticals, Inc.; Taro Pharmaceutical Industries Ltd.; Taro Pharmaceuticals U.S.A., Inc.; Teva Pharmaceuticals USA, Inc.; Mylan Pha
```

**Correct (Y/N):** ___   **Error type:** ___

## 21. `Janssen Products, LP` --partners_with--> `Gilead Sciences Ireland UC`

- **Chunk:** `JNJ_FY2024_ITEM8_0188`
- **Quote:** "Beginning in November 2021, Janssen Products, L.P., Janssen Sciences Ireland Unlimited Company, Gilead Sciences, Inc. and Gilead Sciences Ireland UC filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of SYMTUZA before expiration of certain Orange Book Listed Patents."
- **Name matching:** "Janssen Products, L.P." -> Janssen Products, LP [exact]; "Gilead Sciences Ireland UC" -> Gilead Sciences Ireland UC [new]

```
proposed generic product infringes the asserted patent and that the patent is not invalid. Mylan has appealed the decision. Oral argument before the Court of Appeals for the Federal Circuit was held in February 2025. SYMTUZA
Beginning in November 2021, Janssen Products, L.P., Janssen Sciences Ireland Unlimited Company, Gilead Sciences, Inc. and Gilead Sciences Ireland UC filed patent infringement lawsuits in United States district courts against generic manufacturers who have filed ANDAs seeking approval to market generic versions of SYMTUZA before expiration of certain Orange Book Listed Patents. The following entities are named defendants: Lupin Limited; Lupin Pharmaceuticals, Inc.; MSN Laboratories Private Ltd.; MSN Life Sciences Private Ltd.; MSN Pharmaceuticals Inc.; Apotex Inc.; and Apotex Corp. The following U.S. patents are included in one or more cases: 10,039,718 and 10,786,518. A trial is scheduled to begin in February 2025.
ERLEADA
```

**Correct (Y/N):** ___   **Error type:** ___

## 22. `Johnson & Johnson` --partners_with--> `JPI`

- **Chunk:** `JNJ_FY2025_ITEM8_0160`
- **Quote:** "To date, the Company and JPI have litigated two of the cases to judgment and have prevailed in both, either at trial or on appeal."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "JPI" -> JPI [new]

```
Abstinence Syndrome (NAS); hospitals; and health insurers/payors. To date, the Company and JPI have litigated two of the cases to judgment and have prevailed in both, either at trial or on appeal.
In July 2021, the Company announced finalization of an agreement to settle the state and subdivision claims for up to $ 5.0 billion. Approximately 80 % of the all-in settlement was paid by the end of fiscal year 2025. A few government entities opted out of the settlement. In September 2024, the Company reached an agreement to resolve the hospital cases.
The Company and JPI continue to defend the
```

**Correct (Y/N):** ___   **Error type:** ___

## 23. `Ethicon, Inc.` --subsidiary_of--> `Johnson & Johnson`

- **Chunk:** `JNJ_FY2024_ITEM8_0174`
- **Quote:** "claims for personal injury have been made against Ethicon, Inc. (Ethicon) and the Company alleging personal injury arising out of the use of this hernia mesh device."
- **Name matching:** "Ethicon, Inc." -> Ethicon, Inc. [exact]; "Johnson & Johnson" -> Johnson & Johnson [exact]

```
Australia, Canada and South Africa. The vast majority of these actions are now resolved. The Company has established accruals with respect to product liability litigation associated with Ethicon's pelvic mesh products. Ethicon Physiomesh
Following a June 2016 worldwide market withdrawal of Ethicon Physiomesh Flexible Composite Mesh (Physiomesh), claims for personal injury have been made against Ethicon, Inc. (Ethicon) and the Company alleging personal injury arising out of the use of this hernia mesh device. Cases filed in federal courts in the United States have been organized as a multi-district litigation (MDL) in the United States District Court for the Northern District of Georgia. A multi-county litigation (MCL) also has been formed in New Jersey state court and assigned to Atlantic County for cases pending in New Jersey. In addition to the matters in the MDL and MCL, there are additional lawsu
```

**Correct (Y/N):** ___   **Error type:** ___

## 24. `Aragon Pharmaceuticals, Inc.` --subsidiary_of--> `Johnson & Johnson`

- **Chunk:** `JNJ_FY2025_ITEM8_0179` (+1 more)
- **Quote:** "Aragon Pharmaceuticals, Inc., Janssen Inc., (collectively, Janssen Inc.)"
- **Name matching:** "Aragon Pharmaceuticals, Inc." -> Aragon Pharmaceuticals, Inc. [exact]; "Johnson & Johnson" -> Johnson & Johnson [exact]

```
Supreme Court dismissed the Apotex case. In September 2024, the Supreme Court granted Pharmascience's motion to appeal the Federal Court's decision that the 2,655,335 Patent is not invalid. ERLEADA
In January 2025, Aragon Pharmaceuticals, Inc., Janssen Inc., (collectively, Janssen Inc.) and Sloan-Kettering Institute for Cancer Research (SKI) initiated Statements of Claims under Section 6 of the Patented Medicines (Notice of Compliance) Regulations against Sandoz Canada Inc. (Sandoz) in response to Sandoz's filing of an ANDS seeking approval to market a generic version of ERLEADA before the expiration of CA Patent Nos. 3,008,345 (the '345 patent), 2,875,767 (the '767 patent), 2,8
```

**Correct (Y/N):** ___   **Error type:** ___

## 25. `Janssen Biotech, Inc.` --licensed_from--> `Genmab A/S`

- **Chunk:** `JNJ_FY2025_ITEM1_0011` (+1 more)
- **Quote:** "Genmab A/S owns two patent families related to DARZALEX, and Janssen Biotech, Inc. (a wholly-owned subsidiary of the Company) has an exclusive license to those patent families."
- **Name matching:** "Janssen Biotech, Inc." -> Janssen Biotech, Inc. [exact]; "Genmab A/S" -> Genmab A/S [new]

```
and other intellectual property are described in Note 19 Legal proceedings—Intellectual property of the Notes to Consolidated Financial Statements included in Item 8 of this Report.
Sales of the Company's largest product, collectively DARZALEX (daratumumab) and DARZALEX FASPRO (daratumumab and hyaluronidase-fihj), accounted for approximately 15.0% of the Company's total revenues for fiscal 2025. Genmab A/S owns two patent families related to DARZALEX, and Janssen Biotech, Inc. (a wholly-owned subsidiary of the Company) has an exclusive license to those patent families. Royalty rate ranges from 12% to 20% of total DARZALEX net sales. For the fiscal 2025 and 2024, royalty amounts to Genmab were approximately $2.4 billion and $2.0 billion, respectively. The two patent families both expire in the United States in 2029, and in Europe, compound/use patent protection in select countries extends to 2031/2032. Janssen Biotech, Inc. owns separate patent portfolios relate
```

**Correct (Y/N):** ___   **Error type:** ___

## 26. `Microsoft Corporation` --licensed_from--> `Inflection AI, Inc.`

- **Chunk:** `MSFT_FY2025_ITEM8_0030`
- **Quote:** "In March 2024, we entered into an agreement with Inflection AI, Inc. (“Inflection”), pursuant to which we obtained a non-exclusive license to Inflection's intellectual property."
- **Name matching:** "Microsoft Corporation" -> Microsoft Corporation [exact]; "Inflection AI, Inc." -> Inflection AI, Inc. [new]

```
the estimated useful life in proportion to the economic benefits received. We evaluate the recoverability of intangible assets periodically by taking into account events or circumstances that may warrant revised estimates of useful lives or that indicate the asset may be impaired. Related Party Transactions
In March 2024, we entered into an agreement with Inflection AI, Inc. (“Inflection”), pursuant to which we obtained a non-exclusive license to Inflection's intellectual property. Reid Hoffman, a member of our Board of Directors, is a co-founder of and serves on the board of directors of Inflection. As of the date of the agreement with Inflection, Reprogrammed Interchange LLC (“Reprogrammed”) and entities affiliated with Greylock Ventures (“Greylock”) each held less than a 10 % equity interest in Inflection. Mr. Hoffman may be deemed to beneficially own the shares held by
```

**Correct (Y/N):** ___   **Error type:** ___

## 27. `Johnson & Johnson` --invests_in--> `Idorsia`

- **Chunk:** `JNJ_FY2024_ITEM7_0031`
- **Quote:** "The fiscal year 2023 includes $0.4 billion related to the unfavorable change in the fair value of the remaining stake in Kenvue and $0.4 billion related to the partial impairment of Idorsia convertible debt and the change in the fair value of the Idorsia equity securities held."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Idorsia" -> Idorsia [new]

```
(2) The fiscal year 2024 is primarily related to the acquisition of Shockwave. The fiscal year 2023 is primarily related to the impairment of Ponvory and one-time integration costs related to the acquisition of Abiomed.
(3) The fiscal year 2024 includes the loss of $0.4 billion on the completion of the debt for equity exchange of the retained stake in Kenvue. The fiscal year 2023 includes $0.4 billion related to the unfavorable change in the fair value of the remaining stake in Kenvue and $0.4 billion related to the partial impairment of Idorsia convertible debt and the change in the fair value of the Idorsia equity securities held.
```

**Correct (Y/N):** ___   **Error type:** ___

## 28. `Microsoft Corporation` --invests_in--> `OpenAI`

- **Chunk:** `MSFT_FY2026_ITEM7_0002` (+7 more)
- **Quote:** "Microsoft is a major investor in OpenAI and will continue to receive revenue-sharing payments."
- **Name matching:** "Microsoft Corporation" -> Microsoft Corporation [exact]; "OpenAI" -> OpenAI [new]

```
to identify and address the changing demands of customers and users, industry trends, and competitive forces.
We have a long-term strategic partnership with OpenAI which was originally established in 2019. In October 2025 and April 2026, we extended this partnership and continue to build on our shared vision to advance artificial intelligence responsibly and make its benefits broadly accessible. Microsoft is a major investor in OpenAI and will continue to receive revenue-sharing payments. We hold rights to OpenAI's intellectual property, including models and infrastructure, for integration into our products.
PART II
Economic Conditions, Challenges, and Risks
```

**Correct (Y/N):** ___   **Error type:** ___

## 29. `Johnson & Johnson` --supplies_to--> `Kenvue`

- **Chunk:** `JNJ_FY2025_ITEM8_0205` (+2 more)
- **Quote:** "Additionally, Johnson & Johnson and Kenvue entered into TMAs pursuant to which Johnson & Johnson will manufacture and supply to Kenvue certain products and, similarly, Kenvue will manufacture and supply to Johnson & Johnson certain products."
- **Name matching:** "Johnson & Johnson" -> Johnson & Johnson [exact]; "Kenvue" -> Kenvue [new]

```
cturing agreements (TMAs), trademark agreements, intellectual property agreements, an employee matters agreement, and a tax matters agreement. Under the TSAs, Johnson & Johnson will provide Kenvue various services and, similarly, Kenvue will provide Johnson & Johnson various services. The provision of the majority of services under the TSAs generally terminated 24 months following the Kenvue IPO. Additionally, Johnson & Johnson and Kenvue entered into TMAs pursuant to which Johnson & Johnson will manufacture and supply to Kenvue certain products and, similarly, Kenvue will manufacture and supply to Johnson & Johnson certain products. The terms of the TMAs range in initial duration from 3 months to 5 years.
```

**Correct (Y/N):** ___   **Error type:** ___

## 30. `Kenvue` --manufactures--> `Johnson & Johnson`

- **Chunk:** `JNJ_FY2024_ITEM8_0211` (+1 more)
- **Quote:** "Kenvue will manufacture and supply to Johnson & Johnson certain products."
- **Name matching:** "Kenvue" -> Kenvue [new]; "Johnson & Johnson" -> Johnson & Johnson [exact]

```
son & Johnson will provide Kenvue various services and, similarly, Kenvue will provide Johnson & Johnson various services. The provision of services under the TSAs generally will terminate within 24 months following the Kenvue IPO. Additionally, Johnson & Johnson and Kenvue entered into TMAs pursuant to which Johnson & Johnson will manufacture and supply to Kenvue certain products and, similarly, Kenvue will manufacture and supply to Johnson & Johnson certain products. The terms of the TMAs range in initial duration from 3 months to 5 years.
```

**Correct (Y/N):** ___   **Error type:** ___
