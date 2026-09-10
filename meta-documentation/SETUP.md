# ConsentLedger — Environment Setup

Reproducible setup for the whole project. Three isolated worlds, on purpose:

1. **`.venv`** — the main Python env (NLP + blockchain-client + data + stats). ← this file's focus
2. **`.venv-annotation`** — Label Studio only (kept apart to avoid dependency conflicts).
3. **`contracts/`** — Node/Hardhat (npm), created later in Phase 4. Not a Python env.

Detected on this machine: Python 3.11 (`py -3.11`), RTX A4500 16 GB (driver 595.95), no conda → we use
`venv` + `pip`. torch comes from the CUDA 12.1 wheel index (bundles its own CUDA runtime; the driver is
forward-compatible).

---

## Main environment (`.venv`)

Run from the project root (`C:\Users\pc\Project-Programming\Python\ConsentLedger`) in **PowerShell**:

```powershell
# 1. Create the venv (already done if .venv exists)
py -3.11 -m venv .venv

# 2. Activate it
.venv\Scripts\Activate.ps1
#   (if PowerShell blocks the script:  Set-ExecutionPolicy -Scope Process RemoteSigned  then retry)

# 3. Modern pip/build tools
python -m pip install --upgrade pip setuptools wheel

# 4. Install torch WITH CUDA 12.1 (must be first, and from the torch index)
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# 5. Everything else (pinned, conflict-free) from PyPI
pip install -r requirements.txt

# 6. spaCy English model (not on PyPI as a normal dep)
python -m spacy download en_core_web_sm
```

### Verify it worked

```powershell
python -c "import torch, transformers, sentencepiece, seqeval, web3, spacy; print('torch', torch.__version__, 'cuda', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'); print('transformers', transformers.__version__)"
```

Expected: `cuda True`, `device NVIDIA RTX A4500 ...`, `transformers 4.46.3`.

> If `cuda False`: the CPU wheel got installed. Fix: `pip uninstall -y torch` then repeat step 4 exactly
> (the `--index-url` line is what pulls the CUDA build).

---

## Annotation environment (`.venv-annotation`) — only when you start AA annotation

Kept separate on purpose (see `requirements-annotation.txt` for why).

```powershell
py -3.11 -m venv .venv-annotation
.venv-annotation\Scripts\Activate.ps1
pip install -r requirements-annotation.txt
label-studio start
```

Or, most reliably, via Docker (no Python deps):

```powershell
docker run -it -p 8080:8080 -v ${PWD}/data/annotated:/label-studio/data heartexlabs/label-studio:latest
```

---

## Notes

- **Reproducibility:** exact versions are pinned in `requirements.txt`; torch is pinned to `2.3.1+cu121`.
  A fresh clone + these steps reproduces the environment. If you later `pip freeze > requirements.lock`,
  commit that lock file alongside for byte-exact reproduction.
- **Why numpy<2.0:** it's the compatibility anchor for torch 2.3 / spaCy 3.7 / bert-score / pandas 2.2.
  Do not bump it without re-testing the whole stack.
- **Git ignore:** add `.venv/`, `.venv-annotation/`, `__pycache__/` to `.gitignore` (never commit venvs).
