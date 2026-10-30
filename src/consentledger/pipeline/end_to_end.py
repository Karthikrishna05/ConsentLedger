"""doc -> entities -> summary -> faithfulness -> on-chain -> report JSON.

One policy document (and, optionally, the consent artefact the user is asked to grant) in; one report out:
  1. clean     .html / .pdf -> plain text (data/clean.py); .txt is read as it is
  2. NER       data types, purposes, third parties, with positions (ner/predict.py)
  3. parse     recipient, duration, frequency, data range, data life from the consent JSON (consent_artefact/parse.py)
  4. passages  the document cut as the summariser was trained (summ/predict.py), each summarised
  5. gate      every summary checked against its passage and its facts (summ/faithfulness.py):
               reject -> the passage's facts are shown instead; add -> summary + the missing facts; show
  6. record    the assembled artefact = the consent JSON + the policy's facts (+ the document's SHA-256).
               Its Keccak-256 fingerprint is in the report; with --chain it is registered on Sepolia (chain/)
The report quotes the policy, so it is written to results/pipeline/ (git-ignored).

    python -m consentledger.pipeline.end_to_end --doc policy.html --consent data/aa/consent_artefacts/demo_consent.json
    python -m consentledger.pipeline.end_to_end --doc policy.txt --consent consent.json --chain     # needs .env
    python -m consentledger.pipeline.end_to_end --selfcheck
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from consentledger.consent_artefact.parse import parse
from consentledger.summ import faithfulness

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "results" / "pipeline"


def read_document(path: Path) -> str:
    from consentledger.data.clean import _normalize, clean_html, clean_pdf
    ext = path.suffix.lower()
    if ext in (".html", ".htm"):
        return clean_html(path.read_bytes())
    if ext == ".pdf":
        return clean_pdf(path)
    return _normalize(path.read_text(encoding="utf-8-sig"))


def load_models() -> dict:
    """Both models, loaded once (the app keeps them between requests)."""
    from consentledger.ner import predict as ner
    from consentledger.summ import predict as summ
    return {"ner": ner.load(), "summ": summ.load(), "names": {"ner": ner.RUN, "summariser": summ.MODEL}}


def assemble(artefact: dict | None, doc_sha256: str, facts: list[dict]) -> dict:
    """The record that is fingerprinted: the consent artefact as given, plus what the policy says.
    Facts are deduplicated per label, sorted, and marked denied only if every mention denies them."""
    terms: dict[str, dict[str, bool]] = {}
    for f in facts:
        key = " ".join(f["text"].lower().split())
        seen = terms.setdefault(f["label"], {})
        seen[key] = seen.get(key, True) and f["denied"]
    policy = {"document_sha256": doc_sha256,
              **{lab: [{"text": t, "denied": d} for t, d in sorted(v.items())] for lab, v in sorted(terms.items())}}
    return {**(artefact or {}), "PolicyTerms": policy}


def _offset_in_passage(text: str, p_start: int, start: int, fact: str) -> int | None:
    """Where a fact at document offset `start` sits in its whitespace-normalised passage, so the gate judges THIS
    mention ("we will not sell your mobile number"), not the first one with the same words."""
    prefix = text[p_start:start]
    off = len(" ".join(prefix.split())) + (1 if prefix.split() and prefix[-1:].isspace() else 0)
    norm = " ".join(text[p_start:].split())
    return off if norm[off:off + len(" ".join(fact.split()))] == " ".join(fact.split()) else None


def run(text: str, artefact: dict | None = None, models: dict | None = None, chain: bool = False) -> dict:
    from consentledger.chain.register_consent import hash_artefact
    from consentledger.ner.predict import predict
    from consentledger.summ.predict import passages, summarise

    m = models or load_models()
    ents = predict(text, *m["ner"])
    ps = passages(text)
    summaries = summarise([p["text"] for p in ps], *m["summ"])
    out_passages, all_facts = [], []
    for i, (p, s) in enumerate(zip(ps, summaries)):
        mine = [e for e in ents if p["start"] <= e["start"] < p["end"]]
        context = ps[i - 1]["text"] if i else ""
        g = faithfulness.gate(p["text"], s, [(e["text"], e["label"], _offset_in_passage(text, p["start"], e["start"], e["text"]))
                                             for e in mine], context)
        facts = [dict(f, start=e["start"], end=e["end"]) for f, e in zip(g["facts"], mine)]
        all_facts += facts
        out_passages.append({
            "start": p["start"], "end": p["end"], "verdict": g["verdict"],
            "summary": None if g["verdict"] == "reject" else s,      # a rejected summary is never shown...
            "rejected_summary": s if g["verdict"] == "reject" else None,   # ...but kept for the record
            "why_rejected": {k: g[k] for k in ("reversed", "swapped", "invented") if g[k]},
            "coverage": g["coverage"], "missing": g["missing"], "facts": facts})
    doc_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    record = assemble(artefact, doc_sha, all_facts)
    report = {"document_sha256": doc_sha, "models": m["names"], "facts": all_facts, "passages": out_passages,
              "consent": parse(artefact) if artefact else None, "record": record,
              "record_hash": "0x" + bytes(hash_artefact(record)).hex(), "chain": None}
    if chain:
        if not artefact:
            raise ValueError("--chain needs the consent artefact (--consent): its expiry is what the chain enforces")
        from consentledger.chain.register_consent import register
        report["chain"] = register(record)
    return report


def summary_line(r: dict) -> str:
    v = [p["verdict"] for p in r["passages"]]
    chain = f" | on chain: {r['chain']['consent_id'][:12]}... {r['chain']['audit_link'] or '(local chain)'}" if r["chain"] else ""
    return (f"{len(r['facts'])} facts ({sum(f['denied'] for f in r['facts'])} denied) | {len(v)} passages: "
            f"{v.count('show')} shown, {v.count('add')} shown with missing facts, {v.count('reject')} replaced by "
            f"their facts | record {r['record_hash'][:14]}...{chain}")


def _selfcheck() -> None:
    from consentledger.chain.register_consent import expiry_timestamp, hash_artefact
    policy = ("1. COLLECTION\nWe collect your bank statements, PAN and mobile number when you register on the "
              "Platform, and we use them to assess your eligibility for a loan.\n"
              "2. SHARING\nWe share your financial information with credit bureaus and lenders only with your "
              "explicit consent. We shall not access your user authentication credentials. We will not share "
              "your bank statements with advertisers.\n") * 4
    demo = json.loads((PROJECT_ROOT / "data" / "aa" / "consent_artefacts" / "demo_consent.json").read_text(encoding="utf-8"))
    models = load_models()
    r = run(policy, demo, models)
    texts = {f["text"].lower() for f in r["facts"]}
    assert "bank statements" in texts and r["passages"] and all(p["verdict"] in ("show", "add", "reject") for p in r["passages"])
    assert any(f["text"].lower() == "user authentication credentials" and f["denied"] for f in r["facts"]), r["facts"]
    flags = {f["denied"] for f in r["facts"] if f["text"].lower() == "bank statements"}
    assert flags == {True, False}, flags                 # each mention judged where it stands
    assert _offset_in_passage("a  b\n(PAN) x", 0, 6, "PAN") == 5 and _offset_in_passage("a b", 0, 2, "zz") is None
    terms = {x["text"]: x["denied"] for x in r["record"]["PolicyTerms"]["DATA_TYPE"]}
    assert terms["user authentication credentials"] and not terms["bank statements"]   # collected AND not shared
    assert all(p["summary"] or p["verdict"] == "reject" for p in r["passages"])
    assert r["consent"]["FREQUENCY"] == {"unit": "MONTH", "value": 1}
    # the fingerprint: reproducible, covers the policy's facts, and keeps the consent's own expiry
    assert run(policy, demo, models)["record_hash"] == r["record_hash"]
    assert "0x" + bytes(hash_artefact(r["record"])).hex() == r["record_hash"]
    assert expiry_timestamp(r["record"]) == expiry_timestamp(demo)
    assert hash_artefact(assemble(demo, r["document_sha256"], r["facts"][1:])) == hash_artefact(r["record"])  # a repeat
    other = assemble(demo, r["document_sha256"], [f for f in r["facts"] if f["text"].lower() != "pan"])
    assert hash_artefact(other) != hash_artefact(r["record"])                                     # a fact gone
    assert [t["text"] for t in r["record"]["PolicyTerms"]["DATA_TYPE"]] == sorted(t["text"] for t in r["record"]["PolicyTerms"]["DATA_TYPE"])
    print(summary_line(r))
    print("selfcheck ok")


def main() -> None:
    ap = argparse.ArgumentParser(description="Policy (+ consent) -> facts, checked summaries, fingerprint, report.")
    ap.add_argument("--doc", type=Path, help=".txt, .html or .pdf policy document")
    ap.add_argument("--consent", type=Path, help="the ReBIT consent artefact (JSON) the user is asked to grant")
    ap.add_argument("--chain", action="store_true", help="register the fingerprint on-chain (needs .env, test wallet)")
    ap.add_argument("--out", type=Path, help=f"report path (default {OUT_DIR.relative_to(PROJECT_ROOT)}/<doc>.json)")
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    if args.selfcheck:
        return _selfcheck()
    if not args.doc:
        ap.error("--doc is required")
    artefact = json.loads(args.consent.read_text(encoding="utf-8-sig")) if args.consent else None
    if artefact is not None and not isinstance(artefact, dict):
        ap.error("the consent file must hold a JSON object")
    report = run(read_document(args.doc), artefact, chain=args.chain)
    out = args.out or OUT_DIR / f"{args.doc.stem}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(summary_line(report))
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
