"""Build the summarizer dataset: real policy chunks + NER fact checklists + length-checked references.

Documents are cut into ~180-260-word chunks (T5 takes 512 tokens). References must be at most 25% of the
source and 60 words, and keep 80% of the chunk's NER fact checklist, or they are rejected (an unbounded
"summarise this" gives paraphrase, not compression). Facts are silver (adjudicated merge of the two
annotators) unless --gold is given. The split is by document, the same as the NER split (aa_split.json).

    chunks    -> data/summ/chunks_{train,test}.jsonl and prompts_{train,test}.jsonl (one LLM prompt per chunk)
    validate  -> reads data/summ/refs_train.jsonl, writes train.jsonl, dev.jsonl and rejected_train.jsonl

Usage:
    python -m consentledger.summ.build_dataset chunks
    python -m consentledger.summ.build_dataset validate
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

from consentledger.data.adjudicate import adjudicate_doc
from consentledger.data.annotation_audit import build_consensus_lexicon, load_corpus, norm
from consentledger.data.kappa import load_ls_export
from consentledger.data.relaxed_agreement import content_words, overlap_coeff

ROOT = Path(__file__).resolve().parents[3]
ANN = ROOT / "data" / "aa" / "annotated"
OUT = ROOT / "data" / "summ"

MIN_WORDS, MAX_WORDS = 180, 260            # chunk size (T5 input limit is 512 subword tokens)
MAX_SUMMARY_WORDS, MAX_RATIO = 60, 0.25    # the countable compression rule
MIN_SUMMARY_WORDS = 12
MIN_COVERAGE = 0.8                          # share of checklist facts a reference must keep
MAX_FACT_WORDS = 6                          # longer "facts" are clause-length annotations, not entities
KEYMAP = {"DATA_TYPE": "data_types", "PURPOSE": "purposes", "THIRD_PARTY": "third_parties"}
# numbered clause (1. / 2.3 / (a)) or an ALL-CAPS heading line -> a good place to cut a chunk
SECTION = re.compile(r"^\s*(\(?\d+(\.\d+)*[.)]?\s|\(?[a-z]\)\s|[A-Z][A-Z0-9 &/,'-]{4,}$)")

PROMPT = """You are summarising one passage from an Indian Account Aggregator (AA) policy for an ordinary customer.

Write a plain-English summary that:
- is AT MOST {cap} words, in 1 to 3 sentences;
- mentions EVERY item in this checklist (you may paraphrase, but keep each item recognisable): {facts}
- adds nothing that is not in the passage (no advice, no opinion, no background).
Output only the summary.

PASSAGE:
{text}"""


# ------------------------------------------------------------------------------------------ chunking
def _segments(text: str, max_words: int) -> list[tuple[int, int]]:
    """Non-empty lines as (start, end) offsets; any line longer than max_words is split at sentences."""
    segs, pos = [], 0
    for line in text.split("\n"):
        start, end = pos, pos + len(line)
        pos = end + 1
        if not line.strip():
            continue
        if len(line.split()) <= max_words:
            segs.append((start, end))
            continue
        cur = None
        for m in re.finditer(r"[^.;]+[.;]?", line):
            if not m.group().strip():
                continue
            a, b = start + m.start(), start + m.end()
            if cur and len(text[cur[0]:b].split()) > max_words:
                segs.append(cur)
                cur = (a, b)
            else:
                cur = (cur[0], b) if cur else (a, b)
        if cur:
            segs.append(cur)
    return segs


def chunk(text: str, min_w: int = MIN_WORDS, max_w: int = MAX_WORDS) -> list[tuple[int, int]]:
    """Pack line segments into ~min_w..max_w-word chunks, preferring cuts at section starts."""
    chunks, cur_s, cur_e, words = [], None, None, 0
    for a, b in _segments(text, max_w):
        w = len(text[a:b].split())
        at_section = bool(SECTION.match(text[a:b]))
        if cur_s is not None and (words + w > max_w or (words >= min_w and at_section)):
            chunks.append((cur_s, cur_e))
            cur_s, words = None, 0
        if cur_s is None:
            cur_s = a
        cur_e, words = b, words + w
    if cur_s is not None:
        chunks.append((cur_s, cur_e))
    # fold a tiny trailing chunk into its predecessor
    if len(chunks) > 1 and len(text[chunks[-1][0]:chunks[-1][1]].split()) < 40:
        chunks[-2:] = [(chunks[-2][0], chunks[-1][1])]
    return chunks


def facts_in(text: str, gold_spans, lo: int, hi: int) -> dict[str, list[str]]:
    """Deduplicated fact checklist for the chunk [lo, hi): annotated spans fully inside it."""
    out = {v: [] for v in KEYMAP.values()}
    seen = set()
    for s, e, lab in gold_spans:
        if s >= lo and e <= hi and lab in KEYMAP:
            p = " ".join(text[s:e].split())
            key = (lab, norm(p))
            if key in seen or not p or len(p.split()) > MAX_FACT_WORDS:
                continue
            seen.add(key)
            out[KEYMAP[lab]].append(p)
    return out


def _flat(cd: dict) -> list[str]:
    return [f for v in cd.values() for f in v]


def cmd_chunks(args) -> None:
    if args.gold:   # the final answer key: its highlights ARE the checklists, nothing is re-adjudicated
        gold = {d["doc_id"]: d for d in json.loads(args.gold.read_text(encoding="utf-8"))}
        corpus = {k: d["text"] for k, d in gold.items()}
        spans = {k: [(s["start"], s["end"], s["label"]) for s in d["spans"]] for k, d in gold.items()}
        docs = sorted(gold)
    else:
        corpus = load_corpus(args.corpus)
        A, B = load_ls_export(args.a), load_ls_export(args.b)
        docs = sorted(set(corpus) & set(A) & set(B))
        lexicon = build_consensus_lexicon(A, B, min_count=1, multiword=False, drop_generic=True)
    docs = [d for d in docs if d not in set(args.skip_docs or [])]
    test_docs = set(args.test_docs or docs[:10])
    OUT.mkdir(parents=True, exist_ok=True)

    rows = {"train": [], "test": []}
    for key in docs:
        text = corpus[key]
        silver = spans[key] if args.gold else adjudicate_doc(text, A[key]["spans"], B[key]["spans"], lexicon)[0]
        for i, (lo, hi) in enumerate(chunk(text)):
            src = " ".join(text[lo:hi].split())
            cd = facts_in(text, silver, lo, hi)
            rows["test" if key in test_docs else "train"].append({
                "id": f"{key}__c{i:02d}", "doc_id": key, "source": src,
                "n_src_words": len(src.split()), "cd": cd, "facts_kind": "gold" if args.gold else "silver",
            })

    # training keeps only informative chunks: enough text and at least --min-facts facts
    train = [r for r in rows["train"] if r["n_src_words"] >= 60 and len(_flat(r["cd"])) >= args.min_facts]
    for name, data in (("chunks_train", train), ("chunks_test", rows["test"])):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in data)

    # test prompts give silver references for the optional ROUGE/BERTScore only; the headline metric is reference-free
    scorable_test = [r for r in rows["test"] if r["n_src_words"] >= 60]
    for name, data in (("prompts_train", train), ("prompts_test", scorable_test)):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            for r in data:
                cap = cap_for(r["n_src_words"])
                fh.write(json.dumps({"id": r["id"], "cap_words": cap, "prompt": PROMPT.format(
                    cap=cap, facts="; ".join(_flat(r["cd"])) or "(none)", text=r["source"])},
                    ensure_ascii=False) + "\n")

    nf = Counter()
    for r in train:
        for k, v in r["cd"].items():
            nf[k] += len(v)
    print(f"docs: {len(docs)} ({len(docs) - len(test_docs)} train / {len(test_docs)} test)")
    print(f"chunks: {len(rows['train'])} train-doc chunks -> {len(train)} kept "
          f"(>=60 words and >={args.min_facts} facts); {len(rows['test'])} test-doc chunks")
    print(f"training checklist facts: {dict(nf)}")
    n_gold = sum(1 for r in rows["test"] if _flat(r["cd"]))
    print(f"test chunks with >=1 fact (scorable for coverage): {n_gold}/{len(rows['test'])}  "
          f"[facts are {'GOLD' if args.gold else 'SILVER - rerun with --gold data/aa/annotated/gold.json'}]")
    print("wrote data/summ/chunks_train.jsonl, chunks_test.jsonl, prompts_train.jsonl, prompts_test.jsonl")


# ---------------------------------------------------------------------------------------- validation
def cap_for(n_src_words: int) -> int:
    return max(MIN_SUMMARY_WORDS + 8, min(MAX_SUMMARY_WORDS, int(n_src_words * MAX_RATIO)))


def check(source_words: int, summary: str, facts: list[str]) -> tuple[bool, list[str], float]:
    """Apply the countable rules. Returns (accepted, reasons, fact_coverage)."""
    n = len(summary.split())
    reasons = []
    cap = cap_for(source_words)
    if n > cap:
        reasons.append(f"too long: {n} words > cap {cap} ({source_words}-word source)")
    if n < MIN_SUMMARY_WORDS:
        reasons.append(f"too short: {n} words")
    scw = content_words(summary)
    checkable = [f for f in facts if content_words(f)]
    missed = [f for f in checkable if overlap_coeff(content_words(f), scw) < 0.6]
    cov = 1 - len(missed) / len(checkable) if checkable else 1.0
    if cov < MIN_COVERAGE:
        reasons.append(f"dropped facts ({cov:.0%} kept): {missed}")
    return (not reasons), reasons, cov


def cmd_validate(args) -> None:
    chunks = {json.loads(l)["id"]: json.loads(l)
              for l in (OUT / "chunks_train.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    refs = [json.loads(l) for l in args.refs.read_text(encoding="utf-8").splitlines() if l.strip()]
    ok, bad = [], []
    for r in refs:
        c = chunks.get(r["id"])
        if c is None:
            bad.append({**r, "reasons": ["unknown chunk id"]})
            continue
        summary = " ".join(r["summary"].split())
        accepted, reasons, cov = check(c["n_src_words"], summary, _flat(c["cd"]))
        rec = {"id": c["id"], "doc_id": c["doc_id"], "source": c["source"], "reference": summary,
               "cd": c["cd"], "n_src_words": c["n_src_words"], "n_ref_words": len(summary.split()),
               "coverage": round(cov, 3)}
        (ok if accepted else bad).append(rec if accepted else {**rec, "reasons": reasons})
    # dev = a share of the accepted training pairs, for early stopping; the test set is never used for tuning
    rng = random.Random(42)
    rng.shuffle(ok)
    n_dev = int(round(len(ok) * args.dev_frac)) if len(ok) >= 10 else 0
    dev, ok = ok[:n_dev], ok[n_dev:]
    for name, data in (("train", ok), ("dev", dev), ("rejected_train", bad)):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in data)
    ratio = sum(r["n_ref_words"] for r in ok) / max(sum(r["n_src_words"] for r in ok), 1)
    why = Counter(x.split(":")[0] for r in bad for x in r["reasons"])
    print(f"references: {len(refs)} | accepted {len(ok)} | rejected {len(bad)}  {dict(why)}")
    print(f"accepted pairs: mean compression {ratio:.0%} of source words, "
          f"mean fact coverage {sum(r['coverage'] for r in ok) / max(len(ok), 1):.0%}")
    print(f"split: {len(ok)} train / {len(dev)} dev (dev = early stopping only; test stays sealed)")
    print("wrote data/summ/train.jsonl + dev.jsonl (for summ/train.py) + rejected_train.jsonl (regenerate these)")


def _selfcheck() -> None:
    text = "\n".join(f"{i}. Clause about bank statements and credit bureaus. " + "word " * 40
                     for i in range(1, 12))
    ch = chunk(text)
    assert all(len(text[a:b].split()) <= MAX_WORDS for a, b in ch), "chunk too long"
    assert ch[0][0] == 0 and ch[-1][1] == len(text), "chunks must cover the text"
    facts = ["bank statements", "credit bureaus"]
    good = "The lender may read your bank statements and share them with credit bureaus for checks."
    assert check(220, good, facts)[0]
    assert not check(220, "They may use your information.", facts)[0]          # drops facts, too short
    assert not check(100, " ".join(["bank statements credit bureaus"] * 12), facts)[0]   # over cap
    print("selfcheck OK")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the summarizer dataset.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chunks")
    c.add_argument("--corpus", type=Path, default=ANN / "ls_import_tasks.json")
    c.add_argument("--a", type=Path, default=ANN / "Export2A.json")
    c.add_argument("--b", type=Path, default=ANN / "Export2B.json")
    c.add_argument("--gold", type=Path, help="final gold.json; its highlights become the checklists")
    c.add_argument("--test-docs", nargs="+", help="doc_ids held out for testing (default: first 10)")
    c.add_argument("--skip-docs", nargs="+", help="doc_ids left out altogether (e.g. the glued-text documents)")
    c.add_argument("--min-facts", type=int, default=1,
                   help="min checklist facts for a training chunk (0 = also train pure compression)")
    v = sub.add_parser("validate")
    v.add_argument("--refs", type=Path, default=OUT / "refs_train.jsonl")
    v.add_argument("--dev-frac", type=float, default=0.1, help="share of accepted pairs held out as dev")
    args = ap.parse_args()
    (cmd_chunks if args.cmd == "chunks" else cmd_validate)(args)


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
