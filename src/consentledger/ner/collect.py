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


def aa_test_report(n_boot: int = 5000, seed: int = 0) -> None:
    """E1 / E2 on the AA test set -> results/ner/aa_test.md + .json (numbers only).

    Per backbone and condition: mean over seeds, with a 95% interval from a bootstrap over document groups; then
    the paired differences between conditions (evaluate.compare). Nothing here reads the test set - only the
    test_metrics.json files that `evaluate.py --open-test` wrote."""
    import numpy as np
    from consentledger.ner.evaluate import KEYS, LABELS, bootstrap, compare, resamples

    runs = defaultdict(list)                                     # (backbone, condition) -> [(file, metrics)]
    for f in sorted(ART.glob("*/test_metrics.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        meta = json.loads((f.parent / "run_meta.json").read_text(encoding="utf-8"))
        runs[(meta["model_name"], m["condition"])].append((f, m))
    if not runs:
        return
    conds = sorted({c for _, c in runs})
    backbones = sorted({b for b, _ in runs})
    pooled = {c: [x for (b, cc), v in runs.items() if cc == c for x in v] for c in conds}
    first = next(iter(runs.values()))[0][1]

    def row(items):
        ms = [m for _, m in items]
        idx = resamples(len(ms[0]["counts"]["groups"]), n_boot, seed)
        bs = [bootstrap(np.array(m["counts"]["exact"]), np.array(m["counts"]["relaxed"]), idx) for m in ms]
        val = {"micro_f1": [m["micro_f1"] for m in ms], "macro_f1": [m["macro_f1"] for m in ms],
               "relaxed_micro_f1": [m["relaxed"]["micro_f1"] for m in ms],
               "relaxed_macro_f1": [m["relaxed"]["macro_f1"] for m in ms]}
        out = {"runs": len(ms)}
        for k in KEYS:
            b = np.mean([x[k] for x in bs], 0)
            out[k] = {"mean": float(np.mean(val[k])), "std": float(np.std(val[k], ddof=1)) if len(ms) > 1 else 0.0,
                      "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]}
        out["group_mean_micro_f1"] = float(np.mean([m["group_mean_micro_f1"] for m in ms]))
        out["micro_f1_without_definition_mismatch"] = float(
            np.mean([m["errors"]["micro_f1_without_definition_mismatch"] for m in ms]))
        out["per_label"] = {lab: {"exact_f1": float(np.mean([m["per_label"].get(lab, {}).get("f1-score", 0.0) for m in ms])),
                                  "relaxed_f1": float(np.mean([m["relaxed"]["per_label"][lab]["f1"] for m in ms]))}
                            for lab in LABELS}
        out["per_group_micro_f1"] = {g: float(np.mean([m["per_group"][g]["micro_f1"] for m in ms])) for g in ms[0]["per_group"]}
        out["errors"] = {k: float(np.mean([m["errors"][k] for m in ms])) for k in ms[0]["errors"]}
        out["entities_predicted"] = float(np.mean([m["entities_predicted"] for m in ms]))
        return out

    rep = {"conll_file": first["conll_file"], "entities_gold": first["entities_gold"],
           "bootstrap": {"unit": "document group", "resamples": n_boot, "seed": seed},
           "by_backbone": {b: {c: row(runs[(b, c)]) for c in conds if (b, c) in runs} for b in backbones},
           "pooled": {c: row(pooled[c]) for c in conds}, "differences": {}}
    for a, b in (("E2-sequential", "E1"), ("E2-joint", "E1"), ("E2-sequential", "E2-joint")):
        if a not in conds or b not in conds:
            continue
        d = {"all three": compare([f for f, _ in pooled[a]], [f for f, _ in pooled[b]], n_boot, seed)}
        for bb in backbones:
            if (bb, a) in runs and (bb, b) in runs:
                d[bb] = compare([f for f, _ in runs[(bb, a)]], [f for f, _ in runs[(bb, b)]], n_boot, seed)
        rep["differences"][f"{a} minus {b}"] = {k: {m: v[m] for m in KEYS} for k, v in d.items()}
    # LLM baseline (D64): one run per model and number of examples, compared with each fine-tuned condition and
    # with the best fine-tuned backbone. Their metrics hold numbers only and are copied next to the others.
    llm = {f.parts[-3]: (f, json.loads(f.read_text(encoding="utf-8")))
           for f in sorted((ART.parent / "llm").glob("*/test/metrics.json"))}
    rep["llm"], rep["llm_differences"] = {}, {}
    for name, (f, m) in llm.items():
        (OUT / f"llm_{name}").mkdir(exist_ok=True)
        shutil.copy(f, OUT / f"llm_{name}" / "test_metrics.json")
        rep["llm"][name] = {**row([(f, m)]), "precision": m["precision"], "recall": m["recall"],
                            "phrases_returned": m["phrases_returned"], "phrases_not_in_passage": m["phrases_not_in_passage"]}
        best = max(((b, c) for (b, c) in runs if c == "E2-sequential"),
                   key=lambda k: np.mean([x["micro_f1"] for _, x in runs[k]]), default=None)
        others = {c: pooled[c] for c in conds}
        if best:
            others[f"E2-sequential, {best[0]} only"] = runs[best]
        rep["llm_differences"][name] = {
            c: {k: v for k, v in compare([f], [g for g, _ in items], n_boot, seed).items() if k in KEYS}
            for c, items in others.items()}
    (OUT / "aa_test.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")

    def cell(r, k):
        return f"{r[k]['mean']:.3f} ± {r[k]['std']:.3f} [{r[k]['ci95'][0]:.3f}, {r[k]['ci95'][1]:.3f}]"

    md = ["# E1 / E2 on the AA test set", "",
          f"{rep['entities_gold']} gold entities, 9 documents in 8 groups. Cells: mean ± std over seeds, then the 95% "
          f"interval from a bootstrap over document groups ({n_boot} resamples). Exact = same label and same "
          "boundaries; relaxed = same label, overlapping.", "",
          "| backbone | condition | runs | exact micro-F1 | exact macro-F1 | relaxed micro-F1 | mean of group F1 "
          "| exact, definition mismatch set aside |", "|---|---|---|---|---|---|---|---|"]
    for name, table in [(b, rep["by_backbone"][b]) for b in backbones] + [("all three", rep["pooled"])]:
        for c in conds:
            if c in table:
                r = table[c]
                md.append(f"| {name} | {c} | {r['runs']} | {cell(r, 'micro_f1')} | {cell(r, 'macro_f1')} | "
                          f"{cell(r, 'relaxed_micro_f1')} | {r['group_mean_micro_f1']:.3f} | "
                          f"{r['micro_f1_without_definition_mismatch']:.3f} |")
    md += ["", "## Paired differences (the same resamples of the groups for both sides)", "",
           "| comparison | backbone | exact micro-F1 difference [95% CI] | relaxed micro-F1 difference [95% CI] | verdict (exact) |",
           "|---|---|---|---|---|"]
    for name, d in rep["differences"].items():
        for bb, v in d.items():
            e, r = v["micro_f1"], v["relaxed_micro_f1"]
            verdict = "difference" if e["ci95"][0] > 0 or e["ci95"][1] < 0 else "no significant difference"
            md.append(f"| {name} | {bb} | {e['delta']:+.3f} [{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}] | "
                      f"{r['delta']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] | {verdict} |")
    md += ["", "## Per label, all three backbones (exact F1 / relaxed F1)", "",
           "| condition | " + " | ".join(LABELS) + " |", "|---|" + "---|" * len(LABELS)]
    for c in conds:
        pl = rep["pooled"][c]["per_label"]
        md.append(f"| {c} | " + " | ".join(f"{pl[lab]['exact_f1']:.3f} / {pl[lab]['relaxed_f1']:.3f}" for lab in LABELS) + " |")
    md += ["", "## Per document group, all three backbones (exact micro-F1)", "",
           "| group | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
    for g in rep["pooled"][conds[0]]["per_group_micro_f1"]:
        md.append(f"| {g} | " + " | ".join(f"{rep['pooled'][c]['per_group_micro_f1'][g]:.3f}" for c in conds) + " |")
    md += ["", "## What the predictions were, per run on average (all three backbones)", "",
           "| condition | predicted | exact | right label, wrong boundary | wrong label | spurious | of which definition "
           "mismatch | gold missed entirely |", "|---|---|---|---|---|---|---|---|"]
    for c in conds:
        r, e = rep["pooled"][c], rep["pooled"][c]["errors"]
        md.append(f"| {c} | {r['entities_predicted']:.0f} | {e['pred_exact']:.0f} | {e['pred_boundary']:.0f} | "
                  f"{e['pred_wrong_label']:.0f} | {e['pred_spurious']:.0f} | {e['definition_mismatch']:.0f} | {e['gold_missed']:.0f} |")
    if rep["llm"]:
        md += ["", "## LLM baseline (D64): a chat model given the labelling rules, no training", "",
               "One run each (temperature 0). The interval is the same bootstrap over document groups.", "",
               "| model and examples | exact micro-F1 | exact macro-F1 | relaxed micro-F1 | precision | recall | predicted "
               "| returned phrases not in the passage | mean of group F1 |", "|---|---|---|---|---|---|---|---|---|"]
        for name, r in rep["llm"].items():
            ci = lambda k: f"{r[k]['mean']:.3f} [{r[k]['ci95'][0]:.3f}, {r[k]['ci95'][1]:.3f}]"
            md.append(f"| {name} | {ci('micro_f1')} | {ci('macro_f1')} | {ci('relaxed_micro_f1')} | {r['precision']:.3f} | "
                      f"{r['recall']:.3f} | {r['entities_predicted']:.0f} | {r['phrases_not_in_passage']} of "
                      f"{r['phrases_returned']} | {r['group_mean_micro_f1']:.3f} |")
        md += ["", "### LLM minus fine-tuned (paired; exact micro-F1 difference, then relaxed)", "",
               "| LLM run | against | exact difference [95% CI] | relaxed difference [95% CI] | verdict (exact) |", "|---|---|---|---|---|"]
        for name, d in rep["llm_differences"].items():
            for c, v in d.items():
                e, r = v["micro_f1"], v["relaxed_micro_f1"]
                verdict = ("LLM better" if e["ci95"][0] > 0 else "fine-tuned better" if e["ci95"][1] < 0
                           else "no significant difference")
                md.append(f"| {name} | {c} | {e['delta']:+.3f} [{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}] | "
                          f"{r['delta']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] | {verdict} |")
        md += ["", "### LLM per label (exact F1 / relaxed F1)", "", "| run | " + " | ".join(LABELS) + " |", "|---|" + "---|" * len(LABELS)]
        for name, r in rep["llm"].items():
            md.append(f"| {name} | " + " | ".join(f"{r['per_label'][lab]['exact_f1']:.3f} / {r['per_label'][lab]['relaxed_f1']:.3f}" for lab in LABELS) + " |")
        md += ["", "### LLM per document group (exact micro-F1)", "", "| group | " + " | ".join(rep["llm"]) + " |", "|---|" + "---|" * len(rep["llm"])]
        for g in next(iter(rep["llm"].values()))["per_group_micro_f1"]:
            md.append(f"| {g} | " + " | ".join(f"{r['per_group_micro_f1'][g]:.3f}" for r in rep["llm"].values()) + " |")
    (OUT / "aa_test.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {(OUT / 'aa_test.md').relative_to(PROJECT_ROOT)} + aa_test.json")


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
    md += ["", "_dev = each run's own dev file: OPP-115 dev for E1, the AA dev documents for E2 - NOT comparable "
           "across conditions. AA-test columns are '-' until `evaluate.py --out` is run on the "
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
    aa_test_report()


if __name__ == "__main__":
    main()
