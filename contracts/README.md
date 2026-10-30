# ConsentRegistry

`contracts/ConsentRegistry.sol` stores a **fingerprint** (Keccak-256 hash) of each consent artefact, never
the artefact or any personal data, with its owner, expiry, nonce and status (CREATED → GRANTED → REVOKED).
Sepolia testnet only.

**Deployed:** [`0x2De2051bAb111580a0F0C850E7C8318b94aAA4bF`](https://sepolia.etherscan.io/address/0x2De2051bAb111580a0F0C850E7C8318b94aAA4bF#code)
on Sepolia (source verified on Etherscan).

## Functions
| Function | Who | What |
|---|---|---|
| `createConsent(hash, expiry, nonce)` | anyone | Creates a record; the id is `keccak256(sender, hash, nonce)`, so nobody can take another owner's id. |
| `grantConsent(id)` | owner | CREATED → GRANTED. |
| `revokeConsent(id)` | owner | Revokes a created or granted consent. |
| `isValid(id, hash)` | anyone (view) | True if granted, not expired and the hash matches. |
| `recordAccess(id, hash)` | anyone | Same check, plus an `AccessRecorded` audit event (who asked, valid or not). |
| `consentIdFor(owner, hash, nonce)` / `consents(id)` | anyone (view) | Look up an id / a record. |

## Settings
Copy `../.env.example` to `../.env` (project root, git-ignored); Hardhat and the Python both read it.

| Variable | Needed for |
|---|---|
| `SEPOLIA_RPC_URL` | everything on-chain (read-only checks need only this) |
| `SEPOLIA_PRIVATE_KEY` | sending transactions (use a throwaway test wallet) |
| `ETHERSCAN_API_KEY` | `hardhat verify` |
| `CONSENT_REGISTRY_ADDRESS` | optional on Sepolia (default: `ignition/deployments/chain-11155111/`); required on a local chain |

## Build and test
```shell
npm ci
npx hardhat build                                # compile
npx hardhat test                                 # 10 contract tests (local, offline)
python -m pytest contracts/test/test_registry.py # Python client tests (from the project root)
```

## Deploy to Sepolia and verify
```shell
npx hardhat ignition deploy ignition/modules/ConsentRegistry.ts --network sepolia
npx hardhat verify --network sepolia <DEPLOYED_ADDRESS>
```
The deployment used the `production` profile (optimizer on, 200 runs). Commit
`ignition/deployments/chain-11155111/` (addresses and ABI only, never the key); the Python reads the address
from there.

Gas measured on Sepolia: create 459,911 · grant 31,603 · recordAccess 25,051 · revoke 31,734. These are
higher than a local Hardhat node reports, so quote the Sepolia figures.

## Use from Python (project root, venv active)
```shell
python -m consentledger.chain.register_consent                       # registers data/aa/consent_artefacts/demo_consent.json
python -m consentledger.chain.read_consent --consent-id <id> --file <json> [--record]
python -m consentledger.chain.revoke_consent --consent-id <id> [--yes]
```
The pipeline calls `register()`, `check()`, `record_access()` and `revoke()` from these `consentledger.chain` modules.

## Local practice chain
Run `npx hardhat node` in one terminal and
`npx hardhat ignition deploy ignition/modules/ConsentRegistry.ts --network localhost` in another. Then run the
Python with `SEPOLIA_RPC_URL=http://127.0.0.1:8545`, `SEPOLIA_PRIVATE_KEY` = account #0's key from the node
output and `CONSENT_REGISTRY_ADDRESS` = the printed address. Only Sepolia (11155111) and the local chain
(31337) are accepted; any other network is refused.
