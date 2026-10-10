# E1 / E2 on the AA test set

826 gold entities, 9 documents in 8 groups. Cells: mean ± std over seeds, then the 95% interval from a bootstrap over document groups (5000 resamples). Exact = same label and same boundaries; relaxed = same label, overlapping.

| backbone | condition | runs | exact micro-F1 | exact macro-F1 | relaxed micro-F1 | mean of group F1 | exact, definition mismatch set aside |
|---|---|---|---|---|---|---|---|
| bert-base-uncased | E1 | 3 | 0.130 ± 0.008 [0.106, 0.162] | 0.129 ± 0.007 [0.101, 0.168] | 0.301 ± 0.008 [0.263, 0.331] | 0.116 | 0.144 |
| bert-base-uncased | E2-joint | 3 | 0.266 ± 0.016 [0.222, 0.343] | 0.254 ± 0.016 [0.196, 0.349] | 0.444 ± 0.034 [0.402, 0.504] | 0.242 | 0.277 |
| bert-base-uncased | E2-sequential | 3 | 0.412 ± 0.016 [0.331, 0.463] | 0.406 ± 0.017 [0.311, 0.469] | 0.583 ± 0.023 [0.506, 0.626] | 0.351 | 0.418 |
| law-ai/InLegalBERT | E1 | 3 | 0.119 ± 0.003 [0.091, 0.153] | 0.118 ± 0.003 [0.089, 0.156] | 0.291 ± 0.013 [0.246, 0.322] | 0.104 | 0.131 |
| law-ai/InLegalBERT | E2-joint | 3 | 0.225 ± 0.043 [0.176, 0.315] | 0.218 ± 0.037 [0.160, 0.319] | 0.433 ± 0.021 [0.385, 0.503] | 0.210 | 0.236 |
| law-ai/InLegalBERT | E2-sequential | 3 | 0.427 ± 0.038 [0.327, 0.490] | 0.423 ± 0.041 [0.312, 0.490] | 0.597 ± 0.024 [0.517, 0.642] | 0.365 | 0.438 |
| nlpaueb/legal-bert-base-uncased | E1 | 3 | 0.126 ± 0.007 [0.099, 0.158] | 0.127 ± 0.008 [0.098, 0.161] | 0.286 ± 0.013 [0.247, 0.312] | 0.110 | 0.139 |
| nlpaueb/legal-bert-base-uncased | E2-joint | 3 | 0.266 ± 0.008 [0.229, 0.336] | 0.249 ± 0.007 [0.203, 0.332] | 0.450 ± 0.008 [0.422, 0.494] | 0.254 | 0.279 |
| nlpaueb/legal-bert-base-uncased | E2-sequential | 3 | 0.479 ± 0.026 [0.399, 0.529] | 0.476 ± 0.030 [0.372, 0.530] | 0.637 ± 0.019 [0.584, 0.672] | 0.411 | 0.487 |
| all three | E1 | 9 | 0.125 ± 0.007 [0.101, 0.156] | 0.125 ± 0.007 [0.099, 0.159] | 0.293 ± 0.012 [0.253, 0.319] | 0.110 | 0.138 |
| all three | E2-joint | 9 | 0.252 ± 0.031 [0.209, 0.331] | 0.240 ± 0.027 [0.186, 0.334] | 0.442 ± 0.022 [0.405, 0.500] | 0.235 | 0.264 |
| all three | E2-sequential | 9 | 0.439 ± 0.039 [0.352, 0.494] | 0.435 ± 0.041 [0.332, 0.495] | 0.606 ± 0.031 [0.539, 0.646] | 0.375 | 0.447 |

## Paired differences (the same resamples of the groups for both sides)

| comparison | backbone | exact micro-F1 difference [95% CI] | relaxed micro-F1 difference [95% CI] | verdict (exact) |
|---|---|---|---|---|
| E2-sequential minus E1 | all three | +0.314 [+0.241, +0.358] | +0.313 [+0.253, +0.354] | difference |
| E2-sequential minus E1 | bert-base-uncased | +0.282 [+0.212, +0.322] | +0.282 [+0.224, +0.316] | difference |
| E2-sequential minus E1 | law-ai/InLegalBERT | +0.308 [+0.226, +0.352] | +0.306 [+0.235, +0.350] | difference |
| E2-sequential minus E1 | nlpaueb/legal-bert-base-uncased | +0.353 [+0.271, +0.402] | +0.351 [+0.287, +0.404] | difference |
| E2-joint minus E1 | all three | +0.127 [+0.101, +0.179] | +0.150 [+0.120, +0.200] | difference |
| E2-joint minus E1 | bert-base-uncased | +0.136 [+0.108, +0.185] | +0.143 [+0.115, +0.188] | difference |
| E2-joint minus E1 | law-ai/InLegalBERT | +0.106 [+0.073, +0.168] | +0.142 [+0.104, +0.206] | difference |
| E2-joint minus E1 | nlpaueb/legal-bert-base-uncased | +0.140 [+0.114, +0.187] | +0.164 [+0.135, +0.214] | difference |
| E2-sequential minus E2-joint | all three | +0.187 [+0.126, +0.234] | +0.163 [+0.112, +0.207] | difference |
| E2-sequential minus E2-joint | bert-base-uncased | +0.146 [+0.093, +0.194] | +0.139 [+0.091, +0.179] | difference |
| E2-sequential minus E2-joint | law-ai/InLegalBERT | +0.202 [+0.131, +0.251] | +0.164 [+0.101, +0.215] | difference |
| E2-sequential minus E2-joint | nlpaueb/legal-bert-base-uncased | +0.212 [+0.144, +0.261] | +0.187 [+0.134, +0.229] | difference |

## Per label, all three backbones (exact F1 / relaxed F1)

| condition | DATA_TYPE | PURPOSE | THIRD_PARTY |
|---|---|---|---|
| E1 | 0.135 / 0.269 | 0.111 / 0.353 | 0.128 / 0.247 |
| E2-joint | 0.336 / 0.477 | 0.191 / 0.499 | 0.195 / 0.312 |
| E2-sequential | 0.510 / 0.641 | 0.359 / 0.607 | 0.436 / 0.555 |

## Per document group, all three backbones (exact micro-F1)

| group | E1 | E2-joint | E2-sequential |
|---|---|---|---|
| 08_pennydrop_terms | 0.131 | 0.221 | 0.358 |
| 14_nadl_charter+21_nadl_terms | 0.049 | 0.185 | 0.272 |
| 23_upmint_aa_tos | 0.171 | 0.448 | 0.644 |
| 24_credbuddha_terms | 0.181 | 0.383 | 0.533 |
| 25_the_financiali_privacy | 0.114 | 0.224 | 0.341 |
| 26_zerodha_tos | 0.000 | 0.000 | 0.020 |
| 28_indifi_capital_privacy | 0.105 | 0.209 | 0.473 |
| 29_icici_home_fin_terms | 0.132 | 0.213 | 0.363 |

## What the predictions were, per run on average (all three backbones)

| condition | predicted | exact | right label, wrong boundary | wrong label | spurious | of which definition mismatch | gold missed entirely |
|---|---|---|---|---|---|---|---|
| E1 | 944 | 111 | 150 | 21 | 663 | 170 | 550 |
| E2-joint | 630 | 184 | 144 | 16 | 286 | 66 | 494 |
| E2-sequential | 747 | 347 | 142 | 16 | 243 | 30 | 345 |

## LLM baseline (D64): a chat model given the labelling rules, no training

One run each (temperature 0). The interval is the same bootstrap over document groups.

| model and examples | exact micro-F1 | exact macro-F1 | relaxed micro-F1 | precision | recall | predicted | returned phrases not in the passage | mean of group F1 |
|---|---|---|---|---|---|---|---|---|
| llama3.1_8b_0shot | 0.280 [0.221, 0.325] | 0.284 [0.222, 0.318] | 0.325 [0.255, 0.389] | 0.176 | 0.674 | 3159 | 413 of 3170 | 0.247 |
| llama3.1_8b_8shot | 0.414 [0.345, 0.457] | 0.410 [0.325, 0.450] | 0.471 [0.396, 0.524] | 0.307 | 0.633 | 1703 | 46 of 1595 | 0.353 |
| qwen2.5_14b_0shot | 0.479 [0.439, 0.514] | 0.492 [0.427, 0.525] | 0.553 [0.495, 0.601] | 0.369 | 0.683 | 1529 | 28 of 1430 | 0.410 |
| qwen2.5_14b_8shot | 0.452 [0.369, 0.501] | 0.456 [0.368, 0.495] | 0.518 [0.435, 0.576] | 0.321 | 0.763 | 1961 | 33 of 1834 | 0.382 |

### LLM minus fine-tuned (paired; exact micro-F1 difference, then relaxed)

| LLM run | against | exact difference [95% CI] | relaxed difference [95% CI] | verdict (exact) |
|---|---|---|---|---|
| llama3.1_8b_0shot | E1 | +0.155 [+0.091, +0.212] | +0.033 [-0.038, +0.099] | LLM better |
| llama3.1_8b_0shot | E2-joint | +0.027 [-0.079, +0.103] | -0.117 [-0.219, -0.035] | no significant difference |
| llama3.1_8b_0shot | E2-sequential | -0.160 [-0.229, -0.091] | -0.280 [-0.335, -0.214] | fine-tuned better |
| llama3.1_8b_0shot | E2-sequential, nlpaueb/legal-bert-base-uncased only | -0.199 [-0.262, -0.140] | -0.312 [-0.365, -0.254] | fine-tuned better |
| llama3.1_8b_8shot | E1 | +0.289 [+0.218, +0.344] | +0.178 [+0.103, +0.234] | LLM better |
| llama3.1_8b_8shot | E2-joint | +0.161 [+0.057, +0.234] | +0.029 [-0.073, +0.100] | LLM better |
| llama3.1_8b_8shot | E2-sequential | -0.025 [-0.092, +0.039] | -0.135 [-0.190, -0.078] | no significant difference |
| llama3.1_8b_8shot | E2-sequential, nlpaueb/legal-bert-base-uncased only | -0.065 [-0.124, -0.010] | -0.166 [-0.222, -0.121] | fine-tuned better |
| qwen2.5_14b_0shot | E1 | +0.354 [+0.313, +0.389] | +0.260 [+0.192, +0.323] | LLM better |
| qwen2.5_14b_0shot | E2-joint | +0.227 [+0.148, +0.275] | +0.110 [+0.017, +0.181] | LLM better |
| qwen2.5_14b_0shot | E2-sequential | +0.040 [-0.016, +0.129] | -0.053 [-0.109, +0.036] | no significant difference |
| qwen2.5_14b_0shot | E2-sequential, nlpaueb/legal-bert-base-uncased only | +0.000 [-0.052, +0.078] | -0.084 [-0.136, -0.010] | no significant difference |
| qwen2.5_14b_8shot | E1 | +0.327 [+0.243, +0.387] | +0.225 [+0.143, +0.287] | LLM better |
| qwen2.5_14b_8shot | E2-joint | +0.200 [+0.074, +0.278] | +0.075 [-0.043, +0.153] | LLM better |
| qwen2.5_14b_8shot | E2-sequential | +0.013 [-0.072, +0.093] | -0.088 [-0.163, -0.012] | no significant difference |
| qwen2.5_14b_8shot | E2-sequential, nlpaueb/legal-bert-base-uncased only | -0.027 [-0.109, +0.047] | -0.119 [-0.193, -0.053] | no significant difference |

### LLM per label (exact F1 / relaxed F1)

| run | DATA_TYPE | PURPOSE | THIRD_PARTY |
|---|---|---|---|
| llama3.1_8b_0shot | 0.269 / 0.296 | 0.299 / 0.422 | 0.282 / 0.309 |
| llama3.1_8b_8shot | 0.422 / 0.462 | 0.375 / 0.477 | 0.432 / 0.477 |
| qwen2.5_14b_0shot | 0.433 / 0.483 | 0.437 / 0.584 | 0.606 / 0.654 |
| qwen2.5_14b_8shot | 0.420 / 0.467 | 0.438 / 0.551 | 0.509 / 0.555 |

### LLM per document group (exact micro-F1)

| group | llama3.1_8b_0shot | llama3.1_8b_8shot | qwen2.5_14b_0shot | qwen2.5_14b_8shot |
|---|---|---|---|---|
| 08_pennydrop_terms | 0.229 | 0.329 | 0.446 | 0.428 |
| 14_nadl_charter+21_nadl_terms | 0.154 | 0.292 | 0.394 | 0.201 |
| 23_upmint_aa_tos | 0.315 | 0.387 | 0.416 | 0.452 |
| 24_credbuddha_terms | 0.274 | 0.426 | 0.519 | 0.436 |
| 25_the_financiali_privacy | 0.332 | 0.461 | 0.566 | 0.542 |
| 26_zerodha_tos | 0.000 | 0.000 | 0.000 | 0.044 |
| 28_indifi_capital_privacy | 0.355 | 0.484 | 0.473 | 0.519 |
| 29_icici_home_fin_terms | 0.318 | 0.449 | 0.465 | 0.434 |
