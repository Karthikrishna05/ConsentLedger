"""Entity-level NER evaluation, and the E1-vs-E2 comparison on the AA test set.

One model on one CoNLL file:
    python -m consentledger.ner.evaluate --model-dir artifacts_out/ner/legalbert_s42 --conll data/ner_bio/dev.conll
    python -m consentledger.ner.evaluate --model-dir artifacts_out/ner/legalbert_s42 --open-test      # the AA test set

Two conditions against each other (any number of seeds per side; paired over the same resamples):
    python -m consentledger.ner.evaluate --compare artifacts_out/ner/legalbert_e2_s*/test_metrics.json \\
                                         --against artifacts_out/ner/legalbert_s*/test_metrics.json

Reports exact and relaxed (overlap) F1, 95% CIs by bootstrap over document groups (segments of one
document are not independent), per-group F1, an error breakdown and a truncation check.
The AA test set is opened only with --open-test; each opening is logged to results/ner/test_openings.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from consentledger.data.adjudicate import AA_ROLES, NAMED_AA, STOPLIST, TELEMETRY  # noqa: E402
from consentledger.ner.dataset import ID2LABEL, build_dataset, read_conll  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
NER_BIO = PROJECT_ROOT / "data" / "ner_bio"
SPLIT = PROJECT_ROOT / "data" / "splits" / "aa_split.json"
LABELS = ("DATA_TYPE", "PURPOSE", "THIRD_PARTY")
CORPORATE = re.compile(r"merger|acquisition|reorgani[sz]ation|restructuring|sale of (?:assets|business)|bankruptcy")
_DET = re.compile(r"^(?:(?:the|your|any|our|such|a|an|all|other|certain|its|their|his|her|relevant)\s+)+")
KEYS = ("micro_f1", "macro_f1", "relaxed_micro_f1", "relaxed_macro_f1")
SPURIOUS = ("telemetry", "aa_role", "umbrella_term", "corporate_transaction", "other")
ERR_KEYS = (["pred_exact", "pred_boundary", "pred_wrong_label", "pred_spurious"] + [f"spurious_{k}" for k in SPURIOUS]
            + ["gold_exact", "gold_boundary", "gold_wrong_label", "gold_missed"])


def entities(tags: list[str]) -> list[tuple[str, int, int]]:
    from seqeval.metrics.sequence_labeling import get_entities
    return [e for e in get_entities(tags) if e[0] in LABELS]


def _overlap(a, b) -> bool:
    return a[1] <= b[2] and b[1] <= a[2]


def segment_counts(gold: list[str], pred: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """-> exact (L,3) = tp, n_pred, n_gold ; relaxed (L,4) = pred_hit, n_pred, gold_hit, n_gold."""
    g, p = entities(gold), entities(pred)
    ex, rel = np.zeros((len(LABELS), 3), int), np.zeros((len(LABELS), 4), int)
    for k, lab in enumerate(LABELS):
        gl, pl = [e for e in g if e[0] == lab], [e for e in p if e[0] == lab]
        ex[k] = len(set(gl) & set(pl)), len(pl), len(gl)
        rel[k] = (sum(any(_overlap(x, y) for y in gl) for x in pl), len(pl),
                  sum(any(_overlap(x, y) for y in pl) for x in gl), len(gl))
    return ex, rel


def _f1(hit_p, n_p, hit_g, n_g):
    p = np.divide(hit_p, n_p, out=np.zeros(np.shape(hit_p), float), where=np.asarray(n_p) > 0)
    r = np.divide(hit_g, n_g, out=np.zeros(np.shape(hit_g), float), where=np.asarray(n_g) > 0)
    return p, r, np.divide(2 * p * r, p + r, out=np.zeros(np.shape(p), float), where=(p + r) > 0)


def scores(ex: np.ndarray, rel: np.ndarray) -> dict[str, np.ndarray]:
    """ex (..., L, 3), rel (..., L, 4) -> the four headline F1s, vectorised over the leading axes."""
    e, r = ex.sum(-2), rel.sum(-2)
    return {"micro_f1": _f1(e[..., 0], e[..., 1], e[..., 0], e[..., 2])[2],
            "macro_f1": _f1(ex[..., 0], ex[..., 1], ex[..., 0], ex[..., 2])[2].mean(-1),
            "relaxed_micro_f1": _f1(r[..., 0], r[..., 1], r[..., 2], r[..., 3])[2],
            "relaxed_macro_f1": _f1(rel[..., 0], rel[..., 1], rel[..., 2], rel[..., 3])[2].mean(-1)}


def resamples(n_groups: int, n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n_groups, size=(n, n_groups))


def bootstrap(ex: np.ndarray, rel: np.ndarray, idx: np.ndarray) -> dict[str, np.ndarray]:
    """ex (G, L, 3), rel (G, L, 4), idx (B, G) -> each score for every resample of the groups."""
    return scores(ex[idx].sum(1), rel[idx].sum(1))


def _phrase(tokens: list[str], e) -> str:
    t = " ".join(tokens[e[1]:e[2] + 1]).lower()
    return re.sub(r"\s*([-/'’])\s*", r"\1", t)


def error_breakdown(tokens: list[list[str]], gold: list[list[str]], pred: list[list[str]]):
    """-> (counts, [(category, label, phrase)] for the spurious predictions)."""
    c, spurious = Counter(), []
    for tok, gt, pt in zip(tokens, gold, pred):
        g, p = entities(gt), entities(pt)
        for x in p:
            if x in g:
                c["pred_exact"] += 1
            elif any(y[0] == x[0] and _overlap(x, y) for y in g):
                c["pred_boundary"] += 1
            elif any(_overlap(x, y) for y in g):
                c["pred_wrong_label"] += 1
            else:
                ph = _phrase(tok, x)
                core = _DET.sub("", ph)                       # "your financial information" -> the stop-listed term
                kind = ("telemetry" if TELEMETRY.search(ph) else
                        "aa_role" if {ph, core, core.rstrip("s")} & AA_ROLES or NAMED_AA.search(ph) else
                        "umbrella_term" if {ph, core} & STOPLIST else
                        "corporate_transaction" if CORPORATE.search(ph) else "other")
                c["pred_spurious"] += 1
                c[f"spurious_{kind}"] += 1
                spurious.append((kind, x[0], ph))
        for y in g:
            c["gold_exact" if y in p else "gold_boundary" if any(x[0] == y[0] and _overlap(x, y) for x in p)
              else "gold_wrong_label" if any(_overlap(x, y) for x in p) else "gold_missed"] += 1
    return c, spurious


def group_ids(conll: Path, n_segments: int, by: str) -> list[str]:
    dm = conll.with_name(conll.stem + ".docmap.json")
    if not dm.exists():
        return ["all"] * n_segments
    docs = json.loads(dm.read_text(encoding="utf-8"))
    assert len(docs) == n_segments, (len(docs), n_segments)
    if by == "doc":
        return docs
    grp = {d: "+".join(g) for g in json.loads(SPLIT.read_text(encoding="utf-8"))["groups"] for d in g}
    return [grp[d] for d in docs]


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def predict(model_dir: Path, conll: Path, max_length: int):
    """-> (tokens, gold tags, predicted tags, number of truncated segments), all word-level."""
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(str(model_dir)).eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    segs = read_conll(conll)
    ds = build_dataset(conll, tokenizer, max_length)
    preds, truncated = [], 0
    with torch.no_grad():
        for ex, seg in zip(ds, segs):
            logits = model(input_ids=torch.tensor([ex["input_ids"]], device=device),
                           attention_mask=torch.tensor([ex["attention_mask"]], device=device)).logits[0]
            p = [ID2LABEL[int(p_i)] for p_i, l_i in zip(logits.argmax(-1).tolist(), ex["labels"]) if l_i != -100]
            truncated += len(p) < len(seg["tokens"])
            preds.append(p + ["O"] * (len(seg["tokens"]) - len(p)))     # a cut-off tail counts as missed, not dropped
    return [s["tokens"] for s in segs], [s["tags"] for s in segs], preds, truncated


def evaluate(tokens, gold, pred, groups: list[str], n_boot: int, seed: int) -> dict:
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
    from sklearn.metrics import f1_score as sk_f1

    gids = sorted(set(groups))
    ex, rel = np.zeros((len(gids), len(LABELS), 3), int), np.zeros((len(gids), len(LABELS), 4), int)
    for g, gt, pt in zip(groups, gold, pred):
        e, r = segment_counts(gt, pt)
        ex[gids.index(g)] += e
        rel[gids.index(g)] += r
    point = {k: float(v) for k, v in scores(ex.sum(0), rel.sum(0)).items()}
    micro = f1_score(gold, pred, zero_division=0)
    assert abs(micro - point["micro_f1"]) < 1e-9, (micro, point["micro_f1"])      # our counts == seqeval's

    rep = classification_report(gold, pred, output_dict=True, zero_division=0)
    tot, rtot = ex.sum(0), rel.sum(0)
    rp, rr, rf = _f1(rtot[:, 0], rtot[:, 1], rtot[:, 2], rtot[:, 3])
    per_group = scores(ex, rel)
    err, _ = error_breakdown(tokens, gold, pred)
    mismatch = sum(err[f"spurious_{k}"] for k in ("telemetry", "aa_role", "umbrella_term"))
    n_pred, n_gold, tp = int(tot[:, 1].sum()), int(tot[:, 2].sum()), int(tot[:, 0].sum())
    adj_p = tp / max(1, n_pred - mismatch)
    out = {
        "segments": len(gold), "entities_gold": n_gold, "entities_predicted": n_pred,
        "micro_f1": micro, "macro_f1": rep.get("macro avg", {}).get("f1-score", 0.0),
        "token_f1": sk_f1([t for s in gold for t in s], [t for s in pred for t in s],
                          labels=[t for t in ID2LABEL.values() if t != "O"], average="micro", zero_division=0),
        "precision": precision_score(gold, pred, zero_division=0), "recall": recall_score(gold, pred, zero_division=0),
        "per_label": {k: {m: float(x) for m, x in v.items()} for k, v in rep.items()      # plain floats: JSON-safe
                      if k not in ("micro avg", "macro avg", "weighted avg")},
        "relaxed": {"micro_f1": point["relaxed_micro_f1"], "macro_f1": point["relaxed_macro_f1"],
                    "per_label": {lab: {"precision": float(rp[k]), "recall": float(rr[k]), "f1": float(rf[k])}
                                  for k, lab in enumerate(LABELS)}},
        "group_mean_micro_f1": float(per_group["micro_f1"].mean()),
        "per_group": {g: {"micro_f1": float(per_group["micro_f1"][i]), "relaxed_micro_f1": float(per_group["relaxed_micro_f1"][i]),
                          "entities_gold": int(ex[i, :, 2].sum())} for i, g in enumerate(gids)},
        "errors": {**{k: int(err[k]) for k in ERR_KEYS},
                   "definition_mismatch": int(mismatch),
                   "micro_f1_without_definition_mismatch": 2 * adj_p * (tp / max(1, n_gold)) / max(1e-12, adj_p + tp / max(1, n_gold))},
        "counts": {"groups": gids, "labels": list(LABELS), "exact": ex.tolist(), "relaxed": rel.tolist()},
    }
    if len(gids) >= 3:                                   # fewer groups than that and a group bootstrap says nothing
        b = bootstrap(ex, rel, resamples(len(gids), n_boot, seed))
        out["ci95"] = {k: [float(np.percentile(b[k], 2.5)), float(np.percentile(b[k], 97.5))] for k in KEYS}
        out["bootstrap"] = {"n_groups": len(gids), "resamples": n_boot, "seed": seed}
    return out


def compare(files_a: list[Path], files_b: list[Path], n_boot: int, seed: int) -> dict:
    """A minus B, each side averaged over its seeds, on the same resamples of the document groups (paired)."""
    def load(files):
        runs = [json.loads(Path(f).read_text(encoding="utf-8")) for f in files]
        assert len({(tuple(r["counts"]["groups"]), r["conll_file"]) for r in runs}) == 1, "runs are on different data"
        return runs, [(np.array(r["counts"]["exact"]), np.array(r["counts"]["relaxed"])) for r in runs]
    ra, ca = load(files_a)
    rb, cb = load(files_b)
    assert ra[0]["counts"]["groups"] == rb[0]["counts"]["groups"] and ra[0]["conll_file"] == rb[0]["conll_file"]
    idx = resamples(len(ra[0]["counts"]["groups"]), n_boot, seed)
    out = {"a": [str(f) for f in files_a], "b": [str(f) for f in files_b], "conll_file": ra[0]["conll_file"],
           "bootstrap": {"n_groups": idx.shape[1], "resamples": n_boot, "seed": seed}}
    for k in KEYS:
        pa = np.mean([scores(e.sum(0), r.sum(0))[k] for e, r in ca])
        pb = np.mean([scores(e.sum(0), r.sum(0))[k] for e, r in cb])
        d = np.mean([bootstrap(e, r, idx)[k] for e, r in ca], 0) - np.mean([bootstrap(e, r, idx)[k] for e, r in cb], 0)
        out[k] = {"a": float(pa), "b": float(pb), "delta": float(pa - pb),
                  "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
                  "share_of_resamples_a_better": float((d > 0).mean())}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Entity-level NER evaluation and E1-vs-E2 comparison.")
    ap.add_argument("--model-dir", type=Path)
    ap.add_argument("--conll", type=Path, default=NER_BIO / "dev.conll")
    ap.add_argument("--open-test", action="store_true", help="evaluate on the sealed AA test set (logged)")
    ap.add_argument("--out", type=Path, help="metrics JSON (default for the test set: <model-dir>/test_metrics.json)")
    ap.add_argument("--errors", type=Path, help="write the spurious predictions here (contains policy text - keep out of git)")
    ap.add_argument("--group-by", choices=("group", "doc"), default="group", help="bootstrap unit when a docmap exists")
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--compare", type=Path, nargs="+", help="metrics JSONs of condition A (e.g. E2 seeds)")
    ap.add_argument("--against", type=Path, nargs="+", help="metrics JSONs of condition B (e.g. E1 seeds)")
    args = ap.parse_args()

    if args.compare:
        res = compare(args.compare, args.against, args.bootstrap, args.seed)
        print(f"\n=== A ({len(res['a'])} run(s)) minus B ({len(res['b'])} run(s)) on {Path(res['conll_file']).name}; "
              f"paired bootstrap over {res['bootstrap']['n_groups']} groups ===")
        for k in KEYS:
            r = res[k]
            verdict = "difference" if r["ci95"][0] > 0 or r["ci95"][1] < 0 else "no significant difference"
            print(f"  {k:18} A {r['a']:.4f}  B {r['b']:.4f}  delta {r['delta']:+.4f}  95% CI [{r['ci95'][0]:+.4f}, "
                  f"{r['ci95'][1]:+.4f}]  A better in {100 * r['share_of_resamples_a_better']:.0f}% of resamples -> {verdict}")
        if args.out:
            args.out.write_text(json.dumps(res, indent=2, default=lambda o: o.item()), encoding="utf-8")
        return

    assert args.model_dir, "--model-dir is required"
    if args.open_test:
        args.conll = NER_BIO / "aa_test.conll"
        args.out = args.out or args.model_dir / "test_metrics.json"
    elif args.conll.resolve() == (NER_BIO / "aa_test.conll").resolve():
        raise SystemExit("aa_test.conll is the sealed test set: frozen models only, and pass --open-test.")

    tokens, gold, pred, truncated = predict(args.model_dir, args.conll, args.max_length)
    groups = group_ids(args.conll, len(gold), args.group_by)
    assert not (truncated and len(set(groups)) > 1), f"{truncated} AA segments exceed --max-length: re-run aa_to_conll"
    res = evaluate(tokens, gold, pred, groups, args.bootstrap, args.seed)
    meta_p = args.model_dir / "run_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    res = {"conll_file": str(args.conll), "model_dir": str(args.model_dir), "condition": meta.get("condition", "E1"),
           "seed": meta.get("seed"), "truncated_segments": int(truncated),
           "bootstrap_unit": "document group" if args.group_by == "group" else "document", **res}

    print(f"\n=== {args.conll.name} | {args.model_dir.name} [{res['condition']}] | {res['segments']} segments, "
          f"{res['entities_gold']} gold entities, {truncated} truncated ===")
    ci = res.get("ci95", {})
    for k in KEYS:
        v = res[k] if k in res else res["relaxed"][k.replace("relaxed_", "")]
        print(f"  {k:18} {v:.4f}" + (f"   95% CI [{ci[k][0]:.4f}, {ci[k][1]:.4f}]" if ci else ""))
    print(f"  mean of per-group micro-F1 {res['group_mean_micro_f1']:.4f}  (each of {len(res['per_group'])} group(s) counted once)")
    print("  per label (exact | relaxed F1): " + "; ".join(
        f"{lab} {res['per_label'].get(lab, {}).get('f1-score', 0):.3f} | {res['relaxed']['per_label'][lab]['f1']:.3f}" for lab in LABELS))
    e = res["errors"]
    print(f"  predictions: {e.get('pred_exact', 0)} exact, {e.get('pred_boundary', 0)} right label / wrong boundary, "
          f"{e.get('pred_wrong_label', 0)} wrong label, {e.get('pred_spurious', 0)} spurious")
    print("  spurious by kind: " + ", ".join(f"{k[9:]} {v}" for k, v in e.items() if k.startswith("spurious_"))
          + f"  -> {e['definition_mismatch']} are entities under OPP-115's definition, not ours")
    print(f"  gold: {e.get('gold_exact', 0)} found exactly, {e.get('gold_boundary', 0)} found with another boundary, "
          f"{e.get('gold_wrong_label', 0)} under another label, {e.get('gold_missed', 0)} missed")
    if not ci:
        print("  (no confidence interval: fewer than 3 groups - pass --group-by doc, or this file has no docmap)")

    if args.errors:
        _, spurious = error_breakdown(tokens, gold, pred)
        args.errors.write_text("kind\tlabel\tcount\tphrase\n" + "\n".join(
            f"{k}\t{lab}\t{n}\t{ph}" for (k, lab, ph), n in Counter(spurious).most_common()), encoding="utf-8")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(res, indent=2, default=lambda o: o.item()), encoding="utf-8")
        print(f"saved -> {args.out}")
    if args.open_test:
        log = PROJECT_ROOT / "results" / "ner" / "test_openings.jsonl"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "model_dir": str(args.model_dir),
                                 "condition": res["condition"], "seed": res["seed"], "git_commit": _git_commit(),
                                 "micro_f1": res["micro_f1"]}) + "\n")
        print(f"TEST SET OPENED - logged in {log.relative_to(PROJECT_ROOT)}")


def _selfcheck() -> None:
    tok = [["we", "collect", "your", "bank", "statements", "and", "ip", "address", "for", "credit", "assessment"],
           ["shared", "with", "credit", "bureaus", "and", "lenders"],
           ["we", "use", "email", "address", "for", "marketing"]]
    gold = [["O", "O", "O", "B-DATA_TYPE", "I-DATA_TYPE", "O", "O", "O", "O", "B-PURPOSE", "I-PURPOSE"],
            ["O", "O", "B-THIRD_PARTY", "I-THIRD_PARTY", "O", "B-THIRD_PARTY"],
            ["O", "O", "B-DATA_TYPE", "I-DATA_TYPE", "O", "B-PURPOSE"]]
    pred = [["O", "O", "O", "B-DATA_TYPE", "I-DATA_TYPE", "O", "B-DATA_TYPE", "I-DATA_TYPE", "O", "O", "B-PURPOSE"],
            ["O", "O", "B-THIRD_PARTY", "I-THIRD_PARTY", "O", "B-DATA_TYPE"],
            ["O", "O", "B-DATA_TYPE", "I-DATA_TYPE", "O", "B-PURPOSE"]]
    ex, rel = segment_counts(gold[0], pred[0])
    assert ex.tolist() == [[1, 2, 1], [0, 1, 1], [0, 0, 0]], ex.tolist()          # ip address spurious; purpose cut short
    assert rel.tolist() == [[1, 2, 1, 1], [1, 1, 1, 1], [0, 0, 0, 0]], rel.tolist()   # ... but it overlaps: relaxed hit
    res = evaluate(tok, gold, pred, ["g1", "g2", "g3"], 500, 0)
    assert abs(res["micro_f1"] - 2 * (4 / 7) * (4 / 6) / (4 / 7 + 4 / 6)) < 1e-9, res["micro_f1"]
    assert res["relaxed"]["micro_f1"] > res["micro_f1"] and res["ci95"]["micro_f1"][0] <= res["micro_f1"] <= res["ci95"]["micro_f1"][1]
    e = res["errors"]
    assert (e["pred_exact"], e["pred_boundary"], e["pred_wrong_label"], e["pred_spurious"]) == (4, 1, 1, 1), e
    assert e["spurious_telemetry"] == 1 and e["definition_mismatch"] == 1 and e["gold_missed"] == 0, e
    assert (e["gold_exact"], e["gold_boundary"], e["gold_wrong_label"]) == (4, 1, 1), e
    assert e["micro_f1_without_definition_mismatch"] > res["micro_f1"]
    assert evaluate(tok, gold, pred, ["g1", "g2", "g3"], 500, 0)["ci95"] == res["ci95"]             # deterministic
    assert "ci95" not in evaluate(tok, gold, pred, ["all"] * 3, 500, 0)                              # one group: no interval
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.json", Path(d) / "b.json"
        a.write_text(json.dumps({"conll_file": "x", **evaluate(tok, gold, gold, ["g1", "g2", "g3"], 500, 0)}))
        b.write_text(json.dumps({"conll_file": "x", **res}))
        c = compare([a], [b, b], 500, 0)
        assert c["micro_f1"]["a"] == 1.0 and c["micro_f1"]["delta"] > 0 and c["micro_f1"]["ci95"][0] >= 0, c["micro_f1"]
        assert compare([b], [b], 500, 0)["macro_f1"]["ci95"] == [0.0, 0.0]
    print("selfcheck OK")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        main()
