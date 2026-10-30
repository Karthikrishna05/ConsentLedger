"""Passage -> plain-language summary, exactly as the final models were trained and checked.

The passage cutter, summ_meta.json settings and trim step must match training. `chunk`, `cap_for` and
`trim_to_cap` are copies of build_dataset.py / summ/train.py; the selfcheck compares them when present.
Models: Flan-T5-base (main) and t5-small, from artifacts_out/summ/p2_final/<name> or the private Hub repo.

    python -m consentledger.summ.predict --file <policy.txt>
    python -m consentledger.summ.predict --selfcheck
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HUB_REPO = "Karthikrishna05/consentledger-summ"
MODEL = "flant5base"
MIN_WORDS, MAX_WORDS = 180, 260            # passage size
MAX_SUMMARY_WORDS, MAX_RATIO, MIN_SUMMARY_WORDS = 60, 0.25, 12
SECTION = re.compile(r"^\s*(\(?\d+(\.\d+)*[.)]?\s|\(?[a-z]\)\s|[A-Z][A-Z0-9 &/,'-]{4,}$)")


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
    if len(chunks) > 1 and len(text[chunks[-1][0]:chunks[-1][1]].split()) < 40:    # fold a tiny tail
        chunks[-2:] = [(chunks[-2][0], chunks[-1][1])]
    return chunks


def passages(text: str) -> list[dict]:
    """The passages a document is summarised in: offsets plus the whitespace-normalised text the model reads."""
    return [{"start": a, "end": b, "text": " ".join(text[a:b].split())} for a, b in chunk(text)]


def cap_for(n_src_words: int) -> int:
    return max(MIN_SUMMARY_WORDS + 8, min(MAX_SUMMARY_WORDS, int(n_src_words * MAX_RATIO)))


def trim_to_cap(summary: str, n_src_words: int) -> str:
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


def load(name: str = MODEL):
    """-> (tokenizer, model, meta) on the GPU if there is one."""
    import torch
    from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer

    d = PROJECT_ROOT / "artifacts_out" / "summ" / "p2_final" / name
    if not (d / "model.safetensors").exists():
        from huggingface_hub import snapshot_download
        d = Path(snapshot_download(HUB_REPO, allow_patterns=[f"{name}/*"])) / name
        if not (d / "model.safetensors").exists():     # offline, it returns whatever is cached, possibly without this model
            raise RuntimeError(f"{HUB_REPO}/{name} could not be downloaded: check the internet connection and the Hub "
                               "token (HF_TOKEN or `hf auth login`), then try again - finished files are kept.")
    raw =json.loads((d / "config.json").read_text(encoding="utf-8"))
    cfg = AutoConfig.from_pretrained(str(d))
    if "scale_decoder_outputs" in raw:     # saved by transformers 5: our 4.46 misreads the tying flag
        cfg.tie_word_embeddings = raw["scale_decoder_outputs"]
    model = AutoModelForSeq2SeqLM.from_pretrained(str(d), config=cfg, use_safetensors=True).eval()
    meta = json.loads((d / "summ_meta.json").read_text(encoding="utf-8"))
    return AutoTokenizer.from_pretrained(str(d)), model.to("cuda" if torch.cuda.is_available() else "cpu"), meta


def summarise(texts: list[str], tok, model, meta: dict, batch: int = 16) -> list[str]:
    import torch

    out = []
    for i in range(0, len(texts), batch):
        enc = tok([meta["source_prefix"] + t for t in texts[i:i + batch]], return_tensors="pt", padding=True,
                  truncation=True, max_length=meta["max_source_length"]).to(model.device)
        with torch.no_grad():
            out += tok.batch_decode(model.generate(**enc, **meta["generation"]), skip_special_tokens=True)
    return [trim_to_cap(o, len(t.split())) for o, t in zip(out, texts)]


def _selfcheck() -> None:
    """Same passages as the training data, and the delivered mock-test summaries reproduced word for word."""
    assert cap_for(100) == 25 and cap_for(400) == 60 and cap_for(40) == 20
    assert trim_to_cap("alpha beta, " + "gamma " * 30, 80) == "alpha beta."
    try:
        from consentledger.summ import build_dataset as B
        gold = json.loads((PROJECT_ROOT / "data" / "aa" / "annotated" / "gold.json").read_text(encoding="utf-8"))
        assert all(chunk(d["text"]) == B.chunk(d["text"]) for d in gold)
        assert all(cap_for(n) == B.cap_for(n) for n in range(1000))
        print(f"passage cutter identical to build_dataset on all {len(gold)} documents")
    except (ImportError, FileNotFoundError):
        print("build_dataset.py or gold.json not here: cutter comparison skipped")
    dev_path = PROJECT_ROOT / "data" / "summ" / "dev.jsonl"
    if not dev_path.exists():                     # git-ignored: a fresh clone only loads the models
        for name in ("flant5base", "t5small"):
            tok, model, meta = load(name)
            assert len(summarise(["We collect your bank statements to assess your loan. " * 5], tok, model, meta)[0].split()) >= 3
        return print("data/summ not here: models load and summarise; comparison with the reference summaries skipped")
    dev = [json.loads(l) for l in dev_path.read_text(encoding="utf-8").splitlines()]
    for name in ("flant5base", "t5small"):
        tok, model, meta = load(name)
        got = summarise([r["source"] for r in dev], tok, model, meta)
        sent = PROJECT_ROOT / "artifacts_out" / "summ" / "p2_final" / name / "dev_predictions.jsonl"
        want = {r["id"]: r["summary"] for r in map(json.loads, sent.read_text(encoding="utf-8").splitlines())}
        same = sum(want[r["id"]] == g for r, g in zip(dev, got))
        print(f"{name}: {same} of {len(dev)} mock-test summaries identical to the reference run")
        assert same == len(dev)
    print("selfcheck ok")


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarise a policy text passage by passage.")
    ap.add_argument("--file", type=Path)
    ap.add_argument("--model", default=MODEL, choices=("flant5base", "t5small"))
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    if args.selfcheck:
        return _selfcheck()
    ps = passages(args.file.read_text(encoding="utf-8"))
    for p, s in zip(ps, summarise([p["text"] for p in ps], *load(args.model))):
        print(json.dumps({"start": p["start"], "end": p["end"], "summary": s}, ensure_ascii=False))


if __name__ == "__main__":
    main()
