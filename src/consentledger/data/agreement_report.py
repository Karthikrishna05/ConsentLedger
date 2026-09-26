"""Per-document agreement report: file-wise Cohen's kappa + a categorised diff of the annotations.

Answers two questions kappa.py only summarises:
  1. WHICH documents disagree (file-wise kappa + entity P/R/F1, ranked worst-first);
  2. WHY they disagree, by sorting every span into one of five buckets:

     EXACT     - both annotators marked the same offsets AND the same label (agreement)
     BOUNDARY  - overlapping spans, same label, different edges (e.g. "loan facility" vs
                 "applying for loan facility") -> a span-rule / guideline issue
     LABEL     - overlapping spans, DIFFERENT label -> an ontology confusion
     A_ONLY    - A marked it, B saw nothing there -> a miss / coverage gap
     B_ONLY    - B marked it, A saw nothing there -> a miss / coverage gap

The bucket mix tells you the fix: mostly BOUNDARY -> tighten span rules; mostly A_ONLY/B_ONLY ->
one annotator is skipping content (density problem); mostly LABEL -> fix the ontology examples.

Outputs (default results/annotation/agreement/):
    summary.csv      one row per doc: kappa, P/R/F1, span counts, bucket counts (numbers only)
    report.md        overall + worst-first ranking + dominant failure mode per doc
    docs/<id>.md     the actual disagreeing spans with their text, grouped by bucket

Usage:
    python -m consentledger.data.agreement_report --a ExportA.json --b ExportB.json
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from consentledger.data.kappa import load_ls_export, _tags

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")
BUCKETS = ("EXACT", "BOUNDARY", "LABEL", "A_ONLY", "B_ONLY")


def _overlaps(a: tuple, b: tuple) -> bool:
    """True if two (start, end, label) spans share at least one character."""
    return a[0] < b[1] and b[0] < a[1]


def classify(spans_a: list[tuple], spans_b: list[tuple]) -> dict[str, list]:
    """Sort every span into EXACT / BOUNDARY / LABEL / A_ONLY / B_ONLY."""
    set_a, set_b = set(spans_a), set(spans_b)
    exact = sorted(set_a & set_b)
    rest_a = sorted(set_a - set_b)
    rest_b = sorted(set_b - set_a)

    boundary, label_diff = [], []
    matched_b: set = set()
    for sa in rest_a:
        partner = next((sb for sb in rest_b if sb not in matched_b and _overlaps(sa, sb)), None)
        if partner is None:
            continue
        matched_b.add(partner)
        (boundary if sa[2] == partner[2] else label_diff).append((sa, partner))

    paired_a = {sa for sa, _ in boundary} | {sa for sa, _ in label_diff}
    a_only = [s for s in rest_a if s not in paired_a]
    b_only = [s for s in rest_b if s not in matched_b]
    return {"EXACT": exact, "BOUNDARY": boundary, "LABEL": label_diff,
            "A_ONLY": a_only, "B_ONLY": b_only}


def _doc_markdown(key, text, sa, sb, k, f1, buckets, counts, dominant) -> str:
    out = [f"# {key}", "",
           f"kappa **{k:.3f}** | entity-F1 **{f1:.3f}** | A: {len(sa)} spans, B: {len(sb)} spans",
           f"| dominant issue: **{dominant}**", "",
           "| bucket | n |", "|---|---|"]
    out += [f"| {name} | {counts[name]} |" for name in BUCKETS]

    if buckets["BOUNDARY"]:
        out += ["", "## BOUNDARY - same label, different edges (span-rule issue)", ""]
        for x, y in buckets["BOUNDARY"][:80]:
            out.append(f"- **{x[2]}**  A: `{text[x[0]:x[1]]}`  vs  B: `{text[y[0]:y[1]]}`")
    if buckets["LABEL"]:
        out += ["", "## LABEL - same text, different label (ontology confusion)", ""]
        for x, y in buckets["LABEL"][:80]:
            out.append(f"- `{text[x[0]:x[1]]}` : A said **{x[2]}**, B said **{y[2]}**")
    for side, bucket in (("A", "A_ONLY"), ("B", "B_ONLY")):
        items_all = buckets[bucket]
        if not items_all:
            continue
        out += ["", f"## {bucket} - only {side} marked these ({len(items_all)})", ""]
        for lab in LABELS:
            items = [s for s in items_all if s[2] == lab]
            if not items:
                continue
            out.append(f"**{lab}** ({len(items)}):")
            out += [f"  - `{text[s[0]:s[1]]}`" for s in items[:60]]
            if len(items) > 60:
                out.append(f"  - ...and {len(items) - 60} more")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="File-wise kappa + categorised annotation differences.")
    ap.add_argument("--a", required=True, type=Path, help="annotator A export (Label Studio JSON)")
    ap.add_argument("--b", required=True, type=Path, help="annotator B export (Label Studio JSON)")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "results" / "annotation" / "agreement")
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()

    from sklearn.metrics import cohen_kappa_score
    from seqeval.metrics import f1_score, precision_score, recall_score

    A, B = load_ls_export(args.a), load_ls_export(args.b)
    common = sorted(set(A) & set(B))
    if not common:
        raise SystemExit("No documents in common between the two exports (check doc_id / import).")

    docs_dir = args.out / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for key in common:
        text = A[key]["text"]
        sa, sb = A[key]["spans"], B[key]["spans"]
        ta, tb = _tags(text, sa), _tags(text, sb)
        n = min(len(ta), len(tb))
        ta, tb = ta[:n], tb[:n]

        k = cohen_kappa_score(ta, tb) if len(set(ta + tb)) > 1 else 1.0
        p = precision_score([ta], [tb], zero_division=0)
        r = recall_score([ta], [tb], zero_division=0)
        f1 = f1_score([ta], [tb], zero_division=0)

        buckets = classify(sa, sb)
        counts = {name: len(buckets[name]) for name in BUCKETS}
        disagree = {kk: vv for kk, vv in counts.items() if kk != "EXACT"}
        dominant = max(disagree, key=disagree.get) if any(disagree.values()) else "-"

        rows.append({"doc_id": key, "tokens": n, "kappa": round(k, 4),
                     "entity_p": round(p, 4), "entity_r": round(r, 4), "entity_f1": round(f1, 4),
                     "spans_A": len(sa), "spans_B": len(sb), **counts,
                     "dominant_issue": dominant, "below_gate": k < args.threshold})

        (docs_dir / f"{key}.md").write_text(
            _doc_markdown(key, text, sa, sb, k, f1, buckets, counts, dominant), encoding="utf-8")

    cols = ["doc_id", "tokens", "kappa", "entity_p", "entity_r", "entity_f1", "spans_A", "spans_B",
            *BUCKETS, "dominant_issue", "below_gate"]
    with (args.out / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    worst = sorted(rows, key=lambda x: x["kappa"])
    tot: Counter = Counter()
    for row in rows:
        for bkt in BUCKETS:
            tot[bkt] += row[bkt]
    n_bad = sum(1 for row in rows if row["below_gate"])

    md = [f"# Annotation agreement - {len(rows)} documents", "",
          f"- Documents below the {args.threshold} gate: **{n_bad}/{len(rows)}**",
          f"- Total spans: A={sum(r['spans_A'] for r in rows)}, B={sum(r['spans_B'] for r in rows)}",
          "", "## Where the disagreement lives (all docs)", "",
          "| bucket | n | meaning |", "|---|---|---|",
          f"| EXACT | {tot['EXACT']} | agreed exactly |",
          f"| BOUNDARY | {tot['BOUNDARY']} | same label, different edges -> span-rule fix |",
          f"| LABEL | {tot['LABEL']} | same text, different label -> ontology fix |",
          f"| A_ONLY | {tot['A_ONLY']} | B missed, or A over-marked |",
          f"| B_ONLY | {tot['B_ONLY']} | A missed, or B over-marked |",
          "", "## Documents, worst first", "",
          "| doc | kappa | entF1 | A | B | EXACT | BOUND | LABEL | A_ONLY | B_ONLY | dominant |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in worst:
        md.append(f"| {row['doc_id']} | {row['kappa']:.3f} | {row['entity_f1']:.3f} | "
                  f"{row['spans_A']} | {row['spans_B']} | {row['EXACT']} | {row['BOUNDARY']} | "
                  f"{row['LABEL']} | {row['A_ONLY']} | {row['B_ONLY']} | {row['dominant_issue']} |")
    md += ["", f"Per-document detail (actual phrases): `{docs_dir.relative_to(PROJECT_ROOT)}/<doc_id>.md`"]
    (args.out / "report.md").write_text("\n".join(md), encoding="utf-8")

    print(f"=== file-wise agreement ({len(rows)} docs, gate {args.threshold}) ===")
    for row in worst:
        flag = "" if not row["below_gate"] else "  <-- below gate"
        print(f"  {row['doc_id']:30} k={row['kappa']:.3f} entF1={row['entity_f1']:.3f} "
              f"A:{row['spans_A']:>3} B:{row['spans_B']:>3}  main={row['dominant_issue']}{flag}")
    print(f"\nbuckets across all docs: {dict(tot)}")
    print(f"wrote {(args.out / 'summary.csv').relative_to(PROJECT_ROOT)}, report.md, docs/*.md")


def _selfcheck() -> None:
    """classify() must separate exact / boundary / label / one-sided spans."""
    a = [(0, 5, "DATA_TYPE"), (10, 20, "PURPOSE"), (30, 35, "THIRD_PARTY"), (50, 55, "DATA_TYPE")]
    b = [(0, 5, "DATA_TYPE"), (10, 25, "PURPOSE"), (30, 35, "PURPOSE"), (70, 75, "DATA_TYPE")]
    r = classify(a, b)
    assert len(r["EXACT"]) == 1, r
    assert len(r["BOUNDARY"]) == 1, r      # (10,20) vs (10,25) - same label, different edges
    assert len(r["LABEL"]) == 1, r         # (30,35) THIRD_PARTY vs PURPOSE
    assert len(r["A_ONLY"]) == 1 and len(r["B_ONLY"]) == 1, r
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
