# ConsentLedger — Decision Log

Every real decision, with plain-language reasoning and how it was validated. Newest decisions are added
at the bottom. This is an **audit trail** — nothing here is changed silently; if a decision is reversed,
a new entry records that.

Format per entry: **What** we decided · **Why** (plain) · **Validated by** · **Status**.

---

### D1 — Treat the supplied plan and corpus as *untrusted*, and audit them
- **What:** Independently checked the uploaded build-plan zip and the "VERIFIED" 30-doc corpus instead
  of trusting them.
- **Why:** A plan is only as good as its facts. Trusting a document that turns out wrong wastes months.
- **Validated by:** Found real contradictions (see D4) and one verified-correct citation (D13).
- **Status:** ✅ Standing principle for the whole project.

### D2 — Split the six consent facts *by where they live* ("split by source")
- **What:** `DATA_TYPE`, `PURPOSE`, `THIRD_PARTY` are pulled from prose by the NER model.
  `RECIPIENT`, `DURATION`, `FREQUENCY` (and later `DATA_RANGE`, `DATA_LIFE`) are read from the
  structured ReBIT consent-artefact JSON — **not** by NER.
- **Why:** The AA documents are blank *templates* that rarely state a concrete duration/frequency/name.
  In the real AA system those values are clean fields in a standard JSON form. Asking an AI to "read"
  them from prose is guessing at something that isn't there; reading a labelled box is exact.
  *Analogy: a wedding invitation gushes in prose, but the RSVP card has clean boxes — for the headcount,
  read the box, don't parse the poetry.*
- **Validated by:** The ReBIT/Sahamati consent-artefact schema (structured fields: `consentExpiry`,
  `Frequency`, `FIDataRange`, `DataLife`). See `OVERVIEW.md` → ReBIT section.
- **Status:** ✅ Locked.

### D3 — Research design = "learn elsewhere, prove it here, then test a small top-up" (Design 3)
- **What:** Two experiments on the **same** held-out AA test set: **E1** train on external corpora only;
  **E2** train on external corpora **+ 15 AA docs**. Compare E1 vs E2.
- **Why:** We have too few AA documents to train from scratch. A controlled E1-vs-E2 comparison is a real
  research result *whatever the numbers say*, and it turns "small AA data" from a weakness into the
  thing being measured. It's stronger than a single score and better for a paper, a demo, and a résumé.
  *Analogy: E1 = "can a Delhi-trained driver drive in Mumbai cold?"; E2 = "does a few hours of Mumbai
  practice help?"*
- **Validated by:** Standard transfer-learning / domain-adaptation methodology; E1 alone is the weaker
  "pure transfer" design that E2 strictly improves on.
- **Status:** ✅ Locked (chosen by the user over Design 1 in-domain and Design 2 pure-transfer).

### D4 — One canonical, document-level split; delete the duplicate; 15 adapt / 25 gold test
- **What:** Replace three contradictory split schemes with one. Remove corpus row 30 (it's an exact copy
  of rows 1/6/22). Roles: **15 AA docs = adaptation training** (E2 only), **25 AA docs = sealed gold
  test**, zero overlap.
- **Why:** The original plan gave three different, incompatible splits, and one of them leaked identical
  content into both train and test. A single source of truth (`data/splits/splits.json`) and a sealed
  test set are what make the final score trustworthy. *Analogy: a sealed exam — peek once and the score
  is meaningless.*
- **Validated by:** Direct reading of the plan files (the three schemes literally disagree) and the xlsx
  (row 30 = rows 1+6+22).
- **Status:** ✅ Locked. (Test set opened exactly once, at the end.)

### D5 — Three backbones, uniform training, no layer-freezing
- **What:** Compare `bert-base-uncased`, `nlpaueb/legal-bert-base-uncased`, `law-ai/InLegalBERT`. Same
  training recipe for all; **no** freezing of layers in the main run; early stopping; report entity-level
  P/R/F1 with bootstrap confidence intervals; declare "no significant difference" when intervals overlap.
- **Why:** Freezing different amounts across models that have different internals is an unfair comparison.
  With a small test set, honest confidence intervals prevent crowning a "winner" that's really noise.
- **Validated by:** All three model IDs confirmed to exist on Hugging Face; standard fair-comparison
  practice.
- **Status:** ✅ Locked. (FinBERT optional/appendix, described as a *financial-domain baseline*, not an
  "NER model".)

### D6 — Core training data = OPP-115 + MAPP-English; APP-350 + CUAD are auxiliary only
- **What:** Only OPP-115 and the English half of MAPP are converted into training labels. APP-350 and
  CUAD are background/domain material, never converted into entity labels.
- **Why:** OPP-115 and MAPP mark the **exact phrase** (with character positions) for each fact, so we can
  highlight precisely. APP-350 only tags **whole paragraphs** by topic, and CUAD tags **whole legal
  clauses** — converting those would teach the model to highlight entire blocks (garbage).
  *Analogy: a textbook with chapters labelled by subject is fine background reading but useless for
  teaching precise highlighting.*
- **Validated by:** Read the primary papers directly — MAPS/PoPETs 2019 ("assign labels to policy
  *segments* … loosely correspond to paragraphs") for APP-350.
- **Status:** ⚠️ **Partly superseded by D16.** The claim that *MAPP* provides character offsets was
  based on the LREC paper; the **public MAPP release has no spans** (verified). OPP-115 remains the
  span-level source; MAPP moves to auxiliary. APP-350/CUAD auxiliary decision stands.

### D7 — Character-offset conversion only; whole-segment `text.split()` is banned
- **What:** Each source annotation's *attribute-value span* (its character start/end) is mapped to BIO
  tags via the tokenizer's offset mapping. Never tag a whole sentence/segment.
- **Why:** Whole-segment tagging fabricates labels the human annotator never made, poisoning training.
- **Validated by:** OPP-115/MAPP store `{Practice, Attribute, Value}` with character offsets (confirmed
  in the PolicyQA paper and the datasets themselves).
- **Status:** ✅ Locked. Enforced by a ≥20-span reconstruction spot-check before any training.

### D8 — `THIRD_PARTY` = the entity/recipient span (Definition A)
- **What:** Tag only the span naming the third party (e.g. "credit bureaus"), taken from the
  `Third Party Entity` attribute — not generic "we may share…" sentences.
- **Why:** Keeps the label crisp and learnable; matches what the source datasets actually mark.
- **Validated by:** OPP-115/MAPP `Third Party Entity` attribute.
- **Status:** ✅ Locked.

### D9 — Dropped two tempting-but-wrong mappings
- **What:** Do **not** map `User Choice/Control → PURPOSE`; do **not** treat `Data Retention` as consent
  `DURATION`.
- **Why:** "User choice/control" means opt-out mechanisms, not purpose. "Data retention" (how long data
  is kept) is a different concept from "how long consent is valid." Same-sounding ≠ same-meaning.
- **Validated by:** OPP-115 taxonomy definitions (10 distinct practice categories).
- **Status:** ✅ Locked.

### D10 — The three labels are "candidate transferable" until proven on real files
- **What:** Call them *candidate* transferable labels; only lock "transferable" after loading the actual
  annotation exports and spot-checking ≥20 converted spans against source text.
- **Why:** Whether labels truly line up across corpora is an empirical claim — papers show structure, but
  only the real files prove the conversion.
- **Validated by:** OPP-115 validated on real data (D15 — 24,516 offset-verified spans, gate 0.993).
  MAPP turned out to have no spans (D16), so OPP-115 is the sole span-level source and no MAPP gate is
  needed for the transfer training data.
- **Status:** ✅ Done for the span-level source (OPP-115). The 3 labels are validated as extractable
  from real annotations. (The separate AA gold-annotation gate still applies to the test set.)

### D11 — Environment: venv + pip, CUDA torch, numpy<2, Label Studio isolated
- **What:** Python 3.11 `venv` + `pip`; `torch==2.3.1+cu121` from the CUDA index; `numpy==1.26.4` as the
  compatibility anchor; Label Studio installed in a *separate* venv; Node/Hardhat separate.
- **Why:** conda isn't on this machine's PATH; pip CUDA wheels bundle their own runtime; `numpy<2` is what
  keeps torch/spaCy/bert-score/pandas from fighting; Label Studio's heavy stack is the biggest conflict
  source, so it's quarantined.
- **Validated by:** Built it and ran `pip check` → "No broken requirements found"; `torch.cuda.is_available()`
  → True on the RTX A4500. See `SETUP.md`.
- **Status:** ✅ Done and verified.

### D12 — Documentation & audit protocol
- **What:** All docs live in `meta-documentation/`. Explanations are logged to `OVERVIEW.md`, decisions to
  this file, and system/build flow to `FLOW.md`, all in simple language.
- **Why:** The user wants a fully auditable, plain-language trail rather than knowledge trapped in chat.
- **Validated by:** User instruction.
- **Status:** ✅ Standing rule.

### D13 — Citation integrity: keep the real one, drop the fake one
- **What:** Cite **Barnes et al. 2024** (AJOB) as conceptual prior art; keep the fabricated
  Singh/Pal/Hitchens citation dropped; make novelty claims only "to the best of a systematic search."
- **Why:** A fabricated citation is an instant credibility (and desk-reject) risk; overclaiming novelty
  is unprovable without a literature review.
- **Validated by:** Barnes 2024 confirmed real (DOI 10.1080/15265161.2024.2416117, PubMed 39499856).
- **Status:** ✅ Locked.

### D14 — Datasets downloaded under a research licence into `data/external/`
- **What:** OPP-115, MAPP, APP-350 fetched from usableprivacy.org into `data/external/<corpus>/raw/`.
- **Why:** Keeps downloaded public data isolated from our own AA corpus and reproducible.
- **Validated by:** Exact URLs verified on usableprivacy.org; licence is CC BY-NC (research/teaching) —
  appropriate for this academic project and must be cited. **Downloaded & extracted 2026-09-09**; file
  counts match the papers exactly: OPP-115 = 115 annotation CSVs + 115 policies; MAPP = 64 English + 91
  German; APP-350 = 350 annotations. (macOS `__MACOSX`/`.DS_Store` junk removed.)
- **Status:** ✅ Done — data present under `data/external/<corpus>/raw/`.

### D15 — OPP-115 loader: emit provenance-tagged char-span records, gated on reconstruction
- **What:** `load_opp115.py` converts OPP-115 into normalized **char-span records** (JSONL), not final
  BIO. Defaults: read the **consolidation** set at **threshold 0.75** (annotator redundancy already
  merged); map the 3 attributes (`Personal Information Type`→DATA_TYPE, `Purpose`→PURPOSE,
  `Third Party Entity`→THIRD_PARTY); drop `Other` category, `Unspecified`/`not-selected` values, and
  known errant-offset annotation IDs; tolerate whitespace-offset drift by re-aligning to the trimmed
  span. A built-in **GATE** fails the run if `segment[start:end] == selectedText` holds for < 99% of
  spans.
- **Why:**
  - *Char-span records, not BIO* — BIO is tokenizer-specific; each backbone re-tokenizes from these
    stable records later (matches D7 and the plan). One clean, auditable intermediate.
  - *Consolidation @ 0.75* — removes 3-annotator duplication at a balanced overlap threshold; the
    threshold is a CLI knob so it can be ablated. (Raw `annotations/` remains selectable via `--source`.)
  - *Gate* — offsets are ground truth; if reconstruction fails, our segmentation/offset logic is wrong,
    so the run must refuse rather than emit silently-wrong labels. This is the D10 verification gate.
- **Validated by:** Ran on all 115 policies → **24,516 spans** (DATA_TYPE 10,542 / PURPOSE 9,894 /
  THIRD_PARTY 4,080), 8,250 non-informative values dropped, **match rate 0.9928** (GATE PASSED). The
  remaining ~0.7% are interior unicode/encoding mismatches, dropped conservatively (never mislabeled).
  Output: `data/external/opp115/processed/opp115_spans.jsonl`.
- **Status:** ✅ Done. (Supporting infra: added `pyproject.toml` + `pip install -e .` so
  `python -m consentledger.*` works.)

### D25 — Span-trimming + token-F1 + multi-seed (for citable results)
- **Diagnosis:** the first full BERT-base run gave dev entity-F1 ~0.12 — NOT undertraining (it converged
  and early-stopped at epoch 14/20; the "70%" bar = early stopping). Cause: OPP-115 spans are long
  clauses (PURPOSE median 14 tokens; 42% of entities >10 tokens) and strict exact-match F1 is brutal on
  long spans. Fix is data+metric, not more epochs.
- **What (3 changes, all pre-annotation):**
  1. **Span-trimming** — `trim_spans.py` writes a SEPARATE `opp115_spans_trimmed.jsonl` (original
     `opp115_spans.jsonl` preserved) reducing each span to its longest noun chunk, capped at 6 tokens
     (median 6→2). Aligns training spans with the short AA target → exact-match becomes meaningful and
     transfer improves. Build trimmed CoNLL: `bio_tagging --spans opp115_spans_trimmed.jsonl` (now the
     default training data in `data/ner_bio/`; original CoNLL regenerable via `bio_tagging` with no flag).
  2. **token-F1** — added to `train.py` + `evaluate.py` metrics (fairer signal than exact-match on spans).
  3. **multi-seed** — `train.py --seed N` (suffixes the output dir `_sN`); `collect.py` aggregates
     mean ± std across seeds and both dev + AA-test, tagged E1/E2.
- **Why:** citable results need (a) the right span shape, (b) an honest metric, (c) mean±std over ≥3
  seeds (single-seed isn't citable-grade). The OPP-115 dev number stays a diagnostic; the **AA test is
  the headline**.
- **Validated by:** trim ran (24,516 spans, 0 dropped, median 2 tokens); trimmed CoNLL rebuilt (more
  clean entities: DT 4,233 / PURP 4,167 / TP 1,555); smoke confirmed token-F1 + seed-suffix work.
- **Result (validates the fix):** first full BERT-base run on **TRIMMED** data (seed 42, OPP-115 dev) →
  entity micro-F1 **0.38** / macro-F1 **0.38** / **token-F1 0.53** — ~3× the pre-trim 0.12. Early-stopped
  ~epoch 9. Confirms the low score was span-shape, not training. Full 3×3-seed sweep runs next.
- **Status:** ✅ Implemented + fix validated. Full multi-seed sweep is the author's VS Code step.
- **Follow-up (collect.py missing-seed guard):** `collect.py` only *reads* saved per-seed metrics; a
  crashed seed that never wrote `dev_metrics.json` would be silently omitted, quietly shrinking a group's
  `n_seeds` and its mean±std. Added a guard that infers the expected seed count (max `n_seeds` across
  groups) and warns for any `(backbone, condition)` group with fewer, naming which. Cheap insurance so a
  dropped seed can't silently distort the citable numbers.

### D26 — Sharing the corpus with the annotators (not via git)
- **What:** `data/aa/annotated/ls_import_tasks.json` (the Label Studio import file) embeds the full
  scraped text of the 23 AA docs, so it is **git-ignored** and shared with P4 **directly** (Drive/zip/USB),
  never committed. A handoff bundle `ConsentLedger_annotation_kit_for_P4.zip` (guide v3 + import file) was
  built in `Downloads/`.
- **Why:** (a) both annotators must import the **byte-identical** file or character offsets won't align
  and κ breaks (re-scraping could diverge); (b) it's scraped company text — fine to share privately with
  the 4-person team (research collaboration) but not to commit/redistribute (consistent with the
  `data/aa/raw` exclusion); it's regenerable via `ls_import_export make-tasks`.
- **Status:** ✅ Kit sent to P4; `ANNOTATION_GUIDELINE.md` expanded to **v3** (beginner-proof, click-by-
  click: install → import → annotate file-by-file → export → κ → adjudicate + FAQ).

### D24 — Annotation executed calibration-first, then full double-annotation of all 23
- **What:** Concrete protocol (refines D17 for the real 23-doc corpus): (1) **pilot** — P1 & P4 each
  independently annotate ONE doc (the last, e.g. `29_icici_home_fin_terms`) and run `kappa.py`; (2) if
  **κ ≥ 0.6 → proceed**, else discuss disagreements, update the guideline, re-annotate, recompute;
  (3) both then annotate **all 23** independently; (4) re-run κ on all 23 (reported number); (5)
  adjudicate → one gold corpus → split ~15 test / ~8 adaptation.
- **Why:** at 23 docs, double-annotating everything is feasible and gives the strongest test set + a real
  κ; piloting on 1 doc first catches a bad/ambiguous guideline before the team sinks hours into all 23.
- **Tooling:** `ls_import_export.py make-tasks` (import file preserving `doc_id`); `kappa.py` (entity-F1
  primary + token Cohen's κ secondary, on ONE shared tokenization — no min_len, D10). Label Studio runs
  in `.venv-annotation`. Full steps in `ANNOTATION_GUIDELINE.md`.
- **Status:** ✅ Tooling + guide ready; annotation is the team's manual step (critical path).

### D23 — Trained weights → Hugging Face Hub; metrics → git (via collect.py). Do NOT commit weights.
- **What:** Model weights are **not** committed to GitHub (each ~400–500 MB; GitHub rejects >100 MB;
  they're reproducible from config+seed+data). Instead: (a) `collect.py` copies each model's small
  `dev_metrics.json` + `run_meta.json` into `results/ner/` (committed) and writes `ablation.csv`/`.md`
  — the **citable numbers**; (b) the actual weights go to the **Hugging Face Hub** (purpose-built, free,
  gives a citable model URL, builds the author's HF profile).
- **Why:** keeps the git repo small + reproducible, puts weights where weights belong, and yields both
  citable metrics (git) and a citable artifact (HF).
- **License caveat (must honor):** the models are fine-tuned on **OPP-115 (CC BY-NC, research-use)**, so
  each HF model card must set license `cc-by-nc-4.0`, attribute OPP-115 (Wilson et al. 2016) and the base
  model, and state research/non-commercial use. Keep the HF write token secret (never committed). Upload
  **final** models (not smoke runs).
- **Status:** ✅ Decided. `collect.py` built; HF upload is the author's manual step (see chat/README).

### D22 — Text normalization applied in clean.py (before annotation)
- **What:** `clean.py` normalizes all output text: unicode spaces (incl. `\xa0`) → normal space; curly
  quotes → straight (`"`,`'`); zero-width chars + stray UI symbols (bullets `•●·`, icons `⛔⚠ℹ↓`) removed.
  **Em/en dashes (—,–) and all real content are preserved.**
- **Why:** annotation offsets index this exact text, so it must be finalized *now*. `\xa0` is a
  space-in-disguise that breaks tokenization/offsets; straight quotes match OPP-115; UI icons are
  page-chrome noise. (A prior full-character scan had already confirmed **no** corruption — no U+FFFD,
  control chars, or mojibake; these are consistency fixes, not repairs.)
- **Validated by:** post-regeneration re-scan → only `—`/`–` remain (legitimate); word counts unchanged
  (min 850 / median 3,106 / max 7,990), so no content lost.
- **Status:** ✅ Done. 23 docs in `data/aa/raw/text/` are annotation-final.

### D21 — AA split corrected to the REAL corpus size (~23 usable, not 40)
- **What:** The "15 adaptation + 25 test = 40" figure (from the phantom 2nd-audit doc) exceeds our
  corpus and is **dropped**. Real split on ~23 solid docs: **~15 gold TEST** (double-annotated +
  adjudicated) + **~8 adaptation** (single-annotated, E2). If time is tight, annotate the **test set
  first** — E1 (pure transfer) needs only a test set; E2 is the bonus.
- **Why (is it enough?):** judge by *entities*, not docs. At ~59 entities/doc (OPP-115 rate), ~15 test
  docs ≈ 600–900 entity annotations — a reasonable entity-level F1 size. Few-shot **adaptation** needs
  only 8–10 docs by design. Adequate for the workshop/college target (D19) **with** honest reporting:
  entity-level F1 + **bootstrap CIs** + per-label support + a stated small-corpus limitation. NOT enough
  for tight-CI top-tier claims (never the goal).
- **Whole-system benchmark** needs no more annotation: summarizer test = ~5–10 human-written summaries;
  faithfulness reuses the NER model; contract eval = gas/behaviour.
- **Supersedes:** the "15+25" numbers wherever they appear (D3/D10/D16 context).
- **Status:** ✅ Corrected plan.

### D20 — AA corpus manifest + scrape (28/29 fetched)
- **What:** Built `data/aa/manifest.csv` (29 unique docs; row-30 bundle dropped as a duplicate of
  rows 1/6/22, per A2) with stable `doc_id`s; wrote `scrape_aa.py` (polite: UA + delay + timeout, logs
  status/bytes/sha256 to `data/aa/raw/scrape_log.csv`). Scraped into `data/aa/raw/{html,pdf}/`.
- **Result (2026-09-10):** **28/29 OK.** Failures/caveats: `27_bajaj_finance_consent_form` → HTTP 403
  (bot-blocked; it was the only *filled* consent form — not needed for the 3 prose labels). ~5 responses
  are thin JS-rendered shells (Finvu ×3, Protean charter, CAMS — 12–27 consent-term hits vs ~130 in a
  real doc) → likely unusable without a headless browser.
- **Why it's fine:** deadline mode needs only ~12–15 annotated docs (D19); ~23 solid docs is a surplus.
  Thin/blocked docs are dropped now; a teammate can browser-"Save As" any we later want.
- **Validated by:** scrape log + a consent-term-density check on the small files.
- **Status:** ✅ Done. Next: `clean.py` (HTML/PDF → text; will filter shells by text length).

### D19 — Deadline descope: MVP project + written paper in ~2 weeks; user study → future work
- **What:** Target a working project (demo) + a *written* paper in ~2 weeks. **Cut the IRB + formal user
  study** (deferred to future work). Shrink annotation to ~12 AA docs (double-annotate ~4 for a κ
  number). Reduce the ablation to 3 backbones × 1 seed (more if time). Keep the technical core: NER E1
  (+E2 if time), T5 summarizer, **faithfulness metric (now the headline contribution)**, blockchain +
  Sepolia deploy, integration pipeline.
- **Why:** IRB approval alone takes *weeks* before data collection can even begin — incompatible with a
  2-week deadline. Everything else is fast (infra done; base models train in minutes). A paper can be
  *written and submitted* in 2 weeks; *acceptance* is a months-long process after the deadline and out of
  scope. Dropping the study is honest (stated as future work) and makes the faithfulness metric the lead.
- **Validated by:** Deadline stated by the user (college project + paper to submit alongside).
- **Status:** ✅ Active plan. Full schedule in `DEADLINE_PLAN.md`. (The full-rigor 26-week plan remains in
  the plan file for any later, stronger paper submission.)

### D18 — BIO conversion: word-level CoNLL shared across backbones (not per-tokenizer)
- **What:** `bio_tagging.py` emits **word-level** CoNLL (one word + tag per line). One dataset is shared
  by all 3 backbones; each model's subword tokenizer aligns to these words **at train time** (first
  subword = label, rest = -100). Word tokenization is offset-aware regex (never `.split()`). ALL segments
  are emitted, incl. negatives (all `O`). Overlapping spans of different labels → **longest-span-wins**
  (deterministic). Train/dev split is at the **policy level** (90/10, seed 42) to prevent leakage.
- **Why:** This is the standard HF token-classification pattern and it **supersedes the earlier
  "regenerate CoNLL per tokenizer" wording** — word-level + train-time subword alignment is equivalent,
  simpler, and still fully offset-based / no cross-tokenizer subword reuse (honours D7's real intent).
  Negatives teach the model what is *not* an entity; policy-level split avoids train/dev leakage;
  longest-wins cleanly collapses OPP-115's nested/overlapping practice spans to one maximal entity.
- **Validated by:** Ran on OPP-115 → 103 train / 12 dev policies; train 3,362 segments / 327K tokens,
  entities DATA_TYPE 2,950 / PURPOSE 2,696 / THIRD_PARTY 1,130; built-in self-check reconstructs
  entities from the BIO and asserts labels ⊆ inputs. Output: `data/ner_bio/{train,dev}.conll`.
- **Status:** ✅ Done. (E2 will append AA-adaptation CoNLL to `train.conll` later.)

### D17 — Annotation protocol: double-annotate the κ-overlap + gold test; single-annotate the bulk
- **What:** Two annotators independently label the **~20% overlap subset** (for Cohen's κ) and **all 25
  gold TEST docs** (+ adjudication → reconciled gold). The **bulk training-volume** AA docs may be
  single-annotated (split across people) for efficiency.
- **Why (raised as a team question — "isn't one annotator more accurate?"):** for NER on legal text there
  is no pre-existing ground truth; humans create it by judgment. One annotator makes bias/inconsistency
  *invisible* and yields an F1 that only measures "how well the model imitates one person" — reviewers
  reject that. Two annotators give a reliability number (κ) **and** cleaner labels via adjudication;
  disagreements are information that improves the guideline. Single-annotation is acceptable only for
  bulk training data where volume > perfection.
- **Validated by:** Standard corpus-construction practice; the plan's M1 gate (κ ≥ 0.6) requires it; a
  corpus paper without inter-annotator agreement is essentially un-publishable at the target venues.
- **Status:** ✅ Locked. (Full plain-language rationale + analogies in `OVERVIEW.md`.)

### D16 — MAPP (public release) is segment-level with NO spans → OPP-115 is the sole span-level source
- **What:** Do **not** build a span-level `load_mapp.py`. OPP-115 is the only span-level NER training
  corpus. MAPP joins APP-350 and CUAD as **optional auxiliary** (segment-level) data.
- **Why:** On inspecting the actual files, MAPP's `English_consolidation/` is one row **per segment**
  listing which attributes/values appear (`['Information Type','Purpose',...]`) with **no `selectedText`
  and no character offsets** — the same segment-level limitation as APP-350. You cannot make token-level
  BIO from labels that aren't tied to specific words without fabricating spans (the banned pattern, D7).
- **Validated by:** `grep -riE "selectedText|startIndex|endIndex" English_consolidation/` → **0 matches**;
  the 8 columns are policy id / segment id / category-list / attribute-list / value-list / policy_type /
  URL / MAPP-59 flag; segments are newline-separated plain text. The MAPP *manual*'s "selected text …
  location in the segment" paragraph is boilerplate copied from OPP-115 and does not match the shipped
  columns. (The LREC paper had spans internally; they are not in the public release — so D6's earlier
  "MAPP is span-level" assumption, taken from the paper, does not hold for the data we actually have.)
- **Consequence:** E1/E2 design is unchanged (train on OPP-115 → test on AA; E2 adds 15 AA docs).
  Losing MAPP trims domain diversity but does not break the study; OPP-115's 24,516 spans are ample.
  MAPP *could* later serve a segment-level auxiliary task (multi-label classification / continued
  pretraining) if we choose — optional, not core.
- **Status:** ✅ Decided. This is exactly the kind of assumption the D10 gate exists to catch before
  building on it.

### D27 — Verified the ReBIT consent-artefact schema against a primary source (grounds D2)
- **Trigger:** while annotating, P1 noticed the scraped prose docs (T&C/privacy) contain **no** frequency
  /duration/recipient values — and asked whether the "split by source" assumption (D2: those 3 come from
  the structured ReBIT consent artefact, not NER) is actually factual or just assumed.
- **What we checked:** fetched two REAL published consent artefacts from Sahamati (the AA industry body,
  ReBIT-conformant), one ONETIME + one PERIODIC, and confirmed the exact fields/nesting.
  - Sources: sahamati.org.in/consent-artefact-one-time-consent-for-a-loan-application/ and
    …/consent-artefact-periodic-consent-for-monitoring-of-loan-account/ (verified 2026-09-14).
  - Confirmed field→label map: **DURATION**=`consentStart`/`consentExpiry`; **FREQUENCY**=`Frequency{unit,
    value}`; **RECIPIENT**=`DataConsumer{id,type:"FIU"}`; plus `FIDataRange{from,to}` (DATA_RANGE),
    `DataLife{unit,value}` (DATA_LIFE), `fetchType` (ONETIME/PERIODIC), `Purpose{code,text}`.
- **Findings that shape the parser:** (a) RECIPIENT is a **coded id** (`DC1`), not a prose name → resolve
  id→entity, don't expect text; (b) **nesting varies** between the two examples (some blocks nested in
  `ConsentDetail`, some siblings) → `parse.py` must look keys up **robustly** (recursive), not by fixed
  path; (c) PURPOSE appears in BOTH sources (prose for NER + a canonical code in the artefact) — no
  conflict.
- **The real gap:** schema/examples are now confirmed, but the scraped corpus has **~0 filled artefacts**.
  So the structured-parser eval set = the 2 real examples + **synthetic** variants. Built
  `gen_consent_artefacts.py` (varies values on the real templates; `--selfcheck` passes) and saved the 2
  real examples + a field-map README + a **formal JSON Schema** (`consent_artefact_schema.json`, draft-07)
  into `data/aa/consent_artefacts/` (committed reference fixtures). `--validate` confirms the real ONETIME
  example + 50 synthetic artefacts conform to the schema (uses `jsonschema`, now pinned in requirements).
  The schema validates the canonical nesting; the periodic example's sibling nesting is a rendering quirk,
  handled by robust key lookup in the parser.
- **Honesty rule (locks framing):** the consent-artefact parser is a **deterministic reader of the ReBIT
  schema**, demonstrated on real + synthetic artefacts — **NOT** an evaluated ML model. The NER E1/E2
  study remains the headline contribution; the parser is a supporting pipeline component.
- **Status:** ✅ D2 confirmed factual (primary-source grounded). P1's annotation observation was correct
  and expected — prose docs never carried those 3 fields.

### D28 — Contribution claims REVISED after a systematic novelty search (supersedes D6's framing)
- **Trigger:** P1 noticed the ICICI policy text restating the RBI NBFC-AA Master Direction — standardized
  consent artefact, revocation, artefacts "logged, audited, and verified", user-accessible consent record —
  and asked: *is our system actually novel, or does this already exist?* A systematic search was run
  (2026-09-24; arXiv + PubMed/PMC + web; full protocol, queries and citations in `RELATED_WORK.md`).
- **Findings (evidence, not judgement):**
  - 🔴 **Blockchain consent registry is NOT novel.** *Soteria* (arXiv:2003.10128) already stores hashes of
    data-access/sharing agreements on a ledger for revocation + compliance proof; *Grant, Verify, Revoke*
    (arXiv:2603.15721) names our exact lifecycle as a published pattern; a PRISMA review (PMC13287375)
    covers 55 studies; a GDPR-blockchain SLR names **financial data** as an established domain.
  - 🔴 **Entity-preservation faithfulness is NOT novel.** arXiv:2102.09130 is the canonical entity-level
    factual-consistency metric; **EROS** (arXiv:2403.00141) already does entity-controlled summarization
    *of privacy policy documents* with span-based entity extraction + PD-Sum.
  - 🟡 **Privacy-policy NER / domain adaptation is an established method** (PLUE arXiv:2212.10011;
    EURO-5K arXiv:2606.02971; CrossNER) — our E1/E2 design has direct precedent.
  - 🟢 **Indian AA consent-document NLP is genuinely empty.** A dedicated query returned zero AA papers
    (top relevance 0.49, all generic fintech NLP); web search returned only regulatory/industry material.
- **Decision — reposition as a RESOURCE + APPLICATION study, not a methods paper.** Claim: (1) first
  gold-annotated **AA consent corpus** + released guideline; (2) first **transfer/adaptation benchmark**
  (E1/E2) into the AA domain; (3) a **reference pipeline** (extraction → disclosure-fidelity audit →
  on-chain anchoring) motivated by the gap the Master Direction leaves open: it mandates *informing* the
  user but never verifies the *fidelity* of that informing.
- **Explicitly DROPPED claims:** novel blockchain consent mechanism; novel faithfulness metric; "first
  system to record AA consent on-chain". P3 is now framed as a **reference implementation**.
- **Consequences:** `P2.md` §1 corrected (it had overclaimed the faithfulness metric as novel);
  `RELATED_WORK.md` created with the search protocol, per-pillar citations and required differentiation
  statements. Venue expectation unchanged: workshop / short paper.
- **Caveat carried forward:** the search did NOT cover ACL Anthology, Scopus, IEEE Xplore or ACM DL —
  re-run queries 1–4 there before submission; only then is "to the best of a systematic search" earned.
- **Status:** ✅ Decided. P1's instinct was correct and caught a framing error before submission — the
  finding grounds the paper rather than weakening it.

### D29 — Round-1 double-annotation FAILED the gate (kappa 0.28); guideline -> v4 with Rules 7 & 8
- **What happened:** P1 and P4 completed independent annotation of all **23/23** AA docs (doc_ids match,
  every doc has spans). Agreement on the full corpus: **Cohen's kappa 0.2789** vs the 0.6 gate;
  entity-level P 0.333 / R 0.170 / **F1 0.225**. Only **1 of 23** docs cleared the gate
  (`14_nadl_charter`, 0.625). The pilot doc `29_icici` had scored 0.587 at calibration and has now
  *fallen* to 0.451 — the annotators **diverged after the pilot rather than converging**.
- **Diagnosis (new tool `agreement_report.py`, which buckets every span):**
  | bucket | n | reading |
  |---|---|---|
  | EXACT | 292 | agreed |
  | BOUNDARY | 108 | span edges — minor |
  | LABEL | **7** | the 3-label ontology is essentially SOLVED |
  | A_ONLY | **1432** | one-sided |
  | B_ONLY | **541** | one-sided |
  **83% of all disagreement is one-sided marking** — they disagree on *whether to mark at all*, not on
  which label or where the edges are. This invalidates the earlier "fix the boundaries" hypothesis.
- **Two confirmed causes (evidence, not guesswork):**
  1. **Rule 5 (mark every occurrence) applied by A, ignored by B.** In `28_indifi` A marked "third
     parties" 21x and "cookies" 13x (166 of 438 spans are repeats); B had **0** repeats in the same doc.
  2. **Different inclusiveness thresholds, flipping per document.** Excluding repeats, `28_indifi`:
     A 322 unique vs B 50; but `22_setu_charter`: A 8 vs B 38. Each went deep on different docs.
  - **Ruled out:** incomplete passes. Last-span position covers 85-100% of doc length for both
    annotators on nearly every doc — they read it all and still marked wildly different amounts.
- **Decision — guideline bumped to v4 with two new rules** (not a re-annotation from scratch):
  - **Rule 7 — mark EVERY occurrence, always**, with the reason stated: unmarked repeats are labelled
    "not an entity" in training data, so skipping them actively teaches the model the wrong thing. A's
    behaviour is correct; B's must change.
  - **Rule 8 — a specificity test + an explicit STOPLIST** (`information`, `personal data`, bare
    `third parties`, `services`, `business purposes`, …) plus default rulings on the round-1 borderline
    cases (cookies → no; address/mobile → yes; fraud prevention → yes; provision of the services → no).
    Key ruling: bare **"third parties" is the category name, not a recipient** — mark the named recipient.
  - Tricky-cases section seeded with all round-1 rulings so they cannot re-diverge.
- **Recovery path (deadline-aware):** do **not** re-annotate all 23. Because LABEL/BOUNDARY agreement is
  already high, the remaining work is adjudication — deciding which one-sided spans are real — and
  `results/annotation/agreement/docs/<doc_id>.md` lists exactly those. Sequence: settle rules (done) ->
  re-calibrate on 2 docs to kappa>=0.6 -> adjudicate the existing 23 -> if time is short, cut the gold
  test set to the best-agreeing docs and report n honestly.
- **For the paper:** report this honestly. Round-1 kappa 0.28 -> guideline refinement -> round-2 kappa is
  a legitimate and publishable resource-paper narrative (D28 frames the corpus as the contribution).
- **Repo hygiene:** `ExportA/B.json` and the per-doc diff files quote scraped text -> git-ignored
  (`[Ee]xport*.json`, `results/annotation/agreement/docs/`). `summary.csv` + `report.md` (numbers only)
  are committed as the provenance.
- **Status:** ⚠ Gate NOT met. Guideline v4 shipped; re-calibration + adjudication is the team's next step.

### D30 — Corpus-grounded annotation audit: the failure is mechanical, not conceptual (Rule 8b added)
- **What we did:** built `annotation_audit.py` to compare both exports against the ORIGINAL corpus text
  (`ls_import_tasks.json`), not just against each other. Method: a **consensus lexicon** — every
  (phrase, label) BOTH annotators independently endorsed at least once — is located in the raw text of
  every document, and each occurrence is scored as marked-by-both / A-only / B-only / missed-by-both.
  Conservative by construction: only terms the annotators themselves validated can count as a "miss".
- **Integrity check passed:** corpus, ExportA and ExportB are **byte-identical in text** across all 23
  docs with matching doc_ids. Offsets are comparable — the disagreement is judgement, not tooling.
- **⚠ Self-correction (recorded so the number is not misquoted):** the first run reported **55.7%**
  missed-by-both. That was **inflated** — a single sloppy mark by each annotator promotes a generic word
  into "consensus", e.g. bare `financial` then matched and "missed" 418 times. A `--strict` lexicon
  (multi-word, endorsed >=2x by each, generic stoplist removed; 34 terms / 311 occurrences) gives the
  defensible figures: **both 31.8% | A-only 39.2% | B-only 5.8% | missed-by-both 23.2%**;
  mean recall A **58%**, B **39%**. Always quote the `--strict` numbers.
- **Findings stable across every filter setting:**
  1. Co-marking **never exceeds ~32%**, even on unambiguous multi-word terms both annotators endorse.
  2. **B's recall problem is mechanical:** A made **442 repeat marks**, B made **10**. B essentially
     never marks a phrase twice. This one behaviour explains B's low recall and the 7:1 A-only:B-only
     ratio. Rule 7 is the fix and it is **B** who must change.
  3. **Both miss ~23%** of even the clearest entities — e.g. `grievance redressal` (49x),
     `non-banking financial company` (24x), `data sharing` (21x), `authentication` (18x),
     `agents` (17x), `credit information` (13x), `dispute resolution` (10x).
- **The two perspectives (label proportions are nearly identical — A 44/29/28, B 39/28/33 — so they
  agree on priorities; they differ on what they think they are reading):**
  - **A's lens = web-technical + generic:** `cookie`, `operating system`, `version`, `spi`, `pii`, bare
    `third party`, `related parties`, `agencies`, `bodies`, `partners`, `services`,
    `provision of the services` -> these are precisely the **Rule 8 stoplist**.
  - **B's lens = AA-framework + credentials:** `reserve bank of india`, `rbi`,
    `financial information user`, `financial information provider`, `sahamati`, `consent artefact`,
    `login id`, `pins`, `private keys`, `user authentication credentials`.
  - **Both violate v4 in opposite directions.** B is also self-inconsistent: `financial information`
    tagged DATA_TYPE 15x and THIRD_PARTY 2x.
- **Decision — new Rule 8b: AA-framework roles and regulators are NEVER THIRD_PARTY.** Never mark
  `Account Aggregator`/`AA` (the data-blind pipe), `FIP` (the source), `FIU` (the main company, already
  covered by Rule 3), `RBI`/`Reserve Bank of India` (regulator — supervising is not receiving),
  `Sahamati` (industry body), or `consent artefact`/`consent manager` (mechanism names). Test:
  *"does my data end up in their hands as a result of this consent?"* Worth ~40 of B's spans.
  Tricky-cases list extended with every ruling above; guideline header now says v4 = Rules 7, 8, 8b.
- **Why this is good news:** the residual problem is **mechanical, not conceptual** — only 7 LABEL
  conflicts across 23 documents. Three concrete corrections (B marks repeats; A drops stoplist terms;
  both apply 8b) address the bulk of the gap without re-teaching the task.
- **Artifacts:** `results/annotation/audit/corpus_audit.md`, `missed_terms.csv`, `per_doc/<doc_id>.md`
  (what A marked, what B marked, what both missed, per document). The per-doc files quote scraped text
  and are git-ignored; the summary tables are committed.
- **Status:** ✅ Audit complete, guideline updated. Next: re-calibrate on 2 short docs -> kappa >= 0.6
  (D29 recovery path), then adjudicate.

### D31 — Keep all 23 docs; fix via PER-ANNOTATOR fix lists instead of joint adjudication (supersedes D29's scope cut)
- **Trigger:** P1 rejected the D29 recommendation to cut the corpus to 12 documents, on the correct
  grounds that ~8 test + ~4 adaptation leaves too little room for the E1/E2 ablation that IS the study.
  P1 proposed instead: give each annotator a file telling them what THEY missed and where.
- **Decision — adopt P1's proposal; the 12-doc cut is withdrawn.** All 23 documents are retained.
  Built `fixlist.py`, which emits one file per annotator per document with five buckets, ordered
  most-certain first:
  1. **DELETE** — your span breaks Rule 8 (stoplist) / 8b (AA roles). No judgement.
  2. **ADD_REPEAT** — you marked this phrase elsewhere in THIS document but skipped this occurrence.
     Your own internal inconsistency (Rule 7). No judgement.
  3. **ADD_MISSED** — the phrase is in the corpus consensus lexicon (both of you endorse it somewhere),
     it occurs here, and you left it blank. High confidence.
  4. **SHORTEN** — the other annotator marked a shorter version; Rule 1 prefers shorter.
  5. **SELF_CHECK** — a phrase only YOU use anywhere in the corpus; re-read against the Rule 8 test.
  Every item carries exact character offsets so the annotator jumps straight to the spot.
- **Workload (spans -> DISTINCT phrases to actually decide, which is the real cost):**
  | bucket | P1 | P4 |
  |---|---|---|
  | DELETE | 259 spans -> **23 phrases** | 78 -> **18** |
  | ADD_REPEAT | 750 -> **168** | 615 -> **131** |
  | ADD_MISSED | 429 -> **62** | 694 -> **89** |
  | SHORTEN | 29 | 79 |
  | SELF_CHECK | 883 -> 696 | 471 -> 394 |
  Buckets 1-3 collapse to roughly **250 decisions each** — decide "drop `services`" once and every
  instance follows.
- **Why this beats joint adjudication:** both annotators work **alone and in parallel** (~3 h each wall
  clock) instead of ~7 person-hours scheduled together; the corpus stays at **23 docs, not 12**; and the
  output is **two corrected exports** rather than a hand-merged gold file — so `kappa.py` can be re-run
  to produce a genuine, reportable **round-2 kappa**, which a merged file could never give.
- **Root-cause fit:** P4's 615 missed repeats + 694 missed consensus spans are precisely the one-sided
  gap (A_ONLY 1,432 vs B_ONLY 541) that produced kappa 0.279 in D29/D30. This attacks that directly.
- **Calibration correction (supersedes D29's advice):** D29 suggested piloting on two SHORT documents.
  That would give **false confidence** — the failure mode is density/repeats, which barely exists in a
  5k-char charter. Calibrate on **one short and one dense** document: `26_zerodha_tos` (5k) and
  `17_pb_fintech_aa_privacy` (15k, one of the worst density gaps).
- **Pre-registered decision rule for the 2-doc calibration** (a 2-doc kappa has a CI of roughly +/-0.15,
  so it is a GATE CHECK, not an estimate of the final number):
  - kappa **>= 0.75** -> the rules worked; proceed across all 23.
  - kappa **0.60-0.75** -> ambiguous; proceed but re-check after 5 more documents.
  - kappa **< 0.60** -> rules still insufficient; stop and diagnose rather than grinding through 23.
- **Known risk:** SELF_CHECK is the bucket that can go wrong. With ~696 (P1) and ~394 (P4) distinct
  phrases there is a temptation to mass-delete, which would swing the corpus from over-marking to
  under-marking. Annotators must apply the Rule 8 test honestly — `login id`, `private keys` and
  `grievance redressal` live in that bucket and SHOULD survive.
- **Sequence:** calibrate (2 docs, rule above) -> both apply buckets 1-3 across all 23 in parallel ->
  each does their SELF_CHECK pass -> re-export -> re-run `kappa.py` for the round-2 number -> adjudicate
  only the residue.
- **Repo hygiene:** fix lists quote span text -> `results/annotation/fixlist/` is git-ignored; the
  summary `README.md` counts are the committed record.
- **Status:** ✅ Tooling shipped (`fixlist.py`, selfcheck passes). D29's 12-doc cut is **withdrawn**.
  Team's next action is the 2-document calibration.

### D32 — Round-2 calibration FAILED (kappa 0.374, worse than baseline); cause isolated to PURPOSE span length; Rule 9 added
- **What was run:** P1 and P4 independently re-annotated the two calibration documents
  (`26_zerodha_tos`, `17_pb_fintech_aa_privacy`) from scratch under guideline v4, fix lists unopened for
  those two (so the test was not circular). Exports: `Export2A.json` / `Export2B.json`. Verified only
  those two documents changed; the other 21 are byte-identical to round 1.
- **Result — STOP per the pre-registered rule in D31:**
  | | round 1 (same 2 docs) | round 2 |
  |---|---|---|
  | Cohen's kappa | 0.492 | **0.374** |
  | entity micro-F1 | 0.306 | 0.360 |
  | **PURPOSE F1** | — | **0.000** |
  | DATA_TYPE F1 | — | 0.465 |
  | THIRD_PARTY F1 | — | 0.417 |
  Agreement got **worse**, not better. D31's rule said kappa < 0.60 -> stop and diagnose rather than
  grinding through 23 documents; that rule was followed.
- **Diagnosis (measured, not guessed) — it is span LENGTH on PURPOSE, and nothing else:**
  | PURPOSE median span | P1 | P4 |
  |---|---|---|
  | `26_zerodha_tos` | 3.0 words | **10.0 words** (max 16) |
  | `17_pb_fintech_aa_privacy` | 3.0 words | **8.0 words** (max 12) |
  A 3-word span and a 10-word span naming the same activity can never match under exact-match scoring,
  which is the entire explanation for PURPOSE F1 = 0.000. Examples P4 marked:
  `to raise a grievance with the grievance resolution officer of the FIU`,
  `For exploring additional use cases within the Account Aggregator framework`,
  `calculate the percentage of users accessing a specific feature of the Services`.
  P1 marked the same ideas as `raise a grievance`, `calculate the percentage of users`.
- **What v4 DID fix (so it was not wasted):** DATA_TYPE has **converged** — both annotators now sit at a
  median of 2.0 words on `17_pb`, and DATA_TYPE is the best-scoring label (F1 0.465). LABEL conflicts
  remain at 7 corpus-wide. Rules 7, 8 and 8b worked.
- **Root cause of the rule design itself (the transferable lesson):** Rules 7, 8, 8b are **countable**
  ("mark every occurrence", "this word is banned", "these entities are banned") and they held. Rule 1 —
  "the shortest phrase that still makes sense" — is **qualitative**, and two careful people read it
  differently. P4 was not careless; they were applying a vague rule honestly. **Qualitative annotation
  rules do not survive contact with two annotators.**
- **Decision — add Rule 9 (countable) and Rule 9b:**
  - **Rule 9:** a PURPOSE span is **at most 5 words** — the action plus its object. Drop the leading
    `to`/`for`; stop at the object, deleting every trailing `with…/within…/through…/of the…/during…`
    clause; then count. Includes a table of 8 worked before/after examples taken from the real round-2
    annotations, and a read-aloud sanity check ("does it name an activity, or is it a contract clause?").
  - **Rule 9b:** `data`/`information` with a modifier are still umbrella terms unless the modifier names a
    specific financial item. Mark `credit information`, `transaction data`; do not mark `client data`,
    `data received from an FIP`, `data in an aggregated and anonymised form`. Round 2 showed the banned
    umbrella returning wearing a modifier.
- **Next action:** both annotators re-do **the same two documents again** under v4+Rule 9. Using the same
  documents gives a clean three-point comparison on identical text (0.492 -> 0.374 -> ?). The D31 decision
  table still applies (>=0.75 proceed / 0.60-0.75 proceed with a re-check / <0.60 stop).
- **Tooling note:** fixed a latent bug in `agreement_report.py`, `annotation_audit.py` and
  `adjudicate.py` — a relative `--out` path crashed on `Path.relative_to(PROJECT_ROOT)`. All three now
  resolve `args.out` first. `kappa.py` also gained `--docs` so a full Label Studio export can be scored
  on just the calibration documents (LS export ignores UI filters).
- **Status:** ⚠ Gate NOT met, second time. Rule 9 shipped; re-calibration on the same 2 docs is the
  team's next step. This is the LAST qualitative rule in the set — after Rule 9 every rule is countable.

### D33 — Summarizer switches to TEXT -> summary with NER fact checklists (supersedes P2.md "Option A")
- **Trigger:** P2 generated summaries with GPT and reported "30 lines in, 25 lines out" — almost no
  compression — and asked whether the NER annotations are needed to test summaries.
- **Diagnosis:** (1) GPT was given an un-bounded instruction ("summarise"), so it paraphrased. Same lesson as
  the annotation rounds (D29-D32): an instruction that cannot be counted gives unpredictable output.
  (2) "Lines" misled the comparison: corpus lines are PDF/HTML wrap fragments, median **9 words**, so
  30 lines is only ~270 words. (3) P2 was already doing text -> summary, not the agreed facts -> summary.
- **Decision — adopt text -> summary, and drop Option A.** Option A (linearized fact list -> verbalized
  summary) was the wrong design for the paper: when the input IS the fact list, entity preservation is
  nearly automatic, so the faithfulness audit — the project's claimed application (D28) — measures almost
  nothing. With real policy text as input the model must choose what to keep, which is what the audit is
  for, and it matches the nearest published work (EROS, arXiv:2403.00141) so the comparison is fair.
- **Countable rules for every reference (the fix for P2's problem):**
  - at most **25% of source words and at most 60 words**, 1-3 sentences, at least 12 words;
  - must keep **>= 80% of the chunk's fact checklist** (content-word overlap coefficient >= 0.6 per fact,
    reusing `relaxed_agreement.content_words`);
  - adds nothing absent from the text (enforced by the prompt; hallucination is measured later by the
    faithfulness audit).
- **Built `summ/build_dataset.py`:**
  - `chunks` — cuts the 23 docs into ~180-260-word chunks at section boundaries (T5's input limit is 512
    tokens; documents are 850-8,000 words), splits **by document** (13 train / 10 test), attaches a
    must-mention checklist per chunk from **silver** facts (auto-adjudication of `Export2A/B.json`,
    Rules 7/8/8b applied), writes 130 ready-to-send LLM prompts, and samples 30 test chunks
    (stratified across the 10 test docs) for P1/P4 to summarise by hand.
  - `validate` — accepts/rejects LLM references against the rules above, writes `train.jsonl` +
    `dev.jsonl` (10% for early stopping) + `rejected_train.jsonl` with reasons.
- **Validated end-to-end** on real chunks: 3 hand-written references accepted at **17% compression, 100%
  fact coverage**; a deliberately bad one (63 words vs cap 60, 0/3 facts) rejected for both reasons.
- **Methodology fix carried in:** P2.md's `train.py` skeleton early-stopped on `test.jsonl` — i.e. it would
  have tuned on the test set. Now a dev split from training data is used; the test set is opened exactly
  once, at the end (the project-wide rule).
- **NER dependency, answered:** training checklists use **silver** facts now (no waiting); the test set
  needs **gold** facts after adjudication plus P1/P4's handwritten references for the 30 sampled chunks.
  The doc-level `gold_refs.jsonl` hand-off of the old design is replaced by the chunk-level
  `test_to_summarise.jsonl`; only `{id, reference}` pairs are committed as `gold_refs.jsonl`.
- **Honest limits:** 130 training pairs is small (178 with `--min-facts 0`); training references are
  LLM-generated (distillation); silver checklists carry some context noise (e.g. `password` extracted
  from "password mining" in a prohibited-conduct clause).
- **Repo hygiene:** everything under `data/summ/*.jsonl` quotes scraped text and is git-ignored except
  `gold_refs.jsonl`. The dataset reaches P2 via Drive (`ConsentLedger_P2_summarizer_dataset.zip`).
- **Status:** ✅ Dataset built and shipped to P2. P2 runs the prompts through GPT, then `validate`, then
  trains. P2.md §4 rewritten; §2, §6 and §10 updated to match.

### D34 — Summarizer test set is REFERENCE-FREE; no handwritten test summaries (amends D33)
- **Constraint:** P1 and P4 can deliver the gold NER annotations but have no time to also hand-write
  summaries for the 30 sampled test chunks D33 asked for.
- **Decision:** drop handwritten test references. The headline metric never needed them: the faithfulness
  audit scores each generated summary against the **gold facts of its own source chunk** — coverage (gold
  entities kept), hallucination (entities the NER model finds in the summary that are absent from the
  source) and compression. This is the standard reference-free design for factual consistency, the same
  structure as the entity-level metrics already cited (arXiv:2102.09130).
- **Side benefit:** without per-chunk human effort the test set grows from a 30-chunk sample to **every
  test chunk with at least one gold fact** — 122 of 194 with the current annotations.
- **ROUGE / BERTScore become optional and SILVER:** `build_dataset chunks` now also writes
  `prompts_test.jsonl`; GPT references for test chunks may be used for ROUGE/BERTScore, reported explicitly
  as silver (they measure imitation of GPT, not quality). They were never the headline (plan B4).
- **Gold switch-over needs no new code:** passing the adjudicated gold export as both inputs
  (`--a gold.json --b gold.json`) makes every span count as agreed, so every checklist becomes gold.
  Tested: with identical inputs the builder labels the facts GOLD and scores 122/194 test chunks.
- **Removed:** the `test_to_summarise.jsonl` sample and its `--test-sample` flag.
- **Stated limitation:** no human judgement of summary quality (readability, usefulness).
- **Status:** ✅ Builder, P2.md (§2, §4a, §4d, §4e, §10) and the Drive pack updated.
- **Ownership addendum (recorded with D35):** the summarizer track belongs to P2. The dataset builder
  (`summ/build_dataset.py`) and the rewritten `P2.md` were delivered to P2 via Drive and are **not
  committed by P1**; how P2 builds, filters and trains on the dataset is P2's decision. D33/D34 stand as
  recommendations to P2, not as commitments in the repo. The only shared hook is the gold annotation
  export, which P1 hands to P2 privately.

### D35 — Rule 10: PURPOSE is defined by a closed list of 10 categories (guideline v6)
- **Evidence that forced it (round-2 calibration, `26_zerodha_tos` + `17_pb_fintech_aa_privacy`):**
  - PURPOSE entity-F1 **0.000** exact, only **0.138** under relaxed matching (any overlap, or function
    words stripped). If the disagreement were about span edges, relaxed matching would have jumped to
    0.6-0.8; it did not.
  - The annotators marked **different regions** of the same document: in `17_pb`, P1's ten purposes sit at
    offsets 6,671-9,581, P4's four at 222-1,984, with one shared. P1 marked 3 purposes in the whole
    `26_zerodha` ToS; P4 marked 12.
  - **A "no vague annotations" rule does not fix it — measured:** deleting every vague PURPOSE span from
    both annotators left exact F1 at **0.000** and dropped relaxed F1 to **0.087**. P1's purposes were
    specific (`respond to queries`, `send you notices`, `verification of identity`); P4 simply never looked
    there. The guideline already said "don't mark vague" in six places (Part A since v1, the Rule 8
    stoplist, Rule 9's examples), and `to fulfil the purpose` — listed verbatim as a do-not-mark — was
    still marked.
  - Root cause: "the reason data is used" is an **open** definition. In a 5,000-word policy dozens of
    sentences qualify and two careful people sample different ones. Every rule that worked (7, 8, 8b, 9)
    was a finite target; every rule that failed was a judgement.
- **Alternatives considered and rejected:**
  - *Drop PURPOSE from NER* (take purpose only from the ReBIT artefact) — rejected by P1, rightly: the
    artefact's `Purpose.code` is standardised but `Purpose.text` is **free-form** (the verified Sahamati
    example pairs code 103 with custom text), so the declared purpose cannot be trusted alone. Checking the
    policy prose against the declared code is a real verification the framework does not perform, and it is
    the paper's disclosure-fidelity application (D28).
  - *Use the five ReBIT codes (101-105) as the annotation definition* — too narrow: no slot for loan
    assessment, fraud checks, grievances, notices or marketing, which policies really describe; P1's
    correct round-2 purposes would have been excluded.
  - *Add a second label PURPOSE_OTHER for undeclared uses* — rejected by P1 (no new labels). Undeclared-use
    detection moves to analysis time instead.
- **Decision — Rule 10:** a PURPOSE span is marked only if it names an activity in one of **10 fixed
  categories**: (1) credit/loan assessment, (2) account monitoring & collection, (3) financial management &
  insights, (4) fetching/consolidating/sharing financial information — the AA service itself, (5) fraud
  prevention, security & verification, (6) legal & regulatory compliance, (7) customer support & grievance,
  (8) communication, (9) analytics & service improvement, (10) marketing & promotion. Four checks in order:
  activity (not a goal) -> fits a row -> not policy-generic -> at most 5 words (Rule 9). Same PURPOSE
  button; **no Label Studio change**. The earlier 9-category draft was missing row 9 (analytics), which
  would have excluded P1's correct `calculate the percentage of users`; row 4 absorbs the AA service itself.
- **Link to the verification idea:** rows 1-4 correspond to the ReBIT purpose codes; a policy whose text
  leans on rows 9-10 while declaring a narrow code is the mismatch to flag. Done in analysis, never by
  annotators.
- **Stop-loss (agreed in advance so it cannot be rationalised later):** P1 and P4 annotate the untouched
  `10_perfios_terms` fresh under v6, independently, and it is scored with both `kappa.py --docs` and
  `relaxed_agreement.py --docs`. kappa >= 0.6 and PURPOSE content-F1 >= 0.5 -> fix pass on all 23.
  kappa >= 0.6 but PURPOSE weak -> proceed, report PURPOSE with the relaxed metric plus a limitation.
  kappa < 0.6 -> proceed anyway with the guideline FROZEN; report the round-by-round kappa honestly and name
  PURPOSE as the hard label. **There is no calibration round 4** — every outcome leads to the fix pass.
- **Status:** ✅ Guideline v6 written (Rule 10 + label-table row + tricky cases). P4 needs the v6 guideline
  before the `10_perfios_terms` round.

### D36 — Full granular audit of all 23 documents -> Rules 11-22 (guideline v7); calibration doc switched
- **Why:** after Rule 10 the guideline covered the big decisions but was silent on many small ones, and
  every silent decision is a place where two annotators can diverge. Requirement: a rule for every
  granular decision, however small.
- **Method:** one pass over every span both annotators made in all 23 documents (`Export2A/B.json`:
  P1 1,761 spans, P4 933), measuring 20+ decision types — span edges, brackets, example lists,
  coordination, overlaps, data-flow context, the policy owner's own name, negation, modifier use (spaCy),
  headings, definitions, line crossings, label consistency, X-data/details phrases. The OPP-115 loader was
  also checked to fix the negation convention.
- **Findings -> rules (P1 / P4 counts; heuristic ones marked ~):**
  | Decision the guideline was silent on | P1 | P4 | Rule |
  |---|---|---|---|
  | space/punctuation at a span edge | 14 | 41 | 11 clean edges |
  | name + abbreviation in brackets/quotes, three different treatments | 30 | 30 | 12 stop at the bracket |
  | spans inside "such as / including" lists (P4 stops early) | 834 | 347 | 13 every list item; never the umbrella or "etc." |
  | coordinated PURPOSE spans (P1 splits, P4 lumps) | 19 | 83 | 14 shared-word lists = one highlight |
  | overlapping / nested / duplicate highlights | 0 | 12 | 15 never overlap; keep the outer span |
  | THIRD_PARTY in a sentence with no data-flow verb (~) | ~112 | ~98 | 16 THIRD_PARTY needs a data flow |
  | the policy's own company marked as THIRD_PARTY | 0 | 19 | 17 first party never marked (own staff too) |
  | spans in negated sentences, no rule either way | 508 | 276 | 18 negation/"may" do not matter |
  | data word used as the name of something else | 9 | 9 | 19 a word named after data is not data |
  | spans on heading-like lines (~) | ~67 | ~75 | 20 no headings; definitions are ordinary |
  | spans crossing a line break | 22 | 39 | 21 one highlight across wraps; glued text |
  | same phrase with >1 label (incl. clear mis-clicks) | 9 | 11 | 22 one phrase one label + colour check |
  | "X data / information / details" phrases | 160 | 109 | decision table (extends 9b) |
  Also: Rule 8 stoplist gains `stakeholders`, `persons`, `any person`, `entities`, `others`,
  `third-party entities`; Rule 2 gains the shared-word exception (points to Rule 14).
- **Rule 18 is grounded in the training data, and records a known deviation.** `load_opp115.py` extracts
  every DATA_TYPE / PURPOSE / THIRD_PARTY span regardless of the practice's Does / Does-Not attribute, so
  OPP-115 teaches the model that "we do **not** share with advertisers" contains a THIRD_PARTY. The AA
  annotation must follow the same convention or E1/E2 compares two different tasks. Note: the plan's
  mapping audit (Part E, correction 6) had recommended excluding negated modality from OPP-115; that was
  never implemented. Changing it now would mean re-running the whole E1 sweep, so the decision is to align
  the AA side to the loader instead. **Consequence for the verification idea:** polarity must be handled
  at analysis time — "we do not use your data for marketing" will be extracted as PURPOSE `marketing`,
  which must not be flagged as an undeclared use.
- **Self-correction:** Rule 10's worked example `prevention, detection, investigation` (cut from a longer
  phrase) contradicted the new shared-word rule. Replaced with `fraud detection and prevention` (one
  highlight; the items share "fraud").
- **Glued-text defect found in the corpus, and the calibration document changed because of it.**
  `clean.py` lost spaces in some PDF-extracted documents (`anyinformationprovidedbyyou`,
  `andcontactinformation`, `courts atBengaluru`). Signals: `02_digio_terms` 40 comma-glued + 29 tokens of
  20+ letters; `10_perfios_terms` 29 + 46; minor in `25_the_financiali_privacy`, `01`, `04`; 149 total.
  **`10_perfios_terms` — chosen in D35 for the independent calibration round — is one of the two worst,**
  so calibrating on it would measure an extraction bug, not the guideline. **The calibration document is
  switched to `23_upmint_aa_tos`** (14k chars, balanced round-1 counts, no glued signals). Rule 21 tells
  annotators how to handle glued text meanwhile. **Do not re-clean the two affected documents
  mid-annotation:** re-cleaning shifts every character offset and would invalidate both annotators'
  existing spans on them; the fix belongs in `clean.py` plus a re-annotation (or offset remap) of those
  two documents only.
- **Not added (already covered or negligible):** pronouns/anaphora (0 spans marked — Part A's vague-word
  rule is being followed), leading determiners (Rule 1; 4 spans), durations inside DATA_TYPE (Part A;
  1-2 spans).
- **Heuristic limits:** the data-flow (Rule 16) and heading (Rule 20) counts come from pattern matching and
  are approximate; the rules themselves do not depend on those counts.
- **Tooling gap — CLOSED (same day):** `fixlist.py` now emits three more mechanical buckets:
  **TRIM** (Rule 11 edges; Rule 12 cuts a bracketed tail only when it holds an abbreviation or expansion,
  so `Government Securities (Tradable)` is left alone), **OVERLAP** (Rule 15: duplicate / nested /
  overlapping / same-words-two-labels, keep the outer span) and **OWN_COMPANY** (Rule 17, using each
  document's real legal and brand names read from its own text — e.g. `08_pennydrop` is Shankar
  Fininvest, `19_saafe` is Dashboard Account Aggregation Services — plus own-staff words; a guard
  keeps `ICICI HFC group companies` and similar other-entity phrases unflagged). Trimming now runs
  BEFORE the stoplist check, so `"FIPs"` and `banks ` are judged as `FIPs` and `banks`.
  On the round-2 exports: P1 trim 33 / overlap 0 / own-company 0; P4 trim 59 / overlap 8 /
  own-company 38 — all 38 spot-checked as genuine (the audit's hand-guessed name list had found 19).
- **Two banned-list bugs found by the new self-check and fixed (in `adjudicate.py`, shared by all
  tools):** (1) Rule 8b listed only SINGULAR AA roles, so `FIPs`, `Financial Information Providers`,
  `Account Aggregators` slipped through; plurals added, plus `information user(s)` / `IU`.
  (2) The umbrellas that Rules 9b/13 already ban were not in the machine list —
  `personally identifiable information`, `sensitive personal information/data`, `personal details`,
  `technical data` — nor the v7 generic-group words (`stakeholders`, `persons`, `entities`, ...).
  The tools now enforce exactly what guideline v7 says.
- **Status:** ✅ Guideline v7 written (Rules 11-22, decision table, stoplist row, Rule 2 exception, Rule 10
  example fixed, tricky cases). Next: calibration on **`23_upmint_aa_tos`** under v7 (the D35 stop-loss
  table is unchanged — only the document changes).

### D37 — A PURPOSE needs a data-use frame: your rights and procedures are not purposes (guideline v7.1)
- **Trigger:** P1 pointed out that `raise a grievance` is not a PURPOSE — it does not say why any data is
  collected or shared. In `26_zerodha_tos` it sits in a list of the client's rights ("to raise a grievance
  with the grievance resolution officer of the FIU; to … revoke any consent …; and to deregister from any
  AA"). **P1 was right.**
- **The error was mine, in five places:** Rule 9's example table offered `raise a grievance` as a correctly
  shortened purpose; Rule 10 row 7 listed it; Rule 10's worked examples marked it ✅; and two tricky-case
  lines used it or blanket-approved `grievance redressal` / `dispute resolution`. Root cause: Rule 10
  check 1 asked "is it an activity?" — never *whose* activity, nor whether it involves *your data*. That
  also contradicted D35's own ruling that `to deregister from any AA` (a user right) is not a purpose.
- **Evidence — every grievance / dispute / complaint / consent-right PURPOSE span both annotators made,
  read in its sentence (Export2A/B):**
  - **P1: 8 distinct contexts, all with a data-use frame** — e.g. 08_pennydrop's list of purposes
    ("Addressing grievances and disputes"), 19_saafe "consent records and logs are retained… including for
    … dispute resolution", 24_credbuddha "may maintain records… for purposes including… dispute
    resolution" and "retain, process, use or disclose information where required for…".
  - **P4: 14 distinct contexts, 13 of them rights or procedures** — "the customer may revoke consent",
    "a Grievance Redressal Policy that sets processes and timelines for handling complaints", "dispute
    resolution provisions will survive termination", the heading `Grievance Redressal`, zerodha's rights
    list. One genuine (25_the_financiali "Legal Basis for Processing… audit and grievance redressal").
  - So this is another systematic P1/P4 split, and **P1 was already applying the right test implicitly.**
- **Why not ban the words:** a blanket rule would delete P1's 8 correct spans. The words never decide; the
  sentence does — `dispute resolution` is a PURPOSE in "maintain records… for purposes including dispute
  resolution" and is not one in "dispute resolution provisions shall survive termination".
- **Decision — Rule 10 check 1 rewritten (the PURPOSE twin of Rule 16):** *does the text say the company
  uses, keeps or shares your data FOR it?* — in its own sentence or in the lead-in of the list it sits in
  ("we use your information for…", "retained for…", "processed on the following grounds…"). Fails: a goal
  or state (`maintaining your privacy`); something **you** do — your rights (`raise a grievance`,
  `file a complaint`, `revoke consent`, `deregister`, `access a record of your consents`); a procedure,
  commitment, contract clause or heading. Row 7 narrowed to "customer support, complaints & disputes —
  only where the text says your data is used or kept for it". Examples replaced with real ones of both
  kinds; tricky cases qualified; Part G2's warning no longer cites `grievance redressal` as always-correct.
- **Tooling (`adjudicate.py`, `fixlist.py`):** a `CONTEXT_PURPOSE` pattern (grievance, complaint, dispute,
  revoke/revocation, deregister, withdraw consent). The tools never assert these automatically: no
  consensus auto-accept, no Rule 7 propagation, no ADD_REPEAT / ADD_MISSED suggestions. Instead each
  annotator's existing ones go to a new judgement bucket **PURPOSE_CHECK**, quoted with their sentence.
  On the round-2 exports this removed **73 (P1) and 67 (P4) automatic "add this PURPOSE" suggestions**,
  many in procedure sentences, and routed 10 (P1) / 15 (P4) existing spans to PURPOSE_CHECK.
- **Note for P4:** the v5 fix-pack README called `grievance redressal` always correct — superseded; P4 needs
  guideline **v7.1** before the `23_upmint_aa_tos` round.
- **Status:** ✅ Guideline v7.1, tools updated (self-checks pass), bible updated.

### D38 — E1 sweep complete: no backbone winner; seed spread is not significance
- **Result (OPP-115 dev, 3 backbones x 3 seeds, all 9 runs present — every group `x3`, so the
  missing-seed guard stayed silent):**
  | backbone | entity macro-F1 (mean +/- std) | token-F1 |
  |---|---|---|
  | nlpaueb/legal-bert-base-uncased | 0.3996 +/- 0.0059 | 0.5220 +/- 0.0083 |
  | law-ai/InLegalBERT | 0.3862 +/- 0.0028 | 0.5133 +/- 0.0080 |
  | bert-base-uncased | 0.3816 +/- 0.0025 | 0.5262 +/- 0.0014 |
  Consistent with the single-seed 0.38 that validated span-trimming (D25).
- **How it must be reported:** (1) the ranking **flips** between metrics (Legal-BERT leads on entities,
  BERT-base on tokens) — the textbook sign of no clear winner, so per the pre-registered honesty rule
  (plan B3) no backbone is crowned; (2) the +/- is over **seeds**, measuring training randomness only — it
  is **not** a significance test. Significance comes from bootstrap confidence intervals over
  **documents**, computed on the AA test set; with a 12-document dev set those intervals will be much
  wider than the seed spread.
- **Status:** ✅ E1-on-dev done. These are diagnostic; the headline is E1/E2 on the AA gold test set.

### D39 — Correct the corpus by editing; measure agreement on an untouched document
- **Trigger:** after round-2 calibration P1 asked whether P4 alone had to change, and whether P4 could just
  edit existing annotations to the new rules instead of re-annotating.
- **Evidence:** on the two calibration documents P4 had **27** violations of Rules 8/9/9b (13 PURPOSE spans
  over 5 words, 9 umbrella `data`/`information`, 5 stoplist) against P1's **2**. Corpus-wide, though, P1 had
  work too — **81** Rule 9/9b violations and ~230 stoplist deletions in the 21 documents still carrying
  round-1 annotations.
- **Decision (P1's):** split the two jobs. **Fixing** the corpus is done by **editing** (the per-annotator
  fix pass) — far faster than re-annotating. **Measuring** agreement for the paper is done on a document
  **neither annotator has touched**, annotated fresh and independently. Reason: Rule 9 was derived by
  comparing the annotators and effectively follows P1's style, so if P4 edits towards it, agreement rises
  partly because P4 converged on P1 — that would inflate kappa and be circular as an agreement statistic.
  Applying a written rule is legitimate; imitating the other annotator is not.
- **Document choice:** `10_perfios_terms` was picked first (most balanced round-1 counts), then replaced by
  `23_upmint_aa_tos` when the glued-text defect was found (D36).
- **Status:** ✅ Agreed; the independent round is the next step.

### D40 — Repo hygiene record: what is committed, what is shared privately
- **Principle:** anything that quotes scraped document text is never committed (no-redistribution, as
  for `data/aa/raw/`); numbers-only summaries are. The bible's section 9 lists every output with its status.
- **Correction of earlier advice:** the annotation exports were first suggested for committing as kappa
  provenance. They embed the full document text (e.g. 13.5 KB of the ICICI policy in a single pilot
  export), so they are git-ignored (`[Ee]xport*.json`, `[Gg]old.json`); the provenance is
  `results/annotation/kappa.json`, which holds only doc ids, counts and kappa.
- **`proposed_gold/` excluded from commits:** it is a machine merge built from the *failed* round-1
  annotation, and its name sits one word from "gold" — a teammate could mistake it for the answer key. It
  is committed only after it is regenerated from the round-2 exports.
- **A near-leak, closed:** the round-2 diagnosis written with `--out results/annotation/round2_calib`
  produced a `docs/` folder quoting document text that the ignore rule (written for the default folder
  only) did not cover. Caught before commit; the rule is now `results/annotation/*/docs/` so any report
  folder is covered.
- **Summarizer hand-off mechanics (P2's track, D34 addendum):** `src/consentledger/summ/build_dataset.py`
  is kept out of P1's commits by a **local-only** entry in `.git/info/exclude` (not shared, so P2 can
  commit their own version); the rewritten `P2.md` went to P2 by Drive and the repo copy was restored to
  its last committed version. `data/summ/*.jsonl` is ignored (quotes text) except `gold_refs.jsonl`.
- **Every commit was preceded by a staged-file check** for exports, gold, import file, `docs/`,
  `per_doc/`, `worklist/`, `fixlist/P*/`, `proposed_gold/` and `data/summ/` — all clean.
- **Status:** ✅ In force.

### D41 — Round-3 calibration (kappa 0.283) -> fix pass, guideline frozen; fix lists stop guessing
- **Result (`23_upmint_aa_tos`, Export3A/B, v7.1):** token kappa **0.283**; entity F1 0.267 (DATA_TYPE 0.414,
  PURPOSE 0.167, THIRD_PARTY **0.000** — P4 marked none); relaxed CONTENT micro-F1 0.367, PURPOSE 0.333.
  History: 0.279 (round 1, 23 docs) -> 0.374 (round 2, 2 docs) -> 0.283 (round 3, 1 doc).
- **Decision:** per the stop-loss agreed in advance (D35), kappa < 0.6 -> **proceed to the fix pass with the
  guideline FROZEN; no round 4**. Report the round-by-round kappa honestly; PURPOSE is the hard label.
- **Diagnosis — compliance, not clarity.** Applying only already-written rules to each annotator's spans
  (no judgement calls changed): P1 fixed 0.298, P4 fixed **0.547**, both 0.584, both + P4 marking the 5
  Rule-16 third parties **0.717**. P4: leading `to`/`for` kept on every PURPOSE (Rule 9), umbrellas
  (Rules 8/9b), contract clauses as PURPOSE (Rule 10 checks 1/3, incl. the D37 case), skipped repeats
  (Rule 7), no THIRD_PARTY despite explicit disclosures (Rule 16). P1: indemnity `affiliates`/`agents`
  (Rule 16), `pursuant to valid legal process` as PURPOSE. Action: confirm P4 is working from v7.1.
- **Caveat:** not a blank document — 22/28 (P1) and 16/32 (P4) spans identical to round 1, and the Export2
  fix lists covered it. Reported as calibration round 3, not as D39's untouched-document measurement.
- **Open ambiguities, ruled on at adjudication (guideline frozen):** the bracketed abbreviation itself
  (`("KYC Documents")`; Rule 12 vs Rule 20); status adjectives (`registered email address`); communication
  items as PURPOSE (`OTPs`, `alerts`); `regulators` in an explicit disclosure sentence (Rule 16 vs 8b).
- **Tool correction (`fixlist.py`):** ADD_MISSED, labelled "mechanical", was wrong 6/7 (P1) and 7/10 (P4)
  on this document — word matching without meaning (`title`, `assets`, nested `service providers`,
  indemnity `affiliates`). Now: no suggestion inside/overlapping another (Rule 15); THIRD_PARTY suggested
  only with a data-flow verb in the sentence, span blanked (Rule 16); new bucket **1e THIRD_PARTY_CHECK**
  (sample: ~22/24 genuine); ADD_MISSED is a check-in-context bucket with the sentence, not mechanical;
  `provide the services` added to the stoplist. Selfchecks cover all three.
  Export3 fix lists: mechanical P1 953 / P4 758; check-in-context P1 307 + 132 / P4 459 + 90.
- **Also:** `relaxed_agreement.py` crashed on a relative `--out` (the D40-era resolve fix had missed it) —
  fixed. `results/annotation/kappa.json` now holds the round-3 single-document result;
  `relaxed_round3.json` holds its relaxed scores.
- **Status:** ✅ Fix lists regenerated from Export3. Next: P1/P4 fix pass on all 23 -> Export4A/B ->
  full-corpus kappa -> adjudicate -> gold.

### D42 — Round-3 was a process failure, not a guideline test: one fresh document (deviation from D35/D41)
- **Fact established:** P4 confirmed they did **not** have guideline v7.1 when annotating `23_upmint_aa_tos`.
  So round 3 measured an annotator *without* the guideline, not the guideline. That matches the D41
  diagnosis (P4's errors were all against already-written rules).
- **Decision (P1's):** one fresh, independent document under v7.1 — **`25_the_financiali_privacy`**.
  This **deviates** from D35/D41 ("no round 4"); the deviation is justified only by the process failure
  above and is logged *before* any annotation, so it cannot be rationalised afterwards. Had P4 had v7.1, the
  answer would have been no.
- **Why it is worth it:** the post-fix-pass full-corpus kappa is not fully independent — ADD_MISSED
  suggestions come from the consensus lexicon, built from *both* annotators' spans. A blank document
  annotated separately under the final guideline is the cleanest agreement number the paper can report.
- **Document choice:** 2,888 words, all three labels in quantity, a privacy policy (rich in data-flow
  sentences that test Rule 16); not diagnosed span-by-span (unlike upmint, `17_pb_fintech`, `26_zerodha`,
  `29_icici`); no glued text (unlike `02_digio`, `10_perfios`).
- **Protocol (fixed now):** (1) both read v7.1; any sync discusses rules only, never upmint's spans or the
  diff output; (2) start from **blank** — delete all existing spans on doc 25 first, do not edit round-1
  work (on upmint P1 kept 22/28 old spans); (3) annotate before the fix pass; do not open doc 25 in either
  fix list; no discussion of doc 25 until both have submitted; (4) export the whole project as
  Export4A/B (JSON), score with `kappa.py --docs 25_the_financiali` and `relaxed_agreement.py --docs`;
  (5) **the result is final** — reported with every round (0.279 -> 0.374 -> 0.283 -> round 4); **no round
  5**; below 0.6 still goes to the fix pass with PURPOSE named as the hard label.
- **Repo note found while logging — fixed:** D41's `fixlist.py` / `adjudicate.py` changes (THIRD_PARTY_CHECK
  bucket, Rule 15/16 suppression in ADD_MISSED, `provide the services` stoplist entry) and the bible's
  section 5.9.12 had been lost from the working tree — the files were back at commit `eebaea7` one minute
  after the Export3 fix lists were generated. All were **restored by replaying the original edits from the
  session transcript**; selfchecks pass, and regenerating from Export3 reproduces the on-disk fix lists
  item for item (same counts: P1 953/307/132/10, P4 758/459/90/14). Two small fixes on top: suggestion
  order was hash-seed dependent (equal-length phrases) — now sorted, so two runs are byte-identical; and
  `--out` outside the repo no longer crashes the final print.
- **Status:** ⏳ P4 annotating doc 25 under v7.1; P1 to annotate doc 25 from blank.

### D43 — Round 4: kappa 0.522 (final); rulings for the fix pass -> guideline v7.2
- **Result (`25_the_financiali_privacy`, Export4A/B, both on v7.1, independent):** token kappa **0.522**;
  entity F1 0.457 (DATA_TYPE 0.532, PURPOSE 0.384, THIRD_PARTY 0.419); relaxed CONTENT micro-F1 **0.590**
  (DATA_TYPE 0.596, **PURPOSE 0.658**, THIRD_PARTY 0.465). Spans: P1 91, P4 119.
  History: 0.279 (round 1, 23 docs) -> 0.374 (round 2, 2 docs) -> 0.283 (round 3, P4 without v7.1)
  -> **0.522 (round 4)**. Per D42 this number is **final** — no round 5; it goes to the fix pass.
- **What the number says:** with the guideline in both hands, agreement nearly doubled. PURPOSE, the
  failing label of rounds 2-3, is now the *strongest* under relaxed matching; **THIRD_PARTY is the hardest
  label**, driven by regulators in disclosure lists and AA/registrar names (Rules 8b/16).
- **Who diverged:** both, as a genuine measurement should show. P1: missed recipients (Amazon Web
  Services, Google APIs, GA4/GTM at first mention); `Gmail OAuth` (a mechanism) and `Gmail data` x3
  (Rule 9b); `required for KYC` too long; `audit and grievance redressal` should be two spans (Rule 2);
  `connection with any merger`. P4: `To` kept on 5 PURPOSE spans (Rule 9); `provide, …` edge (Rule 11);
  named AAs, `RBI`, `SEBI` inside a regulation's name, registrars CAMS/KFintech (a data *source*, Rule 16)
  as THIRD_PARTY; umbrellas (`Financial information`, `data categories`, `device and usage data`,
  `financial details`); Rule 14 splits (`mutual fund` + `demat holdings`, `detect` + `investigate and
  prevent fraud`); bracket included in `FIU-IND` (Rule 12); missed the service-provider list.
- **Corrections of my own analysis:** I first called P1's skipped telemetry list (IP address, browser
  type…) an under-marking. **P1 was right** — telemetry is observed, not provided (ruling (a)); P4's
  10 telemetry spans were the violation (removing them alone: kappa 0.522 -> 0.549). I first told P1 to
  delete `required for KYC`; it is a genuine PURPOSE, only too long. I told both to mark `Successor
  entities`; it is a table row label, which Rule 20 excludes — both annotators had treated all five labels
  alike. And the inference that "spans identical to round 1" proves editing rather than blank annotation
  was weak: blank annotation reselects `name` at the same offsets (doc 25: P1 57/91, P4 37/119 identical).
- **Rulings (P1's) -> guideline v7.2 (Rule 23, Rule 10 row 11, decision table):**
  - **The principle (P1 resolved the dilemma, D43 addendum): PROVIDED data is a DATA_TYPE, OBSERVED data
    is not** — not "is it financial?". `email address` and `mobile number` are not financial and are
    marked; the Rule 8 bank-record test is a specificity check against umbrella words, not a financial-only
    filter. My first justification for (a), "fails the bank-record test", was therefore wrong (it would also
    exclude `email address`) and was replaced; the rulings themselves are unchanged.
  - **(a) Observed device/usage telemetry is never DATA_TYPE** — emitted by the device, never handed over;
    and boilerplate common to nearly every web policy, so it says nothing about the company (Rule 10
    check 3's reasoning; Rule 8b cookies). Paper: OPP-115 labels it, so E1 predictions of it count as
    false positives on AA gold — a deliberate scope choice that surfaces as measurable domain shift.
    Added to the stoplist, so the fix lists delete it mechanically.
  - **(b) Communication content you send IS DATA_TYPE** — emails, WhatsApp messages, call recordings, chat
    messages, form inputs, survey responses. Test: did *you* produce it, or did your device emit it?
  - **(c) `KYC` is a PURPOSE only by context** — data collected/used for it (`where required for KYC` ->
    `KYC`, row 5); `KYC records` DATA_TYPE; `KYC/AML verification providers` THIRD_PARTY; `KYC process`
    nothing (Rule 19); heading nothing (Rule 20).
  - **(d) A table row label on its own line is a heading** (Rule 20): mark the items under it.
    *Superseded by D45 — row labels and headings are ordinary text.*
  - **(e) Row 11 — corporate transactions** (`merger`, `acquisition`, `reorganization`, `sale of
    assets/business`), only with a data-use frame. Evidence: 8/23 documents use such words, but only **3**
    describe your data moving because of one (`19_saafe_privacy`, `25_the_financiali_privacy`,
    `28_indifi_capital_privacy`); the rest are contract assignment (`23_upmint`), loan restructuring,
    insolvency declarations, "customer acquisition". It earns a row despite the small count because
    OPP-115 has a *Merger/Acquisition* purpose (an E1 model will predict it, so gold must be able to hold
    it), and transferring your data in a merger is a use *beyond* any declared ReBIT code — the mismatch
    the project exists to flag (rows 9-11).
  - **Decision-table conflict fixed:** `device information` and `location data` had been listed as *mark*,
    contradicting Rule 8b; both moved to *do not mark*.
- **Measurement integrity:** these rulings came *after* the round-4 measurement and apply to the fix pass.
  Round-4 kappa is reported as measured under v7.1; v7.2 touches about one span on doc 25 (`merger`), so
  the number is not materially affected. Stated in the paper.
- **Still open, for adjudication:** regulators in an explicit disclosure list (`SEBI, RBI, the Income-tax
  Department…`; upmint's `regulators`) — Rule 16 says mark, Rule 8b names RBI; plus D41's bracketed
  abbreviation and `registered email address`.
- **Tools:** stoplist + telemetry; `CONTEXT_PURPOSE` now includes `kyc` and the row-11 words, so they are
  never auto-added or propagated (`customer acquisition` stays safe) and are listed for a sentence check
  instead. Fix lists regenerated from **Export4** (doc 25 changed): mechanical P1 943 / P4 769;
  check-in-context P1 299 + 132 + 23 / P4 444 + 89 + 20. Selfchecks pass. `kappa.json` holds round 4;
  relaxed scores in `relaxed_round4.json`.
- **Status:** ✅ Guideline v7.2 — send to P4. Next: fix pass on all 23 from the Export4 fix lists ->
  Export5A/B -> full-corpus kappa -> adjudicate (open items above) -> gold.

### D44 — Audit of the fix lists against every rule; seven detectors added, four bugs fixed
- **Trigger:** P1 asked for every update to be rechecked and for the fix lists to cover every case, edge
  cases included, so the corrected corpus generalises.
- **Method:** (1) a rule-by-rule coverage matrix (Rules 1-23 vs buckets); (2) each candidate detector
  probed on Export4 *before* being added, keeping only those with high precision; (3) **recall** measured
  against the problems found by hand on round-4 doc 25 (D43); (4) **precision** by sampling each new
  bucket across all 23 documents.
- **Bugs found and fixed:**
  1. **Errors were being multiplied.** ADD_REPEAT copied *any* of an annotator's phrases to every other
     occurrence — P4's `SEBI`, marked once inside a regulation's name, was proposed **16** more times.
     Now copies come only from spans no rule doubts, and each copy is re-checked at its own position
     (Rules 16/19/20). Effect on Export4: P1 604 -> 518, P4 389 -> 253 repeat suggestions.
  2. **The same flaw in the gold builder.** `adjudicate.py` auto-accepted and propagated THIRD_PARTY spans
     with no Rule 16 check, so an indemnity `affiliates` could enter gold. Now: agreed-but-doubted spans go
     to a new human bucket (REVIEW_RULE); consensus accept and Rule 7 propagation skip doubted positions.
     The Rule 16/19/20 helpers moved into `adjudicate.py` so both tools apply one definition.
  3. **`financial data` was on the Rule 9b keep-list**, contradicting the decision table — removed;
     `financial data`, `financial details`, `data categories` added to the stoplist.
  4. **Suggestions on field labels and inside deleted spans:** `address` x8 proposed in the company's
     footer ("Registered Address: …"), `CAMS` inside a deleted `CAMS Finserv`. A word followed by a colon
     is never suggested; nothing is suggested over a deleted span. Duplicate highlights are reported once.
- **Detectors added** (each with a selfcheck built from the real failure):
  | bucket | rule | what it catches |
  |---|---|---|
  | 1 DELETE (extended) | 8b, 9b, 23a | named AAs; telemetry *variants* by pattern (`type of browser`, `IMEI`, `web beacons`, `flash cookies`) |
  | 1b TRIM (extended) | 1, 9, 12 | leading `your/the/any`; leading `to/for` on PURPOSE (39 in Export4); bracket with hyphen `(FIU-IND)` |
  | 1e THIRD_PARTY_CHECK (extended) | 16, 19 | data comes FROM them (`from registrars (CAMS)`); part of a law's name (`SEBI (…) Regulations`) |
  | 1f RELABEL | 22 | a phrase you label differently everywhere else (`passwords`, `mobile number` as THIRD_PARTY) — needs >= 2 uses |
  | 1g HEADING_CHECK | 20, 23d | section headings (`8. Cookies`) and table row labels; lettered list items excluded |
  | 3b RULE23_ADD | 23b, 23c | communication content and `for KYC` left blank (check in context) |
  | 4e LIST_CHECK | 2, 14 | a list you split and they joined, or vice versa |
- **Measured recall on doc 25:** P1 **7/10**, P4 **19/22** of the hand-found problems are now in the fix
  lists. Every miss is the same kind: a recipient the annotator did not mark at all and no rule points to
  (`Amazon Web Services`, `payment processors`, `CRM platforms`). Only the other annotator's highlight
  reveals those; they surface at adjudication (REVIEW_ONESIDED). The guideline now tells annotators to read
  each document once more end to end after the list.
- **Measured precision (samples across 23 docs):** TRIM, DELETE, RELABEL ~100%; THIRD_PARTY_CHECK ~7/9 (misses
  list items whose data-flow lead-in is several lines up); RULE23_ADD mixed (`correspondence` in an
  arbitration clause) — which is why it is a check bucket, not mechanical.
- **Deliberately not automated:** Rule 13 completeness beyond the lexicon, Rule 18 (nothing to check),
  Rule 21 glued words, and showing an annotator the *other's* spans (would converge the two exports and
  hollow out the post-fix kappa — that comparison belongs to adjudication).
- **Guideline (still v7.2, no rule changed):** label table says 11 PURPOSE categories and "data you
  provide"; Rule 8 test clarified as a specificity test; PART G2.3 rewritten for all 15 buckets (it listed 5
  and still said ADD_MISSED was automatic); 11 round-4 tricky cases added, including one new micro-ruling:
  the company's own contact block (`Registered Address:`, `Contact Details:`) is not your data.
- **Open (P1 to decide) — decided in D45:** a table row label that is itself a **named organisation** — `PostHog` above
  "— for product analytics…" in doc 25. Rule 23d says labels are not marked, but here the label *is* the
  recipient and appears nowhere else. Proposed: 23d applies to *category* labels (`Service providers`,
  `Successor entities`); a *named* organisation as a row label is marked.
- **Export4 totals:** mechanical P1 901 / P4 665; check-in-context P1 498 / P4 559; selfchecks pass.
- **Status:** ✅ Fix lists regenerated. Next: send P4 v7.2 + their fix list; fix pass.

### D45 — Headings and table row labels are ordinary text (guideline v7.3)
- **Trigger:** D44 left open whether a *named organisation* used as a table row label (`PostHog` above
  "— for product analytics…", doc 25) is marked. P1 decided: **yes** — and went further: **phrases in headings
  can be marked too.**
- **Decision (P1's):** Rule 20's "never highlight headings" and Rule 23d (D43 d) are replaced by one rule: a
  phrase in a heading, title or table row label is marked **exactly like the same phrase in a sentence — if
  it passes every other rule**. Rule 7 ("every occurrence") now includes headings.
- **Why it is sound:** (1) NER marks *mentions*, not claims — the reason negated mentions are already marked
  (Rule 18); a heading is a mention. (2) It removes a judgement two annotators made differently ("is this a
  heading?" — round 1 found ~70 heading-line spans each, treated three ways). (3) The other rules still filter
  most headings: `8. Cookies` (23a), `Data Retention` / `Grievance Redressal` (no data-use frame, Rule 10),
  `Personal Information We Collect` (Rule 8). What changes is mostly specific data headings (`KYC Documents`)
  and recipient row labels.
- **Reverses D43 (d):** `Successor entities` — which P1 had rightly left unmarked under v7.2 — is now
  **THIRD_PARTY**. The table's lead-in ("Your personal data may be shared with the following categories of
  recipients") supplies the Rule 16 flow for every row. Rulings for all 9 row labels in the corpus (all in
  `25_the_financiali_privacy`; no other document has such a table):
  | row label | v7.3 |
  |---|---|
  | `Google Analytics 4 and Google Tag Manager` | `Google Analytics 4`, `Google Tag Manager` — THIRD_PARTY (two, Rule 2) |
  | `PostHog` | THIRD_PARTY |
  | `Service providers`, `Professional advisors`, `Successor entities` | THIRD_PARTY |
  | `Authorised personnel` (within Finfam…) | not marked — the company's own staff (Rule 17) |
  | `Regulated intermediaries` (— "RBI-licensed Account Aggregators…") | not marked — it names the AAs (Rule 8b) |
  | `Partners` | not marked — stoplist (Rule 8) |
  | `Regulators and authorities` | open — the regulator question still pending (D43) — *marked, per D46* |
- **Measurement integrity:** round 4 (kappa 0.522) was measured under v7.1, where both annotators left all
  labels unmarked alike; v7.3 applies to the fix pass. Reported as a post-measurement guideline change.
- **Tools:** the heading detector (HEADING_CHECK bucket; heading guards in suggestion, propagation and
  adjudication) is **deleted** — with headings ordinary text, nothing needs detecting. Suggestions now reach
  headings and row labels like any text (doc 25: `Service providers` and `PostHog` row labels proposed; the
  other labels above are not in either annotator's vocabulary yet, so they are listed here instead of
  building a detector for one document). Selfcheck: a row label under a sharing lead-in passes Rule 16 and
  its repeats are proposed. Fix lists regenerated: mechanical P1 913 / P4 669.
- **Guideline v7.3:** header, Rule 20 (with a table of how the other rules still filter headings), Rule 23c
  (`3.1 KYC` heading — not marked because it has no data-use frame), Rule 23d, PART G2.3 item 8, tricky cases.
- **Status:** ✅ Send P4 **v7.3** + regenerated fix list. Both: add the row labels above on doc 25.

### D46 — The last three open questions settled (guideline v7.4)
- **Context:** D41/D43 left three ambiguities for adjudication. Settling them *before* the fix pass means both
  annotators apply them across all 23 documents instead of meeting them again as disagreements.
- **1. Regulators (P1's ruling):** an authority named in an explicit disclosure is THIRD_PARTY (Rule 16) —
  **except organisations that are part of the AA pipeline itself**: `RBI`, and now `SEBI`. I extended the same
  class to the framework's other two financial-sector regulators, `IRDAI` and `PFRDA`, so the rule is "the four
  AA-framework regulators", not a list of two. Marked: `law enforcement`, `government authorities`, the generic
  word `regulators`, `Income-tax Department`, `Financial Intelligence Unit`, `exchanges`, `courts`, and the row
  label `Regulators and authorities` (resolves the row left open in D45). Tool: the four regulators (and full
  names) added to the Rule 8b set — deleted mechanically.
- **2. Bracketed abbreviation (P1's proposal, adopted over my suggestion):** I had proposed *not* marking the
  abbreviation inside the bracket. P1 proposed marking it as a separate highlight — another repetition. **P1's
  version is the consistent one:** Rule 12 already marks every later standalone `PAN` (Rule 7), so skipping only
  the bracketed one would label the same token an entity everywhere except in brackets — the contradictory
  training signal Rule 7 exists to prevent. It is also what both annotators did unprompted on upmint
  (`("KYC Documents")`). Rule 12 rewritten: **two highlights, same label** — the name, and the abbreviation or
  expansion inside the bracket/quotes; never one highlight that includes the brackets. Banned abbreviations
  stay banned (`FIP`, `PII`…), as does a bracketed umbrella (`("Registration Information")`).
- **3. Status words (P1's ruling):** dropped — `registered email address` -> `email address` (Rule 1). List:
  *registered, verified, valid, updated, latest*. Deliberately **not** *permanent, current, primary*: those are
  part of real field names (`Permanent Account Number`, `current address`, `Primary Account Number`).
- **Tools (`fixlist.py`, `adjudicate.py`):** status words trimmed on DATA_TYPE (2 in Export4); a highlight that
  swallowed its bracket is still trimmed, and the bracket's content is now proposed as its own highlight —
  also when the name was marked without it; three-letter abbreviations (`PAN`, `OTP`, `UPI`) are now proposed
  as repeats, which the 4-character floor had silently blocked, but only where written in capitals. 48 such
  additions in Export4; a sample was nearly all correct. Two noise cases found and guarded: `KYC` is never
  copied automatically (Rule 23c — context decides), and an umbrella in a bracket is never proposed. Tests
  that used `SEBI` for the law-name check now use `UIDAI`, since `SEBI` is deleted outright. Selfchecks pass.
  Fix lists regenerated: mechanical P1 929 / P4 693.
- **Known limit:** a repeat can land on the *company's own* identifier ("bearing CIN … and PAN AABCS7056E");
  the annotator skips it under the D44 contact-block ruling.
- **No open annotation questions remain.** Guideline **v7.4** is the version for the fix pass.
- **Status:** ✅ Send P4 v7.4 + regenerated fix list; begin the fix pass.

### D47 — A DATA_TYPE context gap found mid fix pass: deferred to adjudication, guideline NOT changed
- **Trigger:** during the fix pass P1 noticed the fix list proposing `password` / `username` in sentences
  P1 had deliberately not marked.
- **Evidence (Export4):** P1 marks credentials 17 times, every time in a sentence where the company collects
  or handles them ("…such as your first and last name, username… passwords"); never in a duty sentence
  ("You are solely responsible for maintaining the confidentiality of your username and password") or an
  attack sentence ("password mining"). P4 marks them 54 times, roughly half in duty/attack sentences
  (estimate from a keyword match; it over-counts denied practices such as "shall not request, access or
  store your login credentials", which *are* data practices under Rule 18).
- **The gap:** THIRD_PARTY has a context rule (Rule 16, data flow) and PURPOSE has one (Rule 10 check 1,
  data-use frame); **DATA_TYPE has none**, only Rule 19 for names like "password mining". P1's reading also
  matches the training data: per `NER_LABEL_MAPPING.md`, OPP-115 `Personal Information Type` spans come only
  from First Party Collection/Use and Third Party Sharing/Collection statements.
- **Proposed rule (not yet in the guideline):** *a DATA_TYPE is marked only where its sentence says the
  company collects, receives, asks for, uses, stores, accesses or shares it — affirmed or denied (Rule 18)*.
  Your duty to protect it, and attacks named after it, are not data practices.
- **Decision (P1's): do not change anything now.** The fix pass has started under v7.4; a rule change midway
  would leave some documents fixed under one rule and some under another. Guideline, fix lists and P4's
  pack stay as they are. P1 skips these suggestions — they are in bucket 3 (CHECK, then ADD), which is the
  annotator's judgement by design. P4 is not told mid-pass.
- **Resolution point:** adjudication. These spans arrive in Export5 as one-sided disagreements; the
  adjudication tool will group DATA_TYPE spans whose sentence has no data practice so they are ruled on
  once, and the rule is written into the guideline then (as the version that describes the gold).
- **Cost, stated honestly:** the post-fix-pass kappa is slightly lower than it could have been (~25-30 spans
  of well over a thousand). Reported in the paper as a guideline gap found during the fix pass and resolved
  at adjudication.
- **Status:** ⏳ Deferred. Action when Export5A/B arrive: add the grouping to `adjudicate.py`, then rule.

### D48 — Full-corpus kappa after the fix pass: 0.426 — rule violations are gone, recall differences remain
- **Result (Export5A/B, all 23 documents, guideline v7.4, fix pass done by both):** token kappa **0.426**;
  entity F1 0.403 (DATA_TYPE 0.491, PURPOSE 0.285, THIRD_PARTY 0.388); relaxed CONTENT micro-F1 0.490
  (DATA_TYPE 0.549, PURPOSE 0.382, THIRD_PARTY 0.510). Spans: P1 1,365, P4 1,337. Round 1 on the same 23
  documents was 0.279. History: 0.279 -> 0.374 (2 docs) -> 0.283 (1 doc, P4 without the guideline) ->
  **0.522** (1 doc, independent, D43) -> **0.426** (23 docs, after the fix pass; not independent, D42).
- **Per document:** 0.03 to 0.67. Two clear the gate (`14_nadl_charter` 0.673, `25_the_financiali_privacy`
  0.628). The worst are the short charters/terms where one annotator marks almost nothing:
  `22_setu_aa_charter` 0.025 (7 vs 15 spans), `20_scoremeaa_charter` 0.068 (3 vs 43), `26_zerodha_tos` 0.108,
  `21_nadl_terms` 0.131 (6 vs 46).
- **Buckets:** EXACT 537, BOUNDARY 93, LABEL 26, P1-only 709, P4-only 681 (round 1: 1,973 one-sided).
- **Diagnosis — every one-sided span classified:**
  | why the other did not match | P1 (828) | P4 (800) |
  |---|---|---|
  | the other never marks this phrase anywhere | 462 (56%) | 291 (36%) |
  | the other marks it in other documents, not here | 75 | 193 |
  | the other skipped a repeat in this document | 15 | 93 |
  | boundary / label differs on an overlapping span | 127 | 126 |
  | doubtful THIRD_PARTY kept (Rules 16/19) | 100 | 0 |
  | own remaining rule violation (stoplist, edges, >5 words) | 29 | 93 |
  | context-dependent PURPOSE | 20 | 4 |
  So the fix pass did what it could: outright rule violations are down to ~120 spans in total. What is left
  is **which entities each annotator notices** — P1 finds 430 PURPOSE spans to P4's 356 and P4 matches a
  quarter of them. No list can close that, because a fix list only points at what a rule or a shared
  vocabulary can detect. P4 also did not finish the mechanical buckets (40 edge/lead-word, 33 stoplist, 20
  over-long PURPOSE remain), and P1 kept 100 THIRD_PARTY spans the Rule 16/19 check had flagged.
- **Data problems found in the exports:** Export5B has **13 unusable highlights** — 3 with no label and 10
  with labels outside the scheme (`KYC` x4, `APR` x2, `DRM` x2, `KFS`, `IPR`: an abbreviation typed as the
  label). `load_ls_export` now accepts only the three labels and warns about the rest (it crashed before).
  Export5A has one unsaved draft (`08_pennydrop_terms`, a one-span edge fix not submitted).
- **Adjudication size (`adjudicate.py` on Export5):** proposed gold 1,052 spans; resolved automatically —
  agreed 535, consensus 336, repeats +89, deleted 19; **left for humans 1,158** (one-sided 1,039, boundary 92,
  label 26, rule 1). The one-sided items are 657 distinct phrases; 62 phrases cover 388 of them
  (`lender` x49, `financial` x23, `data sharing` x20, `identity` x17).
- **Pre-registered path (D35, D42):** no further annotation round; the numbers are reported as they are and
  the corpus goes to adjudication.
- **Status:** ⏳ Awaiting P1's choice of adjudication method.

### D49 — Adjudication ruling: the Lender is a THIRD_PARTY, limited by Rule 16
- **Trigger:** `lender` was the most frequent one-sided phrase in the adjudication worklist (49 items, plus
  `lenders` 15, `partner institution(s)` 24). P1 ruled it must be marked: the lender is not part of
  Credbuddha and receives the user's data to grant the loan.
- **Ruling (P1's):** `Lender`, `Lenders`, `lending partner(s)`, `partner institution(s)` (and `Regulated
  Entity` used in that sense) are **THIRD_PARTY**. Nothing excludes them: not the policy's own company
  (Rule 17), not an AA-framework role word (Rule 8b), and Rule 8 already lists "lending partners" as a named
  recipient.
- **The limit (my proposal, P1 agreed):** Rule 16 still decides each occurrence — marked only where the
  sentence says the **user's data** goes to the lender (shared, submitted, accessed, used for assessment),
  affirmed or denied. Movement of **money** (disbursement), **documents sent to the user** (Key Fact
  Statement), fees, recovery, legal action, mandates and definitions do not count. Reason: it is the same
  logic that removes `affiliates` from an indemnity clause; marking every mention would turn THIRD_PARTY
  into "any organisation named", and would drift from OPP-115, which labels recipients only inside
  data-sharing statements.
- **Evidence (Export5):** lender-type THIRD_PARTY spans — P1 **153** (`24_credbuddha_terms` 98,
  `08_pennydrop_terms` 55), P4 **44**; only 33 identical. Many of P1's sit in sentences with no data flow.
- **Tool limit recorded:** the automatic Rule 16 check passed 60 and flagged 60 of P1's 120 unmatched
  lender spans, but it is unreliable in loan documents — its verb list reads "transfer of the Loan amount"
  and "shall provide the Key Fact Statement" as data flows. These spans must be read in their sentence; the
  check is not used to decide them.
- **Where it lives:** guideline **PART I — Adjudication rulings**, entry I-1 (a new part for rulings made
  after the fix pass; v7.4, under which the fix pass was done, is not reopened). D47 will be entered there
  when ruled.
- **Status:** ✅ Ruling in force for adjudication. Adjudication method still to be chosen by P1 (D48).

### D50 — Gold built by automatic adjudication with a human sample check (1,153 spans)
- **Why not a higher kappa first (asked by P1):** each export was cleaned on its own with written rules only
  (no sight of the other): 0.426 -> 0.435 (own rule violations) -> 0.461 (own skipped repeats) -> **0.474**
  (doubtful THIRD_PARTY removed). So a perfect second fix pass tops out near 0.47; 0.6 is reachable only by
  showing the annotators each other's work (no longer agreement) or a new round on new documents (none left;
  a third exception to the stop-loss). Kappa does not enter E1/E2 — the gold does.
- **Decision (P1's):** option 1 — the disagreements are adjudicated automatically, rule by rule, and **both
  annotators independently verify the same random sample** of rulings. Fully automatic adjudication was
  declined: unverified, the set would be silver, and four of my judgement calls had been corrected by P1
  in this project (telemetry, `required for KYC`, `Successor entities`, bracketed abbreviations).
- **Method (`adjudicate_auto.py`, reproducible from the two exports + `decisions.tsv`):**
  1. *Normalise* each export on its own — delete / trim / relabel / own-company — with that annotator's
     spans only.
  2. *Accept* what both marked identically: **511** spans (44 more, agreed but doubted by D47/D49/Rule 16,
     were made items).
  3. *Rule on every other span*, read in its sentence: **1,513 items** (1,371 one-sided, 72 boundary, 26
     label conflicts, 44 agreed-but-doubted). One code per item naming the rule.
  4. *Rule 7 second pass:* accepted phrases at positions neither annotator marked — **133** candidates, each
     ruled in context (19 accepted; e.g. an accepted `Lender` is not copied into a fee clause).
  5. Longest-wins de-overlap (Rule 15).
- **Rulings:** one-sided 543 accepted / 828 rejected; boundary 66 / 6; label 18 / 8; agreed-but-doubted 16 /
  28; repeats 19 / 114. Rejections by rule: R16 no data flow **329** (145 of them lender-type words under
  D49's limit, against 31 lender-type spans accepted), R10 no data-use frame / not on the list 237, not an entity in that sense 117, **D47 69**,
  R9 48, R19 41, company's own details 32, telemetry 29, umbrella 28 + 23, duplicates 24, R8b 6, R17 1.
- **D47 ruled and applied:** a DATA_TYPE needs a data practice in its sentence (guideline PART I-2).
- **Gold: 1,153 spans in 23 documents** — DATA_TYPE 532, PURPOSE 368, THIRD_PARTY 253; 4 to 212 per
  document, median 30. Validated: 0 overlaps, 0 stoplist/telemetry terms, 0 edge problems. Five PURPOSE spans
  are six words (no shorter contiguous phrase names the activity).
- **Consistency audit of my own rulings:** every context-free rejection was compared with what both
  annotators agreed on elsewhere. Four rulings were reversed to match them (`efficiency of the Platform` x3,
  `user profile information`); two over-long purposes shortened; three agreed telemetry spans dropped and one
  agreed boundary re-drawn. Other apparent conflicts were genuine differences of sense (`address` as a verb,
  `title` in "rights, title and interest").
- **Each annotator against the gold (exact match):** P1 precision 0.669 / recall 0.792 / F1 **0.725**
  (token kappa 0.778); P4 0.475 / 0.551 / F1 **0.510** (kappa 0.541). **Stated plainly: the gold sits closer
  to P1.** The guideline was built largely from P1's rulings and I applied it, so this is expected — and it
  is the reason P4's independent sample check matters most.
- **Sample check:** 123 rulings, stratified by item kind, random seed 42, identical sheet for both
  (`sample_check_P1.csv`, `sample_check_P4.csv`). Blind — it does not say who marked what. Each row: the
  highlight(s), the ruling, the rule, the sentence; the checker answers y/n. `adjudicate_auto score` reports
  each acceptance rate, how often the two checkers agree with each other, and the rows either rejected.
  At n = 123 a 90% rate has a margin of about +/-5 points. **Rule fixed now:** >= 90% from both -> the gold
  stands; any rule category below that -> its rulings are reviewed in full.
- **Tool safeguards:** second-pass items carry a stable key (document + offsets) so a changed ruling cannot
  shift the others; a re-drawn span is matched across line breaks and glued words; `load_ls_export` rejects
  labels outside the scheme.
- **Repo hygiene:** `gold.json`, `decisions.tsv`, `items*.txt` and the sample sheets quote text ->
  git-ignored; `auto_summary.json` (numbers only) and the code are committed.
- **Limits to report:** adjudicated by a language model applying the written guideline, verified on a 123-item
  sample by both annotators (rate to be filled in); 511 agreed spans were accepted without review apart from
  the mechanical checks; onboarding/registration purposes are outside the closed Rule 10 list.
- **Status:** ⏳ Gold built. Waiting for the two sample sheets -> `adjudicate_auto score`.

### D51 — Correction of process: the rules are ratified by P1 and P4 together BEFORE the sample check
- **What went wrong (mine):** D47 recorded that the DATA_TYPE context rule would be "ruled on once, together"
  by both annotators at adjudication. When automatic adjudication was chosen (D50) I applied my own proposed
  version of it, and along the way introduced further conventions of my own. P4 has agreed to none of them;
  P1 only to the Lender rule (D49). P1 caught this: the plan had been a meeting.
- **Two different questions, kept apart:** (A) *are the rules right?* — a policy decision for the two
  annotators **together**; (B) *were the rules applied correctly?* — the **independent** sample check. Doing B
  first would make every "no" ambiguous between a wrong rule and a wrong application.
- **Rules put up for ratification** (`results/annotation/adjudication/rules_to_ratify.md`, git-ignored;
  spans accepted / rejected under each): 1 Lender only where data flows (31 / 145) — P1's; 2 DATA_TYPE needs a
  data practice (- / 69) — D47; 3 a data source is not a recipient (- / ~27); 4 registration / onboarding is
  not a PURPOSE (- / 13), alternative: a 12th Rule 10 row; 5 `Account Aggregation Services` only where the
  sentence handles financial information (3 / 14); 6 only the user's identity in consent-artefact lists
  (10 / 13); 7 telemetry never, including 3 agreed spans dropped (- / 32); 8 the company's own details (- / 32);
  9 shared-word lists merged over agreed fragments (27 / -); 10 five six-word PURPOSE spans (5 / -).
- **Sequence now:** meeting -> each rule KEEP / CHANGE / DROP -> I re-apply any changed rule to exactly its
  coded rulings and rebuild the gold -> a **fresh** sample is drawn -> independent check -> score. The sample
  sheets written in D50 are provisional and must not be filled in yet.
- **Agenda rewritten at P1's request** (the first version was a bare table): `rules_to_ratify.md` now explains
  each rule in plain language — why the question arose, an analogy, real marked / not-marked sentences from the
  corpus, the grey cases, what KEEP / CHANGE / DROP would each do to the gold file, a recommendation with its
  confidence, and the questions to settle — plus whose highlights each rule removed (Rule 2: P4 54 of 67;
  Rule 1: P1 98 of 131). It also states that the gold sits closer to P1 (F1 0.73 vs 0.51).
- **Status:** ⏳ Waiting for the meeting's decisions. Gold (1,153 spans) is provisional until then.

### D52 — The AA documents are not independent: split by text family, not only by company (decision pending)
- **Finding:** preparing the test / adaptation split, the documents were compared pairwise (share of the
  smaller document's 8-word sequences found in the other). Many AA terms are **one template with the company
  name changed**: `09_saafe_terms` / `16_oms_aa_privacy` share 75%, `03_oms_aa_terms` /
  `04_pb_fintech_aa_terms` 51%, and a family of 13 documents (Setu x3, Digio, OMS x2, PB Fintech x2, OneMoney,
  Saafe x2, ScoremeAA x2) is linked at >= 10% or by organisation. Splitting by company alone (the plan so far)
  would have placed near-copies on both sides — the leakage D4 was written to prevent.
- **Method (`aa_split.py`, metadata and text only — never gold labels or model output):** link two
  documents if same organisation or similarity >= threshold; connected components are groups; a group is
  never split. At 10%: one family of 13, the NADL pair, and 8 single documents.
- **Consequence:** D21's "15 test + 8 adaptation" cannot be kept without leakage. Two clean options:
  | | test | adaptation | test entities (D / P / T) |
  |---|---|---|---|
  | **A — family in adaptation** | 9 documents, 8 independent groups | 14 (family + glued `10_perfios`) | **726** (282 / 246 / 198) |
  | B — family in test | 12 near-duplicate documents (`02_digio` dropped: glued, and cannot go to adaptation) | 10 | 374 (only 52 third parties) |
  A gives a test set that is larger in entities, balanced across labels and made of independent documents,
  and makes E2 a strict test (adapt on AA-operator templates, test on other organisations' documents). B keeps
  more documents in the test set but they are copies of each other and hold only 52 third parties.
- **Glued-text constraint (D36):** `02_digio_terms` and `10_perfios_terms` may not be test documents. Shown
  concretely by the converter: in `10_perfios` two gold spans sit inside one glued word and cannot be tagged
  separately at word level.
- **Converter built (`aa_to_conll.py`):** gold + split -> `data/ner_bio/aa_test.conll` / `aa_adapt.conll`
  (git-ignored) with a document map for bootstrapping over document groups. Documents are cut into segments at
  sentence ends, never inside a gold span, at most 100 tokens — because the trainer truncates at 256
  sub-word pieces, which would silently drop gold entities. Every gold span is checked to come back out of the
  BIO tags. Trial on the provisional gold (option A): test 560 segments / 726 entities, adaptation 845
  segments / 426 entities, read back correctly by the trainer's own reader.
- **Status:** ⏳ Tools ready; **the split is not written** until P1 chooses A or B. It must be fixed before any
  model sees AA data.

### D53 — Session record: what was discussed and decided but not yet written down
- **Adjudication alternatives that were considered and rejected** (before option 1 was chosen in D50):
  (a) *intersection* — keep only what both marked plus the automatic rule-based additions (~1,050 spans):
  drops every one-sided span, including correct ones, so the gold under-counts (about half of P1's purposes
  would vanish); (b) *union* — keep everything either marked unless a rule deletes it: keeps noise such as
  `firewalls` as a PURPOSE and `software` as a DATA_TYPE; (c) *fully automatic rulings with no human check*:
  best quality of the three but unverified, i.e. a silver set. Chosen: automatic rulings **plus** an
  independent sample check by both annotators.
- **How agreement will be reported in the paper** (agreed in discussion; four numbers, each labelled for
  what it is): independent kappa **0.52** (one fresh document, both on the final guideline, D43); full-corpus
  kappa **0.43** (23 documents after the fix pass, D48); rule-normalised kappa **0.47** (the same two exports
  after the written rules are applied automatically and identically to each, no sight of the other, D50) —
  supplementary and labelled as such; relaxed entity F1 **0.49**. On the usual Landis-Koch scale 0.41-0.60 is
  "moderate". The gold is described as adjudicated, with the sample-check acceptance rate. The round-by-round
  diagnosis (rule violations down to ~120 of 2,700 spans; the residue is recall) is reported as a finding in
  its own right. Kappa does not enter E1/E2, which are scored against the gold.
- **Export file naming, completed:** `ExportA/B` round 1 (23 docs); `Export2A/B` round-2 calibration (2 docs);
  `Export3A/B` round 3 (`23_upmint_aa_tos`); `Export4A/B` round 4 (`25_the_financiali_privacy`);
  `Export5A/B` after the fix pass on all 23 — the pair the gold is built from.
- **Hand-off packs created for P4** (all in P1's Downloads, never in the repo — they quote policy text):
  | file | content | status |
  |---|---|---|
  | `ConsentLedger_v7.4_fixpack_for_P4.zip` | guideline v7.4, P4's 23 fix lists (from Export4), one-page README | used for the fix pass |
  | `ConsentLedger_rules_to_ratify_for_P4.zip` | the plain-language meeting guide + guideline | **current — send before the meeting** |
  | `ConsentLedger_sample_check_for_P4.zip` | the 123-row sample sheet from D50 | **provisional — do not send / do not fill in**; a fresh sample is drawn after the meeting (D51) |
  | `ConsentLedger_round2_fixlist_for_P4.zip`, `ConsentLedger_v5_fixpack_for_P4.zip` | earlier packs | stale — delete |
- **Recommendations on record for the ten rules** (`rules_to_ratify.md`; the annotators decide, D51): KEEP 1, 2,
  5, 6, 7, 8, 9, 10; rule 3 KEEP with only moderate confidence (alternative: credit bureaus and KYC registries
  always count, since fetching a report means sending the user's identifiers); **rule 4 CHANGE — add a 12th
  Rule 10 category "Account opening & onboarding"** (both annotators marked it independently, six times
  each; the sentences are genuine purpose statements that fail only because the list has no slot). Rule 2 is
  the one P4 is most likely to contest (it removes 54 of P4's highlights).
- **Recommendation on record for the split (D52):** option A — the 13-document template family (plus glued
  `10_perfios_terms`) as adaptation, the 9 independent documents as the test set. P1 has not chosen yet.
- **Not built yet:** the E1/E2 evaluation script for the AA test set. Planned: entity-level P/R/F1 per label;
  bootstrap confidence intervals over **document groups** (the NADL pair is one group) using the docmap;
  a check that no segment is truncated; and a breakdown of the two error types predicted in advance — telemetry
  and merger/acquisition words that an OPP-115-trained model will tag (D43).
- **Stale statement elsewhere, now flagged:** `OVERVIEW.md` still gave "~15 gold test + ~8 adaptation"; a note
  there now points to D52.
- **State of the repository at the end of this session:** last commit `842e1bc`. Uncommitted and safe to
  commit: the meta-documentation, `.gitignore`, `kappa.py` (label validation), the three new modules
  `adjudicate_auto.py`, `aa_split.py`, `aa_to_conll.py`, `results/annotation/round5/` (`summary.csv`,
  `report.md`), `adjudication/auto_summary.json`, `adjudication/worklist.md`, the kappa / relaxed JSONs.
  Git-ignored by design: `gold.json`, `decisions.tsv`, `items*.txt`, `sample_check_P*.csv`,
  `rules_to_ratify.md`, every `Export*.json`, `data/ner_bio/`.
- **What happens next, in order:** (1) P1 + P4 meet and decide the ten rules; (2) P1 chooses split A or B;
  (3) changed rules are re-applied to their coded rulings and the gold is rebuilt; (4) a fresh sample is
  drawn and checked independently by both; `adjudicate_auto score`; >= 90% from both -> gold final;
  (5) write `data/splits/aa_split.json`, run `aa_to_conll`; (6) build the evaluation script, run E1 then E2;
  (7) gold to P2.
- **Status:** ✅ Record complete; a new session should read `FLOW.md`, then D48-D53.

### D54 — The AA split is fixed: option A (9 test / 14 adaptation)
- **Decision (P1's):** option A of D52 — the 13-document template family goes to adaptation, the independent
  documents form the test set.
- **Written to `data/splits/aa_split.json`** (document ids only, committed) by
  `aa_split.py --threshold 0.10 --test-groups 2 3 5 6 7 8 9 10 --write`:
  - **Test (9 documents, 8 independent groups):** `08_pennydrop_terms`, `14_nadl_charter` + `21_nadl_terms`
    (one group), `23_upmint_aa_tos`, `24_credbuddha_terms`, `25_the_financiali_privacy`, `26_zerodha_tos`,
    `28_indifi_capital_privacy`, `29_icici_home_fin_terms`.
  - **Adaptation (14 documents):** the family — `01_setu_aa_terms`, `02_digio_terms`, `03_oms_aa_terms`,
    `04_pb_fintech_aa_terms`, `05_onemoney_terms`, `06_setu_aa_privacy`, `09_saafe_terms`,
    `12_scoremeaa_terms`, `16_oms_aa_privacy`, `17_pb_fintech_aa_privacy`, `19_saafe_privacy`,
    `20_scoremeaa_charter`, `22_setu_aa_charter` — plus `10_perfios_terms` (glued text, barred from test).
- **Leakage check:** the largest text overlap between any test and any adaptation document is **4.7%**
  (`14_nadl_charter` / `22_setu_aa_charter`, two citizen's charters quoting the same regulatory wording) —
  under the 10% threshold; the tool refuses to write a split that exceeds it.
- **Fixed before any model has seen AA data, and independent of the labels:** the split uses text and the
  manifest only. The gold file is still provisional (D51), and rebuilding it cannot move a document across
  the split. On the provisional gold the test set holds 726 entities (282 data types, 246 purposes,
  198 third parties) and the adaptation set 426.
- **Supersedes** D21's "~15 test + ~8 adaptation" and the placeholder `data/splits/splits.json` of D4.
- **What the paper must state:** the test set is 9 documents from 8 organisations, six of them lenders / FIUs
  and three AA operators; E2 adapts on AA-operator templates and is tested on other organisations'
  documents, a deliberately strict setting; confidence intervals are bootstrapped over the 8 groups.
- **Not done yet, on purpose:** `aa_to_conll` is not run into `data/ner_bio/` until the gold is final, so no
  stale test file can be picked up by a training run.
- **Status:** ✅ Split locked. The test set is opened once, for E1 and E2 (D4).

### D55 — The P1 + P4 meeting: seven rules kept, one dropped, two changed; gold rebuilt (1,261 spans)
- **What happened.** P1 and P4 met (the step D51 required) and decided each of the ten rulings that the
  automatic adjudication had applied after the fix pass (`rules_to_ratify.md`).

  | # | Rule | Decision |
  |---|---|---|
  | 1 | Lender only where data flows | KEEP |
  | 2 | A data word needs a data practice (D47) | KEEP |
  | 3 | A source is not a recipient | **DROP** |
  | 4 | Registration / onboarding is not a purpose | **CHANGE** — add row 12, "Account opening & onboarding" |
  | 5 | "Account Aggregation Services" only in the right sentence | KEEP |
  | 6 | Only the user's identity | KEEP |
  | 7 | Telemetry — the rule beats agreement | KEEP |
  | 8 | The company's own details | KEEP |
  | 9 | Shared-word lists as one highlight | **CHANGE** — merge only where a piece is meaningless alone |
  | 10 | Five six-word purposes | KEEP |

- **Rule 3 dropped — the annotators' reasoning:** an organisation the data is fetched *from* gets the user's
  data indirectly (to pull a credit report the company must send the name and PAN), so data does flow to it.
  Mark organisations, except the ones in the RBI AA pipeline. THIRD_PARTY therefore now means *an outside
  organisation that exchanges the user's data with the company, in either direction*. Rule 16 still needs an
  exchange in the sentence, and Rule 1 (Lender) is untouched — no Lender rejection sat in a "from" sentence.
- **How each change was applied** (`decisions.tsv`; 85 rulings changed, backed up before):
  - **Rule 3:** 48 rejections became accepts (40 highlights the annotators had drawn — 32 of P4's, 7 of P1's,
    1 both — and 8 repeat candidates): credit bureaus by name, `Credit Information Companies`, `UIDAI`, the
    Central KYC Registry, `business partners`, `verification agencies`, Indifi's long "information from
    independent third parties" lists. 4 rejections stay but are re-coded to the rule that really decides them
    (the "banks where your account is maintained" are the FIP — Rule 8b; `CKYCRR` inside `CKYCRR records` is
    part of a data name — Rule 19).
  - **Rule 4:** of the 12 onboarding highlights, **7 are now PURPOSE** (`register you as a user`,
    `registration as a user`, `onboarding`, `customer onboarding` x3, `Registration` in "For Registration: we
    may collect…"). 5 stay out because the sentence has no data-use frame ("at the time of registration",
    "you must register", a list of message topics) or is a job application.
  - **Rule 9:** of the 28 lists the adjudication had merged, **12 are split back into their pieces** (two of
    them partly) and 16 stay whole. Test applied: *would the piece, highlighted alone, tell a reader what it
    is?* Split: `ACH` / `NEFT` / `IMPS` / `UPI ID details`; `mutual fund` / `demat holdings`; `salary` /
    `income details`; `bank account` / `credit card` / `debit card`; `Aadhaar` / `Virtual ID details`;
    `marketing` / `promotional activities`; `prepare your financial plan` / `recommendations` / `portfolio
    reviews` / `ongoing advice`; `KYC` / `AML` / `risk profiling requirements`. Kept whole: lists of bare
    verbs (`Retrieving, viewing, … Financial Information`), `Verifying your identity and eligibility`, `loan
    evaluation and servicing`, `Complying with legal, regulatory, and tax obligations`. Partly: `credit, debit
    card` + `internet banking account information`.
- **A consequence that needed a new mechanism — highlights nobody drew.** Both annotators had been told by the
  fix lists to *delete* sources, so the exports under-contain them: in "Experian/CIBIL/CRIF" P4 had kept two
  and nobody had `CIBIL`. A gold file with half a list marked is not consistent with any rule. So
  `adjudicate_auto` gained one line type, `new <label> <doc> <start> <end> <text>` (kind **N**): **36
  highlights added** — 33 THIRD_PARTY list-mates of a now-accepted source, `registration` beside `customer
  onboarding`, and `KYC` / `AML` from the split list. They are in the audit trail and are sampled like every
  other ruling. Found by (a) completing each sentence that had a flipped item, (b) a corpus sweep for known
  organisation words after "from / provided by / sources" (96 candidates in 32 sentences, read one by one),
  (c) comparing the pre-fix-pass exports for third parties deleted for this reason (8, of which 4 real).
- **Result.** Gold **1,153 -> 1,261 spans** (DATA_TYPE 545, PURPOSE 382, THIRD_PARTY 334; 120 added, 12 list
  spans removed; 8 documents changed). Validated: no overlaps, clean edges, nothing a mechanical rule drops;
  the converter round-trips it (test 824 entities in 560 segments: D 295 / P 258 / T 271; adaptation 437).
  Against the new gold, exact-match F1 is **P1 0.722, P4 0.510** (before: 0.725, 0.510). 12 new repeat
  candidates appeared and were all rejected (definitions, headings, `CIBIL SCORE`, `Google Chrome`).
- **Judgement calls made while applying — all five confirmed by P1 (2026-10-07):**
  1. *Job applications* stay outside row 12 (the meeting sheet left that question blank; the guide suggested no).
  2. *Pipeline boundary:* "banks / financial institutions where your account is maintained" = the FIP, not
     marked; but `banks` in Indifi's general list of independent third parties is marked. Depositories and
     registrars named as a **direct** source (`CDSL`, `NSDL`, `MF Central`, `CAMS`, `KFintech`) are marked —
     this reverses the guideline's old tricky case.
  3. *No exchange, no mark:* "CAS emails sent by registrars (CAMS, KFintech)" read from the user's own Gmail
     stays unmarked — the company exchanges nothing with them.
  4. *Rule 9 scope:* applied to lists the adjudication merged or chose; a list **both** annotators drew as one
     highlight is left as drawn.
  5. *"Stands alone" calls:* `mutual fund`, `salary`, `consents`, `licenses`, and `address` in "proofs of
     identity and address" (both annotators had marked `address`) count as complete pieces.
- **Limitations to state in the paper.** Row 12 and the source rule were fixed after annotation, so neither
  annotator was looking for them; recall there rests on what somebody happened to mark plus the sweep above.
  A source organisation in a sentence nobody marked, named with a word outside the sweep's list, can be missing.
- **Guideline v7.5:** Rule 10 row 12, Rule 14 narrowed, Rule 16 "Sources" paragraph, PART I-3 and two tricky
  cases rewritten. `fixlist.py` still words its THIRD_PARTY check the old way — it is a record of how the fix
  pass was done and is not re-run.
- **Fresh sample drawn** (seed 55, 124 rulings, all six kinds): `sample_check_P1.csv`, `sample_check_P4.csv`.
  The earlier sheets are void.
- **Status:** ✅ Rules ratified and applied. **Gold still provisional until both annotators check the sample
  alone and both accept at least 90%** (`adjudicate_auto score`).

### D56 — Sample check scored: P1 96.0%, P4 100% — the 90% gate is passed; five rows still to settle
- **Result** (`adjudicate_auto score`, 124 rulings, seed 55, each annotator alone;
  `results/annotation/adjudication/sample_check_result.json`):

  | Checker | Accepted | Rate |
  |---|---|---|
  | P1 | 119 / 124 | **96.0%** (95% Wilson interval 90.9% - 98.3%) |
  | P4 | 124 / 124 | **100%** |

  The two checkers gave the same answer on 119 of 124 rows. Both are above the 90% bar set in D50, so the
  acceptance rule is met and no rule needs a full review.
- **Read the 100% with care.** P4 answered "y" on every row and wrote no comment. That can be genuine
  agreement, but it cannot be told apart from a light read, so the informative figure is P1's 96.0% — and
  even its lower confidence bound stays above 90%.
- **The five rulings P1 rejected** (rows 28, 84, 91, 93, 117; four "mark" rulings and one "do not mark"; P4
  accepted all five). None is an isolated row — each touches neighbours, so they are settled as a set, not
  patched one by one:
  1. `retrieving or collecting` (PURPOSE, `10_perfios_terms`) — P1: no object, cannot stand alone. The same
     phrase is gold in `14_nadl_charter` and `21_nadl_terms` (in 21 both annotators drew it).
  2. `process applications` (PURPOSE, `24_credbuddha_terms`) — P1: the sentence is about what withdrawing
     consent affects; nothing in it should be marked. Five gold spans sit in that sentence.
  3. `ongoing advice` (PURPOSE, `25_the_financiali_privacy`) — P1: maps to none of the 12 rows. It is one of
     the pieces the Rule 9 change split out (D55), beside `recommendations` and `portfolio reviews`.
  4. `Gmail` (DATA_TYPE, `25_the_financiali_privacy`, ruled "do not mark", Rule 9b) — P1: Gmail implies the
     user's emails, so it is data. Four Gmail highlights in that document carry the same ruling.
  5. `third-party advertising companies` (THIRD_PARTY, `28_indifi_capital_privacy`) — P1: the sentence states
     no data flow to them (Rule 16). A single highlight.
- **Tooling:** `adjudicate_auto score` now reads a sheet however the spreadsheet program saved it (comma or
  tab separated; UTF-8, UTF-16 or Windows-1252) and prefers a `sample_check_<name>_filled*` file. The filled
  sheets quote policy text; `.gitignore` now covers every `sample_check_P*` file, not only `.csv`.
- **Status:** ✅ Gate passed. ⏳ Gold becomes final once the five rows are settled and re-applied; only then
  is `aa_to_conll` run.

### D57 — The five sample-check corrections applied; the gold file is FINAL (1,258 spans); test files generated
- **Decision (P1's):** apply all five corrections from the sample check (D56) with the scope proposed —
  each one together with the neighbouring highlights the same reasoning covers.

  | Row | P1's objection | Applied |
  |---|---|---|
  | 28 | `retrieving or collecting` names no object | re-drawn as `retrieving or collecting such financial information` in all three documents (`10_perfios_terms`, `14_nadl_charter`, `21_nadl_terms` — in the last, both annotators had drawn the short form) |
  | 84 | a sentence about what withdrawing consent affects; no data practice | all five highlights in the sentence removed: `process applications`, `verify information`, `assess eligibility` (Rule 10), `Lender`, `Partner Institution` (Rule 16) |
  | 91 | `ongoing advice` fits none of the 12 purpose rows | `ongoing advice` and `recommendations` removed; `portfolio reviews` and `prepare your financial plan` kept |
  | 93 | `Gmail` means the user's emails — it is data | `Gmail` marked DATA_TYPE at the four places it had been rejected, plus one repeat in the section heading; `Gmail` inside `Gmail OAuth` stays unmarked (Rule 19) |
  | 117 | no data flow to `third-party advertising companies` in the sentence | that highlight removed (Rule 16) |

- **In `decisions.tsv`:** 14 rulings changed, 1 `agreed` re-draw line added, 2 new repeat candidates ruled
  (one accepted, one rejected).
- **Final gold: 1,258 spans** — DATA_TYPE 550, PURPOSE 377, THIRD_PARTY 331 (was 1,261: 9 removed, 5 added,
  3 re-drawn; 6 documents touched). Validated again: no overlaps, clean edges, nothing a mechanical rule
  drops. Exact-match F1 of each annotator's own export against it: P1 0.721, P4 0.506.
- **How the gold was reached, in one line for the paper:** two annotators (kappa 0.43 after the fix pass,
  0.52 on a fresh document) -> rule-by-rule automatic adjudication of 1,513 disputed highlights -> the ten
  post-hoc rules ratified by both annotators (7 kept, 1 dropped, 2 changed) -> an independent check of 124
  random rulings by each (96.0% and 100% accepted) -> the five rejected rulings corrected.
- **Model-ready files generated** by `aa_to_conll` into `data/ner_bio/` (git-ignored — they contain policy
  text):
  - `aa_test.conll` + `aa_test.docmap.json` — 9 documents, 559 segments, 40,686 tokens, **821 entities**
    (DATA_TYPE 300, PURPOSE 253, THIRD_PARTY 268).
  - `aa_adapt.conll` + `aa_adapt.docmap.json` — 14 documents, 845 segments, 59,887 tokens, 436 entities
    (DATA_TYPE 249, PURPOSE 124, THIRD_PARTY 63); one of the 437 gold spans shares a glued word with another
    in `10_perfios_terms` and cannot be tagged separately (D36) — the reason that document is barred from test.
  - Checked: the training code's own reader (`read_conll`) reads back exactly those entity counts; the docmap
    has one entry per segment and covers exactly the split's documents; the longest segment is 145 sub-word
    pieces in the test file and 177 in the adaptation file across the three tokenizers — under the 256 limit,
    so **nothing is truncated**.
- **Tooling:** `adjudicate_auto apply --sample 0` rebuilds the gold without overwriting the sample sheets that
  were already scored.
- **The test set is now sealed** (D4): it is opened once, for E1 and E2. No model has seen any AA text.
- **Status:** ✅ Gold final. ✅ Test and adaptation files ready. Next: the E1/E2 evaluation script; the gold
  goes to P2.

### D58 — Audit of the final gold from three perspectives: usable, not yet gold standard; 49 verified defects
- **Why:** P1 asked for a deep check of the finished gold file (D57) as three readers — the user giving consent,
  a financier / auditor, and a paper review panel — repeated three times, before it is used.
- **How (nothing in the gold was changed):**
  1. *Mechanical consistency* over all 1,258 spans: balance, provenance, label conflicts, span shape, and
     whether identical text is annotated identically across documents.
  2. *Reading for wrong and missed spans:* all 1,474 non-gold occurrences of gold phrases; rule-context probes
     on every span; blind reading of 100 random gold spans and 70 random unmarked sentences.
  3. *Verification and fitness:* each suspect re-read with its provenance; a sweep for 41 sensitive / regulated
     terms; one test document read whole and the densest section of the largest.
- **Measured quality:**

  | Measure | Value |
  |---|---|
  | Clearly wrong spans (sample of 100) | 2% (range about 0.6-7%); a further 4% have a debatable boundary |
  | Estimated recall | about 93% (range 90-95%) |
  | Identical text annotated identically | 408 of 442 = 92.3% |
  | Label conflicts, overlaps, dirty edges | none |

- **49 verified defects** (full list with sentences: `results/annotation/adjudication/gold_audit.md`, git-ignored):
  - **20 to remove** — e.g. `parent company / subsidiaries / affiliates / agents` in an indemnity clause;
    `gender` in two non-discrimination clauses (the exact case PART I-2 excludes); `title` in "right, title and
    interest"; `affiliates`, `group companies` where they *define* the policy's own company (2 of the 6 spans
    in `26_zerodha_tos`); `identity` of the recipients; three `marketing communication` in opt-out sentences.
  - **29 to add** — e.g. `user authentication credentials` in three template documents that lack it;
    `biometric data` (absent from the gold, three clear cases, all in test documents); `UIDAI` in "share your
    KYC data with CKYCRR, UIDAI"; `contacts` beside `gallery` in the lending prohibition; `receive all required
    notices` in four documents.
  - **1 to harmonise** — the consent-artefact field "identity and (optional) contact information" appears in
    three different forms across nine template documents.
- **The structural finding:** 16 of the 20 wrong spans were drawn **identically by both annotators**. Those
  488 spans (39% of the gold) were accepted automatically and were never reviewed — the sample check (D56)
  sampled *rulings*, and an agreed span has no ruling. Agreement was treated as correctness; it is not.
  Second cause: the repeat pass (Rule 7) worked inside one document, never across the 13-document template
  family, and skipped words under four letters.
- **Design limits — correct under the rules, to be disclosed in the paper:** no polarity (7% of DATA_TYPE spans
  follow a denial); umbrella terms unmarked (`financial information` 334 mentions); pipeline actors unmarked,
  so THIRD_PARTY is not the full recipient list; telemetry and device access excluded while 33 purposes of
  telemetry are marked; purposes carry no row number; 61% of the gold not agreed by two people; adjudication
  by an AI assistant under human ratification; guideline developed on the test documents too; test and
  adaptation sets are different sub-genres (24.5 vs 8.9 spans per 1,000 words; THIRD_PARTY 268 vs 63);
  `28_indifi_capital_privacy` is 33% of the test set; label definitions differ from OPP-115.
- **Verdict by reader:** *user* — trust the lists, not a summary that ignores negation; *auditor* — sign-off
  after the biometric / UIDAI / contacts gaps are closed, and never call THIRD_PARTY "the recipients" without
  qualification; *panel* — acceptable evaluation set with a stated error rate, not "gold standard" until the
  unreviewed 39% and the template inconsistencies are fixed.
- **Recommended:** apply the 49 corrections and the harmonisation through `decisions.tsv` after both
  annotators see the list; add a `negated` flag per span; re-run the identical-text check (target above 98%);
  regenerate the CoNLL files. No model has seen AA text, so correcting the gold now costs nothing in validity.
- **Status:** ✅ Audit done. Corrections applied in D59.

### D59 — Audit corrections applied with two changes by P1; gold 1,266 spans; identical text now 99.1% consistent
- **Decision (P1's), on the list of D58:** apply it, with two changes.
  1. **The signature is not data.** "…and your signature/digital signature" in the consent-artefact field list
     is the *act of accepting the consent*, not data the user provides. So the two proposed additions in
     `04_pb_fintech_aa_terms` are **not** made — and, for consistency, the four existing highlights of the
     same clause (`signature`, `digital signature` in `02_digio_terms` and `03_oms_aa_terms`) are **removed**.
     This overturns the guideline's old tricky case that listed `signature` among credential fields.
  2. **`identity` and `contact information` are two highlights**, not one, in the consent-artefact field
     ("your identity and (optional) contact information") — in all nine template documents. This overrides
     the audit's proposal of a single highlight and the Rule 14 example that said one.
- **Applied through `decisions.tsv`** (backed up first): 13 rulings changed; **16 agreed spans dropped** with a
  new line type, `drop <label> <doc> <start> <end> <code> <text>` (one span, one position — the existing
  `agreed … => -` line would have removed the phrase in every document); 30 `new` lines; 10 repeat candidates
  created by the additions ruled (1 accepted — "verification through `UIDAI`'s e-KYC service" — 9 rejected).
- **What changed in the gold** (19 documents): 28 highlights removed, 36 added.
  - *Removed:* the 20 of D58 (indemnity list, `suppliers`, `title`, two `gender`, a heading, three `identity`
    of others, one `Lender`, Zerodha's self-definition, a disclaimer, one `account aggregation services`, three
    opt-out `marketing communication`); the 4 signature highlights; the 4 merged or half-formed versions of the
    consent-artefact field (re-drawn as two).
  - *Added:* `user authentication credentials` x3, `PINs`, `private keys`, `receive all required notices` x4,
    `access, fetch or retrieve`, `UIDAI` x2, `court`, `biometric data` x3, `contacts`, `bank statement`,
    `CAS` x2, `billing and collection`, `access and share your Financial Information`, `comply with any
    applicable laws`, `lenders`; and `identity` / `contact information` wherever one of the pair was missing.
- **Final gold: 1,266 spans** — DATA_TYPE 559, PURPOSE 381, THIRD_PARTY 326. Validated: no overlaps, clean
  edges, nothing a mechanical rule drops.
- **Identical text annotated identically: 464 of 468 = 99.1%** (was 408 of 442 = 92.3%). The four remaining
  mismatches are not real: they are the checker failing to align words inside the two glued-text documents
  (`02_digio_terms`, `10_perfios_terms`).
- **CoNLL files regenerated** (`data/ner_bio/`, git-ignored): `aa_test.conll` — 559 segments, **826 entities**
  (DATA_TYPE 307, PURPOSE 252, THIRD_PARTY 267); `aa_adapt.conll` — 845 segments, 439 entities (251 / 129 / 59;
  one of 440 lost to a glued word). Read back exactly by the trainer's reader; longest segment 145 and 177
  sub-word pieces, under 256.
- **Against the final gold:** P1's own export scores exact F1 0.706, P4's 0.489; 473 gold spans (37%) were
  drawn identically by both.
- **Method lesson, now part of the process:** agreement between two annotators is evidence, not proof. The
  gold was built by reviewing *disagreements*; the audit shows the agreed part needs its own check — here a
  consistency test over identical text and a blind sample.
- **Not done (still open from D58):** the `negated` flag per span and the purpose row number — P1 has not
  asked for them. The estimated remainder — roughly 5 wrong and 50-90 missed spans that the samples imply
  but did not locate — stays, and is reported as the gold's error rate.
- **Whether P4 has seen the list** is not recorded here; 16 of the removals overturn something both annotators
  drew. P1 decided.
- **Status:** ✅ Gold final (second time). Test set sealed again; E1/E2 can proceed.

### D60 — The E1/E2 evaluation script is built (`ner/evaluate.py`); the test set is still unopened
- **What it reports,** for one model on one CoNLL file:
  1. **Exact-match** entity precision / recall / F1 — micro, macro over the three labels, per label (seqeval,
     as in training).
  2. **Relaxed match** — a prediction counts if it overlaps a gold entity of the same label. Our boundary
     conventions are specific to the guideline (D58), so exact match alone understates a transferred model.
  3. **95% confidence intervals by bootstrap over document groups** (`aa_split.json`; the docmap says which
     document each segment came from). Segments of one document are not independent, so resampling segments
     would give intervals that are too narrow. 5,000 resamples, fixed seed.
  4. **Per-group F1 and their unweighted mean** — one document holds a third of the test entities.
  5. **Error breakdown.** Predictions: exact / right label, wrong boundary / wrong label / spurious. Gold:
     found / found with another boundary / under another label / missed. Spurious predictions are sorted
     into *telemetry*, *AA-framework role*, *umbrella term* (the three kinds that are entities under
     OPP-115's definition and excluded by ours — the "definition mismatch"), *corporate transaction*, and
     *other*; and F1 is also given with the definition-mismatch predictions set aside.
  6. **Truncation check.** A segment longer than 256 sub-word pieces loses its tail silently in the trainer.
     The script counts such segments, scores the lost tail as *missed* rather than dropping it, and refuses
     to score an AA file that has any.
- **Comparing two conditions** (`--compare … --against …`): any number of seeds per side, averaged; the
  difference is bootstrapped on the *same* resamples of the groups (paired), giving a 95% interval for the
  difference and the share of resamples in which A is ahead. "No significant difference" is printed when the
  interval contains zero (D5).
- **The seal is enforced in code.** `aa_test.conll` cannot be scored unless `--open-test` is passed; every
  opening is appended to `results/ner/test_openings.jsonl` (time, model, commit, score). Results go to
  `<model-dir>/test_metrics.json`, which `collect.py` already folds into the ablation table. The optional
  `--errors` file lists the spurious phrases — it contains policy text and belongs under `artifacts_out/`.
- **Checked three ways, none of them on the test set:**
  1. Built-in self-check on hand-made tags (counts, relaxed match, error categories, deterministic intervals,
     the comparison). Its micro-F1 is asserted equal to seqeval's on every run.
  2. **OPP-115 dev, Legal-BERT seed 42: 0.397** against 0.401 logged at training time. The gap is explained:
     18 of 430 dev segments are longer than 256 pieces, and the training-time metric drops their tails while
     this script counts them as missed.
  3. All nine E1 models on the **adaptation** file `aa_adapt.conll` (14 documents as 14 bootstrap units).
- **Development finding from check 3 — not a result, the adaptation documents are E2's training data:**

  | Backbone (3 seeds) | Exact micro-F1 | Relaxed micro-F1 | Exact, definition mismatch set aside |
  |---|---|---|---|
  | BERT-base | 0.090 ± 0.015 | 0.223 ± 0.015 | 0.117 |
  | Legal-BERT | 0.090 ± 0.015 | 0.219 ± 0.017 | 0.116 |
  | InLegalBERT | 0.088 ± 0.004 | 0.210 ± 0.001 | 0.112 |

  The models score 0.40 on OPP-115 dev and about **0.09** on AA-operator documents. They predict 960-1,140
  entities where the gold has 439; about 800-980 predictions are spurious, and roughly a third of those are
  definition mismatches (`financial information`, `the services`, `third parties`, `Financial Information
  Users`, `cookies`). The backbones are indistinguishable (paired comparison: every interval contains zero).
  So expect E1 on the test set to be low, with a large part of the error explained by the two annotation
  schemes meaning different things — which the script now measures instead of leaving as a guess.
- **Also fixed:** the old `--out` path could not save its JSON (numpy integers from seqeval's report).
- **Not done:** E2 training. `train.py` reads one training file; E2 needs three decisions from P1 —
  joint training on OPP-115 + adaptation data or continuing from the E1 checkpoint; which data stops training
  early (OPP-115 dev would select for OPP-115, not AA); and how many seeds.
- **Status:** ✅ Script built and verified. Test set unopened. Next: P1's E2 design decisions, train E2, then
  open the test set once for all E1 and E2 models.

### D61 — E2 training design (P1's decisions): both ways of adapting, an AA mock test, three seeds each
- **1. How the AA practice is given — both, as two conditions.**
  - **E2-joint:** the pretrained backbone trained once on OPP-115 *and* the AA adaptation documents together.
    The fair twin of E1 (same recipe, only the data differs) — but the AA part is small (726 of about 4,090
    training segments, 350 of about 7,100 entities) and may be drowned out.
  - **E2-sequential:** the finished E1 model of the same seed, trained further on the AA adaptation documents
    only. P1's reasoning: the system exists to label Indian documents, so forgetting some of the American
    lessons does not matter, and this is the variant expected to give the better result.
  - Reporting both turns the choice into a finding: *does adapting on little data work better mixed in, or
    as a second step?*
- **2. When training stops — an AA mock test.** *(The documents and the counts in this point and in point 1
  were revised in D62 — read that for the current picks.)* Two adaptation documents are held out of training and used
  only to pick the best epoch: `09_saafe_terms` and `19_saafe_privacy` — one organisation held out whole, one
  terms document and one privacy policy, **89 entities** (DATA_TYPE 43, PURPOSE 35, THIRD_PARTY 11). The other
  12 documents train: 726 segments, **350 entities** (208 / 94 / 48). Neither glued-text document is in the
  mock test. Known weakness: the Saafe documents share the template of the other eleven, so the mock score is
  optimistic — acceptable, because it only selects an epoch and is never reported as a result.
- **3. Repeats — seeds 42, 43, 44 for each of the three backbones,** the same as E1. So 9 + 9 = **18 new
  runs**, and every E2 model has an E1 twin with the same seed.
- **E1 models are never modified.** `--e2 joint` does not touch them; `--e2 sequential` only *reads* the E1
  folder and writes to a new one. Folders: `<backbone>_s<seed>` (E1), `<backbone>_e2j_s<seed>`,
  `<backbone>_e2s_s<seed>`.
- **Deliberately unchanged:** learning rate, batch size, warm-up, patience and maximum epochs are the E1
  recipe for both E2 variants (D5 — one recipe). For the sequential variant that means a second full-strength
  round on 726 segments; tuning it would add choices E1 never had.
- **What differs between E1 and E2 besides the AA documents — to state in the paper:** E1 stopped on OPP-115
  dev, E2 stops on the AA mock test. That is part of what "having a little AA data" means, but it is a second
  difference, not zero.
- **Built:** `train.py --e2 joint|sequential` (requires `--seed`); `aa_to_conll` also writes
  `aa_adapt_train.conll` and `aa_adapt_dev.conll` (the test file is byte-identical to before);
  `run_meta.json` records condition, starting point, training files and dev file; `collect.py` notes that the
  dev column is each run's own dev set; `evaluate.py --compare` expands wildcards itself.
- **Verified by smoke runs** (1 epoch, 600 segments, Legal-BERT seed 42): both modes train, score on the AA
  mock test and save to their own folder; the E1 weights file is untouched. The sequential smoke run reached
  0.23 micro-F1 on the mock test after one short epoch (E1 scores about 0.09 on AA-operator documents) —
  encouraging, not a result.
- **Status:** ✅ Ready to train. Next: 18 training runs, then the test set is opened once for all 27 models.

### D62 — The AA mock test re-picked by a rule: least shared text with the training documents (revises D61)
- **Why:** D61 held out `09_saafe_terms` and `19_saafe_privacy` ("one organisation held out whole"). Measured
  with the split's own similarity function, `09_saafe_terms` shares **75%** of its text with
  `16_oms_aa_privacy`, which stays in training — the most-shared document of all fourteen. A quarter of that
  mock test was close to a memory test, and a memory test keeps improving while the model overfits the
  template: it would stop training too late.
- **The rule (agreed by P1 before the picks were computed):** hold out the adaptation documents that share
  the *least* text with the others, until the mock test holds about 100 entities; no glued-text document
  (`02_digio_terms`, `10_perfios_terms`).
- **The picks (P1 chose them over D61's):** `20_scoremeaa_charter` (shares 0%), `19_saafe_privacy` (14%),
  `22_setu_aa_charter` (14%), `01_setu_aa_terms` (18%). The largest overlap between any mock-test document and
  any training document is now **18%** (`01_setu_aa_terms` / `06_setu_aa_privacy`), down from 75%.
  One tie: `17_pb_fintech_aa_privacy` shares as little as `19_saafe_privacy`; 19 was held out because 17
  carries 17 of the 59 THIRD_PARTY entities, the scarcest label, and those are worth more in training.

  | | Mock test (`aa_adapt_dev.conll`) | Training (`aa_adapt_train.conll`) |
  |---|---|---|
  | Documents | 4 — a terms document, a privacy policy, two charters | 10 |
  | Segments | 195 | 650 |
  | Entities | **107** (DATA_TYPE 59, PURPOSE 36, THIRD_PARTY 12) | **332** (192 / 93 / 47) |

  Against D61's picks this costs 18 training entities, almost all DATA_TYPE; PURPOSE and THIRD_PARTY in
  training are unchanged within one.
- **Correction of two figures in D61 (and of what P1 was told in discussion):** OPP-115's training file holds
  3,362 segments and **9,955** entities (the 6,776 of D16 predates span trimming, D25). So in **E2-joint** the
  AA documents are 650 of 4,012 segments (16%) and 332 of about 10,290 entities (**3%**) — the dilution P1 was
  worried about is stronger than stated.
- **Changed:** one constant, `ADAPT_DEV` in `aa_to_conll.py`; the two files regenerated and read back by the
  trainer's reader (counts above; longest segment 177 sub-word pieces). `aa_test.conll` and `aa_adapt.conll`
  are byte-identical to before (checksums compared). No model had been trained on the old files.
- **Everything else in D61 stands:** both conditions (E2-joint, E2-sequential), E1's recipe unchanged, seeds
  42-44 for three backbones, E1 models only read, 18 runs, then the test set opened once for all 27 models.
- **Status:** ✅ Ready to train.

### D63 — THE RESULT: the test set opened once for all 27 models — a little AA data lifts F1 from 0.13 to 0.44
- **What was run.** All 18 E2 models were trained by P1 (9 sequential, 9 joint). Before opening the test set:
  all 27 model folders complete and correctly labelled; the nine E1 models still byte-identical to the backup
  uploaded to the Hugging Face Hub before E2 training (so E2 did not alter them); `aa_test.conll` unchanged
  since it was generated; no earlier opening on record. Then `evaluate.py --open-test` once per model:
  27 entries in `results/ner/test_openings.jsonl`, 559 segments, 826 gold entities, 0 truncated, 0 failures.
- **Headline — exact-match entity micro-F1 on the AA test set** (mean over seeds; 95% interval from a
  bootstrap over the 8 document groups):

  | Condition | All three backbones (9 runs) | Relaxed-match F1 |
  |---|---|---|
  | **E1** — OPP-115 only | **0.125** [0.101, 0.156] | 0.293 [0.253, 0.319] |
  | **E2-joint** — OPP-115 + AA together | **0.252** [0.209, 0.331] | 0.442 [0.405, 0.500] |
  | **E2-sequential** — E1 model, then AA | **0.439** [0.352, 0.494] | 0.606 [0.539, 0.646] |

- **Every step is a real difference** (paired bootstrap, the same resamples for both sides; none of these
  intervals contains zero, for the three backbones together and for each one alone):
  - E2-sequential minus E1: **+0.314** [+0.241, +0.358]
  - E2-joint minus E1: **+0.127** [+0.101, +0.179]
  - E2-sequential minus E2-joint: **+0.187** [+0.126, +0.234]
- **By backbone** (exact micro-F1, 3 seeds each):

  | Backbone | E1 | E2-joint | E2-sequential |
  |---|---|---|---|
  | BERT-base | 0.130 ± 0.008 | 0.266 ± 0.016 | 0.412 ± 0.016 |
  | InLegalBERT | 0.119 ± 0.003 | 0.225 ± 0.043 | 0.427 ± 0.038 |
  | Legal-BERT | 0.126 ± 0.007 | 0.266 ± 0.008 | **0.479 ± 0.026** |

  In E1 the backbones are indistinguishable (Legal-BERT minus BERT-base: -0.004 [-0.018, +0.022]). After
  sequential adaptation **Legal-BERT is ahead** of BERT-base by +0.067 [+0.050, +0.084] and of InLegalBERT by
  +0.052 [+0.029, +0.082]; InLegalBERT and BERT-base do not differ (+0.015 [-0.007, +0.033]). So the choice of
  backbone only starts to matter once the model has seen in-domain data. The Indian-law model shows no
  advantage on Indian fintech policies.
- **By label** (all backbones; exact / relaxed F1):

  | Condition | DATA_TYPE | PURPOSE | THIRD_PARTY |
  |---|---|---|---|
  | E1 | 0.135 / 0.269 | 0.111 / 0.353 | 0.128 / 0.247 |
  | E2-joint | 0.336 / 0.477 | 0.191 / 0.499 | 0.195 / 0.312 |
  | E2-sequential | 0.510 / 0.641 | 0.359 / 0.607 | 0.436 / 0.555 |

  PURPOSE has the widest gap between exact and relaxed: the model finds the purpose but draws it longer or
  shorter than the guideline's five-word convention.
- **What the models did** (per run, average over all backbones; 826 gold entities):

  | Condition | Predicted | Exact | Right label, wrong boundary | Spurious | of which definition mismatch | Gold missed |
  |---|---|---|---|---|---|---|
  | E1 | 944 | 111 | 150 | 663 | 170 | 550 |
  | E2-joint | 630 | 184 | 144 | 286 | 66 | 494 |
  | E2-sequential | 747 | 347 | 142 | 243 | 30 | 345 |

  E1 over-predicts; a quarter of its spurious entities are things OPP-115 marks and our guideline does not
  (`financial information`, `third parties`, cookies). Setting those aside moves E1 only from 0.125 to 0.138 —
  **the definition gap is real but is not the main reason E1 is low**; E1 also misses two thirds of the gold.
  Sequential adaptation removes almost all of the mismatch (170 -> 30) and triples the exact hits.
- **P1's hypothesis (D61) is confirmed.** Mixed into OPP-115 the AA documents are 3% of the entities and are
  largely drowned out; given as a second step they have the last word. The feared cost of the second step —
  overfitting 10 documents that share one template — did not prevent transfer to other organisations'
  documents of a different kind (lender privacy policies).
- **Rehearsal versus exam:** E1 scored about 0.09 on the adaptation documents (D60) and 0.125 on the test set —
  slightly higher, as expected for privacy policies, which are nearer to OPP-115's genre.
- **Caveats, to be stated with the result:**
  1. *Eight document groups.* The intervals are honest but coarse; with eight units a bootstrap can only move
     in steps.
  2. *One document weighs a third.* The plain average of the per-group F1 is lower than the pooled figure
     (E2-sequential 0.375 against 0.439) because `28_indifi_capital_privacy` scores above average.
     `26_zerodha_tos` scores about zero in every condition — it holds only four gold entities.
  3. *The mock test flattered, as predicted* (D62): E2-sequential scored 0.58-0.74 on the held-out adaptation
     documents and 0.41-0.48 on the test set. The mock score was used only to pick the epoch.
  4. *E2 differs from E1 in two ways,* the AA training data and the AA stopping set (D61).
  5. *The answer key has its own error rate* — about 2% wrong and about 7% missing (D58) — which caps every
     score a little below 1.0.
  6. *Exact match is harsh on boundaries*; relaxed F1 is reported beside it for that reason, not as a
     replacement.
  7. *Provenance:* the evaluation ran from an uncommitted working tree on top of commit `842e1bc` (that is the
     commit the opening log records). P1 commits immediately after, so the code that produced the numbers is
     the next commit.
- **Files (committed, numbers only):** `results/ner/aa_test.md` and `aa_test.json` (written by the new
  `collect.aa_test_report`), `ablation.md` / `.csv`, one `test_metrics.json` per run, `test_openings.jsonl`.
  The lists of spurious phrases (`test_errors.tsv`) stay under `artifacts_out/` — they contain policy text.
- **The test set is now spent.** Any further change to models, rules or gold followed by a re-score would be
  tuning on the test set. New ideas are tried on the adaptation documents only.
- **Status:** ✅ E1 and E2 complete — the headline result of the project.

### D64 — LLM baseline: the protocol, fixed BEFORE any LLM sees the test set (harness built, not yet run)
- **Why:** the first question a reviewer will ask of D63 is "how does a large language model do if you simply
  give it your guideline?" If it beats the fine-tuned models, the paper's story changes — better to know.
- **Why this does not break "the test set is spent" (D63):** that rule forbids changing something *after looking
  at test results* and scoring again. This is a new system, specified in advance, developed only on the AA dev
  documents, and scored on the test set once. The protocol below is written down before any run.
- **Protocol:**
  1. *Task.* One passage (a segment of the CoNLL file, detokenised) per request. The model returns JSON:
     a list of `{text, label}`. Temperature 0, fixed seed, JSON mode.
  2. *Prompt.* The guideline's general rules, condensed to about 470 words: the three labels, the 12 purpose
     categories, and ten rules (shortest phrase, lists, name + abbreviation, umbrella terms, AA-framework
     actors, own company, telemetry, data exchange for THIRD_PARTY, data-use frame for PURPOSE, every
     occurrence). **The guideline's "tricky cases" are not in it — they quote test documents.** The self-check
     refuses a prompt that names any test organisation.
  3. *Two conditions.* **0-shot** (rules only) and **8-shot** (rules + 8 worked passages). The 8 examples are
     drawn with a fixed seed from `aa_adapt_train.conll` only — the same ten documents E2 trains on: two
     passages with no entity, six covering all three labels.
  4. *Alignment.* Each returned phrase is matched word-for-word onto the passage (case-insensitive); every
     occurrence is tagged; longer phrases win; a phrase that is not in the passage is dropped and counted
     (hallucination rate is reported).
  5. *Scoring.* The same `evaluate.evaluate` as the fine-tuned models — exact and relaxed F1, group-bootstrap
     intervals, error breakdown — and the same paired comparison against E1 / E2.
  6. *Development.* Only on `aa_adapt_dev.conll` (the four mock-test documents). At most the two conditions
     above are carried to the test set; the prompt is frozen before `--open-test`.
- **Built:** `ner/llm_baseline.py` — standard library only (no SDK), any OpenAI-compatible endpoint, default a
  local Ollama server so no document text leaves the machine; replies cached and resumable under
  `artifacts_out/llm/` (git-ignored — they contain policy text); the test set needs `--open-test` and is
  logged like every other opening. Self-check passes (alignment, tolerant JSON parsing, deterministic examples
  taken only from the training file, no test organisation in the prompt).
- **Known limits of this baseline, to state with its result:**
  1. *A conflict of interest for Claude models.* The answer key was adjudicated with an AI assistant from the
     Claude family (D50-D59). A Claude model used as the baseline would be tested against a key it helped to
     write. The baseline should therefore be a model from another family; if a Claude model is ever added, that
     must be disclosed beside its score.
  2. *The LLM may have read the test documents.* They are public web pages; a model's pre-training data may
     contain them. It cannot have seen our labels, which were never published.
  3. *Different supervision.* The fine-tuned models learn from 332 labelled entities and never see the rules;
     the LLM sees the rules and at most 8 passages. The comparison is "which kind of effort pays", not a
     like-for-like method comparison.
  4. *A local 8-14 billion-parameter model is not a frontier model.* If only a local model is run, the paper
     must say so; a reviewer may still ask for a hosted one.
- **Blocked on P1:** no LLM is available on the machine — Ollama is installed but has no model, and no API key
  is configured. P1 must choose the model(s) and either approve a download or set a key.
- **Status:** ✅ Run as specified — results in D65.

### D65 — LLM baseline result: a local 14B model given only the rules ties the best fine-tuned model on exact F1
- **What was run (P1 chose local, open models, D64 option A):** `llama3.1:8b` (4.9 GB) and `qwen2.5:14b`
  (9.0 GB) through Ollama on the laptop's GPU — no document text left the machine. Each in two conditions,
  0-shot and 8-shot, exactly as fixed in D64. Developed on the four AA dev documents, then the test set scored
  once per run: 4 new entries in `results/ner/test_openings.jsonl` (31 in total).
- **Test set, exact-match micro-F1** (one run each, temperature 0; 95% interval over the 8 document groups),
  next to the fine-tuned conditions of D63:

  | System | Exact micro-F1 | Relaxed micro-F1 | Precision | Recall | Predicted (826 gold) |
  |---|---|---|---|---|---|
  | E1 (9 runs) | 0.125 [0.101, 0.156] | 0.293 | — | — | 944 |
  | E2-joint (9 runs) | 0.252 [0.209, 0.331] | 0.442 | — | — | 630 |
  | E2-sequential (9 runs) | 0.439 [0.352, 0.494] | 0.606 | — | — | 747 |
  | E2-sequential, Legal-BERT (3 runs) | 0.479 [0.399, 0.529] | 0.637 | — | — | — |
  | llama3.1:8b, 0-shot | 0.280 [0.221, 0.325] | 0.325 | 0.176 | 0.674 | 3,159 |
  | llama3.1:8b, 8-shot | 0.414 [0.345, 0.457] | 0.471 | 0.307 | 0.633 | 1,703 |
  | **qwen2.5:14b, 0-shot** | **0.479 [0.439, 0.514]** | 0.553 | 0.369 | 0.683 | 1,529 |
  | qwen2.5:14b, 8-shot | 0.452 [0.369, 0.501] | 0.518 | 0.321 | 0.763 | 1,961 |

- **Paired comparisons (same resamples of the groups):**
  - qwen 0-shot minus E2-sequential (all backbones): exact **+0.040 [-0.016, +0.129]** — no significant
    difference; relaxed -0.053 [-0.109, +0.036].
  - qwen 0-shot minus Legal-BERT E2-sequential: exact **+0.000 [-0.052, +0.078]** — a tie; relaxed
    **-0.084 [-0.136, -0.010]** — the fine-tuned model is better on relaxed match.
  - qwen 0-shot beats E1 by +0.354 and E2-joint by +0.227 (both intervals clear of zero).
  - llama 8-shot: level with E2-sequential overall (-0.025 [-0.092, +0.039]), behind Legal-BERT E2-sequential
    (-0.065 [-0.124, -0.010]). llama 0-shot: above E1, level with E2-joint, well behind E2-sequential.
- **What it means.**
  1. **Reading the rulebook is worth as much as 330 labelled examples.** A 14-billion-parameter open model that
     has never seen a labelled AA sentence, given a 470-word summary of the guideline, matches the best
     adapted encoder on exact F1. The claim "a little local data fixes transfer" (D63) stays true *for
     encoder models*; it is no longer the cheapest route.
  2. **The two kinds of system fail differently.** The LLM finds more (recall 0.68 against about 0.42 for
     E2-sequential) but marks about twice as much as there is (1,529 predictions for 826 entities; precision
     0.37). The fine-tuned models are more precise and stay ahead on relaxed match (0.64 against 0.55).
  3. **By label** (exact F1, qwen 0-shot against E2-sequential): THIRD_PARTY 0.606 against 0.436 — the LLM
     knows what an organisation is; PURPOSE 0.437 against 0.359; DATA_TYPE 0.433 against 0.510 — the
     fine-tuned models are better on the most frequent label.
  4. **Examples help the small model and not the large one.** llama: 0.280 -> 0.414 with eight examples (and
     hallucinated phrases fall from 413 of 3,170 to 46 of 1,595). qwen: 0.479 -> 0.452 — more recall, more
     over-marking.
  5. **The mock test misled.** On the AA dev documents the order was qwen 0-shot 0.35, llama 8-shot 0.26,
     qwen 8-shot 0.26, llama 0-shot 0.12 — far below the test scores. The dev documents are AA-operator terms
     with few entities; the test documents are denser privacy policies. No choice was made from the dev
     scores, as agreed.
- **Caveats specific to this baseline — to be printed beside the numbers:**
  1. **The rules are fitted to the corpus, test documents included.** The guideline was developed over all 23
     documents (D58), and the prompt condenses it. No test sentence is quoted, but the rules encode decisions
     that were made while reading the test documents (lenders, credit bureaus, telemetry, the 12 purpose rows).
     The fine-tuned models had no such access — they learned from ten other documents. This favours the LLM
     and cannot be removed after the fact; a fair re-test needs documents the guideline has never seen.
  2. **The prompt was written by the assistant that adjudicated the answer key** (D50-D59), from the guideline.
  3. **The LLM may have read the test documents** in pre-training (public web pages) — not their labels.
  4. **One run per condition.** Temperature 0 makes a run repeatable, not representative: there is no seed
     variation, and the 0-shot / 8-shot difference for qwen is not established.
  5. **Two open models of 8 and 14 billion parameters** — not a frontier model. A larger or hosted model would
     probably score higher still.
  6. **Cost is different in kind:** about 3-5 seconds per passage on a 16 GB GPU, against milliseconds for a
     fine-tuned encoder.
- **Run record.** A runaway reply (the small model repeating one entity without end) timed out a dev run; fixed
  before any test run by capping the reply at 1,024 tokens and keeping the complete entities of a cut-off
  reply (D64's alignment rule otherwise unchanged). The laptop shut down twice during the last test run
  (qwen 8-shot, at passages 268 and 409 of 559); replies are cached per passage and the run resumed without
  repeating a request. Ollama updated itself from 0.40.1 to 0.40.2 during the first restart: five passages
  answered before the update were asked again afterwards and came back character-for-character identical. The
  program and the test file were byte-identical throughout (checksums recorded at freeze).
- **What this does to the paper (decision for P1 — not taken here):** the headline can no longer be only
  "adaptation data fixes transfer". The stronger and more honest paper is a three-way comparison — transfer
  alone (0.13), adaptation with a few hundred labels (0.44-0.48), and a rule-prompted open LLM with none
  (0.48) — on a new, audited AA corpus, with the finding that the *guideline* is as valuable an artefact as
  the labelled data. The corpus's role shifts from training set to benchmark.
- **Files:** `results/ner/aa_test.md` / `.json` now include the LLM section (`collect.aa_test_report`);
  `results/ner/llm_<run>/test_metrics.json` (numbers only). Raw replies stay in `artifacts_out/llm/`
  (git-ignored — they quote the policies).
- **Status:** ✅ Done. The test set has now been opened for 31 pre-specified runs and for nothing else.
