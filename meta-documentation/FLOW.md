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
                        5 JS-shells (0 chars) dropped; 0 errors. 23 ≈ 15 test + 8 adapt (D21; superseded by D52). ✓
[done] 10c. Annotate    Two annotators, all 23 docs, five agreement measurements, all reported:
                        round 1 kappa 0.279 (D29) -> round 2 calibration 0.374 (D32) -> round 3 0.283, P4
                        without the guideline (D41) -> round 4 0.522, one fresh doc, independent (D43)
                        -> fix pass by both on all 23 -> 0.426 full corpus (D48).
                        Guideline v4 -> v7.5 (Rules 7-23, D29-D46, D55) + PART I adjudication rulings (D49-D55).
                        Finding: rule violations nearly gone (~120 of 2,700 spans); the residue is what
                        each annotator NOTICES. Rule-normalised ceiling 0.47 -> no further round (D50).
                        Tools: kappa.py, agreement_report, annotation_audit, fixlist (15 buckets, audited
                        D44), relaxed_agreement, adjudicate.
[done] 10d. Gold        adjudicate_auto.py (D50): 511 agreed spans accepted, 1,513 disputed highlights + 133
                        repeat candidates ruled one by one, each tagged with its rule -> gold.json,
                        1,153 spans. Then the P1 + P4 RULES MEETING (D51, D55): 7 rules kept; rule 3
                        dropped (a data SOURCE is a THIRD_PARTY too); rule 4 changed (PURPOSE row 12,
                        account opening & onboarding); rule 9 changed (merge a list only where a piece is
                        meaningless alone). 85 rulings changed + 36 highlights nobody drew added ("new"
                        lines) -> gold REBUILT: 1,261 spans (D 545 / P 382 / T 334). STILL PROVISIONAL.
                        SAMPLE CHECK (D56): 124 rulings, each alone -> P1 96.0%, P4 100% -> the 90% gate
                        is PASSED. The 5 rulings P1 rejected corrected with their neighbours (D57).
                        Gold of D57: 1,258 spans.
                        AUDIT (D58), three perspectives x three passes: ~98% of spans correct, ~93% recall,
                        92.3% consistency on identical text. 49 verified defects (20 remove, 29 add) —
                        16 of the 20 wrong spans were drawn identically by BOTH annotators and never
                        reviewed. APPLIED with two changes by P1 (D59): the consent-artefact signature
                        is not data; identity / contact information are two highlights.
                        GOLD FINAL: 1,266 spans (D 559 / P 381 / T 326); identical-text consistency 99.1%.
[done] 10e. Split       aa_split.py + aa_to_conll.py BUILT and tested (D52). Finding: 13 documents are one
                        template family (up to 75% shared text) -> "15 test + 8 adapt" (D21) would leak.
                        P1 chose option A (D54): TEST = 9 independent docs / 8 groups (08, 14+21, 23, 24,
                        25, 26, 28, 29), ADAPT = 14 (the family + glued 10_perfios). Max overlap across
                        the split 4.7%. data/splits/aa_split.json written. aa_to_conll RUN on the final gold (D59):
                        data/ner_bio/aa_test.conll (559 segments, 826 entities), aa_adapt.conll (845, 439);
                        read back by the trainer's reader, longest segment 177 of 256 pieces. TEST SET SEALED.
[done] 11. E1 on dev    3 backbones x 3 seeds on OPP-115 dev (D38): Legal-BERT 0.400, InLegalBERT 0.386,
                        BERT-base 0.382 entity macro-F1; ranking flips on token-F1 -> no winner.
[done] 12. E1/E2 on AA  The headline. Gold, split and CoNLL files are READY. ner/evaluate.py BUILT (D60):
                        exact + relaxed F1, 95% CIs by bootstrap over document groups, per-group F1,
                        error breakdown incl. "definition mismatch" with OPP-115, truncation check,
                        paired E1-vs-E2 comparison; aa_test.conll needs --open-test and is logged.
                        Rehearsal on the ADAPTATION docs (not a result): E1 ~0.09 exact / ~0.22 relaxed,
                        all three backbones alike. TEST SET STILL UNOPENED.
                        E2 DESIGN (D61, P1): BOTH ways — E2-joint (OPP-115 + AA together) and
                        E2-sequential (E1 model continued on AA only); stop on an AA mock test
                        (D62: the 4 adaptation docs sharing least text with the rest — 01_setu_aa_terms,
                        19_saafe_privacy, 20_scoremeaa_charter, 22_setu_aa_charter; 107 entities; 10 docs /
                        332 entities train); seeds 42-44 x 3 backbones = 18 runs. train.py --e2 built, smoke-tested.
                        E1 models are only read, never overwritten.
                        DONE (D63): 18 E2 models trained; test set OPENED ONCE for all 27 (logged).
                        Exact micro-F1 (9 runs each, CI over 8 doc groups): E1 0.125 [0.10, 0.16] ->
                        E2-joint 0.252 [0.21, 0.33] -> E2-sequential 0.439 [0.35, 0.49]; relaxed 0.29 ->
                        0.44 -> 0.61. All paired differences significant. Backbones tie in E1; Legal-BERT
                        leads after sequential adaptation (0.479). results/ner/aa_test.md.
                        THE TEST SET IS SPENT: no re-scoring after any change.
                        LLM BASELINE (D64): protocol fixed in advance (rules-only prompt without the
                        guideline's test-document cases; 0-shot and 8-shot from adapt-train; develop on
                        adapt-dev; test once). ner/llm_baseline.py built.
                        RESULT (D65), local open models via Ollama, test set, exact micro-F1:
                        llama3.1:8b 0-shot 0.280, 8-shot 0.414; qwen2.5:14b 0-shot 0.479, 8-shot 0.452.
                        qwen 0-shot TIES Legal-BERT E2-sequential on exact F1 (+0.000 [-0.05, +0.08]),
                        loses on relaxed (-0.084); LLM = high recall, low precision. Caveat: the rules were
                        developed on all 23 documents incl. the test ones -> upper estimate for the LLM.
[par]  P2 summarizer   P2's track; dataset builder + plan handed over by Drive (D33, D34): text ->
                        summary, reference-free test against gold facts. Needs P1's gold export.
[done] P3 contract — ConsentRegistry.sol compiled, tested, and deployed to Sepolia. ABI and deployment records saved in the repository. Python registration, read, and revocation scripts implemented and tested. Consent registration, access audit, and revocation transactions verified on Etherscan. See P3.md.
[later] 13. Rest        summarizer + faithfulness (P2 — see P2.md), 
                        end-to-end pipeline, user study, paper.
```

**Open decision:** none blocking. Gold final after the audit (D59), rules ratified (D55), split fixed (D54).
Optional, undecided: a `negated` flag per highlight (D58). E1/E2 (D63) and the LLM baseline (D65) are complete.
**Open decision for P1: the paper's framing** now that a rule-prompted LLM ties fine-tuning (D65). Then: the
results section, uploading the 18 E2 models to the Hub, P2's summariser and the end-to-end pipeline.
P2 can be sent the final gold.
A new session should read this block, then `DECISIONS.md` D55-D65.

---

*Companion docs: `OVERVIEW.md` (plain-language explanations), `DECISIONS.md` (why each choice),
`NER_LABEL_MAPPING.md` (the translation table), `SETUP.md` (environment).*
*Per-person implementation guides: `P2.md` (summarizer + faithfulness), `P3.md` (smart contract).*
