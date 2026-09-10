"""Turn OPP-115 span records into word-level BIO CoNLL (train/dev for the E1 transfer experiment).

Design (see meta-documentation/DECISIONS.md D18):
- **Word-level** CoNLL, tokenizer-AGNOSTIC: one dataset shared by all 3 backbones. Each model's own
  subword tokenizer aligns to these words at train time (dataset.py, first-subword=label, rest=-100).
  This keeps the "offset-based, no cross-tokenizer subword reuse" guarantee (D7) while avoiding a
  per-model regeneration of the data.
- Word tokenization is offset-aware (regex over the segment text), never a naive whitespace `.split()`
  that loses character positions.
- Unit of a training example = one policy **segment** (the text an annotator saw). ALL segments are
  emitted, including negatives (all `O`), so the model also learns what is NOT an entity.
- Overlapping spans of different labels are resolved **longest-span-wins** (documented, deterministic).
- Split is at the **policy level** (never segment level) to avoid leakage between train and dev.

Input : data/external/opp115/processed/opp115_spans.jsonl  (+ sanitized_policies for segment text)
Output: data/ner_bio/train.conll , data/ner_bio/dev.conll   (word <TAB> tag ; blank line between segments)

Usage:
    python -m consentledger.data.bio_tagging                 # OPP-115, 90/10 policy split, seed 42
    python -m consentledger.data.bio_tagging --dev-frac 0.15
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPANS_JSONL = PROJECT_ROOT / "data" / "external" / "opp115" / "processed" / "opp115_spans.jsonl"
SANITIZED = PROJECT_ROOT / "data" / "external" / "opp115" / "raw" / "OPP-115" / "sanitized_policies"
OUT_DIR = PROJECT_ROOT / "data" / "ner_bio"
SEGMENT_DELIM = "|||"

# Word tokenizer: word-characters OR a single non-space/non-word char (keeps punctuation as its own
# token, with exact character offsets). Deterministic and model-independent.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def resolve_overlaps(spans: list[dict]) -> list[dict]:
    """Longest-span-wins: greedily keep longer spans, drop any that overlap an already-kept one."""
    kept: list[dict] = []
    for s in sorted(spans, key=lambda d: (d["seg_end"] - d["seg_start"]), reverse=True):
        if any(not (s["seg_end"] <= k["seg_start"] or s["seg_start"] >= k["seg_end"]) for k in kept):
            continue
        kept.append(s)
    return sorted(kept, key=lambda d: d["seg_start"])


def bio_for_segment(text: str, spans: list[dict]) -> list[tuple[str, str]]:
    """Return [(word, tag)] for one segment. Tag = B-/I-<LABEL> or O."""
    toks = tokenize_with_offsets(text)
    tags = ["O"] * len(toks)
    for span in resolve_overlaps(spans):
        first = True
        for i, (_, ts, te) in enumerate(toks):
            if ts < span["seg_end"] and te > span["seg_start"]:   # token overlaps span
                tags[i] = ("B-" if first else "I-") + span["label"]
                first = False
    return [(t[0], tag) for t, tag in zip(toks, tags)]


def load_opp115_segments() -> dict[str, dict[int, dict]]:
    """policy_id -> {segment_id -> {"text": str, "spans": [span, ...]}}, ALL segments incl. negatives."""
    spans_by_key: dict[tuple[str, int], list[dict]] = defaultdict(list)
    policies: set[str] = set()
    with SPANS_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            spans_by_key[(r["policy_id"], r["segment_id"])].append(r)
            policies.add(r["policy_id"])

    out: dict[str, dict[int, dict]] = {}
    for pid in sorted(policies):
        p = SANITIZED / f"{pid}.html"
        if not p.is_file():
            continue
        segs = p.read_text(encoding="utf-8").split(SEGMENT_DELIM)
        out[pid] = {
            i: {"text": seg, "spans": spans_by_key.get((pid, i), [])}
            for i, seg in enumerate(segs)
            if seg.strip()  # skip empty segments
        }
    return out


def write_conll(path: Path, policies: list[str], data: dict[str, dict[int, dict]]) -> tuple[int, int, dict]:
    n_seg = n_tok = 0
    per_label: dict[str, int] = defaultdict(int)
    with path.open("w", encoding="utf-8") as fh:
        for pid in policies:
            for seg_id in sorted(data[pid]):
                rec = data[pid][seg_id]
                rows = bio_for_segment(rec["text"], rec["spans"])
                if not rows:
                    continue
                for word, tag in rows:
                    fh.write(f"{word}\t{tag}\n")
                    n_tok += 1
                    if tag.startswith("B-"):
                        per_label[tag[2:]] += 1
                fh.write("\n")
                n_seg += 1
    return n_seg, n_tok, dict(per_label)


def reconstruct(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Rebuild entities from BIO rows -> [(label, surface)] for the self-check."""
    ents, cur, lab = [], [], None
    for word, tag in rows:
        if tag.startswith("B-"):
            if cur:
                ents.append((lab, " ".join(cur)))
            cur, lab = [word], tag[2:]
        elif tag.startswith("I-") and lab == tag[2:]:
            cur.append(word)
        else:
            if cur:
                ents.append((lab, " ".join(cur)))
            cur, lab = [], None
    if cur:
        ents.append((lab, " ".join(cur)))
    return ents


def main() -> None:
    ap = argparse.ArgumentParser(description="OPP-115 spans -> word-level BIO CoNLL.")
    ap.add_argument("--dev-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    if not SPANS_JSONL.is_file():
        raise SystemExit(f"Missing {SPANS_JSONL} — run consentledger.data.load_opp115 first.")

    data = load_opp115_segments()
    policies = sorted(data)
    rng = random.Random(args.seed)
    rng.shuffle(policies)
    n_dev = max(1, round(len(policies) * args.dev_frac))
    dev_p, train_p = policies[:n_dev], policies[n_dev:]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tr = write_conll(args.out_dir / "train.conll", train_p, data)
    dv = write_conll(args.out_dir / "dev.conll", dev_p, data)

    print("=== bio_tagging (OPP-115 -> word-level BIO CoNLL) ===")
    print(f"policies: {len(policies)}  ->  train {len(train_p)} / dev {len(dev_p)} (seed {args.seed})")
    print(f"train: {tr[0]} segments, {tr[1]} tokens, entities/label {tr[2]}")
    print(f"dev  : {dv[0]} segments, {dv[1]} tokens, entities/label {dv[2]}")
    print(f"wrote: {(args.out_dir / 'train.conll').relative_to(PROJECT_ROOT)} , "
          f"{(args.out_dir / 'dev.conll').relative_to(PROJECT_ROOT)}")

    # ---- self-check: reconstruct entities from a segment that has spans and eyeball ----
    print("\n--- self-check: reconstructed entities from BIO (first segment with >=2 entities) ---")
    for pid in train_p:
        for seg_id in sorted(data[pid]):
            rec = data[pid][seg_id]
            rows = bio_for_segment(rec["text"], rec["spans"])
            ents = reconstruct(rows)
            if len(ents) >= 2:
                for lab, surface in ents[:6]:
                    print(f"  [{lab:11}] {surface[:60]!r}")
                # assert reconstructed labels are a subset of what we put in
                in_labels = {s["label"] for s in resolve_overlaps(rec["spans"])}
                out_labels = {lab for lab, _ in ents}
                assert out_labels <= in_labels, f"label leak: {out_labels - in_labels}"
                print("  self-check OK (reconstructed labels subset of input).")
                return


if __name__ == "__main__":
    main()
