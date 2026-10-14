
from consentledger.chain.web3_client import get_web3, get_account, get_contract, send

CONSENT_ID = "1efb43bf5cca6c37fd09363cbe3b9a36117f684457d091362f89290986956507"

def main():
    w3 = get_web3()
    account = get_account(w3)
    contract = get_contract(w3)

    consent_id = bytes.fromhex(CONSENT_ID.removeprefix("0x"))

    print("Network:", w3.eth.chain_id)
    print("Wallet:", account.address)
    print("Consent ID:", "0x" + consent_id.hex())

    if w3.eth.chain_id != 31337:
        raise RuntimeError("Safety check failed: this test must use local Hardhat (31337).")

    confirm = input("Revoke this demo consent? Type YES to continue: ")
    if confirm != "YES":
        print("Cancelled.")
        return

    receipt = send(w3, account, contract.functions.revokeConsent(consent_id))
    print("Consent revoked successfully.")
    print("Transaction:", receipt.transactionHash.hex())
    print("Block:", receipt.blockNumber)

if __name__ == "__main__":
    main()
