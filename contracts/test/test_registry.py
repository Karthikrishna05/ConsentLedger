
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from consentledger.chain.web3_client import send


class ConsentRegistryTests(unittest.TestCase):
    def test_contract_source_contains_required_behaviour(self):
        """Check that the Solidity source contains required functions."""
        source_path = ROOT / "contracts" / "contracts" / "ConsentRegistry.sol"
        source = source_path.read_text(encoding="utf-8")

        required = [
            "function createConsent(",
            "function grantConsent(",
            "function revokeConsent(",
            "function recordAccess(",
            "function isValid(",
            "c.artefactHash == presentedHash",
            "c.status == Status.GRANTED",
            "c.status = Status.REVOKED",
        ]

        for item in required:
            with self.subTest(required=item):
                self.assertIn(item, source)

    def test_abi_contains_required_functions(self):
        """Check the ABI file without requiring a network connection."""
        abi_path = ROOT / "contracts" / "ConsentRegistry.abi.json"
        abi = json.loads(abi_path.read_text(encoding="utf-8"))

        names = {
            item.get("name")
            for item in abi
            if item.get("type") == "function"
        }

        required = {
            "createConsent",
            "grantConsent",
            "revokeConsent",
            "recordAccess",
            "isValid",
            "consents",
        }

        self.assertTrue(required.issubset(names))

    def make_send_mocks(self, receipt_status=1):
        """Prepare mock objects for testing the send() helper."""
        w3 = Mock()
        account = Mock()
        function = Mock()

        w3.eth.chain_id = 11155111
        w3.eth.get_transaction_count.return_value = 7
        w3.eth.send_raw_transaction.return_value = SimpleNamespace(
            hex=lambda: "0xtesttransaction"
        )
        w3.eth.wait_for_transaction_receipt.return_value = SimpleNamespace(
            status=receipt_status
        )

        function.estimate_gas.return_value = 100
        function.build_transaction.return_value = {"to": "0x1234"}

        account.address = "0xTestAccount"
        account.sign_transaction.return_value = SimpleNamespace(
            raw_transaction=b"signed-transaction"
        )

        return w3, account, function

    def test_send_successfully_builds_and_sends_transaction(self):
        """Check gas buffer, nonce, signing, and successful receipt."""
        w3, account, function = self.make_send_mocks()

        receipt = send(w3, account, function)

        self.assertEqual(receipt.status, 1)
        function.estimate_gas.assert_called_once_with(
            {"from": account.address}
        )

        built_params = function.build_transaction.call_args.args[0]
        self.assertEqual(built_params["gas"], 120)
        self.assertEqual(built_params["nonce"], 7)
        self.assertEqual(built_params["chainId"], 11155111)

        account.sign_transaction.assert_called_once()
        w3.eth.send_raw_transaction.assert_called_once_with(
            b"signed-transaction"
        )
        w3.eth.wait_for_transaction_receipt.assert_called_once()

    def test_send_raises_error_when_transaction_fails(self):
        """Check that a failed blockchain transaction raises an error."""
        w3, account, function = self.make_send_mocks(receipt_status=0)

        with self.assertRaisesRegex(RuntimeError, "Transaction failed"):
            send(w3, account, function)


if __name__ == "__main__":
    unittest.main()
