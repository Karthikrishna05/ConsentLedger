"""Load best model; return char-span entities for the pipeline.

Text in, [{"start", "end", "label", "text"}] out. Segmentation and word splitting match the AA training data.
Default model: Legal-BERT E2-sequential seed 44, the best seed on the mock test (dev F1 0.736), chosen without
the test set. Loaded from artifacts_out/ner/<run>, else the private Hub repo (needs HF_TOKEN or `hf auth login`).

    python -m consentledger.ner.predict --file <policy.txt>
    python -m consentledger.ner.predict --selfcheck
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from consentledger.data.aa_to_conll import segment  # noqa: E402
from consentledger.data.bio_tagging import tokenize_with_offsets  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HUB_REPO = "Karthikrishna05/consentledger-ner"
RUN = "legalbert_e2s_s44"
MAX_LENGTH = 256
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")


def load(run: str = RUN):
    """-> (tokenizer, model) on the GPU if there is one."""
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    d = PROJECT_ROOT / "artifacts_out" / "ner" / run
    if not (d / "model.safetensors").exists():
        from huggingface_hub import snapshot_download
        d = Path(snapshot_download(HUB_REPO, allow_patterns=[f"{run}/*"])) / run
        if not (d / "model.safetensors").exists():     # offline, it returns whatever is cached, possibly without this run
            raise RuntimeError(f"{HUB_REPO}/{run} could not be downloaded: check the internet connection and the Hub "
                               "token (HF_TOKEN or `hf auth login`), then try again - finished files are kept.")
    tok =AutoTokenizer.from_pretrained(str(d), use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(str(d), use_safetensors=True).eval()
    return tok, model.to("cuda" if torch.cuda.is_available() else "cpu")


def predict(text: str, tok, model, batch: int = 16) -> list[dict]:
    import torch
    from seqeval.metrics.sequence_labeling import get_entities   # the evaluation's reading of BIO tags

    segs = [(a, tokenize_with_offsets(text[a:b])) for a, b in segment(text, [])]
    segs = [(a, w) for a, w in segs if w]
    out = []
    for i in range(0, len(segs), batch):
        part = segs[i:i + batch]
        enc = tok([[w for w, _, _ in words] for _, words in part], is_split_into_words=True, truncation=True,
                  max_length=MAX_LENGTH, padding=True, return_tensors="pt").to(model.device)
        with torch.no_grad():
            ids = model(**enc).logits.argmax(-1).tolist()
        for k, (a, words) in enumerate(part):
            tags, prev = ["O"] * len(words), None
            for pos, wid in enumerate(enc.word_ids(batch_index=k)):
                if wid is not None and wid != prev:                     # first sub-word piece of a word
                    tags[wid] = model.config.id2label[ids[k][pos]]   # saved with the model; no training code needed
                prev = wid
            for label, s, e in (x for x in get_entities(tags) if x[0] in LABELS):
                start, end = a + words[s][1], a + words[e][2]
                out.append({"start": start, "end": end, "label": label, "text": text[start:end]})
    return out


def _selfcheck() -> None:
    """On the 4 adaptation mock-test documents (never the test set): char-level F1 near the trainer's dev F1."""
    from consentledger.data.aa_to_conll import ADAPT_DEV, GOLD

    tok, model = load()
    if not GOLD.exists():                         # git-ignored: a fresh clone only checks that the model runs
        p = predict("We collect your bank statements and share them with credit bureaus.", tok, model)
        return print(f"gold.json not here: model loads and predicts ({len(p)} highlights on a test sentence)")
    gold = {d["doc_id"]: d for d in json.loads(GOLD.read_text(encoding="utf-8"))}
    tp = n_pred = n_gold = 0
    for doc in ADAPT_DEV:
        g = {(s["start"], s["end"], s["label"]) for s in gold[doc]["spans"]}
        p = {(x["start"], x["end"], x["label"]) for x in predict(gold[doc]["text"], tok, model)}
        assert all(gold[doc]["text"][s:e].strip() for s, e, _ in p)
        tp, n_pred, n_gold = tp + len(g & p), n_pred + len(p), n_gold + len(g)
    f1 = 2 * tp / (n_pred + n_gold)
    print(f"mock-test documents: {n_gold} gold, {n_pred} predicted, exact-match F1 {f1:.3f} (trainer's dev F1 0.736)")
    assert f1 > 0.6, f1
    print("selfcheck ok")


def main() -> None:
    ap = argparse.ArgumentParser(description="Highlight data types, purposes and third parties in a policy text.")
    ap.add_argument("--file", type=Path)
    ap.add_argument("--run", default=RUN)
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    if args.selfcheck:
        return _selfcheck()
    tok, model = load(args.run)
    print(json.dumps(predict(args.file.read_text(encoding="utf-8"), tok, model), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
