# Annotation agreement - 23 documents

- Documents below the 0.6 gate: **22/23**
- Total spans: A=1839, B=952

## Where the disagreement lives (all docs)

| bucket | n | meaning |
|---|---|---|
| EXACT | 292 | agreed exactly |
| BOUNDARY | 108 | same label, different edges -> span-rule fix |
| LABEL | 7 | same text, different label -> ontology fix |
| A_ONLY | 1432 | B missed, or A over-marked |
| B_ONLY | 541 | A missed, or B over-marked |

## Documents, worst first

| doc | kappa | entF1 | A | B | EXACT | BOUND | LABEL | A_ONLY | B_ONLY | dominant |
|---|---|---|---|---|---|---|---|---|---|---|
| 22_setu_aa_charter | -0.007 | 0.000 | 8 | 38 | 0 | 0 | 0 | 8 | 37 | B_ONLY |
| 19_saafe_privacy | 0.008 | 0.000 | 131 | 9 | 0 | 0 | 3 | 128 | 6 | A_ONLY |
| 20_scoremeaa_charter | 0.028 | 0.056 | 4 | 32 | 1 | 0 | 0 | 3 | 31 | B_ONLY |
| 21_nadl_terms | 0.032 | 0.083 | 12 | 38 | 2 | 0 | 0 | 10 | 36 | B_ONLY |
| 24_credbuddha_terms | 0.059 | 0.031 | 182 | 10 | 3 | 1 | 1 | 177 | 5 | A_ONLY |
| 28_indifi_capital_privacy | 0.146 | 0.082 | 438 | 50 | 20 | 12 | 0 | 406 | 18 | A_ONLY |
| 01_setu_aa_terms | 0.161 | 0.158 | 48 | 29 | 5 | 2 | 0 | 41 | 22 | A_ONLY |
| 12_scoremeaa_terms | 0.188 | 0.256 | 10 | 29 | 4 | 2 | 0 | 4 | 23 | B_ONLY |
| 03_oms_aa_terms | 0.246 | 0.320 | 45 | 57 | 14 | 2 | 1 | 28 | 39 | B_ONLY |
| 10_perfios_terms | 0.263 | 0.473 | 27 | 31 | 11 | 3 | 0 | 13 | 17 | B_ONLY |
| 02_digio_terms | 0.271 | 0.242 | 48 | 43 | 10 | 3 | 0 | 35 | 30 | A_ONLY |
| 04_pb_fintech_aa_terms | 0.275 | 0.265 | 44 | 39 | 8 | 4 | 1 | 31 | 26 | A_ONLY |
| 16_oms_aa_privacy | 0.281 | 0.156 | 35 | 42 | 6 | 8 | 0 | 21 | 28 | B_ONLY |
| 23_upmint_aa_tos | 0.317 | 0.436 | 32 | 48 | 16 | 1 | 0 | 15 | 30 | B_ONLY |
| 05_onemoney_terms | 0.328 | 0.312 | 36 | 41 | 11 | 2 | 1 | 22 | 27 | B_ONLY |
| 09_saafe_terms | 0.334 | 0.154 | 35 | 30 | 5 | 7 | 0 | 23 | 18 | A_ONLY |
| 08_pennydrop_terms | 0.378 | 0.279 | 198 | 67 | 35 | 15 | 0 | 148 | 17 | A_ONLY |
| 25_the_financiali_privacy | 0.393 | 0.332 | 120 | 62 | 30 | 5 | 0 | 85 | 27 | A_ONLY |
| 06_setu_aa_privacy | 0.413 | 0.343 | 154 | 63 | 32 | 11 | 0 | 111 | 19 | A_ONLY |
| 29_icici_home_fin_terms | 0.451 | 0.404 | 73 | 41 | 23 | 6 | 0 | 44 | 12 | A_ONLY |
| 17_pb_fintech_aa_privacy | 0.483 | 0.345 | 129 | 68 | 33 | 17 | 0 | 79 | 18 | A_ONLY |
| 26_zerodha_tos | 0.516 | 0.105 | 8 | 32 | 2 | 6 | 0 | 0 | 24 | B_ONLY |
| 14_nadl_charter | 0.625 | 0.575 | 22 | 53 | 21 | 1 | 0 | 0 | 31 | B_ONLY |

Per-document detail (actual phrases): `results\annotation\agreement\docs/<doc_id>.md`