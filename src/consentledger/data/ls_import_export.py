"""Label Studio import/export helpers.

`make-tasks` builds the import file from data/aa/raw/text/*.txt. Import THIS file (not the .txt files) so each
task's `doc_id` survives to the export that kappa.py and the CoNLL export match documents on.

Usage:
    python -m consentledger.data.ls_import_export make-tasks
    # -> data/aa/annotated/ls_import_tasks.json  (import this in Label Studio)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEXT_DIR = PROJECT_ROOT / "data" / "aa" / "raw" / "text"
IMPORT_OUT = PROJECT_ROOT / "data" / "aa" / "annotated" / "ls_import_tasks.json"


def make_tasks() -> None:
    files = sorted(TEXT_DIR.glob("*.txt"))
    if not files:
        raise SystemExit(f"No text files in {TEXT_DIR}. Run clean.py first.")
    tasks = [{"data": {"doc_id": f.stem, "text": f.read_text(encoding="utf-8")}} for f in files]
    IMPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {IMPORT_OUT.relative_to(PROJECT_ROOT)} with {len(tasks)} tasks "
          f"(each carries doc_id + text). Import this file in Label Studio.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Label Studio import/export helpers.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("make-tasks", help="build the LS import JSON from data/aa/raw/text/*.txt")
    args = ap.parse_args()
    if args.cmd == "make-tasks":
        make_tasks()


if __name__ == "__main__":
    main()
