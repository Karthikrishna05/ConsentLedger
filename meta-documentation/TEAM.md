# ConsentLedger — Team Roles (group of 4)

Work division for 4 people (P1 = project owner/architect). Based on the user's proposed split, with two
gaps closed (user study owner; faithfulness-metric owner) and one load-balance fix (P3 finishes early →
picks up the late-phase user study). Roles map to the components in `FLOW.md`.

Guiding rules: one clear owner per area; a defensible individual contribution each (grading/authorship);
shared load on the true bottleneck (annotation); ≥2 independent annotators (D17).

---

## Roles

### P1 — NER/BERT + Lead + Annotator #1  *(you)*
- **Early:** corpus scrape/clean + `splits.json`; **annotator #1**; NER data pipeline (already built:
  loader, bio_tagging).
- **Late:** NER training + evaluation — the **E1 vs E2** experiment across BERT-base / Legal-BERT /
  InLegalBERT (D5); overall **lead + paper coordination**.
- **Résumé line:** "Built the cross-domain transfer-NER experiment and led the system."

### P2 — T5 Summarizer + Faithfulness metric + Summary writer #1
- **Early:** T5 / Flan-T5 ablation (`summ/*`); **writes human summaries** (training pairs + test-split
  human-authored targets).
- **Late:** **owns the faithfulness / entity-preservation metric** — the project's best shot at a
  *methodological* contribution (runs P1's NER over generated summaries; see OVERVIEW "Publication
  outlook"). Do not leave this unowned.
- **Résumé line:** "Built the summarizer and the consent-summary faithfulness metric."

### P3 — Blockchain + (early) IRB + (late) User study & stats
- **Early:** Solidity `ConsentRegistry` + Hardhat tests + Sepolia deploy + `web3.py` bridge +
  `consent_artefact/parse.py`. **Also files the IRB/ethics application in week 2–3** (long latency, low
  ongoing effort).
- **Late:** the contract finishes early, so P3 then **runs the user study + statistics** (3 conditions;
  Cohen's d, bootstrap CIs, Mann-Whitney / Kruskal-Wallis) and **helps annotate** to relieve the
  bottleneck. *(If P3 isn't comfortable with the study, P2 co-owns it — it evaluates P2's summaries.)*
- **Résumé line:** "Built the on-chain consent registry and ran the human-comprehension study."

### P4 — Annotator #2 + Summary writer #2 + Integration
- **Early:** **annotator #2** (pairs with P1 for the double-annotated κ subset + 25 gold test) and
  summary-writing help for P2.
- **Late:** **integration code** — `pipeline/end_to_end.py` wiring NER + T5 + faithfulness + chain into
  one command + report. (Most senior coding task after P1; confirm P4 has the coding skill.)
- **Résumé line:** "Co-built the AA gold corpus and the end-to-end integration."

---

## Annotation (critical path, shared)
- ≥2 independent annotators required for κ (D17): **P1 + P4** double-annotate the ~20% overlap subset
  and **all 25 gold TEST docs**, then adjudicate. The **15 adaptation docs** are single-annotated (split).
- Once the contract ships, **P3 joins annotation** to speed the bottleneck.

## Two open confirmations (only the team can decide)
1. **P3 running the user study + stats** — timing fits (blockchain early, study late), but it's a
   different skill; fall back to P2 co-owning if needed.
2. **P4's coding level for integration** — the hardest coding job after P1's.

## Dependency / timeline map
```
week 2-3: P3 files IRB (long wait)        P1+P4 write guideline + start annotation (P2 helps; P3 after contract)
early   : P1 corpus/splits   P2 T5 setup + summaries   P3 blockchain
mid     : P1 NER E1 train/eval  <── data/ner_bio (done)      P2 summarizer done
          P1+P4 (+P3) finish 25 gold-test annotation → E2
late    : P2 faithfulness metric   P4 integration pipeline   P3 user study + stats
end     : all → paper (P1 coordinates)
```

*All areas' decisions are logged centrally in `DECISIONS.md` regardless of who does the work.*
