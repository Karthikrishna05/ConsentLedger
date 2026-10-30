"""Assemble the Hugging Face Space in artifacts_out/space/: the app and only what it needs at run time.

    python space/build.py
    hf upload <user>/<space> artifacts_out/space . --repo-type space

No data, models (fetched from the Hub at start-up), .env or keys; any git-ignored file aborts the build.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts_out" / "space"
FILES = {
    "app.py": "app.py",
    "space/README.md": "README.md",
    "space/requirements.txt": "requirements.txt",
    "data/aa/consent_artefacts/demo_consent.json": "data/aa/consent_artefacts/demo_consent.json",
    "contracts/ConsentRegistry.abi.json": "contracts/ConsentRegistry.abi.json",
    "contracts/ignition/deployments/chain-11155111/deployed_addresses.json":
        "contracts/ignition/deployments/chain-11155111/deployed_addresses.json",
}


def main() -> None:
    sources = dict(FILES)
    for p in sorted((ROOT / "src" / "consentledger").rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        sources[rel] = rel
    ignored = subprocess.run(["git", "check-ignore", *sources], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert not ignored, f"refusing to ship git-ignored files: {ignored}"
    assert not any(Path(s).name.startswith(".env") for s in sources)
    if OUT.exists():
        shutil.rmtree(OUT)
    for src, dst in sources.items():
        (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / src, OUT / dst)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(sources)} files, {size / 1024:.0f} KB -> {OUT}")


if __name__ == "__main__":
    main()
