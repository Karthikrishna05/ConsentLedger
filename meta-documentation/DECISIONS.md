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
