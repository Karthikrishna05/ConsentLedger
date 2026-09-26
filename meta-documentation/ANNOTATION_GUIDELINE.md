# ConsentLedger — AA Annotation Guide (v4, beginner-proof)

> **v4 (2026-09-26):** adds **Rules 7, 8 and 8b** after round-1 double-annotation scored kappa 0.28, plus **PART G2** (round-2 personal fix lists, D31).
> If you annotated before this version, re-read Part A — the two new rules are the whole fix.

This guide assumes **zero prior experience**. If you can use a mouse and copy-paste a command, you can do
this. Follow it top to bottom. Two people do this independently: **P1** and **P4**.

**What you are doing, in one line:** reading 23 short financial-consent documents and, with your mouse,
highlighting three kinds of phrases (what data, why, and who-else-gets-it). A tool called **Label
Studio** records exactly which words you highlighted. Later a script checks that P1 and P4 highlighted
things the same way.

---

## PART A — The rules (what to highlight)

### The 3 labels — highlight ONLY these

| Label | Highlight… | Real examples (highlight the **bold** words) |
|---|---|---|
| **DATA_TYPE** | a kind of financial/personal information | "we collect your **bank account statements**", "**mutual fund holdings**", "**PAN**", "**salary details**" |
| **PURPOSE** | the reason data is used/shared | "to carry out **loan eligibility assessment**", "for **credit underwriting**" |
| **THIRD_PARTY** | someone the data is shared with **beyond** the main company/FIU | "shared with **credit bureaus**", "**affiliates**", "**service providers**" |

### Do NOT highlight these (leave them alone)
- **How long / how often / which company / date ranges** ("valid for 12 months", "monthly", "HDFC Bank",
  "the FIU", "from 1 Jan to 31 Dec"). These are handled elsewhere by a program, not by you.
- **Consent status** words ("granted", "revoked", "pending").
- **Vague words** with no specific meaning: "your information", "the data", "you", "such details".

### The 6 rules that keep P1 and P4 in agreement (read carefully — this is the whole game)
1. **Highlight the shortest phrase that still makes sense.** In "your mutual fund holdings", highlight
   **mutual fund holdings** — leave out "your". Drop leading words like *your, the, a, any, all, such*.
2. **A list = several separate highlights.** For "bank deposits, mutual funds and insurance", make
   **three** DATA_TYPE highlights: "bank deposits", "mutual funds", "insurance" — not one big highlight.
3. **One label per highlight.** A phrase gets exactly one colour. If you think something is both a
   RECIPIENT and a THIRD_PARTY, remember: THIRD_PARTY = anyone *beyond* the main company the consent is
   for; and a *named main company* (the FIU) is **not** highlighted at all.
4. **Highlight the phrase, not the whole sentence.** In "we use your data to assess loan eligibility",
   highlight only **assess loan eligibility** (PURPOSE) — not the whole line.
5. **If a phrase is repeated, highlight EVERY occurrence** (each time it appears) — see Rule 7, this is
   not optional.
6. **When you're unsure, don't guess silently.** Write it down (message the other annotator / add it to
   the "Tricky cases" list at the bottom). You'll settle it together.

---

### ⚠ Rules 7 and 8 — added after round 1 (κ = 0.28). READ THESE TWICE.

The first full double-annotation of all 23 docs scored **κ = 0.28** against a 0.6 gate. The diagnosis was
clear: you agreed on *which label* (only 7 label conflicts in 23 docs) and mostly on *where spans start
and end* (108 boundary conflicts) — but you disagreed **1,973 times on whether to mark something at all**.
These two rules exist to fix exactly that. (Full analysis: `results/annotation/agreement/report.md`.)

#### Rule 7 — Mark EVERY occurrence. Always. No exceptions.

Round 1: in one document A marked *"third parties"* 21 times and *"cookies"* 13 times; B marked each
phrase **once** and never repeated it. That single difference produced hundreds of disagreements.

**The rule: if a phrase qualifies, highlight it every single time it appears in the document** — 1st, 5th,
20th occurrence, all of them.

**Why this is not busywork:** the model is trained token-by-token. Every occurrence you *don't* mark is
labelled "not an entity" in the training data. So skipping repeats doesn't just lose data — it actively
teaches the model that those words are **not** entities, contradicting the occurrences you did mark. One
skipped repeat is worse than one missed entity.

*(Tip: Label Studio has no reliable "mark all" button — scroll and mark them. If a phrase appears more
than ~20 times, note it in Tricky cases rather than silently stopping.)*

#### Rule 8 — The specificity test, and the stoplist

Round 1: even ignoring repeats, one of you marked 322 distinct phrases in a document where the other
marked 50 — and in a *different* document the ratio flipped. You were reading the same text with very
different thresholds. This rule sets one threshold.

**The test — before highlighting anything, ask: "could I point to this in an actual bank record, or name
a real organisation?"**
- "bank statements", "mutual fund holdings", "PAN", "salary details" → **yes** → mark as DATA_TYPE.
- "credit bureaus", "affiliates", "ICICI HFC group companies" → **yes, a real kind of organisation** → THIRD_PARTY.
- "loan eligibility assessment", "credit underwriting" → **yes, a nameable activity** → PURPOSE.
- "information", "the data", "third parties", "services" → **no** → do not mark.

**The STOPLIST — never highlight these, under any label, however often they appear:**

| Category | Never mark |
|---|---|
| Umbrella data words | `information`, `data`, `personal data`, `personal information`, `financial information`, `sensitive information`, `your details`, `such details`, `the information` |
| Generic recipients | `third parties`, `third party`, `other parties`, `partners` *(mark the **named** recipient instead: "credit bureaus", "lending partners", "group companies")* |
| Generic service words | `services`, `the services`, `our services`, `the platform` |
| Vague purposes | `business purposes`, `lawful purposes`, `other purposes`, `related purposes`, `as required`, `reporting` |

> **The key one:** *"third parties"* is the **category name**, not a recipient. Marking it is like tagging
> the word "fruit" instead of "apple". Mark who they actually are, when the document says.

#### Rule 8b — AA-framework roles and regulators are NEVER THIRD_PARTY

The round-1 audit found one annotator systematically tagging the **machinery of the AA system itself** as
a third party: `Reserve Bank of India`, `RBI`, `Financial Information User` / `FIU`,
`Financial Information Provider` / `FIP`, `Account Aggregator` / `AA`, `Sahamati`. That is ~40 spans of
pure disagreement, and it is wrong.

**Never highlight any of these:**

| Never mark | Why |
|---|---|
| `Account Aggregator`, `AA` | the regulated **pipe** the data travels through — data is not "shared with" it |
| `Financial Information Provider`, `FIP` | the bank **holding** your data — the source, not a recipient |
| `Financial Information User`, `FIU` | the **main company** the consent is for (Rule 3 already says don't mark it) |
| `Reserve Bank of India`, `RBI` | the **regulator**. Supervising is not receiving your data |
| `Sahamati` | the **industry body**, not a data recipient |
| `consent artefact`, `consent manager` | names of **mechanisms**, not data types |

**THIRD_PARTY means: somebody your data is passed ON to, beyond the main company.** Credit bureaus,
affiliates, group companies, service providers, lending partners, credit information companies — those
are real recipients. The framework's own plumbing is not.

*Quick test: "does my data end up in their hands as a result of this consent?" RBI supervises the system
but does not receive your bank statements. The AA moves the data but is forbidden from reading it.*

**Default rulings on the round-1 borderline cases** (use these unless the team agrees otherwise):
- `cookies`, `pixels`, `device identifiers` → **do NOT mark.** They are collection *mechanisms*, not
  financial/personal data types in the AA sense.
- `address`, `mobile number`, `email` → **DO mark** (DATA_TYPE) — specific, appear as real record fields.
- `usage data`, `profile` → **do NOT mark** — umbrella terms.
- `fraud prevention`, `AML/CFT checks`, `credit assessment` → **DO mark** (PURPOSE) — nameable activities.
- `provision of the services` → **do NOT mark** — a generic service word wearing a purpose costume.

**If you are still torn:** do not mark it, and add it to Tricky cases. Under-marking a genuinely
ambiguous phrase costs one entity; over-marking a vague one pollutes every document it appears in.

### Worked examples (exactly what to do)
- Sentence: *"We collect your bank statements and mutual fund units to perform a credit assessment."*
  → highlight **bank statements** (DATA_TYPE), **mutual fund units** (DATA_TYPE), **credit assessment**
  (PURPOSE). Leave "We collect your", "and", "to perform a".
- Sentence: *"Your data may be shared with credit bureaus and our affiliates for reporting."*
  → **credit bureaus** (THIRD_PARTY), **affiliates** (THIRD_PARTY). "for reporting" is vague → skip.
- Sentence: *"This consent is valid for 12 months."* → highlight **nothing**.
- Sentence: *"The FIU uses the information for loan processing."* → **loan processing** (PURPOSE). Do not
  highlight "The FIU".

---

## PART B — One-time setup (each annotator does this on their own laptop)

You need: a Windows laptop, Python 3.11 installed, and the file **`ls_import_tasks.json`** (P1 sends this
to P4 — see PART C). Label Studio runs *entirely on your own laptop*; nothing is uploaded anywhere.

**Step B1 — Open a terminal.** Press `Windows key`, type **PowerShell**, press Enter.

**Step B2 — Make a folder for the tool and create a clean environment.** Copy-paste these one at a time:
```powershell
mkdir C:\Users\%USERNAME%\labelstudio ; cd C:\Users\%USERNAME%\labelstudio
```
```powershell
py -3.11 -m venv .ls-env
```
```powershell
.ls-env\Scripts\Activate.ps1
```
Your prompt should now start with `(.ls-env)`. (If it says running scripts is disabled, run
`Set-ExecutionPolicy -Scope Process RemoteSigned` and press `Y`, then repeat the activate line.)

**Step B3 — Install Label Studio** (downloads once, takes a few minutes):
```powershell
pip install label-studio
```

**Step B4 — Start it:**
```powershell
label-studio start
```
Your web browser opens at **http://localhost:8080**. (If it doesn't open, type that address into Chrome.)
Leave this PowerShell window **open** the whole time you annotate — closing it stops the tool.

**Step B5 — Create a local account.** On the page, click **Sign Up**, enter any email + password (these
are stored only on your laptop), and log in.

---

## PART C — Getting the documents (do this once, together)

**All annotators must load the EXACT SAME file**, or the agreement check won't work.

- **P1** already has `ls_import_tasks.json` (in `data/aa/annotated/`). **P1 sends this one file to P4**
  via Google Drive / Slack / email / WhatsApp / USB. (Do **not** re-generate it separately — you both
  need the identical file.)
- Save it somewhere easy to find, e.g. your Desktop.

---

## PART D — Create the project and load the documents (in Label Studio)

**Step D1 — Create a project.** Click the blue **Create Project** button. Give it a name, e.g.
`ConsentLedger AA`. Click **Save**.

**Step D2 — Set up the labels.** Inside the project, go to **Settings** (top-right) → **Labeling
Interface** → click **Code** (or "Browse Templates" → "Custom"). Delete whatever is in the box, paste
**exactly** this, and click **Save**:
```xml
<View>
  <Labels name="label" toName="text">
    <Label value="DATA_TYPE" background="#FFA39E"/>
    <Label value="PURPOSE" background="#B7EB8F"/>
    <Label value="THIRD_PARTY" background="#91D5FF"/>
  </Labels>
  <Text name="text" value="$text"/>
</View>
```
You should now see three coloured label buttons: DATA_TYPE (red), PURPOSE (green), THIRD_PARTY (blue).

**Step D3 — Import the documents.** Click **Import** (top-right). Drag the **`ls_import_tasks.json`** file
into the box (or click to browse and select it). It will say it found **23 tasks**. Click **Import**.
You now have 23 documents to annotate, each shown as a row.

---

## PART E — How to annotate ONE document (the core skill)

**Step E1 — Open a document.** Click the first document row → the full text appears with the three label
buttons above it.

**Step E2 — Highlight a phrase:**
1. **Click the label button** you want (e.g. **DATA_TYPE**) — it becomes active/outlined.
2. In the text, **click-and-drag your mouse** across the exact words (e.g. "bank statements").
3. Release — the words are now highlighted in that colour. That's one annotation. Done.
   *(If your version needs the other order: drag-select the words first, then click the label. Either
   works — try one; if nothing happens, try the other.)*

**Step E3 — Do it for every matching phrase** in the document, following PART A's rules. Switch the
active label button when you switch between DATA_TYPE / PURPOSE / THIRD_PARTY.

**Step E4 — Fix a mistake.** Click the highlighted phrase once → it's selected → press **Backspace** or
**Delete** (or click the trash/✕ on the little panel that appears) to remove it. To change its label,
delete it and re-highlight with the correct label.

**Step E5 — Save this document.** When the document is fully done, click the blue **Submit** button
(bottom). This saves your annotation and moves you to the next document.

**Step E6 — Repeat for each document.** Work through them one file at a time. The project view shows which
are done (they get a tick / "completed" count). **Do not look at the other annotator's work** while you
do this — you must annotate independently.

---

## PART F — The calibration check (do this FIRST, before all 23)

Do **not** annotate all 23 immediately. First do a quick agreement check on **one** document, so you
catch misunderstandings early.

**Step F1 — Agree on the pilot doc.** P1 and P4 both pick the **same single document** — use the last
one, **`29_icici_home_fin_terms`**.

**Step F2 — Both annotate ONLY that one doc** (PART E), independently, then **Submit** it.

**Step F3 — Both export your work.** Project → **Export** (top-right) → choose format **JSON** → click
**Export**. A file downloads. Rename it clearly:
- P1 saves as `exportA.json`
- P4 saves as `exportB.json`
- Put both files in the same folder (P4 sends theirs to P1).

**Step F4 — Run the agreement check.** In the **project** repo (`ConsentLedger`, with the main `.venv`
active — see the project README), run:
```powershell
python -m consentledger.data.kappa --a exportA.json --b exportB.json
```
(Use the real paths to the two files if they're not in the current folder.)

**Step F5 — Read the VERDICT line at the bottom:**
- **"PASS"** (κ ≥ 0.6) → great, your understanding matches → go to PART G and annotate the other 22.
- **"BELOW GATE"** (κ < 0.6) → do NOT re-annotate blindly. First **re-run with `--show-diff`** to see the
  exact phrases you disagreed on:
  ```powershell
  python -m consentledger.data.kappa --a exportA.json --b exportB.json --show-diff
  ```
  This prints, grouped by label, every span one of you marked and the other didn't (with the text and
  offsets). Also look at the **per-label F1 report** just above the verdict — it tells you *which label*
  is the problem (e.g. PURPOSE much lower than THIRD_PARTY), so you focus the conversation there.
  A phrase shown as **both** `A-only` and `B-only` = you both caught it but drew the edges differently
  (a boundary dispute → re-read Rule 1: shortest phrase that still makes sense). A phrase on only one side
  = you disagree on whether it's an entity at all.
  Then: sit together, decide the rule for each disputed case, write the resolution in "Tricky cases" at
  the bottom of this file, **delete and redo** the pilot doc, and run the check again. (One or two rounds
  of this is normal — a κ just under 0.6 usually clears after fixing the single worst label.)

---

## PART G — Annotate the rest, then finish

**Step G1 — Both annotate the remaining 22 documents** (PART E), independently, Submitting each.

**Step G2 — Both export again** (Project → Export → JSON), now containing all 23 docs. Save as
`exportA_full.json` / `exportB_full.json`, put together, and run the check on all 23:
```powershell
python -m consentledger.data.kappa --a exportA_full.json --b exportB_full.json
```
This κ number is the one reported in the paper.

**Step G3 — Adjudicate (produce ONE final "gold" version).** κ ≥ 0.6 means you *mostly* agree, not that
you agree on everything. So go through the disagreements the script prints and, for each, decide together
which label is correct. One of you edits their Label Studio to reflect the agreed answers, then exports a
final **`gold.json`**. *(Why: the model is later scored against one answer key, so the two versions must
be merged into one. High κ just means this is quick.)*

**Step G4 — Hand off.** Give `gold.json` back to the project (P1). The team then converts it to the
training/test format — you don't need to do that part.

---

## PART H — Common problems (FAQ)
- **"label-studio is not recognized"** → your environment isn't active. Re-run `.ls-env\Scripts\Activate.ps1`
  (prompt must show `(.ls-env)`), then `label-studio start`.
- **The browser didn't open** → go to http://localhost:8080 manually.
- **My highlight grabbed extra spaces/words** → delete it (E4) and redo more precisely. Precise
  boundaries are what keep κ high.
- **I closed PowerShell and the site died** → that's normal; just re-open PowerShell, activate the env,
  and `label-studio start` again. Your work is saved in the project.
- **The two of us got different text** → stop; you must both import the *same* `ls_import_tasks.json`.
- **Unsure about a phrase** → don't guess; note it and settle it in adjudication.

---

---

## PART G2 — Round 2: fixing your own work from your personal fix list (D31)

Round 1 scored **kappa 0.28** against a 0.6 gate. You do **not** need to re-annotate from scratch, and
you do **not** need to sit together for hours. Each of you gets a **personal fix list** telling you
exactly what to change and **where** (character positions), so you can work **alone, in parallel**.

### Step G2.1 — Generate the fix lists (P1 runs this once)

```powershell
python -m consentledger.data.fixlist --corpus data/aa/annotated/ls_import_tasks.json --a data/aa/annotated/ExportA.json --b data/aa/annotated/ExportB.json --name-a P1 --name-b P4
```

This writes `results/annotation/fixlist/P1/<doc>.md` and `results/annotation/fixlist/P4/<doc>.md`.
P1 sends P4 their folder. **Each of you only ever reads your OWN folder.**

### Step G2.2 — Calibrate FIRST on two documents (do not skip)

Before touching all 23, both of you re-do just these two under the v4 rules:
- **`26_zerodha_tos`** — short (5k characters)
- **`17_pb_fintech_aa_privacy`** — dense (15k characters)

*Why one short and one dense: the round-1 problem was density and repeats, which barely shows up in a
short document. Calibrating only on short files would give you false confidence.*

Both export, then run:
```powershell
python -m consentledger.data.kappa --a exportA.json --b exportB.json
```

**Read the number against this table — agreed in advance, so nobody argues afterwards:**

| kappa on the 2 docs | what you do |
|---|---|
| **0.75 or higher** | The rules worked. Go to G2.3 and do all 23. |
| **0.60 – 0.75** | Proceed, but re-run the check after 5 more documents before trusting it. |
| **below 0.60** | **Stop.** The rules are still not enough. Talk to the team and diagnose — do not grind through 23 documents on rules that do not work. |

### Step G2.3 — Work through your fix list, document by document

Open your file for a document. It starts with a line like
*"26 mechanical fixes (no judgement needed) + 5 to shorten + 11 to re-read."*
Do the buckets **in order** — the first three need no thinking at all:

1. **DELETE** — these spans break Rule 8 (stoplist) or Rule 8b (AA roles). Delete them.
   *The file groups them, e.g. "`third parties` x21" — decide once, delete all of them.*
2. **ADD (Rule 7 repeats)** — you already marked this phrase **in this same document** and skipped these
   occurrences. Add them. This is your own inconsistency, so there is nothing to debate.
3. **ADD (missed)** — phrases **both** of you endorse elsewhere, which appear here and you left blank.
   Add them.
4. **SHORTEN** — the other annotator used a shorter version of your span. Rule 1 prefers the shorter one.
5. **RE-READ (self-check)** — phrases that **only you** ever mark anywhere in the corpus. Apply the
   Rule 8 test to each: *"could I point to this in a real bank record, or name a real organisation?"*
   If no, delete it.

> ⚠ **The one place this can go wrong.** The self-check list is long, and it is tempting to mass-delete
> everything in it. **Do not.** You would swing the corpus from over-marking to under-marking, which is
> just as damaging. Real entities live in that list — `login id`, `private keys`, `grievance redressal`
> are all things only one annotator caught, and they are all **correct**. Judge each phrase on the test,
> not on how long the list is.

**Finding a span fast:** every item shows character offsets like `[7979:7996]`. Use your browser's find
(Ctrl+F) on the phrase shown; the offsets tell you which occurrence if the phrase appears several times.

### Step G2.4 — Re-export and measure

When you have finished all 23 documents, both export again (Project → Export → JSON), put the two files
together, and run:

```powershell
python -m consentledger.data.kappa --a exportA.json --b exportB.json
```

**This is the round-2 kappa, and it is the number reported in the paper.** If it clears 0.6, go to
PART G Step G3 (adjudicate the small residue) and produce the gold file. If it does not, run
`agreement_report.py` again — it will show which bucket is still failing.

*Why this route: fixing your own work in parallel keeps all **23 documents** (a smaller corpus leaves too
little for training and testing), takes about 3 hours each instead of a joint all-day session, and
produces two corrected exports — so a real agreement number can be measured, which a hand-merged file
could never give.*

---

## Tricky cases we've resolved (add every hard case here so future annotation stays consistent)
Settled in round 1 (kappa 0.28 post-mortem, see Rules 7 & 8):
- *"third parties"* (bare phrase) → **do not mark**. It is the category name, not a recipient; mark the
  named recipient instead ("credit bureaus", "lending partners", "group companies").
- *"cookies" / "pixels" / "device identifiers"* → **do not mark**. Collection mechanisms, not AA data types.
- *"personal data" / "financial information" / "usage data" / "profile"* → **do not mark**. Umbrella terms.
- *"services" / "the services" / "provision of the services"* → **do not mark**. Generic.
- *"address" / "mobile number" / "email"* → **mark as DATA_TYPE**. Specific, real record fields.
- *"fraud prevention" / "AML/CFT checks" / "credit assessment"* → **mark as PURPOSE**. Nameable activities.
- *"RBI" / "Reserve Bank of India"* → **do not mark**. Regulator, not a data recipient (Rule 8b).
- *"Financial Information User" / "FIU" / "Financial Information Provider" / "FIP" /
  "Account Aggregator" / "AA" / "Sahamati"* → **do not mark**. AA-framework roles, not third parties.
- *"consent artefact" / "consent manager"* → **do not mark**. Mechanism names, not data types.
- *"spi" / "pii" / "cookie" / "operating system" / "version"* → **do not mark**. Web-technical or
  abbreviation noise, not AA data types.
- *"login id" / "pins" / "private keys" / "user authentication credentials" / "signature"* → **mark as
  DATA_TYPE**. Specific credential fields that really do appear in records.
- *"grievance redressal" / "dispute resolution" / "data sharing" / "authentication"* → **mark as
  PURPOSE**. Round 1 missed these ~100 times between them.
- **Repeats:** every occurrence gets marked, always (Rule 7) — skipping repeats poisons the training labels.

Add new cases below as: *"phrase X → label Y (or do not mark), because …"*
