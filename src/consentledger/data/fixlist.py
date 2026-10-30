"""Per-annotator fix lists: one file per annotator per document, saying what to change in their own export.

Unlike adjudicate.py's joint worklist, each annotator works alone. MECHANICAL buckets need no judgement; CHECK
buckets show the sentence for a human decision. _render describes each bucket and the rule behind it.

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

from consentledger.data.adjudicate import (
    CONTEXT_PURPOSE, DROP, _has_flow, _sentence, _tp_reason, is_dropped,
)
from consentledger.data.annotation_audit import (
    build_consensus_lexicon, find_occurrences, load_corpus, norm,
)
from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")
# Rule 9b: head noun data/information is an umbrella UNLESS the modifier names real content.
R9B_KEEP = {"credit information", "transaction data", "account information",
            "transaction information", "credit data", "identity information", "kyc information"}

# Rule 11: characters that must never sit at a span's edge.
EDGE_CHARS = set(",.;:\"'()[]-")
# Rule 1: leading your/the/a/any/all/such...; Rule 9 step 1: a PURPOSE never starts with to/for/purpose of.
LEAD_ANY = re.compile(r"(?:your|the|a|an|any|all|such|our|its|their)\s+", re.I)
# Rule 1: status words on a DATA_TYPE - "registered email address" -> "email address". Not permanent/
# current/primary: those are part of real field names (Permanent Account Number, current address).
LEAD_STATUS = re.compile(r"(?:registered|verified|valid|updated|latest)\s+", re.I)
# Rule 12: the abbreviation/expansion in the bracket (or quotes) right after a name is its own highlight.
BRACKET_AFTER = re.compile(r"\s*(?:\(\s*[\"']?\s*(?P<c>[^()\"']{1,60}?)\s*[\"']?\s*\)|[\"'](?P<q>[^\"']{1,20})[\"'])")
LEAD_PURPOSE = re.compile(r"(?:(?:in order |so as )?to|for(?: the purposes? of)?|the purposes? of)\s+", re.I)
# Rule 12: a bracketed or quoted tail holding an ABBREVIATION or its EXPANSION is cut off.
BRACKET_TAIL = re.compile(r"\s*\(\s*[\"']?\s*(?P<c>[^()\"']{1,60}?)\s*[\"']?\s*\)\s*$"
                          r"|\s*[\"'](?P<q>[^\"']{1,20})[\"']\s*$")
ACRONYM = re.compile(r"^[A-Z][A-Z0-9-]{1,9}s?$")                    # PAN, REs, IU, SIP, TAN, FIU-IND
EXPANSION = re.compile(r"^[A-Z][a-z]+(?:\s+(?:of|and|&)?\s*[A-Z][a-z]+)+$")   # Permanent Account Number

# Rule 17: each policy's own company names (from its opening text / legal name), keyed by doc_id prefix.
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
    """Apply Rule 12 (cut an abbreviation/expansion tail), Rule 11 (strip edge space/punctuation) and
    Rule 1 / Rule 9 step 1 (strip a leading your/the/any..., and to/for on a PURPOSE).

    Returns (new_span, rule) where rule is "12", "11", "1", "9" or None if nothing changed.
    """
    s, e, lab = sp
    rule = None
    m = BRACKET_TAIL.search(text[s:e])
    if m and m.start() > 0:
        inner = (m.group("c") or m.group("q") or "").strip()
        if ACRONYM.match(inner) or EXPANSION.match(inner):
            e, rule = s + m.start(), "12"
    ns, ne = s, e
    while True:
        while ns < ne and (text[ns].isspace() or text[ns] in EDGE_CHARS):
            ns += 1
        while ne > ns and (text[ne - 1].isspace() or text[ne - 1] in EDGE_CHARS):
            ne -= 1
        lead = ((lab == "PURPOSE" and LEAD_PURPOSE.match(text, ns, ne)) or LEAD_ANY.match(text, ns, ne)
                or (lab == "DATA_TYPE" and LEAD_STATUS.match(text, ns, ne)))
        if not lead or lead.end() >= ne:
            break
        rule = rule or ("9" if lab == "PURPOSE" else "1")
        ns = lead.end()
    if (ns, ne) != (s, e):
        rule = rule or "11"
    if (ns, ne) != (sp[0], sp[1]):
        return (ns, ne, lab), rule
    return sp, None


_CONNECTOR = re.compile(r"\s*(?:,|and|or|,\s*and|,\s*or|/|&)\s*")
# Rule 23b (provided communication content is DATA_TYPE) and Rule 23c (`KYC` as a purpose) - phrases the
# consensus lexicon cannot propose when neither annotator marked them yet. Context decides, so CHECK only.
RULE23_TERMS = {"call recordings": "DATA_TYPE", "video meeting recordings": "DATA_TYPE",
                "voice recordings": "DATA_TYPE", "chat messages": "DATA_TYPE", "whatsapp messages": "DATA_TYPE",
                "text messages": "DATA_TYPE", "sms messages": "DATA_TYPE", "form inputs": "DATA_TYPE",
                "survey responses": "DATA_TYPE", "emails": "DATA_TYPE", "correspondence": "DATA_TYPE"}
_KYC_PURPOSE = re.compile(r"\b(?:required |needed )?for (KYC)\b")


def fixes_for(text, mine, theirs, lexicon, own_vocab, both_vocab, owner_re=None, own_labels=None):
    """Build one annotator's fix buckets for one document.

    own_labels: {phrase: Counter(label)} over this annotator's whole corpus (Rule 22 mis-click check).
    """
    out = defaultdict(list)

    # 1 / 1b. TRIM first (Rules 1, 9, 11, 12), then DELETE on the cleaned phrase (Rules 8, 8b, 9b, 23a) - so
    # '"FIPs"' and 'banks ' are judged as FIPs and banks.
    keep = []
    for sp in mine:
        new, rule = trim_span(text, sp)
        phrase = norm(text[new[0]:new[1]])
        if not phrase or is_dropped(phrase, new[2]):
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

    keep = sorted(set(keep))     # duplicates are reported once, above; every later bucket sees each span once

    # 1f. RELABEL - this phrase usually carries another label in MY own corpus (Rule 22: a mis-click)
    for sp in keep:
        counts = (own_labels or {}).get(norm(text[sp[0]:sp[1]]))
        if counts:
            maj, n = counts.most_common(1)[0]
            if maj != sp[2] and n >= 2 and n >= 2 * counts[sp[2]]:     # a habit, not a single use
                out["RELABEL"].append((sp, maj, n))

    # 1d. OWN_COMPANY - the policy's own company or its own staff marked as THIRD_PARTY (Rule 17)
    for sp in keep:
        if sp[2] != "THIRD_PARTY":
            continue
        p = norm(text[sp[0]:sp[1]])
        if p in STAFF or (owner_re is not None and owner_re.search(p) and not NOT_OWNER.search(p)):
            out["OWN_COMPANY"].append((sp, p))

    # 2 / 3. Suggestions never overlap a highlight, a suggestion (longest first) or deleted text; a THIRD_PARTY
    # only where THAT occurrence passes Rules 16/19 (not indemnity "affiliates", a source or a law's name).
    taken = list(keep) + [sp for sp, _ in out["DELETE"]]
    acronyms = set()            # 3-letter abbreviations (PAN, OTP, UPI) repeat only in the same CAPITALS

    # Rule 12: "Permanent Account Number (PAN)" is TWO highlights - the name, and PAN inside the bracket
    for s, e, lab in keep:
        m = BRACKET_AFTER.match(text, e)
        if not m or (lab == "THIRD_PARTY" and _tp_reason(text, s, e)):
            continue
        i, j = m.span("c" if m.group("c") else "q")
        inner = text[i:j]
        umbrella = norm(inner).split()[-1] in ("data", "information") and norm(inner) not in R9B_KEEP
        if ((ACRONYM.match(inner) or EXPANSION.match(inner)) and not _covered(taken, i, j)
                and not is_dropped(norm(inner), lab) and not umbrella and not CONTEXT_PURPOSE.search(inner)):
            taken.append((i, j, lab))
            out["ADD_REPEAT"].append(((i, j, lab), norm(inner)))

    def _suggest(bucket, terms, label_of):
        for i, j, term in find_occurrences(text, sorted(terms, key=lambda t: (-len(t), t))):
            lab = label_of[term]
            if (_covered(taken, i, j) or text[j:j + 2].lstrip().startswith(":")
                    or (term in acronyms and not ACRONYM.match(text[i:j]))
                    or (lab == "THIRD_PARTY" and _tp_reason(text, i, j))):     # "Address: 1201, ..." is a label
                continue
            taken.append((i, j, lab))
            out[bucket].append(((i, j, lab), term))

    # 2. ADD_REPEAT - occurrences I skipped of phrases I marked in THIS doc. Never copied from a mis-click or a
    # doubtful THIRD_PARTY ("SEBI" inside a regulation's name would otherwise be copied 16 times).
    mis_clicked = {norm(text[sp[0]:sp[1]]) for sp, _, _ in out["RELABEL"]}
    my_phrases = {}
    for s, e, lab in keep:
        p = norm(text[s:e])
        short_acronym = len(p) == 3 and bool(ACRONYM.match(text[s:e])) and not CONTEXT_PURPOSE.search(p)
        if ((len(p) >= 4 or short_acronym) and p not in DROP and p not in mis_clicked
                and not (lab == "PURPOSE" and CONTEXT_PURPOSE.search(p))
                and not (lab == "THIRD_PARTY" and _tp_reason(text, s, e))):
            my_phrases.setdefault(p, lab)
            if short_acronym:
                acronyms.add(p)
    _suggest("ADD_REPEAT", my_phrases, my_phrases)

    # 3. ADD_MISSED - consensus phrases here that I never marked. Context-blind ("title" vs "rights, title and
    # interest"), so a CHECK bucket shown with the sentence.
    already = {norm(text[s:e]) for s, e, _ in keep}
    cand = [p for p in lexicon if p not in already and p not in DROP and len(p) >= 4
            and not (lexicon[p] == "PURPOSE" and CONTEXT_PURPOSE.search(p))]
    _suggest("ADD_MISSED", cand, lexicon)

    # 3b. RULE23_ADD - provided communication content (Rule 23b) and "for KYC" (Rule 23c) left blank
    _suggest("RULE23_ADD", [t for t in RULE23_TERMS if t not in already], RULE23_TERMS)
    for m in _KYC_PURPOSE.finditer(text):
        i, j = m.span(1)
        if not _covered(taken, i, j):
            taken.append((i, j, "PURPOSE"))
            out["RULE23_ADD"].append(((i, j, "PURPOSE"), "kyc"))

    # 1e. THIRD_PARTY_CHECK - no data flow, a data SOURCE, or part of a law's name (Rules 16, 19)
    for sp in keep:
        if sp[2] == "THIRD_PARTY":
            reason = _tp_reason(text, sp[0], sp[1])
            if reason:
                out["THIRD_PARTY_CHECK"].append((sp, reason, _sentence(text, sp[0], sp[1])))

    # 4e. LIST_CHECK - you and they cut the same list differently (Rule 2: complete items -> separate;
    # Rule 14: items sharing a word written once -> one highlight). Only shown where you disagree.
    ks = sorted(keep)
    for a, b in zip(ks, ks[1:]):
        if a[2] == b[2] and _CONNECTOR.fullmatch(text[a[1]:b[0]]):
            whole = next((t for t in theirs if t[2] == a[2] and t[0] <= a[0] and b[1] <= t[1]), None)
            if whole and ("you split", whole) not in out["LIST_CHECK"]:
                out["LIST_CHECK"].append(("you split", whole))
    ts = sorted(theirs)
    for a, b in zip(ts, ts[1:]):
        if a[2] == b[2] and _CONNECTOR.fullmatch(text[a[1]:b[0]]):
            for sp in keep:
                if sp[2] == a[2] and sp[0] <= a[0] and b[1] <= sp[1]:
                    if ("you joined", sp) not in out["LIST_CHECK"]:
                        out["LIST_CHECK"].append(("you joined", sp))
                    break

    # 4. SHORTEN - they marked a shorter version of my span, same label
    for sp in keep:
        for tp in theirs:
            if sp[2] == tp[2] and sp[0] < tp[1] and tp[0] < sp[1] and (tp[1] - tp[0]) < (sp[1] - sp[0]):
                out["SHORTEN"].append((sp, tp, text[sp[0]:sp[1]], text[tp[0]:tp[1]]))
                break

    # 4b. RULE9_SHORTEN - PURPOSE spans longer than 5 words (Rule 9)
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

    # 4d. PURPOSE_CHECK - grievance/dispute/consent-right phrases: a PURPOSE only if the sentence says your
    # data is used or kept for it (Rule 10 check 1). Shown with the sentence so it is a quick read.
    for sp in keep:
        if sp[2] == "PURPOSE" and CONTEXT_PURPOSE.search(text[sp[0]:sp[1]]):
            out["PURPOSE_CHECK"].append((sp, _sentence(text, sp[0], sp[1])))

    # 5. SELF_CHECK - vocabulary only I ever use corpus-wide
    for sp in keep:
        p = norm(text[sp[0]:sp[1]])
        if p in own_vocab and p not in both_vocab:
            out["SELF_CHECK"].append((sp, p))
    return out


MECHANICAL = ("DELETE", "TRIM", "OVERLAP", "OWN_COMPANY", "RELABEL", "ADD_REPEAT", "RULE9_SHORTEN",
              "RULE9B_DELETE")
CHECKS = ("THIRD_PARTY_CHECK", "ADD_MISSED", "RULE23_ADD", "PURPOSE_CHECK", "LIST_CHECK")


def _q(text: str, sp: tuple) -> str:
    return " ".join(text[sp[0]:sp[1]].split())


def _render(name, doc, text, buckets) -> str:
    n_mech = sum(len(buckets[k]) for k in MECHANICAL)
    md = [f"# {name} — fix list for `{doc}`", "",
          f"**{n_mech} mechanical fixes** (no judgement needed) + {len(buckets['SHORTEN'])} to shorten "
          f"+ {sum(len(buckets[k]) for k in CHECKS)} to check in context "
          f"+ {len(buckets['SELF_CHECK'])} to re-read.", "",
          "Offsets are character positions — use them to find the spot fast.", ""]
    if buckets["DELETE"]:
        md += [f"## 1. DELETE these {len(buckets['DELETE'])} — they break Rule 8 / 8b / 9b, or are observed "
               "telemetry (Rule 23a)", ""]
        c = Counter(p for _, p in buckets["DELETE"])
        md += [f"Summary: " + ", ".join(f"`{p}` x{n}" for p, n in c.most_common(15)), ""]
        md += [f"- `{p}` **{sp[2]}** `[{sp[0]}:{sp[1]}]`" for sp, p in buckets["DELETE"][:150]]
    if buckets["TRIM"]:
        md += ["", f"## 1b. TRIM these {len(buckets['TRIM'])} — space/punctuation at an edge (Rule 11), a "
               "bracketed abbreviation to cut off (Rule 12), a leading your/the/any (Rule 1) or a leading "
               "to/for on a PURPOSE (Rule 9)", "",
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
    if buckets["RELABEL"]:
        md += ["", f"## 1f. RELABEL these {len(buckets['RELABEL'])} — elsewhere you always give this phrase another "
               "label: almost certainly a mis-click (Rule 22)", "",
               "*Change the colour, unless the phrase's role truly changes here (\"the communications you send "
               "us\" vs \"to send you communications\").*", ""]
        md += [f"- `{_q(text, sp)}` `[{sp[0]}:{sp[1]}]` is **{sp[2]}** here → **{maj}** (your label for it x{n})"
               for sp, maj, n in buckets["RELABEL"]]
    if buckets["ADD_REPEAT"]:
        md += ["", f"## 2. ADD these {len(buckets['ADD_REPEAT'])} — you marked this phrase elsewhere in "
               "THIS doc but skipped these (Rule 7)", ""]
        c = Counter(t for _, t in buckets["ADD_REPEAT"])
        md += [f"Summary: " + ", ".join(f"`{p}` x{n}" for p, n in c.most_common(15)), ""]
        md += [f"- `{t}` → **{sp[2]}** `[{sp[0]}:{sp[1]}]`" for sp, t in buckets["ADD_REPEAT"][:200]]
    if buckets["THIRD_PARTY_CHECK"]:
        md += ["", f"## 1e. CHECK these {len(buckets['THIRD_PARTY_CHECK'])} THIRD_PARTY spans — keep only if "
               "the sentence says your data goes TO them (Rules 16, 19)", "",
               "*Delete if the sentence is about indemnity, liability, jurisdiction, assignment or regulation, if "
               "your data only comes FROM them, or if the name is just part of a law's title.*", ""]
        md += [f"- `{_q(text, sp)}` `[{sp[0]}:{sp[1]}]` — *{r}* — …{s[:200]}"
               for sp, r, s in buckets["THIRD_PARTY_CHECK"][:80]]
    if buckets["ADD_MISSED"]:
        md += ["", f"## 3. CHECK, then ADD these {len(buckets['ADD_MISSED'])} — both of you endorse this phrase "
               "elsewhere; it appears here and you left it blank", "",
               "*Read the sentence first: add only if the word is used in the SAME SENSE as an entity "
               "(`title` in \"rights, title and interest\" or `assets` in \"sale of assets\" are not data).*", ""]
        for lab in LABELS:
            items = [(sp, t) for sp, t in buckets["ADD_MISSED"] if sp[2] == lab]
            if items:
                md.append(f"**{lab}** ({len(items)}):")
                md += [f"  - `{t}` `[{sp[0]}:{sp[1]}]` — …{_sentence(text, sp[0], sp[1])[:160]}"
                       for sp, t in items[:120]]
    if buckets["RULE23_ADD"]:
        md += ["", f"## 3b. CHECK, then ADD these {len(buckets['RULE23_ADD'])} — Rule 23 phrases left blank", "",
               "*DATA_TYPE: communication content YOU send (\"we keep call recordings and emails you send us\") — "
               "not a channel they use (\"we send you emails\"). PURPOSE `KYC`: only where your data is "
               "collected or used for it.*", ""]
        md += [f"- `{_q(text, sp)}` → **{sp[2]}** `[{sp[0]}:{sp[1]}]` — …{_sentence(text, sp[0], sp[1])[:160]}"
               for sp, _ in buckets["RULE23_ADD"][:80]]
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
    if buckets["PURPOSE_CHECK"]:
        md += ["", f"## 4d. CHECK these {len(buckets['PURPOSE_CHECK'])} PURPOSE spans — keep only if the sentence "
               "says your data is used or kept for it (Rule 10, check 1)", "",
               "*Keep: \"we use your information for… addressing grievances\". Delete: your rights (\"you may "
               "raise a grievance\", \"revoke consent\"), procedures (\"Grievance Redressal Policy\"), "
               "contract clauses, a bare heading with no data-use frame.*", ""]
        for sp, sentence in buckets["PURPOSE_CHECK"][:60]:
            md.append(f"- `{_q(text, sp)}` `[{sp[0]}:{sp[1]}]` — …{sentence[:220]}")
    if buckets["LIST_CHECK"]:
        md += ["", f"## 4e. CHECK these {len(buckets['LIST_CHECK'])} lists — you and the other annotator cut them "
               "differently (Rules 2, 14)", "",
               "*Each item complete on its own (\"bank statements, mutual funds\") → separate highlights. Items "
               "sharing a word written once (\"identity and contact information\", \"detect, investigate and "
               "prevent fraud\") → ONE highlight.*", ""]
        md += [f"- {kind}: `{_q(text, sp)}` ({sp[2]}) `[{sp[0]}:{sp[1]}]`" for kind, sp in buckets["LIST_CHECK"]]
    if buckets["SELF_CHECK"]:
        md += ["", f"## 5. RE-READ these {len(buckets['SELF_CHECK'])} — only you ever mark this phrase "
               "anywhere in the corpus", "",
               "*Test: is it a SPECIFIC kind of data you provide (not an umbrella word, not device telemetry), a "
               "nameable activity on the Rule 10 list, or a real organisation your data goes to?* "
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

    def label_counts(X):
        c = defaultdict(Counter)
        for d in X.values():
            for s, e, lab in d["spans"]:
                c[norm(d["text"][s:e])][lab] += 1
        return c

    totals = {args.name_a: Counter(), args.name_b: Counter()}
    per_doc = {args.name_a: {}, args.name_b: {}}
    for name, X, Y, own in ((args.name_a, A, B, va), (args.name_b, B, A, vb)):
        d = args.out / name
        d.mkdir(parents=True, exist_ok=True)
        own_labels = label_counts(X)
        for key in docs:
            text = corpus[key]
            buckets = fixes_for(text, X[key]["spans"], Y[key]["spans"], lexicon, own, both,
                                owner_re=owner_regex(key), own_labels=own_labels)
            (d / f"{key}.md").write_text(_render(name, key, text, buckets), encoding="utf-8")
            counts = {k: len(v) for k, v in buckets.items()}
            per_doc[name][key] = counts
            totals[name].update(counts)

    cols = ("DELETE", "TRIM", "OVERLAP", "OWN_COMPANY", "RELABEL", "THIRD_PARTY_CHECK",
            "ADD_REPEAT", "ADD_MISSED", "RULE23_ADD", "RULE9_SHORTEN", "RULE9B_DELETE", "PURPOSE_CHECK",
            "LIST_CHECK", "SELF_CHECK")
    md = ["# Per-annotator fix lists", "",
          "Each annotator works **alone, in parallel**, on their own file. Mechanical buckets (exact offsets, no "
          "judgement): 1, 1b, 1c, 1d, 1f, 2, 4b, 4c. Check-in-context buckets (sentence shown): 1e, 3, 3b, 4d, "
          "4e. 4 and 5 are quick reads.", ""]
    for name in (args.name_a, args.name_b):
        t = totals[name]
        mech = sum(t[k] for k in MECHANICAL)
        md += [f"## {name} — {mech} mechanical fixes, {t['SHORTEN']} shorten, {t['SELF_CHECK']} re-read", "",
               f"- DELETE (Rules 8/8b/9b/23a): **{t['DELETE']}**",
               f"- TRIM (Rules 1/9/11/12): **{t['TRIM']}**",
               f"- OVERLAP (Rule 15): **{t['OVERLAP']}**",
               f"- OWN_COMPANY (Rule 17): **{t['OWN_COMPANY']}**",
               f"- RELABEL (Rule 22): **{t['RELABEL']}**",
               f"- ADD_REPEAT (Rule 7): **{t['ADD_REPEAT']}**",
               f"- THIRD_PARTY_CHECK (Rules 16/19, check in context): {t['THIRD_PARTY_CHECK']}",
               f"- ADD_MISSED (consensus phrase left blank, check in context): {t['ADD_MISSED']}",
               f"- RULE23_ADD (communications / KYC left blank, check in context): {t['RULE23_ADD']}",
               f"- RULE9 shorten / RULE9b delete: **{t['RULE9_SHORTEN']}** / **{t['RULE9B_DELETE']}**",
               f"- SHORTEN: {t['SHORTEN']}", f"- PURPOSE_CHECK (Rule 10 check 1): {t['PURPOSE_CHECK']}",
               f"- LIST_CHECK (Rules 2/14, check in context): {t['LIST_CHECK']}",
               f"- SELF_CHECK: {t['SELF_CHECK']}", "",
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
              f"own-company {t['OWN_COMPANY']}, relabel {t['RELABEL']}, +repeat {t['ADD_REPEAT']}, "
              f"R9-shorten {t['RULE9_SHORTEN']}, R9b-delete {t['RULE9B_DELETE']}), "
              f"check: +missed {t['ADD_MISSED']}, +rule23 {t['RULE23_ADD']}, third-party {t['THIRD_PARTY_CHECK']}, "
              f"purpose {t['PURPOSE_CHECK']}, list {t['LIST_CHECK']}; "
              f"self-check {t['SELF_CHECK']}")
    print(f"wrote {args.out / 'README.md'} + {args.name_a}/*.md + {args.name_b}/*.md")


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
    pan = t3.index("PAN")                                               # ...and PAN becomes its own highlight
    assert ((pan, pan + 3, "DATA_TYPE"), "pan") in o3["ADD_REPEAT"], o3["ADD_REPEAT"]
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
    assert flagged == ["icici hfc limited", "officers"], flagged   # Rule 1 trims "its" first

    # a grievance PURPOSE is checked, never auto-propagated
    t7 = "We use your data for grievance redressal. You may raise a grievance under grievance redressal."
    g0 = t7.index("grievance redressal")
    o7 = fixes_for(t7, [(g0, g0 + 19, "PURPOSE")], [], {"grievance redressal": "PURPOSE"}, set(), set())
    assert not o7["ADD_REPEAT"] and not o7["ADD_MISSED"], o7
    assert len(o7["PURPOSE_CHECK"]) == 1, o7

    # Rule 16: indemnity 'affiliates' is checked, never propagated; a data-flow repeat IS propagated.
    # Rule 15: a nested lexicon term ('service providers' inside 'third-party service providers') is not suggested.
    t8 = ("We may share your data with affiliates and third-party service providers. "
          "You agree to indemnify us, our affiliates and agents against all claims.")
    a1 = t8.index("affiliates")
    o8 = fixes_for(t8, [(a1, a1 + 10, "THIRD_PARTY"), (t8.rindex("affiliates"), t8.rindex("affiliates") + 10,
                                                        "THIRD_PARTY")], [],
                   {"third-party service providers": "THIRD_PARTY", "service providers": "THIRD_PARTY",
                    "agents": "THIRD_PARTY"}, set(), set())
    assert [t for _, t in o8["ADD_MISSED"]] == ["third-party service providers"], o8["ADD_MISSED"]
    assert len(o8["THIRD_PARTY_CHECK"]) == 1 and o8["THIRD_PARTY_CHECK"][0][0][0] == t8.rindex("affiliates")
    assert not _has_flow("You agree to indemnify our service providers.", 26, 43)   # span can't vouch for itself

    # each detector, on the real annotation error it was built from
    def one(t, phrase, lab, **kw):
        i = t.index(phrase)
        return fixes_for(t, [(i, i + len(phrase), lab)], kw.pop("theirs", []), {}, set(), set(), **kw)

    def trimmed(o):
        return [(text_[n[0]:n[1]], r) for _, n, r in o["TRIM"]]
    text_ = "We do this To assess your suitability and to verify your identity."
    assert trimmed(one(text_, "To assess your suitability", "PURPOSE")) == [("assess your suitability", "9")]
    text_ = "We collect your mobile number."
    assert trimmed(one(text_, "your mobile number", "DATA_TYPE")) == [("mobile number", "1")]
    text_ = "shared with the Financial Intelligence Unit (FIU-IND), exchanges"
    assert trimmed(one(text_, "Financial Intelligence Unit (FIU-IND)", "THIRD_PARTY")) == \
        [("Financial Intelligence Unit", "12")]
    for phrase, lab in (("type of browser", "DATA_TYPE"), ("IMEI", "DATA_TYPE"), ("web beacons", "DATA_TYPE"),
                        ("NESL Asset Data", "THIRD_PARTY"), ("financial details", "DATA_TYPE")):
        assert one(f"we use {phrase} here", phrase, lab)["DELETE"], phrase
    assert not one("we collect IMEI here", "IMEI", "PURPOSE")["DELETE"]        # telemetry rule is DATA_TYPE-only
    o = one("We may share passwords with banks.", "passwords", "THIRD_PARTY",
            own_labels={"passwords": Counter({"DATA_TYPE": 7, "THIRD_PARTY": 1})})
    assert o["RELABEL"] == [((13, 22, "THIRD_PARTY"), "DATA_TYPE", 7)], o["RELABEL"]
    t9 = "Statements obtained from CDSL/NSDL, registrars (CAMS, KFintech). Rules of the UIDAI (Authentication) Regulations apply to processing."
    o = one(t9, "CAMS", "THIRD_PARTY")
    assert "FROM" in o["THIRD_PARTY_CHECK"][0][1], o["THIRD_PARTY_CHECK"]
    o = one(t9, "UIDAI", "THIRD_PARTY")
    assert "law" in o["THIRD_PARTY_CHECK"][0][1], o["THIRD_PARTY_CHECK"]
    # a table row label is ordinary text: a recipient under a sharing lead-in passes Rule 16 (the lead-in's verb
    # is in its sentence) and its repeats are proposed
    t10 = ("Your data may be shared with the following recipients:\nService providers\n— cloud (AWS)\n"
           "PostHog\n— for product analytics\nService providers\n— document storage\n")
    o = one(t10, "PostHog", "THIRD_PARTY")
    assert not o["THIRD_PARTY_CHECK"], o["THIRD_PARTY_CHECK"]
    o = one(t10, "Service providers", "THIRD_PARTY")
    assert [t for _, t in o["ADD_REPEAT"]] == ["service providers"], o["ADD_REPEAT"]
    t11 = "Communications: Emails, call recordings, and documents. Aadhaar (where required for KYC), photo."
    o = fixes_for(t11, [], [], {}, set(), set())
    assert sorted((t11[s:e], lab) for (s, e, lab), _ in o["RULE23_ADD"]) == \
        [("Emails", "DATA_TYPE"), ("KYC", "PURPOSE"), ("call recordings", "DATA_TYPE")], o["RULE23_ADD"]
    t12 = "to detect, investigate and prevent fraud"
    d0, i0 = t12.index("detect"), t12.index("investigate")
    split = [(d0, d0 + 6, "PURPOSE"), (i0, len(t12), "PURPOSE")]
    joined = [(d0, len(t12), "PURPOSE")]
    assert fixes_for(t12, split, joined, {}, set(), set())["LIST_CHECK"][0][0] == "you split"
    assert fixes_for(t12, joined, split, {}, set(), set())["LIST_CHECK"][0][0] == "you joined"
    # a doubted span is never the source of Rule 7 copies; field labels ("Address: ...") are never suggested
    t13 = ("Governed by the UIDAI (Authentication) Regulations. We share data with UIDAI on request. "
           "Registered Address: 12 MG Road.")
    s0 = t13.index("UIDAI")
    assert not one(t13, "UIDAI", "THIRD_PARTY")["ADD_REPEAT"]
    assert not fixes_for(t13, [], [], {"address": "DATA_TYPE"}, set(), set())["ADD_MISSED"]
    assert len(fixes_for(t13, [(s0, s0 + 5, "THIRD_PARTY")] * 2, [], {}, set(), set())["THIRD_PARTY_CHECK"]) == 1
    # status word trimmed; bracket abbreviation proposed after a name marked WITHOUT its bracket; a banned
    # abbreviation is not; a 3-letter acronym repeats only in capitals
    text_ = "via your registered email address"
    assert trimmed(one(text_, "registered email address", "DATA_TYPE")) == [("email address", "1")]
    t14 = 'We need your Permanent Account Number (PAN) and the PAN again, not a pan. Financial Information Provider ("FIP").'
    o = one(t14, "Permanent Account Number", "DATA_TYPE")
    assert [t14[s:e] for (s, e, _), _ in o["ADD_REPEAT"]] == ["PAN"], o["ADD_REPEAT"]
    p0 = t14.index("PAN")
    o = fixes_for(t14, [(p0, p0 + 3, "DATA_TYPE")], [], {}, set(), set())
    assert [(s, t14[s:e]) for (s, e, _), _ in o["ADD_REPEAT"]] == [(t14.index("PAN again"), "PAN")], o["ADD_REPEAT"]
    assert one("disclose to SEBI on request", "SEBI", "THIRD_PARTY")["DELETE"]
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
