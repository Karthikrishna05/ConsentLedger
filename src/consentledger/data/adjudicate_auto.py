"""Automatic adjudication with a human sample check (D50).

Three steps, each reproducible from the two exports plus one decisions file:

  items   - normalise each export on its own (written rules only: delete / trim / relabel / own company),
            accept what both annotators marked identically, and list everything else as numbered ITEMS,
            each shown inside its sentence, for a ruling.
  apply   - read the rulings (results/annotation/adjudication/decisions.tsv: item id, decision code) and
            write gold.json, plus a random SAMPLE sheet per annotator to verify the rulings.
  score   - read the filled-in sample sheets and report the acceptance rate.

Item kinds:
  O  one-sided       only one annotator marked it              -> A (accept) / R<code> (reject) / M:<text>[:D|P|T]
  B  boundary        both marked overlapping spans, same label -> a / b (whose span) / M:<text> / R<code>
  L  label conflict  overlapping spans, different labels       -> a / b (whose span AND label) / M:<text>:<L> / R<code>
  M:<text> re-draws the highlight over exactly <text> (found nearest the item), optionally with a new label.
  G  agreed, doubted both marked it but a ruling doubts it     -> A / R<code>
  X  repeat          a phrase accepted elsewhere in the doc     -> A / R<code>     (second pass)
  "drop <L> <doc> <start> <end> <code> <text>" removes ONE span both annotators drew identically but a rule
     excludes (D59: an agreed span is not automatically a correct one).
  N  new             nobody marked it; a rule ratified after annotation (D55) needs it - the rest of a list
                     whose other members are accepted. Written as "new <L> <doc> <start> <end> <text>".

Reject codes name the rule: R8 umbrella/generic, R8b AA role or regulator, R9 purpose not an activity /
too long, R9b umbrella data, R10 no data-use frame or not on the list, R16 no data flow to or from them, R17 own
company, R19 named after data / law name, R23 telemetry, D47 data word with no data practice, CO the
company's own data, FR a fragment or not an entity, DUP duplicate of a better span.
"""
from __future__ import annotations

import argparse
import codecs
import contextlib
import csv
import io
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from consentledger.data.adjudicate import _bounds, _tp_reason
from consentledger.data.annotation_audit import find_occurrences, load_corpus, norm
from consentledger.data.fixlist import fixes_for, owner_regex
from consentledger.data.kappa import load_ls_export

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT = PROJECT_ROOT / "results" / "annotation" / "adjudication"
LENDER = re.compile(r"^(?:lenders?|lending partners?|partner institutions?|regulated entit(?:y|ies))$")
CREDENTIAL = re.compile(r"password|username|user ?names?|user ids?|login id|credential|\botps?\b|\bpins?\b")
LAB = {"D": "DATA_TYPE", "P": "PURPOSE", "T": "THIRD_PARTY"}
REASON = {
    "R8": "a vague or umbrella word, not a specific entity (Rule 8)",
    "R8b": "an AA-framework role, a named Account Aggregator or a pipeline regulator (Rule 8b)",
    "R9": "not the name of an activity - a fragment, an object or a legal basis (Rule 9)",
    "R9b": "umbrella 'X data / X information' whose modifier does not name content (Rule 9b)",
    "R10": "no data-use frame, or not one of the 12 purpose categories (Rule 10)",
    "R16": "the sentence describes no exchange of the user's data with them, to or from (Rule 16; D49, D55)",
    "R17": "the policy's own company or its own staff (Rule 17)",
    "R19": "only part of another name - a process, a law, a company name (Rule 19)",
    "R23": "device/usage telemetry, not data the user provides (Rule 23a)",
    "D47": "a data word in a sentence with no data practice - a duty, an attack, an eligibility condition (D47)",
    "CO": "the company's (or another party's) own details, not the user's data",
    "FR": "not an entity in this sentence - a different sense of the word, or a fragment",
    "DUP": "covered by a better highlight of the same phrase (Rules 14, 15)",
}


def normalise(X: dict) -> dict:
    """One export, cleaned with its own annotator's spans only - no lexicon, no 'theirs'."""
    labs = defaultdict(Counter)
    for v in X.values():
        for s, e, lab in v["spans"]:
            labs[norm(v["text"][s:e])][lab] += 1
    out = {}
    for d, v in X.items():
        t = v["text"]
        o = fixes_for(t, v["spans"], [], {}, set(), set(), owner_re=owner_regex(d), own_labels=labs)
        spans = set(v["spans"])
        for sp, _ in o["DELETE"] + o["OWN_COMPANY"]:
            spans.discard(sp)
        for old, new, _ in o["TRIM"]:
            spans.discard(old)
            spans.add(new)
        for sp, maj, _ in o["RELABEL"]:
            if sp in spans:
                spans.discard(sp)
                spans.add((sp[0], sp[1], maj))
        keep = []                                           # Rule 15: longest wins
        for sp in sorted(spans, key=lambda x: (-(x[1] - x[0]), x)):
            if not any(k[0] < sp[1] and sp[0] < k[1] for k in keep):
                keep.append(sp)
        out[d] = sorted(keep)
    return out


def build_items(corpus, A, B):
    """-> (agreed {doc: [spans]}, items [dict])."""
    NA, NB = normalise(A), normalise(B)
    agreed, items = {}, []
    for d in sorted(corpus):
        t = corpus[d]
        sa, sb = set(NA[d]), set(NB[d])
        both = sa & sb
        agreed[d] = []
        for sp in sorted(both):
            p = norm(t[sp[0]:sp[1]])
            doubt = (sp[2] == "THIRD_PARTY" and (LENDER.match(p) or _tp_reason(t, sp[0], sp[1]))) or \
                    (sp[2] == "DATA_TYPE" and CREDENTIAL.search(p))
            if doubt:
                items.append({"doc": d, "kind": "G", "a": sp, "b": sp})
            else:
                agreed[d].append(sp)
        rest_a, rest_b = sorted(sa - both), sorted(sb - both)
        used_b = set()
        for x in rest_a:
            y = next((z for z in rest_b if z not in used_b and z[0] < x[1] and x[0] < z[1]), None)
            if y is None:
                items.append({"doc": d, "kind": "O", "a": x, "b": None})
            else:
                used_b.add(y)
                items.append({"doc": d, "kind": "L" if x[2] != y[2] else "B", "a": x, "b": y})
        items += [{"doc": d, "kind": "O", "a": None, "b": y} for y in rest_b if y not in used_b]
    items.sort(key=lambda it: (it["doc"], (it["a"] or it["b"])[0], it["kind"]))
    for i, it in enumerate(items, 1):
        it["id"] = i
    return agreed, items


def _q(t, sp):
    return " ".join(t[sp[0]:sp[1]].split())


def render(corpus, items, start_id=1) -> str:
    """Items grouped by sentence, so each sentence is read once."""
    out, cur_doc, cur_sent = [], None, None
    for it in items:
        t = corpus[it["doc"]]
        sp = it["a"] or it["b"]
        a, b = _bounds(t, sp[0], sp[1])
        if it["doc"] != cur_doc:
            out.append(f"\n##### {it['doc']}")
            cur_doc, cur_sent = it["doc"], None
        if (a, b) != cur_sent:
            cur_sent = (a, b)
            lo, hi = max(a, sp[0] - 260), min(b, sp[1] + 200)
            group = [x for x in items if x["doc"] == it["doc"] and a <= (x["a"] or x["b"])[0] < b]
            lo = max(a, min((x["a"] or x["b"])[0] for x in group) - 200)
            hi = min(b, max((x["a"] or x["b"])[1] for x in group) + 160)
            out.append(f"S: {'…' if lo > a else ''}{' '.join(t[lo:hi].split())}{'…' if hi < b else ''}")
        k = it["kind"]
        if k == "O":
            who = "P1" if it["a"] else "P4"
            out.append(f"  #{it['id']} O {who} {sp[2][0]} «{_q(t, sp)}»")
        elif k == "B":
            out.append(f"  #{it['id']} B {sp[2][0]} P1«{_q(t, it['a'])}» P4«{_q(t, it['b'])}»")
        elif k == "L":
            out.append(f"  #{it['id']} L P1 {it['a'][2][0]}«{_q(t, it['a'])}» P4 {it['b'][2][0]}«{_q(t, it['b'])}»")
        else:
            out.append(f"  #{it['id']} {k} {sp[2][0]} «{_q(t, sp)}»")
    return "\n".join(out)


def load_all(args):
    corpus = load_corpus(args.corpus)
    with contextlib.redirect_stdout(io.StringIO()):
        A, B = load_ls_export(args.a), load_ls_export(args.b)
    return corpus, A, B


def read_decisions(path: Path) -> dict[int, str]:
    dec = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("//", "agreed ", "new ", "drop ")):
            i, code = line.split(None, 1)
            i = int(i) if i.isdigit() else i                  # second-pass items are keyed x|doc|start|end
            assert i not in dec, f"item {i} ruled twice"
            dec[i] = code.strip()
    return dec


def resolve(it, code, text):
    """One ruling -> the gold span it yields, or None."""
    a, b = it["a"], it["b"]
    base = a or b
    if code.startswith(("R", "D47", "CO", "FR", "DUP")):       # every reject code
        return None
    if code.startswith("M:"):                                  # M:<text>[:D|P|T] - re-draw near the item
        _, phrase, *lab = code.split(":")
        lo = max(0, base[0] - 400)
        window = text[lo:base[1] + 400]
        words = [re.escape(w) for w in phrase.split()]         # the documents wrap lines and glue words
        hits = [m for gap in (r"\s+", r"\s*") for m in re.finditer(gap.join(words), window)]
        assert hits, (it["id"], code)
        m = min(hits, key=lambda h: abs(h.start() + lo - base[0]))
        return (m.start() + lo, m.end() + lo, LAB[lab[0]] if lab else base[2])
    if code in ("a", "b"):
        return {"a": a, "b": b}[code]
    assert code == "A" and it["kind"] in "OGXN", (it["id"], code)
    return base


def cmd_items(args):
    corpus, A, B = load_all(args)
    agreed, items = build_items(corpus, A, B)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "items.txt").write_text(render(corpus, items), encoding="utf-8")
    c = Counter(it["kind"] for it in items)
    print(f"agreed and accepted: {sum(len(v) for v in agreed.values())} | items to rule on: {len(items)} {dict(c)}")
    print(f"wrote {args.out / 'items.txt'}")


def cmd_apply(args):
    corpus, A, B = load_all(args)
    agreed, items = build_items(corpus, A, B)
    dec = read_decisions(args.decisions)
    missing = [it["id"] for it in items if it["id"] not in dec]
    if missing:
        raise SystemExit(f"{len(missing)} items have no ruling, e.g. {missing[:10]}")
    gold = {d: set(v) for d, v in agreed.items()}
    stats = Counter()
    # Both annotators marking a span does not make it rule-compliant. "agreed <L> <phrase> => <new>|-" re-draws
    # or drops every agreed span with that phrase and label (Rule 23a telemetry; one boundary made consistent).
    for line in args.decisions.read_text(encoding="utf-8").splitlines():
        if not line.startswith("agreed "):
            continue
        lab, rest = line[7:].split(None, 1)
        phrase, new = (x.strip() for x in rest.split("=>"))
        for d in gold:
            for sp in [sp for sp in gold[d] if sp[2] == LAB[lab] and norm(corpus[d][sp[0]:sp[1]]) == phrase]:
                gold[d].discard(sp)
                stats[("agreed", "dropped" if new == "-" else "redrawn")] += 1
                if new != "-":
                    gold[d].add(resolve({"id": line, "a": sp, "b": None, "kind": "O"}, f"M:{new}", corpus[d]))
    dropped = defaultdict(list)
    for line in args.decisions.read_text(encoding="utf-8").splitlines():
        if line.startswith("drop "):                          # one agreed span, one position
            lab, d, s, e, _code, phrase = line[5:].split(None, 5)
            sp = (int(s), int(e), LAB[lab])
            assert sp in gold[d] and norm(corpus[d][sp[0]:sp[1]]) == norm(phrase), line
            gold[d].discard(sp)
            dropped[d].append(sp)
            stats[("agreed", "dropped")] += 1
        if line.startswith("new "):                           # "new <L> <doc> <start> <end> <text>" (kind N)
            lab, d, s, e, phrase = line[4:].split(None, 4)
            sp = (int(s), int(e), LAB[lab])
            assert norm(corpus[d][sp[0]:sp[1]]) == norm(phrase), line
            items.append({"doc": d, "kind": "N", "a": sp, "b": None, "id": line})
            dec[line] = "A"
    for it in items:
        sp = resolve(it, dec[it["id"]], corpus[it["doc"]])
        stats[(it["kind"], "accept" if sp else "reject")] += 1
        if sp:
            gold[it["doc"]].add(sp)

    # second pass (Rule 7): accepted phrases at positions nobody marked become X items with their own rulings
    xitems = []
    for d in sorted(corpus):
        t = corpus[d]
        phrases = {}
        for s, e, lab in gold[d]:
            p = norm(t[s:e])
            if len(p) >= 4:
                phrases.setdefault(p, lab)
        # a position either annotator marked already has a ruling (accepted or rejected) - never re-propose it
        ruled = [sp for it in items if it["doc"] == d for sp in (it["a"], it["b"]) if sp]
        taken = sorted(gold[d]) + ruled + dropped[d]
        for i, j, term in find_occurrences(t, sorted(phrases, key=lambda p: (-len(p), p))):
            if not any(s < j and i < e for s, e, _ in taken) and t[j:j + 2].lstrip()[:1] != ":":
                taken.append((i, j, phrases[term]))
                xitems.append({"doc": d, "kind": "X", "a": (i, j, phrases[term]), "b": None})
    xitems.sort(key=lambda it: (it["doc"], it["a"][0]))
    for it in xitems:                                         # stable key: a later ruling change cannot shift it
        it["id"] = f"x|{it['doc']}|{it['a'][0]}|{it['a'][1]}"
    todo = [it for it in xitems if it["id"] not in dec]
    if todo:
        (args.out / "items_repeats.txt").write_text(render(corpus, todo), encoding="utf-8")
        print(f"second pass: {len(todo)} repeat candidates need a ruling -> {args.out / 'items_repeats.txt'}")
        return
    for it in xitems:
        sp = resolve(it, dec[it["id"]], corpus[it["doc"]])
        stats[("X", "accept" if sp else "reject")] += 1
        if sp:
            gold[it["doc"]].add(sp)

    final = {}
    for d in sorted(gold):                                    # Rule 15 once more over the merged set
        keep = []
        for sp in sorted(gold[d], key=lambda x: (-(x[1] - x[0]), x)):
            if not any(k[0] < sp[1] and sp[0] < k[1] for k in keep):
                keep.append(sp)
        final[d] = sorted(keep)
    gold_path = PROJECT_ROOT / "data" / "aa" / "annotated" / "gold.json"
    # `negated` (D66): the passage says this practice is NOT done ("we shall not access your credentials"). The
    # label and the span are unchanged - Rule 18 marks a denied practice like an affirmed one - so the BIO files
    # and every score are unaffected; the flag is for the summariser and the ledger. Positions come from
    # negated.tsv (doc, start, end, label), written by the `negation` command from the checked sheet.
    neg_path = args.out / "negated.tsv"
    neg = {tuple(ln.split("\t")) for ln in neg_path.read_text(encoding="utf-8").splitlines() if ln.strip()} if neg_path.exists() else set()
    spans_all = {(d, str(s), str(e), lab[0]) for d in final for s, e, lab in final[d]}
    assert neg <= spans_all, f"negated.tsv names spans that are not in the gold: {sorted(neg - spans_all)[:5]}"
    gold_path.write_text(json.dumps(
        [{"doc_id": d, "text": corpus[d], "spans": [{"start": s, "end": e, "label": lab, "text": corpus[d][s:e],
                                                     **({"negated": True} if (d, str(s), str(e), lab[0]) in neg else {})}
                                                    for s, e, lab in final[d]]} for d in final],
        ensure_ascii=False, indent=1), encoding="utf-8")

    # sample sheets: the same random rulings for both checkers, stratified by kind
    rng = random.Random(args.seed)
    pool = items + xitems
    by_kind = defaultdict(list)
    for it in pool:
        by_kind[it["kind"]].append(it)
    sample = []
    for k, lst in sorted(by_kind.items()) if args.sample else ():
        n = max(4, round(args.sample * len(lst) / len(pool)))
        sample += rng.sample(lst, min(n, len(lst)))
    sample.sort(key=lambda it: (it["doc"], (it["a"] or it["b"])[0]))
    for n, it in enumerate(sample, 1):
        it["row"] = n
    for name in ("P1", "P4") if args.sample else ():           # --sample 0: rebuild the gold, leave the sheets
        with (args.out / f"sample_check_{name}.csv").open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["row", "doc", "what was highlighted (by one or both annotators)", "RULING", "why",
                        "sentence", "AGREE with the ruling? (y/n)", "if n: what should it be"])
            for it in sample:
                t = corpus[it["doc"]]
                sp = it["a"] or it["b"]
                code = dec[it["id"]]
                g = resolve(it, code, t)
                a, b = _bounds(t, sp[0], sp[1])
                lo, hi = max(a, sp[0] - 220), min(b, sp[1] + 180)
                seen = [f"{_q(t, x)} [{x[2]}]" for x in dict.fromkeys(x for x in (it["a"], it["b"]) if x)]
                if it["kind"] == "X":
                    seen = [f"(nobody) - the phrase «{_q(t, sp)}» is marked elsewhere in this document"]
                if it["kind"] == "N":
                    seen = ["(nobody) - added so that every member of this list is treated alike (D55)"]
                ruling = f"MARK «{_q(t, g)}» as {g[2]}" if g else "DO NOT MARK"
                why = REASON.get(code.split(":")[0], "") if not g else ("re-drawn to follow Rules 1/9/12/14" if code.startswith("M:") else "")
                w.writerow([it["row"], it["doc"], "  |  ".join(seen), ruling, why, " ".join(t[lo:hi].split()), "", ""])

    n_gold = sum(len(v) for v in final.values())
    lab = Counter(sp[2] for v in final.values() for sp in v)
    summary = {"gold_spans": n_gold, "by_label": dict(lab), "agreed_accepted": sum(len(v) for v in agreed.values()),
               "items": sum(it["kind"] != "N" for it in items), "repeat_candidates": len(xitems),
               "added_new": sum(it["kind"] == "N" for it in items),
               "rulings": {f"{k}_{v}": n for (k, v), n in sorted(stats.items())},
               "reject_codes": dict(Counter(c for c in dec.values()
                                                if c.startswith(("R", "D47", "CO", "FR", "DUP"))).most_common()),
               **({"sample_size": len(sample), "sample_seed": args.seed} if sample else {}),
               "per_doc": {d: len(v) for d, v in final.items()}}
    (args.out / "auto_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_doc"}, indent=2))
    print(f"wrote {gold_path}" + (f" + sample_check_P1.csv / sample_check_P4.csv ({len(sample)} rulings each)"
                                  if sample else " (sample sheets left as they are)"))


def _sheet(out: Path, name: str, stem: str = "sample_check") -> list[dict]:
    """A filled sheet however the spreadsheet program saved it (CSV, tab-separated, UTF-16); '<name>_filled*' wins."""
    p = (sorted(out.glob(f"{stem}_{name}_filled*")) + [out / f"{stem}_{name}.csv"])[0]
    raw = p.read_bytes()
    try:
        txt = raw.decode("utf-16" if raw[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE) else "utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("cp1252")
    head = txt.splitlines()[0]
    tab = chr(9)
    print(f"{name}: reading {p.name}")
    return list(csv.DictReader(io.StringIO(txt, newline=""), delimiter=tab if head.count(tab) > head.count(",") else ","))


def cmd_negation(args):
    """The checked negation sheet -> negated.tsv (positions only). Then run `apply --sample 0`."""
    rows = _sheet(args.out, "P1", "negation_check")
    col = next(c for c in rows[0] if c and c.startswith("DENIED?"))
    ans = [r[col].strip().lower()[:1] for r in rows]
    assert all(a in ("y", "n") for a in ans), f"{sum(a not in ('y', 'n') for a in ans)} rows have no y/n answer"
    yes = [r for r, a in zip(rows, ans) if a == "y"]
    (args.out / "negated.tsv").write_text(
        "".join(f"{r['doc']}\t{r['start']}\t{r['end']}\t{r['label'][0]}\n" for r in yes), encoding="utf-8")
    changed = sum((a == "y") != r["PROPOSED"].startswith("DENIED") for r, a in zip(rows, ans))
    print(f"{len(yes)} of {len(rows)} checked highlights are negated ({changed} answers differ from the proposal) "
          f"-> {args.out / 'negated.tsv'}")


def cmd_score(args):
    rows = {}
    for name in ("P1", "P4"):
        rows[name] = {r["row"]: (r["AGREE with the ruling? (y/n)"].strip().lower()[:1], r["RULING"][:4])
                      for r in _sheet(args.out, name)}
    res = {}
    for name, r in rows.items():
        done = {i: v for i, v in r.items() if v[0] in ("y", "n")}
        yes = sum(v[0] == "y" for v in done.values())
        res[name] = {"checked": len(done), "agree": yes, "rate": round(yes / len(done), 4) if done else None}
        print(f"{name}: {yes}/{len(done)} rulings accepted" + (f" = {yes / len(done):.1%}" if done else ""))
    both = [i for i in rows["P1"] if rows["P1"][i][0] in "yn" and rows["P4"].get(i, ("",))[0] in "yn"
            and rows["P1"][i][0] and rows["P4"][i][0]]
    if both:
        same = sum(rows["P1"][i][0] == rows["P4"][i][0] for i in both)
        res["checkers_agree_with_each_other"] = round(same / len(both), 4)
        res["rejected_by_either"] = sorted(int(i) for i in both if "n" in (rows["P1"][i][0], rows["P4"][i][0]))
        print(f"the two checkers agree with each other on {same}/{len(both)}; rejected by either: "
              f"{res['rejected_by_either']}")
    (args.out / "sample_check_result.json").write_text(json.dumps(res, indent=2), encoding="utf-8")


def _selfcheck():
    t = "We share bank statements with lenders. Lenders transfer the loan. Keep your password safe."
    bs, l1, l2, pw = t.index("bank"), t.index("lenders"), t.index("Lenders"), t.index("password")
    A = {"d": {"text": t, "spans": [(bs, bs + 15, "DATA_TYPE"), (l1, l1 + 7, "THIRD_PARTY"), (l2, l2 + 7, "THIRD_PARTY")]}}
    B = {"d": {"text": t, "spans": [(bs, bs + 15, "DATA_TYPE"), (l1, l1 + 7, "THIRD_PARTY"), (pw, pw + 8, "DATA_TYPE")]}}
    agreed, items = build_items({"d": t}, A, B)
    assert agreed["d"] == [(bs, bs + 15, "DATA_TYPE")], agreed                  # agreed lender is doubted -> an item
    assert [(it["kind"], _q(t, it["a"] or it["b"])) for it in items] == \
        [("G", "lenders"), ("O", "Lenders"), ("O", "password")], items
    assert resolve(items[0], "A", t) == (l1, l1 + 7, "THIRD_PARTY") and resolve(items[1], "R16", t) is None
    assert resolve({"kind": "B", "a": (0, 5, "PURPOSE"), "b": (0, 9, "PURPOSE"), "id": 1}, "b", t) == (0, 9, "PURPOSE")
    assert resolve({"kind": "L", "a": (0, 5, "PURPOSE"), "b": (0, 9, "DATA_TYPE"), "id": 1}, "b", t) == (0, 9, "DATA_TYPE")
    assert resolve(items[2], "M:your password:P", t) == (pw - 5, pw + 8, "PURPOSE")   # re-drawn near the item
    assert "#1 G T «lenders»" in render({"d": t}, items)
    print("selfcheck OK")


def main():
    ap = argparse.ArgumentParser(description="Automatic adjudication with a human sample check.")
    ap.add_argument("cmd", choices=("items", "apply", "score", "negation", "selfcheck"))
    D = PROJECT_ROOT / "data" / "aa" / "annotated"
    ap.add_argument("--corpus", type=Path, default=D / "ls_import_tasks.json")
    ap.add_argument("--a", type=Path, default=D / "Export5A.json")
    ap.add_argument("--b", type=Path, default=D / "Export5B.json")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--decisions", type=Path, default=OUT / "decisions.tsv")
    ap.add_argument("--sample", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    args.out = args.out.resolve()
    {"items": cmd_items, "apply": cmd_apply, "score": cmd_score, "negation": cmd_negation,
     "selfcheck": lambda a: _selfcheck()}[args.cmd](args)


if __name__ == "__main__":
    main()
