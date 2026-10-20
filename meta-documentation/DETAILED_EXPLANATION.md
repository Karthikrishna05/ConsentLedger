# ConsentLedger — Detailed Explanation (the project "bible")

**Purpose of this file.** Read this and you understand the *entire* project — what it does, why every
decision was made, and how every line of code works — well enough to explain it to an examiner or
re-implement it yourself, no AI needed. Language is deliberately simple, with analogies. **Keep this file
updated whenever anything new is built** (it is part of the audit trail).

> Companions: `OVERVIEW.md` (short plain-language tour), `DECISIONS.md` (why each choice, D1–D85),
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
   - 5.7 `ls_import_export.py` + `kappa.py` (annotation tooling)
   - 5.8 `trim_spans.py`
   - 5.9 Annotation, start to finish (5.9.1-5.9.27): round 1 (kappa 0.28), the rescue tools, rounds 2-4,
     Rules 7-23, the fix pass (kappa 0.43), adjudication and the gold file, the rules meeting
   - 5.10 The summarizer dataset and P2's models — P2's track (D33, D34, D67-D70, D72, D73)
   - 5.11 The smart contract — P3's track
   - 5.12 The test / adaptation split and the gold -> CoNLL converter (D52)
   - 5.13 The faithfulness gate — `summ/faithfulness.py` (D74)
6. NER model pipeline — file by file
   - 6.1 `seed.py`
   - 6.2 `ner/dataset.py`
   - 6.3 `ner/train.py`
   - 6.4 `ner/evaluate.py`
   - 6.5 `ner/collect.py`
   - 6.6 the config files
   - 6.7 The headline result (D63)
   - 6.8 `ner/llm_baseline.py` (D64, D65)
7. How everything connects (end-to-end)
   - 7.1 What is still to be connected
   - 7.2 The two splits do not line up
   - 7.3 Testing it as one pipeline
   - 7.4 Deploying it
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

**What is new and what is not (D28).** A literature search (arXiv, PubMed/PMC and the web; full record in
`RELATED_WORK.md`) was run after P1 noticed that the RBI rules already require consent artefacts to be
"logged, audited and verified". It settled what the project may honestly claim:
- **Blockchain consent registries are not new.** *Soteria* (arXiv:2003.10128) already stores hashes of
  data-sharing agreements on a ledger for revocation and compliance; the create-grant-revoke lifecycle is a
  published pattern (*Grant, Verify, Revoke*, arXiv:2603.15721); a systematic review covers 55 studies.
- **Entity-based summary faithfulness is not new.** arXiv:2102.09130 is the standard entity-level metric,
  and **EROS** (arXiv:2403.00141) already does entity-controlled summarisation *of privacy policies*.
- **Indian AA consent-document NLP is genuinely empty** — a dedicated search found no research at all.
So the paper is a **resource + application study**: the first annotated AA consent corpus and transfer
benchmark, plus a reference pipeline (extraction -> disclosure-fidelity check -> tamper-evident record)
motivated by a real gap — the rules require the user to be *informed*, but nothing verifies that the
informing was *accurate*. The blockchain part is a reference implementation, not a contribution.
*Analogy: you didn't invent the lock or the camera; you are the first to survey this particular building
and show how the two can be fitted to it.* Before submission, repeat the searches in ACL Anthology,
Scopus, IEEE Xplore and ACM DL — only then is "to the best of a systematic search" fully earned.

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

- **The formal schema, and the official purpose codes.** `consent_artefact_schema.json` (JSON Schema,
  draft-07) is the *blank form* of a consent artefact: every box, its type and allowed values (e.g.
  `fetchType` is ONETIME or PERIODIC). `python -m consentledger.data.gen_consent_artefacts --validate`
  confirms the real one-time example and 50 synthetic artefacts all fit it. (The periodic example on the
  source page shows some boxes outside `ConsentDetail` — a page-rendering quirk, so readers look boxes up
  by name rather than by fixed position.) The **ReBIT purpose codes** are: **101** wealth management,
  **102** spending patterns / budgeting, **103** aggregated statement, **104** explicit consent for account
  monitoring, **105** explicit one-time consent. Only the **code** is standardised — `Purpose.text` is
  free text (a published example pairs code 103 with "To process borrower's loan application"). That is
  exactly why checking what the policy *text* says against the *declared* code is a meaningful test (D35).

---

## 3. Repository structure

```
ConsentLedger/
├── README.md                 landing page: clone → setup → run
├── pyproject.toml            makes `consentledger` an importable package
├── requirements*.txt         pinned libraries (+ .lock for exact repro)
├── .gitignore/.gitattributes git hygiene (no datasets/venv committed; LF endings)
├── scaffold.py               one script that (re)creates the empty folder skeleton
├── app.py                    the demo web page (Gradio) over pipeline/end_to_end.run (D80)
├── space/                    the Hugging Face Space card, requirements and builder (D84)
├── configs/                  one YAML per experiment (model + hyperparameters)
├── src/consentledger/        THE code package
│   ├── seed.py               determinism helper
│   ├── data/                 load_opp115, bio_tagging, scrape_aa, clean, kappa, fixlist, adjudicate,
│   │                         adjudicate_auto, aa_split, aa_to_conll, ...
│   ├── ner/                  dataset, train, evaluate, collect, llm_baseline, predict (text -> highlights)
│   ├── summ/                 build_dataset, train (P2's, handed to P1 - D77); faithfulness (D74);
│   │                         predict (passages -> summaries, D76); dataset/evaluate still stubs
│   ├── consent_artefact/     parse (the five structured facts, D76)
│   ├── chain/                P3's contract client (D75)
│   ├── pipeline/             end_to_end (the whole system in one command, D79)
├── data/
│   ├── external/             DOWNLOADED corpora (git-ignored): opp115, mapp, app350, cuad
│   ├── aa/                   our AA corpus: manifest.csv, raw/{html,pdf,text}, annotated/
│   ├── ner_bio/              train.conll / dev.conll, aa_test.conll / aa_adapt.conll (git-ignored)
│   └── splits/               aa_split.json (which AA docs are test vs adaptation - doc ids only)
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

**Exporting from Label Studio — four practical rules learned the hard way.** (1) Always export the
**whole project**: Label Studio ignores the filters you set on screen, so "export just these two
documents" is unreliable — export everything and use `kappa.py --docs <doc_ids>` to score a subset.
(2) **Only submitted work is exported**: a re-annotated document that was not clicked *Submit* (or
*Update*) stays a draft and silently keeps its old version. (3) Use **JSON**, not JSON-MIN — the full
format keeps the `doc_id` everything matches on. (4) Name each round's files distinctly:
`ExportA/B.json` (round 1), `Export2A/B.json` (round-2 calibration), `Export3A/B.json` (round 3),
`Export4A/B.json` (round 4), `Export5A/B.json` (after the fix pass — the pair the gold is built from). They
all embed the full document text, so they are **never committed** — the committed record is the numbers
in `results/annotation/`.

---

### 5.9 Round 1 of annotation, and the three tools built to rescue it

This is the single most instructive episode in the project so far, so it is written out in full.

**What happened.** P1 and P4 each independently annotated all 23 AA documents. Both files checked out —
23 docs each, every one annotated, doc_ids matching. Then we measured agreement with `kappa.py`:

> **Cohen's kappa = 0.279** against a 0.6 gate. Only **1 of 23** documents passed. The pilot document
> `29_icici`, which had scored **0.587** during calibration, had *fallen* to **0.451**.

*Reading kappa plainly: two referees watch the same match and make calls; kappa asks how often they make
the SAME call after subtracting the agreement you would get from pure luck. 1.0 = perfect twins, 0.0 =
guessing. 0.279 means barely better than chance.* And the pilot regression meant they had drifted
**apart** after calibration, not together — so the problem was getting worse on its own.

#### 5.9.1 `agreement_report.py` — file-wise kappa, and WHY they disagree

A single number says there is an argument; it does not say what the argument is about. This tool takes
every highlighted phrase from both annotators and drops it into one of five boxes:

| box | meaning | round-1 count |
|---|---|---|
| EXACT | same words, same label | 292 |
| BOUNDARY | both caught it, drew the edges differently | 108 |
| **LABEL** | both caught it, disagreed on which label | **7** |
| **A_ONLY** | P1 marked it, P4 marked nothing there | **1,432** |
| **B_ONLY** | P4 marked it, P1 marked nothing there | **541** |

**This table reframed the whole problem.** LABEL = 7 across 23 documents means the 3-label ontology is
essentially solved — nobody is confused about the task. BOUNDARY = 108 means the span rules mostly work.
**83% of the disagreement was one person marking something and the other marking nothing at all** — a
*thoroughness* problem, not a comprehension problem. The earlier hypothesis ("fix the boundaries", formed
from the 1-doc pilot) was wrong, and this is what disproved it.

We also tested and **ruled out** the obvious excuse — did someone stop halfway through the long docs? We
measured how far into each document the last highlight sits: **both covered 85-100% of nearly every
document.** They both read everything and still marked wildly different amounts.

Outputs: `results/annotation/agreement/summary.csv`, `report.md` (numbers, committed) and
`docs/<doc_id>.md` (the actual disagreeing phrases — git-ignored, they quote scraped text).

#### 5.9.2 `annotation_audit.py` — what did they BOTH miss?

Comparing A to B can never reveal what both overlooked. For that you need the original text. The method:

> **Consensus lexicon** — every (phrase, label) that BOTH annotators independently marked at least once
> anywhere in the corpus. If both decided "credit bureaus" is a THIRD_PARTY in some document, that
> judgement is trustworthy and should hold everywhere the phrase appears.

Then every occurrence of every consensus term is located in the raw text and scored: marked by both /
only A / only B / **neither**. *Analogy: rather than me inventing the answer key, the key is built out of
the answers the annotators already agreed on — then their papers are marked against their own key.* It is
deliberately conservative: a "miss" can never be blamed on a disputed judgement call.

**Integrity first:** `ls_import_tasks.json`, ExportA and ExportB are **byte-identical in text** for all 23
docs. Every character offset lines up, so the disagreement is genuine judgement, not a tooling artefact.

**A methodological trap, and the correction (recorded so the bad number is never re-quoted).** The first
run reported **55.7% missed by both**. That was **inflated**: a single sloppy mark from each annotator
promoted the bare word `financial` into the "consensus" lexicon, where it then matched — and counted as
missed — **418 times**. Generic words poisoned the measurement. The `--strict` lexicon (multi-word,
endorsed >=2x by each, generic stoplist removed; 34 terms / 311 occurrences) gives the defensible figures:

| | inflated (do not quote) | **honest (`--strict`)** |
|---|---|---|
| both marked it | 12.8% | **31.8%** |
| only P1 | 22.4% | **39.2%** |
| only P4 | 9.1% | **5.8%** |
| missed by both | 55.7% | **23.2%** |

Mean recall against the lexicon: **P1 58%, P4 39%**.

**The mechanical finding — the most important single fact of round 1:**

> **P1 made 442 repeat marks. P4 made 10.**

P4 essentially never highlighted the same phrase twice. That one habit explains P4's low recall and the
7:1 A-only:B-only ratio. **Why repeats matter so much:** the model learns token by token, so every
occurrence you do *not* highlight is labelled "NOT an entity" in the training data. Skipping repeats does
not merely lose data — it teaches the model the *opposite* of what the marked examples teach. *Like
circling some apples in a photo and leaving others uncircled: you are not being efficient, you are telling
the computer those other things are not apples.*

**The perspective finding.** Their label *proportions* are nearly identical (P1 44/29/28, P4 39/28/33) —
they agree on priorities — but they read different worlds:
- **P1's private vocabulary** is web-technical and generic: `cookie`, `operating system`, `version`,
  `spi`, `pii`, bare `third party`, `agencies`, `bodies`, `services`.
- **P4's private vocabulary** is AA-framework and credentials: `Reserve Bank of India`, `RBI`,
  `Financial Information User`, `Financial Information Provider`, `Sahamati`, `login id`, `pins`,
  `private keys`.

**Both were breaking the rules, in opposite directions** — P1 marking generic umbrellas, P4 marking the
machinery of the AA framework itself as third parties. Things both missed ~23% of the time:
`grievance redressal` (49x), `non-banking financial company` (24x), `data sharing` (21x),
`authentication` (18x), `dispute resolution` (10x).

Outputs: `results/annotation/audit/corpus_audit.md`, `missed_terms.csv` (committed) and
`per_doc/<doc_id>.md` (git-ignored).

#### 5.9.3 The rulebook fix — guideline v4 (Rules 7, 8, 8b)

- **Rule 7 — mark EVERY occurrence, always**, with the training-data reason stated. P1 is right; P4 must
  change.
- **Rule 8 — a specificity test + stoplist.** The test: *"could I point to this in a real bank record, or
  name a real organisation?"* Ban list: `information`, `personal data`, bare `third parties`, `services`,
  `business purposes`… Key ruling: **"third parties" is the category name, not a recipient** — like
  tagging "fruit" instead of "apple".
- **Rule 8b — AA-framework roles and regulators are NEVER THIRD_PARTY.** Never mark `Account Aggregator`
  (the data-blind pipe), `FIP` (the source), `FIU` (the main company), `RBI` (the **regulator** —
  supervising is not receiving), `Sahamati`, `consent artefact`. Test: *"does my data actually end up in
  their hands as a result of this consent?"*
- **Tricky Cases** seeded with every ruling, including the positive ones (`login id`, `pins`,
  `private keys` → DO mark; `grievance redressal`, `dispute resolution` → DO mark — later qualified by D37: only where the text
  says your data is used for it) so it does not read as
  "stop marking things".

#### 5.9.4 `adjudicate.py` — let the computer do the decided part

The insight: now that the rules are mechanical, **most of the 1,973 disagreements need no human at all.**
Starting from the union of both annotators' spans, the tool applies every rule it can:

| action | count |
|---|---|
| accept — both agreed | 280 |
| accept — one missed it, but both endorse that phrase elsewhere (consensus lexicon) | 431 |
| add missed repeats (Rule 7 propagation within the document) | +320 |
| delete stoplist / AA-role violations (Rules 8, 8b) | −336 |
| **leave for a human** | **1,351** (label 4, boundary 105, one-sided 1,242) |

**Proposed gold corpus: 1,136 spans.** *Analogy: a spell-checker that silently fixes the obvious typos and
only stops to ask about the genuinely ambiguous words.* Boundary conflicts default to the **shorter** span
(Rule 1) but are still flagged for a quick yes/no.

Each `results/annotation/adjudication/worklist/<doc_id>.md` opens with **"YOU ONLY NEED TO READ THIS: N
items"** and lists every item with **character offsets**, so the annotator jumps straight to the spot in
Label Studio. `proposed_gold/<doc_id>.json` holds offsets + labels only (no document text) and is
committed; the worklists quote spans and are git-ignored.

#### 5.9.5 The scope decision *(superseded — see 5.9.7)*

> ⚠ **Overruled by D31.** The 12-document cut below was rejected: it would leave too few documents for
> the E1/E2 study. All 23 documents are kept and fixed with per-annotator fix lists (5.9.7). Kept here
> as a record of the reasoning.

1,351 review items does not fit the deadline. A stratified cut — **12 documents, 7 terms / 3 privacy /
2 charter**, preserving the corpus mix — gives **385 gold spans and 422 review items: 31% of the work,
roughly 2.5 hours of joint effort.**

**Honesty requirement for the paper:** review cost tracks document **length** far more than difficulty
(the deferred documents are the 50k-character ones), so this must be described as *"we adjudicated the
shorter documents first under time constraints"* — **never** as selecting the documents the annotators
happened to agree on, which would bias the test set toward easy material. The other 11 documents remain
available for a later round.

#### 5.9.6 What to take away from round 1

The failure looked catastrophic (kappa 0.279) but was **mechanical, not conceptual** — only 4-7 label
conflicts in 23 documents means nobody misunderstood the task. Mechanical problems have mechanical fixes,
which are now written into the guideline and largely automated. Two standing cautions:
1. **Re-calibrate on 2 short documents and clear kappa 0.6 BEFORE adjudicating.** They diverged after the
   last pilot, so v4 must be proven, not assumed.
2. The 431 consensus-accepted and 320 auto-added spans are **rule-derived, not human-confirmed**.
   Spot-check ~20 in the first document — if the automation admits junk, you want to know at item 20, not
   item 400.

Decisions logged: **D29** (the failure, diagnosis, recovery path) and **D30** (corpus audit, perspectives,
Rule 8b, and the inflated-number correction).

---

#### 5.9.7 Round 2 plan: personal fix lists instead of cutting the corpus (D31) — `fixlist.py`

The 12-document cut in 5.9.5 was **rejected by P1, correctly**: 12 documents leaves about 8 test and 4
adaptation documents, too few for the E1/E2 comparison that *is* the study. P1's alternative: tell each
annotator exactly what **they** missed and where.

`fixlist.py` writes **one file per annotator per document**, with five buckets ordered from certain to
judgement-needed: **DELETE** (breaks Rule 8/8b), **ADD_REPEAT** (you marked this phrase elsewhere in the
same document but skipped here — Rule 7), **ADD_MISSED** (both of you endorse this phrase elsewhere and it
appears here unmarked), **SHORTEN**, and **SELF_CHECK** (a phrase only you ever use). Every item carries
character offsets. The spans collapse into far fewer real decisions — P1's 259 deletions are only 23
distinct phrases — so each person has roughly 250 mechanical decisions, done **alone and in parallel**.
*Analogy: instead of a long joint referee meeting, each player gets their own marked-up replay.*

Two safeguards came with it. **Calibrate first, and never on fix-list output**: if both annotators apply
the same tool-generated corrections and then measure agreement, the number is circular — it only proves
they can follow the same instruction sheet. And a **decision table fixed in advance** (kappa >= 0.75
proceed; 0.60-0.75 proceed with a re-check; < 0.60 stop), so a borderline result cannot be argued into a
pass afterwards. `kappa.py` gained `--docs`, because Label Studio exports the whole project regardless of
the filters shown on screen.

#### 5.9.8 The second failure, and why "shortest phrase that makes sense" did not work (D32)

Both annotators re-did two documents from scratch under v4. Agreement got **worse**: **0.492 -> 0.374**.
The per-label view explained it at once: **DATA_TYPE had converged** (both at a median of 2 words, the best
label at F1 0.465) — so Rules 7/8/8b worked — but **PURPOSE scored F1 = 0.000**. P1's PURPOSE spans had a
median of **3 words**, P4's **8-10** (`to raise a grievance with the grievance resolution officer of the
FIU`). A 3-word and a 10-word span can never match exactly.

The lesson that shaped every later rule: **countable rules survive two annotators; judgement rules do
not.** Rules 7, 8 and 8b could be counted ("every occurrence", "this word is banned") and held. Rule 1
("the shortest phrase that still makes sense") is a judgement, and P4 was applying it honestly, just
differently. So **Rule 9** made PURPOSE countable — at most 5 words: drop the leading "to/for", stop at the
object, count — and **Rule 9b** closed a loophole where banned umbrellas came back with a modifier
(`client data`, `data received from an FIP`). A small tooling bug surfaced too: a relative `--out` path
crashed three reports; they now resolve the path first.

**Fixing the corpus is not the same as measuring agreement.** On the two calibration documents P4 had
27 violations of the new rules against P1's 2, so P1 suggested — reasonably — that P4 simply *edit*
the existing annotations rather than re-annotate. That is the right way to **fix the corpus** (it is what
the fix pass does). But Rule 9 was written by comparing the two annotators and effectively siding with
P1's style, so if P4 edits towards it, agreement rises partly because P4 copied P1 — not because the
guideline is clear. A number produced that way is not an honest agreement measure. So the two jobs were
separated: **edit to fix, and measure on a document neither has touched**, annotated independently
(first `10_perfios_terms`, switched to `23_upmint_aa_tos` in D36). Corpus-wide, P1 has fixes to make too —
81 Rule 9/9b violations and ~230 stoplist deletions in the documents still carrying round-1 work.

#### 5.9.9 Why PURPOSE kept failing: relaxed matching and Rule 10 (D35) — `relaxed_agreement.py`

P1's next suggestion was reasonable: PURPOSE spans carry function words (a, the, to, within), so score them
with a looser match. `relaxed_agreement.py` computes four levels side by side — **EXACT**, **PARTIAL** (any
character overlap), **CONTENT** (function words removed, then an overlap coefficient of at least 0.6, so
`raise a grievance` matches the long version exactly) and **TOKEN** — with one-to-one matching so one long
span cannot absorb several short ones. Its self-check caught a real bug before any result was trusted: the
matcher compared the *end offset* where it meant to compare the *label*, which would have made the loose
levels behave like exact matching.

The result **refuted** the idea: PURPOSE rose only from **0.000 to 0.138**. If the disagreement had been
about edges, relaxed matching would have lifted it to 0.6-0.8. Listing the spans showed why — the two
annotators marked purposes in **different parts of the same document** (in `17_pb` one found ten
purposes at character positions 6,671-9,581, the other four at 222-1,984, sharing one). A "no vague
annotations" rule was also **tested, not assumed**: deleting every vague PURPOSE span from both left exact
F1 at 0.000 and relaxed F1 at 0.087. P1's purposes were specific; P4 simply never looked there. (The
guideline already said "vague" in six places.)

Dropping PURPOSE was considered and **rejected by P1 for a good reason**: the consent artefact's
`Purpose.code` is standardised but its `Purpose.text` is free-form, so the declared purpose cannot be
trusted on its own. Comparing it with what the policy text actually describes is a real check the
framework never performs — the paper's disclosure-fidelity application (D28).

So **Rule 10** gives PURPOSE a **finite list**: a span counts only if it names an activity in one of **10
categories** — credit/loan assessment, account monitoring, financial management, fetching/sharing
financial information (the AA service itself), fraud & verification, legal compliance, support &
grievance, communication, analytics, marketing. Four checks in order: a reason the company uses your data (not a goal, not your right, not a
procedure — corrected in D37, see 5.9.11) -> fits a row -> not a phrase that fits any company's policy -> at most 5 words. The official five ReBIT codes were
too narrow to use directly (no row for fraud checks, grievances or marketing); the comparison with the
declared code happens later, in analysis. *Analogy: "find anything valuable in this house" produces two
different bags; "find these ten kinds of thing" produces the same bag.* **There will be no round 4**: the
next calibration result, whatever it is, leads to the fix pass.

#### 5.9.10 Every small decision, covered: the granular audit and Rules 11-22 (D36)

The last pass looked at **every span both annotators made in all 23 documents** (1,761 and 933) and asked,
for each small decision an annotator faces, whether the guideline said anything. Where it did not, and
the annotators had actually faced that decision, a rule was added:

| Rule | Decision | Evidence (P1 / P4) |
|---|---|---|
| 11 | no space or punctuation at a span's edge | 14 / 41 spans |
| 12 | abbreviations: highlight the name as first written, stop at the bracket | 30 / 30 handled 3 ways |
| 13 | example lists: every item, never the umbrella word, never "etc." | 834 / 347 spans in such lists |
| 14 | a list whose items share a word written once is **one** highlight | PURPOSE lists 19 / 83 |
| 15 | never overlap, nest or duplicate; keep the outer span | 0 / 12 |
| 16 | THIRD_PARTY only if the sentence says data goes to it | ~112 / ~98 without a data-flow verb |
| 17 | the company that wrote the policy (and its staff) is never a THIRD_PARTY | 0 / 19 |
| 18 | mark the mention whether the practice is affirmed, possible, or denied | 508 / 276 in negated sentences |
| 19 | a word named after data is not data (`password mining`, `KYC process`) | 9 / 9 |
| 20 | never headings; definitions are ordinary sentences | ~67 / ~75 |
| 21 | one highlight across a line wrap; glued text: select only the entity's letters | 22 / 39 |
| 22 | one phrase, one label; check the colour before Submit | 9 / 11 phrases with >1 label |

`fixlist.py` enforces three of these automatically — **Rule 11** (edges), **Rule 15** (overlaps and
duplicates) and **Rule 17** (the policy's own company, matched against each document's real legal
name) — so they arrive in each annotator's fix list as ready-made corrections. Writing those checks
also exposed that the shared banned list only knew the *singular* AA roles (`FIP` but not `FIPs`);
the plurals are now banned too. Plus a decision table for "X data / X information / X details" phrases (mark `contact information`,
`KYC documents`, `transaction history`; not `personal details`, `technical data`), and new stoplist words
(`stakeholders`, `persons`, `entities`).

**Rule 18 comes straight from the training data.** The OPP-115 loader keeps every span whether the
practice is affirmed or denied, so the model learns that *"we do **not** share with advertisers"* contains
a THIRD_PARTY. The AA test set must be annotated the same way or E1/E2 would compare two different tasks.
It does mean a denied purpose ("we do not use your data for marketing") will be extracted as `marketing`,
so the verification analysis must check polarity before flagging anything.

**The audit also found a corpus defect.** In PDF-extracted documents `clean.py` lost spaces, producing
tokens like `anyinformationprovidedbyyou` — 149 signals, concentrated in `02_digio_terms` and
`10_perfios_terms`. That second document had just been chosen for the independent calibration round;
calibrating on it would have measured the extraction bug instead of the guideline. **The calibration
document is now `23_upmint_aa_tos`.** The two affected documents must not be re-cleaned mid-annotation:
re-cleaning shifts every character offset and would invalidate the spans already made on them.

#### 5.9.11 The actor test: your rights are not the company's purposes (D37)

P1 caught an error in Rule 10: `raise a grievance` had been listed as a valid PURPOSE. It isn't — in
`26_zerodha_tos` it sits in a list of the **client's rights** ("to raise a grievance…; to revoke any
consent…; to deregister from any AA"). A PURPOSE answers *why the company collects, uses or shares your
data*; raising a grievance is something **you** do.

Reading every grievance/dispute/consent-right PURPOSE span in its sentence showed the words can't decide
on their own. In P1's eight cases the text really did say data was used or kept for them ("records are
retained… for dispute resolution"); in 13 of P4's 14 it described a right ("the customer may revoke
consent"), a procedure ("a Grievance Redressal Policy for handling complaints") or a contract clause
("dispute resolution provisions survive termination"). So the corrected first check is an **actor test**:
*does the text say the company uses, keeps or shares your data for this?* — the PURPOSE twin of Rule 16
for third parties. *Analogy: "the hospital keeps your records for billing" is a purpose; "you have the
right to complain about your bill" is not, even though both mention billing.*

The tools follow suit: they no longer add or auto-accept these phrases (which would have produced about
140 wrong suggestions), and instead list each annotator's existing ones with the sentence quoted, for a
quick human decision.

#### 5.9.12 Round 3 calibration, and why the fix lists had to stop guessing (D41)

Both annotators re-did `23_upmint_aa_tos` under v7.1 (`Export3A/B.json`). Token kappa: **0.283** (entity
F1 0.267; DATA_TYPE 0.41, PURPOSE 0.17, THIRD_PARTY **0.00** — P4 marked no third party at all; relaxed
CONTENT match 0.367). Below 0.6, so the stop-loss agreed in advance (D35) applies: **no round 4**; go to
the fix pass with the guideline frozen.

The useful question was *why*. Each annotator's violations of **already-written** rules were applied by
hand, changing no judgement call, and kappa re-scored:

| what was corrected | kappa |
|---|---|
| nothing (as submitted) | 0.283 |
| only P1's rule violations | 0.298 |
| only P4's rule violations | 0.547 |
| both | 0.584 |
| both, plus P4 marking the 5 Rule-16 third parties | **0.717** |

So the guideline is mostly *clear enough*; it was not *applied*. P4's PURPOSE spans all kept the leading
`to`/`for` (Rule 9 step 1), umbrella terms returned (Rules 8/9b), contract clauses were marked as purposes
(including `to acknowledge and resolve complaints`, the exact D37 case), repeats were skipped, and
genuine data flows ("disclose information to law enforcement…") went unmarked. P1's two errors were
`affiliates`/`agents` in an indemnity clause (Rule 16's own ❌ example) and `pursuant to valid legal
process` as a PURPOSE (a condition, not an activity). **Caveat for the paper:** this was not a blank
document — 22 of P1's 28 spans and 16 of P4's 32 are identical to their round-1 spans — so it is reported
as calibration round 3, not as the clean "untouched document" measurement D39 planned.

**The fix-list flaw it exposed.** Spot-checking the regenerated fix lists on this document showed that
the "add what both of you endorse elsewhere" bucket (ADD_MISSED) was wrong 6 times out of 7 for P1 and 7
out of 10 for P4 — yet it was labelled "mechanical, no judgement needed" and held ~1,000 suggestions.
It matched **words, not meanings**: `title` in "all rights, title and interest", `assets` in "sale of
assets", `service providers` *inside* an already-suggested `third-party service providers`, and
`affiliates` copied from a data-sharing sentence into an indemnity clause. *Analogy: a spell-checker
that "corrects" every "bank" to a financial institution, including the river bank.* Fixes:
- **Nothing is suggested inside or across another highlight or suggestion** (Rule 15; longest wins).
- **A THIRD_PARTY is only suggested where its sentence has a data-flow verb** (Rule 16) — share, disclose,
  transfer, provide, process, receive… The span itself is blanked first, so `service providers` cannot
  vouch for itself.
- **New bucket 1e THIRD_PARTY_CHECK** — each annotator's own third parties with no data-flow verb, shown
  with the sentence. A sample of 24 was ~22 genuine violations (indemnity, assignment, jurisdiction,
  definitions, own company); 132 for P1 and 90 for P4, matching the round-1 audit's estimate (D36).
- **ADD_MISSED became a *check-in-context* bucket**, each suggestion printed with its sentence, and is no
  longer counted as mechanical. `provide the services` joined the stoplist.

Result on Export3: mechanical fixes P1 **953** / P4 **758**; to check in context P1 307 + 132 / P4 459 + 90.

#### 5.9.13 Round 3 was a process failure: one fresh document (D42)

The table above says the rules were fine and had not been applied. The reason turned out to be mundane:
P4 **never received v7.1**. *Analogy: the exam was marked against an answer key one student had never
been given — the low score says nothing about whether the questions were fair.*

That changes what round 3 measured, so one exception to "no round 4" was made — and written down **before**
anyone started (D42), because a rule broken *after* seeing a bad number is how results get cherry-picked.
Both annotators annotate `25_the_financiali_privacy` from a **blank** page under v7.1, separately, before
the fix pass. Whatever kappa comes out is final and reported alongside every earlier round. This number is
also the cleanest one available: after the fix pass, agreement is partly shared knowledge, because the fix
lists' suggestions are built from both annotators' spans.

#### 5.9.14 Round 4: the honest number, and the last rulings (D43)

Both annotators, now both holding v7.1, annotated `25_the_financiali_privacy` separately. **Kappa 0.522**
— nearly double round 3's 0.283, still under the 0.6 gate, and final by the rule agreed in advance.
PURPOSE, the label that scored 0.000 in round 2, reached **0.658** with relaxed matching and is now the
strongest; **THIRD_PARTY** is the hardest, mostly over regulators and named Account Aggregators. Unlike
round 3, the disagreements were spread across *both* annotators — the sign of a real measurement rather
than one person missing the rulebook.

Discussing the disagreements produced these rulings (guideline **v7.2**, Rule 23 and Rule 10 row 11):
- **Provided data counts; observed data does not.** The question is *not* "is it financial?" — an email
  address isn't financial either, and it has always been marked. It is *where the data comes from*.
  What you hand over — emails, chat messages, call recordings, survey answers — is marked: it is exactly
  what you should know before agreeing. What your device emits — IP address, browser type, pages viewed,
  session duration — is not: you never handed it over, and the same list appears in almost every web
  policy, so it tells you nothing about this company. *Test: did you make it, or did your phone?*
  (P1 raised the dilemma; my first justification, "you can't point to it in a bank record", was wrong
  because it would exclude email addresses too.)
- **`KYC` depends on the sentence** — "collected where required for KYC" is a purpose; "KYC records" is
  data; "the KYC process" is nothing.
- **A table's row label is a heading.** Scraped web tables lose their columns, so `Successor entities`
  ends up on its own line above its description; mark the items, not the label. *(Reversed in D45 —
  see 5.9.16.)*
- **Mergers become PURPOSE row 11** — but only where your data moves because of one. A corpus check
  showed 8 of 23 documents use the words, yet only 3 describe your data being transferred; the rest are
  contract clauses, loan restructuring or insolvency declarations. *Analogy: "the shop may be sold, and
  your loyalty-card records go with it" is about your data; "this contract may be transferred if the shop
  is sold" is not.* It earns a row because OPP-115 has the same purpose, and because handing your data to
  a new owner is exactly a use beyond what you consented to.

Two of my own calls were corrected in this discussion: P1 rightly kept telemetry unmarked (I had counted
it as a miss), and `required for KYC` is a real purpose that only needed shortening.

#### 5.9.15 Testing the fix lists themselves (D44)

Before the fix pass, the fix lists were tested like any other tool: what do they catch, and what do they
get wrong? Every rule was matched to the bucket that enforces it; each new check was tried on the real
round-4 annotations *before* being added, and kept only if it was mostly right; then the lists were scored
against the problems found by hand on doc 25.

The most important finding was a bug that **multiplied mistakes**. The "you marked this elsewhere, add the
skipped repeats" step copied any phrase — so P4's one wrong `SEBI` (inside the name of a regulation) was
about to become seventeen. The same flaw sat in the tool that builds the gold file. *Analogy: a spell-checker
that learns a typo from you and then "corrects" every other occurrence to match it.* Copies now come only from
highlights no rule doubts, and each copy is checked again where it lands.

Seven new checks were added: named Account Aggregators and every variant of device telemetry (deleted),
leading "to/for" on purposes (trimmed), mis-clicked colours, headings and table labels, data *sources*
mistaken for recipients, lists cut differently, and missed communications/KYC. The lists now catch **7 of
10** of P1's hand-found problems on doc 25 and **19 of 22** of P4's. Every miss is the same kind — a
recipient nobody marked and no rule points to — and that is exactly what adjudication exists for: it is
the one place the two annotators' highlights are compared.

#### 5.9.16 Headings are just text (D45)

The fix-list audit left one edge case: in doc 25, `PostHog` appears only as the label of a table row
("PostHog — for product analytics"). Under the old rule labels and headings were never marked, so a real
recipient would vanish. P1 settled it more broadly: **a heading or row label is ordinary text** — marked if,
and only if, it passes every other rule. The model is learning to spot *mentions*, and a heading is a
mention — the same reason a "we never sell your data to advertisers" still marks `advertisers`. It also
removes a judgement the annotators kept making differently.

The other rules do most of the filtering: `8. Cookies` is telemetry, `Data Retention` has no data-use frame,
`Personal Information We Collect` is an umbrella. What newly gets marked is specific data headings (`KYC
Documents`) and recipient row labels — `Service providers`, `Successor entities`, `PostHog` — whose table
begins "Your personal data may be shared with…". *Analogy: a shelf label reading "Pasta" is still the word
pasta; whether it counts depends on what is on the shelf, not on it being a label.* The code that used to
detect headings was simply deleted.

#### 5.9.17 The last three questions (D46) — the rulebook is closed

Three small questions had been parked for later; they were settled before the fix pass so that both
annotators apply the same answer everywhere.

- **Regulators.** When a policy says "we may disclose your information to regulators, courts and the
  Income-tax Department", those are real recipients and are marked — **except the regulators that run the AA
  system itself** (RBI, SEBI, IRDAI, PFRDA). *Analogy: the referee is on the pitch for every match, but is not
  one of the players you are passing the ball to.*
- **Abbreviations in brackets.** "Permanent Account Number (PAN)" is now **two** highlights, the name and the
  abbreviation. P1 proposed this against my suggestion of leaving the bracket unmarked, and was right: every
  later "PAN" is marked anyway, so skipping only the bracketed one would tell the model the same word is data
  everywhere except inside brackets.
- **Status words.** "registered email address" becomes "email address" — the shortest phrase that still makes
  sense. Words that belong to a field's real name stay ("Permanent Account Number").

The tools follow: the four regulators are deleted automatically, the bracket's content is proposed as its own
highlight, and three-letter abbreviations such as PAN and OTP are finally proposed as repeats (a length floor
had been hiding them). Guideline **v7.4** has no open questions left.

#### 5.9.18 After the fix pass: kappa 0.426, and what a fix list cannot fix (D48)

Both annotators worked through their fix lists on all 23 documents. Agreement on the whole corpus rose from
0.279 (round 1) to **0.426** — better, still under 0.6, and lower than the 0.522 measured on the single
round-4 document. Individual documents range from 0.03 to 0.67.

Classifying every remaining disagreement shows why. The rule violations the lists targeted are nearly gone
(about 120 spans left out of 2,700). What remains is **noticing**: more than half of the highlights only P1
made are phrases P4 never marks anywhere, and a third of P4's are phrases P1 never marks. In four short
charter documents one annotator marked a handful of spans and the other forty. *Analogy: two proof-readers
now agree on the spelling rules, but one of them reads every footnote and the other skims them — no rulebook
changes that.*

This is the honest limit of the design. The lists can only point at what a rule or a shared vocabulary can
see; they cannot make two people find the same entities in a 6,000-word contract. It is also why
adjudication was always the last step: it is the one place the two sets of highlights are laid side by
side. The tool resolves about 960 spans on its own (535 agreed, 336 by shared vocabulary, 89 repeats) and
leaves **1,158 for a human decision** — 657 distinct phrases, many of them repeated (`lender` 49 times), so
deciding by phrase rather than by item cuts the work considerably.

#### 5.9.19 First adjudication ruling: the Lender (D49)

The most common disputed phrase was `lender`. P1 ruled that it is a third party: in a loan platform's
terms, the lender is a different company from the one writing the policy, and it receives your data to
decide whether to lend. That is exactly what THIRD_PARTY means.

One limit was kept, the same one that applies to every recipient: the lender is marked **only in sentences
where your data goes to it**. "We submit your information to the lender for eligibility" — yes. "The lender
transfers the loan amount" — no, that is money. "The lender may start legal proceedings" — no. *Analogy: the
courier is a recipient when the parcel is handed to them, not every time the word "courier" appears in the
terms of carriage.* Without that limit, the label would slide from "who receives your data" to "any
organisation mentioned".

Rulings like this, made after the fix pass, are kept in a separate part of the guideline (PART I) so it stays
clear which rules the annotators worked under and which were applied when building the gold file.

#### 5.9.20 Building the answer key: automatic adjudication, checked by people (D50)

Two questions came first. *Could kappa be pushed higher?* Measured: even if both annotators finished every
mechanical fix perfectly, without seeing each other's work, it tops out near **0.47**. Getting past 0.6 would
need them to compare notes — and then the number no longer measures agreement. Since the experiments are
scored against the answer key and not against kappa, the effort went into the key instead.

*Could the key be built with no human at all?* Yes, but unverified it would be a "silver" set, and several of
my own judgement calls had already been corrected by P1 during the project. So the middle path was taken.

**How the gold file was built** (`adjudicate_auto.py`):
1. Each export is cleaned on its own with the written rules.
2. What both annotators marked identically is accepted: 511 spans.
3. Every other highlight — 1,513 of them — is read in its sentence and ruled on with the guideline, each
   ruling tagged with the rule that decided it.
4. Phrases accepted in a document are checked at the 133 places nobody had marked.

The result is **1,153 spans** (532 data types, 368 purposes, 253 third parties). The biggest single reason
for rejection was "the sentence does not say your data goes to them" (329 — nearly half of them the word *lender* in
fee, repayment and legal clauses, against 31 places where the lender does receive your data), then "no data-use frame" for purposes (237).

**The check.** Both annotators get the same random sheet of 123 rulings — without being told who marked what —
and answer agree or disagree. *Analogy: an exam marked by one examiner, with a second and third examiner
re-marking a random tenth of the scripts.* If both accept at least 90%, the key stands; any category that
falls short is reviewed in full.

**One step was put back in its place (D51).** Checking a sample tells you whether the rules were *applied*
correctly; it does not tell you whether the rules are *right*. Ten rules had been set after the fix pass —
one by P1, the rest by the adjudicator — and P4 had agreed to none. So before the sample check the two
annotators meet and decide each rule together: keep, change or drop. Because every ruling carries the code
of its rule, a changed rule is re-applied to exactly its spans and the key rebuilt in minutes.

One honest caveat is recorded: the finished key matches P1's annotations more closely than P4's (F1 0.73
against 0.51). That is expected — the guideline grew out of P1's rulings — and it is exactly why P4's check
is the one that matters most.

#### 5.9.21 Loose ends: the passwords rule, the roads not taken, and what the paper will say (D47, D53)

**The passwords rule (D47).** During the fix pass P1 noticed the fix list suggesting `password` in sentences
P1 had deliberately skipped — *"You are solely responsible for maintaining the confidentiality of your
password."* The data showed a clean pattern: P1 marks credentials only where the company *handles* them;
P4 marks them wherever the word appears. The guideline had a "the sentence matters" rule for third parties
(Rule 16) and for purposes (Rule 10) but none for data types. The proposed fix: **a data word is marked only
where its sentence says the company collects, asks for, uses, stores, accesses or shares it** — including
when it says it does *not* ("we never ask for your password"). *Analogy: "we record your blood group in your
file" tells you what the hospital holds; "patients should know their own blood group" does not.* It was found
mid fix pass, so nothing was changed then; it was applied when the gold was built and is one of the ten
rules the annotators now decide on (rule 2, the one that removes most of P4's highlights — 54 of 67).

**Three roads not taken when building the answer key.** *Intersection* (keep only what both marked): safe
but far too small — half of the real purposes would disappear. *Union* (keep everything either marked):
complete but noisy — `firewalls` would be a purpose. *Fully automatic with no human check*: good, but
unverified, so strictly a "silver" set. The chosen route sits between: rule-by-rule automatic rulings, then
both annotators independently check the same random sample.

**What the paper will say about agreement.** Four numbers, each named for what it is: **0.52** (one fresh
document, both annotators on the final guideline — the only fully independent figure), **0.43** (all 23
documents after the fix pass), **0.47** (the same exports after the written rules are applied to each
automatically — supplementary), and relaxed entity F1 **0.49**. On the usual scale that is "moderate"
agreement. It never reached the 0.6 gate the project set itself, and the paper says so. What it offers
instead is the diagnosis: the rule violations were driven down to about 120 spans in 2,700, and what is left
is two careful people *noticing different things* in long contracts — a finding about this kind of
document, not just a low number. The experiments themselves are scored against the answer key, not kappa.

**The meeting guide.** `rules_to_ratify.md` (kept out of git: it quotes the policies) takes each of the ten
rules through the same steps — the rule in one line, why the question arose, an everyday analogy, real
sentences that were marked and not marked, the genuinely debatable cases, what keeping, changing or dropping
it would do to the answer key in numbers, a recommendation with how sure it is, and a box for the decision.
Two recommendations are not "keep": rule 3 (sources) is held with only moderate confidence, and rule 4
suggests *adding* a twelfth purpose category for account opening and onboarding, because both annotators
marked it independently and the list simply had no slot for it.

#### 5.9.22 The rules meeting: one rule dropped, two changed, and the answer key rebuilt (D55)

**Why a meeting at all.** While building the answer key, ten small rulings had been applied that the two
annotators had never agreed to together (D51). *Analogy: a referee who invents ten new rules at half-time
has to get both captains to accept them before the result counts.* P1 and P4 went through all ten.
Seven they kept. Three they changed.

**1. A source counts as a third party (rule dropped).** The old ruling said: if the company *fetches* your
credit report **from** a bureau, the bureau is not a recipient. The annotators disagreed, with a practical
argument: to fetch your report the company has to hand the bureau your name and PAN, so the bureau does get
your data. *Analogy: asking a librarian for your borrowing history means telling the librarian who you are.*
So THIRD_PARTY now means **any outside organisation that exchanges your data with the company, in either
direction** — except the Account Aggregator pipeline's own bodies (AA, FIP, FIU, RBI and the other
regulators), which were never marked. A sentence with no exchange at all — an indemnity clause, a definition,
"the Lender pays out the loan" — still marks nothing.

**2. A twelfth purpose: opening an account (rule changed).** The fixed list of purposes had no row for
registration and onboarding, although policies plainly say "we use your information to register you as a
user" and both annotators had marked it. *Analogy: a menu without a dish that half the customers order —
add it to the menu rather than serve it at some tables only.* Row 12 follows the same test as every row: the
sentence must say your data is used for it. "Information given **at the time of registration**" is a moment,
not a reason, and stays unmarked. Of the 12 highlights involved, 7 became purposes.

**3. Lists: merge only what cannot stand alone (rule changed).** The answer key had turned many lists into
one long highlight wherever the items shared a word. The annotators kept that only where a piece would be
meaningless by itself. The test: *highlighted alone, would the piece still tell a reader what it is?*
`Retrieving, viewing, consolidating … Financial Information` stays whole — "viewing" alone says nothing.
`ACH, NEFT, IMPS and UPI ID details` becomes four highlights — each names a payment record. *Analogy: "tea
and coffee cups" must stay together; "cups, plates and bowls" are three things.* 12 merged lists were split
back, 16 stayed whole.

**The awkward consequence, and the fix.** The fix lists had told both annotators to *delete* sources. So when
that rule was reversed, the exports held only the sources somebody had ignored the instruction on — in
"Experian/CIBIL/CRIF" two were marked and one was not. An answer key with half a list marked follows no rule
at all. So for the first time the key received highlights **nobody had drawn**: 36 of them, each the
list-mate of something now accepted. They are written in the audit trail as `new` lines, and they go into
the sample check like every other ruling, so both annotators get to reject them. They were found three ways:
finishing every sentence that had a changed ruling, sweeping all 23 documents for organisation words after
"from / provided by / sources", and checking what the annotators had deleted for this reason during the fix
pass.

**The numbers.** 85 rulings changed. The key grew from 1,153 to **1,261 highlights** (545 data types, 382
purposes, 334 third parties) — almost all the growth is third parties, and most of it in one document
(Indifi's privacy policy lists two dozen kinds of organisation it collects information from). Measured
against the new key, P1's own highlights score F1 0.72 and P4's 0.51 — unchanged, so the meeting did not tilt
the key towards either annotator.

**What stays honest.** Two of the three changes introduce things nobody was looking for while annotating
(sources, onboarding). The paper says so: recall for those rests on what somebody happened to mark plus a
systematic sweep, and is likely lower than for the rest. Five judgement calls made while applying the
decisions are listed in D55; P1 confirmed all five. And the key is **still provisional**: a fresh random sample
of 124 rulings now goes to each annotator, to be checked alone.

#### 5.9.23 The sample check: both annotators accept the answer key (D56)

Each annotator, alone, went through the same 124 randomly drawn rulings and wrote agree or disagree beside
each. *Analogy: two inspectors each pull the same 124 items off a production line of 1,700; if both pass at
least nine in ten, the whole batch is accepted.* **P1 accepted 119 (96.0%), P4 all 124 (100%)** — both above
the 90% bar, so the answer key stands and no rule has to be reopened.

Two honest notes. P4's sheet is "yes" on every row with no comment, which may be real agreement or a quick
read — the two cannot be told apart — so the figure that carries weight is P1's 96%. With 124 rows, the range
it could plausibly lie in is about 91% to 98%, still above the bar. And P1's five rejections are not thrown
away: each one points at a small group of neighbouring highlights (the same phrase in two other documents,
the other purposes in the same sentence, the other mentions of Gmail), so they are settled as a set and then
re-applied — the last step before the answer key is final and the test file is generated.

#### 5.9.24 The answer key is final (D57)

P1's five rejections from the sample check were applied — each together with its neighbours, because a
correction that fixes one highlight and leaves its twin untouched just creates a new inconsistency.
*Analogy: if a proof-reader finds "recieve" on page 12, you search the whole book for it, not just page 12.*
So `retrieving or collecting` gained its object (`… such financial information`) in all three documents that
contain it; a sentence about what happens when consent is withdrawn lost all five of its highlights; two
vague advisory "purposes" were removed; `Gmail` became a data type everywhere it means the user's emails;
and one advertiser with no stated data flow was dropped.

**The final answer key has 1,258 highlights**: 550 data types, 377 purposes, 331 third parties. The chain
that produced it is worth stating in one breath, because it is the paper's method: two annotators -> their
disagreements settled rule by rule, each ruling tagged with its rule -> the rules themselves approved by both
annotators -> a random sample of the rulings checked independently by each (96% and 100% accepted) -> the
rejected ones corrected.

**The exam paper is printed.** `aa_to_conll` wrote the model-ready files: `aa_test.conll` (9 documents cut
into 559 segments, **821 entities**) and `aa_adapt.conll` (14 documents, 845 segments, 436 entities). Three
checks were run on them: the training code's own reader counts back exactly the same entities; the list that
says which document each segment came from is complete; and the longest segment is 177 word-pieces against a
limit of 256, so the silent cut-off described in section 5.12 cannot happen. From here the test set is
**sealed**: it is opened exactly once, for E1 and E2.

#### 5.9.25 Auditing the finished answer key from three chairs (D58)

Before using the answer key, it was read again as three different people would read it: the **user** whose
consent is being asked, a **financier or auditor** checking a regulated process, and a **review panel**
judging a research dataset. Each chair went round three times — first the mechanical checks, then reading for
wrong and missed highlights, then re-reading every suspect to throw out false alarms.

**What it found.** The key is clean on the surface — no label conflicts, no overlaps — and about 98% of its
highlights are right. But roughly 7% of what should be marked is missing, and where two documents contain the
*same sentence* (13 of them share a template) the highlights agree only 92% of the time. 49 specific defects
were pinned down: 20 highlights to remove, 29 to add.

**The lesson.** 16 of the 20 wrong highlights were ones *both annotators had drawn identically*. The whole
process had treated agreement as proof — an agreed highlight went straight into the key and nobody looked at
it again. *Analogy: two students who copy the same wrong line from the textbook agree perfectly, and are both
wrong.* Both marked the list of companies in an indemnity clause; both marked "title" in "right, title and
interest". The sample check could not catch these either, because it sampled the *rulings*, and an agreed
highlight never had a ruling. The second cause is that the "mark every repeat" step worked inside one
document only, so it never noticed that a sentence marked in one company's terms was unmarked in the
identical sentence of another's.

**What each chair concluded.** The *user* can trust the lists of data and recipients but not a summary that
ignores "not": 7% of the data highlights sit in sentences where the company promises **not** to take the
thing, and the key marks them the same as things it does take. The *auditor* wants three gaps closed —
`biometric data` appears nowhere in the key although three test documents mention it, one named recipient of
KYC data is missed, and a lending prohibition is half-marked. The *panel* accepts it as an evaluation set with
a stated error rate, and asks that the paper's limitations section say plainly what the scheme leaves out
(umbrella terms such as "financial information", the pipeline's own actors, device data) and how the key was
made.

Nothing was changed: the answer key had been approved by both annotators, so the corrections wait for their
decision. The full list is in `gold_audit.md` beside the adjudication files.

#### 5.9.26 The audit corrections go in (D59)

P1 went through the audit's list and accepted it with two changes of his own. First, the **signature** named
in the consent form's field list is not data the user hands over — it is the act of saying yes — so it is not
marked anywhere (four highlights came out, two proposed ones were not added). Second, **`identity` and
`contact information`** in that same list are two separate things and get two highlights, in all nine
documents that carry the clause.

To remove a highlight that *both* annotators had drawn, the tool needed one new instruction — "drop this one
highlight at this one place" — because the only removal it knew ("drop this phrase wherever both marked it")
would have deleted correct highlights in other documents too. *Analogy: striking one wrong entry from a
ledger, not every entry that happens to share its name.*

**The result.** The answer key now has **1,266 highlights** (559 data types, 381 purposes, 326 third
parties). The check that mattered most — is the same sentence marked the same way in every document that
contains it? — went from 92.3% to **99.1%**, and the four mismatches left are the checker stumbling over the
two documents whose words are glued together, not real differences. The test file was regenerated: 826
entities in 559 segments.

**What the project learned.** Two annotators agreeing is evidence, not proof. The answer key had been built by
examining every place they *disagreed*; nobody had examined where they agreed, and 16 of the 20 wrong
highlights were hiding there. The paper will describe both checks: adjudicating the disagreements, and
auditing the agreements.

#### 5.9.27 "They do" and "they promise not to" (D66)

The answer key highlights a kind of data whether the company says it takes it or says it does **not**. Both
"we collect your email address" and "we shall not access your login credentials" produce a data-type
highlight. For teaching a model to *spot* data types that is correct. For telling a user what a policy says
it is dangerous: a summary built from the highlights would list "login credentials" among the things taken.
*Analogy: a shopping list and a list of allergies written in the same handwriting on the same page — unless
you mark which is which, someone buys the peanuts.*

So each highlight gets one extra mark, **negated: yes or no**. The highlight and its label do not change, the
models never see the mark, and no score moves; it is there for the summariser and the consent ledger.

Finding them took a program and then reading. The program listed every highlight near a word like "not" or
"never" — 411 of them — but most were false alarms ("including but **not** limited to", "does **not**
guarantee the accuracy"). After reading, 67 are proposed as genuinely negated: mostly passwords and other
credentials, phone contacts and galleries, biometric data. Two kinds of sentence needed a rule. "We shall not
access your contacts, *except as permitted by law*" counts as negated — the sentence is a prohibition. But in
"your data will not be shared, *except for fraud verification*", the purpose *fraud verification* is **not**
negated — that is exactly when sharing does happen.

P1 checks the list before anything is written into the answer key.

### 5.10 The summarizer dataset and P2's models — P2's track (D33, D34, D67-D70, D72, D73)

This belongs to P2; the builder and its guide were handed to P2 via Drive and are **not committed by P1**.
It is recorded here so the reasoning is not lost.

P2's first attempt had GPT summarise policy text and got **30 lines in, 25 out** — paraphrase, not
compression. Two causes: GPT was given no countable length rule, and "lines" hid how small the texts were
(corpus lines are wrap fragments of about 9 words). The recommended design (D33) is **real policy text ->
short summary**: documents are cut into 180-260-word chunks at section boundaries (T5 reads at most 512
tokens), split **by document** (13 train / 10 test), and each chunk carries a must-mention **checklist**
of the annotated facts inside it. Every reference summary must be **at most 25% of the chunk and at most
60 words** and keep **at least 80% of its checklist**, or it is rejected automatically with the reason.
Tested on real chunks: accepted references compressed to 17% with every fact kept; a deliberately bad one
was rejected on both counts. The alternative — turning a *list of facts* into a sentence — was dropped,
because when the input is the fact list, "did the summary keep the facts?" is nearly automatic and the
faithfulness audit would measure almost nothing.

Because P1 and P4 only have time for the gold annotations, the **test set is reference-free** (D34): each
summary is scored against the **gold facts of its own chunk** — coverage (kept), hallucination (entities
the NER model finds that are not in the source), compression. No handwritten summaries are needed, and the
test set grows from a 30-chunk sample to every test chunk with a gold fact (122 of 194). ROUGE/BERTScore
become optional, scored against GPT references and reported as silver. Switching the checklists from
silver to gold needs no new code: pass the gold export as both inputs.

**The training summaries (D67).** P2 asked for the 130 reference summaries the small model learns from.
They were written by Claude Opus 5.5, one passage at a time, for P2's prompts exactly as P2 had built them,
and saved as `data/summ/refs_train.jsonl` (one `{"id", "summary"}` per line). All 130 passed P2's own
checker: 19-60 words, about 23% of the passage, no more than three sentences, checklist kept. *Analogy: a
senior student writes model answers, and the junior student learns to write like them — in the literature
this is called distillation, and the paper has to say so.* A second, stricter read caught ten summaries that
used something the passage itself does not say — a detail from the previous passage, the company's name where
the text only says "we", or the long form of an abbreviation — and they were corrected: a summary may only
use what is on its own page. Two things were accepted knowingly: the checklists come from the provisional
highlights, not the final gold, and one training document shares most of its wording with a test document.

**P2's first model, and why it did not work yet (D68).** P2 trained a t5-small on Kaggle and sent it as a
zip. It was opened carefully — unpacked in its own empty folder, only the plain weight file loaded — and
compared with the original, untrained t5-small. Every layer had changed, but none by more than 0.44%.
*Analogy: a new employee who sat through a 20-minute induction — officially trained, still working exactly
as before.* Scored with P2's own acceptance check, 18 of its 117 summaries of the training passages passed
(the untouched t5-small: 14), and it copied 78% of its wording straight from the first sentences of the
passage. Two settings explain it: a step size of 2e-5, which suits BERT-style models but is 5 to 15 times
too small for T5, and only 3 passes over 117 examples. The config files in `configs/` already hold the
right values (3e-4 for t5-small, 1e-4 for Flan-T5-base, 20 passes).

**The retrain pack.** P2 was sent one self-contained script, `train_summ.py`, with the two config files,
the data and P1's reference scores. Tested on P1's laptop with t5-small: the training loss fell from 2.17
to 0.59, copied wording from 92% to 42%, checklist facts kept rose from 22% to 66%, and acceptable
summaries from 1 to 5 of 13. So the model now really learns — but it does not come close to passing every
summary, and it still makes mistakes of meaning, such as turning "no warranty that the platform is
uninterrupted" into "the platform is uninterrupted". With 117 examples that is the ceiling. (The
faithfulness check will *not* catch this kind of error by itself — see the next part.) The script makes
two choices worth knowing:
- **It trims every summary to the word cap.** About half of the raw summaries run long, so each is cut back
  to the whole sentences that fit. The pipeline must apply the same step. *Analogy: an editor who deletes
  the last sentence rather than sending the piece back for a rewrite.*
- **It keeps the model from the last pass.** The mock test has only 13 passages, so its score moves by one
  or two from pass to pass by pure chance; choosing a "best" pass would be choosing noise.
It also writes `summ_meta.json` — the prefix, the lengths, the generation settings and the scores — so the
pipeline can use the model exactly the way it was trained.

**P2's retrained model (D69).** P2 ran the pack unchanged and sent back the t5-small (not yet the
Flan-T5-base). What a trained summariser folder contains:
- `model.safetensors` — the model itself: its 60 million learned numbers.
- `config.json` — the model's blueprint (how many layers, how wide), needed to load the numbers.
- `generation_config.json` — default writing settings; the pipeline uses the ones in `summ_meta.json`.
- `tokenizer.json`, `tokenizer_config.json` — the dictionary that turns text into the word-pieces the
  model reads, and back.
- `summ_meta.json` — the run's logbook: the settings used and the scores after every pass.
- `dev_predictions.jsonl` — the 13 mock-test summaries the model wrote, each marked accepted or not, with
  the reason.

The model is now properly trained: its most-changed layer moved 12% (the first model: 0.44%), it passes 84
of the 117 training passages (first model: 21) and copies only about a fifth of its wording. On the 13
passages it has *not* studied it passes 3, and keeps 47% of the facts. That gap — 72% on seen text, 23% on
unseen — means it has largely memorised. *Analogy: a student who learned the practice paper by heart.*
The cure is more examples and a larger model, not more passes.

Reading the 13 summaries showed something no score did: four have the meaning wrong and two are
*reversed* — one tells the user they "must interrupt, destroy or limit" a computer resource where the
policy forbids it, and that summary **passed** the acceptance check, because the check only counts words
and facts. The planned faithfulness check has the same blind spot: it compares *which facts* are
mentioned, so it catches a dropped or invented fact but not a "must not" that became a "must".
*Analogy: a proof-reader who checks that every name in the contract appears in the summary, but not who
owes whom.* A separate check for reversed meaning is needed; the `negated` mark on the gold highlights
(5.9.27) is where it would start.

**One split for everything (D70).** The paragraphs above describe the first dataset: 13 training
documents chosen before the NER split existed. P1 then decided that the summariser must use the *same*
split as the NER models (section 7.2 explains why), and the dataset was rebuilt:
- **Training:** the NER adaptation documents, minus the two with glued-together words — 12 documents,
  193 passages, giving 174 training and 19 mock-test pairs.
- **Test:** the 9 NER test documents — 154 passages, 84 of them with gold facts. Sealed.
- **Checklists** now come straight from the final answer key (`--gold`), not from the provisional merge.
- **Every passage is trained on**, even one with no highlighted fact, because the finished system has to
  summarise every passage of a document, not only the interesting ones.

Claude Opus 5.5 wrote 156 new summaries and revised 10 of the 37 that carried over; the 93 older ones that
now sit on test documents were set aside (`refs_test_silver.jsonl`) and may only be used for optional
overlap scores. One writing rule was added. Some passages start in the middle of a list whose heading —
"you shall not ..." — is on the previous passage. For those the summary says "the list covers ..."
and does not say whether the acts are allowed or forbidden. *Analogy: handed page 2 of a list without its
heading, you report what is on the page; you do not guess the heading.* A model taught to guess is how
"you must not" turned into "you must".

A test run of t5-small on the new data shows what the larger set bought and what it did not. The writing
became more fluent — only 28% of the wording is copied — and 13 of 19 mock-test summaries passed. But 10
of those 19 passages have no checklist and pass on length alone; on the 9 that have one, 3 passed and 62%
of the facts were kept, about the same as before, and one summary again reversed a meaning. The training
script now reports the two groups separately so that nobody mistakes the easy passes for progress. And
because the training documents share templates, the mock test is easier than the real one will be.
P2's two earlier models were trained on what are now test passages and cannot be used for testing.

**Both models side by side, and where the bar really is (D72).** P2 then delivered a t5-small trained on
the new data and a Flan-T5-base — which turned out to have been trained on the *old* data, so it has seen
the test documents and must be redone. It also would not load correctly: Kaggle's newer library saved a
setting whose meaning our older library reads differently, and the model wrote gibberish until the loader
was told how to read it. *Analogy: the same recipe, with "tsp" read as tablespoon — the ingredients
are right, the dish is ruined.* The weights were fine; the pipeline's loader has to carry this fix.

With that solved, the two model sizes could be compared fairly for the first time: both trained on the same
117 old pairs, both scored on 136 passages neither had seen. Flan-T5-base passed 58% of the passages that
have a checklist and kept 67% of the facts; t5-small passed 44% and kept 55%. Twelve summaries from each
were read against their passages: t5-small had the meaning wrong in seven, Flan-T5-base in four —
including "the company retrieves your financial information without your explicit consent" where the
policy promises the opposite.

Three lessons follow. The larger model is better, so it is the main one. More data and more passes do not
help much: Flan keeps 90% of the facts on passages it studied and 65% on fresh ones, and going from 117 to
174 examples changed almost nothing. *Analogy: a student who scores 90 on the practice paper and 65 on a
fresh one does not need to re-read the practice paper.* And even the better model misstates the meaning
about one time in three, which no retraining at this size will remove. So the bar belongs on the
*system*, not the model: a summary reaches the user only if it passes the faithfulness check and a check
for reversed meaning; otherwise the system shows the plain list of facts it found. *Analogy: a junior
writes the letter, but nothing is posted until a second person has checked it — and if it fails, the
client gets the bare facts instead.*

**The final models (D73).** P2's rerun of Flan-T5-base came back correct: right data, right library version,
and a training curve that matches P1's reference run almost exactly. So both summarisers are now trained
the way the project intended, and the training work is done. Read against their passages, the 19 mock-test
summaries still contain 4 wrong meanings for t5-small and 3 for Flan-T5-base — including one each that
turn a "shall not" into a "does". That confirms the plan above: the models are frozen, and the remaining
work is the check that stops such a summary from reaching the user.

### 5.11 The smart contract — P3's track (`P3.md`)

P3 owns this; the full step-by-step guide is `meta-documentation/P3.md`. The essentials:

- **What it does:** records a tamper-evident *fingerprint* of each consent on the Ethereum test network
  (Sepolia), so anyone can later check that a consent existed and was not altered. **Only a hash goes
  on-chain — never any personal data.** *Analogy: a wax seal in a public glass case proves the letter is
  genuine and unopened without showing what it says.*
- **The fingerprint:** the consent artefact is turned into one exact, repeatable string (keys sorted, no
  spaces) and hashed with keccak256. Same consent -> same hash; change one character -> a completely
  different hash. The consent's id is `keccak(hash + nonce)`, so two consents never collide.
- **The contract (`ConsentRegistry.sol`):** a status per consent (NONE -> CREATED -> GRANTED -> REVOKED);
  `createConsent`, `grantConsent`, `revokeConsent` (owner only); `recordAccess` — the *state-changing*
  check that records an access attempt as an event and is what the security tests attack; and `isValid`,
  a free read-only version. Expiry is checked only when someone asks ("lazy expiry"), because a contract
  cannot run a timer.
- **Practicalities:** a throwaway wallet with free test-ETH only (never real funds); the private key lives
  in the git-ignored `.env`; deployment through Remix (nothing to install); `web3.py` v6 fills the
  `chain/` stubs.
- **What proves it works:** three tests — the genuine consent verifies **valid**, a tampered one
  **invalid**, a revoked one **invalid**.
- **Honest limits for the paper:** it proves a record was not *changed*, not that whoever created it was
  *honest*; and per D28 it is a reference implementation of a known pattern, not a novel mechanism.

**P3's first version, reviewed (D71).** P3 committed the contract, a Hardhat project to compile and test
it, and the three Python files. The contract compiles, its three tests pass on a local practice chain, and
its rules hold when attacked: only the owner can grant or revoke, an id cannot be registered twice, a
changed document is rejected, an expired consent is refused. Three things remain:
- **The Python breaks on first real use.** The function that sends a transaction asks for a field under
  the name used by a *newer* version of the library than the project installs, so nothing can be sent.
  The test did not notice, because it used a stand-in object with the same wrong name. *Analogy: a fire
  drill run with a cardboard extinguisher — the drill passes, the fire would not be put out.* The consent
  id is also printed with a doubled `0x`, the file's comment fields are hashed along with the consent, and
  the expiry is taken from a command-line number, not from the consent itself.
- **The promised security test is not there yet.** `recordAccess` — the function that leaves the audit
  entry — is never called by any test, and the contract is not deployed.
- **Two gaps in the design, which come from our own guide.** The consent's id is chosen by whoever calls
  first and is never checked, so a stranger can register it before the owner. *Analogy: a cloakroom
  where you choose your own ticket number — anyone who sees it can hang their coat there first.* And
  anyone may add audit entries to any consent, with nothing recording who did. Both were shown on the
  practice chain, and both have small fixes: compute the id inside the contract from the caller's
  address, and write the caller's address into the audit entry.

**Fix pack v2 (D77).** The last small gaps are closed in a pack P3 applies: one settings file for the whole
project, one name for the wallet key, a revoke tool that takes any consent, a way to write the "who checked"
entry, an Etherscan link from every registration, and a refusal to talk to any network but the test ones.
*Analogy: the door is hung; what remains is getting the keys cut at the locksmith* — the test wallet, test
money from a faucet and the Sepolia deployment, which only P3 can do.

**On the real test network (D78).** P3 deployed it to Sepolia and ran all four steps there — create, grant,
record a check, revoke. P1 confirmed that what sits on the chain is exactly the code in the repo, and that the
project's own `check()` reads the live record correctly. One surprise for the paper: creating a consent costs
about four times as much gas on Sepolia as on the practice chain, most likely because Sepolia now charges more
for adding new storage. *Analogy: the same parcel costs more to post this year — the parcel did not change, the
tariff did.* Left to do: publish the source on Etherscan so anyone can read it next to the address.

One more honest limit for the paper: a hash hides the consent only if its contents are hard to guess.
Consent artefacts are structured and partly predictable, so someone who can guess one can confirm it
against the chain. Storing only a hash limits exposure; it is not secrecy.

**The second commit (D75).** P3 fixed everything on the list: the id is now worked out by the contract from
the owner's own address, so nobody can take it first; every audit entry records who asked; the Python can
send; the expiry comes from the consent itself. P1 ran the whole round trip on a practice chain — register,
check (valid), change one date in the document (rejected), revoke (invalid) — and it behaved correctly every
time. *Analogy: the lock is fitted and the key turns; what is left is hanging the door in the real building.*
Left: it is not on Sepolia yet, and the one wallet key goes by three different names in three places, so
nobody can fill in the settings correctly; the revoke script works on one hard-coded consent only; and no
Python code writes the "who checked" audit entry yet. Each one is a small fix.

### 5.12 The test / adaptation split and the gold -> CoNLL converter (D52)

**The problem nobody had looked for.** The plan was to split the 23 documents by company — a company's
documents all on one side — so the model is never tested on text it trained on. But company names hide
something: **many AA terms are the same template with the name changed.** `aa_split.py` compares every pair
of documents by how much of the shorter one's wording (runs of eight words) also appears in the other.
`09_saafe_terms` and `16_oms_aa_privacy` share 75%; `03_oms_aa_terms` and `04_pb_fintech_aa_terms` share 51%;
and a *family of 13 documents* — Setu, Digio, OMS, PB Fintech, OneMoney, Saafe, ScoremeAA — is tied together
by shared text or shared company. *Analogy: thirteen students handed in essays copied from the same guidebook.
Put six in the practice set and seven in the exam, and the exam tests memory, not understanding.*

**How the tool works.** Link two documents if they are from the same organisation **or** share at least 10%
of their wording. Follow the links: every connected cluster is a *group*, and a group is never split. It uses
only the text and the manifest — never the gold labels and never a model's output — so the split cannot be
tuned, even accidentally, to make results look better. It refuses to write a split that leaks, or one that
puts a glued-text document in the test set.

**The consequence.** The old plan of "15 test + 8 adaptation" cannot be done cleanly: the family of 13 has to
sit on one side. Two honest options remain. **A — family as adaptation:** the test set is the 9 independent
documents (PennyDrop, CredBuddha, The Financialist, Zerodha, Indifi, ICICI, Upmint, NADL x2) with 726
entities, well balanced across the three labels. **B — family as test:** 12 documents that are largely copies
of one another, 374 entities, only 52 third parties. A is recommended: nearly twice the entities, genuinely
independent documents, and a stricter E2 — the model practises on AA-operator templates and is examined on
other organisations' documents. Its cost is a test set of 9 documents instead of 15. **P1 chose A (D54).** The split is written to
`data/splits/aa_split.json`; the largest overlap between a test and an adaptation document is 4.7% — two
citizen's charters quoting the same regulatory wording.

**`aa_to_conll.py` — from the gold file to what the model reads.** The models were trained on files with
one word per line and a tag beside it (`bank B-DATA_TYPE` / `statements I-DATA_TYPE` / `for O`). The AA
gold file is a list of character positions in long documents, so it has to be converted — with one trap.
The model reads at most 256 word-pieces at a time and the training code *silently cuts off* anything longer.
Feed it a 6,000-word document and nearly all the gold answers would be dropped without any error.
*Analogy: a scanner that only reads the top third of each page and never tells you.* So each document is cut
into **segments** of at most 100 words, at sentence ends, **never in the middle of a gold highlight**.
OPP-115's training segments are paragraphs of about the same size, so the model sees input of a familiar
length.

Two safeguards. First, after converting, every document's highlights are rebuilt from the tags and counted
against the gold file — if one was lost, split or merged, the tool stops. Second, a small companion file
(the *docmap*) records which document each segment came from, because the statistics must be computed over
**documents**, not segments: two segments of the same contract are not independent evidence.

**What the glued documents taught.** The check failed once, on `10_perfios_terms`: two gold highlights sat
inside one glued "word" (`…depositaccountsandcurrentdepositaccounts`), and a word-level file can give a word
only one tag. That is the concrete reason the two glued documents may be used for practice but never for the
exam. The tool allows it for those two by name, reports it, and treats it as a bug anywhere else.

A trial on the provisional gold with option A — in a scratch folder, nothing written to the project — gave
560 test segments holding 726 entities and 845 adaptation segments holding 426, and the training code's own
reader read both back correctly. Repeated after the rules meeting (D55): the same 560 and 845 segments, now
holding **824** test entities (295 data types, 258 purposes, 271 third parties) and 437 adaptation entities.

### 5.13 The faithfulness gate — `summ/faithfulness.py` (D74)

The summarisers are frozen, and even the better one gets the meaning wrong sometimes (D72, D73). So nothing
the model writes reaches the user unchecked. *Analogy: a junior drafts the letter; a checker reads it
against the file before it is posted, and if it fails, the client gets the bare facts instead.*
`gate(passage, summary, facts)` is that checker. It looks for four things.

- **Kept facts.** Each fact of the passage (the gold highlights while evaluating, the NER model's highlights
  in the real pipeline) should be recognisable in the summary. The test is the word-overlap rule that
  accepted the reference summaries, so the bar is the same one the training data met.
- **Invented names and numbers.** A number, name or acronym in the summary that the passage never mentions
  ("resolved in 30 days by RBI" when the passage says "one month") is a red flag. One model copied a company
  address footer and turned "Bangalore" into "Bangkok"; this check caught it.
- **Reversed meaning.** The dangerous error: "will not share without consent" summarised as "shares without
  consent". Each claim in the summary is matched to the passage claim it restates — the one sharing the most
  content words, at least two of them — and the two are compared: does each one *deny* or *affirm*?
  The rules for reading a stance are the ones a careful person uses:
  - "not", "never", "no", "disclaim", a plain "without warranty" deny.
  - An exception lifts the denial: "will not share, except with consent" affirms sharing — with consent.
  - A condition the summary simply leaves out ("may change the terms [without notice]") is not held against
    it. *Analogy: a shorter sentence is not a lie; an opposite one is.*
  - A "not" that belongs to something else is not the claim's stance: inside an "if" part ("if you do not
    want cookies, change your settings"), in a relative clause ("a number that does not have a meaning"),
    in a heading ("No access:") or in boilerplate ("not limited to").
  - A list inherits its heading: in "you shall not: (a) copy the app, (b) send viruses", each item is a
    "shall not". The heading can sit at the end of the *previous* passage, so the gate is given that passage
    as context. *Analogy: page 2 of a list of rules still belongs under the heading on page 1.*
- **Swapped party.** The same stance, but the other side doing it: "you may assign your rights" for "we may
  assign our rights". "We shall require you to upload documents" names both sides, so "you must upload
  documents" is not a swap.

The verdict: **reject** — anything invented, reversed or swapped — and the user sees the plain list of facts;
**add** — the summary is fine but drops facts, so the missing ones are listed under it; **show**. Every listed
fact carries a "denied" mark (D66's meaning: the passage says the practice is *not* done), so "contact
lists — denied" reads correctly. That mark agrees with 116 of the 124 D66 proposals (which P1 still has to
check), including all 67 denials; the 8 others are in text with missing full stops.

**How it was tested.** Each summary was read against its passage and marked OK, REV (a claim turned into its
opposite) or ERR (any other wrong claim). The gate was built and tuned on 118 such summaries — there it
blocked no correct summary and caught 9 of 10 reversals, but numbers on your own practice paper are always
flattering. The honest test is two documents nobody had used: the two glued-text documents, left out of
summariser training. Both final models summarised their 29 passages (58 summaries), the summaries were
labelled first, and only then was the gate run. It caught **both reversals**, among them Flan-T5-base
writing "you may modify, rent, lease or sell the services ... or reverse engineer" where the policy says you
shall *not*. It blocked **4 of 38 correct summaries**. Two of those were caused by the glued words
("willnotbeheldliable" hides its "not"), and two by matching a claim on one shared word. Three general fixes
followed, which brought the false blocks to 1 in 38. But numbers measured after fixing what the test showed
are no longer a fresh test.

**What it does not catch.** Most remaining mistakes are not reversals: a garbled definition ("It is a person
who has entered into a contract" said of the consent artefact), a list mangled into nonsense, a condition
dropped that mattered, "may" for "shall". For the main model, Flan-T5-base, 4 of the 27 summaries the gate
let through on the fresh documents were wrong in such ways (about 15%). So the gate removes the most
dangerous error, the reversal, but it is not a full fact checker. That is why the facts list, with its
denied marks, is shown under every summary that drops facts, and why the summary is never the only thing
the user sees.

**P1's check (D81).** P1 labelled the 58 fresh summaries without seeing anyone else's labels. The two of us agreed
on 67% of them (kappa 0.32; 76% and kappa 0.45 on simply "right or wrong") — moderate, which is normal for judging
meaning, and the disagreements run both ways. *Analogy: two examiners marking the same essays — they agree on most,
and the ones they don't are discussed before the marks are final.* The 19 disputed summaries were then settled
together (D82): P1 took Claude's label in 14 and kept their own in 5. On the settled labels the check caught one of
the two reversals (it missed one because it does not know "Perfios" is a company), blocked 2 of 36 good summaries,
and cut the share of wrong Flan-T5-base summaries a user sees from 28% to 22%. So it helps, modestly; the facts
list under the summary is what really protects the reader. *The earlier "caught both reversals" was on Claude's
labels alone.*

**Two honesty notes.** Every label in the first numbers was written by Claude; `gate_label_check_P1.csv` asks P1
to label the 58 fresh summaries alone, so the agreement can be reported. And while testing, a real bug turned
up: giving the gate the previous passage as context made it drop the current passage's first sentence in
152 of 326 passages (the sentence seemed to run on from a section number like "17.3" at the end of the
previous one). It is fixed, and a self-test now guards it.

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

**E2: two ways to give the model AA practice (D61).** The same script trains E2 with one extra flag.

- `--e2 joint` — start from the untouched pretrained model and train once on the American policies **and**
  the AA practice documents mixed together. *Analogy: a driver who practises in Delhi and Mumbai in the same
  weeks.* Fairest comparison with E1, but the AA documents are a small share of the pile (about 330 of 10,300
  highlights) and may barely be heard.
- `--e2 sequential` — take the finished E1 model and give it a second round on the AA documents alone.
  *Analogy: finish learning in Delhi, then move to Mumbai and practise only there.* It may forget some Delhi
  habits — which hardly matters, since the model's job is Indian documents.

Both are run, so the paper can say which way of using a small amount of local data works better.

**The mock test.** Training goes in rounds and stops when a mock-test score stops improving. E1 used American
policies for that. For E2 four AA practice documents are kept out of training and used as the mock test, so progress is
judged on the right subject. They were chosen by a rule (D62): the practice documents that share the *least*
text with the ones left for training — at most 18% — holding 107 highlights between them. (The first choice,
two Saafe documents, turned out to include one that is 75% identical to a training document. *A mock paper
that repeats the textbook's worked examples tests memory, not understanding* — and would have let training
run on while the model was only memorising the template.) *Analogy: a student preparing for a
Hindi exam should check progress with a Hindi mock paper, not an English one.* The mock score may still flatter a
little (all these documents come from the same family of AA operators), but it only picks the best round; it
is never reported as a result. The real test documents are never used for this.

**Copies, not originals.** An E2 run never changes an E1 model. `joint` does not open one at all; `sequential`
*reads* the E1 model and writes its result into a new folder (`legalbert_e2s_s42` beside `legalbert_s42`).
The E1 models must stay exactly as they are, because they still have to sit the exam themselves.

**Repeats.** Each of the three model types is trained three times per condition with the same three random
starting points as E1 — 18 new runs — so every E2 model has an E1 twin that differs only in the AA practice.

### 6.4 `ner/evaluate.py` — score a trained model

Loads a saved model and a CoNLL file, predicts, and scores. It answers six questions, because a single F1
number would hide most of what this project needs to know (D60).

1. **How many entities did it get exactly right?** Exact-match precision, recall and F1 — overall, averaged
   over the three labels, and per label. Same measure as during training.
2. **How many did it roughly get?** *Relaxed* match: the prediction counts if it overlaps a gold entity of the
   same label. Our answer key draws boundaries by our own guideline (`email address`, not `your email
   address`); a model trained elsewhere that marks `your email address` found the right thing. *Analogy:
   marking a spelling test by "right word" as well as "every letter right".*
3. **How sure are we?** A 95% confidence interval. The trick is *what to resample*. Sentences from one
   document resemble each other, so shuffling sentences would make us look more certain than we are. The
   script resamples whole **document groups** — a company's documents, or documents sharing a template, count
   as one. *Analogy: to know how a class will do next year you look at different classes, not at the same
   pupils' answers reshuffled.* With 8 groups in the test set the intervals will be wide, and that is honest.
4. **Does one document decide everything?** One test document holds a third of the entities, so the score of
   each group is listed and their plain average is given next to the pooled score.
5. **What kind of mistakes?** Each prediction is exact, right-label-wrong-boundary, wrong-label, or spurious;
   each gold entity is found, found with another boundary, found under another label, or missed. Spurious
   predictions are then sorted: *telemetry* (`IP address`), *AA role* (`Financial Information User`),
   *umbrella term* (`financial information`, `third parties`) — things OPP-115 taught the model to mark and
   our guideline deliberately leaves out — plus *corporate transaction* and *other*. F1 is reported again with
   those "different definition" predictions set aside, so the paper can separate "the model is wrong" from
   "the two rulebooks disagree".
6. **Was anything cut off?** The model reads at most 256 word-pieces; anything longer loses its tail without a
   word. The script counts such segments and scores the lost part as missed.

**Comparing E1 with E2.** `--compare <E2 runs> --against <E1 runs>` averages each side over its seeds and
bootstraps the *difference* on the same resamples for both (a paired test — both sides face the same luck of
the draw). If the interval for the difference contains zero, it prints "no significant difference".

**The seal.** The test file cannot be scored by accident: it needs `--open-test`, and each opening is written
to `results/ner/test_openings.jsonl`. Day-to-day the script points at dev.

**Checked before use, without touching the test set:** a self-check on hand-made examples; the OPP-115 dev
score reproduced (0.397 against 0.401 at training time — the difference is the 18 over-long dev segments whose
tails training silently ignored); and all nine E1 models run on the *adaptation* documents. That last run is
a rehearsal, not a result, but it is a warning: about **0.09** exact and **0.22** relaxed F1, with the models
predicting more than twice as many entities as the key holds and a third of the extra ones being
different-definition cases. E1 on the test set should be expected to be low.

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

**The first full sweep, and how to read it (D38).** All 9 runs completed (3 backbones x 3 seeds, every
group `x3`). OPP-115 dev entity macro-F1: Legal-BERT **0.400 +/- 0.006**, InLegalBERT **0.386 +/- 0.003**,
BERT-base **0.382 +/- 0.003**; token-F1 0.522 / 0.513 / 0.526. Two cautions decide how this is reported:
the **ranking flips** between the two metrics (Legal-BERT leads on entities, BERT-base on tokens), which
is the classic sign of *no clear winner*; and the **+/- is over seeds**, so it only measures training
randomness — it is **not** a significance test. Significance comes from bootstrap confidence intervals
over **documents**, on the AA test set. *Analogy: re-rolling the same dice three times tells you how
steady your hand is, not whether the dice are loaded.* These dev numbers are a health check; the
headline is E1/E2 on the AA test set.

### 6.6 The config files (`configs/*.yaml`)

Each experiment is one YAML: `model_name` (the HF id), `labels`, `seed`, `learning_rate`,
`num_train_epochs`, batch size, early-stopping patience, and the train/dev file paths. Three NER configs
(`ner_bert_base`, `ner_legalbert`, `ner_inlegalbert`) and two summarizer configs. *Analogy: a recipe
card — same method, swap one ingredient (the backbone) to compare fairly.*

---

### 6.7 The headline result: what a little local data is worth (D63)

The exam was opened once, for all 27 models at the same sitting: nine that had only studied American privacy
policies (**E1**), nine that studied American policies and Indian AA documents mixed together
(**E2-joint**), and nine that finished the American course first and then took a short second course on the
Indian documents alone (**E2-sequential**).

| | Strict score (exact match) | Lenient score (overlap) |
|---|---|---|
| E1 — American policies only | **0.13** | 0.29 |
| E2-joint — both together | **0.25** | 0.44 |
| E2-sequential — American first, then Indian | **0.44** | 0.61 |

*Analogy: a driver trained only in Delhi, tested in Mumbai, gets about one manoeuvre in eight exactly right.
Mix a few Mumbai lessons into the Delhi course and it is one in four. Give the same few lessons as a
separate finishing course and it is nearly one in two.*

**Three things the numbers say.**

1. **Learning elsewhere is not enough.** A model that scores 0.40 on American policies scores 0.13 on Indian
   AA documents. It marks too much (944 guesses for 826 answers) and still misses two thirds of the real
   ones. Part of this is the two rulebooks disagreeing — the American data marks "financial information" and
   "third parties", ours does not — but taking those cases out only lifts 0.125 to 0.138. Mostly, the model
   simply does not recognise what matters in these documents.
2. **A small amount of local data is worth a great deal — about 330 highlighted phrases from 10 documents
   more than tripled the score.** And the gain shows up on *other companies'* documents of a different kind,
   so it is not memorising a template.
3. **How you give the local data matters as much as having it.** Mixed into 10,000 American examples, 330
   Indian ones are a 3% voice and are mostly drowned out. Given afterwards, they have the last word. This was
   P1's prediction before the run (D61), and the difference between the two ways (+0.19) is as large as the
   whole benefit of the mixed way.

**The model types.** With American data only, the three are indistinguishable. After the second course,
Legal-BERT is clearly ahead (0.48 against 0.41-0.43). The model pre-trained on Indian court judgments
(InLegalBERT) gains nothing from being Indian: fintech privacy policies are not court judgments.

**How sure is this?** Each difference was tested the paired way described in 6.4, and none of the intervals
comes near zero. What keeps the conclusions modest is the size of the exam: 9 documents from 8 organisations,
one of which holds a third of the answers, and an answer key that is itself about 2% wrong and 7% incomplete.
The *ordering* E1 < joint < sequential is solid; the exact decimals are not.

**The exam is now used up.** Looking at these results and then changing a model or a rule and re-scoring would
be studying with the answer sheet open. Anything new is tried on the practice documents.

### 6.8 `ner/llm_baseline.py` — what if you just give a chatbot the rulebook? (D64)

The models of 6.7 *learned by example*: they were shown highlighted text and never read a rule. A large
language model can do the opposite — read the rules and try, with no training at all. If that works as well,
there was no need to annotate training data. *Analogy: two ways to learn a board game — play 300 practice
rounds with someone correcting you, or read the rulebook once and start. The paper needs to know which player
is better.*

**How it works.** One passage at a time is sent to the model with a 470-word summary of the labelling rules.
The model answers with a list of phrases and labels. Each phrase is located in the passage word for word and
turned into the same tags the other models produce, then marked by the same marking program. A phrase the
model invented — not present in the passage — is thrown away and counted.

**Two versions.** *Zero-shot*: rules only. *Eight-shot*: rules plus eight worked passages, taken from the same
ten practice documents the E2 models trained on.

**Three safeguards.** (1) The rule summary contains only general rules; the guideline's list of "tricky cases"
quotes the exam documents and is left out — the program refuses to run if the prompt names an exam company.
(2) All trial-and-error happens on the four mock-test documents; the exam is scored once with everything
frozen. (3) The baseline model should not be from the Claude family, because an assistant from that family
helped settle the answer key — it would be marking its own homework.

**Where it runs.** By default on a model installed on the laptop itself (through Ollama), so no policy text is
sent anywhere. A hosted model can be used instead by pointing the program at its address.

**What happened (D65).** Two free, open models were run on the laptop: a small one (Llama 3.1, 8 billion
parameters) and a larger one (Qwen 2.5, 14 billion).

| | Strict score | Lenient score |
|---|---|---|
| E1 — learned from American policies | 0.13 | 0.29 |
| Best fine-tuned model (Legal-BERT, second course on AA documents) | 0.48 | 0.64 |
| Small chatbot, rules only | 0.28 | 0.33 |
| Small chatbot, rules + 8 examples | 0.41 | 0.47 |
| **Larger chatbot, rules only** | **0.48** | 0.55 |
| Larger chatbot, rules + 8 examples | 0.45 | 0.52 |

**The player who only read the rulebook drew with the player who practised.** On the strict score the larger
chatbot, with no training and no examples, ties the best trained model (the difference is 0.000, with a range
from -0.05 to +0.08). It is a different kind of player, though. It finds more of the answers (about two in
three, against two in five) but highlights nearly twice as many phrases as there are answers — *an eager
student who underlines half the page*. The trained model is more careful, and stays ahead on the lenient
score. The chatbot is much better at spotting organisations; the trained model is better at data types.

**Why this is good news and a warning at once.** Good news: writing clear rules — which this project spent
five annotation rounds doing — turns out to be as valuable as the labelled data itself. Warning: the rules
were written while reading all 23 documents, the exam documents among them. They quote none of them, but they
were *shaped* by them, and the trained models never had that advantage. So the tie is an upper estimate for
the chatbot. The fair re-match needs fresh documents the rulebook has never met.

Other limits: one run each, two modest open models (a bigger commercial one would likely do better), and the
chatbot takes seconds per passage where the trained model takes milliseconds.

## 7. How everything connects (end-to-end)

```
DOWNLOAD                 CONVERT                         TRAIN / EVALUATE
OPP-115 (usableprivacy) → load_opp115.py → spans.jsonl → bio_tagging.py → train.conll/dev.conll
                                                                              │
                                                                     ner/dataset.py (align subwords)
                                                                              │
                                                                     ner/train.py → model + dev metrics
                                                                              │
AA docs (manifest) → scrape_aa.py → raw html/pdf → clean.py → 23 text docs → [ANNOTATE x2]
      → kappa.py (agreement) → fixlist.py (each fixes own work) → adjudicate_auto.py (+ sample check)
      → gold.json → aa_split.py (leak-free test/adapt) → aa_to_conll.py → aa_test.conll / aa_adapt.conll
                                                                              │
                                                              ner/evaluate.py → E1 / E2 results
```

The annotation itself is human work (two annotators, using `ANNOTATION_GUIDELINE.md`). Everything after it
is tooling: measure how far they agree, let each correct their own work, settle what is left rule by rule,
have both check a sample of those rulings, then split the documents so nothing leaks and convert the result
with the *same* word-and-tag machinery used for OPP-115. The test file is used for E1 and E2; the adaptation
file is the small training add-on for E2.

### 7.1 What is still to be connected

The diagram above ends at the NER scores. The full system has six steps, and this is where each stands:

| Step | What it does | Owner | State (14 Oct 2026) |
|---|---|---|---|
| 1. Clean | web page -> plain text | P1 | done |
| 2a. NER | highlights data types, purposes, third parties | P1 | done: `ner/predict.py` (Legal-BERT E2-sequential, seed 44) reproduces the trainer's mock-test F1 (D76) |
| 2b. Parser | reads duration, frequency, recipient from the consent JSON | P1 | done: `consent_artefact/parse.py`, checked on both real examples and 30 synthetic ones (D76) |
| 4a. Summariser | passage -> short plain summary | P2 | done: both models frozen, Flan-T5-base the main one (D73); `summ/predict.py` reproduces P2's summaries word for word (D76); on the Hub and checked from a fresh cache (D83) |
| 4b. Faithfulness check | did the summary drop or invent a fact, reverse a meaning, swap the party? | P2 | built (`summ/faithfulness.py`, D74); on fresh documents and the final labels (D82) it caught 1 of 2 reversals and blocked 2 of 36 good summaries; falls back to the facts list |
| 5. Blockchain | hash the facts, record on Sepolia | P3 | done: deployed on Sepolia, all four calls checked on the live chain (D78); source verification on Etherscan still to do |
| 6. Glue | one command, one report per document (`pipeline/end_to_end.py`) | P1 | done (D79): checked on a real policy page and a local chain; next the demo app |

**The three readers (D76).** `ner/predict.py`, `summ/predict.py` and `consent_artefact/parse.py` are the
parts that turn raw input into facts and summaries. Each was checked by making it redo something training
already did and comparing: the NER reader gets the trainer's mock-test score (0.733 vs 0.736), the summariser
reproduces all 19 of P2's mock-test summaries word for word, and the passage cutter gives exactly the 347
passages of the training data. *Analogy: before trusting a new photocopier, copy a page you already have and
lay the two side by side.* The summariser's cutting and trimming code was copied into the repo, because the
originals live in P2's files, which are not in it.

**How P2's model plugs in.** The summariser learns *passage -> summary*; the fact checklist was only an
instruction to whoever wrote the reference summaries, so at run time the model needs nothing but the
passage. Three things must match between training and use, or the summaries quietly get worse: the model
folder itself, the settings in `summ_meta.json` (prefix, lengths, generation settings, the trim step), and
the passage cutter — the pipeline must cut documents with the same `chunk` function the training data was
cut with. *Analogy: a recipe only works if you use the same oven temperature and the same size of tin.*

**How the faithfulness check works (D74, section 5.13).** NER finds the facts in the passage; each should be
recognisable in the summary (*coverage*), by the word matcher that accepted the reference summaries —
the NER model on its own is right only about half the time and cannot be the sole judge. Inventions are
caught as names and numbers the passage never mentions (instead of running NER over the summary, as first
planned). On top of that, each summary claim is compared with the passage claim it restates, for a reversed
meaning or a swapped party. The pipeline passes the previous passage as `context`, because a list's
"you shall not:" heading can sit there.

**The whole system in one command (D79).** `python -m consentledger.pipeline.end_to_end --doc <policy> --consent
<consent.json> [--chain]` runs every step and writes one report. For each passage the user sees the summary,
the summary with the facts it dropped, or — if the check rejected it — just the facts. Then the consent JSON and
the policy's facts are put together into one record, and that record's fingerprint is what goes on the chain.
*Analogy: the clerk staples the terms you were shown to the form you signed and seals the bundle — anyone can
later check that neither page was swapped.* A fact counts as "denied" only if the policy never says the
opposite elsewhere. Checking a consent later uses the saved record from the report, not a fresh run of the
models.

### 7.2 The two splits do not line up

The NER models and the summariser were split into training and test documents separately, and the two
splits cross: the summariser *trains* on 13 documents of which 8 are NER **test** documents, and is *tested*
on 10 documents of which 9 are NER **training** (adaptation) documents. Only one document,
`08_pennydrop_terms` (29 passages), has been seen by neither model. End-to-end numbers only mean something
on documents neither model has studied. *Analogy: two examiners who each wrote their own paper — and each
paper contains the other's practice questions.*

The fix is one split for the whole system: the summariser trains on the NER adaptation documents and is
tested on the 9 NER test documents. **P1 decided this on 12 Oct and it is done (D70):** 156 new reference
summaries were written, the training set grew from 117 to 174 pairs (plus 19 for the mock test), nine
documents are now unseen by both models instead of one, and the `16_oms_aa_privacy` / `09_saafe_terms`
template overlap is gone because both sit on the training side. The two glued-text documents are left
out of summariser training.

### 7.3 Testing it as one pipeline

*Analogy: a relay race — time each runner alone, then the whole team.*
- **Level 1, does it run:** one document end to end, with a local test blockchain instead of Sepolia.
- **Level 2, each part alone:** the NER scores (done), the summariser scores (P2), and P3's three contract
  tests (genuine -> valid, tampered -> invalid, revoked -> invalid).
- **Level 3, the team time:** run the test documents twice — once feeding the *gold* highlights into the
  faithfulness check, once the *NER model's* highlights. The gap shows how much NER mistakes damage the
  final result.

### 7.4 Deploying it

"Deploying" means something a person can open: paste an AA policy, press a button, get the highlights, the
plain summary, the faithfulness check and a blockchain link. *Analogy: a restaurant — the kitchen staff, the
public register and the counter.*
- **The models (the staff)** live on the Hugging Face Hub; the app downloads them when it starts. **Checked (D83):**
  downloaded into an empty cache, all three are byte-identical to the originals and give the same results. The repos
  are private, so the app needs a Hub token (`HF_TOKEN`).
- **The contract (the public register)** is deployed once on Sepolia by P3 and then has a permanent address.
- **The app (the counter)** is a small Gradio web page that calls the same pipeline function the experiments
  use, so the demo and the reported numbers cannot drift apart.

**Built (D80):** `python app.py` opens it at http://127.0.0.1:7860 — paste or upload a policy, add the consent,
and read the coloured facts, the checked summaries, the consent terms and the fingerprint; a second tab checks a
recorded consent against the chain. Building it exposed one real bug: when a policy mentions the same thing twice
("we collect your mobile number" ... "we will not sell your mobile number"), both mentions got the first one's
"denied" mark. *Analogy: a teacher marking every answer by looking only at the first student's paper.* Each mention
is now judged where it stands.

It runs first on P1's laptop (fast, for the viva) and can then be put on a Hugging Face Space (a public
link, slow on the free tier). Rules that carry over: the Hub token and the test wallet's key live only in
the Space's secrets or the local `.env`; the wallet holds test funds only; the "record on chain" button is
optional and rate-limited; the app ships none of the 23 scraped documents; and it is marked research-use
only, because the NER models were trained on non-commercial data. **Packaged (D84):** `python space/build.py`
puts together a 366 KB folder — the app, the code, the demo consent and the contract's address — which was run
exactly as the Space will run it. **But Hugging Face now charges for Gradio Spaces (D85)**, so the demo runs on
the laptop; `python app.py --share` gives a temporary public link (optionally password-protected) while it runs.
*Analogy: instead of renting a shop, you open your own front door for an afternoon — free, but only while you are home.*

---

## 8. Current state: done vs pending

**Done & verified:** environment; OPP-115 loaded (24,516 spans) and BIO-tagged; span trimming
(D25); multi-seed training + `collect.py`; **the full E1 sweep — 3 backbones x 3 seeds on OPP-115 dev**:
Legal-BERT 0.400 +/- 0.006, InLegalBERT 0.386 +/- 0.003, BERT-base 0.382 +/- 0.003 entity macro-F1, with
the ranking flipping on token-F1 — i.e. **no clear backbone winner**, as the honesty rule expects. AA corpus
scraped, cleaned (23 documents), double-annotated. Consent-artefact schema verified against the primary
source (D27); contribution claims revised after a systematic search (D28, `RELATED_WORK.md`).

**Annotation — where it stands:** five measurements, all reported: round 1 kappa **0.279** on 23 documents
(D29); round-2 calibration **0.374** (D32); round 3 **0.283** — P4 had not received the guideline (D41);
round 4 **0.522** on a fresh document with both on the final rules, the one fully independent figure (D43);
and **0.426** on all 23 after both annotators worked through their personal fix lists (D48). The guideline
grew from v4 to **v7.5** (Rules 7-23) plus **PART I**, the rulings made while building the gold file.
The lesson of the last round: the fix lists removed almost all rule violations, and what remains is which
entities each annotator *notices* — which no list can fix.

**The gold file is final** (D50, D55-D59): **1,266 highlights** (559 data types, 381 purposes, 326 third
parties) built by settling 1,513 disputed highlights rule by rule. The annotators **met and decided the ten
rules** set after the fix pass — seven kept, one dropped, two changed (D55); each then **independently
checked a random sample** of 124 rulings — P1 accepted 96.0%, P4 100% (D56); and the five rulings P1 rejected
were corrected (D57). A three-perspective audit then found 49 defects, mostly among highlights both
annotators had drawn identically; they were corrected with two changes by P1 (D58, D59).
`data/ner_bio/aa_test.conll` (826 entities) and `aa_adapt.conll` (439) are generated.

Tools: `kappa.py` (`--docs`, rejects labels outside the scheme), `agreement_report.py`,
`annotation_audit.py` (`--strict`), `fixlist.py` (15 buckets), `relaxed_agreement.py`, `adjudicate.py`
(joint worklist), `adjudicate_auto.py` (`items` / `apply` / `score` / `negation`), `aa_split.py`,
`aa_to_conll.py`, `ner/evaluate.py`, `ner/collect.py`, `ner/llm_baseline.py`.

**Models on the Hub:** all 27 NER models (9 E1 + 18 E2) are in the private repo
`Karthikrishna05/consentledger-ner`; every weight file was checked against the local copy (11 Oct 2026).

**Summarizer (P2's track):** dataset builder and plan delivered to P2 via Drive (D33, D34); not in P1's
commits. The 130 training summaries are written and validated (D67, `data/summ/refs_train.jsonl`, sent by
Drive). P2's first t5-small was barely changed from the original (D68); after the retrain pack, P2's second
t5-small is properly trained (84 of 117 training passages acceptable) but weak on new text (3 of 13) and
sometimes reverses the meaning (D69). The dataset has since been rebuilt on the NER split with gold
checklists — 174 training and 19 mock-test pairs, all summaries written and validated (D70) — and P2 is to
retrain both t5-small and Flan-T5-base on it; the earlier models cannot be used for testing. P2's t5-small
on the new data is in; the Flan-T5-base delivered was trained on the old data and was redone correctly on
14 Oct (D72, D73). Both models are final.
Neither model is reliable enough to show summaries unchecked — about one in three has the meaning wrong
even for the better model — so the summariser needs the check-and-fall-back step around it. **That step is
built (D74, section 5.13):** on two fresh documents, scored on the labels P1 and Claude settled (D82), it caught
1 of the 2 reversed meanings and blocked 2 of 36 correct summaries. About 22% of the Flan-T5-base summaries it lets
through are still wrong in other ways (28% without it), which is why the facts list goes with every summary that
drops facts.

**Audit of the final gold (D58, D59):** before correction, about 98% of highlights correct, about 93% of
markable entities present, 92% consistency on identical text. The 49 verified defects are now corrected;
consistency on identical text is 99.1%. The unlocated remainder (roughly 5 wrong, 50-90 missed) is the
gold's stated error rate.

**Pending — in priority order:**
0. ~~Decide on the 49 audit corrections~~ **done — applied with two changes by P1; CoNLL regenerated (D59).**
   The `negated` flag (D66): **checked by P1 and applied (D81)** — 67 highlights marked, nothing else in the
   gold changed. The purpose row number is still optional (D58).
1. ~~P1 + P4 meeting~~ **done — 7 kept, rule 3 dropped, rules 4 and 9 changed (D55).**
2. ~~Choose the split~~ **done — option A, 9 test / 14 adaptation (D54).**
3. ~~Re-apply the changed rules, rebuild the gold, draw a fresh sample, both check it alone~~ **done — P1
   96.0%, P4 100%, gate passed; the five rejected rulings corrected; gold FINAL (D55-D57).**
4. ~~Run `aa_to_conll`~~ **done — `aa_test.conll` (826 entities), `aa_adapt.conll` (439) (D57, D59).**
5. ~~Build the evaluation script~~ **done (D60): exact and relaxed F1, group-bootstrap intervals, error
   breakdown with definition mismatch, truncation check, paired E1-vs-E2 comparison, sealed test set.**
   E2 design decided and built (D61, D62). **All 18 E2 models trained; the test set opened once for all 27
   (D63): exact micro-F1 E1 0.125 -> E2-joint 0.252 -> E2-sequential 0.439, every step significant;
   Legal-BERT best after adaptation (0.479).** **LLM baseline (D64, D65): a local 14B model given only the
   rules scores 0.479 — a tie with the best fine-tuned model on exact F1, behind it on relaxed F1.** The
   test set is spent — no re-scoring after changes. Open: how the paper is framed now (D65).
6. ~~Decide the split for the whole system~~ **done — one split, summariser dataset rebuilt (D70).**
   ~~Open: how reversed meanings will be detected (D69)~~ **done — the faithfulness gate (D74).** Open: P1
   labels the 58 fresh summaries alone (`gate_label_check_P1.csv`) so the labels' agreement can be reported.
   Then: P3's contract; P1's glue code
   (`ner/predict.py`, the JSON parser, `pipeline/end_to_end.py`); the demo app (sections 7.1-7.4).
7. Glued-text documents (`02_digio_terms`, `10_perfios_terms`): fixing `clean.py` is still open; they are
   adaptation-only until then (D36, D52).
8. Paper: Related Work and the annotation-methodology section can be written now (the agreement story is
   complete: 0.28 -> 0.37 -> 0.28 -> 0.52 -> 0.43, with the diagnosis at each step).

See `FLOW.md` for live status and `DECISIONS.md` (D1-D85) for the reasoning behind every choice.

---

## 9. Every output file, explained

- `data/external/opp115/processed/opp115_spans.jsonl` — one line per verified OPP-115 highlight
  (label + text + offsets + provenance). Git-ignored (contains OPP-115 text).
- `data/ner_bio/train.conll`, `dev.conll` — the word+tag training/dev files. Git-ignored, regenerable.
- `data/aa/manifest.csv` — the 29 AA docs (URLs + metadata). **Committed** (just URLs).
- `data/aa/raw/{html,pdf}/*` — raw downloads. Git-ignored (copyrighted pages).
- `data/aa/raw/text/*.txt` — the 23 cleaned, normalized, annotation-ready docs. Git-ignored.
- `data/aa/raw/scrape_log.csv` — provenance of the scrape (status, bytes, hash, date).
- `artifacts_out/ner/<run>/` — a trained model + `dev_metrics.json` + `run_meta.json`, and after the test
  was opened `test_metrics.json` + `test_errors.tsv`. 27 folders: `<backbone>_s<seed>` (E1),
  `<backbone>_e2j_s<seed>` (E2-joint), `<backbone>_e2s_s<seed>` (E2-sequential). Git-ignored.
- `artifacts_out/llm/<model>_<k>shot/{dev,test}/` — the LLM baseline's saved replies and scores (D64,
  D65). Git-ignored (the replies quote the policies).
- `results/ner/aa_test.md`, `aa_test.json` — the headline table: every backbone and condition on the AA
  test set, intervals, paired differences, per label, per group, errors, and the LLM rows. **Committed.**
- `results/ner/<run>/test_metrics.json`, `results/ner/llm_<run>/test_metrics.json` — the per-run test
  scores behind that table. **Committed** (numbers only).
- `results/ner/test_openings.jsonl` — the log of every time the sealed test set was opened (31 entries:
  27 models + 4 LLM runs). **Committed** — it is the proof the test was not re-run.
- `results/ner/ablation.{csv,md}`, `ablation_runs.csv`, `<run>/{dev_metrics,run_meta}.json` — the
  citable NER numbers, mean +/- std over seeds. **Committed** (weights go to the Hugging Face Hub: all 27
  models are in the private repo `Karthikrishna05/consentledger-ner`, one folder per run such as
  `legalbert_e2s_s42`; checkpoints and `test_errors.tsv`, which quotes policy phrases, were left out).
- `data/aa/consent_artefacts/` — two real artefacts, the JSON Schema and a README. **Committed**;
  `synthetic/` is git-ignored (regenerable with a fixed seed).
- `data/aa/annotated/ls_import_tasks.json`, `Export*A.json` / `Export*B.json`, `gold.json` — the Label
  Studio import file and every annotation export. **Git-ignored**: each embeds the full document text.
  Shared between annotators privately.
- `results/annotation/kappa.json`, `kappa_per_doc.csv`, `relaxed.json` — agreement numbers for the latest
  run (now Export5, all 23 documents); `relaxed_round3.json`, `relaxed_round4.json` keep the two calibration
  rounds. **Committed** (numbers only, no text).
- `results/annotation/round5/` — the agreement report after the fix pass: `summary.csv` + `report.md`
  **committed**; `docs/` git-ignored.
- `results/annotation/agreement/` and `round2_calib/` — `summary.csv` + `report.md` **committed**;
  `docs/` (the actual disagreeing phrases) **git-ignored** — any report folder's `docs/` is, after one
  such folder nearly slipped into a commit.
- `results/annotation/audit/` — `corpus_audit.md` + `missed_terms.csv` **committed**; `per_doc/` ignored.
- `results/annotation/adjudication/` — `worklist.md` (counts) **committed**; `worklist/` and
  `proposed_gold/` **git-ignored**. `proposed_gold/` is a machine merge of the *failed* round-1
  annotation; it must never be mistaken for the answer key, so it is committed only once regenerated from
  the round-2 exports.
- `results/annotation/fixlist/README.md` (counts) **committed**; `P1/`, `P4/` (quote the text) ignored.
- `data/aa/annotated/gold.json` — **the answer key**: for each of the 23 documents, its text and every
  accepted highlight (start, end, label). Git-ignored (contains the text). **Final** since D59: 1,266
  highlights. It will gain a `negated` mark on some highlights once P1's check is done (D66).
- `results/annotation/adjudication/negation_check_P1.csv` — the sheet P1 fills in for the `negated` flag;
  `negated.tsv` (positions only) is made from it. Git-ignored (the sheet quotes the policies).
  `negation_check_P1.html` is the same sheet as a page to read and answer in a browser (Y / N per highlight);
  its Save button downloads `negation_check_P1_filled.csv`, which the `negation` command reads. Git-ignored.
- `results/annotation/adjudication/` (automatic adjudication, D50) —
  `decisions.tsv`: one line per disputed highlight with the code of the rule that settled it — the full audit
  trail of the gold file (plus `agreed` lines for the four agreed spans a rule overrode and `new` lines for the
  36 highlights added after the rules meeting, D55); `items.txt`, `items_repeats.txt`: the disputed highlights shown in their sentences;
  `sample_check_P1.csv`, `sample_check_P4.csv`: the sheets the annotators fill in;
  `rules_to_ratify.md`: the meeting guide; `gold_audit.md`: the three-perspective audit of the final gold with
  its 49 defects (D58). **All git-ignored** (they quote the policies).
  `auto_summary.json`: counts only — gold size, rulings by kind, rejections by rule — **committed**.
  `sample_check_result.json` appears once the sheets are scored — **committed** (numbers only).
- `data/splits/aa_split.json` — which documents are test and which are adaptation, with the groups and the
  largest text overlap across the split. Document ids only — **committed**. Written: option A (D54).
- `data/ner_bio/aa_test.conll`, `aa_adapt.conll` and their `.docmap.json` — the AA documents in the model's
  word-and-tag format, plus the document each segment came from. Git-ignored (text). Written: 559 test
  segments with 826 entities, 845 adaptation segments with 439. `aa_adapt_train.conll` (10 documents) and
  `aa_adapt_dev.conll` (4 documents) are the adaptation set divided into practice and mock test for E2.
- `data/summ/*.jsonl` — P2's summarizer data. **Git-ignored** (quotes text), except `gold_refs.jsonl`.
  `chunks_*.jsonl` and `prompts_*.jsonl`: the passages and the writing instructions; `refs_train.jsonl`:
  the 193 reference summaries (D70); `train.jsonl` (174) and `dev.jsonl` (19): the pairs the model trains
  on and is mock-tested on; `rejected_train.jsonl`: empty; `refs_test_silver.jsonl`: 93 older summaries
  of test-document passages, for optional overlap scores only — never for training.
- P2's models and the retrain pack travel by Drive and are in nobody's commits; a trained summariser
  folder holds the model, its tokenizer, `summ_meta.json` and `dev_predictions.jsonl` (D68).
- `space/` — the Hugging Face Space: `README.md` (the Space card), `requirements.txt` (CPU, run-time only),
  `build.py` (assembles `artifacts_out/space/`, refusing git-ignored files) (D84).
- `results/pipeline/<doc>.json` — one report per document from `end_to_end.py` (D79): facts with positions
  and denied marks, each passage's verdict and what is shown, the consent fields, the assembled record and its
  fingerprint, and the chain result. Git-ignored (quotes the policy).
- `src/consentledger/summ/build_dataset.py` and `summ/train.py` — the summariser's dataset builder and the
  exact training script of the final models. P2's work, handed over to P1 on 16 Oct (D77) and now committed;
  the old local rule that kept the builder out of P1's commits is gone.
- `src/consentledger/summ/faithfulness.py` — the faithfulness gate (D74); `--selfcheck` runs its tests,
  `score --data <jsonl...> --preds <dev_predictions.jsonl>` gates a predictions file. Planned as P2's file
  (P2.md §7); whether P1 commits it is P1's call.
- `results/summ/gate_label_check_P1.csv` — the 58 fresh summaries for P1 to label alone (OK / ERR / REV),
  without Claude's labels or the gate's verdicts (D74). Git-ignored (quotes the policies).
  `gate_label_check_P1.html` is the same as a reading page: one passage, laid out line by line with negation
  and exception words coloured, its two summaries in random order with the model names hidden, OK / ERR / REV
  buttons; Save downloads `gate_label_check_P1_filled.csv`. Git-ignored.
  `gate_label_check_settle_P1.html` shows only the 19 summaries P1 and Claude labelled differently, both labels
  and Claude's reason, for P1 to choose the final label; Save downloads `gate_label_settled_P1.csv` (D81). Git-ignored.
- `artifacts_out/summ/gate_eval/` — the gate's evaluation: the summaries it was tuned and tested on,
  Claude's labels (`labels_dev.json`, `labels_heldout.json`) and the scripts that score them (D74).
  Git-ignored.
- `meta-documentation/RELATED_WORK.md` — the literature-search record behind every novelty claim.

**The rule of thumb behind all of this:** anything that quotes scraped document text is never committed;
numbers-only summaries are.

---

*Maintenance: update this file whenever new code or data steps are added — it is the single place a new
teammate (or examiner) should be able to learn the whole project from.*
