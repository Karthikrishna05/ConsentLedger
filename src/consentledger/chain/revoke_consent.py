"""Revoke a consent on the ConsentRegistry contract (only its owner's wallet can).

    python -m consentledger.chain.revoke_consent --consent-id 0x<64 hex>          # asks before sending
    python -m consentledger.chain.revoke_consent --consent-id 0x<64 hex> --yes
"""

from __future__ import annotations

import argparse
import json

from web3 import Web3

from .web3_client import explorer_link, get_account, get_contract, get_web3, send


def parse_consent_id(value: str) -> bytes:
    raw = bytes.fromhex(value.strip().removeprefix("0x"))
    if len(raw) != 32:
        raise ValueError("a consent id is 32 bytes (64 hex characters)")
    return raw


def revoke(consent_id: str) -> dict:
    """Revoke the consent; return the transaction and its audit link. Revoking cannot be undone."""
    w3 = get_web3()
    receipt = send(w3, get_account(w3), get_contract(w3).functions.revokeConsent(parse_consent_id(consent_id)))
    return {"consent_id": consent_id, "revoke_transaction": Web3.to_hex(receipt.transactionHash),
            "block": receipt.blockNumber, "audit_link": explorer_link(w3, receipt.transactionHash)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Revoke a consent (cannot be undone).")
    parser.add_argument("--consent-id", required=True, help="Consent ID printed by register_consent.py.")
    parser.add_argument("--yes", action="store_true", help="Do not ask for confirmation.")
    args = parser.parse_args()

    try:
        parse_consent_id(args.consent_id)
    except ValueError as exc:
        parser.error(f"--consent-id: {exc}")

    if not args.yes and input(f"Revoke {args.consent_id}? This cannot be undone. Type YES: ") != "YES":
        print("Cancelled.")
        return

    print(json.dumps(revoke(args.consent_id), indent=2))


if __name__ == "__main__":
    main()
