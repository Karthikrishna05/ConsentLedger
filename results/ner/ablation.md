# NER ablation (mean ± std over seeds) — E1 transfer / E2 domain-adapted

| backbone | cond | seeds | dev entity-macroF1 | dev token-F1 | AA-test macroF1 | AA-test token-F1 |
|---|---|---|---|---|---|---|
| nlpaueb/legal-bert-base-uncased | E2-sequential | 3 | 0.6422±0.0391 | 0.7260±0.0228 | 0.4761±0.0300 | 0.5859 |
| law-ai/InLegalBERT | E2-sequential | 3 | 0.5429±0.0450 | 0.6702±0.0230 | 0.4233±0.0412 | 0.5404 |
| bert-base-uncased | E2-sequential | 3 | 0.5489±0.0449 | 0.6790±0.0201 | 0.4059±0.0168 | 0.5206 |
| bert-base-uncased | E2-joint | 3 | 0.4694±0.0509 | 0.5555±0.0409 | 0.2539±0.0156 | 0.3636 |
| nlpaueb/legal-bert-base-uncased | E2-joint | 3 | 0.4797±0.0260 | 0.5754±0.0117 | 0.2494±0.0067 | 0.3865 |
| law-ai/InLegalBERT | E2-joint | 3 | 0.4111±0.0668 | 0.5038±0.0591 | 0.2179±0.0375 | 0.3626 |
| bert-base-uncased | E1 | 3 | 0.3816±0.0025 | 0.5262±0.0014 | 0.1287±0.0071 | 0.2313 |
| nlpaueb/legal-bert-base-uncased | E1 | 3 | 0.3996±0.0059 | 0.5220±0.0083 | 0.1272±0.0077 | 0.2357 |
| law-ai/InLegalBERT | E1 | 3 | 0.3862±0.0028 | 0.5133±0.0080 | 0.1184±0.0029 | 0.2326 |

_dev = each run's own dev file: OPP-115 dev for E1, the AA dev documents for E2 - NOT comparable across conditions. AA-test columns are '-' until `evaluate.py --out` is run on the annotated AA test set. Entity-macroF1 = strict exact-match; token-F1 = token-level (fairer for long spans)._