"""Inter-annotator agreement under RELAXED span matching, alongside strict exact match.

Why this exists: exact-match entity F1 scores `raise a grievance` against
`to raise a grievance with the grievance resolution officer of the FIU` as a complete miss, even though
the two annotators clearly agree on the substance. PURPOSE spans are inherently phrasal - they carry
function words (to, for, a, the, within, during) and trailing circumstance clauses that two careful
people will bracket differently. DATA_TYPE and THIRD_PARTY are mostly short noun phrases and suffer far
less. So a single strict number hides whether the disagreement is about MEANING or about EDGES.

Four matching criteria, strictest first (same label required in all four):

  EXACT    - identical character offsets.
  PARTIAL  - the two spans overlap by at least one character.           (MUC-style partial credit)
  CONTENT  - after removing function words, the content-word sets have an overlap coefficient
             |A and B| / min(|A|,|B|) >= --threshold (default 0.6). This is the criterion that matches
             "raise a grievance" to the long version: {raise, grievance} is fully contained in
             {raise, grievance, resolution, officer, fiu}, so the coefficient is 1.0.
  TOKEN    - token-level micro-F1 over non-O tags (ignores span boundaries entirely).

Matching is greedy and ONE-TO-ONE within a label, so one long span cannot absorb several short ones and
inflate the score.

Reading the output: if PURPOSE jumps sharply from EXACT to CONTENT while DATA_TYPE barely moves, the
annotators agree on the purposes and differ only on how much text to bracket - which is a reportable
finding, not a failure.

Usage:
    python -m consentledger.data.relaxed_agreement --a ExportA.json --b ExportB.json
    python -m consentledger.data.relaxed_agreement --a A.json --b B.json --docs 10_perfios_terms
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from consentledger.data.kappa import _tags, load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")

# Function words that carry no content: articles, prepositions, conjunctions, determiners, light verbs.
FUNCTION_WORDS = {
    "a", "an", "the", "to", "for", "of", "in", "on", "at", "by", "with", "within", "during", "from",
    "and", "or", "any", "all", "such", "your", "our", "its", "their", "this", "that", "these", "those",
    "other", "including", "include", "includes", "related", "certain", "so", "it", "is", "are", "be",
    "as", "per", "under", "through", "upon", "via", "may", "will", "shall", "can", "we", "you", "us",
    "purpose", "purposes",          # 'for the purpose of X' -> X is the content
}


def content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in FUNCTION_WORDS and len(w) > 1}


def overlap_coeff(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def greedy_match(gold, pred, ok) -> int:
    """Greedy one-to-one matching: how many gold spans find a distinct partner satisfying ok()?

    Callers pre-filter by label, so no label check here (an earlier version compared index 2, which is
    the END offset, not the label - that silently forced exact end-matching under every criterion).
    """
    used, hits = set(), 0
    for g in gold:
        for i, p in enumerate(pred):
            if i in used:
                continue
            if ok(g, p):
                used.add(i)
                hits += 1
                break
    return hits


def prf(hits: int, n_gold: int, n_pred: int) -> tuple[float, float, float]:
    p = hits / n_pred if n_pred else 0.0
    r = hits / n_gold if n_gold else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def score(docs, A, B, threshold: float) -> dict:
    """Returns {criterion: {label|micro: (P,R,F1,n_gold,n_pred)}}."""
    gold_all, pred_all, texts = [], [], {}
    for k in docs:
        texts[k] = A[k]["text"]
        gold_all += [(k, s, e, l) for s, e, l in A[k]["spans"]]
        pred_all += [(k, s, e, l) for s, e, l in B[k]["spans"]]

    def _txt(item):
        k, s, e, _ = item
        return texts[k][s:e]

    crit = {
        "EXACT":   lambda g, p: g[1] == p[1] and g[2] == p[2],
        "PARTIAL": lambda g, p: g[1] < p[2] and p[1] < g[2],
        "CONTENT": lambda g, p: overlap_coeff(content_words(_txt(g)), content_words(_txt(p))) >= threshold,
    }
    out = {}
    for name, fn in crit.items():
        out[name] = {}
        tot_h = tot_g = tot_p = 0
        for lab in LABELS:
            # spans are (doc, start, end, label); compare within the same doc only
            gl = [g for g in gold_all if g[3] == lab]
            pl = [p for p in pred_all if p[3] == lab]
            hits = 0
            for k in docs:
                gk = [g for g in gl if g[0] == k]
                pk = [p for p in pl if p[0] == k]
                hits += greedy_match(
                    [(g[0], g[1], g[2], g[3]) for g in gk],
                    [(p[0], p[1], p[2], p[3]) for p in pk],
                    lambda g, p: fn((g[0], g[1], g[2], g[3]), (p[0], p[1], p[2], p[3])),
                )
            out[name][lab] = (*prf(hits, len(gl), len(pl)), len(gl), len(pl))
            tot_h += hits
            tot_g += len(gl)
            tot_p += len(pl)
        out[name]["micro"] = (*prf(tot_h, tot_g, tot_p), tot_g, tot_p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Relaxed-match inter-annotator agreement.")
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    ap.add_argument("--docs", nargs="+", metavar="DOC_ID", help="restrict to these doc_ids (substring)")
    ap.add_argument("--threshold", type=float, default=0.6, help="CONTENT overlap coefficient (default 0.6)")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "results" / "annotation" / "relaxed.json")
    args = ap.parse_args()

    from sklearn.metrics import f1_score as skf1

    A, B = load_ls_export(args.a), load_ls_export(args.b)
    docs = sorted(set(A) & set(B))
    if args.docs:
        docs = [k for k in docs if any(d.lower() in k.lower() for d in args.docs)]
        if not docs:
            raise SystemExit(f"--docs matched nothing: {args.docs}")
    res = score(docs, A, B, args.threshold)

    # token-level micro F1 over non-O tags (boundary-free)
    ta_all, tb_all = [], []
    for k in docs:
        ta, tb = _tags(A[k]["text"], A[k]["spans"]), _tags(B[k]["text"], B[k]["spans"])
        n = min(len(ta), len(tb))
        ta_all += ta[:n]
        tb_all += tb[:n]
    lbls = sorted({t for t in ta_all + tb_all if t != "O"})
    token_f1 = skf1(ta_all, tb_all, labels=lbls, average="micro", zero_division=0)

    print(f"=== relaxed agreement over {len(docs)} doc(s)  (CONTENT threshold {args.threshold}) ===")
    print(f"{'criterion':10}{'label':14}{'P':>8}{'R':>8}{'F1':>8}   {'A spans':>8}{'B spans':>8}")
    for name in ("EXACT", "PARTIAL", "CONTENT"):
        for lab in (*LABELS, "micro"):
            p, r, f, ng, npd = res[name][lab]
            star = " <<<" if (name == "CONTENT" and lab == "micro") else ""
            print(f"{name:10}{lab:14}{p:>8.3f}{r:>8.3f}{f:>8.3f}   {ng:>8}{npd:>8}{star}")
        print()
    print(f"{'TOKEN':10}{'micro':14}{'':>8}{'':>8}{token_f1:>8.3f}   (boundary-free)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "n_docs": len(docs), "docs": docs, "content_threshold": args.threshold,
        "token_micro_f1": token_f1,
        "scores": {c: {l: dict(zip(("precision", "recall", "f1", "n_A", "n_B"), v))
                       for l, v in d.items()} for c, d in res.items()},
    }, indent=2), encoding="utf-8")
    print(f"\nsaved {args.out.relative_to(PROJECT_ROOT)}")


def _selfcheck() -> None:
    short, long_ = "raise a grievance", "to raise a grievance with the grievance resolution officer"
    assert overlap_coeff(content_words(short), content_words(long_)) == 1.0
    assert overlap_coeff(content_words("bank statements"), content_words("mutual funds")) == 0.0
    # greedy matching must be one-to-one
    g = [("d", 0, 5, "P"), ("d", 6, 9, "P")]
    p = [("d", 0, 20, "P")]
    assert greedy_match(g, p, lambda a, b: a[1] < b[2] and b[1] < a[2]) == 1
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
