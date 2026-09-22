"""Read CoNLL BIO files and turn them into tokenized, label-aligned HF datasets.

Convention (D18): input is **word-level** CoNLL (word <TAB> tag, blank line between segments). Here we
apply a backbone's subword tokenizer and align labels: the **first subword** of each word gets the word's
label id; every other subword and all special tokens get **-100** (ignored by the loss).
"""
from __future__ import annotations

from pathlib import Path

from datasets import Dataset

# The 7-tag scheme for the 3 transferable labels (D1).
LABELS = ["O", "B-DATA_TYPE", "I-DATA_TYPE", "B-PURPOSE", "I-PURPOSE", "B-THIRD_PARTY", "I-THIRD_PARTY"]
LABEL2ID = {t: i for i, t in enumerate(LABELS)}
ID2LABEL = {i: t for t, i in LABEL2ID.items()}


def read_conll(path: str | Path) -> list[dict]:
    """-> [{"tokens": [...], "tags": [...]}] , one entry per segment."""
    sents, toks, tags = [], [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            if toks:
                sents.append({"tokens": toks, "tags": tags})
                toks, tags = [], []
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        toks.append(parts[0])
        tags.append(parts[1])
    if toks:
        sents.append({"tokens": toks, "tags": tags})
    return sents


def build_dataset(path: str | Path, tokenizer, max_length: int = 256, limit: int | None = None) -> Dataset:
    sents = read_conll(path)
    if limit:
        sents = sents[:limit]
    ds = Dataset.from_list(
        [{"tokens": s["tokens"], "ner_tags": [LABEL2ID.get(t, 0) for t in s["tags"]]} for s in sents]
    )

    def tokenize_and_align(batch: dict) -> dict:
        enc = tokenizer(
            batch["tokens"],
            is_split_into_words=True,
            truncation=True,
            max_length=max_length,
        )
        all_labels = []
        for i, tags in enumerate(batch["ner_tags"]):
            word_ids = enc.word_ids(batch_index=i)
            prev = None
            labels = []
            for wid in word_ids:
                if wid is None:
                    labels.append(-100)
                elif wid != prev:
                    labels.append(tags[wid])          # first subword of the word
                else:
                    labels.append(-100)               # continuation subword -> ignored
                prev = wid
            all_labels.append(labels)
        enc["labels"] = all_labels
        return enc

    return ds.map(tokenize_and_align, batched=True, remove_columns=ds.column_names)
