# ConsentLedger — External-Corpus → NER Label Mapping (v2, for review)

**Purpose.** Load-bearing artifact of the E1 transfer experiment (plan Part D). Defines how
source-corpus annotations become BIO training labels for the **three candidate transferable NER
labels**: `DATA_TYPE`, `PURPOSE`, `THIRD_PARTY`. "Candidate" until validated on the real annotation
exports (§7). If this mapping is wrong, E1 measures nothing — so it is reviewed and signed off *before*
loader code or annotation work.

**Grounding.** Every claim below is checked against the primary papers (read directly, not from memory):
OPP-115 = Wilson et al., ACL 2016; MAPP = LREC 2022 (2022.lrec-1.585); APP-350 = Zimmeck et al. /
MAPS, PoPETs 2019; CUAD = Hendrycks et al., NeurIPS 2021. See §8.

**v2 changelog (from v1):** MAPP reworded as an *extension* of OPP-115 with its own attribute names;
`THIRD_PARTY` pinned to Definition A; **APP-350 downgraded to auxiliary** (segment-level, not entity
spans); provenance fields added; negative-modality exclusion extended to OPP-115/MAPP; labels marked
"candidate"; worked example marked illustrative.

---

## Core principle (non-negotiable)

Map **an attribute value's character span → BIO**. Never a whole category, segment, or clause; never
`text.split()`. The unit of conversion is one grounded attribute-value span, tagged over the tokens its
character offsets cover via `tokenizer(..., return_offsets_mapping=True)`.

Replicate the sources' own exclusions: **drop practices labelled `Other`, values labelled
`Unspecified`, and any negative/reversed-modality practice** (see §5).

---

## 1. OPP-115 (Tier 1, span-level, primary)

OPP-115 stores `{Practice, Attribute, Value}` triples, each attribute value carrying **character-level
start/end offsets** into a policy segment. Only three attributes map to our labels:

| OPP-115 attribute (verbatim) | Appears under | → label | Note |
|---|---|---|---|
| `Personal Information Type` | First Party Collection/Use **and** Third Party Sharing/Collection | **`DATA_TYPE`** | value set includes "Financial"; OPP-115 is website policies → generic. That generic-vs-AA gap is what E1 measures. |
| `Purpose` | First Party Collection/Use **and** Third Party Sharing/Collection | **`PURPOSE`** | values are categorical; we tag the **annotated span**, flat (not sub-typed). |
| `Third Party Entity` | Third Party Sharing/Collection only | **`THIRD_PARTY`** | see Definition A below |

**Explicitly NOT mapped:** `User Choice/Control` (≠ PURPOSE — it's control mechanisms), `Data Retention`
(≠ consent duration; and duration is a structured-artefact field, not NER), and every other attribute /
category (`Collection Mode`, `Action First-Party`, `Action Third-Party`, `Identifiability`, `User Type`,
`Choice Type`, `Choice Scope`, `Data Security`, `Policy Change`, `Do Not Track`, `International &
Specific Audiences`, `Other`).

### THIRD_PARTY — Definition A (locked)

`THIRD_PARTY` = **the text span identifying the third-party entity/recipient** (the value of the
`Third Party Entity` attribute), e.g. "credit bureaus", "service providers", "affiliates".
It is **not** any span of generic third-party-sharing language. So:
> "…share information with **[credit bureaus]**" → the bracketed span only.

---

## 2. MAPP-English — RECLASSIFIED to auxiliary (public release has NO spans) — see D16

**Correction (validated against the actual files, 2026-09-09):** the earlier plan to use MAPP as a
Tier-1 span-level source was based on the LREC 2022 *paper* (which had `selectedText` internally). The
**public MAPP release does not ship spans.** Its `English_consolidation/` is one row **per segment**
listing which attributes/values appear (`['Information Type','Purpose',...]`) — **no `selectedText`, no
character offsets** (verified: `grep` for offset fields → 0 matches; segments are newline-separated).

Consequence: MAPP **cannot** be converted to token-level BIO without fabricating spans, so it is
**demoted to auxiliary** alongside APP-350 and CUAD. **OPP-115 (§1) is the sole span-level NER source.**
MAPP-English may still be used later for a *segment-level* auxiliary task (multi-label classification /
continued pretraining) — optional, not core. The refined attribute names (`Information Type`, etc.)
remain accurate for that segment-level use.

---

## 3. Auxiliary only — NOT converted to entity labels (APP-350, CUAD)

Neither yields clean entity spans, so **neither is BIO-converted**. Both are optional legal/privacy
domain-adaptation signal (continued pretraining / auxiliary classification), or dropped.

- **APP-350** — annotates at the **segment level**: "assign annotation labels to policy segments …
  loosely correspond to paragraphs," each practice *classified* by (data type, party, modality). The
  party (1st/3rd) is a **segment classification**, not a character-span entity. BIO-tagging a
  party=3rd-party segment would relabel a whole paragraph as `THIRD_PARTY` — the banned pattern.
  **→ auxiliary only. No `DATA_TYPE` / `THIRD_PARTY` rows.**
- **CUAD** — 41 clause *types* for clause extraction; a clause span is a whole clause, not an entity.
  **→ auxiliary only, or drop.**

**Consequence:** the core span-level NER training sources are **OPP-115 + MAPP-English**. APP-350 + CUAD
are auxiliary.

---

## 4. Provenance (every generated BIO span must carry this)

So each training label is traceable to its source annotation and the conversion is auditable:

```
doc_id, segment_id, practice, attribute, value,
start_char, end_char, polarity/modality,
source_dataset, source_annotation_id
```

Example record → tags:
```
{OPP-115, policy_037, seg_12, Third Party Sharing/Collection,
 Third Party Entity, "credit bureaus", 142, 157, positive, OPP-115, ann_8842}
→  B-THIRD_PARTY I-THIRD_PARTY
```

---

## 5. Polarity / modality exclusion (applies to ALL sources)

Exclude negative/reversed-modality practices from positive supervision — a policy asserting it does
**not** do something must not produce a positive entity:
- OPP-115 / MAPP: drop practices whose `Does/Does Not` (or equivalent) dimension is negative.
- APP-350 (if used as auxiliary): `not-performed` modality excluded.
> "We do **not** share your location with third parties." → yields **no** `THIRD_PARTY` / `DATA_TYPE`.

---

## 6. Review decisions (sign-off before loader code)

1. **DATA_TYPE from third-party context** — default **include** `Personal Information Type` /
   `Information Type` values regardless of which category. Confirm, or restrict to first-party only.
2. **APP-350 / CUAD** — default **auxiliary only** (no BIO). Confirm, or drop entirely.
3. **MAPP** — default **English-64 only**; validate its `Purpose`/`Information Type`/`Third Party
   Entity` attribute names against MAPP Table 7 before converting. Confirm.
4. **PURPOSE** flat, not sub-typed. Confirm.

---

## 7. Validation gate (before "candidate" → "transferable")

Papers confirm structure; only the real exports confirm the conversion. Before trusting the loader:
1. Load the actual OPP-115 + MAPP annotation exports.
2. Confirm the three attribute names + character offsets exist **per corpus** (they differ).
3. Spot-check ≥20 converted spans against source text (reconstruct, eyeball).
Only then drop "candidate" and call the three labels transferable.

---

## 8. Worked example (Illustrative — NOT an OPP-115 quotation)

> "We collect your **email address** to **send you promotional offers**, and may share it with our
> **advertising partners**."

- `Personal Information Type` span "email address" → `B-DATA_TYPE I-DATA_TYPE`
- `Purpose` span "send you promotional offers" → `B-PURPOSE I-PURPOSE I-PURPOSE I-PURPOSE`
- `Third Party Entity` span "advertising partners" → `B-THIRD_PARTY I-THIRD_PARTY`
- all other tokens → `O`

Banned alternative: tagging the entire sentence `B-DATA_TYPE I-DATA_TYPE …`.

---

## 9. Provenance of the facts in this document

- OPP-115: Wilson et al., *The Creation and Analysis of a Website Privacy Policy Corpus*, ACL 2016 —
  115 policies, 23,194 practices, 128,347 attribute values, 102,576 spans with char offsets.
- MAPP: *A Tale of Two Regulatory Regimes*, LREC 2022 (2022.lrec-1.585) — 64 EN + 91 DE; refines
  OPP-115 (14 attrs/89 vals → 19 attrs/124 vals); span-grounded via `selectedText`.
- APP-350 / MAPS: Zimmeck et al., PoPETs 2019 — 350 Android policies; segment-level (data type / party /
  modality) classification.
- CUAD: Hendrycks et al., NeurIPS 2021 D&B — 510 contracts, 41 clause types, CC BY 4.0.
- PolicyQA (attribute-name + offset structure verification): Ahmad et al., 2020, arXiv:2010.02557.
