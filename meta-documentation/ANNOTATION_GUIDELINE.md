# ConsentLedger — AA Annotation Guideline (v1)

For annotating **Account Aggregator consent documents** with **3 labels** in Label Studio. Read this
fully before annotating. Keep it open while you work. (Why 3 labels and 2 annotators: OVERVIEW.md.)

## The 3 labels (and ONLY these)

| Label | Tag what | Examples (tag the **bold** part) |
|---|---|---|
| **DATA_TYPE** | a category of financial/personal information shared | **bank account statements**, **mutual fund holdings**, **insurance policies**, **GST returns**, **salary details** |
| **PURPOSE** | why the data is collected/shared | **loan eligibility assessment**, **credit underwriting**, **personal financial management** |
| **THIRD_PARTY** | a named/identified recipient **beyond** the primary FIU | **credit bureaus**, **affiliates**, **service providers**, **analytics partners** |

## Do NOT tag (out of scope)
- **DURATION / FREQUENCY / RECIPIENT / DATA_RANGE / DATA_LIFE** — these come from the structured consent
  artefact (JSON), not from prose. Ignore "valid for 12 months", "monthly", "the FIU", named FIU, etc.
- Consent status ("granted/revoked") — that's blockchain state, not a label.
- Generic references: "your information", "the data", "you", "the FIU/requesting entity" — too vague, skip.

## Boundary rules (this is what keeps agreement high)
1. **Minimal noun phrase.** Tag "mutual fund holdings", NOT "your mutual fund holdings" (drop possessives
   and determiners like your/the/a).
2. **Lists = separate spans.** "bank deposits, mutual funds, and insurance" → **three** DATA_TYPE spans,
   not one.
3. **One label per span.** If torn between RECIPIENT and THIRD_PARTY: THIRD_PARTY = anyone *beyond* the
   FIU the consent is for. (And a *named FIU itself* is not tagged — it's a structured field.)
4. **Tag the specific phrase, not the whole sentence.** In "we use your data to assess loan eligibility",
   tag only **assess loan eligibility** (PURPOSE), not the whole clause.
5. When unsure, **note it** (don't guess silently) — ambiguous cases get discussed and added here.

## Worked examples
- "We collect your **bank statements** and **mutual fund units** to perform a **credit assessment**."
  → DATA_TYPE: "bank statements"; DATA_TYPE: "mutual fund units"; PURPOSE: "credit assessment".
- "Data may be shared with **credit bureaus** and **affiliates** for reporting."
  → THIRD_PARTY: "credit bureaus"; THIRD_PARTY: "affiliates". ("for reporting" is vague → skip.)
- "Your consent is valid for 12 months." → **nothing** (duration = structured field).
- "The FIU will use the information for loan processing." → PURPOSE: "loan processing". (FIU not tagged.)
- "We share **your location data** with **analytics providers**." → DATA_TYPE: "location data";
  THIRD_PARTY: "analytics providers".

## Workflow
1. Two annotators (P1, P4) each label the **same ~4 docs independently** (no peeking) → compute κ
   (`kappa.py`). Discuss disagreements, refine this guideline, re-check.
2. Double-annotate all **gold-test docs**; single-annotate the rest (split).
3. Adjudicate disagreements → one reconciled gold version.
4. Export Label Studio JSON (char offsets) → same span→`bio_tagging.py`→CoNLL pipeline as OPP-115.

*Living doc: add every resolved hard case below so the next annotation stays consistent.*

## Resolved edge cases (append as they come up)
- (none yet)
