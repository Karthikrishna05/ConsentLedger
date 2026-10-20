# ConsentRegistry — the on-chain consent record (P3)

`contracts/ConsentRegistry.sol` stores a **fingerprint** (Keccak-256 hash) of each consent artefact — never
the artefact or any personal data — with its owner, expiry and status (CREATED → GRANTED → REVOKED).
Anyone can check a document against it; `recordAccess` leaves an audit entry saying who checked and whether
the document was valid. The consent id is computed by the contract from the owner's address, the hash and
a nonce, so nobody can take someone else's id. Sepolia testnet only.

## Settings
One file for the whole project: copy `../.env.example` to `../.env` (project root, git-ignored) and fill in
`SEPOLIA_RPC_URL`, `SEPOLIA_PRIVATE_KEY` (a throwaway test wallet) and `ETHERSCAN_API_KEY`. Hardhat and the
Python both read it. The Python finds the contract address in `ignition/deployments/chain-<id>/` by itself;
`CONSENT_REGISTRY_ADDRESS` overrides it. Read-only checks (`check()`) need only the RPC URL, no key.

## Test
```shell
npm ci
npx hardhat test                                         # 10 contract tests
python -m pytest test/test_registry.py                   # the Python helpers (from the project root: contracts/test/...)
```

## Deploy to Sepolia and verify
```shell
npx hardhat ignition deploy ignition/modules/ConsentRegistry.ts --network sepolia
npx hardhat verify --network sepolia <DEPLOYED_ADDRESS>
```
Commit `ignition/deployments/chain-11155111/` (addresses and ABI only — never the key); the Python reads the
address from there. **Deployed:** `0x2De2051bAb111580a0F0C850E7C8318b94aAA4bF` on Sepolia (18 Oct 2026).
Gas measured on Sepolia: create 459,911 · grant 31,603 · recordAccess 25,051 · revoke 31,734. Creating a
consent costs about 4x the local simulator's figure, most likely because Sepolia now prices new storage
higher (EIP-8037); quote Sepolia's numbers.

## Use from Python (project root, venv active)
```shell
python -m consentledger.chain.register_consent                       # registers data/aa/consent_artefacts/demo_consent.json
python -m consentledger.chain.read_consent --consent-id <id> --file <json> [--record]
python -m consentledger.chain.revoke_consent --consent-id <id> [--yes]
```
`register()`, `check()`, `record_access()` and `revoke()` are the functions the pipeline calls.

## Try it on a local practice chain first
In one terminal `npx hardhat node`; in another `npx hardhat ignition deploy ignition/modules/ConsentRegistry.ts
--network localhost`, then run the Python with `SEPOLIA_RPC_URL=http://127.0.0.1:8545`,
`SEPOLIA_PRIVATE_KEY` = account #0's key from the node's output, and the printed address. Only Sepolia and the
local chain (31337) are accepted; any other network is refused.
