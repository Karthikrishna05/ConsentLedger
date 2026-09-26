"""Per-annotator fix lists: tell EACH annotator exactly what to change, where, in their own export.

adjudicate.py produces a JOINT worklist - it assumes P1 and P4 sit together and decide 1,351 items.
This module instead produces ONE FILE PER ANNOTATOR PER DOCUMENT, so both can work alone, in parallel,
in their own Label Studio project. After both apply their fixes and re-export, agreement should jump
because most one-sided spans are simply the other person's omission.

Each annotator's list has five buckets, ordered easiest-and-most-certain first:

  1. DELETE       - your span breaks Rule 8 (stoplist) or Rule 8b (AA roles). Certain, no judgement.
  2. ADD_REPEAT   - you marked this phrase elsewhere IN THIS SAME DOCUMENT but skipped this occurrence.
                    Your own inconsistency (Rule 7). Certain, no judgement.
  3. ADD_MISSED   - this phrase is in the corpus consensus lexicon (BOTH of you endorse it somewhere),
                    it appears here, and you did not mark it. High confidence.
  4. SHORTEN      - the other annotator marked a shorter version of your span; Rule 1 prefers shorter.
  5. SELF_CHECK   - a phrase only YOU ever use anywhere in the corpus. Re-read it against the Rule 8
                    test ("could I point to this in a real bank record, or name a real organisation?").
                    This is the only bucket needing judgement.

Buckets 1-3 are mechanical and carry exact character offsets, so they are fast to apply.

Usage:
    python -m consentledger.data.fixlist --corpus data/aa/annotated/ls_import_tasks.json \\
        --a data/aa/annotated/ExportA.json --b data/aa/annotated/ExportB.json \\
        --name-a P1 --name-b P4
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from consentledger.data.adjudicate import DROP
from consentledger.data.annotation_audit import (
    build_consensus_lexicon, find_occurrences, load_corpus, norm,
)
from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")


def _covered(spans, i, j) -> bool:
    return any(s < j and i < e for s, e, _ in spans)


def fixes_for(text, mine, theirs, lexicon, own_vocab, both_vocab):
    """Build one annotator's fix buckets for one document."""
    out = defaultdict(list)

    # 1. DELETE - rule violations in my own spans
    keep = []
    for sp in mine:
        phrase = norm(text[sp[0]:sp[1]])
        if phrase in DROP:
            out["DELETE"].append((sp, phrase))
        else:
            keep.append(sp)

    # 2. ADD_REPEAT - phrases I marked in THIS doc, at occurrences I skipped
    my_phrases = {}
    for s, e, lab in keep:
        p = norm(text[s:e])
        if len(p) >= 4 and p not in DROP:
            my_phrases.setdefault(p, lab)
    if my_phrases:
        for i, j, term in find_occurrences(text, sorted(my_phrases, key=len, reverse=True)):
            if not _covered(keep, i, j):
                out["ADD_REPEAT"].append(((i, j, my_phrases[term]), term))

    # 3. ADD_MISSED - consensus-lexicon phrases present here that I never marked
    already = {norm(text[s:e]) for s, e, _ in keep}
    cand = [p for p in lexicon if p not in already and p not in DROP and len(p) >= 4]
    seen = {(i, j) for (i, j, _), _ in out["ADD_REPEAT"]}
    for i, j, term in find_occurrences(text, sorted(cand, key=len, reverse=True)):
        if not _covered(keep, i, j) and (i, j) not in seen:
            out["ADD_MISSED"].append(((i, j, lexicon[term]), term))

    # 4. SHORTEN - they marked a shorter version of my span, same label
    for sp in keep:
        for tp in theirs:
            if sp[2] == tp[2] and sp[0] < tp[1] and tp[0] < sp[1] and (tp[1] - tp[0]) < (sp[1] - sp[0]):
                out["SHORTEN"].append((sp, tp, text[sp[0]:sp[1]], text[tp[0]:tp[1]]))
                break

    # 5. SELF_CHECK - vocabulary only I ever use corpus-wide
    for sp in keep:
        p = norm(text[sp[0]:sp[1]])
        if p in own_vocab and p not in both_vocab:
            out["SELF_CHECK"].append((sp, p))
    return out


def _render(name, doc, text, buckets) -> str:
    n_mech = len(buckets["DELETE"]) + len(buckets["ADD_REPEAT"]) + len(buckets["ADD_MISSED"])
    md = [f"# {name} — fix list for `{doc}`", "",
          f"**{n_mech} mechanical fixes** (no judgement needed) + {len(buckets['SHORTEN'])} to shorten "
          f"+ {len(buckets['SELF_CHECK'])} to re-read.", "",
          "Offsets are character positions — use them to find the spot fast.", ""]
    if buckets["DELETE"]:
        md += [f"## 1. DELETE these {len(buckets['DELETE'])} — they break Rule 8 / 8b", ""]
        c = Counter(p for _, p in buckets["DELETE"])
        md += [f"Summary: " + ", ".join(f"`{p}` x{n}" for p, n in c.most_common(15)), ""]
        md += [f"- `{p}` **{sp[2]}** `[{sp[0]}:{sp[1]}]`" for sp, p in buckets["DELETE"][:150]]
    if buckets["ADD_REPEAT"]:
        md += ["", f"## 2. ADD these {len(buckets['ADD_REPEAT'])} — you marked this phrase elsewhere in "
               "THIS doc but skipped these (Rule 7)", ""]
        c = Counter(t for _, t in buckets["ADD_REPEAT"])
        md += [f"Summary: " + ", ".join(f"`{p}` x{n}" for p, n in c.most_common(15)), ""]
        md += [f"- `{t}` → **{sp[2]}** `[{sp[0]}:{sp[1]}]`" for sp, t in buckets["ADD_REPEAT"][:200]]
    if buckets["ADD_MISSED"]:
        md += ["", f"## 3. ADD these {len(buckets['ADD_MISSED'])} — both of you endorse this phrase "
               "elsewhere; it appears here and you left it blank", ""]
        for lab in LABELS:
            items = [(sp, t) for sp, t in buckets["ADD_MISSED"] if sp[2] == lab]
            if items:
                md.append(f"**{lab}** ({len(items)}):")
                md += [f"  - `{t}` `[{sp[0]}:{sp[1]}]`" for sp, t in items[:120]]
    if buckets["SHORTEN"]:
        md += ["", f"## 4. SHORTEN these {len(buckets['SHORTEN'])} (Rule 1 — shortest phrase that still "
               "makes sense)", ""]
        md += [f"- yours `{a}` `[{sp[0]}:{sp[1]}]` → use `{b}`" for sp, tp, a, b in buckets["SHORTEN"][:120]]
    if buckets["SELF_CHECK"]:
        md += ["", f"## 5. RE-READ these {len(buckets['SELF_CHECK'])} — only you ever mark this phrase "
               "anywhere in the corpus", "",
               "*Test: could I point to this in a real bank record, or name a real organisation?* "
               "If no → delete it.", ""]
        c = Counter(p for _, p in buckets["SELF_CHECK"])
        md += [f"- `{p}` x{n}" for p, n in c.most_common(60)]
    return "\n".join(md)


def main() -> None:
    ap = argparse.ArgumentParser(description="Per-annotator fix lists.")
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    ap.add_argument("--name-a", default="P1")
    ap.add_argument("--name-b", default="P4")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "results" / "annotation" / "fixlist")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    A, B = load_ls_export(args.a), load_ls_export(args.b)
    docs = sorted(set(corpus) & set(A) & set(B))
    lexicon = build_consensus_lexicon(A, B, min_count=1, multiword=False, drop_generic=True)

    def vocab(X):
        return {norm(d["text"][s:e]) for d in X.values() for s, e, _ in d["spans"]}
    va, vb = vocab(A), vocab(B)
    both = va & vb

    totals = {args.name_a: Counter(), args.name_b: Counter()}
    per_doc = {args.name_a: {}, args.name_b: {}}
    for name, X, Y, own in ((args.name_a, A, B, va), (args.name_b, B, A, vb)):
        d = args.out / name
        d.mkdir(parents=True, exist_ok=True)
        for key in docs:
            text = corpus[key]
            buckets = fixes_for(text, X[key]["spans"], Y[key]["spans"], lexicon, own, both)
            (d / f"{key}.md").write_text(_render(name, key, text, buckets), encoding="utf-8")
            counts = {k: len(v) for k, v in buckets.items()}
            per_doc[name][key] = counts
            totals[name].update(counts)

    md = ["# Per-annotator fix lists", "",
          "Each annotator works **alone, in parallel**, on their own file. Buckets 1-3 are mechanical "
          "(exact offsets, no judgement); 4-5 are quick reads.", ""]
    for name in (args.name_a, args.name_b):
        t = totals[name]
        mech = t["DELETE"] + t["ADD_REPEAT"] + t["ADD_MISSED"]
        md += [f"## {name} — {mech} mechanical fixes, {t['SHORTEN']} shorten, {t['SELF_CHECK']} re-read", "",
               f"- DELETE (rule violations): **{t['DELETE']}**",
               f"- ADD_REPEAT (own inconsistency, Rule 7): **{t['ADD_REPEAT']}**",
               f"- ADD_MISSED (consensus phrase left blank): **{t['ADD_MISSED']}**",
               f"- SHORTEN: {t['SHORTEN']}", f"- SELF_CHECK: {t['SELF_CHECK']}", "",
               "| doc | delete | add-repeat | add-missed | shorten | self-check |", "|---|---|---|---|---|---|"]
        for key in docs:
            c = per_doc[name][key]
            md.append(f"| {key} | {c.get('DELETE',0)} | {c.get('ADD_REPEAT',0)} | {c.get('ADD_MISSED',0)} "
                      f"| {c.get('SHORTEN',0)} | {c.get('SELF_CHECK',0)} |")
        md.append("")
    (args.out / "README.md").write_text("\n".join(md), encoding="utf-8")

    for name in (args.name_a, args.name_b):
        t = totals[name]
        mech = t["DELETE"] + t["ADD_REPEAT"] + t["ADD_MISSED"]
        print(f"{name}: {mech} mechanical (delete {t['DELETE']}, +repeat {t['ADD_REPEAT']}, "
              f"+missed {t['ADD_MISSED']}), shorten {t['SHORTEN']}, self-check {t['SELF_CHECK']}")
    print(f"wrote {(args.out / 'README.md').relative_to(PROJECT_ROOT)} + {args.name_a}/*.md + {args.name_b}/*.md")


def _selfcheck() -> None:
    text = "We collect bank statements for loans. Third parties get bank statements too."
    bs, tp = text.index("bank statements"), text.index("Third parties")
    mine = [(bs, bs + 15, "DATA_TYPE"), (tp, tp + 13, "THIRD_PARTY")]
    out = fixes_for(text, mine, [], {"bank statements": "DATA_TYPE"},
                    {"bank statements", "third parties"}, {"bank statements"})
    assert len(out["DELETE"]) == 1, out            # 'Third parties' -> Rule 8
    assert len(out["ADD_REPEAT"]) == 1, out        # 2nd 'bank statements' skipped
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
