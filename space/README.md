---
title: ConsentLedger
emoji: 🔏
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.17.3
python_version: "3.11"
app_file: app.py
pinned: false
short_description: What an Account Aggregator policy says, checked and sealed
---

# ConsentLedger — demo

Paste an Indian **Account Aggregator (AA)** policy, or upload it, and optionally the consent artefact you are
asked to grant. The demo shows:

- **what the policy mentions** — your data, purposes and who it is shared with, with anything the policy
  promises *not* to do marked in red;
- **a plain-language summary of each passage**, checked automatically against the passage — if a summary
  reverses a meaning, names the wrong party or invents a name, it is withheld and the passage's facts are shown
  instead; if it leaves facts out, they are listed under it;
- **the consent's terms** in plain words (who receives the data, why, for how long, how often);
- **a fingerprint** of the policy's facts and the consent together, which can be recorded on the Ethereum
  **Sepolia test network**, and a tab to check a recorded consent later — change one word and the check fails.

**Research prototype, research use only.** The models were trained partly on the OPP-115 corpus
(CC BY-NC 4.0). Summaries are machine-written; the automatic check catches some errors but not all, so read
the passage when it matters. This is not legal advice. Do not paste personal data. The blockchain is a test
network: nothing here has monetary value.

## For maintainers
Hosting a Gradio Space requires a Hugging Face PRO subscription (since 2026; free accounts get a 402 error).
Built from the project repository with `python space/build.py` (it copies only the app, the package code, the
demo consent, and the contract's address and ABI — no scraped documents, no annotations, no keys).
Settings → *Variables and secrets*:

| Secret | Needed for |
|---|---|
| `HF_TOKEN` | downloading the private models (a **read** token) |
| `SEPOLIA_RPC_URL` | the "Check a recorded consent" tab |
| `SEPOLIA_PRIVATE_KEY` | optional: recording on-chain (a throwaway test wallet only; at most 20 writes per restart) |

On the free CPU hardware the first start downloads the models (~1.6 GB) and a long policy takes a minute or two.
