
"""web3.py v6 connection to Sepolia + a loaded ConsentRegistry contract object."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

# Project root: ConsentLedge/
ROOT = Path(__file__).resolve().parents[3]

# Load environment variables from the project root.
load_dotenv(ROOT / ".env.local", override=True)

def get_web3() -> Web3:
    """Connect to the Sepolia Ethereum test network."""
    rpc_url = os.environ.get("SEPOLIA_RPC_URL")

    if not rpc_url:
        raise RuntimeError(
            "SEPOLIA_RPC_URL is missing. Configure it in the project .env file."
        )

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise ConnectionError(
            "Cannot reach Sepolia RPC. Check SEPOLIA_RPC_URL."
        )

    return w3


def get_account(w3: Web3):
    """Load the dedicated test wallet account."""
    private_key = os.environ.get("TEST_WALLET_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError(
            "TEST_WALLET_PRIVATE_KEY is missing from the project .env file."
        )

    return w3.eth.account.from_key(private_key)


def get_contract(w3: Web3):
    """Load the ABI and connect to the deployed ConsentRegistry."""
    address = os.environ.get("CONSENT_REGISTRY_ADDRESS")

    if not address:
        raise RuntimeError(
            "CONSENT_REGISTRY_ADDRESS is missing from the project .env file."
        )

    abi_path = ROOT / "contracts" / "ConsentRegistry.abi.json"

    if not abi_path.is_file():
        raise FileNotFoundError(f"Contract ABI not found: {abi_path}")

    abi = json.loads(abi_path.read_text(encoding="utf-8"))

    return w3.eth.contract(
        address=Web3.to_checksum_address(address),
        abi=abi,
    )



def send(w3: Web3, acct, fn):
    """Sign and send a transaction with explicit gas estimation."""
    tx_params = {
        "from": acct.address,
    }

    # Estimate gas before building the transaction.
    estimated_gas = fn.estimate_gas(tx_params)
    gas_limit = estimated_gas + estimated_gas // 5  # 20% buffer

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
        raise RuntimeError(
            f"Transaction failed: {tx_hash.hex()}"
        )

    return receipt
