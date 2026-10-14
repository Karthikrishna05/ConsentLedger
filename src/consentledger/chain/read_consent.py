
"""Verify consent state, document integrity, and audit links."""

import argparse
import os
import json
from datetime import datetime, timezone

from web3 import Web3

from .register_consent import hash_artefact
from .web3_client import get_web3, get_contract


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether a consent record is valid."
    )
    parser.add_argument(
        "--consent-id",
        required=True,
        help="Consent ID printed by register_consent.py.",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the consent JSON file to verify.",
    )
    parser.add_argument(
        "--tx-hash",
        default=os.environ.get("CONSENT_TRANSACTION_HASH"),
        help="Optional transaction hash for the audit link.",
    )
    args = parser.parse_args()

    try:
        consent_id = bytes.fromhex(args.consent_id.removeprefix("0x"))
    except ValueError:
        parser.error("--consent-id must be a valid hexadecimal value.")

    if len(consent_id) != 32:
        parser.error(
            "--consent-id must contain exactly 32 bytes (64 hex characters)."
        )

    try:
        with open(args.file, "r", encoding="utf-8-sig") as file:
            consent_data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"Could not read consent JSON: {exc}")

    if not isinstance(consent_data, dict):
        parser.error("The consent JSON must contain a JSON object.")

    # Use the same canonicalization and hashing as registration.
    presented_hash = hash_artefact(consent_data)

    w3 = get_web3()
    contract = get_contract(w3)

    consent = contract.functions.consents(consent_id).call()
    stored_hash, owner, expiry, nonce, status = consent

    hash_matches = bytes(stored_hash) == bytes(presented_hash)

    valid = contract.functions.isValid(
        consent_id,
        presented_hash,
    ).call()

    status_names = {
        0: "NONE",
        1: "CREATED",
        2: "GRANTED",
        3: "REVOKED",
    }
    status_name = status_names.get(status, "UNKNOWN")
    now = int(datetime.now(timezone.utc).timestamp())

    print(f"Network chain ID: {w3.eth.chain_id}")
    print(f"Consent ID: {Web3.to_hex(consent_id)}")
    print(f"Owner: {owner}")
    print(f"Expiry timestamp: {expiry}")
    print(f"Expired: {expiry <= now}")
    print(f"Nonce: {nonce}")
    print(f"Status code: {status}")
    print(f"Stored document hash: {Web3.to_hex(stored_hash)}")
    print(f"Presented document hash: {Web3.to_hex(presented_hash)}")
    print(f"Document hash matches: {hash_matches}")
    print(f"Consent valid: {valid}")
    print(f"Consent status: {status_name}")

    if args.tx_hash:
        tx_hash = args.tx_hash.strip()
        if tx_hash.startswith("0x"):
            tx_hash = tx_hash[2:]

        try:
            if len(tx_hash) != 64:
                raise ValueError
            bytes.fromhex(tx_hash)
        except ValueError:
            parser.error("--tx-hash must be a 32-byte hexadecimal transaction hash.")

        if w3.eth.chain_id == 11155111:
            print(
                "Etherscan audit link: "
                f"https://sepolia.etherscan.io/tx/0x{tx_hash}"
            )
        elif w3.eth.chain_id == 1:
            print(
                f"Etherscan audit link: https://etherscan.io/tx/0x{tx_hash}"
            )
        else:
            print(
                "Audit link unavailable: this is a local or unsupported network."
            )
    else:
        print("Audit link: no transaction hash supplied.")


if __name__ == "__main__":
    main()
