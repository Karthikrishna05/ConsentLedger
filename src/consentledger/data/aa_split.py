"""Leakage-safe test / adaptation split of the AA corpus, fixed BEFORE any model sees AA data (D52).

Two documents must be on the same side if they come from the same organisation OR share a large part of
their text (many AA terms are one template with the company name changed). So:

  1. similarity(a, b) = share of the smaller document's 8-word sequences that also occur in the other;
  2. link documents with the same organisation, or similarity >= --threshold;
  3. connected components = GROUPS; a group is never split;
  4. assign whole groups to `test` or `adapt`.

Uses document text and the manifest only - never the gold labels, never a model output.

    python -m consentledger.data.aa_split                      # show the groups
    python -m consentledger.data.aa_split --write --test-groups <ids>
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from itertools import combinations
from pathlib import Path

from consentledger.data.annotation_audit import load_corpus

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORPUS = PROJECT_ROOT / "data" / "aa" / "annotated" / "ls_import_tasks.json"
MANIFEST = PROJECT_ROOT / "data" / "aa" / "manifest.csv"
OUT = PROJECT_ROOT / "data" / "splits" / "aa_split.json"
# Scraping defect (glued words, D36): usable for adaptation, kept out of the test set.
GLUED = ("02_digio_terms", "10_perfios_terms")
# One organisation under several manifest spellings ("Setu AA (Agya Technologies)", "Setu AA").
ORG_KEY = re.compile(r"^[a-z]+")


def shingles(text: str, n: int = 8) -> set[str]:
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def similarity(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, min(len(a), len(b)))


def groups(corpus: dict[str, str], org: dict[str, str], threshold: float):
    """-> (list of sorted doc-id lists, {pair: similarity})."""
    docs = sorted(corpus)
    sh = {d: shingles(corpus[d]) for d in docs}
    parent = {d: d for d in docs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    sims = {}
    for a, b in combinations(docs, 2):
        s = similarity(sh[a], sh[b])
        sims[(a, b)] = s
        if org[a] == org[b] or s >= threshold:
            parent[find(a)] = find(b)
    comp: dict[str, list[str]] = {}
    for d in docs:
        comp.setdefault(find(d), []).append(d)
    return sorted(comp.values(), key=lambda g: (-len(g), g)), sims


def leakage(test: list[str], adapt: list[str], sims: dict) -> tuple[float, tuple]:
    """Largest similarity between any test document and any adaptation document."""
    worst = max(((sims.get((min(a, b), max(a, b)), 0.0), (a, b)) for a in test for b in adapt), default=(0.0, ()))
    return worst


def load():
    corpus = load_corpus(CORPUS)
    man = {r["doc_id"]: r for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))}
    org = {d: ORG_KEY.match(man[d]["organization"].lower()).group() for d in corpus}
    return corpus, man, org


def main() -> None:
    ap = argparse.ArgumentParser(description="Leakage-safe AA test/adaptation split.")
    ap.add_argument("--threshold", type=float, default=0.10)
    ap.add_argument("--test-groups", type=int, nargs="*", help="group numbers (as printed) that form the test set")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    corpus, man, org = load()
    gs, sims = groups(corpus, org, args.threshold)
    print(f"=== groups at similarity >= {args.threshold:.0%} or same organisation ===")
    for i, g in enumerate(gs, 1):
        words = sum(len(corpus[d].split()) for d in g)
        print(f"  G{i}: {len(g)} doc(s), {words} words: {', '.join(g)}")
    if args.test_groups is None:
        return
    test = sorted(d for i in args.test_groups for d in gs[i - 1])
    adapt = sorted(d for d in corpus if d not in test)
    glued_in_test = [d for d in GLUED if d in test]
    if glued_in_test:
        raise SystemExit(f"glued-text documents may not be in the test set: {glued_in_test}")
    worst, pair = leakage(test, adapt, sims)
    assert worst < args.threshold, (worst, pair)
    print(f"\ntest  ({len(test)}): {', '.join(test)}\nadapt ({len(adapt)}): {', '.join(adapt)}")
    print(f"largest test<->adapt text overlap: {worst:.1%} {pair}")
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "method": "connected components of (same organisation OR >= threshold shared 8-word sequences)",
            "threshold": args.threshold, "glued_excluded_from_test": list(GLUED),
            "groups": gs, "test_groups": args.test_groups,
            "max_test_adapt_overlap": round(worst, 4), "test": test, "adapt": adapt}, indent=2), encoding="utf-8")
        print(f"wrote {OUT.relative_to(PROJECT_ROOT)}")


def _selfcheck() -> None:
    base = " ".join(f"w{i}" for i in range(200))
    corpus = {"a1": base, "a2": base + " extra words here", "b1": " ".join(f"x{i}" for i in range(200)),
              "b2": " ".join(f"y{i}" for i in range(200)), "c1": " ".join(f"z{i}" for i in range(200))}
    org = {"a1": "one", "a2": "two", "b1": "three", "b2": "three", "c1": "four"}
    gs, sims = groups(corpus, org, 0.10)
    assert gs == [["a1", "a2"], ["b1", "b2"], ["c1"]], gs          # a1~a2 by text, b1~b2 by organisation
    assert leakage(["c1"], ["a1", "a2", "b1", "b2"], sims)[0] == 0.0
    assert leakage(["a1"], ["a2"], sims)[0] > 0.9                   # splitting a template pair would leak
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
