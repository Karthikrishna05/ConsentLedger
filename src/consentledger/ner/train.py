"""Fine-tune a token-classification backbone on the OPP-115 BIO data (E1).

Uniform recipe across backbones, NO layer-freezing (D5). Entity-level seqeval metrics; early stopping
on dev. Reads a YAML config (configs/ner_*.yaml). Saves best model + tokenizer + metrics + run_meta.

Usage:
    python -m consentledger.ner.train --config configs/ner_bert_base.yaml
    python -m consentledger.ner.train --config configs/ner_bert_base.yaml --smoke   # fast pipeline check
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import yaml

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from consentledger.ner.dataset import ID2LABEL, LABEL2ID, LABELS, build_dataset  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def make_compute_metrics():
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    def compute(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        true_labels, true_preds = [], []
        for pred, lab in zip(preds, labels):
            cur_l, cur_p = [], []
            for p_i, l_i in zip(pred, lab):
                if l_i == -100:
                    continue
                cur_l.append(ID2LABEL[int(l_i)])
                cur_p.append(ID2LABEL[int(p_i)])
            true_labels.append(cur_l)
            true_preds.append(cur_p)
        rep = classification_report(true_labels, true_preds, output_dict=True, zero_division=0)
        from sklearn.metrics import f1_score as sk_f1
        flat_t = [t for seq in true_labels for t in seq]
        flat_p = [t for seq in true_preds for t in seq]
        ent_tags = [lab for lab in LABELS if lab != "O"]
        return {
            "precision": precision_score(true_labels, true_preds, zero_division=0),
            "recall": recall_score(true_labels, true_preds, zero_division=0),
            "f1": f1_score(true_labels, true_preds, zero_division=0),               # entity micro (best-model)
            "macro_f1": rep.get("macro avg", {}).get("f1-score", 0.0),              # entity macro
            "token_f1": sk_f1(flat_t, flat_p, labels=ent_tags, average="micro", zero_division=0),  # token-level
        }

    return compute


def main() -> None:
    ap = argparse.ArgumentParser(description="Fine-tune a NER backbone on OPP-115 (E1).")
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--epochs", type=int, help="override num_train_epochs")
    ap.add_argument("--smoke", action="store_true", help="1 epoch + capped samples, to validate the pipeline")
    ap.add_argument("--seed", type=int, help="override config seed (for multi-seed runs; suffixes output dir)")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    seed = int(args.seed if args.seed is not None else cfg.get("seed", 42))

    import torch
    from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                              DataCollatorForTokenClassification, EarlyStoppingCallback,
                              Trainer, TrainingArguments)
    from consentledger.seed import set_seed
    set_seed(seed)

    epochs = args.epochs or (1 if args.smoke else int(cfg.get("num_train_epochs", 20)))
    train_limit = 600 if args.smoke else None
    dev_limit = 200 if args.smoke else None
    max_length = int(cfg.get("max_length", 256))
    out_dir = PROJECT_ROOT / cfg["output_dir"]
    if args.seed is not None:
        out_dir = out_dir.parent / f"{out_dir.name}_s{seed}"
    if args.smoke:
        out_dir = out_dir.parent / (out_dir.name + "_smoke")

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"], use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(
        cfg["model_name"], num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID,
    )

    train_ds = build_dataset(PROJECT_ROOT / cfg["train_file"], tokenizer, max_length, train_limit)
    dev_ds = build_dataset(PROJECT_ROOT / cfg["dev_file"], tokenizer, max_length, dev_limit)
    collator = DataCollatorForTokenClassification(tokenizer)

    targs = TrainingArguments(
        output_dir=str(out_dir),
        eval_strategy="epoch",              # transformers >= 4.46 (installed 4.46.3)
        save_strategy="epoch",
        learning_rate=float(cfg.get("learning_rate", 2e-5)),
        num_train_epochs=epochs,
        per_device_train_batch_size=int(cfg.get("per_device_train_batch_size", 16)),
        per_device_eval_batch_size=int(cfg.get("per_device_train_batch_size", 16)),
        weight_decay=float(cfg.get("weight_decay", 0.01)),
        warmup_ratio=float(cfg.get("warmup_ratio", 0.1)),
        load_best_model_at_end=True,
        metric_for_best_model=cfg.get("metric_for_best_model", "eval_f1").replace("eval_", "eval_"),
        greater_is_better=True,
        bf16=torch.cuda.is_available(),
        logging_steps=25,
        save_total_limit=1,
        report_to=[],
        seed=seed,
    )

    callbacks = [EarlyStoppingCallback(early_stopping_patience=int(cfg.get("early_stopping_patience", 3)))]
    trainer = Trainer(
        model=model, args=targs, train_dataset=train_ds, eval_dataset=dev_ds,
        tokenizer=tokenizer, data_collator=collator,
        compute_metrics=make_compute_metrics(), callbacks=callbacks,
    )

    trainer.train()
    metrics = trainer.evaluate()
    out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    (out_dir / "dev_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out_dir / "run_meta.json").write_text(json.dumps({
        "config": cfg, "seed": seed, "epochs": epochs, "smoke": args.smoke,
        "condition": cfg.get("condition", "E1"),
        "git_commit": _git_commit(), "model_name": cfg["model_name"],
    }, indent=2), encoding="utf-8")

    print("\n=== NER train done ===")
    print(f"model      : {cfg['model_name']}  ({'SMOKE' if args.smoke else 'full'}, {epochs} epoch(s), seed {seed})")
    print(f"dev metrics: entity micro-F1 {metrics.get('eval_f1', 0):.4f} | macro-F1 "
          f"{metrics.get('eval_macro_f1', 0):.4f} | token-F1 {metrics.get('eval_token_f1', 0):.4f} | "
          f"P {metrics.get('eval_precision', 0):.4f} | R {metrics.get('eval_recall', 0):.4f}")
    print(f"saved      : {out_dir.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
