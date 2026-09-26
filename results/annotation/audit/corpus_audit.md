# Annotation audit - two annotators vs the source corpus

23 documents | consensus lexicon: **34** (phrase, label) pairs both annotators independently endorsed at least once

## 1. Recall against the consensus lexicon

Every occurrence of a term BOTH annotators endorse somewhere, located in the raw text:

| outcome | n | share |
|---|---|---|
| both marked it | 99 | 31.8% |
| only A marked it | 122 | 39.2% |
| only B marked it | 18 | 5.8% |
| **missed by BOTH** | **72** | **23.2%** |
| total opportunities | 311 | |

## 2. The two perspectives

| | A | B |
|---|---|---|
| total spans | 1839 | 952 |
| repeat marks | 442 | 10 |
| DATA_TYPE | 804 (44%) | 372 (39%) |
| PURPOSE | 527 (29%) | 266 (28%) |
| THIRD_PARTY | 508 (28%) | 314 (33%) |
| mean recall vs lexicon | 58% | 39% |

### Vocabulary only A ever uses (top 25)

- `spi` [DATA_TYPE] x19
- `third party` [THIRD_PARTY] x16
- `services` [PURPOSE] x12
- `related parties` [THIRD_PARTY] x10
- `pii` [DATA_TYPE] x8
- `credit information companies` [THIRD_PARTY] x8
- `statistics` [PURPOSE] x6
- `agencies` [THIRD_PARTY] x6
- `bodies` [THIRD_PARTY] x6
- `cookie` [DATA_TYPE] x6
- `provision of the services` [PURPOSE] x6
- `partner institutions` [THIRD_PARTY] x6
- `lenders` [THIRD_PARTY] x6
- `trends' identification` [PURPOSE] x5
- `connection with criminal proceedings` [PURPOSE] x5
- `operating system` [DATA_TYPE] x5
- `partner institution` [THIRD_PARTY] x5
- `efficiency of the platform` [PURPOSE] x4
- `suggestions` [DATA_TYPE] x4
- `contact data` [DATA_TYPE] x4
- `version` [DATA_TYPE] x4
- `regulatory authorities` [THIRD_PARTY] x4
- `partners` [THIRD_PARTY] x4
- `market` [PURPOSE] x4
- `marketing communication` [PURPOSE] x4

### Vocabulary only B ever uses (top 25)

- `financial information` [DATA_TYPE] x15
- `reserve bank of india` [THIRD_PARTY] x10
- `rbi` [THIRD_PARTY] x6
- `financial information user` [THIRD_PARTY] x6
- `account information` [DATA_TYPE] x5
- `financial information provider` [THIRD_PARTY] x5
- `user authentication credentials` [DATA_TYPE] x4
- `directors` [THIRD_PARTY] x4
- `login id` [DATA_TYPE] x4
- `pins` [DATA_TYPE] x4
- `private keys` [DATA_TYPE] x4
- `government and related bodies` [THIRD_PARTY] x3
- `create a profile` [PURPOSE] x3
- `officers` [THIRD_PARTY] x3
- `related information` [DATA_TYPE] x3
- `presenting your financial information` [PURPOSE] x3
- `financial information providers` [THIRD_PARTY] x3
- `sahamati` [THIRD_PARTY] x3
- `purpose of collecting such financial information` [PURPOSE] x3
- `retrieving or collecting` [PURPOSE] x3
- `financial information` [THIRD_PARTY] x2
- `consent artefact` [DATA_TYPE] x2
- `retrieve, view, consolidate and share financial information` [PURPOSE] x2
- `customer identification` [PURPOSE] x2
- `signature` [DATA_TYPE] x2

## 3. Most-missed consensus terms (both annotators skipped)

| term | label | times missed |
|---|---|---|
| `service providers` | THIRD_PARTY | 16 |
| `credit information` | DATA_TYPE | 13 |
| `sensitive personal information` | DATA_TYPE | 8 |
| `email address` | DATA_TYPE | 8 |
| `third-party service provider` | THIRD_PARTY | 6 |
| `mobile number` | DATA_TYPE | 6 |
| `contact information` | DATA_TYPE | 3 |
| `credit bureaus` | THIRD_PARTY | 3 |
| `kyc documents` | DATA_TYPE | 2 |
| `group companies` | THIRD_PARTY | 2 |
| `parent companies` | THIRD_PARTY | 1 |
| `crif highmark` | THIRD_PARTY | 1 |
| `parent company` | THIRD_PARTY | 1 |
| `phone numbers` | DATA_TYPE | 1 |
| `ip addresses` | DATA_TYPE | 1 |

## 4. Per document

| doc | chars | opps | both | A only | B only | missed both | recall A | recall B | A spans | B spans |
|---|---|---|---|---|---|---|---|---|---|---|
| 28_indifi_capital_privacy | 51,157 | 52 | 6 | 25 | 2 | **19** | 60% | 15% | 438 | 50 |
| 24_credbuddha_terms | 50,586 | 34 | 4 | 18 | 1 | **11** | 65% | 15% | 182 | 10 |
| 08_pennydrop_terms | 43,588 | 32 | 10 | 15 | 0 | **7** | 78% | 31% | 198 | 67 |
| 03_oms_aa_terms | 25,360 | 18 | 6 | 6 | 0 | **6** | 67% | 33% | 45 | 57 |
| 05_onemoney_terms | 33,466 | 13 | 4 | 4 | 1 | **4** | 62% | 38% | 36 | 41 |
| 25_the_financiali_privacy | 20,055 | 12 | 7 | 1 | 0 | **4** | 67% | 58% | 120 | 62 |
| 09_saafe_terms | 29,656 | 13 | 5 | 4 | 1 | **3** | 69% | 46% | 35 | 30 |
| 16_oms_aa_privacy | 28,395 | 13 | 3 | 5 | 2 | **3** | 62% | 38% | 35 | 42 |
| 19_saafe_privacy | 21,265 | 16 | 1 | 10 | 2 | **3** | 69% | 19% | 131 | 9 |
| 01_setu_aa_terms | 33,827 | 20 | 6 | 11 | 1 | **2** | 85% | 35% | 48 | 29 |
| 12_scoremeaa_terms | 18,827 | 8 | 4 | 1 | 1 | **2** | 62% | 62% | 10 | 29 |
| 17_pb_fintech_aa_privacy | 14,820 | 13 | 9 | 2 | 0 | **2** | 85% | 69% | 129 | 68 |
| 04_pb_fintech_aa_terms | 26,100 | 11 | 6 | 3 | 1 | **1** | 82% | 64% | 44 | 39 |
| 14_nadl_charter | 10,995 | 4 | 3 | 0 | 0 | **1** | 75% | 75% | 22 | 53 |
| 22_setu_aa_charter | 10,310 | 3 | 0 | 0 | 2 | **1** | 0% | 67% | 8 | 38 |
| 23_upmint_aa_tos | 14,312 | 11 | 6 | 4 | 0 | **1** | 91% | 55% | 32 | 48 |
| 26_zerodha_tos | 5,231 | 1 | 0 | 0 | 0 | **1** | 0% | 0% | 8 | 32 |
| 29_icici_home_fin_terms | 13,487 | 14 | 6 | 3 | 4 | **1** | 64% | 71% | 73 | 41 |
| 02_digio_terms | 29,909 | 11 | 5 | 6 | 0 | **0** | 100% | 46% | 48 | 43 |
| 06_setu_aa_privacy | 18,789 | 12 | 8 | 4 | 0 | **0** | 100% | 67% | 154 | 63 |
| 10_perfios_terms | 20,931 | 0 | 0 | 0 | 0 | **0** | 0% | 0% | 27 | 31 |
| 20_scoremeaa_charter | 11,091 | 0 | 0 | 0 | 0 | **0** | 0% | 0% | 4 | 32 |
| 21_nadl_terms | 12,785 | 0 | 0 | 0 | 0 | **0** | 0% | 0% | 12 | 38 |

Per-document detail: `results\annotation\audit\per_doc/<doc_id>.md`