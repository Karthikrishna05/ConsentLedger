"""Trim OPP-115's long clause-spans down to concise noun-phrase entities, the AA span shape.

Long spans (PURPOSE median ~14 tokens) teach the wrong shape. Each span becomes its longest spaCy noun chunk
(head-final, capped at --max-tokens), else its last --max-tokens tokens. Writes a SEPARATE file with offsets
recomputed; the original span is kept in orig_* fields.

Usage:
    python -m consentledger.data.trim_spans                 # max 6 tokens (default)
    python -m consentledger.data.trim_spans --max-tokens 5
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
IN_DEFAULT = PROJECT_ROOT / "data" / "external" / "opp115" / "processed" / "opp115_spans.jsonl"
OUT_DEFAULT = PROJECT_ROOT / "data" / "external" / "opp115" / "processed" / "opp115_spans_trimmed.jsonl"


def _choose(doc, max_tokens: int):
    """Return (start_char, end_char) within the span text for the trimmed entity, or None."""
    chunks = list(doc.noun_chunks)
    if chunks:
        ch = max(chunks, key=lambda c: c.end - c.start)      # longest noun chunk
        toks = [t for t in ch if not t.is_space]
        if len(toks) > max_tokens:
            toks = toks[-max_tokens:]                          # head-final trim
        if toks:
            return toks[0].idx, toks[-1].idx + len(toks[-1])
    toks = [t for t in doc if not t.is_space]                  # no noun chunk -> last N tokens
    if not toks:
        return None
    sel = toks[-max_tokens:]
    return sel[0].idx, sel[-1].idx + len(sel[-1])


def main() -> None:
    ap = argparse.ArgumentParser(description="Trim OPP-115 spans to concise noun phrases (separate file).")
    ap.add_argument("--in", dest="inp", type=Path, default=IN_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--max-tokens", type=int, default=6)
    args = ap.parse_args()

    if not args.inp.is_file():
        raise SystemExit(f"Missing {args.inp}. Run load_opp115 first.")

    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])

    records = [json.loads(ln) for ln in args.inp.read_text(encoding="utf-8").splitlines() if ln.strip()]
    texts = [r["text"] for r in records]

    out, dropped = [], 0
    before_len, after_len = [], []
    for r, doc in zip(records, nlp.pipe(texts, batch_size=256)):
        before_len.append(len([t for t in doc if not t.is_space]))
        res = _choose(doc, args.max_tokens)
        if res is None:
            dropped += 1
            continue
        s, e = res
        trimmed = doc.text[s:e]
        if not trimmed.strip():
            dropped += 1
            continue
        rec = dict(r)
        rec["orig_text"], rec["orig_seg_start"], rec["orig_seg_end"] = r["text"], r["seg_start"], r["seg_end"]
        rec["seg_start"] = r["seg_start"] + s
        rec["seg_end"] = r["seg_start"] + e
        rec["text"] = trimmed
        after_len.append(len(trimmed.split()))
        out.append(rec)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"=== trim_spans (max {args.max_tokens} tokens) ===")
    print(f"in : {args.inp.name}  ({len(records)} spans)")
    print(f"out: {args.out.name}  ({len(out)} spans, {dropped} dropped)")
    print(f"span length (tokens)  before: median {int(st.median(before_len))}, "
          f"p90 {sorted(before_len)[int(len(before_len)*0.9)]}, max {max(before_len)}")
    print(f"                       after: median {int(st.median(after_len))}, "
          f"p90 {sorted(after_len)[int(len(after_len)*0.9)]}, max {max(after_len)}")
    # spot-check: show a few trims
    print("\n--- sample trims (orig -> trimmed) ---")
    for rec in out[:8]:
        print(f"  [{rec['label']:11}] {rec['orig_text'][:55]!r}  ->  {rec['text']!r}")


if __name__ == "__main__":
    main()
