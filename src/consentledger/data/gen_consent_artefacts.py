"""Generate synthetic ReBIT consent artefacts by varying the field values of the real templates.

The corpus has almost no filled artefacts, so the structured-parser eval set is the 2 real Sahamati examples
(data/aa/consent_artefacts/real_*.json) plus these schema-valid synthetic variants.

Usage:
    python -m consentledger.data.gen_consent_artefacts --n 30 --out data/aa/consent_artefacts/synthetic
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ART_DIR = PROJECT_ROOT / "data" / "aa" / "consent_artefacts"

# (code, text) pairs are the real RBI AA purpose codes 101-105.
PURPOSES = [
    ("101", "Wealth management service"),
    ("102", "Customer spending patterns, budget or other reportings"),
    ("103", "To process borrower's loan application"),
    ("104", "To monitor a borrower's accounts for loan collection, in case of overdue payments"),
    ("105", "Explicit consent from customer for accessing his financial information"),
]
UNITS = ["DAY", "MONTH", "YEAR"]
CONSENT_TYPES = ["PROFILE", "SUMMARY", "TRANSACTIONS"]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def make_artefact(rng: random.Random, i: int) -> dict:
    start = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 600))
    expiry = start + timedelta(days=rng.randint(30, 730))
    data_from = start - timedelta(days=rng.randint(30, 365))
    fetch = rng.choice(["ONETIME", "PERIODIC"])
    code, text = rng.choice(PURPOSES)
    return {
        "ConsentDetail": {
            "consentStart": _iso(start),
            "consentExpiry": _iso(expiry),
            "consentMode": rng.choice(["STORE", "VIEW", "QUERY"]),
            "fetchType": fetch,
            "consentTypes": rng.sample(CONSENT_TYPES, rng.randint(1, 3)),
            "DataConsumer": {"id": f"DC{rng.randint(1, 50)}", "type": "FIU"},
            "DataProvider": {"id": f"DP{rng.randint(1, 50)}", "type": "FIP"},
            "Customer": {"id": f"cust{i:04d}@aa"},
            "Purpose": {"code": code, "text": text},
            "FIDataRange": {"from": _iso(data_from), "to": _iso(start)},
            "DataLife": {"unit": rng.choice(UNITS), "value": rng.randint(1, 24)},
            # ONETIME still carries a Frequency box in the schema; value 1 is conventional.
            "Frequency": {"unit": rng.choice(UNITS), "value": 1 if fetch == "ONETIME" else rng.randint(1, 30)},
        }
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic ReBIT consent artefacts.")
    ap.add_argument("--n", type=int, default=30, help="how many to generate")
    ap.add_argument("--out", type=Path, default=ART_DIR / "synthetic", help="output dir")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for i in range(args.n):
        art = make_artefact(rng, i)
        (args.out / f"synthetic_{i:03d}.json").write_text(json.dumps(art, indent=2), encoding="utf-8")
    print(f"wrote {args.n} synthetic artefacts -> {args.out.relative_to(PROJECT_ROOT)} (seed {args.seed})")


def _selfcheck() -> None:
    """Every generated artefact must carry the 3 structured labels + parse as valid JSON."""
    rng = random.Random(0)
    for i in range(50):
        a = make_artefact(rng, i)["ConsentDetail"]
        assert a["Frequency"]["value"] >= 1 and a["Frequency"]["unit"] in UNITS
        assert a["consentExpiry"] > a["consentStart"]          # ISO strings sort chronologically
        assert a["DataConsumer"]["id"].startswith("DC")
        assert a["FIDataRange"]["from"] < a["FIDataRange"]["to"]
        json.loads(json.dumps(a))
    print("selfcheck OK")


def _validate() -> None:
    """Validate generated + the real ONETIME example against the formal schema."""
    import jsonschema
    schema = json.loads((ART_DIR / "consent_artefact_schema.json").read_text(encoding="utf-8"))
    real = json.loads((ART_DIR / "real_onetime_loan_application.json").read_text(encoding="utf-8"))
    real.pop("_source", None); real.pop("_note", None)
    jsonschema.validate(real, schema)                          # real example conforms
    rng = random.Random(1)
    for i in range(50):
        jsonschema.validate(make_artefact(rng, i), schema)     # every synthetic conforms
    print("validate OK (real ONETIME + 50 synthetic conform to schema)")


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        _selfcheck()
    elif "--validate" in sys.argv:
        _validate()
    else:
        main()
