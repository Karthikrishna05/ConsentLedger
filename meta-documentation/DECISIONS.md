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
