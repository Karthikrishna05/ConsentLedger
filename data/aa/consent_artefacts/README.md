# AA Consent Artefacts — parser fixtures (structured source, NOT NER)

These are the **structured** side of the "split by source" design (DECISIONS D2). The three fields the
prose T&C documents do NOT contain — RECIPIENT, DURATION, FREQUENCY — live here, as JSON, in the ReBIT
**consent artefact** exchanged FIP↔AA↔FIU when a consent is actually granted. This was verified against a
primary source on 2026-09-14 (see DECISIONS D27).

## Files
- `consent_artefact_schema.json` — the **formal JSON Schema** (draft-07): the blank-form definition of
  every box and its type. Use it to validate any filled artefact. Validates the CANONICAL nesting
  (everything inside `ConsentDetail`); the periodic example below shows sibling nesting (a rendering
  quirk) so it does not validate as-is — parse.py looks keys up robustly regardless.
- `real_onetime_loan_application.json` — real published example (Sahamati, one-time/ONETIME).
- `real_periodic_loan_monitoring.json` — real published example (Sahamati, periodic/PERIODIC).

Validate real + synthetic against the schema:
```
python -m consentledger.data.gen_consent_artefacts --validate
```

Sources:
- https://sahamati.org.in/consent-artefact-one-time-consent-for-a-loan-application/
- https://sahamati.org.in/consent-artefact-periodic-consent-for-monitoring-of-loan-account/

## Field → label map (what `consent_artefact/parse.py` extracts)
| Label | JSON field | Example value |
|---|---|---|
| DURATION | `consentStart` / `consentExpiry` (ISO timestamps) | 2020-01-06 → 2022-01-06 |
| FREQUENCY | `Frequency { unit, value }` | `{ "unit": "MONTH", "value": 5 }` |
| RECIPIENT | `DataConsumer { id, type:"FIU" }` | `{ "id": "DC1", "type": "FIU" }` (a coded id, not a prose name) |
| (DATA_RANGE) | `FIDataRange { from, to }` | date window |
| (DATA_LIFE) | `DataLife { unit, value }` | `{ "unit": "MONTH", "value": 1 }` |
| context | `fetchType` (ONETIME/PERIODIC), `Purpose { code, text }`, `consentTypes`, `DataProvider`, `Customer` | — |

## Two gotchas for the parser
1. **RECIPIENT is a code** (`DC1`), not "ICICI HFC" — resolve id→entity; do not expect a text name.
2. **Nesting varies**: one example nests `DataConsumer`/`Purpose`/`Frequency`/… inside `ConsentDetail`,
   the other has them as siblings. Look each key up **robustly** (recursive search), not by a fixed path.

## Generating synthetic artefacts
The scraped corpus contains ~0 filled artefacts, so the parser's eval set = these 2 real ones + synthetic
variants. Generate with:
```
python -m consentledger.data.gen_consent_artefacts --n 30 --out data/aa/consent_artefacts/synthetic
```
Honesty rule (D2/D27): the parser is a **deterministic reader of the ReBIT schema**, demonstrated on real
+ synthetic artefacts — NOT an evaluated ML model. The NER E1/E2 study stays the headline contribution.
