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
import re
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
    "provide the services", "provide services", "providing the services",
    "business purposes", "lawful purposes", "other purposes", "related purposes", "as required",
    "reporting", "usage data", "profile", "market", "statistics", "suggestions", "feedback",
    "cookie", "cookies", "pixels", "device identifiers", "operating system", "version", "spi", "pii",
    # umbrellas that PII/SPI abbreviate (Rule 13; Rule 9b decision table)
    "personally identifiable information", "sensitive personal information", "sensitive personal data",
    "personal details", "technical data",
    # generic people & groups (Rule 8 table, added v7)
    "stakeholders", "persons", "any person", "entities", "others", "third-party entities",
    # device/usage telemetry (Rule 23a, v7.2) - collected by the device, not in any bank record
    "ip address", "ip addresses", "browser type", "browser type and version", "browser types",
    "referring urls", "pages viewed", "in-app actions", "session duration", "device information",
    "location data", "device and usage data", "telemetry", "time zone settings", "time zone setting",
    # Rule 9b decision table: umbrellas with a non-content modifier (D44)
    "financial data", "financial details", "data categories", "categories of data",
}
# Rule 8b - AA-framework roles and regulators are never THIRD_PARTY (and never anything else).
AA_ROLES = {
    "account aggregator", "aa", "financial information provider", "fip",
    "financial information user", "fiu", "reserve bank of india", "rbi", "sahamati",
    # the other financial-sector regulators of the AA framework (D46) - part of the pipeline, like RBI
    "sebi", "securities and exchange board of india", "irdai",
    "insurance regulatory and development authority of india", "pfrda",
    "pension fund regulatory and development authority",
    "consent artefact", "consent manager", "nbfc-aa",
    # plurals - "Financial Information Providers (FIPs)" is how most documents write them
    "account aggregators", "aas", "financial information providers", "fips",
    "financial information users", "fius", "consent artefacts", "consent artifacts", "consent artifact",
    "consent managers",
    "information user", "information users", "iu",
}
DROP = STOPLIST | AA_ROLES
# Variants no exact list can enumerate (D44): observed telemetry as DATA_TYPE (Rule 23a: "type of browser",
# "flash cookies", "IMEI", "web beacons") and any NAMED Account Aggregator as THIRD_PARTY (Rule 8b).
TELEMETRY = re.compile(
    r"\b(ip address\w*|browser\w*|device (?:id\w*|identifier\w*|information|data|model)|operating systems?|"
    r"referr\w* (?:urls?|pages?|sites?)|pages? (?:viewed|visited)|clickstream|session (?:duration|information|data|ids?)|"
    r"cookies?|pixels?|web beacons?|log (?:data|files?)|usage (?:data|information)|time ?zones?|imei|"
    r"mac address\w*|advertising ids?|hardware model|telemetry|location (?:data|information)|geolocation|"
    r"in-app actions?)\b", re.I)
NAMED_AA = re.compile(r"\b(one ?money|finvu|nesl asset data|cams ?finserv|perfios (?:aa|account aggregation\w*)|"
                      r"anumati|saafe aa|setu aa|protean surakshaa)\b", re.I)


def is_dropped(phrase: str, label: str) -> bool:
    """Rules 8 / 8b / 9b / 23a: a span that is never an entity (phrase already normalised)."""
    return (phrase in DROP or (label == "DATA_TYPE" and bool(TELEMETRY.search(phrase)))
            or (label == "THIRD_PARTY" and bool(NAMED_AA.search(phrase))))

# Rule 10 check 1 (D37): these are PURPOSEs only when the sentence says your data is used/kept for
# them; as rights, procedures or bare headings (no data-use frame) they are not. The words cannot decide, so the tools never
# assert them automatically - a human reads the sentence.
CONTEXT_PURPOSE = re.compile(r"grievance|complaint|dispute|revok|revocation|deregist|withdraw\w* consent"
                             r"|\bkyc\b|merger|acquisition|reorgani[sz]ation|restructuring|sale of (?:assets|business)",
                             re.I)  # D37 + D43: only the sentence decides these


# Rule 16: a THIRD_PARTY needs a data-flow verb in its sentence (checked with the span itself blanked out,
# so "service PROVIDers" cannot vouch for itself).
# ponytail: verb list, not a parser - a flow phrased unusually lands in THIRD_PARTY_CHECK for a human read.
FLOW = re.compile(r"\b(shar\w*|disclos\w*|transfer\w*|sold|sell\w*|provid\w*|made available|access\w*|"
                  r"receiv\w*|pass\w*|process\w*|send\w*|sent|furnish\w*|report\w*|collect\w*|obtain\w*|"
                  r"store\w*|retain\w*|transmit\w*|forward\w*)\b", re.I)


def _bounds(text: str, i: int, j: int) -> tuple[int, int]:
    a = max(text.rfind(".", 0, i), text.rfind(";", 0, i)) + 1
    b = text.find(".", j)
    return a, len(text) if b < 0 else b + 1


def _sentence(text: str, i: int, j: int) -> str:
    a, b = _bounds(text, i, j)
    return " ".join(text[a:b].split())


def _has_flow(text: str, i: int, j: int) -> bool:
    a, b = _bounds(text, i, j)
    return bool(FLOW.search(text[a:i] + " " + text[j:b]))


# Rule 16 direction: "obtained from CDSL/NSDL, registrars (CAMS, KFintech)" - a data SOURCE, not a recipient.
# ponytail: nearest preceding preposition, not a parser - so these go to a human CHECK, never auto-delete.
_PREP = re.compile(r"\b(from|to|with|by)\b", re.I)
# Rule 19: "the SEBI (Investment Advisers) Regulations" - the organisation is only part of a law's name.
_LAW_NAME = re.compile(r"^\s*(?:\([^)]{1,60}\)\s*)?(?:[A-Z][\w&-]*,?\s+){0,6}?"
                       r"(?:Regulations|Act|Rules|Directions|Code|Guidelines)\b")


def _tp_reason(text: str, i: int, j: int) -> str | None:
    """Why a THIRD_PARTY span needs a second look (Rules 16, 19), or None."""
    if _LAW_NAME.match(text[j:j + 90]):
        return "part of a law's or regulation's name (Rule 19)"
    if not _has_flow(text, i, j):
        return "no data-flow verb in the sentence (Rule 16)"
    a, _ = _bounds(text, i, j)
    preps = _PREP.findall(text[a:i])
    if preps and preps[-1].lower() == "from":
        return "data comes FROM them - a source, not a recipient (Rule 16)"
    return None


def _overlaps(a, b) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def adjudicate_doc(text, spans_a, spans_b, lexicon):
    """Return (gold_spans, actions) where actions is a list of (kind, detail) for the worklist."""
    actions = []
    sa, sb = set(spans_a), set(spans_b)

    def dropped(sp):
        return is_dropped(norm(text[sp[0]:sp[1]]), sp[2])

    def suspect(sp):
        """Rules 16/19 (D44): never auto-accept or propagate a THIRD_PARTY these rules put in doubt."""
        return _tp_reason(text, sp[0], sp[1]) if sp[2] == "THIRD_PARTY" else None

    # 1. DELETE - stoplist / AA-role violations, whoever marked them
    deletes = [(sp, who) for who, S in (("A", sa), ("B", sb)) for sp in S if dropped(sp)]
    sa = {s for s in sa if not dropped(s)}
    sb = {s for s in sb if not dropped(s)}
    for sp, who in deletes:
        actions.append(("DELETE", (sp, who, norm(text[sp[0]:sp[1]]))))

    gold: set = set()

    # 2. ACCEPT - exact agreement (unless both broke the same Rule 16/19 - then a human looks)
    for sp in sorted(sa & sb):
        reason = suspect(sp)
        if reason:
            actions.append(("REVIEW_RULE", (sp, norm(text[sp[0]:sp[1]]), reason)))
        else:
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
        if (lexicon.get(phrase) == sp[2] and not (sp[2] == "PURPOSE" and CONTEXT_PURPOSE.search(phrase))
                and not suspect(sp)):
            gold.add(sp)
            actions.append(("ACCEPT_CONSENSUS", (sp, who, phrase)))
        else:
            actions.append(("REVIEW_ONESIDED", (sp, who, phrase)))

    # 7. Rule 7 - propagate every accepted phrase to all its occurrences in this document
    accepted = {}
    for s, e, lab in gold:
        accepted.setdefault(norm(text[s:e]), lab)
    accepted = {p: l for p, l in accepted.items() if len(p) >= 4 and p not in DROP
                and not (l == "PURPOSE" and CONTEXT_PURPOSE.search(p))}   # D37: context decides
    if accepted:
        occ = find_occurrences(text, sorted(accepted, key=lambda p: (-len(p), p)))
        occ.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        last = -1
        for i, j, term in occ:
            if i < last:
                continue
            last = j
            sp = (i, j, accepted[term])
            if not any(s < j and i < e for s, e, _ in gold) and not suspect(sp):
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
    args.out = args.out.resolve()   # relative --out would break relative_to(PROJECT_ROOT)

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
        review = kinds["REVIEW_LABEL"] + kinds["REVIEW_BOUNDARY"] + kinds["REVIEW_ONESIDED"] + kinds["REVIEW_RULE"]
        rows.append({"doc_id": key, "gold": len(gold), "review": review, **kinds})

        by = defaultdict(list)
        for k, d in actions:
            by[k].append(d)
        md = [f"# {key} — adjudication worklist", "",
              f"**Proposed gold: {len(gold)} spans.**  Automatic: "
              f"{kinds['ACCEPT_AGREED']} agreed + {kinds['ACCEPT_CONSENSUS']} consensus + "
              f"{kinds['ADD_REPEAT']} repeats added − {kinds['DELETE']} deleted.", "",
              f"## 👉 YOU ONLY NEED TO READ THIS: {review} items to decide", ""]
        if by["REVIEW_RULE"]:
            md += [f"### Both marked it, but a rule doubts it — keep or delete ({len(by['REVIEW_RULE'])})", ""]
            md += [f"- `{ph}` **{sp[2]}** `[{sp[0]}:{sp[1]}]` — *{why}*" for sp, ph, why in by["REVIEW_RULE"]]
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
          f"  (label {grand['REVIEW_LABEL']}, boundary {grand['REVIEW_BOUNDARY']}, one-sided {grand['REVIEW_ONESIDED']}, "
          f"rule-doubted agreement {grand['REVIEW_RULE']})",
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
          f"boundary {grand['REVIEW_BOUNDARY']}, one-sided {grand['REVIEW_ONESIDED']}, rule {grand['REVIEW_RULE']})")
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

    # D44: agreed indemnity 'affiliates' goes to a human; a data-sharing 'affiliates' is accepted and its
    # repeat in the indemnity clause is NOT propagated into gold
    t2 = "We may share your data with affiliates. You agree to indemnify us and our affiliates."
    a1, a2 = t2.index("affiliates"), t2.rindex("affiliates")
    gold, actions = adjudicate_doc(t2, [(a1, a1 + 10, "THIRD_PARTY")], [(a1, a1 + 10, "THIRD_PARTY")], {})
    assert gold == [(a1, a1 + 10, "THIRD_PARTY")], gold
    gold, actions = adjudicate_doc(t2, [(a2, a2 + 10, "THIRD_PARTY")], [(a2, a2 + 10, "THIRD_PARTY")], {})
    assert not gold and [k for k, _ in actions] == ["REVIEW_RULE"], actions
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
