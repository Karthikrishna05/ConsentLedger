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
[now]  10c. Annotate    Round 1 (all 23 docs, double-annotated): kappa 0.279 — FAILED (D29); failure is
                        mechanical, not conceptual (D30). Round-2 calibration (2 docs): kappa 0.374 —
                        FAILED, PURPOSE F1 0.000 (D32). Guideline now v7.1: Rules 7-22 (D29-D37).
                        Tools: kappa.py --docs, agreement_report, annotation_audit --strict, adjudicate,
                        fixlist (Rules 7/8/8b/9/9b/11/15/17 + PURPOSE check), relaxed_agreement.
                        NEXT: final calibration on 23_upmint_aa_tos (fresh, independent, v7.1 sent to P4)
                        -> fix pass on all 23 (regenerated fix lists) -> full-corpus kappa -> adjudicate
                        -> gold. No round 4 (D35). Glued-text docs 02_digio / 10_perfios last (D36).
[done] 11. E1 on dev    3 backbones x 3 seeds on OPP-115 dev (D38): Legal-BERT 0.400, InLegalBERT 0.386,
                        BERT-base 0.382 entity macro-F1; ranking flips on token-F1 -> no winner.
                        E1/E2 on the AA test set (the headline) waits on gold; needs a gold ->
                        aa_test.conll converter (not built yet).
[par]  P2 summarizer   P2's track; dataset builder + plan handed over by Drive (D33, D34): text ->
                        summary, reference-free test against gold facts. Needs P1's gold export.
[par]  P3 contract     P3's track; see P3.md. Reference implementation (not a novelty claim, D28).
[later] 11. Rest        summarizer + faithfulness (P2 — see P2.md), smart contract (P3 — see P3.md),
                        end-to-end pipeline, user study, paper.
```

**One thing still open (a gate, not a blocker):** the three labels are only *candidate* transferable
until the loader loads the real files and the spot-check passes (D10). That's the next real milestone.

---

*Companion docs: `OVERVIEW.md` (plain-language explanations), `DECISIONS.md` (why each choice),
`NER_LABEL_MAPPING.md` (the translation table), `SETUP.md` (environment).*
*Per-person implementation guides: `P2.md` (summarizer + faithfulness), `P3.md` (smart contract).*
