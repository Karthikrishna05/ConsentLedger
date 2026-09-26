"""Turn the A/B disagreements into a per-document adjudication worklist + a proposed gold corpus.

Most of the round-1 gap is now MECHANICALLY decidable under guideline v4 (Rules 7, 8, 8b), so it should
not cost human time. This applies every rule that can be applied automatically, and leaves humans only
the genuinely ambiguous cases.

Decision procedure, per document (start from the union of A and B spans):

  1. DELETE (Rule 8 / 8b)  - span text is a stoplist umbrella term, or an AA-framework role/regulator.
                             Auto, no review.
  2. ACCEPT (agreement)    - both annotators marked the same offsets and label. Auto.
  3. ACCEPT (consensus)    - only one annotator marked it here, BUT the phrase+label is in the corpus
                             consensus lexicon (both endorsed it somewhere else). The other simply
                             missed it. Auto.
  4. REVIEW (label)        - overlapping spans, different labels. Human must choose. (Rare: ~7 total.)
  5. REVIEW (boundary)     - overlapping, same label, different edges. Proposes the SHORTER span per
                             Rule 1, flagged for a quick human yes/no.
  6. REVIEW (one-sided)    - only one annotator ever uses this phrase anywhere. Human must judge.
  7. ADD (Rule 7)          - once a phrase is accepted for a document, every other occurrence of it in
                             that same document is added. This is the repeat-marking fix, applied
                             automatically so annotators never have to hunt repeats again.

Outputs (default results/annotation/adjudication/):
    worklist.md               how much human review is left, per document
    worklist/<doc_id>.md      the human's actual to-do list (only the REVIEW items need reading)
    proposed_gold/<id>.json   offsets + labels only (no document text) -> safe to commit

Usage:
    python -m consentledger.data.adjudicate --corpus data/aa/annotated/ls_import_tasks.json \
        --a data/aa/annotated/ExportA.json --b data/aa/annotated/ExportB.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from consentledger.data.annotation_audit import (
    build_consensus_lexicon, find_occurrences, load_corpus, norm,
)
from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Rule 8 - umbrella / generic terms that are never entities.
STOPLIST = {
    "information", "data", "personal data", "personal information", "financial information",
    "sensitive information", "your details", "such details", "the information", "related information",
    "third parties", "third party", "other parties", "partners", "partner", "agencies", "bodies",
    "services", "the services", "our services", "the platform", "provision of the services",
    "business purposes", "lawful purposes", "other purposes", "related purposes", "as required",
    "reporting", "usage data", "profile", "market", "statistics", "suggestions", "feedback",
    "cookie", "cookies", "pixels", "device identifiers", "operating system", "version", "spi", "pii",
}
# Rule 8b - AA-framework roles and regulators are never THIRD_PARTY (and never anything else).
AA_ROLES = {
    "account aggregator", "aa", "financial information provider", "fip",
    "financial information user", "fiu", "reserve bank of india", "rbi", "sahamati",
    "consent artefact", "consent manager", "nbfc-aa",
}
DROP = STOPLIST | AA_ROLES


def _overlaps(a, b) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def adjudicate_doc(text, spans_a, spans_b, lexicon):
    """Return (gold_spans, actions) where actions is a list of (kind, detail) for the worklist."""
    actions = []
    sa, sb = set(spans_a), set(spans_b)

    def dropped(sp):
        return norm(text[sp[0]:sp[1]]) in DROP

    # 1. DELETE - stoplist / AA-role violations, whoever marked them
    deletes = [(sp, who) for who, S in (("A", sa), ("B", sb)) for sp in S if dropped(sp)]
    sa = {s for s in sa if not dropped(s)}
    sb = {s for s in sb if not dropped(s)}
    for sp, who in deletes:
        actions.append(("DELETE", (sp, who, norm(text[sp[0]:sp[1]]))))

    gold: set = set()

    # 2. ACCEPT - exact agreement
    for sp in sorted(sa & sb):
        gold.add(sp)
        actions.append(("ACCEPT_AGREED", (sp,)))

    rest_a, rest_b = sorted(sa - sb), sorted(sb - sa)

    # 4/5. pair up overlapping leftovers -> label or boundary conflicts
    matched_b, paired_a = set(), set()
    for x in rest_a:
        y = next((z for z in rest_b if z not in matched_b and _overlaps(x, z)), None)
        if y is None:
            continue
        matched_b.add(y)
        paired_a.add(x)
        if x[2] != y[2]:
            actions.append(("REVIEW_LABEL", (x, y, text[x[0]:x[1]], text[y[0]:y[1]])))
        else:
            shorter = x if (x[1] - x[0]) <= (y[1] - y[0]) else y
            gold.add(shorter)                      # Rule 1 default: the shorter span
            actions.append(("REVIEW_BOUNDARY", (x, y, shorter, text[shorter[0]:shorter[1]])))

    # 3/6. one-sided spans -> consensus lexicon decides, else human
    for sp, who in [(s, "A") for s in rest_a if s not in paired_a] + \
                   [(s, "B") for s in rest_b if s not in matched_b]:
        phrase = norm(text[sp[0]:sp[1]])
        if lexicon.get(phrase) == sp[2]:
            gold.add(sp)
            actions.append(("ACCEPT_CONSENSUS", (sp, who, phrase)))
        else:
            actions.append(("REVIEW_ONESIDED", (sp, who, phrase)))

    # 7. Rule 7 - propagate every accepted phrase to all its occurrences in this document
    accepted = {}
    for s, e, lab in gold:
        accepted.setdefault(norm(text[s:e]), lab)
    accepted = {p: l for p, l in accepted.items() if len(p) >= 4 and p not in DROP}
    if accepted:
        occ = find_occurrences(text, sorted(accepted, key=len, reverse=True))
        occ.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        last = -1
        for i, j, term in occ:
            if i < last:
                continue
            last = j
            if not any(s < j and i < e for s, e, _ in gold):
                sp = (i, j, accepted[term])
                gold.add(sp)
                actions.append(("ADD_REPEAT", (sp, term)))

    return sorted(gold), actions


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the adjudication worklist + proposed gold.")
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "results" / "annotation" / "adjudication")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    A, B = load_ls_export(args.a), load_ls_export(args.b)
    docs = sorted(set(corpus) & set(A) & set(B))
    lexicon = build_consensus_lexicon(A, B, min_count=1, multiword=False, drop_generic=True)

    wl_dir, gold_dir = args.out / "worklist", args.out / "proposed_gold"
    wl_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    rows, grand = [], Counter()
    for key in docs:
        text = corpus[key]
        gold, actions = adjudicate_doc(text, A[key]["spans"], B[key]["spans"], lexicon)
        kinds = Counter(k for k, _ in actions)
        grand.update(kinds)
        review = kinds["REVIEW_LABEL"] + kinds["REVIEW_BOUNDARY"] + kinds["REVIEW_ONESIDED"]
        rows.append({"doc_id": key, "gold": len(gold), "review": review, **kinds})

        by = defaultdict(list)
        for k, d in actions:
            by[k].append(d)
        md = [f"# {key} — adjudication worklist", "",
              f"**Proposed gold: {len(gold)} spans.**  Automatic: "
              f"{kinds['ACCEPT_AGREED']} agreed + {kinds['ACCEPT_CONSENSUS']} consensus + "
              f"{kinds['ADD_REPEAT']} repeats added − {kinds['DELETE']} deleted.", "",
              f"## 👉 YOU ONLY NEED TO READ THIS: {review} items to decide", ""]
        if by["REVIEW_LABEL"]:
            md += [f"### Label conflict — pick one ({len(by['REVIEW_LABEL'])})", ""]
            md += [f"- `{ta}` : A says **{x[2]}**, B says **{y[2]}**  `[{x[0]}:{x[1]}]`"
                   for x, y, ta, tb in by["REVIEW_LABEL"]]
        if by["REVIEW_BOUNDARY"]:
            md += ["", f"### Boundary — shorter span taken by default, confirm ({len(by['REVIEW_BOUNDARY'])})", ""]
            md += [f"- **{sh[2]}** proposed `{t}`  (A `{x[0]}:{x[1]}` vs B `{y[0]}:{y[1]}`)"
                   for x, y, sh, t in by["REVIEW_BOUNDARY"][:120]]
        if by["REVIEW_ONESIDED"]:
            md += ["", f"### One-sided — only one annotator ever used this phrase ({len(by['REVIEW_ONESIDED'])})", ""]
            for lab in ("DATA_TYPE", "PURPOSE", "THIRD_PARTY"):
                items = [(sp, who, ph) for sp, who, ph in by["REVIEW_ONESIDED"] if sp[2] == lab]
                if items:
                    md.append(f"**{lab}** ({len(items)}):")
                    md += [f"  - `{ph}` — {who} only  `[{sp[0]}:{sp[1]}]`" for sp, who, ph in items[:80]]
                    if len(items) > 80:
                        md.append(f"  - …and {len(items) - 80} more")
        md += ["", "---", "", "## Applied automatically (no action needed)", ""]
        if by["DELETE"]:
            c = Counter(ph for _, _, ph in by["DELETE"])
            md += [f"**Deleted {len(by['DELETE'])} stoplist / AA-role spans:** " +
                   ", ".join(f"`{p}`x{n}" for p, n in c.most_common(20)), ""]
        if by["ADD_REPEAT"]:
            c = Counter(t for _, t in by["ADD_REPEAT"])
            md += [f"**Added {len(by['ADD_REPEAT'])} missed repeats (Rule 7):** " +
                   ", ".join(f"`{p}`x{n}" for p, n in c.most_common(20)), ""]
        if by["ACCEPT_CONSENSUS"]:
            md += [f"**Accepted {len(by['ACCEPT_CONSENSUS'])} one-sided spans** whose phrase both "
                   "annotators endorse elsewhere.", ""]
        (wl_dir / f"{key}.md").write_text("\n".join(md), encoding="utf-8")
        (gold_dir / f"{key}.json").write_text(
            json.dumps({"doc_id": key, "n_spans": len(gold),
                        "spans": [{"start": s, "end": e, "label": l} for s, e, l in gold]}, indent=1),
            encoding="utf-8")

    total_review = sum(r["review"] for r in rows)
    total_gold = sum(r["gold"] for r in rows)
    md = ["# Adjudication worklist — all documents", "",
          f"**Proposed gold: {total_gold} spans across {len(rows)} documents.**", "",
          f"- Resolved automatically: **{grand['ACCEPT_AGREED'] + grand['ACCEPT_CONSENSUS'] + grand['ADD_REPEAT'] + grand['DELETE']}**",
          f"  - agreed by both: {grand['ACCEPT_AGREED']}",
          f"  - accepted via consensus lexicon: {grand['ACCEPT_CONSENSUS']}",
          f"  - repeats added (Rule 7): {grand['ADD_REPEAT']}",
          f"  - deleted (Rules 8 / 8b): {grand['DELETE']}",
          f"- **Left for humans: {total_review}**"
          f"  (label {grand['REVIEW_LABEL']}, boundary {grand['REVIEW_BOUNDARY']}, one-sided {grand['REVIEW_ONESIDED']})",
          "", "## Per document — worst first (do these top-down)", "",
          "| doc | proposed gold | TO REVIEW | label | boundary | one-sided | auto-deleted | repeats added |",
          "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: -x["review"]):
        md.append(f"| {r['doc_id']} | {r['gold']} | **{r['review']}** | {r.get('REVIEW_LABEL',0)} | "
                  f"{r.get('REVIEW_BOUNDARY',0)} | {r.get('REVIEW_ONESIDED',0)} | "
                  f"{r.get('DELETE',0)} | {r.get('ADD_REPEAT',0)} |")
    md += ["", f"Per-document to-do lists: `{wl_dir.relative_to(PROJECT_ROOT)}/<doc_id>.md`",
           f"Proposed gold (offsets only): `{gold_dir.relative_to(PROJECT_ROOT)}/<doc_id>.json`"]
    (args.out / "worklist.md").write_text("\n".join(md), encoding="utf-8")

    print(f"=== adjudication over {len(rows)} docs ===")
    print(f"proposed gold spans : {total_gold}")
    print(f"auto-resolved       : agreed {grand['ACCEPT_AGREED']}, consensus {grand['ACCEPT_CONSENSUS']}, "
          f"repeats +{grand['ADD_REPEAT']}, deleted {grand['DELETE']}")
    print(f"HUMAN REVIEW LEFT   : {total_review}  (label {grand['REVIEW_LABEL']}, "
          f"boundary {grand['REVIEW_BOUNDARY']}, one-sided {grand['REVIEW_ONESIDED']})")
    print("\nper doc (worst first):")
    for r in sorted(rows, key=lambda x: -x["review"])[:12]:
        print(f"  {r['doc_id']:30} gold={r['gold']:>4}  review={r['review']:>4}")
    print(f"\nwrote {(args.out / 'worklist.md').relative_to(PROJECT_ROOT)} + worklist/*.md + proposed_gold/*.json")


def _selfcheck() -> None:
    text = "We collect bank statements for loan eligibility. Third parties get bank statements too."
    bs = text.index("bank statements")
    tp = text.index("Third parties")
    a = [(bs, bs + 15, "DATA_TYPE"), (tp, tp + 13, "THIRD_PARTY")]
    b = [(bs, bs + 15, "DATA_TYPE")]
    gold, actions = adjudicate_doc(text, a, b, {"bank statements": "DATA_TYPE"})
    kinds = Counter(k for k, _ in actions)
    assert kinds["DELETE"] == 1, kinds                 # 'Third parties' dropped by Rule 8
    assert kinds["ACCEPT_AGREED"] == 1, kinds
    assert kinds["ADD_REPEAT"] == 1, kinds             # 2nd 'bank statements' added by Rule 7
    assert len(gold) == 2, gold
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
