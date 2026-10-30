"""Faithfulness gate for a passage summary: facts kept, names/numbers invented, meaning reversed, party swapped.

  kept      passage facts recognisable in the summary (the same overlap rule as build_dataset.check)
  invented  numbers, names or acronyms the passage never mentions
  reversed  a summary clause takes the opposite stance of the passage clause it restates; an exception or
            condition lifts a negation ("will not share without consent" affirms sharing with consent)
  swapped   the same stance with the other party acting ("you may assign" for "we may assign")
Verdict: reject (invented/reversed/swapped: show the facts instead), add (facts missing: list them), or show.
Facts are (text, label, start) triples; `start` is a character offset into the passage, or None.

    python -m consentledger.summ.faithfulness --selfcheck
    python -m consentledger.summ.faithfulness score --data data/summ/dev.jsonl data/summ/chunks_train.jsonl --preds <dev_predictions.jsonl>
(the second --data file supplies each passage's previous passage as context)
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from consentledger.data.relaxed_agreement import FUNCTION_WORDS, content_words, overlap_coeff

CORE = {"not", "no", "never", "none", "nothing", "nobody", "neither", "nor", "cannot", "can't", "won't",
        "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't", "shouldn't", "wouldn't",
        "couldn't", "mustn't", "shan't", "disclaim", "disclaims", "disclaimed", "prohibited", "prohibit",
        "prohibits", "forbidden", "refrain"}
EXCEPT = {"except", "unless", "excluding", "otherthan"}         # lift a negation wherever they stand
WITHOUT = "without"                                              # a condition after a negation, else a negation
MODAL = "shall|will|may|must|can|cannot|could|would|should|might|does|do|did|is|are|was|were|has|have"
MAIN_MODAL = {"shall", "will", "may", "must", "can", "cannot", "could", "would", "should", "might"}
COMPLEMENT = {"agree", "agrees", "acknowledge", "acknowledges", "confirm", "confirms", "understand", "understands",
              "note", "notes", "clarify", "clarifies", "ensure", "ensures", "warrant", "warrants", "represent",
              "represents", "declare", "declares", "accept", "accepts", "mean", "means", "say", "says", "state",
              "states", "undertake", "undertakes", "certify", "certifies", "aware"}
STOP = FUNCTION_WORDS | CORE | EXCEPT | {WITHOUT} | set(MODAL.split("|")) | {
    "also", "which", "who", "whom", "whose", "what", "when", "where", "there", "here", "than", "then", "if",
    "only", "each", "every", "some", "more", "most", "been", "being", "them", "they", "he", "she", "his",
    "her", "him", "i", "me", "my", "these", "those", "into", "out", "up", "about", "after", "before", "over"}
BOILER = re.compile(r"\b(?:but\s+)?not\s+(?:be\s+)?limited\s+to\b|\bwithout\s+(?:limitation|limiting|prejudice)\b"
                    r"|\bwhether\s+or\s+not\b|\bno\s+later\s+than\b|\bnot\s+later\s+than\b|\bnot\s+only\b"
                    r"|\bnot\s+(?=(?:current|applicable|transferable|exclusive)\b)|\b(?P<w>\w+)\s+or\s+not\s+(?P=w)\b", re.I)
TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?|,")
ROMAN = re.compile(r"[ivx]+")
SENT_END = re.compile(r"(?<=[.!?])\s+")
ENUM_END = re.compile(r"(?:^|[\s(,])(?:[a-zA-Z]|[ivxIVX]{1,4}|\d{1,3}|e\.g|i\.e|etc|ltd|pvt|no|nos|rs|vs|viz|inc|co)\.$", re.I)
ENUM = r"\((?:[a-z]{1,2}|[ivx]{1,4}|\d{1,2})\)|(?:[a-z]|[ivx]{1,4}|\d{1,2})\.|\d{1,2}\.\d{1,2}"
ENUM_START = re.compile(rf"\s*(?:{ENUM})\s", re.I)
CUT = re.compile(                                              # where one claim ends and the next begins
    r"(?P<semi>[;:])"
    rf"|(?P<enum>(?<=[\s,;:])(?:{ENUM})(?=\s))"
    rf"|(?P<neg>,?\s+(?:and|or|but)\s+(?=(?:(?:{MODAL})\s+)?(?:not|never|no)\b))"
    rf"|(?P<aux>,?\s+(?:and|but)\s+(?=(?:also\s+)?(?:{MODAL})\b))"
    rf"|(?P<aux2>,\s+(?:and|but)\s+(?=(?:\S+\s+){{1,4}}?(?:{MODAL})\b))"
    r"|(?P<subj>,\s+(?:and|but|while|whereas|though|although)\s+(?=(?:\S+\s+){0,5}?(?:we|you|it|they|company)\b))"
    rf"|(?P<subj2>\s+and\s+(?=(?:we|you|it|they)\s+(?:{MODAL})\b))"
    r"|(?P<comma_not>,\s+(?=not\b))", re.I)
SCOPE_END = {",", "or", "and", "but", "which", "that", "who"}      # "without illegality, or it may be severed"
LEAD_END = {"that", "to", "which", "who", "following", "include", "includes", "including"}
NOT_PRACTICE = {"apply", "applies", "mandatory", "compulsory", "required", "obligatory", "obliged", "obligated"}
RISK = {"liabl", "liabil", "respon", "accoun"}
LIMIT = {"limit", "limited", "capped", "cap", "maximum", "max"}
MODALS = set(MODAL.split("|"))
CONTROL = {"require", "requires", "ask", "asks", "request", "requests", "allow", "allows", "permit", "permits",
           "enable", "enables", "authorise", "authorises", "authorize", "authorizes", "entitle", "entitles",
           "need", "needs", "expect", "expects", "advise", "advises", "encourage", "encourages"}
PASSIVE_ASK = {"asked", "required", "requested", "expected", "advised", "encouraged"}   # not "allowed", "entitled": a right
SUBJ_BEFORE = {None, ",", "the", "a", "an", "and", "that", "hereby"}
USER_SUBJ = {"you", "user", "users", "customer", "customers"}
COMPANY_SUBJ = {"we", "company", "agya", "it", "omsaa", "onemoney", "finsec", "saafe", "scoremeaa", "setu", "nadl", "pb"}
NEW_SUBJECT = {"the", "its", "your", "all", "any", "these", "this", "such", "their", "our"}
SWAP_ALIGN = 0.6         # a party swap is only called on a close match
MIN_ALIGN = 0.5          # share of a summary clause's content words that must reappear in the passage clause
TIE = 0.1                # passage clauses this close to the best match also count; all must disagree to flag
MIN_COVERAGE = 0.8       # the acceptance rule for references (build_dataset.MIN_COVERAGE)


def _mask(text: str) -> str:
    """Same-length copy for parsing: curly quotes straightened, "No. 2" (an address), "other than" and
    "can not" made single words, boilerplate negations blanked out."""
    t = text.replace("’", "'").replace("‘", "'")
    t = re.sub(r"\bNo(s?)\.(?=\s*\d)", lambda m: "num" + m.group(1), t)
    t = re.sub(r"\bother(\s+)than\b", lambda m: "otherthan" + " " * len(m.group(1)), t, flags=re.I)
    t = re.sub(r"\bcan(\s+)not\b", lambda m: "cannot" + " " * len(m.group(1)), t, flags=re.I)
    return BOILER.sub(lambda m: " " * len(m.group()), t)


def _stem(w: str) -> str:
    for suf in ("ies", "ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)] + ("y" if suf == "ies" else "")
            break
    return w.rstrip("e")[:6]


def _stems(toks: list[str]) -> set[str]:
    return {_stem(w) for w in toks
            if w != "," and w not in STOP and len(w) > 1 and not w.isdigit() and not ROMAN.fullmatch(w)}


def sentences(text: str) -> list[tuple[int, int]]:
    """Sentence spans; an enumerator or abbreviation ("f.", "Ltd.") does not end a sentence - except a list's
    closing "etc." before a capital letter ("... Bank Account Information etc. Once you register")."""
    spans, start = [], 0
    for m in SENT_END.finditer(text):
        before = text[start:m.start()].rstrip()
        if ENUM_END.search(before) and not (before.lower().endswith("etc.") and text[m.end():m.end() + 1].isupper()):
            continue
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    return [s for s in spans if text[s[0]:s[1]].strip()]


def _subject_of(toks: list[str], ignore: set) -> frozenset | None:
    """Who acts: a user or company word that opens the clause (or follows a comma, article, "and" or "that")
    before its first modal or negation - not "information users may share". None if unclear. In "we shall
    require you to upload" and "you authorise the Company to access" both parties act."""
    found, prev = set(), None
    for i, w in enumerate(toks[:10]):
        if i in ignore:                              # the "if you provide ..." part has its own actor
            continue
        if prev is None and (len(w) == 1 or w.isdigit() or ROMAN.fullmatch(w)):    # "(c) You ...", "3.2 We ..."
            continue
        if w in MODALS or w in CORE:
            break
        if prev in SUBJ_BEFORE and (w in USER_SUBJ or w in COMPANY_SUBJ):
            found.add("user" if w in USER_SUBJ else "company")
        prev = w
    if len(found) != 1:
        return None
    for i, w in enumerate(toks[1:-2], 1):            # "... shall require you to", "... hereby authorise the Company to"
        if w in CONTROL and i not in ignore and (toks[i - 1] in MODALS | USER_SUBJ | COMPANY_SUBJ
                                                 or toks[i - 1] in ("hereby", "also")):
            k = i + 2 if toks[i + 1] == "the" else i + 1
            if k + 1 < len(toks) and toks[k + 1] == "to" and (toks[k] in USER_SUBJ or toks[k] in COMPANY_SUBJ | {"us"}):
                found.add("user" if toks[k] in USER_SUBJ else "company")
    if any(w in PASSIVE_ASK and toks[i - 1] in ("are", "is", "be", "been") for i, w in enumerate(toks[1:10], 1)
           if i not in ignore):
        found |= {"user", "company"}                 # "you are asked for your name": the company asks
    return frozenset(found)


def _clause(text: str, masked: str, start: int, end: int, inherit: bool = False, lead: set | None = None) -> dict:
    toks = TOKEN.findall(masked[start:end].lower())
    ignore = set()
    for i, w in enumerate(toks):                     # "if ...," / "in the event ...": a condition, not the stance
        if w == "if" or (w == "event" and toks[i - 2:i] == ["in", "the"]) or (w == "case" and toks[i - 1:i] == ["in"]):
            j = i
            while j < len(toks) and toks[j] != "," and not (j > i + 1 and toks[j] in MAIN_MODAL):
                ignore.add(j)
                j += 1
    for i, w in enumerate(toks):                     # "... the computer that does not have a meaning"
        if w in CORE:
            for k in (i - 1, i - 2):
                if k >= 0 and (toks[k] in ("which", "who") or (toks[k] == "that" and (k == 0 or toks[k - 1] not in COMPLEMENT))):
                    ignore.add(i)
    lifts = [i for i, w in enumerate(toks) if (w in EXCEPT or w == WITHOUT) and i not in ignore]
    scopes = {}
    for i in lifts:                                  # what an exception/condition is about: its own words
        j = i + 1
        while j < len(toks) and toks[j] not in SCOPE_END and toks[j] not in EXCEPT and toks[j] != WITHOUT and j - i <= 6:
            j += 1
        scopes[i] = _stems(toks[i + 1:j]) - _stems(toks[:i] + toks[j:])
    return {"text": text[start:end].strip(), "start": start, "end": end, "toks": toks, "stems": _stems(toks),
            "subj": _subject_of(toks, ignore),
            "core": [i for i, w in enumerate(toks) if w in CORE and i not in ignore],
            "exc": [i for i in lifts if toks[i] in EXCEPT], "wo": [i for i in lifts if toks[i] == WITHOUT],
            "scopes": scopes, "inherit": inherit, "lead": lead or set()}


def _stance(c: dict, kept=lambda j: True) -> bool:
    """True = the clause denies. kept(j) says whether an exception/condition/"without" counts."""
    core = ([-1] if c["inherit"] else []) + c["core"]
    wo_cond = [j for j in c["wo"] if core and core[0] < j and kept(j)]       # "not ... without consent"
    wo_neg = [j for j in c["wo"] if not (core and core[0] < j) and kept(j)]  # "without warranty"
    return (bool(core) or bool(wo_neg)) and not (wo_cond or any(kept(j) for j in c["exc"]))


def clauses(text: str, context: str = "") -> list[dict]:
    """Clauses of a text. A list's items inherit a denying lead-in ("you shall not: a. ..., b. ...") up to the
    end of the sentence, and on into following sentences that open with an item marker of the same kind.
    `context` is the text just before (the previous passage): a lead-in there still governs the items here."""
    if context:
        off, full = len(context) + 1, context + " " + text
        out = []
        for c in clauses(full):
            if c["end"] <= off or not full[max(c["start"], off):c["end"]].strip():
                continue
            if c["start"] < off:     # a sentence running on from the context ("17.3", a heading): keep this part
                c = dict(_clause(full, _mask(full), off, c["end"], c["inherit"], c["lead"]), lead_subj=c["lead_subj"])
            out.append(dict(c, start=c["start"] - off, end=c["end"] - off))
        return out
    masked = _mask(text)
    out, inherit, lead, style, lead_subj = [], False, set(), None, None
    for s0, s1 in sentences(masked):
        prev_subj, coord = None, False
        m = ENUM_START.match(masked, s0)
        kind = None
        if m:
            e = m.group().strip(" ().").lower()
            kind = "roman" if ROMAN.fullmatch(e) else "digit" if e[:1].isdigit() else "letter"
        if not (inherit and kind and (style is None or kind == style)):
            inherit, lead, style = False, set(), None
        start = s0
        for m in list(CUT.finditer(masked, s0, s1)) + [None]:
            pos = m.start() if m else s1
            if masked[start:pos].strip():
                c = _clause(text, masked, start, pos, inherit, lead)
                if c["subj"] is None and coord and c["toks"] and (c["toks"][0] in MODALS or c["toks"][0] in CORE
                                                                  or c["toks"][0] == "also"):
                    c["subj"] = prev_subj                           # "... and shall not use the Platform"
                prev_subj = c["subj"] or prev_subj
                c["lead_subj"] = lead_subj if inherit else None
                out.append(c)
                if m and m.group("semi") == ":":
                    # a list lead-in ("you shall not:", "we make no warranty that:"), not a heading ("No access:")
                    is_lead = bool(MAIN_MODAL & set(c["toks"])) or (c["toks"] and c["toks"][-1] in LEAD_END)
                    if is_lead and _stance(dict(c, inherit=False)):
                        inherit, lead, style, lead_subj = True, c["stems"], None, c["subj"]
            if inherit and m and m.group("enum") and style is None:
                e = m.group("enum").strip("().").lower()
                style = "roman" if ROMAN.fullmatch(e) else "digit" if e[:1].isdigit() else "letter"
            if m is None:
                break
            coord = bool(m.group("neg") or m.group("aux") or m.group("aux2") or m.group("comma_not"))
            start = m.start() if m.group("enum") else m.end()
    return out


def _split_summary(c: dict, summary: str, masked: str, verbs: set[str]) -> list[dict]:
    """Model summaries chain claims with commas ("does not use X, shares Y, and collects Z"): cut before a
    finite verb. A list of base-form verbs under one "must not" stays together."""
    cuts = []
    for m in re.finditer(r",\s+(and\s+)?([A-Za-z]+)", masked[c["start"]:c["end"]]):
        w = m.group(2).lower()
        verb = w.endswith("s") and not w.endswith("ss") and len(w) >= 4 and w not in STOP and (m.group(1) or _stem(w) in verbs)
        new_subject = m.group(1) and w in NEW_SUBJECT                  # ", and the remaining provisions remain"
        if verb or new_subject:
            cuts.append((c["start"] + m.start(), c["start"] + m.start(2)))
    if not cuts:
        return [c]
    bounds = [(c["start"], None)] + cuts
    ends = [a for a, _ in cuts] + [c["end"]]
    parts = [_clause(summary, masked, b if b is not None else a, e, c["inherit"], c["lead"])
             for (a, b), e in zip(bounds, ends)]
    for x in parts:
        x["subj"] = x["subj"] or c["subj"]
    return parts


def _stances(sc: dict, c: dict) -> tuple[bool, bool]:
    """(summary clause denies?, passage clause denies?), each exception/condition counted only where it applies."""
    kept_s = lambda j: bool(sc["scopes"][j] & (c["stems"] | c["lead"]))     # not borrowed from elsewhere
    s_core = ([-1] if sc["inherit"] else []) + sc["core"]
    p_core = ([-1] if c["inherit"] else []) + c["core"]
    s_wo = any(kept_s(j) for j in sc["wo"])
    s_lift = any(kept_s(j) for j in sc["exc"]) or any(kept_s(j) and s_core and s_core[0] < j for j in sc["wo"])
    s_scopes = [sc["scopes"][j] for j in sc["exc"] + sc["wo"] if kept_s(j)]

    def kept_p(j: int) -> bool:                  # does the summary keep this exception/condition?
        lifting = c["toks"][j] != WITHOUT or (p_core and p_core[0] < j)
        if any(c["scopes"][j] & s for s in s_scopes):                     # it names the same condition
            return True
        if (s_lift if lifting else s_wo):                                  # it says the same kind of thing
            return True
        if "only" in sc["toks"] and lifting:                               # "not ... without X" -> "only with X"
            return True
        scope = c["scopes"][j]
        return bool(scope) and len(scope & sc["stems"]) >= min(2, len(scope))
    return _stance(sc, kept_s), _stance(c, kept_p)


def _opposed(sc: dict, c: dict, s_den: bool, p_den: bool) -> bool:
    if s_den == p_den:
        return False
    p_subj = c["subj"] or c.get("lead_subj")
    # two sides of one allocation: "we are not liable for X" ~ "you are responsible for X"
    if sc["subj"] and p_subj and not sc["subj"] & p_subj and RISK & sc["stems"] and RISK & (c["stems"] | c["lead"]):
        return False
    # "liability shall not exceed INR 10,000" ~ "liability is limited to INR 10,000"
    if p_den and "exceed" in c["toks"] and LIMIT & set(sc["toks"]):
        return False
    return True


def compare(passage: str, summary: str, context: str = "") -> dict:
    """Each summary clause against the passage clause(s) it restates (most shared content words):
    reversed - the opposite stance ("shares without consent" for "will not share without consent");
    swapped  - the same stance, the other party acting ("you may assign" for "we may assign")."""
    out = {"reversed": [], "swapped": []}
    src = clauses(passage, context)
    if not src:
        return out
    ptoks = TOKEN.findall(_mask(passage).lower())
    verbs = {_stem(ptoks[i + 1]) for i, w in enumerate(ptoks[:-1]) if w in CORE or w in MAIN_MODAL or w == "to"}
    smasked = _mask(summary)
    for big in clauses(summary):
        for sc in _split_summary(big, summary, smasked, verbs):
            scored = sorted(((len(sc["stems"] & c["stems"]) / len(sc["stems"]), k) for k, c in enumerate(src)
                             if len(sc["stems"] & c["stems"]) >= 2), reverse=True)    # one shared word is no match
            if not scored or scored[0][0] < MIN_ALIGN:
                continue
            best = scored[0][0]
            cands = [src[k] for v, k in scored if v >= best - TIE]
            st = [_stances(sc, c) for c in cands]
            if all(_opposed(sc, c, *s) for c, s in zip(cands, st)):
                out["reversed"].append((sc["text"], cands[0]["text"]))
            elif best >= SWAP_ALIGN and sc["subj"] and all(
                    s[0] == s[1] and c["subj"] and not c["subj"] & sc["subj"] for c, s in zip(cands, st)):
                out["swapped"].append((sc["text"], cands[0]["text"]))
    return out


def reversals(passage: str, summary: str, context: str = "") -> list[tuple[str, str]]:
    return compare(passage, summary, context)["reversed"]


def invented(passage: str, summary: str) -> list[str]:
    """Numbers, names and acronyms in the summary that the passage never mentions."""
    p = _mask(passage).lower()
    words = set(re.findall(r"[a-z0-9]+", p))
    pref = {w[:5] for w in words if len(w) >= 5}
    flat = re.sub(r"[^a-z0-9]", "", p)               # extraction can glue words: "outsidetheterritoryofIndia"
    nums = {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", passage)}
    caps = [w for w in re.findall(r"[A-Za-z]+", passage) if w.lower() not in ("of", "and", "the", "for")]
    initials = {"".join(w[0] for w in caps[i:i + n]).lower() for i in range(len(caps)) for n in range(2, 6)
                if all(w[0].isupper() for w in caps[i:i + n])}  # "Information Technology" -> "it"
    known = lambda w: w in words or w in initials or (len(w) >= 5 and (w[:5] in pref or w in flat))
    out = [n for n in re.findall(r"\d[\d,]*(?:\.\d+)?", summary) if n.replace(",", "").rstrip(".") not in nums]
    for s0, s1 in sentences(summary):
        for j, t in enumerate(re.findall(r"[A-Za-z][\w&'-]*", summary[s0:s1])):
            if (j > 0 and t[0].isupper()) or (len(t) > 1 and t.isupper()):
                parts = [x for x in re.split(r"[-'&]", t.lower()) if len(x) > 1]
                if parts and not all(known(x) for x in parts):
                    out.append(t)
    return sorted(set(out))


def fact_denied(passage: str, start: int | None, text: str, context: str = "") -> bool:
    """The fact's clause says the practice is NOT done (a legal carve-out keeps the
    denial; a fact named inside the exception - 'will not share, except for fraud checks' - is affirmed).
    Not a denial of the practice: a negation in brackets that do not hold the fact ("Aadhaar (full number
    not stored), Voter ID"), or one about scope or obligation ("does not apply to", "is not mandatory")."""
    if start is None:
        start = _mask(passage).lower().find(_mask(text).lower())
        if start < 0:
            return False
    passage = re.sub(r"\([^()]*\)", lambda m: m.group() if m.start() <= start < m.end() or not
                     CORE & set(TOKEN.findall(m.group().lower())) else " " * len(m.group()), passage)
    masked = _mask(passage)
    for c in clauses(passage, context):
        if c["start"] <= start < c["end"]:
            core = [j for j in ([-1] if c["inherit"] else []) + c["core"]
                    if j < 0 or not NOT_PRACTICE & set(c["toks"][j + 1:j + 3])]
            if not core:
                return False
            k = len(TOKEN.findall(masked[c["start"]:start].lower()))
            lifts = [j for j in c["exc"] + c["wo"] if j > core[0]]
            return not (lifts and k > min(lifts))
    return False


def gate(passage: str, summary: str, facts: list[tuple[str, str, int | None]], context: str = "") -> dict:
    """context: the previous passage of the same document (a list's lead-in may sit there)."""
    cmp, inv = compare(passage, summary, context), invented(passage, summary)
    rev, swap = cmp["reversed"], cmp["swapped"]
    scw = content_words(summary)
    checkable = [f for f in facts if content_words(f[0])]
    missing = [f for f in checkable if overlap_coeff(content_words(f[0]), scw) < 0.6]
    cov = 1 - len(missing) / len(checkable) if checkable else 1.0
    verdict = "reject" if rev or swap or inv else ("add" if cov < MIN_COVERAGE else "show")
    return {"verdict": verdict, "coverage": round(cov, 3), "reversed": rev, "swapped": swap, "invented": inv,
            "missing": [{"text": t, "label": lab, "denied": fact_denied(passage, s, t, context)} for t, lab, s in missing],
            "facts": [{"text": t, "label": lab, "denied": fact_denied(passage, s, t, context)} for t, lab, s in facts]}


def _facts_of(row: dict) -> list[tuple[str, str, None]]:
    keys = {"data_types": "DATA_TYPE", "purposes": "PURPOSE", "third_parties": "THIRD_PARTY"}
    return [(f, keys[k], None) for k, v in row["cd"].items() for f in v]


def cmd_score(args) -> None:
    rows = {r["id"]: r for f in args.data for r in map(json.loads, filter(str.strip, f.read_text(encoding="utf-8").splitlines()))}
    preds = [json.loads(l) for l in args.preds.read_text(encoding="utf-8").splitlines() if l.strip()]
    verdicts = Counter()
    for p in preds:
        r = rows[p["id"]]
        doc, n = p["id"].rsplit("__c", 1)                       # the previous passage, if loaded, is the context
        context = rows.get(f"{doc}__c{int(n) - 1:02d}", {}).get("source", "")
        g = gate(r["source"], p["summary"], _facts_of(r), context)
        verdicts[g["verdict"]] += 1
        if g["reversed"] or g["swapped"] or g["invented"]:
            print(f"{p['id']}: {g['verdict']} | invented {g['invented']}")
            for kind in ("reversed", "swapped"):
                for s, c in g[kind]:
                    print(f"    {kind} summary : {s}\n    passage : {c[:220]}")
    print(f"{len(preds)} summaries: " + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())))


def _selfcheck() -> None:
    R = lambda p, s: bool(reversals(p, s))
    share = "It shall not share any information that it acquires from you, without your explicit consent."
    assert R(share, "Agya shares your information without your explicit consent.")
    assert not R(share, "Agya shares your information only with your explicit consent.")
    assert not R(share, "Agya will not share your information without your explicit consent.")
    notice = "Agya reserves the right to change these Terms at any time without any prior written notice to you."
    assert not R(notice, "Agya may change these terms at any time.")                  # a dropped condition
    assert not R(notice, "Agya may change these terms at any time without notice.")
    liable = "Setu AA shall not be liable for any loss that you may suffer if any information provided is incorrect."
    assert R(liable, "It is liable for loss caused by incorrect information.")
    assert not R(liable, "It is not liable for loss caused by incorrect information.")
    waiver = "Failure to enforce a provision in some instances does not constitute a waiver of the Company's right."
    assert R(waiver, "Failure to enforce a provision is a waiver of the company's right.")
    assert not R(waiver, "Failure to enforce a provision does not waive the company's right.")
    lst = "You shall not: a. use any robot to copy the Application, b. transmit viruses to the Platform."
    assert not R(lst, "You must not use robots to copy the application.")              # inherited lead-in
    assert R(lst, "It transmits viruses to the platform.")
    minor = "If you are under 18 years, you shall not register as a user and shall not use the Platform."
    assert not R(minor, "If you are under 18 you must not register as a user.")        # two negations, one stance
    assert R(minor, "Under 18, you must register as a user.")
    boiler = "We disclaim all warranties, including but not limited to the warranties of accuracy and reliability."
    assert not R(boiler, "The company disclaims all warranties, including accuracy and reliability.")
    cookies = "If You do not want information collected through cookies, you may change the settings in your browser."
    assert not R(cookies, "You may change the settings in your browser.")             # negation inside "if"
    rel = "Cookies work by assigning a unique number to the computer that does not have a meaning beyond the site."
    assert not R(rel, "Cookies work by assigning a unique number to your computer.")  # negation in a relative clause
    save = "Save and except with our prior written consent, you may not insert a hyperlink to the Platform."
    assert not R(save, "You may not insert a hyperlink without the company's written consent.")
    waive2 = ("Failure to enforce a provision does not constitute a waiver of the Company's right. "
              "The remaining provisions shall remain in full force and effect.")
    assert R(waive2, "Failure to enforce a provision is a waiver of the company's right, and the remaining provisions remain in full force.")
    sev2 = "If a provision is unenforceable, the Company may amend it without illegality, or it may be severed unless the Company decides otherwise."
    assert not R(sev2, "If a provision is unenforceable, the company may amend it without illegality.")
    both = "We shall not be liable for any loss arising from the use of the Services."
    assert not R(both, "You are solely responsible for any loss arising from the use of the services.")
    cap = "Our liability for direct damages shall not exceed INR 10,000."
    assert not R(cap, "Its liability for direct damages is limited to INR 10,000.")
    prev = "We make no warranty that:"
    items = "(a) The Services will meet your requirements; (b) errors in the technology will be corrected."
    assert not R(items, "The services will meet your requirements.")                    # no context: cannot tell
    assert reversals(items, "The services will meet your requirements.", context=prev)   # the lead-in is in context
    run_on = "We will not sell your data. We may share it with partners."
    for ctx in ("These terms apply. 17.3", "These terms apply. Usage of information"):  # not swallowed by context
        assert [c["text"] for c in clauses(run_on, ctx)] == [c["text"] for c in clauses(run_on)]
    assert reversals("transmit viruses to the Platform.", "It transmits viruses to the platform.",
                     context="You shall not: (a) copy the Platform; (b)")                # an item split across passages
    kyc = "In this regard, we shall require you to upload documents to ascertain your eligibility."
    assert not compare(kyc, "You must upload documents to ascertain your eligibility.")["swapped"]
    assert not compare(kyc, "The company may require documents to ascertain your eligibility.")["swapped"]
    views = "4.1 The Services provided by Agya allows you to retrieve and view your financial information."
    assert not compare(views, "Agya provides services to retrieve and view your financial information.")["swapped"]
    assign = "You shall not assign your rights without our prior written consent. We may assign our rights to our affiliates."
    assert compare(assign, "You may assign your rights to affiliates.")["swapped"]
    assert not compare(assign, "The company may assign its rights to affiliates.")["swapped"]
    susp = "If you provide any information that is untrue, Company has the right to suspend your account."
    assert not compare(susp, "Company may suspend your account if your information is untrue.")["swapped"]
    cover = "This policy explains practices of the Company relating to collection and disclosure of information."
    assert not compare(cover, "The policy covers information users may share with the company and disclosure.")["swapped"]
    head = "2.7 No access: We clarify that at no time will Agya have access to your SPI. Your SPI is encrypted by FIPs."
    assert not R(head, "Your SPI is encrypted by FIPs.")                                 # a heading is no lead-in
    sev = "If any provision is unenforceable, the Company may amend it without illegality, or it may be severed."
    assert not R(sev, "If a provision is unenforceable, the company may amend it or sever it.")
    warr = "Without limiting the foregoing, we make no warranty that: (i) the Services will meet your requirements."
    assert not R(warr, "The services are provided without warranty that they will meet your requirements.")
    chain = ("a. It shall not use the services of a third-party service provider. b. It shall not share any "
             "information that it acquires from you, without your explicit consent. c. It shall share your "
             "financial information only with third parties as explicitly specified and consented by you.")
    doc = "c. It shall not retrieve or share any of your information, without your explicit consent as documented in a valid consent artefact."
    assert R(doc, "Agya shares your information without your explicit consent.")
    assert R(chain, "Agya does not use a third-party service provider, shares your information without "
                    "your explicit consent, and shares financial information only with third parties you specified.")
    verbs = "You shall not: (i) copy or modify the Platform, (ii) provide time-sharing services to third parties."
    assert not R(verbs, "You must not copy or modify the platform, provide time-sharing services to third parties.")
    assert invented("Complaints are resolved within one month.", "Complaints are resolved within 30 days by RBI.") == ["30", "RBI"]
    assert invented("The Reserve Bank of India licenses it.", "It is licensed by the Indian Reserve Bank.") == []
    assert invented("Do not transfer it outsidetheterritoryofIndia.", "It stays in India, not Bangkok.") == ["Bangkok"]
    assert invented("Under the Information Technology Rules and the Reserve Bank of India.", "Under the IT rules and RBI.") == []
    assert invented("Under the Information Technology Rules.", "Under the IT rules and SEBI.") == ["SEBI"]
    minor2 = "If you are under 18, you shall not register. The Company may terminate your membership if it is discovered."
    assert not R(minor2, "If you are under 18 you must not register, though the company may terminate your membership.")
    assert not R("The Platform may suffer delays or unauthorised access to records.",
                 "The services end, and you no longer have access to them.")             # one shared word is no match
    carve = "We shall not access your contact lists, except as permitted under law."
    assert fact_denied(carve, None, "contact lists")
    exc = "We will not share your data, except as required for fraud verification."
    assert fact_denied(exc, None, "data") and not fact_denied(exc, None, "fraud verification")
    assert not fact_denied("We collect your bank statements.", None, "bank statements")
    addr = "Agya, having its office at No. 2/1, Infantry Road, collects your email address."
    assert not fact_denied(addr, None, "email address")                                 # "No. 2/1" is an address
    ids = "We collect Aadhaar (full number not stored), Voter ID or Passport."
    assert not fact_denied(ids, None, "Voter ID") and fact_denied(ids, None, "full number")
    assert not fact_denied("This Policy does not apply to information collected by merchants.", None, "merchants")
    assert not fact_denied("Submission of your Aadhaar number is not mandatory for KYC.", None, "Aadhaar number")
    etc = "We ask for your name, mobile number etc. Once you sign in you are not anonymous to us."
    assert len(sentences(etc)) == 2 and not fact_denied(etc, None, "mobile number")   # "etc." ended the list
    assert len(sentences("We collect PAN, Aadhaar etc. and we use them.")) == 1         # mid-sentence "etc." still joins
    asked = "When you register with PB Financial, you are asked for your name and mobile number."
    assert not compare(asked, "PB Financial asks for your name and mobile number.")["swapped"]   # passive: no swap
    right = "You are allowed to download your consent records at any time."
    assert compare(right, "The company may download your consent records at any time.")["swapped"]  # a right still swaps
    g = gate(share, "Agya shares your information without your explicit consent.", [("information", "DATA_TYPE", None)])
    assert g["verdict"] == "reject" and g["reversed"]
    names = "We collect information including but not limited to your name and email address."
    g = gate(names, "The company collects your name.", [("name", "DATA_TYPE", None), ("email address", "DATA_TYPE", None)])
    assert g["verdict"] == "add" and g["missing"][0]["text"] == "email address"
    print("selfcheck ok")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selfcheck", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("score", help="gate every summary in a predictions file")
    s.add_argument("--data", type=Path, nargs="+", required=True,
                   help="jsonl file(s) with id, source, cd; add chunks_train.jsonl to give each passage its context")
    s.add_argument("--preds", type=Path, required=True, help="jsonl with id, summary (dev_predictions.jsonl)")
    args = ap.parse_args()
    if args.selfcheck:
        return _selfcheck()
    if args.cmd == "score":
        return cmd_score(args)
    ap.print_help()


if __name__ == "__main__":
    main()
