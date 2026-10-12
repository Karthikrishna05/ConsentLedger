
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ConsentRegistryTests(unittest.TestCase):
    def test_contract_source_contains_required_behaviour(self):
        """Basic offline check; does not deploy or execute the contract."""
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


if __name__ == "__main__":
    unittest.main()
