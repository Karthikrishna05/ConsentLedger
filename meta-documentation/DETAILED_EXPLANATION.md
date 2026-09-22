# ConsentLedger — Detailed Explanation (the project "bible")

**Purpose of this file.** Read this and you understand the *entire* project — what it does, why every
decision was made, and how every line of code works — well enough to explain it to an examiner or
re-implement it yourself, no AI needed. Language is deliberately simple, with analogies. **Keep this file
updated whenever anything new is built** (it is part of the audit trail).

> Companions: `OVERVIEW.md` (short plain-language tour), `DECISIONS.md` (why each choice, D1–D22),
> `FLOW.md` (progress), `NER_LABEL_MAPPING.md`, `TEAM.md`, `SETUP.md`, `DEADLINE_PLAN.md`,
> `ANNOTATION_GUIDELINE.md`. This file is the deep version of all of them combined.

---

## Table of contents
1. The big picture (what & why)
2. Core concepts (glossary with analogies)
3. Repository structure
4. The environment (venv, libraries, CUDA, editable install)
5. Data pipeline — file by file
   - 5.1 `scaffold.py`
   - 5.2 The external datasets (what OPP-115 actually is)
   - 5.3 `load_opp115.py`
   - 5.4 `bio_tagging.py`
   - 5.5 `scrape_aa.py`
   - 5.6 `clean.py`
6. NER model pipeline — file by file
   - 6.1 `seed.py`
   - 6.2 `ner/dataset.py`
   - 6.3 `ner/train.py`
   - 6.4 `ner/evaluate.py`
   - 6.5 the config files
7. How everything connects (end-to-end)
8. Current state: done vs pending
9. Every output file, explained

---

## 1. The big picture (what & why)

**ConsentLedger** takes a dense financial *consent* document (the fine print you approve when an app
wants to pull your bank data under India's RBI **Account Aggregator (AA)** system) and does three things:

1. **Extracts the key facts** with an NLP model (a "smart highlighter").
2. **Rewrites them in plain English** and **checks that plain version didn't lie** (drop or invent facts).
3. **Records the consent on a blockchain** so there's a tamper-proof audit trail.

> **Analogy.** It turns fine print into a **nutrition label + a receipt**: the label says what's inside
> in plain terms; the receipt is proof of what you agreed to that nobody can secretly alter later.

**The research question** (what makes it a paper, not just an app): *Can NLP models trained on ordinary
website/app privacy policies generalize to the under-studied Indian AA consent domain — and how much does
a little AA-specific training help?* We test this as two conditions on the **same** held-out AA test set:
- **E1 (pure transfer):** train only on outside data (OPP-115) → test on AA docs.
- **E2 (domain-adapted):** train on outside data **+ a few AA docs** → test on the same AA docs.

> **Analogy — learning to drive.** E1: "can a Delhi-trained driver drive in Mumbai cold?" E2: "does a few
> hours of Mumbai practice help?" Comparing E1 vs E2 is the result — good *whatever the numbers say*.

**Why this shape of project?** We have very few AA documents (~23 usable). Training a model from scratch
on 23 docs is hopeless, so we *transfer* knowledge from a big labelled privacy-policy corpus (OPP-115)
and measure how well it carries over. Small AA data becomes the *experiment's variable*, not a weakness.

---

## 2. Core concepts (glossary with analogies)

- **NER (Named Entity Recognition).** Teaching a model to highlight specific kinds of phrases in text.
  Ours highlights three: **DATA_TYPE** (a kind of data, "bank statements"), **PURPOSE** (why, "loan
  assessment"), **THIRD_PARTY** (who else gets it, "credit bureaus"). *Analogy: a highlighter that only
  colours those three categories.*

- **Token.** A word (or word-piece) the model reads one at a time. The model outputs **one label per
  token**.

- **BIO tagging.** How we write a multi-word highlight as per-token labels: **B-**X = beginning of an
  entity of type X, **I-**X = inside (continuation), **O** = outside (not an entity). *Analogy: a train —
  B is the engine, I are the carriages, O is empty track. The engine marker lets you tell two trains
  parked nose-to-tail apart.* Example: "mutual fund units" → `B-DATA_TYPE I-DATA_TYPE I-DATA_TYPE`.

- **Character offsets / spans.** The exact start/end character positions of a highlighted phrase in the
  text. Ground truth for where an entity is. *Analogy: "the highlight runs from character 200 to 209."*

- **Subword tokenizer.** Modern models split words into pieces ("statements" → "state","ments"). Each
  model splits differently, so we store labels at the **word** level and let each model align its own
  subwords at training time.

- **Transfer learning / fine-tuning.** Take a model already pretrained on huge text, then train it a bit
  more on *our* task. *Analogy: hiring someone who already speaks English and teaching them your company's
  jargon, vs. teaching a baby to talk.*

- **E1 / E2.** The two training conditions above (transfer only vs transfer + a little AA).

- **seqeval / entity-level F1.** The scoring method for NER. It checks whole *entities* (did you get
  "mutual fund units" exactly right?), not individual tokens. **Precision** = of the entities you
  predicted, how many were correct. **Recall** = of the real entities, how many you found. **F1** =
  their balance. *Analogy: precision = "of the fish you caught, how many were the target species";
  recall = "of all target fish in the lake, how many you caught."*

- **The consent artefact (ReBIT JSON).** In the real AA system, a consent is also stored as a
  machine-readable form (JSON) with clean fields (how long, how often, which company). ReBIT (an RBI-owned
  body) defines that form's shape. So some facts we **read from fields** instead of highlighting from
  prose — see "split by source" below.

- **Split by source (a key design).** Facts that appear as prose → NER (DATA_TYPE/PURPOSE/THIRD_PARTY).
  Facts that are structured fields → read directly (DURATION/FREQUENCY/RECIPIENT). *Analogy: a wedding
  invitation — read the date off the RSVP card's box, don't parse it out of the flowery paragraph.*

- **Why the prose docs have no frequency/duration (verified — D27).** While annotating, P1 correctly
  noticed the scraped T&C/privacy docs never state "fetched daily" or "valid until 26 Jan". That's
  expected: those are **per-consent values that only exist in the ReBIT consent-artefact JSON** created
  when a real consent is granted — not in the human-readable pamphlets. *Two different things called "the
  AA document": (1) the pamphlet you annotate = prose, no numbers; (2) the consent artefact = a JSON
  "receipt" with the numbers in labelled boxes.* We verified against a **primary source** (two real
  Sahamati artefacts) that the boxes are real and named exactly: DURATION=`consentStart`/`consentExpiry`,
  FREQUENCY=`Frequency{unit,value}`, RECIPIENT=`DataConsumer{id}` (a coded id like `DC1`, not a name),
  plus `FIDataRange`, `DataLife`, `fetchType`, `Purpose{code,text}`. So split-by-source is grounded, not
  assumed. **Caveat:** our scraped corpus has ~0 real artefacts, so the parser's data = the 2 real
  examples + **synthetic** ones from `gen_consent_artefacts.py`; the parser is described as a
  *deterministic schema reader*, not an evaluated ML model. Fixtures + field-map live in
  `data/aa/consent_artefacts/` (with a README). NER E1/E2 stays the headline; this is a support component.

---

## 3. Repository structure

```
ConsentLedger/
├── README.md                 landing page: clone → setup → run
├── pyproject.toml            makes `consentledger` an importable package
├── requirements*.txt         pinned libraries (+ .lock for exact repro)
├── .gitignore/.gitattributes git hygiene (no datasets/venv committed; LF endings)
├── scaffold.py               one script that (re)creates the empty folder skeleton
├── configs/                  one YAML per experiment (model + hyperparameters)
├── src/consentledger/        THE code package
│   ├── seed.py               determinism helper
│   ├── data/                 load_opp115, bio_tagging, scrape_aa, clean, kappa, ...
│   ├── ner/                  dataset, train, evaluate, predict
│   ├── summ/  chain/  pipeline/  consent_artefact/   (later phases, still stubs)
├── data/
│   ├── external/             DOWNLOADED corpora (git-ignored): opp115, mapp, app350, cuad
│   ├── aa/                   our AA corpus: manifest.csv, raw/{html,pdf,text}, annotated/
│   ├── ner_bio/              train.conll / dev.conll (git-ignored, regenerable)
│   └── splits/               splits.json (which AA docs are test vs adaptation)
├── artifacts_out/            trained models (git-ignored, large)
├── results/                  metrics/tables (committed, small)
├── tests/                    verification gates
└── meta-documentation/       ALL docs (this file lives here)
```

---

## 4. The environment (venv, libraries, CUDA, editable install)

- **venv** = a private box of Python libraries for this project, so it doesn't clash with other projects.
  Created with `py -3.11 -m venv .venv`, activated per terminal. *Analogy: a separate toolbox per job.*
- **`requirements.txt`** pins exact library versions. The load-bearing pin is **`numpy==1.26.4`** (< 2.0)
  — it's the compatibility anchor that keeps torch, spaCy, bert-score, pandas from fighting.
- **torch (the deep-learning engine)** is installed *separately* from a special CUDA index
  (`--index-url .../cu121`) so it uses the **GPU**. Its wheels bundle their own CUDA runtime, so only a
  recent NVIDIA driver is needed. On this machine `torch.cuda.is_available()` is `True` on an RTX A4500.
- **`pip install -e .`** ("editable install") registers the `consentledger` package so you can run
  `python -m consentledger.data.load_opp115` from anywhere. `pyproject.toml` says the code lives under
  `src/`. *Analogy: adding the toolbox to your PATH so tools are callable by name.*
- **spaCy model** `en_core_web_sm` is downloaded once (a small English model, for noun-chunk helpers).
- Verified with `pip check` → "No broken requirements found" (no version conflicts).

---

## 5. Data pipeline — file by file

### 5.1 `scaffold.py` — builds the empty skeleton

**Job:** create every folder and placeholder file the project expects, safely and repeatably. *Analogy:
laying out labelled empty drawers before you start filling them.*

- `DIRS` — a list of every directory to create. `PACKAGES` — dirs that need an `__init__.py` (that empty
  file is what makes a folder an importable Python package). `GITKEEP` — dirs that should stay in git even
  while empty (git ignores empty folders, so a `.gitkeep` file holds their place).
- `STUB_FILES` — a dict of `path → starter content` (docstring + `TODO`) for each code file. `CONFIGS`
  generates the YAML config files by looping over the backbones (`_ner_config`).
- `main()` — parses `--dry-run` (preview without writing). Two helpers, `ensure_dir` and `ensure_file`,
  are **idempotent**: they create only what's missing and **never overwrite** an existing file, and they
  refuse to touch protected dirs (`.venv`, `meta-documentation`). So re-running it is always safe.

*Why it matters:* after someone clones the repo, the git-ignored data folders don't exist. Running
`python scaffold.py` recreates them so the download/scrape commands have somewhere to write.

### 5.2 The external datasets (what OPP-115 actually is)

We train the NER model on **OPP-115** — 115 real website privacy policies, hand-annotated by law
students (Wilson et al., ACL 2016). Its files (verified by reading the corpus manual):

- `annotations/<id>_<site>.csv` — one row per **data practice**, **no header**, 9 columns. The important
  ones: **col E** = segment id, **col F** = category (e.g. "First Party Collection/Use"), **col G** =
  attribute-value pairs as **JSON**.
- Column G JSON looks like: `{"Personal Information Type": {"selectedText": "email address",
  "startIndexInSegment": 200, "endIndexInSegment": 209, "value": "Contact"}}`. So each attribute carries
  the **exact phrase** and its **character offsets *within the segment***.
- `sanitized_policies/<id>_<site>.html` — the policy text, split into **segments** by the delimiter
  `|||`. Offsets in the CSV are relative to a segment.
- `consolidation/threshold-{0.5,0.75,1.0}-overlap-similarity/` — the same data but with the 3 annotators'
  overlapping picks **merged** (we use threshold 0.75).

**MAPP** and **APP-350** turned out to be *segment-level only* (no character offsets), so they can't feed
token-level NER — they're demoted to optional/auxiliary (see DECISIONS D16). **CUAD** is legal-contract
clauses, also auxiliary. So **OPP-115 is the sole span-level training source.**

### 5.3 `load_opp115.py` — OPP-115 → clean span records

**Job:** turn OPP-115's messy CSVs into a clean list of *span records* (one per highlighted phrase we
care about), and **refuse to continue if the offsets don't line up** (a safety gate). Output:
`data/external/opp115/processed/opp115_spans.jsonl` (one JSON object per line).

*Analogy: a strict librarian copying only the three kinds of index cards we want, and checking each card
against the actual book page before filing it.*

**Key constants:**
- `LABEL_MAP` — the *only* three attributes we keep and what they become:
  `Personal Information Type → DATA_TYPE`, `Purpose → PURPOSE`, `Third Party Entity → THIRD_PARTY`.
- `DROP_VALUES = {"Unspecified", "not-selected"}` — skip vague picks. `DROP_CATEGORIES = {"Other"}`.
- `SEGMENT_DELIM = "|||"`, `GATE_MIN_MATCH_RATE = 0.99`.
- `C_ANN_ID … C_DATE = range(9)` — names for the 9 CSV columns so the code reads clearly.

**Functions:**
- `load_errant_ann_ids()` — OPP-115 ships a list of annotation IDs with known-buggy offsets
  (`documentation/errant_span_indexes/`); this reads them so we can skip them.
- `csv_dir()` — returns the folder to read: `consolidation/threshold-0.75-...` by default (or raw
  `annotations/` if you pass `--source annotations`).
- `segments_for(stem)` — reads a policy's sanitized text and `split("|||")` → the list of segments.
- `main()` walks every CSV. For each row it: skips `Other` category and errant IDs; parses the segment id
  and the column-G JSON; then for each attribute in that JSON:
  1. map it via `LABEL_MAP` (skip if not one of our three),
  2. skip `Unspecified`/`not-selected` values,
  3. read `start`, `end`, `selectedText`; guard against missing/negative offsets,
  4. get the segment text, compute `recon = segment[start:end]`,
  5. **the gate check:** if `recon == selectedText`, keep it. If not, try a small **whitespace
     re-alignment** (some OPP-115 offsets are off by a leading/trailing space) and re-check.
  6. keep the record with full **provenance** (policy_id, segment_id, label, offsets, value, annotator,
     annotation_id).
- At the end it writes the JSONL, prints per-label counts and a 20-span spot-check, and **the GATE**: if
  fewer than 99% of spans reconstructed exactly, it `sys.exit`s with an error so you never train on
  silently-wrong data.

**Result we got:** 24,516 verified spans (DATA_TYPE 10,542 / PURPOSE 9,894 / THIRD_PARTY 4,080), match
rate 0.9928 → **GATE PASSED**.

### 5.4 `bio_tagging.py` — span records → word-level BIO CoNLL

**Job:** convert those span records into the actual training file the model reads: **CoNLL** format
(one `word <TAB> tag` per line, a blank line between segments). Output: `data/ner_bio/train.conll` and
`dev.conll`.

*Analogy: taking the librarian's index cards and the book, and writing in the margin of every word
whether it's the start of a highlight, inside one, or plain text.*

**Functions:**
- `tokenize_with_offsets(text)` — splits text into words **with their character positions** using the
  regex `\w+|[^\w\s]` (a run of word-characters, OR a single punctuation mark). Offset-aware, never a
  naive `.split()` that would lose positions.
- `resolve_overlaps(spans)` — OPP-115 segments often have overlapping/nested highlights (e.g. "names,
  e-mail" inside "names, e-mail and website addresses"). This keeps the **longest** span and drops any
  that overlap it, so each stretch of text gets one clean label. *Analogy: if two highlighters overlap,
  keep the bigger stroke.*
- `bio_for_segment(text, spans)` — tokenises the segment, starts every token as `O`, then for each
  resolved span marks the tokens it covers: the first gets `B-LABEL`, the rest `I-LABEL`.
- `load_opp115_segments()` — groups all spans by (policy, segment) and, crucially, reads **every**
  segment of each policy (including ones with **no** entities) so the model also learns what *isn't* an
  entity (negative examples).
- `write_conll(path, policies, data)` — writes the CoNLL lines for a set of policies; counts segments,
  tokens, and entities per label.
- `reconstruct(rows)` — rebuilds entities back out of the BIO tags; used by the **self-check** at the end
  to prove the round-trip is correct (`assert` that reconstructed labels ⊆ input labels).
- `main()` — shuffles the 115 policies with a fixed seed and splits **by policy** (90% train / 10% dev)
  so no policy's sentences leak across the split, then writes both CoNLL files.

**Design note (D18):** we store **word-level** tags shared by all backbones; each model aligns its own
subwords at training time. This is simpler than regenerating per model and still fully offset-based.

**Result:** 103 train / 12 dev policies; train ~3,362 segments, entities DATA_TYPE 2,950 / PURPOSE 2,696
/ THIRD_PARTY 1,130. (Entity count < span count because overlaps were collapsed.)

### 5.5 `scrape_aa.py` — download the AA documents

**Job:** fetch the 29 real AA documents listed in `data/aa/manifest.csv` into `data/aa/raw/{html,pdf}`,
politely and once. *Analogy: photocopying each source document once and keeping the copies in labelled
folders, with a logbook of when and what.*

- Reads the manifest (columns: `doc_id, rank, organization, role, doc_type, tier, format, url`).
- For each row: skip if already downloaded (unless `--force`); `GET` the URL with a browser-like
  User-Agent and a timeout; save the raw bytes to `<doc_id>.html` or `.pdf`; record HTTP status, byte
  size, and a content hash to `data/aa/raw/scrape_log.csv`; wait 1.5s between requests (politeness).
- Prints a summary and lists failures.

**Result:** 28/29 downloaded. Bajaj (row 27) returned 403 (bot-blocked); ~5 others came back as tiny
JavaScript shells (their real text loads via JS, which `requests` can't run).

### 5.6 `clean.py` — raw HTML/PDF → clean, normalized text

**Job:** turn the raw downloads into plain text an annotator can read, and normalize awkward characters.
Output: `data/aa/raw/text/<doc_id>.txt`. *Analogy: scanning a messy web page down to just the readable
words, then tidying the punctuation.*

- `clean_html(bytes)` — uses BeautifulSoup to **remove** noise tags (`script, style, nav, footer, header,
  form, …`) and elements whose class/id looks like chrome (`cookie|nav|footer|menu|popup…`), then takes
  the text of `<main>`/`<article>`/`<body>`.
- `clean_pdf(path)` — uses pdfplumber to extract each page's text.
- `_TRANS` (the normalization table, D22) — applied to all output: unicode spaces (incl. `\xa0`
  no-break space) → normal space; **curly quotes → straight**; zero-width chars and stray UI symbols
  (bullets `•●·`, icons `⛔⚠ℹ↓`) removed. **Em/en dashes and all real content are kept.**
- `_normalize(text)` — applies `_TRANS`, collapses runs of spaces, strips each line, drops blank lines,
  collapses 3+ newlines to 2.
- `main()` — processes every raw file; if the cleaned text is shorter than `--min-chars` (default 800) it
  flags the doc as a **thin/JS-shell** and skips it (this is what filters out the failed scrapes).

**Result:** 23 usable docs (median ~3,100 words); 5 thin shells dropped; a re-scan confirmed only
legitimate em/en dashes remain.

### 5.7 `ls_import_export.py` + `kappa.py` — annotation tooling

**`ls_import_export.py make-tasks`** turns the 23 cleaned `.txt` files into one Label Studio import file
(`data/aa/annotated/ls_import_tasks.json`), each task carrying `doc_id` + `text`. *Why: importing this
(not raw .txt) keeps the `doc_id`, which κ uses to match the two annotators' exports.*

**`kappa.py`** measures inter-annotator agreement from two Label Studio JSON exports. It parses each
export into `{doc_id: {text, spans}}`, then for each shared doc it tokenizes the text **once** (via
`bio_tagging.bio_for_segment`) and maps **both** annotators' spans onto those same tokens — so the
comparison is on one shared tokenization, full document, no truncation (avoids the classic κ bug, D10).
It reports **entity-level P/R/F1 (primary)** and **token-level Cohen's κ (secondary)**, per-doc κ, a
PASS/refine verdict vs a 0.6 gate, and saves `results/annotation/kappa.json` + `kappa_per_doc.csv`. It
works on 1 doc (the calibration pilot) or all 23 (the final number). *Analogy: two referees scoring the
same match on the same rulebook — κ says how often they call it the same way.* Full workflow (calibration
pilot → full double-annotation → adjudicate) is in `ANNOTATION_GUIDELINE.md` (D24).

**`--show-diff` (calibration aid):** the score alone tells you *how much* two annotators disagree, not
*where*. When a pilot lands below the gate you need the actual disputed phrases to fix the guideline.
Passing `--show-diff` prints, per doc, every span one annotator marked and the other didn't (with the
surface text and char offsets), grouped by label. A phrase appearing as **both** `A-only` and `B-only`
with overlapping offsets = a boundary disagreement (both caught it, drew edges differently); a phrase on
only one side = a genuine disagreement on whether it's an entity at all. *Analogy: not just "the referees
disagreed 40% of the time" but the exact replays they called differently.* This is what turns a
"BELOW GATE" verdict into a concrete list to calibrate on (guide Part F5). Added because the pilot on
`29_icici_home_fin_terms` came in at κ 0.587 with PURPOSE (entity-F1 0.35) the sole culprit.

---

## 6. NER model pipeline — file by file

### 6.1 `seed.py` — make runs repeatable

`set_seed(seed=42)` fixes the random number generators in `random`, `numpy`, and `torch` (plus
`PYTHONHASHSEED`, and `cudnn.deterministic=True`). Called at the top of training so the same seed gives
the same result. *Analogy: shuffling a deck the exact same way every time so the game is reproducible.*

### 6.2 `ner/dataset.py` — CoNLL → model-ready tensors

- `LABELS` — the 7 tags (`O` + B/I × 3 labels); `LABEL2ID`/`ID2LABEL` map them to numbers and back
  (models work in numbers).
- `read_conll(path)` — reads a CoNLL file back into a list of `{tokens, tags}`, one per segment (blank
  line = segment boundary).
- `build_dataset(path, tokenizer, max_length)` — the important one. For each segment it runs the model's
  subword tokenizer with `is_split_into_words=True`, then **aligns labels** using `word_ids()`:
  - special tokens (`[CLS]`, `[SEP]`) → label **-100** (means "ignore in the loss"),
  - the **first** subword of a word → that word's label,
  - later subwords of the same word → **-100**.
  *Analogy: if "statements" becomes "state"+"ments", only "state" carries the highlight colour; "ments"
  is marked "don't grade me."* This is how we keep word-level labels while using any model's subwords.

### 6.3 `ner/train.py` — fine-tune a backbone

**Job:** train one model on the CoNLL data, score it on dev with entity-level metrics, and save the best
version. Driven by a YAML config so hyperparameters aren't buried in code.

- `make_compute_metrics()` — builds the scoring function: it takes the model's predictions, drops the
  -100 positions, converts numbers back to tag strings, and runs **seqeval** to get entity-level
  precision/recall/F1 (micro) and macro-F1. (Entity-level, never token-accuracy, because "O" dominates
  and token-accuracy would look falsely high.)
- `main()`:
  1. loads the YAML config and `set_seed`,
  2. loads the tokenizer and `AutoModelForTokenClassification` with `num_labels=7` and the id↔label maps,
  3. builds train/dev datasets and a `DataCollatorForTokenClassification` (pads batches, pads labels with
     -100),
  4. sets `TrainingArguments`: evaluate + save each **epoch**, `load_best_model_at_end`, `bf16=True` on
     GPU (fast, stable on the A4500), early stopping,
  5. runs `Trainer.train()`, evaluates, and **saves** the best model + tokenizer + `dev_metrics.json` +
     `run_meta.json` (config, seed, git commit — so every result traces back to how it was made).
- Flags: `--config`, `--epochs`, `--smoke` (fast pipeline test), `--seed N` (override the config seed for
  multi-seed runs; suffixes the output dir `_sN` so runs don't overwrite each other).
- Metrics reported/saved: **entity** micro-F1 + macro-F1 (strict exact-match) **and token-F1**
  (token-level, fairer when spans are long) — plus precision/recall. `run_meta.json` also records the
  `condition` (E1/E2). Multi-seed rigor: run each config with `--seed 42/43/44`, then `collect.py`
  reports mean ± std.

**Smoke test result:** F1 rose 0.0 → 0.034 over 5 epochs on a 600-sample subset while loss fell
0.80 → 0.63 — proving the pipeline *learns* correctly (the point of a smoke test; real runs use all data).

### 6.4 `ner/evaluate.py` — score a trained model

Loads a saved model and a CoNLL file, predicts, and prints a full seqeval `classification_report`
(per-label + micro/macro P/R/F1). **The test set is opened exactly once, in Phase 6** — the file header
says so; day-to-day you point it at dev.

### 5.8 `trim_spans.py` — shorten OPP-115 spans to entity-shaped noun phrases

**Job:** OPP-115 spans are long clauses (PURPOSE median ~14 tokens); strict exact-match F1 is nearly
impossible on those, and they don't match our short AA target. `trim_spans.py` reads
`opp115_spans.jsonl` and writes a **separate** `opp115_spans_trimmed.jsonl` (original preserved),
reducing each span to its **longest spaCy noun chunk**, capped at 6 tokens (head-final), recomputing the
character offsets so they still point into the segment. *Analogy: highlighting just "credit bureaus"
instead of the whole sentence that mentions them.* Result: median span 6→2 tokens. Then
`bio_tagging.py --spans opp115_spans_trimmed.jsonl` builds the training CoNLL from the trimmed spans
(the original CoNLL is regenerable by running `bio_tagging` with no flag). Why: better exact-match AND
better transfer to the short-span AA test (D25).

### 6.5 `ner/collect.py` — gather citable metrics (without the weights)

**Job:** after training, pull each model's tiny `dev_metrics.json` + `run_meta.json` out of the
git-ignored `artifacts_out/ner/` and into the committed `results/ner/`, plus write a side-by-side
`ablation.csv` and `ablation.md`. *Analogy: you keep the exam **scores** on file (small, shareable) but
not every student's full answer booklet (huge).* The weights themselves go to the Hugging Face Hub
(D23), not git — they're ~400–500 MB each and reproducible from config+seed+data. Run:
`python -m consentledger.ner.collect`.

It folds in **AA-test** results too: run `evaluate.py --out artifacts_out/ner/<name>/test_metrics.json`
on the annotated AA test set, and `collect.py` adds `test_macro_f1`/`test_micro_f1` columns next to the
dev numbers (shown as `-` until that eval exists), tagged by **E1/E2 condition** (read from
`run_meta.json`'s `condition`, default `E1`). So one `ablation.csv`/`ablation.md` ends up holding the
whole story: each backbone × E1/E2 × dev/AA-test.

**Missing-seed guard:** `collect.py` only *reads* metrics — it never re-runs a model — so if one seed
crashed and never wrote `dev_metrics.json`, that run is silently absent and a group's `n_seeds` quietly
drops (e.g. 3→2). To catch this, after printing the table it infers the expected count as the largest
`n_seeds` seen across groups and warns for any `(backbone, condition)` group that has fewer, naming which
and by how much. *Analogy: the class register expects everyone present; if one seat is empty it flags the
name rather than silently averaging the rest.* So after a sweep, eyeball the output — every backbone
should say `x3`; a warning means re-run the missing seed.

### 6.6 The config files (`configs/*.yaml`)

Each experiment is one YAML: `model_name` (the HF id), `labels`, `seed`, `learning_rate`,
`num_train_epochs`, batch size, early-stopping patience, and the train/dev file paths. Three NER configs
(`ner_bert_base`, `ner_legalbert`, `ner_inlegalbert`) and two summarizer configs. *Analogy: a recipe
card — same method, swap one ingredient (the backbone) to compare fairly.*

---

## 7. How everything connects (end-to-end)

```
DOWNLOAD                 CONVERT                         TRAIN / EVALUATE
OPP-115 (usableprivacy) → load_opp115.py → spans.jsonl → bio_tagging.py → train.conll/dev.conll
                                                                              │
                                                                     ner/dataset.py (align subwords)
                                                                              │
                                                                     ner/train.py → model + dev metrics
                                                                              │
AA docs (manifest) → scrape_aa.py → raw html/pdf → clean.py → 23 text docs → [ANNOTATE] → AA test.conll
                                                                              │
                                                              ner/evaluate.py → E1 / E2 results
```

The AA branch's last step (annotate) is human work (the team), using `ANNOTATION_GUIDELINE.md`. Once the
AA docs are annotated, they run through the *same* span→BIO machinery and become the test set (E1) and a
small training add-on (E2).

---

## 8. Current state: done vs pending

**Done & verified:** environment; `scaffold.py`; OPP-115 downloaded + `load_opp115.py` (24,516 spans,
gated) + `bio_tagging.py` (train/dev CoNLL); **`trim_spans.py`** (long spans → short noun phrases,
median 6→2, original preserved) + **token-F1** + **multi-seed (`--seed`)** + **`collect.py`** (mean±std);
AA scraped (28/29) + cleaned + normalized (23 usable docs); annotation tooling (`ls_import_export
make-tasks`, `kappa.py`) + **`ANNOTATION_GUIDELINE.md` v3** (beginner-proof) + kit zip sent to P4 (D26);
pre-training code committed.

**Key result so far (D25):** the span-trimming fix lifted OPP-115 dev entity-F1 from **0.12 → 0.38**
(token-F1 0.53) on BERT-base — confirming the earlier low score was span-shape, not training. The full
3-backbone × 3-seed sweep is running; **the AA test set (E1/E2) is the headline number**, produced after
annotation.

**Pending:** finish the 3×3 seed sweep → `collect.py`; team annotates the 23 AA docs (→ ~15 test + ~8
adaptation, calibration-pilot-first per D24); build the export→`aa_test.conll` converter; run E1/E2 on
AA; upload weights to HF Hub; summarizer + faithfulness metric; smart contract; integration; paper. See
`FLOW.md` for live status and `DECISIONS.md` (D1–D26) for the reasoning behind every choice.

---

## 9. Every output file, explained

- `data/external/opp115/processed/opp115_spans.jsonl` — one line per verified OPP-115 highlight
  (label + text + offsets + provenance). Git-ignored (contains OPP-115 text).
- `data/ner_bio/train.conll`, `dev.conll` — the word+tag training/dev files. Git-ignored, regenerable.
- `data/aa/manifest.csv` — the 29 AA docs (URLs + metadata). **Committed** (just URLs).
- `data/aa/raw/{html,pdf}/*` — raw downloads. Git-ignored (copyrighted pages).
- `data/aa/raw/text/*.txt` — the 23 cleaned, normalized, annotation-ready docs. Git-ignored.
- `data/aa/raw/scrape_log.csv` — provenance of the scrape (status, bytes, hash, date).
- `artifacts_out/ner/<config>/` — a trained model + `dev_metrics.json` + `run_meta.json`. Git-ignored.

---

*Maintenance: update this file whenever new code or data steps are added — it is the single place a new
teammate (or examiner) should be able to learn the whole project from.*
