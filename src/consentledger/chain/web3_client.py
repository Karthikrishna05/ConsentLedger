
"""web3.py v6 connection to Sepolia (or a local Hardhat chain) + a loaded ConsentRegistry contract object."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

# Project root: ConsentLedger/
ROOT = Path(__file__).resolve().parents[3]

# Load the project's .env file without overriding existing environment variables.
load_dotenv(ROOT / ".env")

SEPOLIA, LOCAL = 11155111, 31337
EXPLORER = {SEPOLIA: "https://sepolia.etherscan.io/tx/"}


def get_web3() -> Web3:
    """Connect only to Sepolia or the local Hardhat chain."""
    rpc_url = os.environ.get("SEPOLIA_RPC_URL")

    if not rpc_url:
        raise RuntimeError(
            "SEPOLIA_RPC_URL is missing. Set it in the project's .env file."
        )

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise ConnectionError("Cannot reach the RPC. Check SEPOLIA_RPC_URL.")

    if w3.eth.chain_id not in (SEPOLIA, LOCAL):
        raise RuntimeError(
            f"Chain {w3.eth.chain_id} refused: only Sepolia "
            f"({SEPOLIA}) or local Hardhat ({LOCAL})."
        )

    return w3


def get_account(w3: Web3):
    """Load the dedicated test wallet account."""
    private_key = os.environ.get("SEPOLIA_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError(
            "SEPOLIA_PRIVATE_KEY is missing. Set it in the project's .env file."
        )

    return w3.eth.account.from_key(private_key)


def get_contract(w3: Web3):
    """Load the ConsentRegistry ABI and connect to its deployed address.

    Uses CONSENT_REGISTRY_ADDRESS when explicitly configured.
    Otherwise, loads the recorded Ignition deployment on Sepolia.
    """
    address = os.environ.get("CONSENT_REGISTRY_ADDRESS")
    chain_id = w3.eth.chain_id

    # Without an explicit address, only use the recorded Sepolia deployment.
    if not address:
        if chain_id != SEPOLIA:
            raise RuntimeError(
                "No ConsentRegistry address: set CONSENT_REGISTRY_ADDRESS "
                "in the project's .env file."
            )

        deployment_file = (
            ROOT
            / "contracts"
            / "ignition"
            / "deployments"
            / f"chain-{chain_id}"
            / "deployed_addresses.json"
        )

        if deployment_file.is_file():
            deployment_data = json.loads(
                deployment_file.read_text(encoding="utf-8")
            )
            address = deployment_data.get(
                "ConsentRegistryModule#ConsentRegistry"
            )

    if not address:
        raise RuntimeError(
            "No ConsentRegistry address: set CONSENT_REGISTRY_ADDRESS "
            "in the project's .env file."
        )

    abi_path = ROOT / "contracts" / "ConsentRegistry.abi.json"

    if not abi_path.is_file():
        raise FileNotFoundError(f"Contract ABI not found: {abi_path}")

    abi = json.loads(abi_path.read_text(encoding="utf-8"))

    return w3.eth.contract(
        address=Web3.to_checksum_address(address),
        abi=abi,
    )


def explorer_link(w3: Web3, tx_hash) -> str | None:
    """Return a public transaction link, or None for a local chain."""
    base = EXPLORER.get(w3.eth.chain_id)

    if not base:
        return None

    tx_hash_hex = (
        tx_hash if isinstance(tx_hash, str) else Web3.to_hex(tx_hash)
    )

    return base + tx_hash_hex


def send(w3: Web3, acct, fn):
    """Sign and send a transaction with explicit gas estimation."""
    tx_params = {"from": acct.address}

    # Estimate gas and add a 20% safety buffer.
    estimated_gas = fn.estimate_gas(tx_params)
    gas_limit = estimated_gas + estimated_gas // 5

    tx = fn.build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(
                acct.address, "pending"
            ),
            "chainId": w3.eth.chain_id,
            "gas": gas_limit,
        }
    )

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError(f"Transaction failed: {tx_hash.hex()}")

    return receipt
