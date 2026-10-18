"""Verify consent state, document integrity, and audit links.

    python -m consentledger.chain.read_consent --consent-id 0x<64 hex> --file <consent.json>
    python -m consentledger.chain.read_consent --consent-id 0x<64 hex> --file <consent.json> --record
      (--record also writes the check on-chain: who asked, which document, valid or not - a transaction)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from web3 import Web3

from .register_consent import hash_artefact
from .revoke_consent import parse_consent_id
from .web3_client import explorer_link, get_account, get_contract, get_web3, send

STATUS = {0: "NONE", 1: "CREATED", 2: "GRANTED", 3: "REVOKED"}


def check(consent_id: str, artefact: dict) -> dict:
    """Read-only: the stored record, and whether this document is the one consented to (no transaction)."""
    w3 = get_web3()
    contract = get_contract(w3)
    cid, presented = parse_consent_id(consent_id), hash_artefact(artefact)
    stored, owner, expiry, nonce, status = contract.functions.consents(cid).call()
    return {"chain_id": w3.eth.chain_id, "consent_id": Web3.to_hex(cid), "owner": owner, "expiry_timestamp": expiry,
            "expired": expiry <= int(datetime.now(timezone.utc).timestamp()), "nonce": nonce,
            "status": STATUS.get(status, "UNKNOWN"), "stored_hash": Web3.to_hex(stored),
            "presented_hash": Web3.to_hex(presented), "hash_matches": bytes(stored) == bytes(presented),
            "valid": contract.functions.isValid(cid, presented).call()}


def record_access(consent_id: str, artefact: dict) -> dict:
    """Check the consent AND leave an audit entry on-chain (AccessRecorded: accessor, document hash, valid)."""
    w3 = get_web3()
    contract = get_contract(w3)
    receipt = send(w3, get_account(w3),
                   contract.functions.recordAccess(parse_consent_id(consent_id), hash_artefact(artefact)))
    event = contract.events.AccessRecorded().process_receipt(receipt)[0]["args"]
    return {"consent_id": consent_id, "valid": event["valid"], "accessor": event["accessor"],
            "access_transaction": Web3.to_hex(receipt.transactionHash),
            "audit_link": explorer_link(w3, receipt.transactionHash)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether a consent record is valid.")
    parser.add_argument("--consent-id", required=True, help="Consent ID printed by register_consent.py.")
    parser.add_argument("--file", required=True, help="Path to the consent JSON file to verify.")
    parser.add_argument("--record", action="store_true", help="Also record this check on-chain (a transaction).")
    args = parser.parse_args()

    try:
        parse_consent_id(args.consent_id)
    except ValueError as exc:
        parser.error(f"--consent-id: {exc}")
    try:
        with open(args.file, "r", encoding="utf-8-sig") as file:
            artefact = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"Could not read consent JSON: {exc}")
    if not isinstance(artefact, dict):
        parser.error("The consent JSON must contain a JSON object.")

    print(json.dumps(check(args.consent_id, artefact), indent=2))
    if args.record:
        print(json.dumps(record_access(args.consent_id, artefact), indent=2))


if __name__ == "__main__":
    main()
