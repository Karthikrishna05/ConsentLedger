"""Train the ConsentLedger summariser and score it with the project's acceptance check.

One file, no project imports, plain PyTorch loop (so it runs the same on Kaggle, Colab or a laptop,
whatever the transformers version).

    python train_summ.py --config summ_t5small.yaml    --data . --out out/t5small
    python train_summ.py --config summ_flant5base.yaml --data . --out out/flant5base
    python train_summ.py --selfcheck

In this repo (P2 handed the summariser over to P1 on 16 Oct; this is the exact script, pack v2, that trained
the two final models - D70, D73):
    python -m consentledger.summ.train --config configs/summ_flant5base.yaml --data data/summ --out artifacts_out/summ/flant5base

--data is the folder holding train.jsonl and dev.jsonl. After every pass over the training data the model
summarises the dev passages and the scores are printed. The model after the LAST pass is the one saved:
13 dev passages are too few to pick a "best" pass from (the scores jump by chance), so dev only reports.
Every summary is cut back to whole sentences that fit the passage's word cap (trim_to_cap) - the pipeline
applies the same step, so the length rule always holds.
Written to --out: the model + tokenizer, summ_meta.json (settings + scores), dev_predictions.jsonl.
Do NOT turn on fp16 / mixed precision: T5 produces NaN losses with it.
"""
import argparse
import json
import random
import re
from pathlib import Path

# ---- the acceptance check: a copy of check() in summ/build_dataset.py (same constants, same result) ----
FUNCTION_WORDS = {
    "a", "an", "the", "to", "for", "of", "in", "on", "at", "by", "with", "within", "during", "from",
    "and", "or", "any", "all", "such", "your", "our", "its", "their", "this", "that", "these", "those",
    "other", "including", "include", "includes", "related", "certain", "so", "it", "is", "are", "be",
    "as", "per", "under", "through", "upon", "via", "may", "will", "shall", "can", "we", "you", "us",
    "purpose", "purposes",
}
MAX_WORDS, MAX_RATIO, MIN_WORDS, MIN_COVERAGE = 60, 0.25, 12, 0.8


def content_words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in FUNCTION_WORDS and len(w) > 1}


def cap_for(n_src_words):
    return max(MIN_WORDS + 8, min(MAX_WORDS, int(n_src_words * MAX_RATIO)))


def check(n_src_words, summary, facts):
    """-> (accepted, reasons, share of checklist facts kept)."""
    n, reasons, scw = len(summary.split()), [], content_words(summary)
    if n > cap_for(n_src_words):
        reasons.append(f"too long: {n} words > cap {cap_for(n_src_words)}")
    if n < MIN_WORDS:
        reasons.append(f"too short: {n} words")
    facts = [f for f in facts if content_words(f)]
    missed = [f for f in facts
              if not scw or len(content_words(f) & scw) / min(len(content_words(f)), len(scw)) < 0.6]
    cov = 1 - len(missed) / len(facts) if facts else 1.0
    if cov < MIN_COVERAGE:
        reasons.append(f"dropped facts ({cov:.0%} kept): {missed}")
    return (not reasons), reasons, cov


def copied(summary, source):
    """Share of the summary's 4-word runs lifted word-for-word from the passage (1.0 = pure copying)."""
    s, t = re.findall(r"[a-z0-9]+", summary.lower()), " ".join(re.findall(r"[a-z0-9]+", source.lower()))
    runs = [" ".join(s[i:i + 4]) for i in range(len(s) - 3)]
    return sum(r in t for r in runs) / len(runs) if runs else 0.0


def trim_to_cap(summary, n_src_words):
    """Keep whole sentences while the summary stays within the passage's word cap."""
    cap, kept = cap_for(n_src_words), []
    for sent in re.split(r"(?<=[.!?])\s+", summary.strip()):
        if len(" ".join(kept + [sent]).split()) > cap:
            break
        kept.append(sent)
    if kept:
        return " ".join(kept)
    # one over-long sentence: cut it at its last comma/semicolon inside the cap, so it still ends cleanly
    words = summary.split()[:cap]
    cut = max((i for i, w in enumerate(words) if w[-1] in ",;"), default=None)
    return " ".join(words[:cut + 1]).rstrip(",;") + "." if cut else " ".join(words)


def selfcheck():
    facts = ["bank statements", "credit bureaus"]
    good = "We collect your bank statements and share them with credit bureaus to assess your loan."
    assert check(200, good, facts)[0]
    assert "too long" in check(200, good + " extra" * 60, facts)[1][0]
    assert "dropped facts" in check(200, "We collect some things about you and may share them with others.", facts)[1][0]
    assert cap_for(100) == 25 and cap_for(400) == 60 and cap_for(40) == 20
    assert copied("we collect your bank statements today", "x we collect your bank statements y") > 0.6
    two = "One two three four five six seven eight nine ten. " * 2 + "Eleven twelve thirteen."
    assert trim_to_cap(two, 80) == ("One two three four five six seven eight nine ten. " * 2).strip()   # cap 20
    assert trim_to_cap(good, 400) == good and len(trim_to_cap("word " * 90, 400).split()) == 60
    assert trim_to_cap("alpha beta, " + "gamma " * 30, 80) == "alpha beta."          # clause cut, clean ending
    print("selfcheck ok")


# ------------------------------------------------------------------------------------------- training
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path)
    ap.add_argument("--data", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    if args.selfcheck:
        return selfcheck()

    import torch
    import transformers
    import yaml
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    out = args.out or Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    read = lambda name: [json.loads(l) for l in (args.data / name).read_text(encoding="utf-8").splitlines() if l.strip()]
    train, dev = read("train.jsonl"), read("dev.jsonl")
    random.seed(cfg["seed"])
    torch.manual_seed(cfg["seed"])
    dev_cuda = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(cfg["model_name"])
    model = AutoModelForSeq2SeqLM.from_pretrained(cfg["model_name"]).to(dev_cuda)
    prefix, bs = cfg["source_prefix"], cfg["per_device_train_batch_size"]
    gen = dict(max_new_tokens=cfg["max_target_length"], num_beams=cfg["num_beams"],
               no_repeat_ngram_size=cfg["no_repeat_ngram_size"])

    def enc(rows):
        return tok([prefix + r["source"] for r in rows], return_tensors="pt", padding=True, truncation=True,
                   max_length=cfg["max_source_length"]).to(dev_cuda)

    def score_dev():
        model.eval()
        outs = []
        with torch.no_grad():
            for i in range(0, len(dev), 16):
                outs += tok.batch_decode(model.generate(**enc(dev[i:i + 16]), **gen), skip_special_tokens=True)
        raw, outs = outs, [trim_to_cap(o, r["n_src_words"]) for r, o in zip(dev, outs)]
        res = [check(r["n_src_words"], o, [f for v in r["cd"].values() for f in v]) for r, o in zip(dev, outs)]
        has = [bool([f for v in r["cd"].values() for f in v]) for r in dev]   # passages with a checklist
        return {"accepted": sum(a for a, _, _ in res), "of": len(dev),
                # passages without checklist facts pass on length alone, so the honest numbers are these two:
                "accepted_with_facts": sum(a for (a, _, _), h in zip(res, has) if h), "with_facts": sum(has),
                "facts_kept": round(sum(c for (_, _, c), h in zip(res, has) if h) / max(sum(has), 1), 3),
                "words": round(sum(len(o.split()) for o in outs) / len(dev), 1),
                "had_to_trim": sum(a != b for a, b in zip(raw, outs)),
                "copied": round(sum(copied(o, r["source"]) for r, o in zip(dev, outs)) / len(dev), 3)}, outs, res

    steps = (len(train) + bs - 1) // bs * cfg["num_train_epochs"]
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"])
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: max(0.0, 1 - s / steps))   # linear decay to 0
    history = [{"epoch": 0, **score_dev()[0]}]
    print("before training:", history[0], flush=True)
    for epoch in range(1, cfg["num_train_epochs"] + 1):
        model.train()
        random.shuffle(train)
        total = 0.0
        for i in range(0, len(train), bs):
            rows = train[i:i + bs]
            labels = tok(text_target=[r["reference"] for r in rows], return_tensors="pt", padding=True,
                         truncation=True, max_length=cfg["max_target_length"]).input_ids.to(dev_cuda)
            labels[labels == tok.pad_token_id] = -100
            loss = model(**enc(rows), labels=labels).loss
            assert torch.isfinite(loss), "loss is NaN/inf - is fp16 / mixed precision switched on?"
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            total += loss.item() * len(rows)
        m, outs, res = score_dev()
        history.append({"epoch": epoch, "train_loss": round(total / len(train), 4), **m})
        print(history[-1], flush=True)
    model.save_pretrained(out)
    tok.save_pretrained(out)
    with (out / "dev_predictions.jsonl").open("w", encoding="utf-8") as fh:
        fh.writelines(json.dumps({"id": r["id"], "summary": o, "accepted": a, "reasons": why},
                                 ensure_ascii=False) + "\n" for r, o, (a, why, _) in zip(dev, outs, res))
    meta = {"model_name": cfg["model_name"], "source_prefix": prefix, "max_source_length": cfg["max_source_length"],
            "generation": gen, "postprocess": "trim_to_cap", "learning_rate": cfg["learning_rate"],
            "num_train_epochs": cfg["num_train_epochs"], "batch_size": bs, "seed": cfg["seed"],
            "n_train": len(train), "n_dev": len(dev), "final_dev": m, "history": history,
            "transformers": transformers.__version__, "torch": torch.__version__}
    (out / "summ_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"saved the final model to {out}: {m}")


if __name__ == "__main__":
    main()
