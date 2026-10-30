"""Audit two annotators against the source text, including what BOTH missed.

"Should have been marked" proxy: the consensus lexicon of (phrase, label) pairs both annotators marked somewhere.
Each occurrence in the raw text counts as both / A only / B only / neither. Also per-annotator label mix,
span lengths, repeats and private vocabulary. Writes corpus_audit.md, per_doc/<id>.md, missed_terms.csv.

Usage:
    python -m consentledger.data.annotation_audit --corpus data/aa/annotated/ls_import_tasks.json \
        --a data/aa/annotated/ExportA.json --b data/aa/annotated/ExportB.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")
MIN_TERM, MAX_TERM = 4, 60          # ignore 1-3 char noise and runaway clause-length spans


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def load_corpus(path: Path) -> dict[str, str]:
    out = {}
    for t in json.loads(Path(path).read_text(encoding="utf-8")):
        d = t.get("data", t)
        out[d.get("doc_id") or norm(d.get("text", ""))[:40]] = d.get("text", "")
    return out


# Over-generic words that slipped into "consensus" from one sloppy mark each; they match hundreds of
# times and inflate the missed-by-both rate. Excluded under --strict (they are Rule-8 stoplist terms).
GENERIC = {"financial", "security", "bank", "name", "device", "personal data", "documents", "records",
           "identity", "personal information", "feedback", "liabilities", "government", "transactions",
           "third parties", "financial information", "services", "information", "data", "profile",
           "usage data"}


def build_consensus_lexicon(A: dict, B: dict, min_count: int = 1, multiword: bool = False,
                            drop_generic: bool = False) -> dict[str, str]:
    """(normalized phrase -> label) for phrases BOTH annotators marked with the SAME label.

    Unfiltered, one sloppy mark each promotes e.g. "financial" (~400 hits); --strict's filters avoid that.
    """
    def vocab(X):
        v = defaultdict(Counter)
        for doc in X.values():
            for s, e, lab in doc["spans"]:
                p = norm(doc["text"][s:e])
                if MIN_TERM <= len(p) <= MAX_TERM:
                    v[p][lab] += 1
        return v
    va, vb = vocab(A), vocab(B)
    lex = {}
    for p in set(va) & set(vb):
        if sum(va[p].values()) < min_count or sum(vb[p].values()) < min_count:
            continue
        if multiword and len(p.split()) < 2:
            continue
        if drop_generic and p in GENERIC:
            continue
        la, lb = va[p].most_common(1)[0][0], vb[p].most_common(1)[0][0]
        if la == lb:
            lex[p] = la
    return lex


def find_occurrences(text: str, terms: list[str]) -> list[tuple[int, int, str]]:
    """Every literal occurrence of each lexicon term in the text (case-insensitive, word-bounded)."""
    hits = []
    low = text.lower()
    for t in terms:
        start = 0
        while True:
            i = low.find(t, start)
            if i < 0:
                break
            j = i + len(t)
            before_ok = i == 0 or not low[i - 1].isalnum()
            after_ok = j >= len(low) or not low[j].isalnum()
            if before_ok and after_ok:
                hits.append((i, j, t))
            start = i + 1
    return hits


def covered(idx: set[tuple[int, int]], i: int, j: int) -> bool:
    """Did the annotator mark a span overlapping [i, j)?"""
    return any(s < j and i < e for s, e in idx)


def span_stats(spans: list, text: str) -> dict:
    lens = [len(text[s:e].split()) for s, e, _ in spans] or [0]
    by_label = Counter(lab for _, _, lab in spans)
    phrases = [norm(text[s:e]) for s, e, _ in spans]
    uniq = len(set(phrases))
    return {"n": len(spans), "unique": uniq, "repeats": len(spans) - uniq,
            "median_words": st.median(lens), "max_words": max(lens), **{f"n_{l}": by_label.get(l, 0) for l in LABELS}}


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit two annotators against the source corpus.")
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "results" / "annotation" / "audit")
    ap.add_argument("--strict", action="store_true",
                    help="defensible lexicon: multi-word, endorsed >=2x by each, generic words dropped")
    args = ap.parse_args()
    args.out = args.out.resolve()   # relative --out would break relative_to(PROJECT_ROOT)

    corpus = load_corpus(args.corpus)
    A, B = load_ls_export(args.a), load_ls_export(args.b)
    docs = sorted(set(corpus) & set(A) & set(B))

    lex = (build_consensus_lexicon(A, B, min_count=2, multiword=True, drop_generic=True)
           if args.strict else build_consensus_lexicon(A, B))
    print(f"lexicon mode: {'STRICT' if args.strict else 'permissive (inflated - prefer --strict)'}")
    terms = sorted(lex, key=len, reverse=True)
    per_doc_dir = args.out / "per_doc"
    per_doc_dir.mkdir(parents=True, exist_ok=True)

    # annotator-level vocabulary (for the "perspective" section)
    def all_phrases(X):
        c = Counter()
        for d in X.values():
            for s, e, lab in d["spans"]:
                c[(norm(d["text"][s:e]), lab)] += 1
        return c
    pa, pb = all_phrases(A), all_phrases(B)
    only_a = Counter({k: v for k, v in pa.items() if k not in pb})
    only_b = Counter({k: v for k, v in pb.items() if k not in pa})

    rows, missed_counter = [], Counter()
    for key in docs:
        text = corpus[key]
        sa, sb = A[key]["spans"], B[key]["spans"]
        ia = {(s, e) for s, e, _ in sa}
        ib = {(s, e) for s, e, _ in sb}

        occ = find_occurrences(text, terms)
        # de-duplicate nested hits: keep the longest term at each position
        occ.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        kept, last_end = [], -1
        for i, j, t in occ:
            if i >= last_end:
                kept.append((i, j, t))
                last_end = j
        both = a_only = b_only = neither = 0
        missed_here = Counter()
        for i, j, t in kept:
            ca, cb = covered(ia, i, j), covered(ib, i, j)
            if ca and cb:
                both += 1
            elif ca:
                a_only += 1
            elif cb:
                b_only += 1
            else:
                neither += 1
                missed_here[t] += 1
                missed_counter[t] += 1

        stats_a, stats_b = span_stats(sa, text), span_stats(sb, text)
        total_opps = len(kept) or 1
        rows.append({
            "doc_id": key, "chars": len(text), "lexicon_hits": len(kept),
            "both": both, "only_A": a_only, "only_B": b_only, "missed_by_both": neither,
            "recall_A": round((both + a_only) / total_opps, 3),
            "recall_B": round((both + b_only) / total_opps, 3),
            "spans_A": stats_a["n"], "spans_B": stats_b["n"],
            "repeats_A": stats_a["repeats"], "repeats_B": stats_b["repeats"],
            "medw_A": stats_a["median_words"], "medw_B": stats_b["median_words"],
            **{f"A_{l}": stats_a[f"n_{l}"] for l in LABELS},
            **{f"B_{l}": stats_b[f"n_{l}"] for l in LABELS},
        })

        # ---- per-doc report ----
        md = [f"# {key}", "", f"{len(text):,} chars | consensus-term occurrences found: **{len(kept)}**", "",
              "| | A | B |", "|---|---|---|",
              f"| spans marked | {stats_a['n']} | {stats_b['n']} |",
              f"| unique phrases | {stats_a['unique']} | {stats_b['unique']} |",
              f"| repeat marks | {stats_a['repeats']} | {stats_b['repeats']} |",
              f"| median span (words) | {stats_a['median_words']} | {stats_b['median_words']} |",
              f"| DATA_TYPE | {stats_a['n_DATA_TYPE']} | {stats_b['n_DATA_TYPE']} |",
              f"| PURPOSE | {stats_a['n_PURPOSE']} | {stats_b['n_PURPOSE']} |",
              f"| THIRD_PARTY | {stats_a['n_THIRD_PARTY']} | {stats_b['n_THIRD_PARTY']} |",
              f"| recall vs consensus lexicon | **{rows[-1]['recall_A']:.0%}** | **{rows[-1]['recall_B']:.0%}** |",
              "", "## Coverage of known-good terms in THIS document", "",
              f"- both marked: **{both}**", f"- only A marked: **{a_only}**",
              f"- only B marked: **{b_only}**", f"- **missed by BOTH: {neither}**", ""]
        if missed_here:
            md += ["### Missed by both (terms both annotators endorse elsewhere)", ""]
            md += [f"- `{t}` ({lex[t]}) x{c}" for t, c in missed_here.most_common(40)]
        for name, X in (("A", A), ("B", B)):
            md += ["", f"### What {name} marked (top phrases)", ""]
            c = Counter(norm(X[key]['text'][s:e]) + f"  [{lab}]" for s, e, lab in X[key]["spans"])
            md += [f"- `{p}` x{n}" for p, n in c.most_common(30)]
        (per_doc_dir / f"{key}.md").write_text("\n".join(md), encoding="utf-8")

    # ---- missed_terms.csv ----
    with (args.out / "missed_terms.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["term", "label", "times_missed_by_both"])
        for t, c in missed_counter.most_common():
            w.writerow([t, lex[t], c])

    # ---- corpus_audit.md ----
    tot_hits = sum(r["lexicon_hits"] for r in rows)
    tot_both = sum(r["both"] for r in rows)
    tot_a = sum(r["only_A"] for r in rows)
    tot_b = sum(r["only_B"] for r in rows)
    tot_n = sum(r["missed_by_both"] for r in rows)
    mixA = Counter(); mixB = Counter()
    for r in rows:
        for l in LABELS:
            mixA[l] += r[f"A_{l}"]; mixB[l] += r[f"B_{l}"]

    md = ["# Annotation audit - two annotators vs the source corpus", "",
          f"{len(rows)} documents | consensus lexicon: **{len(lex)}** (phrase, label) pairs both "
          "annotators independently endorsed at least once", "",
          "## 1. Recall against the consensus lexicon", "",
          "Every occurrence of a term BOTH annotators endorse somewhere, located in the raw text:", "",
          "| outcome | n | share |", "|---|---|---|",
          f"| both marked it | {tot_both} | {tot_both/max(tot_hits,1):.1%} |",
          f"| only A marked it | {tot_a} | {tot_a/max(tot_hits,1):.1%} |",
          f"| only B marked it | {tot_b} | {tot_b/max(tot_hits,1):.1%} |",
          f"| **missed by BOTH** | **{tot_n}** | **{tot_n/max(tot_hits,1):.1%}** |",
          f"| total opportunities | {tot_hits} | |", "",
          "## 2. The two perspectives", "",
          "| | A | B |", "|---|---|---|",
          f"| total spans | {sum(r['spans_A'] for r in rows)} | {sum(r['spans_B'] for r in rows)} |",
          f"| repeat marks | {sum(r['repeats_A'] for r in rows)} | {sum(r['repeats_B'] for r in rows)} |",
          f"| DATA_TYPE | {mixA['DATA_TYPE']} ({mixA['DATA_TYPE']/max(sum(mixA.values()),1):.0%}) | {mixB['DATA_TYPE']} ({mixB['DATA_TYPE']/max(sum(mixB.values()),1):.0%}) |",
          f"| PURPOSE | {mixA['PURPOSE']} ({mixA['PURPOSE']/max(sum(mixA.values()),1):.0%}) | {mixB['PURPOSE']} ({mixB['PURPOSE']/max(sum(mixB.values()),1):.0%}) |",
          f"| THIRD_PARTY | {mixA['THIRD_PARTY']} ({mixA['THIRD_PARTY']/max(sum(mixA.values()),1):.0%}) | {mixB['THIRD_PARTY']} ({mixB['THIRD_PARTY']/max(sum(mixB.values()),1):.0%}) |",
          f"| mean recall vs lexicon | {st.mean(r['recall_A'] for r in rows):.0%} | {st.mean(r['recall_B'] for r in rows):.0%} |",
          "", "### Vocabulary only A ever uses (top 25)", ""]
    md += [f"- `{p}` [{l}] x{n}" for (p, l), n in only_a.most_common(25)]
    md += ["", "### Vocabulary only B ever uses (top 25)", ""]
    md += [f"- `{p}` [{l}] x{n}" for (p, l), n in only_b.most_common(25)]
    md += ["", "## 3. Most-missed consensus terms (both annotators skipped)", "",
           "| term | label | times missed |", "|---|---|---|"]
    md += [f"| `{t}` | {lex[t]} | {c} |" for t, c in missed_counter.most_common(30)]
    md += ["", "## 4. Per document", "",
           "| doc | chars | opps | both | A only | B only | missed both | recall A | recall B | A spans | B spans |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: x["missed_by_both"], reverse=True):
        md.append(f"| {r['doc_id']} | {r['chars']:,} | {r['lexicon_hits']} | {r['both']} | {r['only_A']} | "
                  f"{r['only_B']} | **{r['missed_by_both']}** | {r['recall_A']:.0%} | {r['recall_B']:.0%} | "
                  f"{r['spans_A']} | {r['spans_B']} |")
    md += ["", f"Per-document detail: `{per_doc_dir.relative_to(PROJECT_ROOT)}/<doc_id>.md`"]
    (args.out / "corpus_audit.md").write_text("\n".join(md), encoding="utf-8")

    print(f"=== audit: {len(rows)} docs, consensus lexicon {len(lex)} terms ===")
    print(f"opportunities {tot_hits} | both {tot_both} ({tot_both/max(tot_hits,1):.1%}) | "
          f"A only {tot_a} | B only {tot_b} | MISSED BY BOTH {tot_n} ({tot_n/max(tot_hits,1):.1%})")
    print(f"mean recall vs lexicon:  A {st.mean(r['recall_A'] for r in rows):.1%}   "
          f"B {st.mean(r['recall_B'] for r in rows):.1%}")
    print(f"label mix  A: {dict(mixA)}\n           B: {dict(mixB)}")
    print(f"wrote {(args.out / 'corpus_audit.md').relative_to(PROJECT_ROOT)}, missed_terms.csv, per_doc/*.md")


def _selfcheck() -> None:
    txt = "We collect bank statements and share with credit bureaus. Bank statements again."
    assert len(find_occurrences(txt.lower(), ["bank statements"])) == 2
    assert find_occurrences("rebanking", ["bank"]) == []          # word-bounded, no substring hits
    assert covered({(0, 10)}, 5, 8) and not covered({(0, 10)}, 20, 30)
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
