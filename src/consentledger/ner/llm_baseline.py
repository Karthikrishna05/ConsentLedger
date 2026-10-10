"""Guideline-prompted LLM baseline for the three AA entity labels (D64).

A chat model is given the labelling rules (PROMPT) and, in the few-shot condition, SHOTS worked examples from the
adaptation TRAINING documents. It returns the entities of one passage as JSON; they are aligned back onto the
passage's words and scored by the same code as the fine-tuned models (evaluate.evaluate).

    # develop on the AA dev documents only (never on the test set):
    python -m consentledger.ner.llm_baseline --model llama3.1:8b --shots 0
    python -m consentledger.ner.llm_baseline --model llama3.1:8b --shots 8
    # once, with everything frozen:
    python -m consentledger.ner.llm_baseline --model llama3.1:8b --shots 8 --open-test

Any OpenAI-compatible chat endpoint works (--base-url). The default is a local Ollama server, so no document text
leaves the machine. For a hosted model put the key in the environment variable LLM_API_KEY (never in a file).

Two rules that keep the comparison honest:
  - PROMPT states the guideline's general rules only. The guideline's "tricky cases" quote test documents and are
    NOT in it; the self-check refuses a prompt that names a test organisation.
  - Few-shot examples come from aa_adapt_train.conll only - the same 10 documents E2 trains on.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from consentledger.data.bio_tagging import tokenize_with_offsets
from consentledger.ner.dataset import read_conll
from consentledger.ner.evaluate import LABELS, NER_BIO, PROJECT_ROOT, entities, evaluate, group_ids

OUT = PROJECT_ROOT / "artifacts_out" / "llm"
PROMPT = """You label entities in Indian Account Aggregator (AA) consent documents and fintech privacy policies.

Return every entity in the passage as JSON:
{"entities": [{"text": "<words copied exactly from the passage>", "label": "DATA_TYPE" | "PURPOSE" | "THIRD_PARTY"}]}
If there are none, return {"entities": []}. Return JSON only.

DATA_TYPE - a specific kind of the user's data that the passage says is collected, received, used, stored, accessed or shared (also when it says this is NOT done). Examples: email address, PAN, bank statements, date of birth, passwords.
PURPOSE - the activity the user's data is used for: a short activity name of at most 5 words, without a leading "to" or "for". It must belong to one of: credit or loan assessment; account monitoring and collection; financial management and insights; fetching, consolidating and sharing financial information; fraud prevention, security and verification; legal and regulatory compliance; customer support, complaints and disputes; communication; analytics and service improvement; marketing; corporate transactions (merger, acquisition); account opening and onboarding. Examples: credit assessment, fraud prevention, send notifications.
THIRD_PARTY - an outside organisation, or kind of organisation, that the passage says the user's data goes to or comes from. Examples: credit bureaus, service providers, law enforcement agencies.

Rules:
1. Copy the shortest phrase that names the thing. Drop determiners and possessives (your, the, our), status words (registered, valid) and a trailing "purposes".
2. A list is one entity per item ("name, email address and PAN" is three). Keep a list whole only when an item would mean nothing alone ("first and last name").
3. A name followed by its abbreviation in brackets is two entities: "Permanent Account Number" and "PAN".
4. Do NOT mark umbrella terms: information, data, personal information, personal data, financial information, sensitive personal data, details, services, third parties.
5. Do NOT mark the Account Aggregator framework's own actors: Account Aggregator / AA (also by company name), Financial Information Provider / FIP, Financial Information User / FIU, RBI, SEBI, IRDAI, PFRDA, Sahamati.
6. Do NOT mark the company that wrote the document, its staff, or the company's own details (its address, its officers' contact details).
7. Do NOT mark device or usage telemetry as DATA_TYPE: IP address, cookies, browser type, device identifiers, location, pages visited. What the user creates or provides (emails, messages, contact lists, photographs) IS a DATA_TYPE.
8. A THIRD_PARTY needs an exchange of the user's data in the passage. Do not mark organisations in indemnity, liability, jurisdiction, intellectual-property or definition clauses, or inside the name of a law.
9. A PURPOSE needs the passage to say the user's data is used, kept or shared for it. The user's rights (opt out, raise a grievance, revoke consent), headings with no data use, and duties of the user are not purposes.
10. Mark every occurrence that passes these rules, including in headings and table labels."""
TEST_ORGS = ("indifi", "pennydrop", "credbuddha", "zerodha", "icici", "nadl", "upmint", "financialist")


def detok(tokens: list[str]) -> str:
    t = " ".join(tokens)
    t = re.sub(r"\s+([,.;:!?%)\]])", r"\1", t)
    t = re.sub(r"([(\[])\s+", r"\1", t)
    return re.sub(r"\s*([-/'’])\s*", r"\1", t)


def shots(k: int, seed: int = 0) -> list[tuple[str, dict]]:
    """k worked examples from the adaptation TRAINING file: one empty passage in four, the rest covering all labels."""
    segs = read_conll(NER_BIO / "aa_adapt_train.conll")
    rng = random.Random(seed)
    rng.shuffle(segs)
    with_lab = {lab: [s for s in segs if any(e[0] == lab for e in entities(s["tags"]))] for lab in LABELS}
    empty = [s for s in segs if not entities(s["tags"])]
    picked, order = [], []
    for i in range(k):
        pool = empty if i % 4 == 3 else with_lab[LABELS[i % 4 % 3]]
        s = next(x for x in pool if x not in picked)
        picked.append(s)
        order.append((detok(s["tokens"]), {"entities": [{"text": detok(s["tokens"][a:b + 1]), "label": lab}
                                                         for lab, a, b in sorted(entities(s["tags"]), key=lambda e: e[1])]}))
    return order


def messages(passage: str, examples: list[tuple[str, dict]]) -> list[dict]:
    msgs = [{"role": "system", "content": PROMPT}]
    for text, ans in examples:
        msgs += [{"role": "user", "content": "Passage:\n" + text},
                 {"role": "assistant", "content": json.dumps(ans, ensure_ascii=False)}]
    return msgs + [{"role": "user", "content": "Passage:\n" + passage}]


def ask(base_url: str, model: str, msgs: list[dict], timeout: int = 300) -> tuple[str, int]:
    """-> (reply, prompt tokens). The token count is kept because a server silently cuts a prompt that is longer
    than its context window - from the front, i.e. the rules."""
    # max_tokens: a small model can fall into repeating one entity for ever; a 100-word passage never needs 1024.
    body = {"model": model, "messages": msgs, "temperature": 0, "seed": 0, "max_tokens": 1024,
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ.get("LLM_API_KEY", "none")})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"], int(d.get("usage", {}).get("prompt_tokens", 0))


def parse(reply: str) -> list[tuple[str, str]]:
    """The model's reply -> [(label, text)]; anything malformed is dropped, never guessed."""
    m = re.search(r"\{.*\}", reply, re.S)
    try:
        items = json.loads(m.group())["entities"] if m else []
    except (json.JSONDecodeError, KeyError, TypeError):
        # a reply cut off at max_tokens: keep the entity objects that were written out completely
        items = [json.loads(x) for x in re.findall(r'\{\s*"text"\s*:\s*"(?:[^"\\]|\\.)*"\s*,\s*"label"\s*:\s*"[A-Z_]+"\s*\}', reply)]
    if not isinstance(items, list):
        return []
    return [(e["label"], e["text"]) for e in items
            if isinstance(e, dict) and e.get("label") in LABELS and isinstance(e.get("text"), str) and e["text"].strip()]


def to_tags(tokens: list[str], ents: list[tuple[str, str]]) -> tuple[list[str], int]:
    """Align returned phrases onto the passage's words -> (BIO tags, number of phrases not found in the passage).
    Every occurrence of a phrase is tagged (Rule 7); longer phrases first; nothing overlaps."""
    low = [t.lower() for t in tokens]
    tags, unmatched = ["O"] * len(tokens), 0
    for lab, text in sorted(set(ents), key=lambda e: -len(e[1])):
        words = [w.lower() for w, _, _ in tokenize_with_offsets(text)]
        hits = [i for i in range(len(low) - len(words) + 1) if low[i:i + len(words)] == words] if words else []
        unmatched += not hits
        for i in hits:
            if all(t == "O" for t in tags[i:i + len(words)]):
                tags[i:i + len(words)] = [f"B-{lab}"] + [f"I-{lab}"] * (len(words) - 1)
    return tags, unmatched


def main() -> None:
    ap = argparse.ArgumentParser(description="Guideline-prompted LLM baseline for AA entities.")
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://localhost:11434/v1", help="OpenAI-compatible endpoint (default: local Ollama)")
    ap.add_argument("--shots", type=int, default=0, help="worked examples from the adaptation training documents")
    ap.add_argument("--open-test", action="store_true", help="score the sealed AA test set (logged)")
    ap.add_argument("--limit", type=int, help="first N passages only (quick trials on dev)")
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()

    conll = NER_BIO / ("aa_test.conll" if args.open_test else "aa_adapt_dev.conll")
    assert not (args.open_test and args.limit), "the test set is scored whole, once"
    name = re.sub(r"[^\w.-]+", "_", args.model) + f"_{args.shots}shot"
    out = OUT / name / ("test" if args.open_test else "dev")
    out.mkdir(parents=True, exist_ok=True)
    cache = out / "replies.jsonl"                                       # resumable; contains policy text - not for git
    done = [json.loads(ln) for ln in cache.read_text(encoding="utf-8").splitlines()] if cache.exists() else []
    segs = read_conll(conll)[:args.limit]
    examples = shots(args.shots)
    with cache.open("a", encoding="utf-8") as fh:
        for i in range(len(done), len(segs)):
            reply, n_prompt = ask(args.base_url, args.model, messages(detok(segs[i]["tokens"]), examples))
            done.append({"i": i, "reply": reply, "prompt_tokens": n_prompt})
            fh.write(json.dumps(done[-1], ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(segs)}", flush=True)

    tokens, gold, pred, unmatched, returned, bad = [], [], [], 0, 0, 0
    for s, d in zip(segs, done):
        ents = parse(d["reply"])
        bad += not re.search(r'"entities"', d["reply"])
        tags, u = to_tags(s["tokens"], ents)
        tokens.append(s["tokens"]); gold.append(s["tags"]); pred.append(tags)
        unmatched += u; returned += len(set(ents))
    groups = group_ids(conll, len(read_conll(conll)), "group" if args.open_test else "doc")[:len(segs)]
    res = {"conll_file": str(conll), "model_dir": name, "condition": f"LLM-{args.shots}shot", "seed": 0,
           "model": args.model, "shots": args.shots, "truncated_segments": 0,
           "phrases_returned": returned, "phrases_not_in_passage": unmatched, "malformed_replies": bad,
           "max_prompt_tokens": max(d.get("prompt_tokens", 0) for d in done),
           **evaluate(tokens, gold, pred, groups, args.bootstrap, 0)}
    (out / "metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    ci = res.get("ci95", {})
    print(f"\n=== {conll.name} | {args.model} | {args.shots}-shot | {len(segs)} passages, {res['entities_gold']} gold entities ===")
    print(f"  exact micro-F1 {res['micro_f1']:.4f}" + (f"  95% CI {ci['micro_f1']}" if ci else "")
          + f" | macro {res['macro_f1']:.4f} | relaxed micro {res['relaxed']['micro_f1']:.4f}")
    print(f"  P {res['precision']:.3f} R {res['recall']:.3f} | predicted {res['entities_predicted']} | "
          f"{unmatched} of {returned} returned phrases were not in the passage | {bad} malformed replies | "
          f"longest prompt {res['max_prompt_tokens']} tokens")
    print(f"  saved -> {out / 'metrics.json'}")
    if args.open_test:
        with (PROJECT_ROOT / "results" / "ner" / "test_openings.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "model_dir": f"llm/{name}",
                                 "condition": res["condition"], "seed": 0, "micro_f1": res["micro_f1"]}) + "\n")
        print("TEST SET OPENED - logged in results/ner/test_openings.jsonl")


def _selfcheck() -> None:
    assert not any(o in PROMPT.lower() for o in TEST_ORGS), "the prompt names a test organisation"
    tok = ["We", "share", "your", "e", "-", "mail", "address", "and", "PAN", "with", "credit", "bureaus", ";", "PAN", "is", "masked", "."]
    assert detok(tok) == "We share your e-mail address and PAN with credit bureaus; PAN is masked."
    tags, miss = to_tags(tok, [("DATA_TYPE", "e-mail address"), ("DATA_TYPE", "pan"), ("THIRD_PARTY", "Credit Bureaus"),
                               ("DATA_TYPE", "address"), ("PURPOSE", "marketing")])
    assert tags[3:7] == ["B-DATA_TYPE", "I-DATA_TYPE", "I-DATA_TYPE", "I-DATA_TYPE"] and miss == 1, (tags, miss)   # nested "address" loses
    assert tags[8] == tags[13] == "B-DATA_TYPE" and tags[10:12] == ["B-THIRD_PARTY", "I-THIRD_PARTY"]            # every occurrence
    assert parse('```json\n{"entities": [{"text": "PAN", "label": "DATA_TYPE"}, {"text": "x", "label": "OTHER"}]}\n```') == [("DATA_TYPE", "PAN")]
    assert parse("sorry, I cannot") == [] and parse('{"entities": "none"}') == []
    ex = shots(8)
    assert ex == shots(8) and len(ex) == 8 and sum(not a["entities"] for _, a in ex) == 2                      # deterministic; 2 empty
    assert {e["label"] for _, a in ex for e in a["entities"]} == set(LABELS)
    train = {detok(s["tokens"]) for s in read_conll(NER_BIO / "aa_adapt_train.conll")}
    assert all(t in train for t, _ in ex) and len(messages("p", ex)) == 18
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
