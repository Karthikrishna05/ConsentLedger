"""AA gold (gold.json) + split (aa_split.json) -> word-level BIO CoNLL, same format as the OPP-115 files.

    data/ner_bio/aa_test.conll   + aa_test.docmap.json     (the sealed test set)
    data/ner_bio/aa_adapt.conll  + aa_adapt.docmap.json    (E2 adaptation data, all 14 documents)
    data/ner_bio/aa_adapt_train.conll / aa_adapt_dev.conll (the same data split for E2 training, D61:
                                                            dev = ADAPT_DEV, used only to stop training)

An AA document is one long text; the models read at most 256 sub-word pieces at a time and the trainer
TRUNCATES anything longer - which would silently drop gold entities. So each document is cut into SEGMENTS:
  - at a sentence end (. ; or a line break), never inside a gold span;
  - closed at the first such boundary after TARGET tokens, and force-closed at MAX tokens (long lists), still
    never inside a span.
OPP-115 segments are paragraphs of comparable size (median 83 tokens), so E1 sees familiar-length input.

The docmap lists the document of every segment, in order - evaluation bootstraps over DOCUMENT GROUPS, not
segments. Every gold span is checked to come back out of the BIO tags unchanged.

    python -m consentledger.data.aa_to_conll
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from consentledger.data.aa_split import GLUED
from consentledger.data.bio_tagging import bio_for_segment, reconstruct, tokenize_with_offsets

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GOLD = PROJECT_ROOT / "data" / "aa" / "annotated" / "gold.json"
SPLIT = PROJECT_ROOT / "data" / "splits" / "aa_split.json"
OUT_DIR = PROJECT_ROOT / "data" / "ner_bio"
TARGET, MAX = 60, 100          # tokens; 100 word-tokens stays well inside 256 sub-word pieces
# E2's "mock test" (D61, revised D62): the adaptation documents that share the LEAST text with the ones left in
# training (at most 18% - aa_split.similarity), about 100 entities, no glued-text document. The earlier pick
# 09_saafe_terms is 75% identical to 16_oms_aa_privacy, which trains - a memory test, not a mock test.
ADAPT_DEV = ("01_setu_aa_terms", "19_saafe_privacy", "20_scoremeaa_charter", "22_setu_aa_charter")


def segment(text: str, spans: list[tuple[int, int, str]]) -> list[tuple[int, int]]:
    """Character ranges (start, end) of the segments of one document."""
    toks = tokenize_with_offsets(text)
    if not toks:
        return []

    def inside(pos: int) -> bool:                       # a cut at `pos` would split a gold span
        return any(s < pos < e for s, e, _ in spans)

    cuts, start, n, last_ok = [], 0, 0, None
    for i, (word, ts, te) in enumerate(toks):
        n += 1
        nxt = toks[i + 1][1] if i + 1 < len(toks) else len(text)
        if not inside(te) and not inside(nxt):
            last_ok = (i, te)
        sentence_end = word in ".;" or "\n" in text[te:nxt]
        if (n >= TARGET and sentence_end and last_ok and last_ok[0] == i) or n >= MAX:
            if last_ok is None:                         # a single span longer than MAX tokens - keep it whole
                continue
            cuts.append((start, last_ok[1]))
            start = toks[last_ok[0] + 1][1] if last_ok[0] + 1 < len(toks) else len(text)
            n = i - last_ok[0]
            last_ok = None
    if start < len(text) and text[start:].strip():
        cuts.append((start, len(text)))
    return cuts


def convert(doc: dict) -> list[list[tuple[str, str]]]:
    text = doc["text"]
    spans = [(s["start"], s["end"], s["label"]) for s in doc["spans"]]
    out = []
    for a, b in segment(text, spans):
        local = [{"seg_start": s - a, "seg_end": e - a, "label": lab} for s, e, lab in spans if a <= s and e <= b]
        rows = bio_for_segment(text[a:b], local)
        if rows:
            out.append(rows)
    return out


def write(name: str, docs: list[dict], out_dir: Path) -> dict:
    stats, docmap, lens = Counter(), [], []
    with (out_dir / f"{name}.conll").open("w", encoding="utf-8") as fh:
        for doc in docs:
            segs = convert(doc)
            got = Counter(lab for rows in segs for lab, _ in reconstruct(rows))
            want = Counter(s["label"] for s in doc["spans"])
            if got != want:                             # a span was lost, split or merged
                # Only possible where two spans sit inside one glued "word" (D36) - which is why those
                # documents are barred from the test set. Anywhere else it is a bug.
                assert doc["doc_id"] in GLUED, (doc["doc_id"], dict(want), dict(got))
                lost = sum((want - got).values())
                stats["lost_in_glued_words"] += lost
                print(f"  note {doc['doc_id']}: {lost} span(s) share a glued word with another and cannot be "
                      "tagged separately")
                want = got
            for rows in segs:
                fh.write("".join(f"{w}\t{t}\n" for w, t in rows) + "\n")
                docmap.append(doc["doc_id"])
                lens.append(len(rows))
            stats.update(want)
            stats["tokens"] += sum(len(r) for r in segs)
    (out_dir / f"{name}.docmap.json").write_text(json.dumps(docmap), encoding="utf-8")
    lost = stats.pop("lost_in_glued_words", 0)
    return {"docs": len(docs), "segments": len(lens), "tokens": stats.pop("tokens"), "max_segment": max(lens),
            "lost_in_glued_words": lost,
            "median_segment": sorted(lens)[len(lens) // 2], "entities": dict(stats)}


def main() -> None:
    ap = argparse.ArgumentParser(description="AA gold -> BIO CoNLL (test + adaptation).")
    ap.add_argument("--gold", type=Path, default=GOLD)
    ap.add_argument("--split", type=Path, default=SPLIT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    gold = {d["doc_id"]: d for d in json.loads(args.gold.read_text(encoding="utf-8"))}
    split = json.loads(args.split.read_text(encoding="utf-8"))
    assert set(split["test"]) | set(split["adapt"]) == set(gold) and not set(split["test"]) & set(split["adapt"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    assert set(ADAPT_DEV) <= set(split["adapt"]) and not set(ADAPT_DEV) & set(GLUED)
    sets = {"aa_test": split["test"], "aa_adapt": split["adapt"], "aa_adapt_dev": list(ADAPT_DEV),
            "aa_adapt_train": [d for d in split["adapt"] if d not in ADAPT_DEV]}
    for name, docs in sets.items():
        s = write(name, [gold[d] for d in docs], args.out_dir)
        print(f"{name}: {s['docs']} docs, {s['segments']} segments (median {s['median_segment']}, max "
              f"{s['max_segment']} tokens), {s['tokens']} tokens, entities {s['entities']}")
        assert s["max_segment"] <= MAX + 40, "a segment is too long for the 256 sub-word window"


def _selfcheck() -> None:
    sent = "We collect your bank statements and mutual fund holdings for credit assessment. "
    text = sent * 12
    spans = []
    for k in range(12):
        o = k * len(sent)
        spans += [(o + sent.index("bank"), o + sent.index("bank") + 15, "DATA_TYPE"),
                  (o + sent.index("mutual"), o + sent.index("mutual") + 20, "DATA_TYPE"),
                  (o + sent.index("credit"), o + sent.index("credit") + 17, "PURPOSE")]
    segs = segment(text, spans)
    assert len(segs) > 1 and all(not any(s < b < e for s, e, _ in spans) for _, b in segs)   # never inside a span
    assert all(len(tokenize_with_offsets(text[a:b])) <= MAX for a, b in segs)
    doc = {"doc_id": "d", "text": text, "spans": [{"start": s, "end": e, "label": lab} for s, e, lab in spans]}
    ents = [x for rows in convert(doc) for x in reconstruct(rows)]
    assert Counter(lab for lab, _ in ents) == {"DATA_TYPE": 24, "PURPOSE": 12}, Counter(lab for lab, _ in ents)
    assert ("DATA_TYPE", "bank statements") in ents and ("PURPOSE", "credit assessment") in ents
    # one unbroken list longer than MAX tokens is force-cut, but outside the span that sits in it
    long_ = "items " + ", ".join(f"thing{i}" for i in range(150)) + " and the Permanent Account Number here"
    ps = long_.index("Permanent")
    cuts = segment(long_, [(ps, ps + 24, "DATA_TYPE")])
    assert len(cuts) >= 2 and all(not (ps < b < ps + 24) for _, b in cuts)
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
