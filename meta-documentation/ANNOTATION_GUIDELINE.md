# ConsentLedger — AA Annotation Guide (v3, beginner-proof)

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
5. **If a phrase is repeated, highlight every occurrence** (each time it appears).
6. **When you're unsure, don't guess silently.** Write it down (message the other annotator / add it to
   the "Tricky cases" list at the bottom). You'll settle it together.

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

## Tricky cases we've resolved (add every hard case here so future annotation stays consistent)
- (none yet — add as: *"phrase X → label Y, because …"*)
