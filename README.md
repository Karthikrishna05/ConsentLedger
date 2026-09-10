# ConsentLedger

A consent-aware **NLP + blockchain** reference system for India's RBI **Account Aggregator (AA)**
framework. It (1) extracts consent fields from AA documents with a transfer-learned **NER** model,
(2) rewrites them into a plain-language **summary** and checks the summary is **faithful** (drops/invents
nothing), and (3) anchors the consent on an on-chain **registry** for a tamper-evident audit trail.

> **New to the project? Read [`meta-documentation/OVERVIEW.md`](meta-documentation/OVERVIEW.md) first**
> (plain-language walkthrough). Design decisions: [`DECISIONS.md`](meta-documentation/DECISIONS.md);
> flow: [`FLOW.md`](meta-documentation/FLOW.md); who-does-what: [`TEAM.md`](meta-documentation/TEAM.md).

---

## What's in this repo vs. what you download

| In git (you get on clone) | NOT in git (you fetch/regenerate locally) |
|---|---|
| all `src/` code, `scaffold.py`, `pyproject.toml` | `.venv/` (make your own) |
| `configs/`, `tests/`, all `meta-documentation/` | `data/external/**` — OPP-115 / MAPP / APP-350 |
| `requirements*.txt`, `requirements.lock` | `data/aa/raw/**` — scraped company pages |
| `.env.example`, `.gitignore`, this README | `data/ner_bio/**`, `opp115_spans.jsonl` (derived) |
| the team's own `data/aa/annotated/`, `splits.json` | `artifacts_out/**` (model checkpoints) |

**Why the datasets aren't committed:** OPP-115/MAPP/APP-350 are **CC BY-NC (research-use)** — their
license forbids redistribution, and that extends to files containing their text (spans/CoNLL). They're
also large and **fully regenerable** from the download + our seeded scripts. So everyone downloads from
the original source and regenerates identical derived files (steps 4–5 below).

---

## Prerequisites
- **Python 3.11** (`py -3.11` on Windows).
- For NER/T5 training: an **NVIDIA GPU + recent driver** (project was built on an RTX A4500, CUDA 12.1
  wheels). CPU works for everything except fast training.
- `git`, and `curl` + `unzip` (bundled with Git for Windows / Git Bash).
- Node.js 20 + Hardhat — only for the blockchain part (Phase 4), set up later under `contracts/`.

---

## Setup (each teammate does this once)

The virtual environment (`.venv`) is **not** in the repo — everyone creates their **own** and installs
the libraries into it. Only `requirements*.txt` are committed; the actual packages are downloaded here.
Full detail / troubleshooting: [`meta-documentation/SETUP.md`](meta-documentation/SETUP.md).

**Step 1 — Clone and enter the project**
```bash
git clone <your-private-repo-url> ConsentLedger
cd ConsentLedger
```

**Step 2 — Create and activate the venv (Python 3.11).** Pick your shell:

PowerShell (Windows default):
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```
Git Bash:
```bash
py -3.11 -m venv .venv
source .venv/Scripts/activate
```
Your prompt should now start with `(.venv)`. (First-time PowerShell block? run
`Set-ExecutionPolicy -Scope Process RemoteSigned` then re-run the activate line.)

**Step 3 — Install ALL libraries into the venv** (torch FIRST from the CUDA index, then the rest). Same
commands in both shells once `(.venv)` is active:
```bash
python -m pip install --upgrade pip setuptools wheel
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install -e .
```
> **No NVIDIA GPU?** Replace the torch line with `pip install torch==2.3.1` (CPU build — everything works
> except fast training). **Exact-pin reproduction:** after torch, use `pip install -r requirements.lock`.

**Step 4 — Recreate the git-ignored folder skeleton**
```bash
python scaffold.py
```

**Step 5 — Verify** (expect `cuda True` on a GPU box, `transformers 4.46.3`, and no conflicts):
```bash
python -c "import torch, transformers; print('cuda', torch.cuda.is_available(), '| transformers', transformers.__version__)"
pip check
```
> If `cuda False`: the CPU torch got installed — `pip uninstall -y torch`, then redo the Step-3 torch
> line exactly (the `--index-url` is what pulls the CUDA build).

You must **activate the venv** (`Step 2`) in every new terminal before running project commands.

---

## Get the data (not in the repo)

Download the external corpora into `data/external/` (CC BY-NC — for your own research use only). These
commands use `curl` + `unzip` (**Git Bash**); PowerShell users: run them in Git Bash, or use
`Invoke-WebRequest` + `Expand-Archive` (see [`SETUP.md`](meta-documentation/SETUP.md)).
```bash
curl -L -o data/external/opp115/OPP-115_v1_0.zip https://usableprivacy.org/static/data/OPP-115_v1_0.zip
unzip -o -q data/external/opp115/OPP-115_v1_0.zip -d data/external/opp115/raw

curl -L -o data/external/mapp/MAPP_Corpus.zip https://usableprivacy.org/static/data/MAPP_Corpus.zip
unzip -o -q data/external/mapp/MAPP_Corpus.zip -d data/external/mapp/raw

curl -L -o data/external/app350/APP-350_v1.1.zip https://usableprivacy.org/static/data/APP-350_v1.1.zip
unzip -o -q data/external/app350/APP-350_v1.1.zip -d data/external/app350/raw

# macOS zip junk — remove so it doesn't clutter the loaders
find data/external -type d -name "__MACOSX" -prune -exec rm -rf {} + ; find data/external -name ".DS_Store" -delete
```

Sanity check the downloads (expect OPP-115 = 115 annotation CSVs, MAPP = 64 EN + 91 DE, APP-350 = 350):
```bash
echo "OPP-115: $(ls data/external/opp115/raw/OPP-115/annotations/*.csv | wc -l) CSVs"
echo "MAPP EN: $(ls data/external/mapp/raw/MAPP_Corpus/English_sanitized_policies | wc -l)"
```

---

## Regenerate the derived data (deterministic — identical for everyone)

```bash
python -m consentledger.data.load_opp115     # OPP-115 -> data/external/opp115/processed/opp115_spans.jsonl (gated)
python -m consentledger.data.bio_tagging     # spans -> data/ner_bio/{train,dev}.conll  (word-level BIO)
```
Both print a summary and self-check; `load_opp115` **refuses to emit** if span reconstruction < 99%.

Run tests:
```bash
pytest -q
```

---

## After setup — you are here, and where each person starts

Completing the steps above puts you at the **current project state**: environment ready, external
datasets downloaded, and the **E1 NER training data** (`data/ner_bio/train.conll`, `dev.conll`) generated.
From here, work is phase-wise — see [`TEAM.md`](meta-documentation/TEAM.md) and
[`DEADLINE_PLAN.md`](meta-documentation/DEADLINE_PLAN.md).

- **Everyone first (days 1–3):** AA **annotation sprint** — it's the critical path. Follow
  [`ANNOTATION_GUIDELINE.md`](meta-documentation/ANNOTATION_GUIDELINE.md).
- **P1 (NER):** build `ner/dataset.py` + `train.py` + `evaluate.py`; run **E1** on `data/ner_bio/`
  (BERT-base / Legal-BERT / InLegalBERT), then **E2** once AA docs are annotated.
- **P2 (Summarizer):** generate summary pairs → train T5 (`summ/*`) → build the **faithfulness metric**.
- **P3 (Blockchain):** `contracts/` (Solidity + Hardhat + Sepolia deploy); **file the IRB early**; later
  run the user study.
- **P4 (Integration):** annotate; then build `pipeline/end_to_end.py` wiring NER + T5 + faithfulness + chain.

> Current progress and what's next is always tracked in [`FLOW.md`](meta-documentation/FLOW.md).

---

## Project layout

```
src/consentledger/   package: data/ (loaders, bio_tagging, kappa), consent_artefact/, ner/, summ/, chain/, pipeline/
configs/             one YAML per experiment (NER backbones, T5 variants)
data/external/       downloaded corpora (git-ignored)   |  data/aa/ our AA corpus + annotations
data/ner_bio/        derived CoNLL (git-ignored)         |  data/splits/ splits.json
contracts/           Hardhat / Solidity (Phase 4)        |  tests/ verification gates
meta-documentation/  ALL project docs (see below)        |  paper/ LaTeX
```

## Documentation (all in `meta-documentation/`)
`OVERVIEW.md` (start here) · `DECISIONS.md` (every choice + why) · `FLOW.md` (system + build flow) ·
`TEAM.md` (roles) · `SETUP.md` (env detail) · `DEADLINE_PLAN.md` (the 2-week plan) ·
`ANNOTATION_GUIDELINE.md` (how to annotate) · `NER_LABEL_MAPPING.md` (label table).

> Convention: **all Markdown lives in `meta-documentation/`** — this root `README.md` is the one
> exception (GitHub renders it on the landing page).

## Secrets
Copy `.env.example` → `.env` (git-ignored). Use a **throwaway Sepolia test wallet only** — never a wallet
with real funds.
