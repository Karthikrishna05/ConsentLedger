# ConsentLedger — AA Annotation Guide (v7.5, beginner-proof)

> **v7.5 (2026-10-07) — rules ratified by P1 and P4 together (D55).** The two annotators met and went through
> the ten rulings the adjudication had applied. Seven were kept as they were. Three were changed, and the gold
> file was rebuilt with them: **(1) a data *source* is a THIRD_PARTY too** — an organisation your data is
> fetched *from* (a credit bureau, UIDAI, the Central KYC Registry, a registrar) also handles your data, so it
> is marked, except the AA pipeline's own bodies (Rule 16, PART I-3). **(2) Rule 10 gains row 12 — Account
> opening & onboarding.** **(3) Rule 14 is narrowed** — a list is one highlight only where a piece means
> nothing on its own; pieces that are complete stay separate highlights.

> **After the fix pass (2026-10-06):** rulings made while resolving disagreements are collected in
> **PART I — Adjudication rulings**. They do not change how the fix pass was done (that was v7.4); they
> decide the gold file. First entry: **the Lender** (D49).

> **v7.4 (2026-10-03):** the last three open questions, settled (D46). **Regulators:** authorities named
> in an explicit disclosure are THIRD_PARTY — *except* the regulators of the AA pipeline itself (`RBI`,
> `SEBI`, `IRDAI`, `PFRDA`), never marked (Rule 8b, Rule 16). **Bracketed abbreviations** are their own
> highlight — `Permanent Account Number (PAN)` is **two** highlights (Rule 12). **Status words** are dropped —
> `registered email address` -> `email address` (Rule 1).

> **v7.3 (2026-10-02):** **headings and table row labels are ordinary text** (Rule 20 and Rule 23d rewritten,
> D45). A phrase in a heading or a row label is marked when it passes every other rule — `PostHog` and
> `Service providers` as row labels of a sharing table are THIRD_PARTY; `KYC Documents` in a heading is a
> DATA_TYPE. Most headings still fail another rule (`8. Cookies` — Rule 23a; `Data Retention` — no data-use
> frame, Rule 10). **This reverses v7.2's row-label ruling: add the labels you skipped.**

> **v7.2 (2026-10-02):** rulings from round 4 (D43), for the fix pass — **Rule 23**: device/usage telemetry
> is never a DATA_TYPE; what *you* send (emails, chat messages, call recordings) is; `KYC` is a PURPOSE only
> where the text uses your data for it; a table's row label is a heading *(reversed in v7.3)*. Rule 10 gains **row 11 —
> corporate transactions** (merger, acquisition…). Decision table: `device information`, `location data`
> moved to *do not mark*.

> **v7.1 (2026-10-01):** Rule 10 check 1 corrected (D37) — a PURPOSE needs a *data-use frame*: the text
> must say the company uses or keeps **your data** for it. Your rights (raise a grievance, revoke consent,
> deregister) and complaint procedures are **not** purposes.
> **v7 (2026-09-30):** adds **Rules 11-22** — every small decision found in a full audit of all 23
> documents (D36): clean edges, abbreviations, example lists, shared-word lists, overlaps, when a
> THIRD_PARTY counts, the policy's own company, negation, headings, glued text, label consistency.
> Earlier: Rule 10 (PURPOSE list, D35), Rules 9/9b (D32), Rules 7/8/8b (D29/D30), PART G2 (D31).
> If you annotated before this version, re-read Part A. **Rules 9 and 10 decide every PURPOSE; Rules
> 16-17 decide every THIRD_PARTY.**

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
| **DATA_TYPE** | a kind of financial/personal information **you provide** (not what your device emits — Rule 23) | "we collect your **bank account statements**", "**mutual fund holdings**", "**PAN**", "**salary details**" |
| **PURPOSE** | an activity your data is used for — **only from the 11-category list in Rule 10** | "to carry out **loan eligibility assessment**", "for **credit underwriting**" |
| **THIRD_PARTY** | someone the data is shared with **beyond** the main company/FIU | "shared with **credit bureaus**", "**affiliates**", "**service providers**" |

### Do NOT highlight these (leave them alone)
- **How long / how often / which company / date ranges** ("valid for 12 months", "monthly", "HDFC Bank",
  "the FIU", "from 1 Jan to 31 Dec"). These are handled elsewhere by a program, not by you.
- **Consent status** words ("granted", "revoked", "pending").
- **Vague words** with no specific meaning: "your information", "the data", "you", "such details".

### The 6 rules that keep P1 and P4 in agreement (read carefully — this is the whole game)
1. **Highlight the shortest phrase that still makes sense.** In "your mutual fund holdings", highlight
   **mutual fund holdings** — leave out "your". Drop leading words like *your, the, a, any, all, such*.
   **Drop status words too (v7.4):** *registered, verified, valid, updated, latest* — `registered email
   address` -> **`email address`**, `valid bank account details` -> **`bank account details`**. Keep words that
   are part of a field's real name: `Permanent Account Number`, `current address`.
2. **A list = several separate highlights.** For "bank deposits, mutual funds and insurance", make
   **three** DATA_TYPE highlights: "bank deposits", "mutual funds", "insurance" — not one big highlight.
   *Exception: if the items share a word written only once ("credit/debit card details"), it is ONE
   highlight — see Rule 14.*
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

### ⚠ Rules 7, 8, 8b, 9, 9b, 10 — added after the failed rounds. READ THESE TWICE.

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
a real organisation?"** *(It is a test against vague umbrella words, not a financial-only filter:
`email address` and `call recordings` pass. Where data comes from is settled by Rule 23.)*
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
| Generic people & groups *(added v7)* | `stakeholders`, `persons`, `any person`, `entities`, `others`, `third-party entities` |

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
| `SEBI`, `IRDAI`, `PFRDA` *(v7.4)* | the other financial-sector regulators of the AA framework — part of the pipeline, like RBI. Never marked, **even in a disclosure list** |
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

#### Rule 9 — PURPOSE: maximum 5 words. Count them.

Round-2 calibration **failed** (kappa 0.374, *worse* than the 0.492 it replaced) and the reason was
measured precisely: **PURPOSE entity-F1 was exactly 0.000** — not one purpose span matched between the
two annotators. Not because they disagreed about *what* the purposes were, but about **how much text to
highlight**:

| PURPOSE span length | P1 | P4 |
|---|---|---|
| `26_zerodha_tos` | median **3.0** words | median **10.0** words (longest 16) |
| `17_pb_fintech_aa_privacy` | median **3.0** words | median **8.0** words (longest 12) |

A 3-word span and a 10-word span describing the same idea **can never match**. That is the whole of the
zero. Rules 7, 8 and 8b were countable rules and they worked — DATA_TYPE has now converged at a median of
2 words for both annotators. Rule 1 ("the shortest phrase that still makes sense") is a *judgement* rule,
and two careful people read it differently. So PURPOSE now gets a countable rule too.

**THE RULE: a PURPOSE highlight is AT MOST 5 WORDS — the action and its object, nothing else.**

Three steps, in order:
1. **Drop the leading `to` / `for` / `for the purpose of`.** They are never part of the purpose.
2. **Stop at the object.** Delete every trailing clause that says *where, with whom, through what, or
   under which circumstances* — anything starting `with…`, `within…`, `through…`, `of the…`, `during…`,
   `received from…`, `on the … request`.
3. **Count the words. More than 5? You are highlighting a sentence — cut it down.**

**Worked examples, taken from real round-2 annotations:**

| What was marked (too long) | What to mark |
|---|---|
| `to raise a grievance with the grievance resolution officer of the FIU` | **do not mark at all** — a right *you* have, not a use of your data (Rule 10, check 1). Shortening does not make it a purpose. |
| `For exploring additional use cases within the Account Aggregator framework` | **`exploring additional use cases`** |
| `calculate the percentage of users accessing a specific feature of the Services` | **`calculate the percentage of users`** |
| `Verifying income details during account opening or segment activation processes` | **`Verifying income details`** |
| `or transfer of data on the client's own request from FIPs to clients through the AA` | **`transfer of data`** |
| `to independently verify any information request received from an AA` | **`verify information request`** |
| `to fulfil the purpose` | **do not mark** — vague, says nothing |
| `for the express purpose mentioned in the consent artefact` | **do not mark** — vague, says nothing |

> **Sanity check before you highlight a PURPOSE:** read your span aloud on its own. If it still sounds
> like a *sentence fragment from a contract* rather than a *name for an activity*, it is too long.
> "verifying income details" names an activity. "verifying income details during account opening or
> segment activation processes" is a contract clause.

#### Rule 9b — `data` and `information` with a modifier are still umbrella terms

Rule 8 already bans bare `data` and `information`. Round 2 showed the same umbrella sneaking back in
wearing a modifier: `client data`, `data received from a Financial Information Provider`,
`data collected from an FIP`, `data in an aggregated and anonymised form`, `related information`.

**The rule: if the head noun is `data` or `information`, only mark it when the modifier names a specific
financial item.**

- ✅ **mark:** `credit information`, `transaction data`, `account information` — the modifier names a real
  category you could find in a record.
- ❌ **do not mark:** `client data`, `data received from an FIP`, `such information`,
  `data in an aggregated and anonymised form` — the modifier describes *whose* it is, *where it came
  from*, or *what state it is in*. That is not a kind of data.

*Quick test: strip the modifier. If what is left is just "data" or "information" and the modifier told you
nothing about the CONTENT, do not mark it.*

#### Rule 10 — PURPOSE comes from a FIXED LIST of 12 categories. Anything else is not a PURPOSE.

Round-2 calibration scored **PURPOSE F1 = 0.000**, and Rule 9 (word count) was not the whole story. The
two annotators found purposes **in different parts of the same document** — in `17_pb_fintech_aa_privacy`
one found ten purposes at character positions 6,671-9,581, the other found four at 222-1,984, and they
shared exactly one. Even with relaxed matching, PURPOSE only reached **F1 0.138**, and deleting every vague
span made it **worse** (0.087). The problem was not vague spans; it was that "the reason data is used"
has no edge, so in a 5,000-word policy two careful people pick different sentences.

The fix is the same as every rule that worked: give a **finite list to find**, not an open idea to judge.

**THE RULE: mark a PURPOSE span only if it names an activity that belongs to one of these 12 categories.**
Same PURPOSE button as before — this changes the *definition*, not the labels.

| # | Category | Mark phrases like |
|---|---|---|
| 1 | **Credit / loan assessment** | `loan eligibility assessment`, `credit underwriting`, `verifying income details`, `processing loan application` |
| 2 | **Account monitoring & collection** | `monitor accounts`, `loan collection`, `track overdue payments` |
| 3 | **Financial management & insights** | `wealth management`, `budgeting`, `spending analysis` |
| 4 | **Fetching, consolidating & sharing financial information** (the AA service itself) | `retrieve and share financial information`, `consolidate accounts`, `aggregated statement`, `Account Aggregation services` |
| 5 | **Fraud prevention, security & verification** | `fraud prevention`, `verification of identity`, `KYC checks`, `AML checks`, `fraud detection and prevention` |
| 6 | **Legal & regulatory compliance** | `comply with applicable law`, `respond to authorities`, `prosecution of offences` |
| 7 | **Customer support, complaints & disputes** — *only where the text says your data is used or kept for it* | `respond to queries`, `resolve problems`, `addressing grievances`, `dispute resolution` |
| 8 | **Communication** | `send you notices`, `offer alerts`, `send notifications` |
| 9 | **Analytics & service improvement** | `calculate the percentage of users`, `improve our services`, `exploring additional use cases` |
| 10 | **Marketing & promotion** | `marketing`, `promotional offers`, `cross-selling products` |
| 11 | **Corporate transactions** *(v7.2, D43)* — *only where your data is transferred or shared because of it* | `merger`, `acquisition`, `reorganization`, `sale of assets`, `sale of business` |
| 12 | **Account opening & onboarding** *(v7.5, D55)* — *only where the text says your data is used for it* | `register you as a user`, `registration as a user`, `customer onboarding`, `onboarding` |

*Row 12 was added after annotation, at the P1+P4 meeting: both annotators had marked onboarding purposes that
no row covered. It follows check 1 like every row — "we use your information **to register you as a user**"
✅; "information you gave **at the time of registration**" ❌ (that is a moment, not a reason); "you must
register to use the Website" ❌ (your duty, no data-use frame). A **job application** is not row 12.*

**Four checks, in order, before you press PURPOSE:**
1. **Does the text say the company uses, keeps or shares YOUR DATA for it?** *(corrected in v7.1, D37)*
   A PURPOSE is a **reason for processing your data**, so it needs a *data-use frame* — in its own sentence,
   or in the lead-in of the list it sits in:
   *"we use your information **for**…"*, *"may be used **for**…"*, *"retained **for**…"*, *"processed on the
   following grounds…"*, *"for purposes including…"*, a list headed *"How we use your information"*.
   Three things fail this check even though they sound like purposes:
   - **a goal or state:** `maintaining your privacy`
   - **something YOU do — your rights:** `raise a grievance`, `file a complaint`, `revoke consent`,
     `deregister from any AA`, `access a record of your consents`
   - **a procedure, commitment, contract clause or heading:** *"a Grievance Redressal Policy… for handling
     complaints"*, *"dispute resolution provisions shall survive termination"*, the heading `Grievance Redressal`
   **The words never decide — the sentence does.** `dispute resolution` is a PURPOSE in *"we may maintain
   records… for purposes including fraud prevention, dispute resolution"*, and is **not** one in *"dispute
   resolution provisions shall survive termination"*. This is the PURPOSE twin of Rule 16 (THIRD_PARTY needs
   a data flow).
2. **Does it fit one of the 12 rows above?** If you cannot name the row number, **do not mark it**.
3. **Would it read the same in ANY company's policy?** Then it names nothing. **Do not mark it.**
   `to fulfil the purpose`, `for the purposes stated herein`, `for lawful purposes` → **do not mark**.
4. **Cut it to at most 5 words** (Rule 9): drop `to`/`for`/`purpose of`, stop at the object.
   `purpose of verification of identity` → **`verification of identity`** (row 5).

**Worked examples, taken from the real round-2 annotations:**

| What was marked | Verdict |
|---|---|
| `Respond to queries` | ✅ row 7 |
| `send you notices` | ✅ row 8 |
| `calculate the percentage of users` | ✅ row 9 |
| `Verifying income details` | ✅ row 1 |
| `Fraud detection and prevention` | ✅ row 5 — one highlight: the items share "fraud" (Rule 14) |
| `Addressing grievances and disputes` (in a list of purposes for using your information) | ✅ row 7 — the list says your data is used for it |
| `dispute resolution` in *"maintain records… for purposes including… dispute resolution"* | ✅ row 7 |
| `to raise a grievance with the grievance resolution officer of the FIU` | ❌ a right you have, not a use of your data (check 1) |
| `handling complaints and grievances` in *"a Grievance Redressal Policy that sets processes… for handling complaints"* | ❌ a procedure; no data use (check 1) |
| `revoke consent` in *"the customer may revoke consent"* | ❌ a right (check 1) |
| `Account Aggregation services` | ✅ row 4 — it names the specific AA service (bare `services` is still banned by Rule 8) |
| `maintaining your privacy` | ❌ a goal, not an activity (check 1) |
| `to deregister from any AA` | ❌ a user right (check 1) |
| `to fulfil the purpose` | ❌ fits any policy (check 3) |
| `contracted third parties` | ❌ not an activity at all — if anything it is a THIRD_PARTY |

> **Why this list and not the five official ReBIT purpose codes?** The ReBIT codes (101-105) describe why
> an FIU pulls financial data — they have no slot for fraud checks, grievances, notices or marketing,
> which policies really do describe. The 12 rows cover what AA policies actually say. The comparison with
> the declared ReBIT code happens later, in analysis: rows 1-4 correspond to the codes; a policy whose text
> leans on rows 9-11 while declaring a narrow code is exactly the mismatch the project wants to flag.
> **Annotators never need to think about codes** — only about the row.

---

### Rules 11–22 — the small decisions (from the full 23-document audit, D36)

After Rule 10, every span both annotators made in all 23 documents (P1: 1,761, P4: 933) was checked
against every small decision an annotator faces. Each rule below exists because the guideline was
**silent** on a decision the annotators actually had to make — the numbers in *italics* are how often
it came up. Most take one second to apply.

#### Rule 11 — Clean edges: a highlight starts and ends on a letter or digit

No space, comma, full stop, quote mark or bracket at either end.
`'banks '` → **`banks`** · `'chat messages,'` → **`chat messages`** · `'"FIPs"'` → (Rule 8b: not marked at all)
*Round 1: P1 14 spans, P4 41 spans had a space or punctuation at an edge. Every one is an automatic
exact-match miss even when both people meant the same words.*

#### Rule 12 — Abbreviations: the name and the bracket are TWO highlights

When a name is followed by its abbreviation or expansion in brackets or quotes, make **two separate
highlights with the same label** — the name as first written, and the abbreviation **inside** the bracket.
Never one highlight that swallows the brackets or quote marks (Rule 11).
- `Permanent Account Number (PAN)` → **`Permanent Account Number`** + **`PAN`**
- `PAN (Permanent Account Number)` → **`PAN`** + **`Permanent Account Number`**
- `transaction authentication number "TAN"` → **`transaction authentication number`** + **`TAN`**
- `know-your-customer documents ("KYC Documents")` → **`know-your-customer documents`** + **`KYC Documents`**
- `Financial Intelligence Unit (FIU-IND)` → **`Financial Intelligence Unit`** + **`FIU-IND`**

*Why two (changed in v7.4, D46): every later standalone `PAN` is marked (Rule 7). Leaving out the one in the
bracket would teach the model that the same token is an entity everywhere except in brackets. The bracket is
just another occurrence.*
If the bracket sits **inside** the name — `CIS (Collective Investment Schemes) units` — highlight the whole
name including the bracket, as one. Abbreviations of banned terms stay banned: `PII`, `SPI` (Rule 8), `FIP`,
`FIU`, `AA`, `RBI`, `SEBI` (Rule 8b); so does a bracketed umbrella (`("Registration Information")`, Rule 9b).
*Round 1: 30 bracketed spans each, handled three different ways between the two annotators.*

#### Rule 13 — Lists of examples: mark every item, never the umbrella, never "etc."

When the text says *"… such as / including / e.g. / for example …"* followed by a list:
- **Mark every item in the list** that passes the other rules.
- **Never mark the umbrella word** that introduces the list, or its abbreviation.
  *"We collect your PII, including: a. your name, b. your mobile number"* → **`name`**, **`mobile number`**
  — not `PII`, not `Personally Identifiable Information`.
- **Never mark** `etc.`, `and more`, `and the like`, `other similar information`, `and so on`.

*Round 1: 834 of P1's spans sat inside example lists against 347 of P4's — the single largest source of
one-sided marking. P4 was stopping after the first few items.*

#### Rule 14 — Lists that share a word: one highlight

Rule 2 says a list becomes several highlights. That holds only when **each item is complete on its
own**. When the items share a word that is written only **once**, splitting would leave broken pieces —
so the whole list is **one** highlight:

| Text | Why | Highlight |
|---|---|---|
| `bank statements, mutual funds and insurance` | each item complete alone | **3** highlights (Rule 2) |
| `credit/debit card details` | "card details" is shared | **1**: `credit/debit card details` |
| `first and last name` | "name" is shared | **1**: `first and last name` |
| `identity and contact information` | two separate fields of the consent artefact *(P1's ruling, D59)* | **2**: `identity` · `contact information` |
| `fraud detection and prevention` | "fraud" is shared | **1** (PURPOSE, row 5) |
| `retrieve, view, consolidate and share financial information` | one shared object | **1** (PURPOSE, row 4) |

**Counting for Rule 9:** a shared-word list counts as **one word**. So
`retrieve, view, consolidate and share financial information` counts as 3 (`[list] financial information`)
and stays within the 5-word limit.
*Round 1: PURPOSE lists were split by P1 and lumped by P4 — 19 vs 83 coordinated PURPOSE spans.*

**Narrowed in v7.5 (D55) — merge only what cannot stand alone.** Ask of each piece: *highlighted by itself,
would it still tell a reader what data, purpose or party it is?* If **every** piece passes, make separate
highlights even though a word is shared. Merge only as far as needed to rescue a piece that fails.

| Text | Piece by piece | Highlights |
|---|---|---|
| `ACH, NEFT, IMPS and UPI ID details` | each names a payment record by itself | **4**: `ACH` · `NEFT` · `IMPS` · `UPI ID details` |
| `mutual fund and demat holdings` | both stand alone | **2**: `mutual fund` · `demat holdings` |
| `salary and income details` | both stand alone | **2**: `salary` · `income details` |
| `marketing and promotional activities` | both stand alone | **2**: `marketing` · `promotional activities` |
| `first and last name` | "first" alone says nothing | **1** |
| `Verifying your identity and eligibility` | "eligibility" alone — of what? | **1** |
| `Retrieving, viewing, consolidating, organizing, and sharing Financial Information` | bare verbs need the object | **1** |
| `loan evaluation and servicing` | "servicing" alone says nothing | **1** |
| `credit, debit card and/or internet banking account information` | "credit" alone is not "credit card" | **2**: `credit, debit card` · `internet banking account information` |

*Analogy: "tea and coffee cups" must stay whole — "tea" alone is a drink, not a cup. "Cups, plates and
bowls" is three things, even though one shelf holds them all.*

#### Rule 15 — Never overlap, never nest, never duplicate

One stretch of text carries **at most one** highlight.
- If one entity sits **inside** another, mark only the **outer (longer)** one:
  `verifying income details` → one PURPOSE; do **not** also mark `income details` inside it.
  *(The training pipeline keeps only the longest of any overlapping spans anyway — anything inside is
  silently thrown away, so marking it is wasted effort and makes agreement look worse.)*
- Never highlight the same words twice (a double-click creates an invisible duplicate).
*Round 1: P4 had 12 overlapping or duplicate highlights, P1 none.*

#### Rule 16 — THIRD_PARTY needs a data flow in the same sentence

Mark an organisation as THIRD_PARTY **only if its sentence says your data goes to it** — it is shared,
disclosed, transferred, sold, provided, made available, given access, or received by it.
Organisations named for **any other reason** are **not** marked:

| Sentence is about… | Example | Mark? |
|---|---|---|
| sharing data | "we may share your information with **credit bureaus**" | ✅ |
| indemnity / liability | "you agree to indemnify the Company and its affiliates, agents and suppliers" | ❌ |
| jurisdiction | "subject to the exclusive jurisdiction of the courts at Bengaluru" | ❌ |
| assigning the contract | "we may assign our rights to our subsidiaries or parent companies" | ❌ |
| being regulated | "we are regulated by the Reserve Bank of India" | ❌ (also Rule 8b) |

Government bodies, **law enforcement** and **courts** follow the same test: "we may disclose your
information to **law enforcement agencies**" ✅; "the courts at Bengaluru shall have jurisdiction" ❌.
**Regulators and authorities (v7.4, D46).** In an explicit disclosure — *"we may disclose information to law
enforcement, government authorities, or regulators"*, *"SEBI, RBI, the Income-tax Department, the Financial
Intelligence Unit (FIU-IND), exchanges, courts"* — mark every authority **except the AA pipeline's own
regulators** (`RBI`, `SEBI`, `IRDAI`, `PFRDA`, Rule 8b): `law enforcement`, `government authorities`,
`regulators` (the generic word), `Income-tax Department`, `Financial Intelligence Unit`, `exchanges`,
`courts` ✅; `SEBI`, `RBI` ❌.
**Sources (v7.5, D55).** A data flow counts in **either direction**. An organisation the company gets your
data *from* is marked as well: *"accessing your credit information **from** Credit Information Companies
(`TransUnion CIBIL`, `Experian`, `Equifax`, `CRIF HighMark`)"* ✅ all five; *"details obtained from `UIDAI`"* ✅;
*"information about you we get from our `business partners`"* ✅. To pull your record the company has to hand
over your name and PAN, so the "source" receives your data too. **Not marked:** the AA pipeline's own bodies
(Rule 8b) — and that includes *"the banks or other financial institutions where your account is maintained"*,
which is just the FIP described in words. A sentence with **no** exchange of your data (indemnity, definitions,
"the Lender disburses the loan") still marks nothing.
*Round 1: about 112 of P1's and 98 of P4's THIRD_PARTY spans sat in sentences with no data-flow verb
(automatic estimate — a few genuine flows use unusual verbs).*

#### Rule 17 — The company that wrote the policy is never a THIRD_PARTY

Extends Rule 3. Never highlight the policy's own company **under any of its names** — brand, product or
legal name: `Setu`, `Agya Technologies Private Limited`, `Digio Internet Private Limited`, `PennyDrop`,
`Zerodha` (each in its own policy). The same goes for **its own people**: `officers`, `directors`,
`employees`, `Support Team`, `our staff`. They are the first party.
Named **outside** companies that receive your data **are** marked, full name as written:
`PostHog`, `TransUnion CIBIL Limited`, `Experian`.
*Round 1: P4 marked the policy's own company 19 times; P1 never did.*

#### Rule 18 — Negation and "may" do not matter: mark the mention either way

Highlight the entity whether the sentence says the company **does**, **may**, or **does NOT** do it:
*"We will **never** sell your data to **advertisers**"* → **`advertisers`** is a THIRD_PARTY.
*"We do **not** use your data for **marketing**"* → **`marketing`** is a PURPOSE.
**Why:** the model is trained on OPP-115, where every practice is highlighted regardless of whether it is
affirmed or denied. Annotating the AA documents any other way would make the transfer experiment
compare two different tasks. Whether a practice actually happens is a separate question the model does
not answer. (For Rule 16, a denied flow — "do not share with X" — still counts as a sentence about data
going to X.)
*Round 1: 508 of P1's and 276 of P4's spans sat in negated sentences, with no rule to say whether that
was right.*

#### Rule 19 — A word named after data is not data

Do not mark a data word that is only the **name of something else**:
`password mining` (an attack), `KYC process` (a process), `cookie preference` (a setting),
`Financial Information User` (a role — Rule 8b), `data protection officer` (a person).
Do mark it when the sentence is **about the data itself**: `date of birth information` → **`date of birth`**.
*Test: is the sentence talking about the information, or about a thing that is named after it?*
*Round 1: 9 such spans each.*

#### Rule 20 — Headings, titles and definitions

- **Headings are ordinary text (v7.3, D45).** A phrase in a section heading, document title or table row
  label is marked exactly like the same phrase in a sentence — **if it passes every other rule**. Rule 7
  ("every occurrence") includes headings. *Why: NER marks mentions, not claims — the same reason a negated
  mention is marked (Rule 18) — and "is this a heading?" was a judgement two annotators made differently.*
  The other rules still filter most headings:
  | Heading | Mark? | Because |
  |---|---|---|
  | `3.2 KYC Documents` | ✅ DATA_TYPE | specific data |
  | `8. Cookies`, `4.5 Location Data` | ❌ | observed telemetry (Rule 23a) |
  | `11. Data Retention`, `Grievance Redressal` | ❌ | a bare heading has no data-use frame (Rule 10 check 1) |
  | `Disclosures to Third Parties`, `Personal Information We Collect` | ❌ | umbrella words (Rule 8) |
  | `3.5 Third-Party Service Providers` | only if a data flow governs it (Rule 16) — a heading over a sharing section, yes |
- **Definitions are ordinary sentences.** In *"'KYC Documents' means …"*, `KYC Documents` is a DATA_TYPE
  like anywhere else. A THIRD_PARTY in a definition still needs a data flow (Rule 16), so
  *"'Lender' means any bank or NBFC …"* marks nothing.
*Round 1: about 70 spans each sat on heading-like lines — treated three different ways; v7.3 ends that.*

#### Rule 21 — Line breaks and glued words

- A phrase broken across **two lines** (the documents are wrapped) is still **one** highlight — drag
  across the line break. Never run a highlight past the **end of a sentence**.
- If the document shows words **glued together** (`yourlogin ID`, `personalinformation`), select **only
  the letters of the entity** — in `yourlogin ID` highlight `login ID`. Do not try to fix the text.
*Round 1: 22 (P1) and 39 (P4) spans crossed a line. Glued text is concentrated in `02_digio_terms` and
`10_perfios_terms`.*

#### Rule 22 — One phrase, one label — and check the colour before you submit

- The same phrase gets the **same label in every document**. The only exception is when its role
  truly changes: *"the **communications** you send us"* is a DATA_TYPE; *"to send you **communications**"*
  is a PURPOSE (row 8).
- **Mis-click check.** Label Studio keeps the last label button active, so the next highlight silently
  gets the wrong colour. After each highlight, glance at its colour. Before **Submit**, scan the document
  once for a colour that looks wrong for its word.
*Round 1: 9 (P1) and 11 (P4) phrases carried more than one label — `email address`, `mobile number` and
`username` were each tagged THIRD_PARTY once, which can only be a mis-click.*

#### Decision table — "X data / X information / X details / X documents" (extends Rule 9b)

These came up 160 (P1) and 109 (P4) times. Strip the last word; if what is left names a **kind of
content**, mark the whole phrase:

| ✅ Mark | ❌ Do not mark |
|---|---|
| `contact information`, `contact details` | `personal details`, `personal information`, `personal data` |
| `KYC documents`, `KYC details`, `KYC data` | `sensitive personal data`, `sensitive personal information` |
| `account information`, `bank account information` | `technical data`, `usage data`, `related information` |
| `credit information`, `transaction data`, `transaction history` | `financial information`, `financial data` |
| `bank account details` | `such information`, `the data`, `client data`, `location data`, `device information` *(v7.2)* |
| `identity document`, `income details` | `data received from an FIP` |

#### Rule 23 — Round-4 rulings (v7.2, D43)

From the disagreements on `25_the_financiali_privacy`. Apply them in the fix pass, in all 23 documents.

**The line: data you PROVIDE is a DATA_TYPE; data your device EMITS is not.** *(Not "is it financial?" —
`email address` and `mobile number` are not financial either, and they are marked. The Rule 8 test is a
check for vague umbrella words, not a financial-only filter.)*

**a. Observed telemetry is never a DATA_TYPE.** Your device or browser emits it; you never hand it over.
It is also boilerplate — the same list appears in nearly every web privacy policy, so it says nothing
about *this* company (the reasoning of Rule 10 check 3, and of the cookies ruling in Rule 8b). Do not mark:
`IP address`, `device identifiers`, `browser type`, `operating system`, `referring URLs`, `pages viewed`,
`in-app actions`, `session duration`, `cookies`, `device information`, `location data`,
`device and usage data`, `telemetry`.

**b. Provided content IS a DATA_TYPE**, even when it is not financial. Communication content you hand
over to the company is marked, every item of the list (Rule 13): `emails`, `WhatsApp messages`,
`call recordings`, `video meeting recordings`, `chat messages`, `form inputs`, `survey responses`.
It is exactly what a user needs to know before consenting ("they keep your call recordings").
*Test that separates a from b: did **you** make it, or did **your phone**?*

**c. `KYC` depends on its sentence** (the Rule 10 check-1 actor test):
| Text | Mark |
|---|---|
| *"Aadhaar (last four digits, where required for **KYC**)"* — data collected for it | **`KYC`** → PURPOSE (row 5) |
| *"to complete **KYC** checks"* | **`KYC checks`** → PURPOSE |
| *"**KYC records** are retained…"* | DATA_TYPE |
| *"**KYC/AML verification providers**"* (receive data) | THIRD_PARTY |
| *"the **KYC process** takes two days"* | nothing (Rule 19 — a process named after data) |
| heading *"3.1 KYC"* | nothing (a bare heading has no data-use frame — Rule 10 check 1) |

**d. A table row label is ordinary text** *(rewritten in v7.3, D45)*. Scraped tables lose their
formatting, so a label lands on its own line above its description:
```
Your personal data may be shared with the following categories of recipients:
Service providers
— cloud infrastructure (AWS), email and messaging providers, …
Successor entities
— in connection with any merger, acquisition, restructuring or sale of business
PostHog
— for product analytics, session-level usage measurement…
```
Mark the label when it passes the other rules — here the lead-in ("shared with") is the data flow, so
`Service providers`, `Successor entities` and `PostHog` are all **THIRD_PARTY**, and so are the items under
them (`AWS`, `email and messaging providers`). A label that is an umbrella (`Partners`, Rule 8) is not
marked; `Regulators and authorities` **is** (v7.4) — and under it `Income-tax Department`, `exchanges`,
`courts`, but not `SEBI` or `RBI`.

**e. Row 11 — corporate transactions need a data-use frame**, like every PURPOSE:
- ✅ *"may transfer … your Information in connection with a **merger**, **acquisition**, **reorganization**
  or **sale of assets**"* → four highlights (Rule 2: each item complete).
- ✅ *"Successor entities — in connection with any **merger**, **acquisition**, **restructuring** or
  **sale of business**"* — the table says your data is shared with them.
- ❌ *"We may assign or transfer our **rights and obligations** … in connection with a merger"* — a
  contract, not your data (same as Rule 16's assignment row).
- ❌ loan `restructuring` requests, `insolvency` declarations, `customer acquisition` — not corporate
  transactions at all.

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

Generate the lists from the **latest** exports (v7.2: `Export4A/B.json`). Open your file for a document. It
starts with a line like *"33 mechanical fixes (no judgement needed) + 5 to shorten + 24 to check in context
+ 37 to re-read."* Do the buckets **in this order**:

**Mechanical — just do them (exact positions given):**
1. **1 DELETE** — stoplist, AA roles **including named AAs** (`Onemoney`, `Finvu`, `CAMS Finserv`…),
   umbrellas (`financial details`) and **observed telemetry** (`IP address`, `type of browser`, `IMEI`,
   `web beacons`) — Rules 8, 8b, 9b, 23a. *Grouped, e.g. "`third parties` x21" — decide once, delete all.*
2. **1b TRIM** — re-draw over the corrected words shown: edge space/punctuation (Rule 11), a bracketed
   abbreviation swallowed into the highlight (Rule 12 — it becomes its own highlight under bucket 2), a leading `your/the/any` (Rule 1), a leading `to/for` on a
   PURPOSE (Rule 9).
3. **1c OVERLAP** — keep the outer highlight (Rule 15). **1d OWN_COMPANY** — delete (Rule 17).
4. **1f RELABEL** — you give this phrase another colour everywhere else: fix the mis-click (Rule 22).
5. **2 ADD (repeats)** — you marked this phrase elsewhere in this document; add the skipped occurrences
   (Rule 7). Only copied from your spans that no rule doubts.
6. **4b / 4c** — shorten PURPOSE to 5 words (Rule 9); delete umbrella `X data/information` (Rule 9b).

**Check in context — read the quoted sentence, then decide:**
7. **1e THIRD_PARTY** — keep only if your data goes **to** them: delete when the sentence is indemnity,
   jurisdiction or assignment, when your data comes **from** them (`from registrars (CAMS, KFintech)`) *(the fix pass was done this way;
   reversed in v7.5 — sources are marked now, and the gold file was corrected for it)*, or
   when the name is part of a law's title (`SEBI (Investment Advisers) Regulations`) — Rules 16, 19.
8. **Headings and table row labels** need no bucket (v7.3): they are ordinary text, so the repeat and
   missed-phrase buckets now propose them too. *If you skipped row labels under v7.2, add them.*
9. **3 ADD (missed)** — phrases both of you endorse elsewhere. **Not automatic**: add only if used in the
   same sense (`title` in "rights, title and interest" is not data).
10. **3b ADD (Rule 23)** — communication content you send, or `KYC` as a purpose: add where the sentence
    fits (not "we send you emails"; not "arbitration correspondence").
11. **4d PURPOSE** — grievance/dispute/KYC/merger words: keep only with a data-use frame (Rule 10 check 1).
12. **4e LIST** — you and the other annotator cut a list differently: complete items → separate (Rule 2);
    items sharing a word written once → one highlight (Rule 14).

**Quick reads:**
13. **4 SHORTEN** — the other annotator used a shorter version of your span; Rule 1 prefers the shorter.
14. **5 RE-READ** — phrases only you ever mark. Test: a *specific* kind of data **you provide**, a Rule-10
    activity, or a real organisation your data goes **to**? If no, delete it.

**What no list can catch:** an entity neither rule nor lexicon points to — e.g. a recipient you simply
did not see (`Amazon Web Services` in "hosted on providers (primarily Amazon Web Services)"). Those surface
at adjudication, where the other annotator's highlights are compared. So read each document once more,
end to end, after the lists are done.

> ⚠ **The one place this can go wrong.** The self-check list is long, and it is tempting to mass-delete
> everything in it. **Do not.** You would swing the corpus from over-marking to under-marking, which is
> just as damaging. Real entities live in that list — `login id`, `private keys`, `fraud prevention`
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

## PART I — Adjudication rulings (made after the fix pass; they decide the gold file)

The fix pass was done under v7.4 and that is not reopened. These rulings were made afterwards, when the two
exports were compared, and are applied to every disputed span during adjudication.

### I-1. The Lender is a THIRD_PARTY — where your data goes to it (D49)

In a lending platform's documents (`24_credbuddha_terms`, `08_pennydrop_terms`) the **Lender** is a separate
company from the one that wrote the policy, and it receives your data to decide on the loan. So `Lender`,
`Lenders`, `lending partner(s)`, `partner institution(s)` and `Regulated Entity` in that sense are
**THIRD_PARTY** — not the policy's own company (Rule 17), not an AA-framework role word (Rule 8b), and
Rule 8 already names "lending partners" as a real recipient.

**But Rule 16 still decides each occurrence:** mark it only where the sentence says **your data** goes to
the lender — shared, submitted, accessed, used to assess you — affirmed or denied (Rule 18).

| Sentence | Your data to the lender? | Mark? |
|---|---|---|
| "authorises CREDBUDDHA to … submit … information to **partner institutions** for evaluation of eligibility" | yes | ✅ |
| "The Company and the **Lender** are prohibited from accessing the Customer's phone contacts" | a denied practice | ✅ |
| "transfer of the sanctioned Loan amount by the **Lender**" | no — that is money | ❌ |
| "the **Lender** shall provide the Key Fact Statement to the User" | no — a document coming to you | ❌ |
| "The **Lender** may initiate legal proceedings for recovery" | no | ❌ |
| "a NACH mandate in favour of the **Lender**" | no | ❌ |
| "'**Lender**' means any bank or NBFC…" (definition) | no | ❌ |

*Why the limit: it is the rule that already removes `affiliates` from an indemnity clause. Mark the lender
at every mention and THIRD_PARTY stops meaning "who receives your data" and starts meaning "any organisation
named". Careful with the verbs: in loan documents "transfer" and "provide" usually move **money** or
**paperwork**, not your data.*

### I-2. A DATA_TYPE needs a data practice in its sentence (D47, applied in D50)

Mark a data word only where its sentence says the company **collects, receives, asks for, uses, stores,
accesses or shares** it — affirmed or denied (Rule 18). This is the DATA_TYPE twin of Rule 16 and Rule 10
check 1.

| Sentence | Mark? |
|---|---|
| "setting up a **username** and **password** to create the Profile" | ✅ you provide it |
| "It shall not request, access or store your **login credentials**" | ✅ a denied practice |
| "You are solely responsible for the confidentiality of your username and password" | ❌ your duty |
| "password mining", "hacking" | ❌ an attack (Rule 19) |
| "You possess a valid bank account… You are not insolvent" | ❌ an eligibility condition |
| "shall not discriminate on the basis of age, religion, caste" | ❌ no data is collected |

### I-3. Conventions used when the gold file was built (D50)

- **Sources are THIRD_PARTY too** *(changed at the P1+P4 meeting, D55 — the first build did the opposite)*.
  "accessing your credit information *from* Credit Information Companies (TransUnion CIBIL, Experian…)" marks
  the bureaus, exactly as "the Default shall be reported *to* Credit Information Companies" does. Same for
  UIDAI, the Central KYC Registry, registrars named as a direct source (`CDSL`, `NSDL`, `MF Central`, `CAMS`,
  `KFintech`), `business partners`, `verification agencies`. Not marked: AA-pipeline bodies (Rule 8b), and a
  company that never exchanges data with the policy's company ("CAS emails *sent by* registrars" that the app
  reads from your own mailbox). Where one member of such a list was marked, **every** member is — the gold
  file adds the ones nobody drew (listed in `decisions.tsv` as `new`).
- **Registration and onboarding are PURPOSE row 12** *(added at the meeting, D55)* where the sentence uses
  your data for it. Job applications are still not on the list.
- **`Account Aggregation Services` is a PURPOSE** only where the sentence describes handling your financial
  information — not in a company's name, a licence statement or "you may avail of the Services".
- **Consent-artefact field lists:** the *user's* `identity` and `contact information` are marked, as **two**
  highlights (D59); the identity of the recipients or of the Account Aggregator is not, and neither is the
  signature / digital signature (the act of consenting, D59).
- **Communication topics:** only notification-type items are PURPOSE row 8 (`repayment reminders`,
  `service-related updates`, `alerts`); a subject such as `loan application status` is not an activity.
- **Shared-word lists are one highlight only where a piece means nothing alone** *(narrowed at the meeting,
  D55 — see Rule 14)*. `Retrieving, viewing, consolidating, organizing, and sharing Financial Information`
  stays whole; `ACH, NEFT, IMPS and UPI ID details` is four highlights. Applied to lists the adjudication had
  merged; a list **both** annotators drew as one highlight is left as they drew it.
- **Rule 9 length:** five gold PURPOSE spans are six words because no shorter contiguous phrase names the
  activity (`generation of a one time password`, `analyse how the Application is used`, `analyse the
  effectiveness of the advertising`, `improve the quality of the Platform`).
- **Spans both annotators marked are kept** — except where a mechanical rule says otherwise: three telemetry
  spans dropped (`app usage patterns`, `number of clicks`, `device-level`) and one boundary made consistent
  with the same sentence in four other documents (`criminal proceedings`).

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
- *"login id" / "pins" / "private keys" / "user authentication credentials"* → **mark as
  DATA_TYPE**. Specific credential fields that really do appear in records. *(`signature` was on this list
  until D59 — see the audit cases below.)*
- *"grievance redressal" / "dispute resolution" / "data sharing" / "authentication"* → **mark as
  PURPOSE only where the text says your data is used or kept for it** (e.g. a "we use your information
  for…" or "retained for…" list). As a right, procedure, policy description or heading → **do not mark**
  (Rule 10, check 1 — corrected in v7.1, D37).
- *"to fulfil the purpose" / "for the express purpose mentioned in the consent artefact"* -> **do not
  mark**. Vague; says nothing about what the purpose actually is (Rule 9).
- *"client data" / "data received from an FIP" / "data in an aggregated and anonymised form"* -> **do not
  mark**. Umbrella `data` wearing a modifier that describes whose/where it is, not its content (Rule 9b).
- *"credit information" / "transaction data" / "account information"* -> **mark**. The modifier names a
  real category of content (Rule 9b).
- *"maintaining your privacy"* -> **do not mark**. A goal, not an activity (Rule 10, check 1).
- *"to deregister from any AA"* / *"raise a grievance"* / *"revoke consent"* -> **do not mark**. Your
  rights, not uses of your data (Rule 10, check 1).
- *"calculate the percentage of users"* -> **mark** as PURPOSE, row 9 (analytics) (Rule 10).
- *"Account Aggregation services"* -> **mark** as PURPOSE, row 4 — it names the AA service itself;
  bare `services` stays banned (Rules 8 and 10).
- **PURPOSE length:** count the words, max 5. `verifying income details`, NOT `verifying income details
  during account opening or segment activation processes` (Rule 9).
- *The policy's own company* (`Setu`, `Agya Technologies`, `Digio Internet Private Limited`, `PennyDrop`) and
  its `officers` / `directors` / `employees` / `Support Team` -> **do not mark** (Rule 17).
- *"courts at Bengaluru"* in a jurisdiction clause -> **do not mark**; *"disclose to law enforcement
  agencies"* -> **mark** THIRD_PARTY (Rule 16).
- *affiliates / agents / suppliers* in an **indemnity** or **assignment** clause -> **do not mark** (Rule 16).
- *"We never sell your data to advertisers"* -> **mark** `advertisers` (Rule 18: negation does not matter).
- *"Permanent Account Number (PAN)"* -> **two** highlights: `Permanent Account Number` and `PAN`; every later bare `PAN` too (Rule 12, v7.4).
- *"PII, including your name and mobile number"* -> **`name`**, **`mobile number`**; never `PII` (Rule 13).
- *`password mining`, `KYC process`, `cookie preference`* -> **do not mark** (Rule 19).
- *Glued text* `yourlogin ID` -> highlight **`login ID`** only (Rule 21).
- **Repeats:** every occurrence gets marked, always (Rule 7) — skipping repeats poisons the training labels.

Settled in round 4 (v7.2, D43-D44):
- *`IP address`, `browser type`, `pages viewed`, `session duration`, `IMEI`, `web beacons`, `device
  information`, `location data`* -> **do not mark**. Observed telemetry, not data you provide (Rule 23a).
- *`emails`, `WhatsApp messages`, `call recordings`, `chat messages`, `survey responses`* you send ->
  **mark DATA_TYPE** (Rule 23b). *"We send you emails"* -> not data (a channel).
- *"Aadhaar (… where required for **KYC**)"* -> **`KYC`** PURPOSE; *`KYC records`* DATA_TYPE; *`KYC process`*
  nothing (Rule 23c).
- *`Service providers` / `Successor entities` / `PostHog` as row labels of a sharing table* -> **mark**
  THIRD_PARTY, and the items under them too (Rule 23d, v7.3 — reverses v7.2).
- *A heading* (`3.2 KYC Documents`) -> marked like running text when it passes the other rules; `8. Cookies`,
  `Data Retention` still not (Rule 20, v7.3).
- *"transfer … your Information in connection with a **merger**, **acquisition**"* -> **mark** PURPOSE row 11;
  *"assign our rights … in a merger"* -> **do not mark** (Rule 23e).
- *Named Account Aggregators* (`Onemoney`, `Finvu`, `NESL Asset Data`, `CAMS Finserv`, `Perfios AA`) ->
  **do not mark** (Rule 8b — an AA by name is still the pipe).
- *"obtained **from** `CDSL`/`NSDL`, `MF Central`, registrars (`CAMS`, `KFintech`)"* -> **mark each** (v7.5, D55:
  a source handles your data too). *Earlier versions said do not mark.* But *"CAS emails **sent by** registrars
  (such as CAMS and KFintech)"*, read from your own Gmail -> **do not mark**: the company exchanges nothing
  with them.
- *`SEBI`, `IRDAI`, `PFRDA`* -> **never mark**, like `RBI` (Rule 8b, v7.4). Other authorities in a disclosure list (`Income-tax Department`, `courts`, `regulators`) -> **mark** (Rule 16).
- *An organisation inside a law's name* (`UIDAI (Authentication) Regulations`) -> **do not mark** (Rule 19).
- *`Financial Intelligence Unit (FIU-IND)`* -> **`Financial Intelligence Unit`** + **`FIU-IND`**, two highlights (Rule 12, v7.4).
- *`registered email address`, `valid bank account details`* -> **`email address`**, **`bank account details`** (Rule 1, v7.4).
- *The company's own contact block* — "Registered **Address**: 1201 …", "Email: hello@…", "**Contact
  Details**: Principal Officer" -> **do not mark**. That is the company's data, not yours; a word followed by
  a colon there is a field label.
- *`mutual fund and demat holdings`* -> **two** highlights (v7.5, D55: each piece stands alone; earlier
  versions said one); *`audit and grievance redressal`* -> **two** (each complete, Rule 2).

- **From the sample check (D57), both annotators' sheets in:**
  - *"the service of **retrieving or collecting such financial information**"* -> one PURPOSE **with its
    object** (row 4). `retrieving or collecting` alone does not say what.
  - *"withdrawal of consent may affect the ability of … the Lender … to process applications, verify
    information or assess eligibility"* -> **mark nothing**. The sentence is about the effect of withdrawing
    consent; it describes no use or sharing of your data.
  - *`recommendations`, `ongoing advice`* -> **do not mark** (fit none of the 12 rows); *`portfolio
    reviews`*, *`prepare your financial plan`* -> PURPOSE row 3.
  - *`Gmail`* in "read-only access to your **Gmail** mailbox", "human reading of your **Gmail** data" ->
    **DATA_TYPE**: it means your emails. *`Gmail OAuth`* -> do not mark (a sign-in method, Rule 19).
  - *"We use **third-party advertising companies** to serve advertisements"* -> **do not mark**: the sentence
    states no flow of your data to them (Rule 16).

- **From the audit of the finished gold (D58, D59):**
  - *"…and **your signature/digital signature**"* in the consent-artefact field list -> **do not mark**. It is
    the act of accepting the consent, not data you provide.
  - *"your **identity** and (optional) **contact information**"* in the same list -> **two** highlights. But
    *"the identity of the recipients"*, *"identity and signature of the account aggregator"* -> do not mark.
  - *"indemnify … and hold us, our parent company, subsidiaries, affiliates, … agents"* -> **mark nothing**,
    even if you both would: an indemnity moves no data (Rule 16).
  - *"all right, **title** and interest"* -> do not mark (a legal term). *"gender, **title**, passwords"* -> mark.
  - *"shall not discriminate … on the basis of **gender**, age, religion"* -> do not mark; nothing is collected.
  - *"X Limited, its **affiliates** and **group companies** (hereinafter 'X', 'us')"* -> do not mark: that
    sentence defines the policy's own company (Rule 17).
  - *"entitled to **opt out** from receiving marketing communication"* -> do not mark (your right). *"marketing
    communication You receive from third parties with whom We share Your information"* -> mark.
  - *`biometric data`* -> DATA_TYPE wherever a practice is stated or denied ("We do not store any biometric
    data"). *"phone **contacts**, gallery, or social media"* -> mark `contacts` and `gallery`.
  - **The same sentence in two companies' documents gets the same highlights.** Thirteen of our documents share
    a template; check the twin before deciding.

Add new cases below as: *"phrase X → label Y (or do not mark), because …"*
