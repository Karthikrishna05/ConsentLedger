# ConsentLedger — 2-Week Deadline Plan (MVP + paper)

Goal: a **working project + demo** and a **written paper** in ~2 weeks (college submission). Decision
context: DECISIONS.md **D19**. The full-rigor 26-week plan stays in the plan file for any later stronger
submission.

## Scope

**KEEP (fast, high-value):**
- NER **E1** (3 backbones on OPP-115 → small annotated AA test); **E2** if annotations land in time.
- Small AA gold test (~12 docs), light κ on ~4 double-annotated.
- T5 summarizer + **faithfulness metric** ← the paper's headline contribution.
- Blockchain: minimal `ConsentRegistry` + tests + Sepolia deploy + Etherscan verify.
- Integration `end_to_end.py` (one command) + demo + reproducible README.

**CUT / DEFER (slow, blocking):**
- IRB + formal user study + stats → **future work** (optional tiny informal, clearly-labeled pilot).
- Double-annotate-everything κ protocol → small double-annotated subset only.
- 3 seeds × everything → 1 seed (more only if time).

## Schedule (4 people, parallel)

**Week 1**
- **Days 1–3:** Annotation sprint (ALL 4) on ~12 AA docs (double-annotate ~4 for κ). ∥ P3 Solidity ∥
  P2 summary-pair generation ∥ P1 writes NER `dataset/train/evaluate`.
- **Days 4–7:** P1 runs E1 (+E2) → F1 table ∥ P2 trains T5 + builds faithfulness ∥ P3 deploys +
  verifies contract ∥ P4 starts integration + drafts paper Methods/Related Work.

**Week 2**
- **Days 8–10:** P4 end-to-end pipeline ∥ P2 faithfulness eval ∥ assemble results tables.
- **Days 11–13:** paper writing (all; P1 coordinates) + demo + reproducibility check.
- **Day 14:** buffer, polish, submit.

## Owners (from TEAM.md, deadline mode)
- **P1:** annotation #1 + NER E1/E2 + lead + paper coordination.
- **P2:** summary pairs + T5 + faithfulness metric.
- **P3:** blockchain + Sepolia deploy; then help annotate/integrate. (No user study in deadline mode.)
- **P4:** annotation #2 + integration pipeline + demo.

## Paper skeleton (write in parallel)
Intro · Related Work (cite Barnes 2024; privacy-policy NER; blockchain-consent) · Corpus (OPP-115
transfer + small AA gold) · Method (3-label transfer NER + **faithfulness metric** + on-chain registry)
· NER results (E1/E2 table) · Summarizer results (ROUGE/BERTScore + entity-preservation) · Contract
(gas + verified Sepolia address) · Limitations (small corpus; user study = future work; testnet-only) ·
Conclusion.

## Critical path
Annotation → NER eval → integration → results → paper. **Start annotation today.** Blockchain and
summarizer run fully in parallel and do not block the critical path.
