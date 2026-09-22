"""Evaluate a trained NER model on a CoNLL file with entity-level seqeval metrics.

Reports micro/macro P/R/F1 + a per-label breakdown. With `--out`, also SAVES a structured metrics JSON
(micro/macro + per-label) so `collect.py` can fold AA-test (E1/E2) results into the ablation table.

**TEST SET RULE:** `data/ner_bio/aa_test.conll` (once it exists) is opened EXACTLY ONCE, in Phase 6, with
a frozen model. Do NOT point this at the test set for tuning. Default target is the dev file.

Usage:
    # dev sanity:
    python -m consentledger.ner.evaluate --model-dir artifacts_out/ner/legalbert --conll data/ner_bio/dev.conll
    # AA test (save for collect.py):
    python -m consentledger.ner.evaluate --model-dir artifacts_out/ner/legalbert \\
        --conll data/ner_bio/aa_test.conll --out artifacts_out/ner/legalbert/test_metrics.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from consentledger.ner.dataset import ID2LABEL, build_dataset  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    ap = argparse.ArgumentParser(description="Entity-level NER evaluation.")
    ap.add_argument("--model-dir", required=True, type=Path)
    ap.add_argument("--conll", type=Path, default=PROJECT_ROOT / "data" / "ner_bio" / "dev.conll")
    ap.add_argument("--out", type=Path, help="save a metrics JSON here (e.g. for AA-test / collect.py)")
    ap.add_argument("--max-length", type=int, default=256)
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    tokenizer = AutoTokenizer.from_pretrained(str(args.model_dir), use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(str(args.model_dir))
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    ds = build_dataset(args.conll, tokenizer, args.max_length)
    true_labels, true_preds = [], []
    with torch.no_grad():
        for ex in ds:
            input_ids = torch.tensor([ex["input_ids"]], device=device)
            attn = torch.tensor([ex["attention_mask"]], device=device)
            logits = model(input_ids=input_ids, attention_mask=attn).logits[0]
            pred = logits.argmax(-1).tolist()
            cur_l, cur_p = [], []
            for p_i, l_i in zip(pred, ex["labels"]):
                if l_i == -100:
                    continue
                cur_l.append(ID2LABEL[int(l_i)])
                cur_p.append(ID2LABEL[int(p_i)])
            true_labels.append(cur_l)
            true_preds.append(cur_p)

    print(f"\n=== NER evaluation: {args.conll.name} (model: {args.model_dir.name}) ===")
    print(classification_report(true_labels, true_preds, digits=4, zero_division=0))

    if args.out:
        rep = classification_report(true_labels, true_preds, output_dict=True, zero_division=0)
        per_label = {k: v for k, v in rep.items()
                     if k not in ("micro avg", "macro avg", "weighted avg")}
        from sklearn.metrics import f1_score as sk_f1
        flat_t = [t for seq in true_labels for t in seq]
        flat_p = [t for seq in true_preds for t in seq]
        ent_tags = [lab for lab in ID2LABEL.values() if lab != "O"]
        metrics = {
            "conll_file": str(args.conll),
            "model_dir": str(args.model_dir),
            "micro_f1": f1_score(true_labels, true_preds, zero_division=0),
            "macro_f1": rep.get("macro avg", {}).get("f1-score", 0.0),
            "token_f1": sk_f1(flat_t, flat_p, labels=ent_tags, average="micro", zero_division=0),
            "precision": precision_score(true_labels, true_preds, zero_division=0),
            "recall": recall_score(true_labels, true_preds, zero_division=0),
            "per_label": per_label,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"saved metrics -> {args.out}")


if __name__ == "__main__":
    main()
