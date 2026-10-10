# Annotation agreement - 23 documents

- Documents below the 0.6 gate: **21/23**
- Total spans: A=1365, B=1337

## Where the disagreement lives (all docs)

| bucket | n | meaning |
|---|---|---|
| EXACT | 537 | agreed exactly |
| BOUNDARY | 93 | same label, different edges -> span-rule fix |
| LABEL | 26 | same text, different label -> ontology fix |
| A_ONLY | 709 | B missed, or A over-marked |
| B_ONLY | 681 | A missed, or B over-marked |

## Documents, worst first

| doc | kappa | entF1 | A | B | EXACT | BOUND | LABEL | A_ONLY | B_ONLY | dominant |
|---|---|---|---|---|---|---|---|---|---|---|
| 22_setu_aa_charter | 0.025 | 0.091 | 7 | 15 | 1 | 0 | 0 | 6 | 14 | B_ONLY |
| 20_scoremeaa_charter | 0.068 | 0.130 | 3 | 43 | 3 | 0 | 0 | 0 | 40 | B_ONLY |
| 26_zerodha_tos | 0.108 | 0.143 | 17 | 25 | 3 | 2 | 0 | 12 | 20 | B_ONLY |
| 21_nadl_terms | 0.131 | 0.115 | 6 | 46 | 3 | 0 | 0 | 3 | 43 | B_ONLY |
| 12_scoremeaa_terms | 0.251 | 0.300 | 10 | 30 | 5 | 2 | 0 | 3 | 23 | B_ONLY |
| 28_indifi_capital_privacy | 0.317 | 0.277 | 247 | 138 | 55 | 14 | 1 | 177 | 68 | A_ONLY |
| 19_saafe_privacy | 0.334 | 0.330 | 63 | 52 | 18 | 2 | 2 | 41 | 30 | A_ONLY |
| 24_credbuddha_terms | 0.370 | 0.346 | 267 | 128 | 69 | 13 | 11 | 174 | 35 | A_ONLY |
| 04_pb_fintech_aa_terms | 0.396 | 0.400 | 24 | 36 | 9 | 4 | 0 | 11 | 23 | B_ONLY |
| 10_perfios_terms | 0.404 | 0.582 | 29 | 29 | 14 | 2 | 0 | 13 | 13 | A_ONLY |
| 23_upmint_aa_tos | 0.408 | 0.400 | 30 | 35 | 13 | 3 | 1 | 13 | 18 | B_ONLY |
| 16_oms_aa_privacy | 0.428 | 0.312 | 23 | 42 | 10 | 4 | 0 | 9 | 28 | B_ONLY |
| 17_pb_fintech_aa_privacy | 0.452 | 0.465 | 53 | 78 | 30 | 3 | 1 | 19 | 44 | B_ONLY |
| 05_onemoney_terms | 0.487 | 0.493 | 26 | 43 | 16 | 1 | 0 | 9 | 26 | B_ONLY |
| 08_pennydrop_terms | 0.488 | 0.392 | 177 | 137 | 60 | 9 | 6 | 102 | 62 | A_ONLY |
| 29_icici_home_fin_terms | 0.495 | 0.495 | 54 | 55 | 27 | 6 | 0 | 21 | 22 | B_ONLY |
| 09_saafe_terms | 0.496 | 0.375 | 24 | 42 | 13 | 3 | 0 | 8 | 26 | B_ONLY |
| 01_setu_aa_terms | 0.537 | 0.528 | 36 | 36 | 19 | 1 | 2 | 14 | 14 | A_ONLY |
| 03_oms_aa_terms | 0.564 | 0.593 | 35 | 56 | 25 | 2 | 0 | 8 | 29 | B_ONLY |
| 06_setu_aa_privacy | 0.564 | 0.570 | 78 | 73 | 41 | 5 | 0 | 32 | 27 | A_ONLY |
| 02_digio_terms | 0.581 | 0.561 | 26 | 31 | 16 | 0 | 0 | 10 | 15 | B_ONLY |
| 25_the_financiali_privacy | 0.628 | 0.574 | 103 | 121 | 65 | 12 | 2 | 24 | 42 | B_ONLY |
| 14_nadl_charter | 0.673 | 0.522 | 27 | 46 | 22 | 5 | 0 | 0 | 19 | B_ONLY |

Per-document detail (actual phrases): `results\annotation\round5\docs/<doc_id>.md`