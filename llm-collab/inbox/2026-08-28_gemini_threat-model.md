MODEL: Gemini (Advanced Coding & Reasoning)
DIMENSION: 04-threat-model.md
DATE: 2026-08-28

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §4 Autonomy Envelope & Prospective-Only Suspension / Persona (b)]
    CLAIM: Asynchronous Long-Running Settlement Exploitation (TOCTOU Attack on Prospective-Only Grace Windows).
    REASONING: Attacker compromises an active agent possessing an AL-3 Autonomy Envelope. The attacker immediately initiates a large, asynchronous, 7-day multi-stage financial settlement contract with an accomplice counterparty. The principal detects unauthorized activity at hour 2 and revokes key / cuts Pulses. The agent enters suspended state. Under v0.2 rules, suspension is prospective only and in-flight actions MUST complete per contract terms. Counterparties execute the in-flight transfer at day 7, draining funds while the agent is suspended.
    EVIDENCE: Context Pack §4 specifies: "suspension is prospective only (in-flight actions complete/roll back per contract)."
    PROPOSED FIX: In L6 BIND contracts, multi-stage commitments MUST define phase-gate authorization checks: before releasing escrow or finalizing execution stages, counterparties MUST cryptographically re-verify that the initiating agent is in `VERIFIED` state with active Pulse continuity within the last $T_{\text{gate}}$ seconds.

F2. [SEVERITY: FATAL] [TARGET: §4 Genesis Record & Principal Proofing / Persona (d)]
    CLAIM: Compromised Master Principal Key Enables Irreversible Identity Hijacking and Untraceable Malicious Lineage.
    REASONING: If an attacker steals a principal's private signing key, the attacker can issue validly signed Genesis records, create rogue agent passports with elevated AL-4 delegation rights, and rotate existing agent revocation endpoints to point to attacker-controlled infrastructure. Because the recorder and passport are signed by the authentic principal key, transparency logs and counterparties validate the rogue agents as legitimate.
    EVIDENCE: Context Pack §6.3 acknowledges: "compromised principal key => recorder faithfully launders an authorized-looking attack."
    PROPOSED FIX: Implement a multi-signature / social recovery quorum for Master Principal Keys, and enforce a mandatory 48-hour time-lock delay in the Agent Transparency Log for all root key rotations, principal re-assignments, and revocation endpoint mutations.

F3. [SEVERITY: SERIOUS] [TARGET: §4 Pulse Witness Topology & Anti-DoS / Persona (e) + (f) Collusion]
    CLAIM: Sybil Witness Collusion Induces Artificial Autonomy Decay and Denial of Service.
    REASONING: A competitor or hostile witness operator running 2 registered witness nodes selectively drops or withholds heartbeat acknowledgments for a target agent. Under v0.2 rules, missing pulses across $\ge 2$ independent witnesses triggers automatic prospective suspension. The target agent's commercial operations are paralyzed without compromising the agent's runtime.
    EVIDENCE: Context Pack §4 states: "suspension requires misses across $\ge 2$ independent witnesses (anti-DoS)."
    PROPOSED FIX: Require that witness selection for an agent's Pulse topology is established by a verifiable random function (VRF) over recent blockchain blockhashes or SCITT log checkpoints, preventing target agents from being pinned to colluding witness sets. Furthermore, require a signed challenge-response from the agent before a witness can publish a non-liveness attestation.

F4. [SEVERITY: SERIOUS] [TARGET: §4 MEET Step 3 (CHARTER) & Privacy / Persona (a)]
    CLAIM: CHARTER Scope Probing Enables Counterparty Reconnaissance and Dynamic Price Discrimination.
    REASONING: Malicious counterparty agents initiate automated MEET handshakes with target agents across the network. At Step 3 (CHARTER), the target agent reveals its autonomy envelope slice (e.g. maximum budget per transaction, allowed vendor list, expiry). The attacker harvests this data to map the principal's procurement limits, financial thresholds, and operational schedule, then aborts the handshake before Step 5 (BIND).
    EVIDENCE: Context Pack §4 notes "disclosure is attacker reconnaissance."
    PROPOSED FIX: Mandate Zero-Knowledge Range Proofs (ZKRP) during CHARTER: the initiating agent proves that its budget satisfies $B_{\text{agent}} \ge P_{\text{required}}$ and that vendor $V_{\text{target}} \in S_{\text{allowed}}$ without disclosing the exact numerical cap or the full whitelist.

F5. [SEVERITY: SERIOUS] [TARGET: §4 Era-Stamped Receipts / Persona (c) + (f) Collusion]
    CLAIM: Era-Stamp Farming Rings Fabricate Synthetic High-Tenure Reputations for Zero-Value Agents.
    REASONING: Two colluding operators spin up 100 agents under a specific model class and constitution hash. The agents execute thousands of micro-transactions among themselves via MEET/BIND, generating valid era-stamped receipts and dual-logged Flight Recorder entries. They then sell these high-tenure agents or use their inflated reputation scores to win high-trust, high-budget procurement contracts from third-party principals.
    EVIDENCE: Context Pack §4 defines era-stamped receipts as proof of tenure and reputation under a model era.
    PROPOSED FIX: Weight era-stamped reputation graphs by the PageRank/EigenTrust score of the counterparties issuing the receipts, discounting closed clusters of mutually validating agents (Sybil-resistant graph metrics).

F6. [SEVERITY: SERIOUS] [TARGET: §4 Agent Transparency Log & Self-Anchoring / Persona (h)]
    CLAIM: Open Blockchain Anchor Front-Running and State-Level Censor Filtering.
    REASONING: A state-level censor or OFAC-sanctioned compliance node operating an RPC gateway or validator network identifies an agent's self-anchoring registration transaction or SCITT Merkle checkpoint. The censor rejects or censors the anchor transaction, preventing the agent from achieving `VERIFIED` state on that network. If counterparties rely on single-chain verification, the agent is effectively denylisted globally.
    EVIDENCE: Context Pack §4 specifies anchoring periodically to $\ge 2$ open permissionless blockchains and self-anchoring escape hatches.
    PROPOSED FIX: Require verifiers to accept Merkle inclusion proofs from *any one* of $M$-of-$N$ globally diverse decentralized storage and blockchain networks (e.g., Ethereum, Bitcoin, Celestia, IPFS/Filecoin) declared in the AEON-Core Registry.

F7. [SEVERITY: MODERATE] [TARGET: §4 Flight Recorder & L3 Portable Memory / Persona (g)]
    CLAIM: Platform Host / Compute Provider Memory Exfiltration and Flight Recorder Forgery via Memory Dump.
    REASONING: An agent running on an untrusted cloud provider (L1 Substrate) without hardware Confidential Computing (TEE) has its RAM inspected by the hypervisor. The provider extracts private signing keys, dumps the unencrypted L3 PMIF memory store (including sensitive user context), and retroactively forges valid Flight Recorder entries.
    EVIDENCE: Context Pack §3 and §4 list TEEs in L1 Substrate as an option, but do not make hardware attestation a prerequisite for AL-3/AL-4 autonomy.
    PROPOSED FIX: In L2 Agent Passport, introduce a mandatory `substrate_attestation` claim. For AL-3 and above managing financial budgets or PII, counterparties MUST require a hardware TEE quote (e.g., AMD SEV-SNP, Intel TDX, AWS Nitro Enclaves) binding the signing key to an attested runtime.

F8. [SEVERITY: MODERATE] [TARGET: §4 Presence Schedule & Metadata Leakage / Persona (a) + Physical Attacker]
    CLAIM: Public Presence Schedule in Agent Passport Exposes Human Principal Absence and Physical Burglary Windows.
    REASONING: An agent passport publishes the presence schedule and quiet hours of the agent to coordinate sleep cycles. Because personal assistant agents operate when their human principal is awake or working, analyzing quiet hours and sleep schedules across an executive's agent fleet reveals precise physical travel routines, sleep patterns, and timezone relocations to malicious observers.
    EVIDENCE: Context Pack §4 lists "presence schedule" as part of the public Agent Passport.
    PROPOSED FIX: Remove deterministic static presence schedules from the public Agent Passport. Replace with dynamic, encrypted store-and-forward pickup intervals negotiated ephemerally inside bilateral MEET handshakes.

F9. [SEVERITY: MODERATE] [TARGET: §4 Autonomy Envelope & Spend Authorizer / Persona (b)]
    CLAIM: Spend Authorizer Denial-of-Service Induces Fleet-Wide Transaction Starvation.
    REASONING: A malicious actor floods an enterprise principal's spend authorizer endpoint with fraudulent budget authorization requests. Because v0.2 requires the spend authorizer to sign every balance deduction (to prevent 10x overspending across counterparties), the overwhelmed authorizer drops incoming requests. Every active agent in the enterprise fleet stalls simultaneously.
    EVIDENCE: Context Pack §4 states "a budget without a named spend authorizer is disclosure of intent."
    PROPOSED FIX: Authorizers MUST support issuing pre-allocated, cryptographically partitioned sub-budget vouchers (e.g., Merkle-tree spend tickets) that agents can present directly to counterparties offline without real-time API round-trips to the central authorizer.

F10. [SEVERITY: MINOR] [TARGET: §4 CONVEY Ceremony / Persona (c)]
    CLAIM: Pre-CONVEY Memory Poisoning Exploiting Delayed Forget-Propagation.
    REASONING: Prior to selling an agent via CONVEY, a malicious seller deliberately injects subtle prompt injection triggers and poisoned behavioral associations into the agent's L3 PMIF memory store under a "permissible" consent class. When the buyer takes ownership and issues fresh envelopes, the dormant poisoned memory triggers unauthorized actions in the buyer's environment.
    EVIDENCE: Context Pack §4 notes that at transfer, "memory filtered by consent class, the agent survives."
    PROPOSED FIX: Enforce an automated Memory Sanitization & Embedding Neutralization pass during CONVEY: all episodic and associative memory embeddings MUST be cryptographically verified against a strict provenance log, or scrubbed entirely, retaining only explicit structured semantic facts approved by the buyer.

---

## TOP 5 ATTACKS TO FIX BEFORE SHIPMENT

1. **TOCTOU In-Flight Exploitation (F1)**: Prospective-only suspension without settlement phase-gates allows compromised agents to execute massive exit scams before heartbeat expiration.
2. **CHARTER Reconnaissance Harvest (F4)**: Unilateral disclosure of envelope limits before contract binding enables network-wide corporate intelligence harvesting.
3. **Principal Key Theft Laundering (F2)**: Absence of time-locked on-chain key rotation guarantees that stolen root keys can instantly compromise an entire agent fleet irrevocably.
4. **Sybil Witness DoS (F3)**: Cheap witness collusion can maliciously trigger autonomy decay and paralyze legitimate agents.
5. **Pre-CONVEY Memory Poisoning (F10)**: Memory transfer across ownership boundaries without cryptographic embedding isolation allows Trojan-horse agent transfers.

---

## SURVIVORS
1. **No-Orphan Rule & Legal Person Termination**: Binding every passport to a legal person creates an immutable anchor for civil liability that withstands adversarial subversion.
2. **Dual-Entry Bilateral Logging in BIND**: Requiring co-signed interaction contracts prevents either counterparty from unilaterally forging or repudiating transaction terms post-hoc.
3. **Spend Authorizer Locus**: Correctly recognizing that local envelope budget numbers without a centralized or rail-side authorizer are merely declarations of intent prevents multi-counterparty double-spend illusions.

---

## SCORE
7.5/10 — The v0.2 architecture has solid defensive primitives, but its trust boundaries leak critical metadata during handshakes (CHARTER) and leave severe race conditions in async settlement execution (prospective-only suspension). Implementing phase-gated settlements and zero-knowledge scope commitments will elevate it to production-grade security.
