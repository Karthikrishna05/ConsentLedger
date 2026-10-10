# ConsentLedger — Plain-Language Overview

*The "explain it to me / explain it to an examiner" version. What the project is, every decision made
so far, and the label-transfer idea explained with everyday analogies.*

---

## What the project is (one line)

**ConsentLedger** reads a dense financial "consent" document (the kind you approve when an app wants to
pull your bank data under India's Account Aggregator system), **pulls out the key facts**, **rewrites
it in plain English**, and **stamps a tamper-proof record on a blockchain**.

Think of it as turning fine print into a **nutrition label + a receipt**: the label tells you what's
inside in plain terms; the receipt is proof of what you agreed to that nobody can secretly alter later.

The part we've spent the most care on is the first step: **teaching a model to pull out the key facts.**

---

## The one problem underneath everything

To "pull out key facts," you train an AI on examples — you show it many documents where a human has
already **highlighted** the important bits, and it learns to highlight new ones. This highlighting task
is called **NER** (Named Entity Recognition). Think of it as a **smart highlighter** that only
highlights certain kinds of things.

The problem: **we barely have any Indian AA documents to learn from** (~27 usable ones), and most are
**blank templates**.

> **Analogy — the blank rental agreement.** "Tenant: ______, Term: ______ months." The *structure* is
> there, but the actual values aren't filled in. Only **one** document we have (a Bajaj consent form)
> was actually filled in. Asking the model to learn "how long is consent valid" from these templates is
> like asking someone to read the tenant's name off a blank form — it's not there to learn.

---

## The decisions, in order

### Decision 1 — Split the facts by where they actually live ("split by source")

Some facts are written out in sentences; others are really just **form fields**.

> **Analogy — the wedding invitation.** The flowery paragraph describes the celebration (free text), but
> the **date, time, and RSVP** are fixed fields. You don't "read" the date out of a paragraph — you read
> the field.

So the six facts we care about split into two piles:

| Read from the sentences (AI highlighter / NER) | Read straight from the form field (no AI) |
|---|---|
| **DATA_TYPE** — a kind of data ("bank statements") | **DURATION** — how long consent is valid |
| **PURPOSE** — why it's wanted ("loan assessment") | **FREQUENCY** — how often data is pulled |
| **THIRD_PARTY** — who else it's shared with | **RECIPIENT** — which company receives it |

This fixed the "unlearnable labels" problem: we stopped asking the AI to find things that aren't written
in the text. (In the real AA system, duration/frequency/recipient are literally structured data fields.)

### Decision 2 — Pick the research design: "learn elsewhere, prove it here" (+ a small top-up test)

Since we can't train on AA documents (too few), we **train on big piles of related, already-labelled
documents** — website and app **privacy policies** — then test whether that learning **carries over** to
AA consent documents.

> **Analogy — learning to drive.**
> - **E1:** "Someone who learned to drive in Delhi — can they drive in Mumbai with zero Mumbai practice?"
>   (train on privacy policies, test on AA docs.)
> - **E2:** "Does a few hours of Mumbai practice noticeably help?" (train on privacy policies **+ 15 AA
>   documents**, test on the *same* AA docs.)

Comparing **E1 vs E2** is the actual research result — and it's a good result *either way* (transfer
works / doesn't / adaptation helps a lot). That's what makes it a real paper instead of a single number.

### Decision 3 — Keep a sealed "exam"

25 AA documents are hand-labelled by two people, then **locked** and "opened" only once, at the very end.

> **Analogy — the sealed exam paper.** If you peek before exam day and tweak your answers, your score
> means nothing. Same with a test set.

### Decision 4 — Verify everything against original sources; don't trust summaries

Twice, other AI "audits" were handed over; each claim was checked against the actual research papers
instead of being believed. One audit turned out to describe a file that doesn't even exist; another was
mostly right but had two wrong details, caught by reading the papers.

> **Analogy — don't play telephone.** Go to the original document, not someone's recap of it.

---

## The "label transfer" explained simply

**What's a label?** A category of highlight. We use three: `DATA_TYPE`, `PURPOSE`, `THIRD_PARTY`.

**The catch:** the training corpora use their **own names** for these same ideas. So we need a
**translation table** — this is the "mapping."

> **Analogy — recipe units.** One recipe says "1 cup," another says "240 ml." Same thing, different
> words. Before combining recipes, you standardize to one unit.

The from → to translation (verified word-for-word against the actual datasets):

| Source corpus | Their exact label name | → Our label |
|---|---|---|
| OPP-115 (website privacy policies) | `Personal Information Type` | **DATA_TYPE** |
| MAPP (app privacy policies) | `Information Type` *(they renamed it)* | **DATA_TYPE** |
| OPP-115 / MAPP | `Purpose` | **PURPOSE** |
| OPP-115 / MAPP | `Third Party Entity` | **THIRD_PARTY** |

MAPP calls it `Information Type` while OPP-115 calls it `Personal Information Type` — same idea,
different label. If we'd assumed they matched, the translation would silently break. That's why label
names are validated against each dataset.

**Why only these three transfer:** the training corpora simply **don't contain** the other concepts
(consent duration, access frequency, named company). You can't transfer knowledge that isn't there.

> **Analogy — cats-and-dogs photos.** A model trained only on cat and dog photos will never learn to
> recognize an **elephant** — there are no elephants in the training set. So we only "transfer" the
> three concepts that actually appear in both worlds.

**The right vs wrong way to highlight (subtle but crucial):**
- ❌ Wrong: highlight the **whole sentence** as DATA_TYPE.
- ✅ Right: highlight only the exact words the original human marked ("email address"), using the precise
  character positions the dataset records.

> **Analogy — a highlighter that colors only the two words that matter,** not the whole paragraph.
> Coloring the whole paragraph teaches the model garbage.

**Why two datasets got demoted to "background only":**
- **APP-350** (app policies) tags **whole paragraphs** with a topic; it never marks the exact phrase.
  *Analogy: a textbook where each chapter is labelled by subject, but no sentences are highlighted —
  fine background reading, useless for teaching precise highlighting.*
- **CUAD** (legal contracts) is whole-clause legal text — same issue.

So the teaching material was expected to be two clean sources — but on checking the *actual files*
(not just the papers), **MAPP's public download turned out to have no highlighted spans at all** — only
whole-segment labels, like APP-350. *Analogy: we were promised a highlighted textbook and received one
where only the chapter titles are tagged.* So the real teaching material is now **OPP-115 alone** for
the AI-highlighter part (its 24,516 highlighted spans are plenty); MAPP and APP-350 are both kept only
as optional background. (This catch is exactly why we insisted on validating against the real files
before building — see DECISIONS D16.)

---

## Where we are right now

- A written, source-checked **mapping table** (`NER_LABEL_MAPPING.md`, v2) — the "translation
  dictionary" the training pipeline will use.
- A locked research design (**E1 vs E2**), a locked label scheme (3 highlighted + 3 read-from-fields),
  and a locked plan for the sealed **25-document exam**.
- **The honest gap:** the research *papers* confirm these datasets are shaped the way we think — but the
  **actual data files** haven't been downloaded yet to confirm the exact highlights line up. That's the
  last check before any code runs.

**Next real steps:** sign off four minor choices → download the real OPP-115 + MAPP files (free,
research license) → write the loader that builds the training data and **refuses to run until it passes
a 20-example spot-check** against the real text.

---

## What "ReBIT" and the consent-artefact JSON mean (and why they drive the design)

**ReBIT** = **Re**serve **B**ank **I**nformation **T**echnology Pvt. Ltd. — a company **owned by RBI**
that writes the technical rulebook for the Account Aggregator system. It defines the exact format every
AA, bank, and app must follow when exchanging consent and data.

> **Analogy — the passport office.** Within a country, every passport has the same boxes in the same
> order because one authority defined the template. ReBIT is that authority for AA. It doesn't issue
> your consent; it defines the **standard shape** every consent must take.

**JSON** is just a text format for structured data — labelled boxes written as `label: value`.

> **Analogy — a form with labelled boxes.** Instead of "the tenant, John, will rent for twelve months,"
> JSON writes `tenant: "John"`, `months: 12`. A computer reads the `months` box instantly — no reading
> between the lines.

The key point: **when you approve an AA consent, the system creates a machine-readable JSON document —
the "consent artefact" — recording exactly what you agreed to, in a shape fixed by ReBIT.** Simplified:

```json
{
  "consentExpiry": "2026-07-14T10:00:00Z",       // how long consent is valid   (DURATION)
  "Frequency":  { "unit": "MONTH", "value": 1 },  // how often data is pulled    (FREQUENCY)
  "DataLife":   { "unit": "MONTH", "value": 3 },  // how long the app may keep it (DATA_LIFE)
  "FIDataRange":{ "from": "2025-01-14", "to": "2026-01-14" }, // window of history (DATA_RANGE)
  "fiTypes":    ["DEPOSIT", "MUTUAL_FUNDS"],      // what kinds of data          (DATA_TYPE)
  "Purpose":    { "text": "Loan eligibility check" }, //                          (PURPOSE)
  "DataConsumer": { "id": "BAJAJ-FINANCE-FIU" }   // who receives it             (RECIPIENT)
}
```
*(Field names are close to the real ReBIT spec, simplified for clarity.)*

**Why this drives the "split by source" decision.** There are two different things in the AA world:

| The wordy T&C / privacy prose | The consent artefact (this JSON) |
|---|---|
| Long legal paragraphs on a website | Short, structured, machine-readable form |
| Vague: "valid for the period specified" | Exact: `consentExpiry: 2026-07-14` |
| Needs AI to *read between the lines* | Already labelled — just **read the box** |

> **Analogy — a wordy invitation vs. the RSVP card.** The invitation gushes in prose; the RSVP card has
> clean boxes for date and headcount. For the headcount, you read the box — you don't parse the poetry.

So the split is simply:
- **DATA_TYPE, PURPOSE, THIRD_PARTY** → described in prose → use the **AI highlighter (NER)**.
- **DURATION, FREQUENCY, RECIPIENT** (and DATA_RANGE, DATA_LIFE) → already clean boxes in the ReBIT JSON
  → **read the field directly**, no AI, no guessing.

Building an AI to "extract how long consent lasts" from legal prose was the wrong idea: in the real
system that answer isn't buried in prose — it's a labelled box in a standard form ReBIT already designed.

---

## Why two annotators, not one (a common and reasonable question)

*"Wouldn't one annotator be more accurate, since two people disagree about what counts as an entity?"*
Intuitive, but backwards. For NER on legal/consent text **there is no pre-existing correct answer** —
humans *create* the gold labels by judgment. So the real question is: *whose judgment becomes "correct,"
and can anyone check it?*

- **One annotator:** the gold standard = whatever that one person thought. Bias, fatigue, or drift is
  **invisible** — nobody can tell. No accuracy is being "protected"; the single person's calls simply
  *are* the standard, mistakes included.
- **Two annotators + reconciliation:** you get (a) a **reliability number** (Cohen's κ) proving the
  labels aren't arbitrary, and (b) **cleaner final labels**, because hard cases get caught and resolved.

Disagreements are **information**, not noise: they flag genuinely ambiguous cases the guideline didn't
cover. The workflow is *measure* (κ) → *adjudicate* (agree the right label) → *refine the guideline*. The
final gold is the **reconciled** version, so it is more reliable than one person's, not less.

> **Analogies.** *Double-marking exams:* two examiners reconcile to prove a grade is fair, not because a
> second marker adds error. *Medical second opinion:* two doctors don't give a worse diagnosis — and if
> they disagree, that's exactly the case you needed the second for. *Two tape measures:* agreement =
> trust; disagreement reveals your ruler (guideline) is ambiguous, so you fix it. One tape measure never
> reveals it's mis-marked.

**Why it matters for the score:** the model's F1 is measured against the gold test set. If that gold is
one person's subjective calls, F1 just measures "how well the model imitates that one person" — reviewers
reject this. A corpus paper *without* inter-annotator agreement is essentially un-publishable (the plan
makes κ ≥ 0.6 a hard gate).

**Practical reconciliation (you're partly right):** you don't need two people on everything.
Double-annotate the **~20% κ-overlap subset** and the **25 gold TEST docs** (+ adjudication); the **bulk
training volume** can be single-annotated for efficiency. See DECISIONS D17.

---

## What BIO tagging is

An NER model reads text one word (token) at a time and outputs one label per token. But entities span
multiple words ("mutual fund units" = one DATA_TYPE). BIO encodes that per word:
- **B-X** = Beginning of an entity of type X (first word)
- **I-X** = Inside (a continuation word of the same entity)
- **O** = Outside (not part of any entity)

Example — "…your **bank statements** and **mutual fund units** for **loan assessment**":
`your/O bank/B-DATA_TYPE statements/I-DATA_TYPE and/O mutual/B-DATA_TYPE fund/I-DATA_TYPE
units/I-DATA_TYPE for/O loan/B-PURPOSE assessment/I-PURPOSE`

The **B vs I** distinction is the trick: the `B-` on "mutual" says *a new entity starts here*, so
"bank statements" and "mutual fund units" stay two separate entities instead of merging.

> **Analogy — a train.** `B-` is the engine (a train starts here), `I-` are the carriages, `O` is empty
> track. Two trains nose-to-tail are still two trains because each begins with an engine.

**`bio_tagging.py`** converts our char-span records ("chars 200–209 = DATA_TYPE") into per-word B/I/O
using the **model's own tokenizer** (never a space-split — D7). It handles subwords (tag the first piece,
ignore the rest in the loss) and overlaps (a documented rule picks one label when spans collide).

## How two people annotate (step by step)

Applies to the **AA documents** only (OPP-115 is already annotated) and the **3 prose labels**. Annotating
= drag-select the exact words, click the label; the tool (Label Studio) records the character offsets.

1. **Guideline first** — a rulebook: label meanings, boundary rules (tag the *minimal* noun phrase),
   ≥15 worked examples. *Analogy: agree the game's rules before kickoff.*
2. **Practice round** on 1–2 throwaway docs; compare; fix the guideline. *Analogy: a warm-up scrimmage.*
3. **Independent double-annotation** of the shared set — each person labels the **same** docs **alone**,
   no peeking. *Analogy: two students, same exam, separate rooms.*
4. **Measure κ** (`kappa.py`) word-by-word; target ≥ 0.6. *Analogy: do two referees call the same fouls?*
5. **If κ too low:** the *guideline* was ambiguous → clarify → re-annotate → recompute. One cycle is normal.
6. **Adjudicate** disagreements → one reconciled GOLD. *Analogy: two markers reconcile to a final grade.*
7. **Split the bulk** (15 adaptation docs) for solo annotation — efficiency, guideline now battle-tested.
8. **25 gold TEST docs:** both annotators + adjudication on all of them (evaluation rests on these); κ
   reported here.
9. **Export** JSON (char offsets) → same span-record → `bio_tagging.py` → CoNLL pipeline as OPP-115.

---

## Two team-role explanations: the user study (P3) and the faithfulness metric (P2)

### The user study + stats + IRB → P3
- **User study =** testing the "our summaries help people understand consent" claim on **real humans**:
  show 3 versions (raw legal text / our T5 summary / a human-written control), measure comprehension
  (a quiz), confidence, and time. *Analogy: a blind taste test — you don't declare the recipe better,
  you test it.*
- **Stats =** proving the difference is real, not luck, with small samples: effect size (how big),
  confidence intervals (how sure), non-parametric tests (Mann-Whitney/Kruskal-Wallis). *Analogy: one
  good innings doesn't make a great batsman — you need enough data and the right measure.*
- **IRB =** ethics approval for human studies; quick to file but **weeks** to approve. *Analogy: apply
  for a visa early because approval is slow, even though the trip is later.*
- **Why P3:** blockchain is self-contained and **finishes early**; the study happens **late** (needs the
  finished summaries) — so P3 is free exactly then. P3 files the IRB early (week 2–3) so approval is
  ready by study time. *Analogy: the cook who finishes early moves to plating/serving — nobody idle.*
  This was the biggest gap: the study is required for the paper and was previously unassigned.

### The faithfulness metric → P2
- **Faithfulness =** a plain summary must not **drop** a real fact or **invent** a fake one — critical
  for consent. *Analogy: simplifying a prescription that drops "take with food" is dangerous, not
  helpful.*
- **How measured:** run P1's NER over **both** source and summary; every DATA_TYPE/PURPOSE/THIRD_PARTY
  in the source must survive, with nothing invented → an entity-preservation rate. *Analogy: counting
  luggage — 3 bags in, exactly 3 out, none lost, none added.*
- **Why it matters most:** ROUGE/BERTScore only measure word similarity, not whether a critical fact was
  dropped. A consent-specific faithfulness measure is a **method**, not just an application — and methods
  are what top venues reward. *Analogy: a good dish vs. a reusable cooking technique.*
- **Why P2 explicitly:** it's about summary quality (P2 owns the summarizer), but it sits at a seam
  (P1's NER × P2's summaries × P4's integration) and would fall through the cracks if unowned. *Analogy:
  the roof corner each worker assumes the other will seal — assign it to one person so it doesn't leak.*

---

## Which models we train (and which we only use)

**Trained — family 1: NER (token classification).** Same recipe, backbone swapped (D5); each fine-tuned
twice — **E1** (OPP-115) and **E2** (OPP-115 + 15 AA docs):
- `bert-base-uncased` — general-domain baseline
- `nlpaueb/legal-bert-base-uncased` — legal-domain
- `law-ai/InLegalBERT` — Indian legal-domain
- *(optional, appendix)* `ProsusAI/finbert` — financial-domain baseline, **not** an NER model

**Trained — family 2: Summarizer (seq2seq):**
- `t5-small` (fast baseline) · `google/flan-t5-base` (instruction-tuned, the one to beat)
- *(plan also lists `t5-base`; deadline mode keeps to the two above)*

**Used but NOT trained:** BERTScore scorer (`roberta-large`, scoring only) · GPT-4o/LLM (generates
summary pairs, external) · the **faithfulness metric** (reuses the trained NER model, no new model) ·
blockchain (no ML).

**Training runs:** NER = 3 backbones × 2 conditions (E1,E2) = 6 (× seeds); Summarizer = 2. Deadline mode
uses 1 seed; full rigor ≥3 + bootstrap CIs.

---

## Is ~15 AA documents enough? (corpus size, honestly)

The "15 adaptation + 25 test = 40" figure was from the phantom 2nd-audit doc and **exceeds our real
corpus** (~29 in the manifest, ~23 genuinely usable after scraping). So the numbers were corrected (D21).

**Judge by entities, not documents.** AA docs are long; on OPP-115 we saw ~59 entities/doc. So ~15 test
docs ≈ **600–900 entity annotations** — not "15 data points." *Analogy: 15 filled worksheets, each with
dozens of answers, not 15 answers.*

- **For fine-tuning (E2 adaptation): 8–10 docs is enough** — E2 *adapts* an already-OPP-115-trained
  model; few-shot adaptation is built for small in-domain data (it's the experiment's variable, not a flaw).
- **For benchmarking (test): ~15 docs is adequate but noisy** — enough entities for entity-level F1, but
  few *documents* means wide confidence intervals (esp. THIRD_PARTY). Fix with honesty: report bootstrap
  CIs + per-label support + a stated small-corpus limitation. Fine for the workshop/college target; not
  for tight-CI top-tier claims.
- **Whole-system benchmark** needs no more annotation: summarizer = ~5–10 human summaries; faithfulness
  reuses the NER model; contract = gas/behaviour.

**Plan:** annotate all ~23 usable docs (feasible: ~30–45 min/doc, 4 people, ~1 week) → ~15 gold test +
~8 adaptation. If time is tight, do the **test set first** (E1 needs only a test set; E2 is the bonus).

> **Update (D52).** All 23 documents were annotated, but "15 + 8" turned out not to be possible without
> leakage: 13 of the documents are one template with the company name changed (up to 75% shared text), so
> they must all sit on the same side of the split. The recommended split is 9 independent test documents
> (826 entities in the final gold, D59) and 14 adaptation documents — the split P1 chose
> (`DECISIONS.md` D52, D54).

---

## If κ > 0.6, why still adjudicate? (a common confusion)

κ > 0.6 means the two annotators **agree a lot**, not that their files are **identical** — even at κ 0.6–0.8
there are still spans where P1 and P4 chose differently. So after annotating you have **two** versions of
each doc, but the test set needs **one** answer key to score the model against. **Adjudication** = resolve
the leftover disagreements together → produce that single reconciled **gold**.

- **κ (the gate):** *are we reliable enough to proceed?* (> 0.6 → yes)
- **Adjudication (the output):** *produce the one definitive gold key* by settling the remaining conflicts.

> **Analogy — two examiners, one grade sheet.** κ asks "do the two teachers mostly agree?"; but each
> student still needs one final grade, so where they differ they settle on one. High κ just makes that
> settling quick — it doesn't remove the need for a single final sheet.

High κ is good news: few conflicts → fast adjudication. (Low κ → many conflicts → the guideline is
ambiguous → fix it and re-annotate.) Then "export → CoNLL" runs on that **one gold file** to make
`aa_test.conll`, the file the model is evaluated against.

---

## Publication outlook (honest assessment)

*Can this be accepted at well-established international conferences?* **Yes — realistically at the
workshop / short-paper / resource-track level, not the flagship main tracks.** For a final-year BE
project that is a strong, credible outcome, and it matches the tier the original plan targeted.

> **Analogy — university applications: reach / match / safety.**

- **Reach (unlikely as-is):** ACL/EMNLP/NAACL *main*, IEEE S&P, USENIX Security, CCS, NDSS, NeurIPS, WWW
  main. These need methodological novelty or large scale. We use standard fine-tuning + a standard smart
  contract, a small corpus (~25–40 docs), and a small user study — solid application, not a new method.
- **Match (target these):** top-venue **workshops** — NLLP (Natural Legal Language Processing),
  PrivateNLP, TrustNLP; **PETS**; **ACM CODASPY**; **IEEE TrustCom**; **ESORICS** workshops (DPM, CBT);
  **LREC-COLING** for the corpus as a *resource*. **ACL/EMNLP Findings** is a stretch-but-possible if the
  transfer study + faithfulness metric are rigorous.
- **Safety:** regional/national conferences and student research tracks.

**Why this tier:** the NER transfer is novel in *application* but standard in *method*; the blockchain
registry is engineering, not new research; the corpus is a real but *small* resource. The **integration**
reads as applied/systems work — great for a workshop, not a flagship main track.

**Biggest lever to punch above weight:** formalize the **faithfulness / entity-preservation check** into
a proper, validated evaluation *metric* (does the plain-language summary silently drop or invent a data
type/purpose?). That turns "we built a pipeline" into "we propose a way to measure consent-summary
faithfulness" — a genuine, if small, methodological contribution.

**What currently caps the ceiling:** small corpus (the #1 limiter), a possibly-inconclusive ablation
(small dev set), and an underpowered user study. What *wins* at the match tier isn't more ambition — it's
execution and honesty: a clean reproducible artifact, rigorous modest evaluation, and no overclaiming
(habits already built into the plan).

---

*Companion documents: `NER_LABEL_MAPPING.md` (the translation table) and the full audit/decision log in
the plan file `c-users-pc-downloads-consentledger-30-g-quiet-storm.md`.*
