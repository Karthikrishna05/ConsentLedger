
"""Register a consent artefact on the ConsentRegistry contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from web3 import Web3

from .web3_client import explorer_link, get_account, get_contract, get_web3, send

ROOT = Path(__file__).resolve().parents[3]


def canonicalize(artefact: dict[str, Any]) -> bytes:
    """Return deterministic JSON bytes, ignoring underscore-prefixed comments."""
    if not isinstance(artefact, dict):
        raise TypeError("The consent artefact must be a JSON object.")

    clean = {key: value for key, value in artefact.items()
             if not key.startswith("_")}

    return json.dumps(
        clean,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def hash_artefact(artefact: dict[str, Any]) -> bytes:
    """Calculate the Keccak-256 hash of the canonical artefact."""
    return Web3.keccak(canonicalize(artefact))


def expiry_timestamp(artefact: dict[str, Any]) -> int:
    """Use ConsentDetail.consentExpiry, falling back to expiry_days."""
    detail = artefact.get("ConsentDetail", {})
    expiry = detail.get("consentExpiry") if isinstance(detail, dict) else None

    if expiry:
        value = str(expiry).strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        timestamp = int(parsed.timestamp())
        if timestamp <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Consent expiry must be in the future.")
        return timestamp

    days = artefact.get("expiry_days", 30)
    if isinstance(days, bool) or not isinstance(days, int) or days <= 0:
        raise ValueError("expiry_days must be a positive integer.")

    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())


def register(artefact: dict[str, Any]) -> dict[str, Any]:
    """Register an artefact, then grant consent; return its on-chain details."""
    w3 = get_web3()
    account = get_account(w3)
    contract = get_contract(w3)

    artefact_hash = hash_artefact(artefact)
    expiry = expiry_timestamp(artefact)

    # Nonce helps the contract generate a distinct ID for each registration.
    nonce = w3.eth.get_transaction_count(account.address, "pending")

    receipt = send(
        w3,
        account,
        contract.functions.createConsent(
            artefact_hash,
            expiry,
            nonce,
        ),
    )

    events = contract.events.ConsentCreated().process_receipt(receipt)
    if not events:
        raise RuntimeError(
            "The transaction succeeded, but no ConsentCreated event was found."
        )

    consent_id = events[0]["args"]["consentId"]

    grant_receipt = send(
        w3,
        account,
        contract.functions.grantConsent(consent_id),
    )

    return {
        "consent_id": Web3.to_hex(consent_id),
        "artefact_hash": Web3.to_hex(artefact_hash),
        "expiry_timestamp": expiry,
        "create_transaction": Web3.to_hex(receipt.transactionHash),
        "grant_transaction": Web3.to_hex(grant_receipt.transactionHash),
        "granted": True,
        "audit_link": explorer_link(w3, receipt.transactionHash),
    }


def run_selfcheck() -> None:
    """Check deterministic hashing without a network or wallet."""
    original = {
        "purpose": "Research",
        "data": {"subject": "Demo User"},
        "_comment": "This field should not affect the hash.",
    }
    reordered = {
        "_comment": "Different comment.",
        "data": {"subject": "Demo User"},
        "purpose": "Research",
    }
    changed = {
        "purpose": "Clinical Research",
        "data": {"subject": "Demo User"},
    }

    assert hash_artefact(original) == hash_artefact(reordered)
    assert hash_artefact(original) != hash_artefact(changed)
    print("Self-check passed: stable JSON hashing and change detection work.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register and grant a consent artefact."
    )
    parser.add_argument(
        "--file",
        default=str(ROOT / "data" / "aa" / "consent_artefacts" / "demo_consent.json"),
        help="Path to the consent JSON file.",
    )
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="Test hashing locally without connecting to a blockchain.",
    )
    args = parser.parse_args()

    if args.selfcheck:
        run_selfcheck()
        return

    file_path = Path(args.file)
    artefact = json.loads(file_path.read_text(encoding="utf-8-sig"))

    print("Connecting to the configured blockchain...")
    result = register(artefact)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
