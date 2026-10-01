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
   - 5.7 `ls_import_export.py` + `kappa.py` (annotation tooling)
   - 5.8 `trim_spans.py`
   - 5.9 Annotation: round 1 (kappa 0.28), the rescue tools, round-2 calibration, Rules 9-22
   - 5.10 The summarizer dataset — P2's track (D33, D34)
   - 5.11 The smart contract — P3's track
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

**Exporting from Label Studio — four practical rules learned the hard way.** (1) Always export the
**whole project**: Label Studio ignores the filters you set on screen, so "export just these two
documents" is unreliable — export everything and use `kappa.py --docs <doc_ids>` to score a subset.
(2) **Only submitted work is exported**: a re-annotated document that was not clicked *Submit* (or
*Update*) stays a draft and silently keeps its old version. (3) Use **JSON**, not JSON-MIN — the full
format keeps the `doc_id` everything matches on. (4) Name each round's files distinctly:
`ExportA/B.json` (round 1), `Export2A/B.json` (round-2 calibration), `Export3A/B.json` (round 3). They
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

### 5.10 The summarizer dataset — P2's track (D33, D34)

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

**Done & verified:** environment; OPP-115 loaded (24,516 spans) and BIO-tagged; span trimming
(D25); multi-seed training + `collect.py`; **the full E1 sweep — 3 backbones x 3 seeds on OPP-115 dev**:
Legal-BERT 0.400 +/- 0.006, InLegalBERT 0.386 +/- 0.003, BERT-base 0.382 +/- 0.003 entity macro-F1, with
the ranking flipping on token-F1 — i.e. **no clear backbone winner**, as the honesty rule expects. AA corpus
scraped, cleaned (23 documents), double-annotated. Consent-artefact schema verified against the primary
source (D27); contribution claims revised after a systematic search (D28, `RELATED_WORK.md`).

**Annotation — where it stands:** round 1 kappa **0.279** (D29); corpus audit found the failure mechanical
(D30); personal fix lists replace the corpus cut (D31); round-2 calibration kappa **0.374** with PURPOSE
F1 0.000 (D32); relaxed matching showed PURPOSE failing on *where* to look, not on edges, leading to the
10-category **Rule 10** (D35); a full granular audit added **Rules 11-22** (D36); Rule 10's first check
became an actor test — your rights and procedures are not purposes (D37). **Guideline is v7.1.**
Tools: `kappa.py` (`--docs`), `agreement_report.py`, `annotation_audit.py` (`--strict`), `adjudicate.py`,
`fixlist.py` (Rule 9/9b buckets), `relaxed_agreement.py`.

**Summarizer (P2's track):** dataset builder and plan delivered to P2 via Drive (D33, D34); not in P1's
commits.

**Pending — in priority order:**
1. **Calibration round 3 (final) on `23_upmint_aa_tos`** under guideline v7 — fresh, independent, no fix
   lists open. Score with `kappa.py --docs` and `relaxed_agreement.py --docs`. Whatever the result, the
   next step is the fix pass (no round 4, D35). P4 needs the **v7.1** guideline first.
2. Fix pass on all 23 documents in parallel (regenerate fix lists first), then round-2 kappa on the full
   corpus, then adjudicate the residue -> gold.
3. Glued-text documents (`02_digio_terms`, `10_perfios_terms`): fix `clean.py`, then re-annotate or remap
   offsets for those two only — never re-clean mid-annotation (D36).
4. Convert gold to `aa_test.conll`; run **E1/E2** on the AA test set — the headline number.
5. Hand P2 the gold export for the reference-free summarizer test; P3 contract in parallel.
6. Paper: Related Work and the annotation-methodology story (0.28 -> 0.37 -> round 3, with the diagnosis
   at each step) can be written now.

See `FLOW.md` for live status and `DECISIONS.md` (D1-D40) for the reasoning behind every choice.

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
- `results/ner/ablation.{csv,md}`, `ablation_runs.csv`, `<run>/{dev_metrics,run_meta}.json` — the
  citable NER numbers, mean +/- std over seeds. **Committed** (weights go to the Hugging Face Hub).
- `data/aa/consent_artefacts/` — two real artefacts, the JSON Schema and a README. **Committed**;
  `synthetic/` is git-ignored (regenerable with a fixed seed).
- `data/aa/annotated/ls_import_tasks.json`, `Export*A.json` / `Export*B.json`, `gold.json` — the Label
  Studio import file and every annotation export. **Git-ignored**: each embeds the full document text.
  Shared between annotators privately.
- `results/annotation/kappa.json`, `kappa_per_doc.csv`, `relaxed.json` — agreement numbers.
  **Committed** (numbers only, no text).
- `results/annotation/agreement/` and `round2_calib/` — `summary.csv` + `report.md` **committed**;
  `docs/` (the actual disagreeing phrases) **git-ignored** — any report folder's `docs/` is, after one
  such folder nearly slipped into a commit.
- `results/annotation/audit/` — `corpus_audit.md` + `missed_terms.csv` **committed**; `per_doc/` ignored.
- `results/annotation/adjudication/` — `worklist.md` (counts) **committed**; `worklist/` and
  `proposed_gold/` **git-ignored**. `proposed_gold/` is a machine merge of the *failed* round-1
  annotation; it must never be mistaken for the answer key, so it is committed only once regenerated from
  the round-2 exports.
- `results/annotation/fixlist/README.md` (counts) **committed**; `P1/`, `P4/` (quote the text) ignored.
- `data/summ/*.jsonl` — P2's summarizer data. **Git-ignored** (quotes text), except `gold_refs.jsonl`.
- `src/consentledger/summ/build_dataset.py` — P2's code, kept out of P1's commits by a **local-only**
  rule in `.git/info/exclude` (it does not affect anyone else's repo, so P2 can commit their own version).
- `meta-documentation/RELATED_WORK.md` — the literature-search record behind every novelty claim.

**The rule of thumb behind all of this:** anything that quotes scraped document text is never committed;
numbers-only summaries are.

---

*Maintenance: update this file whenever new code or data steps are added — it is the single place a new
teammate (or examiner) should be able to learn the whole project from.*
