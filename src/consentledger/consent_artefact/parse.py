"""Parse RECIPIENT/DURATION/FREQUENCY/DATA_RANGE/DATA_LIFE from ReBIT-shaped consent JSON.

A deterministic reader, not a model. Keys are found at any depth, since published artefacts put the blocks
inside `ConsentDetail` or beside it. A missing block comes back as None.

    python -m consentledger.consent_artefact.parse data/aa/consent_artefacts/real_periodic_loan_monitoring.json
    python -m consentledger.consent_artefact.parse --selfcheck
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _find(obj: Any, key: str) -> Any:
    """The first value stored under `key`, searching nested objects breadth-first."""
    todo = [obj]
    while todo:
        cur = todo.pop(0)
        if isinstance(cur, dict):
            if key in cur:
                return cur[key]
            todo += list(cur.values())
        elif isinstance(cur, list):
            todo += cur
    return None


def _block(obj: Any, key: str, fields: tuple[str, ...]) -> dict | None:
    v = _find(obj, key)
    return {f: v.get(f) for f in fields} if isinstance(v, dict) else None


def parse(artefact: dict) -> dict:
    """The five structured facts plus the context a reader needs to interpret them."""
    if not isinstance(artefact, dict):
        raise TypeError("a consent artefact must be a JSON object")
    start, expiry = _find(artefact, "consentStart"), _find(artefact, "consentExpiry")
    return {
        "RECIPIENT": _block(artefact, "DataConsumer", ("id", "type")),         # a coded id ("DC1"), not a name
        "DURATION": {"start": start, "expiry": expiry} if start or expiry else None,
        "FREQUENCY": _block(artefact, "Frequency", ("unit", "value")),         # fetches allowed per unit
        "DATA_RANGE": _block(artefact, "FIDataRange", ("from", "to")),
        "DATA_LIFE": _block(artefact, "DataLife", ("unit", "value")),          # how long the data may be kept
        "fetch_type": _find(artefact, "fetchType"),
        "consent_mode": _find(artefact, "consentMode"),
        "consent_types": _find(artefact, "consentTypes"),
        "purpose": _block(artefact, "Purpose", ("code", "text")),
        "data_provider": _block(artefact, "DataProvider", ("id", "type")),
    }


def _selfcheck() -> None:
    import random
    from consentledger.data.gen_consent_artefacts import ART_DIR, make_artefact

    one = parse(json.loads((ART_DIR / "real_onetime_loan_application.json").read_text(encoding="utf-8")))
    per = parse(json.loads((ART_DIR / "real_periodic_loan_monitoring.json").read_text(encoding="utf-8")))
    assert one["RECIPIENT"] == {"id": "DC1", "type": "FIU"} and one["FREQUENCY"] == {"unit": "DAY", "value": 1}
    assert one["DATA_LIFE"] == {"unit": "DAY", "value": 15} and one["fetch_type"] == "ONETIME"
    assert one["DURATION"]["expiry"] == "2019-12-26T11:39:57.153Z" and one["purpose"]["code"] == "103"
    # the periodic example keeps its blocks beside ConsentDetail, not inside it
    assert per["FREQUENCY"] == {"unit": "MONTH", "value": 5} and per["DATA_LIFE"] == {"unit": "MONTH", "value": 1}
    assert per["DATA_RANGE"]["from"] == "2020-01-06T11:33:34.509Z" and per["fetch_type"] == "PERIODIC"
    rng = random.Random(0)
    for i in range(30):
        p = parse(make_artefact(rng, i))
        assert all(p[k] is not None for k in ("RECIPIENT", "DURATION", "FREQUENCY", "DATA_RANGE", "DATA_LIFE")), p
    empty = parse({"ConsentDetail": {}})
    assert empty["RECIPIENT"] is None and empty["DURATION"] is None
    print("selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        print(json.dumps(parse(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))), indent=2))
