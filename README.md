# ConsentLedger

A consent-aware **NLP + blockchain** reference system for India's RBI **Account Aggregator (AA)** framework.
Give it an AA policy (and, optionally, the consent artefact a user is asked to grant) and it:

1. **highlights** the data types, purposes and third parties in the policy with a transfer-learned NER model,
   marking what the policy promises *not* to do;
2. **reads** the consent artefact's structured terms (recipient, duration, frequency, data range, data life);
3. **summarises** each passage in plain language and **checks** each summary against its passage — a summary
   that reverses a meaning, names the wrong party or invents a name is withheld and the facts are shown instead;
4. **fingerprints** the consent together with the policy's facts and can record that fingerprint on the
   Ethereum **Sepolia** test network, so anyone can later check that neither was changed.

> **New here?** Read [`meta-documentation/OVERVIEW.md`](meta-documentation/OVERVIEW.md) (plain-language tour), then
> the project "bible" [`DETAILED_EXPLANATION.md`](meta-documentation/DETAILED_EXPLANATION.md). Every decision and
> its reasoning: [`DECISIONS.md`](meta-documentation/DECISIONS.md) (D1–D85). Live status:
> [`FLOW.md`](meta-documentation/FLOW.md).

**Research prototype, research use only** — the NER models were trained partly on OPP-115 (CC BY-NC 4.0).
Summaries are machine-written and only partly checked; this is not legal advice. Testnet only.

---

## Quick start — run the demo (no training needed)

1. Do the **Setup** below (clone, venv, libraries).
2. Log in to Hugging Face with an account that can read the team's **private** model repos
   (`Karthikrishna05/consentledger-ner`, `Karthikrishna05/consentledger-summ`):
   ```powershell
   hf auth login
   ```
   The models (~1.6 GB) download on first use and are cached; later starts take seconds. If the download stops
   (a dropped connection), just run the command again — finished files are kept.
3. *(Optional, for the blockchain parts)* copy `.env.example` to `.env` and fill it in — see **Secrets** below.
4. Start the demo and open http://127.0.0.1:7860 :
   ```powershell
   python app.py
   ```
   Or run the whole pipeline on a file and get a JSON report in `results/pipeline/`:
   ```powershell
   python -m consentledger.pipeline.end_to_end --doc policy.html --consent data/aa/consent_artefacts/demo_consent.json
   ```
   Add `--chain` to record the fingerprint on Sepolia (needs `.env`).
5. *(Optional)* share it while it runs: `python app.py --share` prints a temporary public `https://….gradio.live`
   link. Set a password first with `$env:DEMO_PASSWORD="…"` (visitors log in as `demo`).

---

## Setup (each teammate does this once)

The virtual environment (`.venv`) is **not** in the repo — everyone creates their own.
Full detail / troubleshooting: [`meta-documentation/SETUP.md`](meta-documentation/SETUP.md).

**Prerequisites:** Python **3.11**; `git`. For training: an NVIDIA GPU (built on an RTX A4500, CUDA 12.1) — the
demo and the pipeline run on CPU too. Node.js 20 only for the contract (`contracts/`).

**Step 1 — Clone and enter the project** (the first line lets Windows handle the contract's long file names):
```bash
git config --global core.longpaths true
git clone <your-private-repo-url> ConsentLedger
cd ConsentLedger
```
> Clone into a short folder such as `C:\Users\<you>\ConsentLedger`, not a deeply nested one.

**Step 2 — Create and activate the venv (Python 3.11).** PowerShell:
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```
Git Bash: `py -3.11 -m venv .venv` then `source .venv/Scripts/activate`. Your prompt should start with `(.venv)`.
(First-time PowerShell block? run `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again.)

**Step 3 — Install the libraries** (torch first, from the CUDA index, then the rest):
```bash
python -m pip install --upgrade pip setuptools wheel
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install -e .
```
> **No NVIDIA GPU?** Use `pip install torch==2.3.1` (CPU build). **Exact reproduction:** after torch,
> `pip install -r requirements.lock`. Do not upgrade `transformers` (pinned 4.46.3) or `numpy` (1.26.4).

**Step 4 — Recreate the git-ignored folder skeleton**
```bash
python scaffold.py
```

**Step 5 — Verify** (expect `transformers 4.46.3`, `cuda True` on a GPU machine, and no conflicts):
```bash
python -c "import torch, transformers; print('cuda', torch.cuda.is_available(), '| transformers', transformers.__version__)"
pip check
pytest -q
```

Activate the venv in every new terminal before running project commands.

---

## Results at a glance

| Part | Result | Where |
|---|---|---|
| NER, transfer from OPP-115 (E1) vs + a little AA data (E2) | exact micro-F1 on the sealed AA test set: E1 0.125 → E2-joint 0.252 → **E2-sequential 0.439** (each step significant); best single backbone Legal-BERT 0.479 | D63 |
| LLM baseline (local 14B model, rules only) | 0.479 exact — ties fine-tuning on exact F1, behind on relaxed F1 | D64, D65 |
| Annotation | 23 AA documents, 1,266 gold highlights; final inter-annotator kappa 0.43 (0.52 on a fresh document) | D43, D48, D57 |
| Summariser | Flan-T5-base (main) and t5-small, fine-tuned on 174 passages; frozen | D73 |
| Faithfulness check | on fresh documents (settled labels): Flan-T5-base summaries shown wrong 22% (28% unchecked); 1 of 2 reversals caught; 2 of 36 good summaries blocked | D82 |
| Smart contract | `ConsentRegistry` on Sepolia `0x2De2051bAb111580a0F0C850E7C8318b94aAA4bF`; gas: create 459,911 · grant 31,603 · record access 25,051 · revoke 31,734 | D78 |

The summariser's sealed test (154 passages) and the whole-system test are still to be run, once.

---

## Reproduce the experiments

The AA corpus, the gold answer key (`data/aa/annotated/gold.json`) and the summariser data quote the scraped
policies, so they are **not in git** — team members get them from P1. The external corpora are downloaded below.

**Get the external data** (CC BY-NC, research use; Git Bash, or see `SETUP.md` for PowerShell):
```bash
curl -L -o data/external/opp115/OPP-115_v1_0.zip https://usableprivacy.org/static/data/OPP-115_v1_0.zip
unzip -o -q data/external/opp115/OPP-115_v1_0.zip -d data/external/opp115/raw
curl -L -o data/external/mapp/MAPP_Corpus.zip https://usableprivacy.org/static/data/MAPP_Corpus.zip
unzip -o -q data/external/mapp/MAPP_Corpus.zip -d data/external/mapp/raw
curl -L -o data/external/app350/APP-350_v1.1.zip https://usableprivacy.org/static/data/APP-350_v1.1.zip
unzip -o -q data/external/app350/APP-350_v1.1.zip -d data/external/app350/raw
find data/external -type d -name "__MACOSX" -prune -exec rm -rf {} + ; find data/external -name ".DS_Store" -delete
```

**Regenerate the derived data** (deterministic — identical for everyone):
```bash
python -m consentledger.data.load_opp115     # OPP-115 -> opp115_spans.jsonl (refuses to emit if reconstruction < 99%)
python -m consentledger.data.bio_tagging     # -> data/ner_bio/{train,dev}.conll
python -m consentledger.data.aa_to_conll     # gold.json -> aa_test / aa_adapt(_train,_dev).conll
```

**NER (E1, E2):** one config per backbone in `configs/`, three seeds each:
```bash
python -m consentledger.ner.train --config configs/ner_legalbert.yaml --seed 42                  # E1
python -m consentledger.ner.train --config configs/ner_legalbert.yaml --seed 42 --e2 sequential  # E2
python -m consentledger.ner.collect                                                             # metrics table
```
> **The AA test set is spent (D63):** it was opened once for the pre-specified runs and is never re-scored after
> any change. `ner.evaluate` scores `aa_test.conll` only with `--open-test`, and logs every opening.

**Summariser:**
```bash
python -m consentledger.summ.build_dataset chunks --gold data/aa/annotated/gold.json --test-docs 08_pennydrop_terms 14_nadl_charter 21_nadl_terms 23_upmint_aa_tos 24_credbuddha_terms 25_the_financiali_privacy 26_zerodha_tos 28_indifi_capital_privacy 29_icici_home_fin_terms --skip-docs 02_digio_terms 10_perfios_terms --min-facts 0
python -m consentledger.summ.build_dataset validate
python -m consentledger.summ.train --config configs/summ_flant5base.yaml --data data/summ --out artifacts_out/summ/flant5base
```

**Self-checks** (each module tests itself; data-dependent parts are skipped on a fresh clone):
```bash
python -m consentledger.summ.faithfulness --selfcheck
python -m consentledger.consent_artefact.parse --selfcheck
python -m consentledger.ner.predict --selfcheck
python -m consentledger.summ.predict --selfcheck
python -m consentledger.pipeline.end_to_end --selfcheck
pytest -q
```

**Contract:** see [`contracts/README.md`](contracts/README.md) (10 Hardhat tests, deploy, verify, Python CLIs).

---

## Deploy the demo to Hugging Face Spaces

> Hosting a Gradio Space now needs a Hugging Face **PRO** subscription (D85). Without it, run the demo on your
> laptop and use `python app.py --share` for a temporary public link.


```powershell
python space/build.py
hf repo create <user>/consentledger-demo --repo-type space --space_sdk gradio --private
hf upload <user>/consentledger-demo artifacts_out/space . --repo-type space
```
`space/build.py` copies only the app, the package code, the demo consent and the contract's address and ABI —
never documents, annotations, models or keys. In the Space's *Settings → Variables and secrets* add `HF_TOKEN`
(a read token, for the private models), `SEPOLIA_RPC_URL`, and optionally `SEPOLIA_PRIVATE_KEY` (test wallet).
Details: [`space/README.md`](space/README.md).

---

## What's in git vs. what you fetch

| In git | Not in git |
|---|---|
| `src/`, `app.py`, `space/`, `scaffold.py`, `pyproject.toml`, `configs/`, `tests/`, `contracts/` | `.venv/`, `.env` |
| `meta-documentation/`, `requirements*.txt`, `.env.example` | `data/external/**` — OPP-115 / MAPP / APP-350 (licence forbids redistribution) |
| `results/` (numbers only), `data/splits/`, the synthetic and real consent-artefact examples | `data/aa/raw/**`, `gold.json`, `data/summ/*.jsonl` — they quote the scraped policies |
| the contract's ABI and Sepolia deployment record | `artifacts_out/**` — models (they live on the Hugging Face Hub) |

**Rule of thumb:** anything that quotes scraped document text is never committed; numbers-only summaries are.

## Project layout
```
app.py               the demo web page (Gradio) over pipeline/end_to_end.run
src/consentledger/   data/ (corpus, annotation, adjudication, splits), ner/ (train, evaluate, predict, LLM baseline),
                     summ/ (dataset, train, predict, faithfulness), consent_artefact/ (parse), chain/ (web3 client,
                     register / read / revoke), pipeline/ (end_to_end)
configs/             one YAML per experiment            contracts/   Solidity + Hardhat (P3)
space/               the Hugging Face Space card, requirements and builder
data/                external/ (git-ignored), aa/ (corpus, annotations, consent artefacts), splits/
tests/               verification gates                 meta-documentation/   all project docs
```

## Secrets
Copy `.env.example` → `.env` (git-ignored; one file for the Python and Hardhat): `SEPOLIA_RPC_URL`,
`SEPOLIA_PRIVATE_KEY` (a **throwaway Sepolia test wallet** — never one with real funds), `ETHERSCAN_API_KEY`.
The code refuses any network other than Sepolia and a local Hardhat chain. Never paste a key into chat, a
commit or a screenshot.

## Team
P1 — NER, annotation lead, integration, paper · P2 — summariser (handed over to P1, D77) · P3 — smart contract ·
P4 — annotation, testing. Roles: [`TEAM.md`](meta-documentation/TEAM.md).
