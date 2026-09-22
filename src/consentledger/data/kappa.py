"""Inter-annotator agreement between two Label Studio exports.

Primary metric: **entity-level** precision/recall/F1 (treat annotator A as reference, B as hypothesis).
Secondary metric: **token-level Cohen's kappa** (the number people usually quote).

Both are computed on ONE shared tokenization per document (we tokenize each doc's text once, via
`bio_tagging`, and map BOTH annotators' character spans onto those same tokens). This avoids the classic
bug of tokenizing each annotator differently or truncating to a common length (D10): no min_len, full
document, token-for-token.

Works on any set of docs both annotators labelled — 1 doc (the pilot/calibration check) or all 23.

Usage:
    python -m consentledger.data.kappa --a exportA.json --b exportB.json
    python -m consentledger.data.kappa --a A.json --b B.json --threshold 0.6
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from consentledger.data.bio_tagging import bio_for_segment

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT = PROJECT_ROOT / "results" / "annotation"


def load_ls_export(path: Path) -> dict[str, dict]:
    """Parse a Label Studio JSON export -> {doc_key: {"text": str, "spans": [(start,end,label)]}}.

    Handles the standard export (task.data.text + task.annotations[].result[].value) and the flatter
    JSON-MIN export (task.text + task.label[]). Matches docs by data.doc_id when present (recommended),
    else by the text itself.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    docs: dict[str, dict] = {}
    for task in raw:
        data = task.get("data", task)
        text = data.get("text")
        if text is None:  # last resort: first string value in data
            text = next((v for v in data.values() if isinstance(v, str)), "")
        key = data.get("doc_id") or data.get("ref_id") or (text[:60] if text else f"task_{len(docs)}")

        results = []
        if task.get("annotations"):
            results = task["annotations"][0].get("result", [])
        elif task.get("predictions"):
            results = task["predictions"][0].get("result", [])
        elif isinstance(task.get("label"), list):      # JSON-MIN
            results = [{"value": v} for v in task["label"]]

        spans = []
        for r in results:
            v = r.get("value", {})
            labels = v.get("labels") or v.get("hypertextlabels")
            if labels and "start" in v and "end" in v:
                spans.append((int(v["start"]), int(v["end"]), labels[0]))
        docs[key] = {"text": text, "spans": spans}
    return docs


def _tags(text: str, spans: list[tuple]) -> list[str]:
    span_dicts = [{"seg_start": s, "seg_end": e, "label": lab} for s, e, lab in spans]
    return [tag for _, tag in bio_for_segment(text, span_dicts)]


def main() -> None:
    ap = argparse.ArgumentParser(description="Cohen's kappa + entity-level agreement (two LS exports).")
    ap.add_argument("--a", required=True, type=Path, help="annotator A export (Label Studio JSON)")
    ap.add_argument("--b", required=True, type=Path, help="annotator B export (Label Studio JSON)")
    ap.add_argument("--threshold", type=float, default=0.6, help="pass gate for kappa (0.6 = substantial)")
    ap.add_argument("--show-diff", action="store_true",
                    help="print the spans where A and B disagree (with text), grouped by label — for calibration")
    args = ap.parse_args()

    from sklearn.metrics import cohen_kappa_score
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    A, B = load_ls_export(args.a), load_ls_export(args.b)
    common = sorted(set(A) & set(B))
    only_a, only_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    if not common:
        raise SystemExit("No documents in common between the two exports (check doc_id / import).")

    tok_a_all, tok_b_all = [], []          # flat token tags -> Cohen's kappa
    seq_true, seq_pred = [], []            # per-doc tag lists -> seqeval entity metrics
    per_doc = []
    for key in common:
        text = A[key]["text"]
        if B[key]["text"] and B[key]["text"] != text:
            print(f"  WARN {key}: text differs between exports; offsets may not align.")
        ta, tb = _tags(text, A[key]["spans"]), _tags(text, B[key]["spans"])
        n = min(len(ta), len(tb))
        ta, tb = ta[:n], tb[:n]            # should already match (same text/tokenizer)
        tok_a_all += ta
        tok_b_all += tb
        seq_true.append(ta)
        seq_pred.append(tb)
        k = cohen_kappa_score(ta, tb) if len(set(ta + tb)) > 1 else 1.0
        per_doc.append({"doc_id": key, "tokens": n, "kappa": round(k, 4),
                        "spans_A": len(A[key]["spans"]), "spans_B": len(B[key]["spans"])})

    kappa = cohen_kappa_score(tok_a_all, tok_b_all)
    ent_f1 = f1_score(seq_true, seq_pred, zero_division=0)
    ent_p = precision_score(seq_true, seq_pred, zero_division=0)
    ent_r = recall_score(seq_true, seq_pred, zero_division=0)

    print(f"\n=== inter-annotator agreement ({len(common)} shared doc(s)) ===")
    print(f"PRIMARY  entity-level  P {ent_p:.4f} | R {ent_r:.4f} | F1 {ent_f1:.4f}")
    print(f"SECONDARY token-level  Cohen's kappa = {kappa:.4f}   (gate {args.threshold})")
    print("\nper-document token kappa:")
    for d in per_doc:
        flag = "" if d["kappa"] >= args.threshold else "  <-- below gate"
        print(f"  {d['doc_id']:32} k={d['kappa']:.3f}  (A:{d['spans_A']} B:{d['spans_B']} spans){flag}")
    if only_a or only_b:
        print(f"\nnote: only in A: {only_a}   only in B: {only_b}")
    print("\nentity-level report (A = reference, B = hypothesis):")
    print(classification_report(seq_true, seq_pred, digits=4, zero_division=0))

    if args.show_diff:
        print("\n=== disagreements (exact-span mismatches, for calibration) ===")
        for key in common:
            text = A[key]["text"]
            sa = {(s, e, lab): text[s:e] for s, e, lab in A[key]["spans"]}
            sb = {(s, e, lab): text[s:e] for s, e, lab in B[key]["spans"]}
            a_only = sorted(set(sa) - set(sb))
            b_only = sorted(set(sb) - set(sa))
            if not a_only and not b_only:
                continue
            print(f"\n--- {key} ---")
            for label in ("DATA_TYPE", "PURPOSE", "THIRD_PARTY"):
                al = [f'{s}:{e} \"{sa[(s, e, l)]}\"' for (s, e, l) in a_only if l == label]
                bl = [f'{s}:{e} \"{sb[(s, e, l)]}\"' for (s, e, l) in b_only if l == label]
                if not al and not bl:
                    continue
                print(f"  [{label}]")
                for x in al:
                    print(f"      A-only: {x}")
                for x in bl:
                    print(f"      B-only: {x}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "kappa.json").write_text(json.dumps({
        "n_docs": len(common), "cohen_kappa_token": kappa, "threshold": args.threshold,
        "entity_precision": ent_p, "entity_recall": ent_r, "entity_f1": ent_f1,
        "per_doc": per_doc, "only_in_A": only_a, "only_in_B": only_b,
    }, indent=2), encoding="utf-8")
    with (OUT / "kappa_per_doc.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["doc_id", "tokens", "kappa", "spans_A", "spans_B"])
        w.writeheader(); w.writerows(per_doc)

    verdict = "PASS - proceed to annotate the rest" if kappa >= args.threshold else \
              "BELOW GATE - discuss disagreements, refine the guideline, re-annotate"
    print(f"\nVERDICT: kappa {kappa:.4f} vs gate {args.threshold} -> {verdict}")
    print(f"saved: {(OUT / 'kappa.json').relative_to(PROJECT_ROOT)} + kappa_per_doc.csv")


if __name__ == "__main__":
    main()
