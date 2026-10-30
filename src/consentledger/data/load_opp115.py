"""Load OPP-115 -> provenance-tagged char-span records (DATA_TYPE / PURPOSE / THIRD_PARTY) as JSONL.

GATE: segment[seg_start:seg_end] must equal selectedText for >= GATE_MIN_MATCH_RATE of spans, else exit non-zero.
Format (documentation/manual.txt): headerless 9-column CSVs, col G = attribute JSON; policies split on '|||'.

Usage:
    python -m consentledger.data.load_opp115                 # consolidation, threshold 0.75 (default)
    python -m consentledger.data.load_opp115 --threshold 0.5
    python -m consentledger.data.load_opp115 --source annotations   # raw 3-annotator (no merge)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPP_DIR = PROJECT_ROOT / "data" / "external" / "opp115" / "raw" / "OPP-115"
OUT_DEFAULT = PROJECT_ROOT / "data" / "external" / "opp115" / "processed" / "opp115_spans.jsonl"

# OPP-115 attribute name -> our NER label (the three attributes that transfer)
LABEL_MAP = {
    "Personal Information Type": "DATA_TYPE",
    "Purpose": "PURPOSE",
    "Third Party Entity": "THIRD_PARTY",
}
DROP_VALUES = {"Unspecified", "not-selected"}   # non-informative annotator values
DROP_CATEGORIES = {"Other"}
SEGMENT_DELIM = "|||"
GATE_MIN_MATCH_RATE = 0.99

# CSV column indices (no header row), per documentation/manual.txt
C_ANN_ID, C_BATCH, C_ANNOTATOR, C_POLICY, C_SEGMENT, C_CATEGORY, C_ATTRS, C_URL, C_DATE = range(9)


def load_errant_ann_ids(opp_dir: Path) -> set[str]:
    """annotation IDs whose span offsets are known-buggy (documentation/errant_span_indexes/)."""
    ids: set[str] = set()
    d = opp_dir / "documentation" / "errant_span_indexes"
    if d.is_dir():
        for f in d.iterdir():
            if not f.is_file():
                continue
            try:
                for row in csv.reader(f.open(encoding="utf-8")):
                    if row:
                        ids.add(row[0].strip())
            except OSError:
                pass
    return ids


def csv_dir(opp_dir: Path, source: str, threshold: str) -> Path:
    if source == "annotations":
        return opp_dir / "annotations"
    return opp_dir / "consolidation" / f"threshold-{threshold}-overlap-similarity"


def segments_for(opp_dir: Path, stem: str) -> list[str] | None:
    p = opp_dir / "sanitized_policies" / f"{stem}.html"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").split(SEGMENT_DELIM)


def main() -> None:
    ap = argparse.ArgumentParser(description="Load OPP-115 into normalized span records.")
    ap.add_argument("--source", choices=["consolidation", "annotations"], default="consolidation")
    ap.add_argument("--threshold", choices=["0.5", "0.75", "1.0"], default="0.75")
    ap.add_argument("--opp-dir", type=Path, default=OPP_DIR)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()

    ann_dir = csv_dir(args.opp_dir, args.source, args.threshold)
    if not ann_dir.is_dir():
        sys.exit(f"ERROR: annotation dir not found: {ann_dir}")
    errant = load_errant_ann_ids(args.opp_dir)
    csv_files = sorted(ann_dir.glob("*.csv"))

    records: list[dict] = []
    per_label: dict[str, int] = {}
    n_span = n_match = n_mismatch = n_skip_val = n_missing_seg = 0
    mismatches: list[tuple] = []

    for csv_path in csv_files:
        stem = csv_path.stem
        segs = segments_for(args.opp_dir, stem)
        if segs is None:
            continue
        for row in csv.reader(csv_path.open(encoding="utf-8")):
            if len(row) < 9:
                continue
            if row[C_CATEGORY] in DROP_CATEGORIES:
                continue
            ann_id = row[C_ANN_ID]
            if ann_id in errant:            # known-buggy offsets
                continue
            try:
                seg_id = int(row[C_SEGMENT])
                attrs = json.loads(row[C_ATTRS])
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
            if not isinstance(attrs, dict):
                continue
            for attr, d in attrs.items():
                label = LABEL_MAP.get(attr)
                if label is None or not isinstance(d, dict):
                    continue
                value = d.get("value")
                if value in DROP_VALUES:
                    n_skip_val += 1
                    continue
                start, end, text = d.get("startIndexInSegment"), d.get("endIndexInSegment"), d.get("selectedText")
                if not (isinstance(start, int) and isinstance(end, int) and isinstance(text, str)):
                    continue
                if start < 0 or end <= start:   # no real span selected
                    continue
                if seg_id >= len(segs):
                    n_missing_seg += 1
                    continue
                seg = segs[seg_id]
                recon = seg[start:end]
                n_span += 1
                if recon != text:
                    # Tolerate leading/trailing-whitespace offset drift (a known OPP-115 quirk):
                    # re-align to the trimmed span and re-verify. Interior differences still fail.
                    stripped = text.strip()
                    if stripped and recon.strip() == stripped:
                        lead = len(recon) - len(recon.lstrip())
                        ns = start + lead
                        ne = ns + len(stripped)
                        if seg[ns:ne] == stripped:
                            start, end, text, recon = ns, ne, stripped, stripped
                if recon == text:
                    n_match += 1
                    records.append({
                        "source_dataset": "OPP-115",
                        "policy_id": stem,
                        "segment_id": seg_id,
                        "label": label,
                        "text": text,
                        "seg_start": start,
                        "seg_end": end,
                        "value": value,
                        "category": row[C_CATEGORY],
                        "annotator_id": row[C_ANNOTATOR],
                        "annotation_id": ann_id,
                    })
                    per_label[label] = per_label.get(label, 0) + 1
                else:
                    n_mismatch += 1
                    if len(mismatches) < 10:
                        mismatches.append((stem, seg_id, attr, text, recon))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    match_rate = (n_match / n_span) if n_span else 0.0
    print(f"\n=== OPP-115 loader ({args.source}, threshold {args.threshold}) ===")
    print(f"policies processed : {len(csv_files)}")
    print(f"spans kept (match) : {n_match}")
    print(f"per-label          : {per_label}")
    print(f"skipped (Unspecified/not-selected): {n_skip_val}")
    print(f"missing-segment    : {n_missing_seg}")
    print(f"offset mismatches  : {n_mismatch}  (match rate {match_rate:.4f})")
    print(f"wrote              : {args.out.relative_to(PROJECT_ROOT)}  ({len(records)} records)")

    print("\n--- reconstruction spot-check (first 20 kept spans) ---")
    for r in records[:20]:
        print(f"  [{r['label']:11}] {r['text'][:60]!r}")
    if mismatches:
        print("\n--- sample mismatches (selectedText vs reconstructed) ---")
        for stem, seg, attr, text, recon in mismatches:
            print(f"  {stem} seg{seg} {attr}: {text[:40]!r} != {recon[:40]!r}")

    # ---- GATE ----
    if n_span == 0:
        sys.exit("GATE FAILED: no spans produced — check paths/format.")
    if match_rate < GATE_MIN_MATCH_RATE:
        sys.exit(f"GATE FAILED: match rate {match_rate:.4f} < {GATE_MIN_MATCH_RATE}. "
                 "Offset/segmentation logic is wrong — do NOT use this output.")
    print(f"\nGATE PASSED: {n_match} spans, match rate {match_rate:.4f} >= {GATE_MIN_MATCH_RATE}.")


if __name__ == "__main__":
    main()
