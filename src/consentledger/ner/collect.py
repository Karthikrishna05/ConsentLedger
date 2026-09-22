"""Collect NER metrics into results/ner/ (committed) — citable numbers, WITHOUT the weights.

Scans each artifacts_out/ner/<run>/ (including multi-seed dirs like `inlegalbert_s42`, `..._s43`) for
dev_metrics.json (+ optional test_metrics.json from `evaluate.py --out` on the AA test set), copies the
small files into results/ner/<run>/, and writes:
  - results/ner/ablation_runs.csv   : one row per run (per backbone × condition × seed)
  - results/ner/ablation.csv/.md    : AGGREGATED by (backbone, condition) with mean ± std across seeds

Columns cover entity macro-F1, token-F1, and (once present) AA-test macro/micro-F1, tagged E1/E2.
The big weights stay out of git and go to the HF Hub (D23).

Usage:
    python -m consentledger.ner.collect
"""
from __future__ import annotations

import csv
import json
import shutil
import statistics as st
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ART = PROJECT_ROOT / "artifacts_out" / "ner"
OUT = PROJECT_ROOT / "results" / "ner"


def _get(d: dict, *keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _agg(vals: list) -> tuple[float | None, float]:
    nums = [v for v in vals if isinstance(v, (int, float))]
    if not nums:
        return None, 0.0
    return sum(nums) / len(nums), (st.stdev(nums) if len(nums) > 1 else 0.0)


def _cell(mean, std) -> str:
    return "-" if mean is None else (f"{mean:.4f}±{std:.4f}" if std else f"{mean:.4f}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = []
    for d in sorted(ART.glob("*")):
        if not d.is_dir() or d.name.endswith("_smoke") or not (d / "dev_metrics.json").exists():
            continue
        dev = json.loads((d / "dev_metrics.json").read_text(encoding="utf-8"))
        meta = json.loads((d / "run_meta.json").read_text(encoding="utf-8")) if (d / "run_meta.json").exists() else {}
        test = json.loads((d / "test_metrics.json").read_text(encoding="utf-8")) if (d / "test_metrics.json").exists() else {}
        (OUT / d.name).mkdir(parents=True, exist_ok=True)
        for fn in ("dev_metrics.json", "run_meta.json", "test_metrics.json"):
            if (d / fn).exists():
                shutil.copy(d / fn, OUT / d.name / fn)
        runs.append({
            "run": d.name,
            "model_name": meta.get("model_name", d.name),
            "condition": meta.get("condition", "E1"),
            "seed": meta.get("seed", ""),
            "dev_macro_f1": _get(dev, "eval_macro_f1"),
            "dev_micro_f1": _get(dev, "eval_f1"),
            "dev_token_f1": _get(dev, "eval_token_f1"),
            "test_macro_f1": _get(test, "macro_f1"),
            "test_micro_f1": _get(test, "micro_f1"),
            "test_token_f1": _get(test, "token_f1"),
            "git_commit": meta.get("git_commit", ""),
        })
    if not runs:
        raise SystemExit(f"No trained runs with dev_metrics.json under {ART}. Train first.")

    # per-run detail
    run_cols = ["run", "model_name", "condition", "seed", "dev_macro_f1", "dev_micro_f1", "dev_token_f1",
                "test_macro_f1", "test_micro_f1", "test_token_f1", "git_commit"]
    with (OUT / "ablation_runs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=run_cols)
        w.writeheader()
        w.writerows(runs)

    # aggregate by (backbone, condition) across seeds
    groups: dict[tuple, list] = defaultdict(list)
    for r in runs:
        groups[(r["model_name"], r["condition"])].append(r)

    agg = []
    for (model, cond), rs in sorted(groups.items()):
        row = {"model_name": model, "condition": cond, "n_seeds": len(rs)}
        for key in ("dev_macro_f1", "dev_token_f1", "test_macro_f1", "test_micro_f1", "test_token_f1"):
            m, s = _agg([r[key] for r in rs])
            row[f"{key}_mean"], row[f"{key}_std"] = m, s
        agg.append(row)

    agg_cols = ["model_name", "condition", "n_seeds",
                "dev_macro_f1_mean", "dev_macro_f1_std", "dev_token_f1_mean", "dev_token_f1_std",
                "test_macro_f1_mean", "test_macro_f1_std", "test_micro_f1_mean", "test_token_f1_mean"]
    with (OUT / "ablation.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=agg_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(agg)

    md = ["# NER ablation (mean ± std over seeds) — E1 transfer / E2 domain-adapted", "",
          "| backbone | cond | seeds | dev entity-macroF1 | dev token-F1 | AA-test macroF1 | AA-test token-F1 |",
          "|---|---|---|---|---|---|---|"]
    for row in sorted(agg, key=lambda x: -(x["test_macro_f1_mean"] or x["dev_macro_f1_mean"] or 0)):
        md.append(f"| {row['model_name']} | {row['condition']} | {row['n_seeds']} | "
                  f"{_cell(row['dev_macro_f1_mean'], row['dev_macro_f1_std'])} | "
                  f"{_cell(row['dev_token_f1_mean'], row['dev_token_f1_std'])} | "
                  f"{_cell(row['test_macro_f1_mean'], row['test_macro_f1_std'])} | "
                  f"{_cell(row['test_token_f1_mean'], 0)} |")
    md += ["", "_dev = OPP-115 dev. AA-test columns are '-' until `evaluate.py --out` is run on the "
           "annotated AA test set. Entity-macroF1 = strict exact-match; token-F1 = token-level (fairer "
           "for long spans)._"]
    (OUT / "ablation.md").write_text("\n".join(md), encoding="utf-8")

    print("=== collected NER metrics -> results/ner/ ===")
    for row in sorted(agg, key=lambda x: -(x["dev_macro_f1_mean"] or 0)):
        print(f"  {row['model_name']:40} [{row['condition']}] x{row['n_seeds']} seed(s)  "
              f"dev entity-macro {_cell(row['dev_macro_f1_mean'], row['dev_macro_f1_std'])} | "
              f"dev token {_cell(row['dev_token_f1_mean'], row['dev_token_f1_std'])} | "
              f"AA-test {_cell(row['test_macro_f1_mean'], row['test_macro_f1_std'])}")

    # missing-seed guard: warn if any (backbone, condition) has fewer than the most-seeded group.
    expected = max((row["n_seeds"] for row in agg), default=0)
    short = [row for row in agg if row["n_seeds"] < expected]
    if short:
        print(f"\n!! WARNING: expected {expected} seed(s) per group; these have fewer "
              f"(a run crashed or didn't write dev_metrics.json):")
        for row in short:
            print(f"   - {row['model_name']} [{row['condition']}]: only {row['n_seeds']} seed(s)")
        print("   mean±std for those groups is computed over the seeds present.")

    print(f"wrote {(OUT / 'ablation.csv').relative_to(PROJECT_ROOT)} + ablation.md + ablation_runs.csv")


if __name__ == "__main__":
    main()
