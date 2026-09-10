#!/usr/bin/env python3
"""Create the ConsentLedger project skeleton (Design 3: transfer + domain-adaptation).

Safe to run repeatedly:
  * directories are created with exist_ok=True
  * files are NEVER overwritten (existing content is preserved)
  * .venv/, meta-documentation/, requirements*.txt, .gitignore are left untouched

Usage (from the project root):
  python scaffold.py            # create the structure
  python scaffold.py --dry-run  # print what WOULD be created, write nothing
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Folders we must never scaffold into or clobber.
PROTECTED = {".venv", ".venv-annotation", "meta-documentation", ".git"}

# ---------------------------------------------------------------------------
# 1. Directories (empty ones get a .gitkeep so git tracks them)
# ---------------------------------------------------------------------------
DIRS: list[str] = [
    # --- DOWNLOADED public datasets (kept separate from our own AA corpus) ---
    "data/external/opp115/raw",
    "data/external/opp115/processed",
    "data/external/mapp/raw",
    "data/external/mapp/processed",
    "data/external/app350/raw",        # auxiliary (segment-level; not BIO-converted)
    "data/external/cuad/raw",          # auxiliary (clause-level; not BIO-converted)
    # --- our Account Aggregator corpus ---
    "data/aa/raw/html",
    "data/aa/raw/pdf",
    "data/aa/raw/text",
    "data/aa/annotated",               # Label Studio gold exports
    "data/aa/consent_artefacts",       # structured ReBIT-shaped JSON (duration/freq/recipient)
    # --- merged, training-ready BIO (external [+ optional AA adaptation]) ---
    "data/ner_bio",
    "data/splits",                     # splits.json — single source of truth
    # --- code package ---
    "src/consentledger/data",
    "src/consentledger/consent_artefact",
    "src/consentledger/ner",
    "src/consentledger/summ",
    "src/consentledger/chain",
    "src/consentledger/pipeline",
    # --- smart contract (Node/Hardhat world, Phase 4) ---
    "contracts/contracts",
    "contracts/scripts",
    "contracts/test",
    # --- experiment configs / outputs / tests / paper ---
    "configs",
    "artifacts_out/ner",               # gitignored (large checkpoints)
    "artifacts_out/summ",
    "results/ner",
    "results/summ",
    "results/chain",
    "results/user_study",
    "results/pipeline",
    "tests",
    "notebooks",
    "paper/figures",
]

# Directories that should stay tracked even while empty.
GITKEEP = {
    "data/external/opp115/raw", "data/external/opp115/processed",
    "data/external/mapp/raw", "data/external/mapp/processed",
    "data/external/app350/raw", "data/external/cuad/raw",
    "data/aa/raw/html", "data/aa/raw/pdf", "data/aa/raw/text",
    "data/aa/annotated", "data/aa/consent_artefacts",
    "data/ner_bio", "data/splits",
    "artifacts_out/ner", "artifacts_out/summ",
    "results/ner", "results/summ", "results/chain", "results/user_study", "results/pipeline",
    "notebooks", "paper/figures",
    "contracts/contracts", "contracts/scripts", "contracts/test",
}

# Python packages that need an __init__.py
PACKAGES = [
    "src/consentledger",
    "src/consentledger/data",
    "src/consentledger/consent_artefact",
    "src/consentledger/ner",
    "src/consentledger/summ",
    "src/consentledger/chain",
    "src/consentledger/pipeline",
    "tests",
]

# NER label set for Design 3 (3 entity types -> 7 BIO tags)
NER_LABELS = [
    "O",
    "B-DATA_TYPE", "I-DATA_TYPE",
    "B-PURPOSE", "I-PURPOSE",
    "B-THIRD_PARTY", "I-THIRD_PARTY",
]

# ---------------------------------------------------------------------------
# 2. Stub files (docstring + TODO only — real logic lands per phase)
# ---------------------------------------------------------------------------
def _stub(desc: str, phase: str, cli: bool = False) -> str:
    body = f'"""{desc}\n\nTODO ({phase}): implement. See meta-documentation/ for the locked design.\n"""\n'
    if cli:
        body += (
            "\n\ndef main() -> None:\n"
            '    raise NotImplementedError("TODO: implement CLI entry point")\n'
            '\n\nif __name__ == "__main__":\n    main()\n'
        )
    return body


SEED_PY = '''"""Global determinism helper — call set_seed(cfg.seed) at every train/eval entry point."""
from __future__ import annotations

import os
import random


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
'''

STUB_FILES: dict[str, str] = {
    "src/consentledger/seed.py": SEED_PY,
    "src/consentledger/config.py": _stub("Load and validate a YAML experiment config.", "Phase 0"),
    # data
    "src/consentledger/data/download_external.py": _stub("Download OPP-115 / MAPP / APP-350 / CUAD into data/external/.", "Phase 1", cli=True),
    "src/consentledger/data/load_opp115.py": _stub("OPP-115 attribute-value spans -> BIO (DATA_TYPE/PURPOSE/THIRD_PARTY), offset-based. See meta-documentation/NER_LABEL_MAPPING.md.", "Phase 1", cli=True),
    "src/consentledger/data/load_mapp.py": _stub("MAPP-English attribute-value spans -> BIO (validate MAPP's own attribute names first).", "Phase 1", cli=True),
    "src/consentledger/data/scrape_aa.py": _stub("Fetch the AA corpus from the manifest into data/aa/raw/.", "Phase 1", cli=True),
    "src/consentledger/data/clean.py": _stub("HTML/PDF -> clean plain text, boilerplate stripped.", "Phase 1"),
    "src/consentledger/data/bio_tagging.py": _stub("Offset-mapping BIO alignment (never .split()); reconstruction spot-check.", "Phase 1"),
    "src/consentledger/data/ls_import_export.py": _stub("Label Studio JSON <-> CoNLL converters.", "Phase 1"),
    "src/consentledger/data/kappa.py": _stub("Inter-annotator agreement: entity-level P/R/F1 (primary) + token Cohen's kappa (secondary).", "Phase 1"),
    # consent artefact (structured fields, not NER)
    "src/consentledger/consent_artefact/parse.py": _stub("Parse RECIPIENT/DURATION/FREQUENCY/DATA_RANGE/DATA_LIFE from ReBIT-shaped consent JSON.", "Phase 1"),
    # ner
    "src/consentledger/ner/dataset.py": _stub("CoNLL -> tokenized dataset; first-subword label, rest -100.", "Phase 2"),
    "src/consentledger/ner/train.py": _stub("Fine-tune a backbone (uniform recipe, no layer-freezing).", "Phase 2", cli=True),
    "src/consentledger/ner/evaluate.py": _stub("seqeval entity-level metrics. TEST OPENED ONCE, IN PHASE 6.", "Phase 2/6", cli=True),
    "src/consentledger/ner/predict.py": _stub("Load best model; return char-span entities for the pipeline.", "Phase 2"),
    # summ
    "src/consentledger/summ/dataset.py": _stub("Build (clause -> plain-language) pairs; task prefix; chunk long sources.", "Phase 3"),
    "src/consentledger/summ/train.py": _stub("Fine-tune T5/Flan-T5 (predict_with_generate=True).", "Phase 3", cli=True),
    "src/consentledger/summ/evaluate.py": _stub("ROUGE + BERTScore (log scorer version) + entity-preservation.", "Phase 3/6", cli=True),
    "src/consentledger/summ/predict.py": _stub("Load best summarizer; return plain-language summary.", "Phase 3"),
    # chain
    "src/consentledger/chain/web3_client.py": _stub("web3.py v6 connection + tx signing/gas/nonce helpers.", "Phase 4/5"),
    "src/consentledger/chain/register_consent.py": _stub("canonicalize -> keccak -> createConsent + grantConsent.", "Phase 5", cli=True),
    "src/consentledger/chain/read_consent.py": _stub("Query state, decode events, build the Etherscan audit link.", "Phase 5"),
    # pipeline
    "src/consentledger/pipeline/end_to_end.py": _stub("doc -> entities -> summary -> faithfulness -> on-chain -> report JSON.", "Phase 5", cli=True),
    # tests (verification gates from the plan)
    "tests/test_split_integrity.py": _stub("Assert no doc_id / content-hash appears in two splits; 15-adapt vs 25-test disjoint.", "Phase 1"),
    "tests/test_label_support.py": _stub("Assert DATA_TYPE/PURPOSE/THIRD_PARTY have non-trivial support per split.", "Phase 1"),
    "tests/test_bio_reconstruction.py": _stub("Round-trip: CoNLL -> entities -> compare >=20 spans to source text.", "Phase 1"),
    # env template
    ".env.example": (
        "# Sepolia testnet only — NEVER a wallet holding real funds.\n"
        "SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY\n"
        "DEPLOYER_PRIVATE_KEY=0xYOUR_TEST_WALLET_PRIVATE_KEY_NEVER_REAL_FUNDS\n"
        "ETHERSCAN_API_KEY=YOUR_ETHERSCAN_KEY\n"
    ),
}


def _ner_config(name: str, model_id: str) -> str:
    labels = ", ".join(f'"{t}"' for t in NER_LABELS)
    return (
        f"# NER experiment: {name}\n"
        f"model_name: {model_id}\n"
        f"labels: [{labels}]\n"
        "seed: 42\n"
        "learning_rate: 2.0e-5\n"
        "num_train_epochs: 20\n"
        "per_device_train_batch_size: 16\n"
        "weight_decay: 0.01\n"
        "warmup_ratio: 0.1\n"
        "early_stopping_patience: 3\n"
        "metric_for_best_model: eval_f1\n"
        "train_file: data/ner_bio/train.conll\n"
        "dev_file: data/ner_bio/dev.conll\n"
        f"output_dir: artifacts_out/ner/{name}\n"
    )


CONFIGS = {
    "configs/ner_bert_base.yaml": _ner_config("bert_base", "bert-base-uncased"),
    "configs/ner_legalbert.yaml": _ner_config("legalbert", "nlpaueb/legal-bert-base-uncased"),
    "configs/ner_inlegalbert.yaml": _ner_config("inlegalbert", "law-ai/InLegalBERT"),
    "configs/summ_t5small.yaml": "# Summarizer: T5-small\nmodel_name: t5-small\nseed: 42\nsource_prefix: \"summarize: \"\nmax_source_length: 512\nmax_target_length: 128\nlearning_rate: 3.0e-4\nnum_train_epochs: 20\nper_device_train_batch_size: 8\nnum_beams: 4\nno_repeat_ngram_size: 3\noutput_dir: artifacts_out/summ/t5small\n",
    "configs/summ_flant5base.yaml": "# Summarizer: Flan-T5-base\nmodel_name: google/flan-t5-base\nseed: 42\nsource_prefix: \"Summarize this consent clause in plain language: \"\nmax_source_length: 512\nmax_target_length: 128\nlearning_rate: 1.0e-4\nnum_train_epochs: 20\nper_device_train_batch_size: 8\nnum_beams: 4\nno_repeat_ngram_size: 3\noutput_dir: artifacts_out/summ/flant5base\n",
}


# ---------------------------------------------------------------------------
# 3. Runner
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold the ConsentLedger project.")
    ap.add_argument("--dry-run", action="store_true", help="print planned actions, write nothing")
    args = ap.parse_args()

    created: list[str] = []
    skipped: list[str] = []

    def ensure_dir(rel: str) -> None:
        p = ROOT / rel
        if p.exists():
            return
        if args.dry_run:
            created.append(f"dir  {rel}/")
        else:
            p.mkdir(parents=True, exist_ok=True)
            created.append(f"dir  {rel}/")

    def ensure_file(rel: str, content: str) -> None:
        p = ROOT / rel
        top = Path(rel).parts[0]
        if top in PROTECTED:
            return
        if p.exists():
            skipped.append(rel)
            return
        if args.dry_run:
            created.append(f"file {rel}")
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        created.append(f"file {rel}")

    for d in DIRS:
        ensure_dir(d)
    for pkg in PACKAGES:
        ensure_file(f"{pkg}/__init__.py", '"""ConsentLedger package."""\n')
    for rel, content in STUB_FILES.items():
        ensure_file(rel, content)
    for rel, content in CONFIGS.items():
        ensure_file(rel, content)
    for d in GITKEEP:
        ensure_file(f"{d}/.gitkeep", "")

    mode = "DRY-RUN (nothing written)" if args.dry_run else "APPLIED"
    print(f"\n=== ConsentLedger scaffold — {mode} ===")
    print(f"created/planned: {len(created)}   already-present (skipped): {len(skipped)}")
    for line in created:
        print("  +", line)
    if skipped:
        print("  (skipped existing:", ", ".join(skipped) + ")")
    print("\nProtected, never touched: .venv/, meta-documentation/, requirements*.txt, .gitignore")


if __name__ == "__main__":
    main()
