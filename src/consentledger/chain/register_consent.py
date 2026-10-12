
"""Canonicalize consent data, hash it, and register/grant consent."""

import argparse
import hashlib
import json
import time

from web3 import Web3

from .web3_client import get_web3, get_account, get_contract, send


def canonicalize(data: dict) -> bytes:
    """Serialize JSON deterministically so equivalent data gets the same hash."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def keccak_hash(data: bytes) -> bytes:
    """Return the Ethereum Keccak-256 hash."""
    return Web3.keccak(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register and grant consent on ConsentRegistry."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the consent JSON file.",
    )
    parser.add_argument(
        "--expiry-days",
        type=int,
        default=30,
        help="Number of days until consent expires (default: 30).",
    )
    args = parser.parse_args()

    if args.expiry_days <= 0:
        parser.error("--expiry-days must be greater than zero.")

    with open(args.file, "r", encoding="utf-8") as file:
        consent_data = json.load(file)

    if not isinstance(consent_data, dict):
        parser.error("The consent JSON must contain a JSON object.")

    canonical_data = canonicalize(consent_data)
    artefact_hash = keccak_hash(canonical_data)

    # Derive a deterministic consent ID from the document hash and a unique nonce.
    nonce = int(time.time_ns())
    consent_id = Web3.keccak(
        artefact_hash + nonce.to_bytes(32, byteorder="big")
    )

    expiry = int(time.time()) + args.expiry_days * 24 * 60 * 60

    w3 = get_web3()
    account = get_account(w3)
    contract = get_contract(w3)

    print("Connecting to Sepolia...")
    print(f"Wallet address: {account.address}")
    print(f"Consent ID: 0x{consent_id.hex()}")
    print(f"Document hash: 0x{artefact_hash.hex()}")
    print(f"Expiry timestamp: {expiry}")

    input("Review the details above. Press Enter to submit, or Ctrl+C to cancel.")

    created_receipt = send(
        w3,
        account,
        contract.functions.createConsent(
            consent_id,
            artefact_hash,
            expiry,
            nonce,
        ),
    )

    if created_receipt.status != 1:
        raise RuntimeError("createConsent transaction failed.")

    print(f"Consent created. Transaction: {created_receipt.transactionHash.hex()}")

    granted_receipt = send(
        w3,
        account,
        contract.functions.grantConsent(consent_id),
    )

    if granted_receipt.status != 1:
        raise RuntimeError("grantConsent transaction failed.")

    print(f"Consent granted. Transaction: {granted_receipt.transactionHash.hex()}")
    print("Save the consent ID above; you will need it to verify consent later.")


if __name__ == "__main__":
    main()
