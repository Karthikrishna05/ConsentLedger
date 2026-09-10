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
[now]  9. NER training  ner/dataset.py + ner/train.py + ner/evaluate.py: fine-tune BERT-base /
                        Legal-BERT / InLegalBERT on data/ner_bio (E1), early stopping on dev, seqeval
                        entity-level metrics, ≥3 seeds + bootstrap CIs (D5).
[later] 10. AA corpus   annotate 15 adaptation + 25 gold-test AA docs (D17) → E2 + final evaluation.
[later] 11. Rest        summarizer + faithfulness, smart contract, end-to-end pipeline, user study, paper.
[later] 9. Summarizer + faithfulness, smart contract, end-to-end pipeline, user study, paper.
```

**One thing still open (a gate, not a blocker):** the three labels are only *candidate* transferable
until the loader loads the real files and the spot-check passes (D10). That's the next real milestone.

---

*Companion docs: `OVERVIEW.md` (plain-language explanations), `DECISIONS.md` (why each choice),
`NER_LABEL_MAPPING.md` (the translation table), `SETUP.md` (environment).*
