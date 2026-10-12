
"""Verify consent state, check document integrity, and build audit links."""

import argparse
import json
import os

from web3 import Web3

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
    args = parser.parse_args()

    try:
        consent_id = bytes.fromhex(args.consent_id.removeprefix("0x"))
    except ValueError:
        parser.error("--consent-id must be a valid hexadecimal value.")

    if len(consent_id) != 32:
        parser.error("--consent-id must contain exactly 32 bytes (64 hex characters).")

    with open(args.file, "r", encoding="utf-8") as file:
        consent_data = json.load(file)

    if not isinstance(consent_data, dict):
        parser.error("The consent JSON must contain a JSON object.")

    canonical_data = json.dumps(
        consent_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    presented_hash = Web3.keccak(canonical_data)

    w3 = get_web3()
    contract = get_contract(w3)

    consent = contract.functions.consents(consent_id).call()

    # Public mapping tuple:
    # artefactHash, owner, expiry, nonce, status
    stored_hash, owner, expiry, nonce, status = consent

    valid = contract.functions.isValid(
        consent_id,
        presented_hash,
    ).call()

    print(f"Consent ID: 0x{consent_id.hex()}")
    print(f"Owner: {owner}")
    print(f"Expiry timestamp: {expiry}")
    print(f"Nonce: {nonce}")
    print(f"Status code: {status}")
    print(f"Stored document hash: 0x{stored_hash.hex()}")
    print(f"Presented document hash: 0x{presented_hash.hex()}")
    print(f"Document hash matches: {stored_hash == presented_hash}")
    print(f"Consent valid: {valid}")

    # Status codes from ConsentRegistry.sol:
    # 0 = NONE, 1 = CREATED, 2 = GRANTED, 3 = REVOKED
    status_names = {0: "NONE", 1: "CREATED", 2: "GRANTED", 3: "REVOKED"}
    print(f"Consent status: {status_names.get(status, 'UNKNOWN')}")

    tx_hash = os.environ.get("CONSENT_TRANSACTION_HASH")
    if tx_hash:
        print(f"Etherscan audit link: https://sepolia.etherscan.io/tx/{tx_hash}")
    else:
        print("Etherscan audit link: available after supplying a transaction hash.")


if __name__ == "__main__":
    main()
