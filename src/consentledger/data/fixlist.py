"""Per-annotator fix lists: tell EACH annotator exactly what to change, where, in their own export.

adjudicate.py produces a JOINT worklist - it assumes P1 and P4 sit together and decide 1,351 items.
This module instead produces ONE FILE PER ANNOTATOR PER DOCUMENT, so both can work alone, in parallel,
in their own Label Studio project. After both apply their fixes and re-export, agreement should jump
because most one-sided spans are simply the other person's omission.

Buckets, ordered most-certain first (1-4c are mechanical, with exact character offsets):

  1.  DELETE        - your span breaks Rule 8 (stoplist) or Rule 8b (AA roles).
  1b. TRIM          - Rule 11 (space/punctuation at an edge) or Rule 12 (bracketed abbreviation tail):
                      the corrected span is given.
  1c. OVERLAP       - Rule 15: two of your highlights overlap, nest or duplicate - keep the outer one.
  1d. OWN_COMPANY   - Rule 17: a THIRD_PARTY that is the policy's own company or its own staff.
  2.  ADD_REPEAT    - you marked this phrase elsewhere IN THIS SAME DOCUMENT but skipped this occurrence
                      (Rule 7).
  3.  ADD_MISSED    - the phrase is in the corpus consensus lexicon (BOTH of you endorse it somewhere),
                      appears here, and you did not mark it.
  4b. RULE9_SHORTEN - PURPOSE span over 5 words (Rule 9).
  4c. RULE9B_DELETE - umbrella data/information with a non-content modifier (Rule 9b).
  4.  SHORTEN       - the other annotator marked a shorter version of your span (Rule 1). Quick read.
  5.  SELF_CHECK    - a phrase only YOU ever use in the corpus. Needs judgement (Rule 8 test).

Usage:
    python -m consentledger.data.fixlist --corpus data/aa/annotated/ls_import_tasks.json \\
        --a data/aa/annotated/ExportA.json --b data/aa/annotated/ExportB.json \\
        --name-a P1 --name-b P4
"""
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

from consentledger.data.adjudicate import DROP
from consentledger.data.annotation_audit import (
    build_consensus_lexicon, find_occurrences, load_corpus, norm,
)
from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")
# Rule 9b: head noun data/information is an umbrella UNLESS the modifier names real content.
R9B_KEEP = {"credit information", "transaction data", "account information", "financial data",
            "transaction information", "credit data", "identity information", "kyc information"}

# Rule 11: characters that must never sit at a span's edge.
EDGE_CHARS = set(",.;:\"'()[]-")
# Rule 12: a bracketed or quoted tail holding an ABBREVIATION or its EXPANSION is cut off.
BRACKET_TAIL = re.compile(r"\s*\(\s*[\"']?\s*(?P<c>[^()\"']{1,60}?)\s*[\"']?\s*\)\s*$"
                          r"|\s*[\"'](?P<q>[^\"']{1,20})[\"']\s*$")
ACRONYM = re.compile(r"^[A-Z][A-Z0-9]{1,7}s?$")                     # PAN, REs, IU, SIP, TAN
EXPANSION = re.compile(r"^[A-Z][a-z]+(?:\s+(?:of|and|&)?\s*[A-Z][a-z]+)+$")   # Permanent Account Number

# Rule 17: each policy's own company names, taken from the document's own opening text / legal name
# (extend when documents are added). Keyed by doc_id prefix.
OWNERS = {
    "01_setu": r"setu|agya", "06_setu": r"setu|agya", "22_setu": r"setu|agya",
    "02_digio": r"digio",
    "03_oms": r"\boms", "16_oms": r"\boms",
    "04_pb_fintech": r"pb financial|pb fintech|pbfintech", "17_pb_fintech": r"pb financial|pb fintech|pbfintech",
    "05_onemoney": r"finsec|one\s?money",
    "08_pennydrop": r"shankar fininvest|penny\s?drop",
    "09_saafe": r"dashboard account aggregation|saafe", "19_saafe": r"dashboard account aggregation|saafe",
    "10_perfios": r"perfios",
    "12_scoremeaa": r"score\s?me", "20_scoremeaa": r"score\s?me",
    "14_nadl": r"nesl|nadl", "21_nadl": r"nesl|nadl",
    "23_upmint": r"upmint",
    "24_credbuddha": r"credbuddha",
    "25_the_financiali": r"finfam|financiali",
    "26_zerodha": r"zerodha",
    "28_indifi": r"indifi|riviera investors",
    "29_icici": r"icici",
}
# ...but "ICICI HFC group companies", "Zerodha's affiliates" ARE other entities -> not the owner.
NOT_OWNER = re.compile(r"\b(group|affiliat\w*|subsidiar\w*|partner\w*|associate\w*|parent|sister)\b")
STAFF = {"officers", "directors", "employees", "staff", "support team", "our staff", "our employees",
         "its officers", "its directors", "its employees", "our support team", "customer support team"}


def owner_regex(doc_id: str):
    for prefix, pat in OWNERS.items():
        if doc_id.startswith(prefix):
            return re.compile(rf"\b(?:{pat})", re.I)
    return None


def _covered(spans, i, j) -> bool:
    return any(s < j and i < e for s, e, _ in spans)


def trim_span(text: str, sp: tuple) -> tuple[tuple, str | None]:
    """Apply Rule 12 (cut an abbreviation/expansion tail) then Rule 11 (strip edge space/punctuation).

    Returns (new_span, rule) where rule is "12", "11" or None if nothing changed.
    """
    s, e, lab = sp
    rule = None
    m = BRACKET_TAIL.search(text[s:e])
    if m and m.start() > 0:
        inner = (m.group("c") or m.group("q") or "").strip()
        if ACRONYM.match(inner) or EXPANSION.match(inner):
            e, rule = s + m.start(), "12"
    ns, ne = s, e
    while ns < ne and (text[ns].isspace() or text[ns] in EDGE_CHARS):
        ns += 1
    while ne > ns and (text[ne - 1].isspace() or text[ne - 1] in EDGE_CHARS):
        ne -= 1
    if (ns, ne) != (s, e):
        rule = rule or "11"
    if (ns, ne) != (sp[0], sp[1]):
        return (ns, ne, lab), rule
    return sp, None


def fixes_for(text, mine, theirs, lexicon, own_vocab, both_vocab, owner_re=None):
    """Build one annotator's fix buckets for one document."""
    out = defaultdict(list)

    # 1 / 1b. TRIM first (Rules 11, 12), then DELETE on the cleaned phrase (Rules 8, 8b) - so '"FIPs"'
    # and 'banks ' are judged as FIPs and banks.
    keep = []
    for sp in mine:
        new, rule = trim_span(text, sp)
        phrase = norm(text[new[0]:new[1]])
        if not phrase or phrase in DROP:
            out["DELETE"].append((sp, phrase or "(empty after trimming)"))
            continue
        if rule:
            out["TRIM"].append((sp, new, rule))
        keep.append(new)

    # 1c. OVERLAP - my own highlights that overlap, nest or duplicate (Rule 15): keep the outer one
    ordered = sorted(keep, key=lambda x: (x[0], -(x[1] - x[0])))
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if b[0] >= a[1]:
                break
            if (a[0], a[1]) == (b[0], b[1]):
                kind = "duplicate" if a[2] == b[2] else "same words, two labels"
                out["OVERLAP"].append((kind, a, b))
            else:
                outer, inner = (a, b) if (a[1] - a[0]) >= (b[1] - b[0]) else (b, a)
                nested = outer[0] <= inner[0] and inner[1] <= outer[1]
                out["OVERLAP"].append(("nested" if nested else "overlapping", outer, inner))

    # 1d. OWN_COMPANY - the policy's own company or its own staff marked as THIRD_PARTY (Rule 17)
    for sp in keep:
        if sp[2] != "THIRD_PARTY":
            continue
        p = norm(text[sp[0]:sp[1]])
        if p in STAFF or (owner_re is not None and owner_re.search(p) and not NOT_OWNER.search(p)):
            out["OWN_COMPANY"].append((sp, p))

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

    # 4b. RULE9_SHORTEN - PURPOSE spans longer than 5 words (round-2 failure, D32)
    for sp in keep:
        if sp[2] != "PURPOSE":
            continue
        phrase = text[sp[0]:sp[1]]
        n_words = len(phrase.split())
        if n_words > 5:
            out["RULE9_SHORTEN"].append((sp, phrase, n_words))

    # 4c. RULE9B_DELETE - head noun is data/information with a non-content modifier
    for sp in keep:
        p_norm = norm(text[sp[0]:sp[1]])
        words = p_norm.split()
        if words and words[-1] in ("data", "information") and p_norm not in R9B_KEEP:
            out["RULE9B_DELETE"].append((sp, p_norm))

    # 5. SELF_CHECK - vocabulary only I ever use corpus-wide
    for sp in keep:
        p = norm(text[sp[0]:sp[1]])
        if p in own_vocab and p not in both_vocab:
            out["SELF_CHECK"].append((sp, p))
    return out


MECHANICAL = ("DELETE", "TRIM", "OVERLAP", "OWN_COMPANY", "ADD_REPEAT", "ADD_MISSED",
              "RULE9_SHORTEN", "RULE9B_DELETE")


def _q(text: str, sp: tuple) -> str:
    return " ".join(text[sp[0]:sp[1]].split())


def _render(name, doc, text, buckets) -> str:
    n_mech = sum(len(buckets[k]) for k in MECHANICAL)
    md = [f"# {name} — fix list for `{doc}`", "",
          f"**{n_mech} mechanical fixes** (no judgement needed) + {len(buckets['SHORTEN'])} to shorten "
          f"+ {len(buckets['SELF_CHECK'])} to re-read.", "",
          "Offsets are character positions — use them to find the spot fast.", ""]
    if buckets["DELETE"]:
        md += [f"## 1. DELETE these {len(buckets['DELETE'])} — they break Rule 8 / 8b", ""]
        c = Counter(p for _, p in buckets["DELETE"])
        md += [f"Summary: " + ", ".join(f"`{p}` x{n}" for p, n in c.most_common(15)), ""]
        md += [f"- `{p}` **{sp[2]}** `[{sp[0]}:{sp[1]}]`" for sp, p in buckets["DELETE"][:150]]
    if buckets["TRIM"]:
        md += ["", f"## 1b. TRIM these {len(buckets['TRIM'])} — space/punctuation at an edge (Rule 11) or a "
               "bracketed abbreviation to cut off (Rule 12)", "",
               "*Delete the highlight and re-draw it over exactly the corrected words.*", ""]
        for old, new, rule in buckets["TRIM"][:150]:
            md.append(f"- Rule {rule}: `{text[old[0]:old[1]]!r}` → **`{_q(text, new)}`** "
                      f"`[{new[0]}:{new[1]}]` ({new[2]})")
    if buckets["OVERLAP"]:
        md += ["", f"## 1c. FIX these {len(buckets['OVERLAP'])} overlapping / duplicate highlights (Rule 15)", "",
               "*One stretch of text carries one highlight. Keep the outer (longer) one, delete the other. "
               "For 'same words, two labels', keep the correct label only (Rule 22).*", ""]
        for kind, keep_sp, drop_sp in buckets["OVERLAP"][:100]:
            if kind == "same words, two labels":
                md.append(f"- {kind}: `{_q(text, keep_sp)}` `[{keep_sp[0]}:{keep_sp[1]}]` is marked both "
                          f"**{keep_sp[2]}** and **{drop_sp[2]}** — delete the wrong one")
            else:
                md.append(f"- {kind}: keep `{_q(text, keep_sp)}` ({keep_sp[2]}) — delete "
                          f"`{_q(text, drop_sp)}` ({drop_sp[2]}) `[{drop_sp[0]}:{drop_sp[1]}]`")
    if buckets["OWN_COMPANY"]:
        md += ["", f"## 1d. DELETE these {len(buckets['OWN_COMPANY'])} — the policy's own company or its own "
               "staff is never a THIRD_PARTY (Rule 17)", ""]
        md += [f"- `{p}` `[{sp[0]}:{sp[1]}]`" for sp, p in buckets["OWN_COMPANY"][:80]]
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
    if buckets["RULE9_SHORTEN"]:
        md += ["", f"## 4b. SHORTEN these {len(buckets['RULE9_SHORTEN'])} PURPOSE spans to 5 words max "
               "(Rule 9)", "",
               "*Drop the leading `to`/`for`, stop at the object, delete every trailing "
               "`with…/within…/through…/of the…` clause, then count.*", ""]
        for sp, phrase, n in sorted(buckets["RULE9_SHORTEN"], key=lambda x: -x[2])[:120]:
            md.append(f"- ({n} words) `{' '.join(phrase.split())}` `[{sp[0]}:{sp[1]}]`")
    if buckets["RULE9B_DELETE"]:
        md += ["", f"## 4c. DELETE these {len(buckets['RULE9B_DELETE'])} — umbrella `data`/`information` "
               "with a non-content modifier (Rule 9b)", ""]
        c = Counter(ph for _, ph in buckets["RULE9B_DELETE"])
        md += [f"- `{ph}` x{n}" for ph, n in c.most_common(60)]
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
    args.out = args.out.resolve()

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
            buckets = fixes_for(text, X[key]["spans"], Y[key]["spans"], lexicon, own, both,
                                owner_re=owner_regex(key))
            (d / f"{key}.md").write_text(_render(name, key, text, buckets), encoding="utf-8")
            counts = {k: len(v) for k, v in buckets.items()}
            per_doc[name][key] = counts
            totals[name].update(counts)

    cols = ("DELETE", "TRIM", "OVERLAP", "OWN_COMPANY", "ADD_REPEAT", "ADD_MISSED",
            "RULE9_SHORTEN", "RULE9B_DELETE", "SELF_CHECK")
    md = ["# Per-annotator fix lists", "",
          "Each annotator works **alone, in parallel**, on their own file. Buckets 1-4c are mechanical "
          "(exact offsets, no judgement); 4 and 5 are quick reads.", ""]
    for name in (args.name_a, args.name_b):
        t = totals[name]
        mech = sum(t[k] for k in MECHANICAL)
        md += [f"## {name} — {mech} mechanical fixes, {t['SHORTEN']} shorten, {t['SELF_CHECK']} re-read", "",
               f"- DELETE (Rules 8/8b): **{t['DELETE']}**",
               f"- TRIM (Rules 11/12): **{t['TRIM']}**",
               f"- OVERLAP (Rule 15): **{t['OVERLAP']}**",
               f"- OWN_COMPANY (Rule 17): **{t['OWN_COMPANY']}**",
               f"- ADD_REPEAT (Rule 7): **{t['ADD_REPEAT']}**",
               f"- ADD_MISSED (consensus phrase left blank): **{t['ADD_MISSED']}**",
               f"- RULE9 shorten / RULE9b delete: **{t['RULE9_SHORTEN']}** / **{t['RULE9B_DELETE']}**",
               f"- SHORTEN: {t['SHORTEN']}", f"- SELF_CHECK: {t['SELF_CHECK']}", "",
               "| doc | " + " | ".join(c.lower() for c in cols) + " |",
               "|---|" + "---|" * len(cols)]
        for key in docs:
            c = per_doc[name][key]
            md.append(f"| {key} | " + " | ".join(str(c.get(col, 0)) for col in cols) + " |")
        md.append("")
    (args.out / "README.md").write_text("\n".join(md), encoding="utf-8")

    for name in (args.name_a, args.name_b):
        t = totals[name]
        mech = sum(t[k] for k in MECHANICAL)
        print(f"{name}: {mech} mechanical (delete {t['DELETE']}, trim {t['TRIM']}, overlap {t['OVERLAP']}, "
              f"own-company {t['OWN_COMPANY']}, +repeat {t['ADD_REPEAT']}, +missed {t['ADD_MISSED']}, "
              f"R9-shorten {t['RULE9_SHORTEN']}, R9b-delete {t['RULE9B_DELETE']}), "
              f"self-check {t['SELF_CHECK']}")
    print(f"wrote {(args.out / 'README.md').relative_to(PROJECT_ROOT)} + {args.name_a}/*.md + {args.name_b}/*.md")


def _selfcheck() -> None:
    text = "We collect bank statements for loans. Third parties get bank statements too."
    bs, tp = text.index("bank statements"), text.index("Third parties")
    mine = [(bs, bs + 15, "DATA_TYPE"), (tp, tp + 13, "THIRD_PARTY")]
    out = fixes_for(text, mine, [], {"bank statements": "DATA_TYPE"},
                    {"bank statements", "third parties"}, {"bank statements"})
    assert len(out["DELETE"]) == 1, out            # 'Third parties' -> Rule 8
    assert len(out["ADD_REPEAT"]) == 1, out        # 2nd 'bank statements' skipped
    long_p = "to raise a grievance with the grievance resolution officer of the FIU"
    t2 = f"We act {long_p} using client data."
    lp, cd = t2.index(long_p), t2.index("client data")
    o2 = fixes_for(t2, [(lp, lp + len(long_p), "PURPOSE"), (cd, cd + 11, "DATA_TYPE")], [], {}, set(), set())
    assert len(o2["RULE9_SHORTEN"]) == 1, o2
    assert len(o2["RULE9B_DELETE"]) == 1, o2

    # Rule 11: edge space / comma  |  Rule 12: abbreviation tail cut, qualifier tail kept
    t3 = "We share with banks , Permanent Account Number (PAN) and Government Securities (Tradable)."
    b0 = t3.index("banks")
    p0 = t3.index("Permanent")
    g0 = t3.index("Government")
    o3 = fixes_for(t3, [(b0 - 1, b0 + 7, "THIRD_PARTY"),
                        (p0, p0 + len("Permanent Account Number (PAN)"), "DATA_TYPE"),
                        (g0, g0 + len("Government Securities (Tradable)"), "DATA_TYPE")], [], {}, set(), set())
    fixed = {t3[n[0]:n[1]]: r for _, n, r in o3["TRIM"]}
    assert fixed.get("banks") == "11", fixed
    assert fixed.get("Permanent Account Number") == "12", fixed
    assert "Government Securities" not in fixed, fixed               # "(Tradable)" is not an abbreviation
    # Rule 8b after trimming: '"FIPs"' is still an AA role
    t4 = 'the "FIPs" will send data'
    f0 = t4.index('"FIPs"')
    assert len(fixes_for(t4, [(f0, f0 + 6, "THIRD_PARTY")], [], {}, set(), set())["DELETE"]) == 1

    # Rule 15: duplicate + nested
    t5 = "for verifying income details and username checks"
    v0, i0, u0 = t5.index("verifying"), t5.index("income details"), t5.index("username")
    o5 = fixes_for(t5, [(v0, i0 + 14, "PURPOSE"), (i0, i0 + 14, "DATA_TYPE"),
                        (u0, u0 + 8, "DATA_TYPE"), (u0, u0 + 8, "DATA_TYPE")], [], {}, set(), set())
    kinds = sorted(k for k, _, _ in o5["OVERLAP"])
    assert kinds == ["duplicate", "nested"], kinds

    # Rule 17: own company flagged, its group companies are not, own staff flagged
    t6 = "ICICI HFC Limited may share data with ICICI HFC group companies and its officers."
    a0 = t6.index("ICICI HFC Limited")
    g1 = t6.index("ICICI HFC group companies")
    o0 = t6.index("its officers")
    o6 = fixes_for(t6, [(a0, a0 + 17, "THIRD_PARTY"), (g1, g1 + 25, "THIRD_PARTY"),
                        (o0, o0 + 12, "THIRD_PARTY")], [], {}, set(), set(),
                   owner_re=owner_regex("29_icici_home_fin_terms"))
    flagged = sorted(p for _, p in o6["OWN_COMPANY"])
    assert flagged == ["icici hfc limited", "its officers"], flagged
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
