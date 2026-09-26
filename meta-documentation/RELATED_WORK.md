# Related Work & Systematic Novelty Search

**Purpose.** Evidence base for the paper's contribution claims, and the record behind the phrase
"to the best of a systematic search". Run because P1 observed (while annotating) that the RBI AA
framework *already* mandates standardized consent artefacts that are "logged, audited, and verified" —
raising the question of whether ConsentLedger is novel at all. **Short answer: two of the three pillars
are not novel. One is.** Details below.

---

## 1. Search protocol

| Item | Value |
|---|---|
| **Date run** | 2026-09-24 |
| **Indexes** | Academic paper index spanning **arXiv**, **PubMed/PMC**, bioRxiv/medRxiv and other scientific sources (via Firecrawl research tools); plus general web search for grey literature/regulatory text |
| **Results per query** | k = 30 (ranked, with relevance scores) |
| **Screening** | Title + abstract read; retained if it overlapped a ConsentLedger pillar |

**Queries run (verbatim):**
1. `Account Aggregator India RBI consent artefact natural language processing financial data sharing consent document extraction`
2. `privacy policy named entity recognition span extraction OPP-115 transfer learning domain adaptation legal BERT`
3. `summarization faithfulness entity preservation factual consistency metric legal privacy policy plain language summary`
4. `blockchain smart contract consent management personal data auditability revocation hash on-chain registry`
5. (web) `blockchain consent management GDPR smart contract survey systematic review`
6. (web) `"Account Aggregator" India consent NLP machine learning research paper RBI`

**⚠ Limitation (must be stated if this is cited).** This search covered arXiv + PubMed/PMC + general web.
It did **not** cover ACL Anthology, Scopus, IEEE Xplore, ACM DL, or Google Scholar directly. Several
relevant venues (ACL/EMNLP/PoPETs/CHI) are only partially represented. Re-run queries 1–4 in those
databases before final submission; treat the current result as **strong but not exhaustive** evidence.

---

## 2. Pillar-by-pillar findings

### 2.1 🟢 Indian AA consent-document NLP — **GAP CONFIRMED (our contribution)**

Query 1 returned **no paper on the Account Aggregator framework at all.** Top relevance was 0.49, and
every high-ranked hit was generic financial NLP unrelated to consent documents (payment NER, KYC
processing, PII detection in financial docs, FinTech NLP surveys). The general web search likewise
returned only regulatory/industry material (CGAP, law firms, IIBF, Infosys) — no research.

**Nearest neighbours (cite as adjacent, not overlapping):**
- *Machine learning-based donor permission extraction from informed consent documents* — [PMC10724888](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10724888/). NLP over **biomedical informed-consent** documents. Closest "NLP on consent documents" work; different domain, different ontology.
- *Consent verification monitoring* — [arXiv:2206.06406](https://arxiv.org/abs/2206.06406). Formal framework for consent granting/withdrawal and policy evolution under GDPR. Formal-methods, not NLP.
- *LADFA: LLMs + RAG for Personal Data Flow Analysis in Privacy Policies* — [arXiv:2601.10413](https://arxiv.org/abs/2601.10413).
- *Decoding the Legalese* — [arXiv:2609.26680](https://arxiv.org/abs/2609.26680). LLM structuring of 10,000 privacy policies.
- Indian-fintech NLP exists but not on consent: *FiMI Banking* [arXiv:2609.03960](https://arxiv.org/abs/2609.03960); *RBI-approved P2P lending app reviews* [PMC12832989](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12832989/).

**Verdict:** the AA **gold corpus + transfer benchmark** is genuinely first. This is the paper's contribution.

### 2.2 🟡 Privacy-policy NER / domain adaptation — **METHOD ESTABLISHED, DOMAIN NEW**

Active, mature field. Our *method* (E1 vs E2 domain-adaptation ablation across backbones) has direct
precedent; only the target domain is new.

- *PLUE: Language Understanding Evaluation Benchmark for Privacy Policies* — [arXiv:2212.10011](https://arxiv.org/abs/2212.10011). Multi-task privacy-policy benchmark + domain-specific continual pretraining. **Closest benchmark.**
- *EURO-5K: When Does Domain Pretraining Matter?* — [arXiv:2606.02971](https://arxiv.org/abs/2606.02971). Generic vs Legal-BERT on EU reporting-obligation extraction, learning curves, cross-dataset eval. **Almost exactly our ablation design, on EU legislation.**
- *Beyond The Text: Privacy Statements via Syntactic & Semantic Role Labeling* — [arXiv:2010.00678](https://arxiv.org/abs/2010.00678). Extracting privacy *parameters* from policies.
- *Enabling Multilingual Privacy Policy Audits* — [arXiv:2607.18424](https://arxiv.org/abs/2607.18424). Uses **both OPP-115 and MAPP**; LLM classifier for data-collection categories (classification, not span NER).
- *Automating GKC-CI Privacy Policy Annotations with LLMs* — [arXiv:2311.02192](https://arxiv.org/abs/2311.02192).
- *Privacy Policy Coverage Analysis* (OPP-115 segment classification) — [arXiv:2003.04972](https://arxiv.org/abs/2003.04972).
- *LegNER* — [PMC12631292](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12631292/); *CrossNER* — [arXiv:2012.04373](https://arxiv.org/abs/2012.04373); *Cross-domain NER via Graph Matching* — [arXiv:2408.00981](https://arxiv.org/abs/2408.00981); *Domain Adaptation from Scratch* — [arXiv:2209.00830](https://arxiv.org/abs/2209.00830).

**Verdict:** claim **domain novelty only**. Do not claim a methodological advance.

### 2.3 🔴 Summarization faithfulness / entity preservation — **DIRECT PRIOR ART**

- **⚠ *EROS: Entity-Driven Controlled Policy Document Summarization*** — [arXiv:2403.00141](https://arxiv.org/abs/2403.00141). **The closest paper to P2.** Controlled abstractive summarization of *privacy policy documents*, enforcing inclusion of critical privacy entities (data, medium, target, reason) via a **span-based entity extraction model** + PPO; introduces the PD-Sum dataset. **Must cite and differentiate explicitly.**
- *APPSI-139* — [arXiv:2604.27550](https://arxiv.org/abs/2604.27550). Expert-annotated privacy-policy summarization/interpretation corpus (139 policies, 36,351 labels) + TCSI-pp-V2.
- *Entity-level Factual Consistency of Abstractive Text Summarization* — [arXiv:2102.09130](https://arxiv.org/abs/2102.09130). **Canonical source of the entity-level precision/recall metrics our faithfulness audit uses.**
- *Entity Coverage Control* — [arXiv:2207.02263](https://arxiv.org/abs/2207.02263); *Entity-based SpanCopy* — [arXiv:2209.03479](https://arxiv.org/abs/2209.03479).
- *FFCI* (faithfulness/focus/coverage framework) — [arXiv:2011.13662](https://arxiv.org/abs/2011.13662); *SWING* (coverage vs faithfulness) — [arXiv:2301.10483](https://arxiv.org/abs/2301.10483); *FactKB* — [arXiv:2305.08281](https://arxiv.org/abs/2305.08281).
- Plain-language factuality: *APPLS* — [arXiv:2305.14341](https://arxiv.org/abs/2305.14341); *PlainQAFact* — [arXiv:2503.08890](https://arxiv.org/abs/2503.08890); *FactPICO* — [arXiv:2402.11456](https://arxiv.org/abs/2402.11456).
- *Helping Johnny Make Sense of Privacy Policies with LLMs* — [CHI 2026](https://dl.acm.org/doi/10.1145/3772318.3791465). Catalogues hallucination in LLM privacy-policy explanation.
- Indian legal summarization precedent: [arXiv:2602.07382](https://arxiv.org/abs/2602.07382).

**Verdict:** the metric is **not novel**. Our only defensible difference: EROS uses entities to *control
generation*; we use them to *audit a disclosure against a regulatory obligation* in the AA domain.

### 2.4 🔴 Blockchain consent registry — **COMPREHENSIVELY DONE. CLAIM NOTHING.**

Every design element of our contract has published precedent:

- **⚠ *Soteria: A Provably Compliant User Right Manager*** — [arXiv:2003.10128](https://arxiv.org/abs/2003.10128). Stores an **indelible audited trail of the hash of data access and sharing agreements** on a ledger, supports revocation, proves GDPR/CCPA compliance. **This is our contract's core idea, published.**
- **⚠ *Grant, Verify, Revoke: A User-Centric Pattern for Blockchain Compliance*** — [arXiv:2603.15721](https://arxiv.org/abs/2603.15721). Our create→grant→revoke lifecycle is a **named pattern** in the literature.
- *A Smart Contract-Based Dynamic Consent Management System under GDPR* — [PMC8659597](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8659597/).
- *Blockchain-Based Dynamic and Revocable Consent: Systematic Review* — [PMC13287375](https://pmc.ncbi.nlm.nih.gov/articles/PMC13287375/) (PRISMA, 55 studies).
- *A Survey of Blockchain-Based Privacy Applications* — [arXiv:2411.16404](https://arxiv.org/abs/2411.16404); *GDPR Compliant Blockchains SLR* — [arXiv:2104.00648](https://arxiv.org/pdf/2104.00648) (names **financial data** as an established domain).
- *Consentio* — [arXiv:1910.07110](https://arxiv.org/abs/1910.07110); *OConsent* — [arXiv:2201.01326](https://arxiv.org/abs/2201.01326); *GDPR-Compliant Personal Data Management* — [arXiv:1904.03038](https://arxiv.org/abs/1904.03038); *Design & Implementation of a Blockchain-based Consent Management System* — [arXiv:1912.09882](https://arxiv.org/abs/1912.09882); *A Consent Model for Blockchain-based Data Sharing* — [arXiv:2007.04847](https://arxiv.org/abs/2007.04847); *ConsentChain* — [PMC8600428](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8600428/).
- Conceptual prior art already in the plan: Barnes et al. 2024, *AJOB* 25(4), DOI `10.1080/15265161.2024.2416117`.

**Verdict:** P3 is a **reference implementation**, not a contribution. Saying otherwise invites rejection.

---

## 3. Required differentiation statements (write these into the paper)

| Near neighbour | What we must say |
|---|---|
| **EROS** (arXiv:2403.00141) | "EROS uses privacy entities to *control generation* on English web privacy policies; we use entity preservation as a *post-hoc audit* of disclosure fidelity in the Indian AA consent domain, against a specific regulatory obligation." |
| **Soteria** / **Grant-Verify-Revoke** | "Hash-anchored, revocable consent registries are established. Our contract is a reference implementation for the AA artefact schema, not a novel mechanism." |
| **PLUE / EURO-5K** | "These establish privacy/legal domain-adaptation benchmarking. We apply the same paradigm to a domain with no prior resource: RBI AA consent documents." |
| **Entity-level Factual Consistency** (arXiv:2102.09130) | Cite as the **source** of our coverage/hallucination metric. Do not present it as ours. |
| **Multilingual Privacy Policy Audits** (arXiv:2607.18424) | "Uses OPP-115/MAPP for multilingual *classification*; we use OPP-115 for *span-level transfer* into a new domain." |
| **RBI NBFC-AA Master Direction** | Cite the mandate directly — it motivates the gap (disclosure is required; disclosure *fidelity* is unverified). |

---

## 4. Revised contribution claims (supersedes earlier framing)

**Position the paper as a RESOURCE + APPLICATION study, not a methods paper.**

> *First gold-annotated corpus and cross-domain transfer benchmark for Indian RBI Account Aggregator
> consent documents, with a reference pipeline demonstrating extraction → summary faithfulness auditing
> → on-chain anchoring.*

**Claim (defensible):**
1. First gold-annotated **AA consent corpus** + released annotation guideline (κ reported).
2. First **transfer/adaptation benchmark** (E1 vs E2) for privacy NER into the AA domain.
3. A **reference pipeline** tying extraction → disclosure-fidelity audit → tamper-evident anchoring,
   motivated by a gap the Master Direction leaves open (it mandates informing the user, not verifying
   the fidelity of that informing).

**Do NOT claim:**
- ❌ Novel blockchain consent mechanism (Soteria; Grant-Verify-Revoke; 55-study review).
- ❌ Novel faithfulness/entity-preservation metric (arXiv:2102.09130; EROS).
- ❌ "First system to record consent on-chain" — false.
- ❌ Any pre-stated numeric result, or unqualified "first/novel" without the systematic-search hedge.

**Realistic venue:** workshop / short paper (consistent with the original plan). The corpus is the
contribution; the pipeline is the demonstration.

---

*Search run 2026-09-24. Re-run queries 1–4 in ACL Anthology, Scopus, IEEE Xplore and ACM DL before
submission — see the limitation in §1.*
