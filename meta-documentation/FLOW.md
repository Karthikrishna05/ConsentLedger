# ConsentLedger — Flow (simple language)

Two flows in one place: **(A)** how the finished system will work, and **(B)** how the *build* has
progressed so far. Kept current for audit.

---

## A. How the system will work (the pipeline)

One AA consent document goes in; a plain summary + a tamper-proof on-chain record comes out.

```
   A raw AA consent document (web page / PDF)
                 │
                 ▼
        [1] Clean it to plain text
                 │
        ┌────────┴─────────────────────────────┐
        ▼                                       ▼
[2a] NER model highlights            [2b] Structured parser reads the
     3 things from the prose:             ReBIT consent-artefact JSON fields:
     DATA_TYPE, PURPOSE,                   RECIPIENT, DURATION, FREQUENCY,
     THIRD_PARTY                           DATA_RANGE, DATA_LIFE
        │                                       │
        └────────────────┬──────────────────────┘
                         ▼
        [3] Assemble the full "consent artefact"
            (all six kinds of fact together)
                         │
             ┌───────────┴───────────┐
             ▼                        ▼
   [4a] Summarizer (T5)      [4b] Faithfulness check:
        rewrites it in            run NER over the summary and
        plain English             compare — did the summary drop
                                   or invent any fact?
             │                        │
             └───────────┬────────────┘
                         ▼
        [5] Hash the facts (no personal data on-chain)
            → record consent on the blockchain
            → get a tamper-proof audit link
                         │
                         ▼
        [6] One report: fields + summary + faithfulness
            + on-chain link  (results/pipeline/<doc>.json)
```

> **Why two boxes at step 2:** see the "split by source" decision (`DECISIONS.md` D2). Wordy facts are
> *highlighted* by AI; the exact values (how long / how often / who) are *read from labelled JSON boxes*.

**The research experiment lives inside step 2a.** The NER model is trained two ways and both are scored
on the same sealed 25-document AA test set:
- **E1:** trained only on outside data (OPP-115 + MAPP-English).
- **E2:** trained on that outside data **plus** 15 AA documents.
Comparing E1 vs E2 answers: *how far does outside learning transfer, and how much does a little AA
practice help?*

---

## B. How the build has progressed (where we are)

```
[done] 1. Audit         Read the supplied plan + corpus as untrusted; found contradictions,
                        a duplicate document, and unlearnable labels. → DECISIONS D1, D4
[done] 2. Design        Chose "split by source" (D2) and the E1-vs-E2 study (D3); scoped the
                        NER task to 3 transferable labels; 3 backbones, fair training (D5).
[done] 3. Data plan     Core = OPP-115 + MAPP-English; APP-350 + CUAD auxiliary (D6). Wrote and
                        twice-corrected the label translation table (NER_LABEL_MAPPING.md, v2).
[done] 4. Environment   Built .venv (Python 3.11, CUDA torch, numpy<2); pip check clean; CUDA
                        live on the A4500. (D11, SETUP.md)
[done] 5. Scaffold      Created the whole project skeleton; downloaded datasets get their own
                        data/external/ folder, separate from our data/aa/ corpus.
[done] 6. Get data      Downloaded + extracted OPP-115 (115), MAPP (64 EN + 91 DE), APP-350 (350)
                        into data/external/<corpus>/raw/. Counts match the papers. (D14)
[done] 7. Loader        load_opp115.py DONE + validated: 24,516 offset-verified span records
                        (DATA_TYPE 10,542 / PURPOSE 9,894 / THIRD_PARTY 4,080), gate 0.993 (D15).
                        MAPP turned out to have NO spans in its public release → demoted to auxiliary
                        (D16); no span-level load_mapp.py. OPP-115 is the sole span source; the 3
                        labels are now validated as transferable (D10 ✅).
[done] 8. To CoNLL      bio_tagging.py DONE: OPP-115 → word-level BIO CoNLL (shared across backbones;
                        subword alignment at train time — D18). 103 train / 12 dev policies; train
                        entities DATA_TYPE 2,950 / PURPOSE 2,696 / THIRD_PARTY 1,130. → data/ner_bio/.
[~]    9. NER training  Pipeline BUILT + smoke-tested: ner/dataset.py + train.py + evaluate.py.
                        Smoke (BERT-base, 600 samples, 5 ep) → F1 rises 0.0→0.034, loss 0.80→0.63,
                        i.e. learns correctly (no alignment/metric bug). NEXT: full E1 run —
                        3 backbones × full OPP-115, early stopping on dev, seqeval entity metrics
                        (OPP-115 dev usable now; the AA-test transfer number waits on annotation). D5.
[done] 10a. AA scrape   data/aa/manifest.csv (29 docs) + scrape_aa.py → 28/29 fetched into
                        data/aa/raw/ (1 blocked, ~5 JS-shells; ~23 solid — surplus for deadline). D20.
[done] 10b. AA clean    clean.py DONE → 23 usable docs in data/aa/raw/text/ (median ~3,100 words);
                        5 JS-shells (0 chars) dropped; 0 errors. 23 ≈ 15 test + 8 adapt (D21). ✓
[ready]10c. Annotate    Tooling ready: ls_import_export.py (import w/ doc_id) + kappa.py (entity-F1 +
                        Cohen's κ) + ANNOTATION_GUIDELINE.md (v2, step-by-step). Protocol (D24):
                        pilot 1 doc → κ≥0.6? → both annotate all 23 → adjudicate → gold →
                        ~15 test + ~8 adaptation. THIS is the team's manual critical-path step.
[now]  11. Train/eval   Trimmed spans VALIDATED: BERT-base seed42 OPP-115 dev entity-F1 0.38 /
                        token-F1 0.53 (was 0.12) — D25. Full 3 backbones x 3 seeds sweep running;
                        then collect.py -> results/ner/ablation.{csv,md} (mean +/- std).
                        Pre-training code staged/committed. E1 (eval AA test) + E2 after annotation.
                        AA test = headline number.
[par]  A1. Annotation   Kit (guide v3 + ls_import_tasks.json) sent to P4 (D26). Team runs the
                        calibration pilot -> full double-annotation -> adjudicate -> gold (D24).
[later] 11. Rest        summarizer + faithfulness (P2 — see P2.md), smart contract (P3 — see P3.md),
                        end-to-end pipeline, user study, paper.
```

**One thing still open (a gate, not a blocker):** the three labels are only *candidate* transferable
until the loader loads the real files and the spot-check passes (D10). That's the next real milestone.

---

*Companion docs: `OVERVIEW.md` (plain-language explanations), `DECISIONS.md` (why each choice),
`NER_LABEL_MAPPING.md` (the translation table), `SETUP.md` (environment).*
*Per-person implementation guides: `P2.md` (summarizer + faithfulness), `P3.md` (smart contract).*
