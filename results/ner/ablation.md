# NER ablation (mean ± std over seeds) — E1 transfer / E2 domain-adapted

| backbone | cond | seeds | dev entity-macroF1 | dev token-F1 | AA-test macroF1 | AA-test token-F1 |
|---|---|---|---|---|---|---|
| nlpaueb/legal-bert-base-uncased | E1 | 3 | 0.3996±0.0059 | 0.5220±0.0083 | - | - |
| law-ai/InLegalBERT | E1 | 3 | 0.3862±0.0028 | 0.5133±0.0080 | - | - |
| bert-base-uncased | E1 | 3 | 0.3816±0.0025 | 0.5262±0.0014 | - | - |

_dev = OPP-115 dev. AA-test columns are '-' until `evaluate.py --out` is run on the annotated AA test set. Entity-macroF1 = strict exact-match; token-F1 = token-level (fairer for long spans)._