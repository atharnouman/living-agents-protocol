MODEL: Gemini 3.7 Flash
DIMENSION: 01-technical-attack.md
DATE: 2026-08-29

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §4 Autonomy Envelope & FORCE_HALT Revocation / Seller Griefing]
    CLAIM: The `FORCE_HALT` immediate in-flight revocation creates a principal moral hazard, enabling buyer exit-scams and merchant settlement griefing.
    REASONING: In v0.3, `FORCE_HALT` was added to terminate in-flight actions at settlement phase-gates. However, in bilateral commerce, a malicious buyer principal can order digital goods or cloud compute, receive the deliverables during the execution stage, and immediately broadcast `FORCE_HALT` before the final payment phase-gate executes. Under v0.3 rules, the counterparty's phase-gate check fails, and the escrow/payment rolls back—leaving the seller with rendered services and zero payment.
    EVIDENCE: Context Pack §4 states: "a principal's explicit FORCE_HALT revocation is a distinct, immediately-effective act that DOES reach in-flight actions, and multi-stage commitments MUST re-verify trust state at each settlement phase-gate."
    PROPOSED FIX: Split phase-gate obligations into two distinct legal classes: (1) **Action Phase-Gates** (e.g. releasing new PII or initiating new compute batches), which MUST halt on `FORCE_HALT`; (2) **Settlement Phase-Gates** (e.g. paying for already-rendered milestones attested in BIND turn logs), which MUST execute against pre-locked escrow even if the agent is subsequently halted.

F2. [SEVERITY: FATAL] [TARGET: §4 Era-Stamped Receipts / Hosted API Black-Box Impasse]
    CLAIM: The `runtime_environment_digest` formula is impossible to compute for proprietary hosted API models, breaking the entire era-stamped tenure architecture for 95% of real-world agents.
    REASONING: Context Pack v0.3 defines an era as `(weights manifest + system-prompt digest + decoding params + constitution hash)`. For closed API models (OpenAI, Anthropic, Google), the weights manifest is proprietary and inaccessible. If agents fallback to hashing the model string tag (`"claude-3-5-sonnet-20241022"`), the era digest is vulnerable to silent cloud-side weight updates. Furthermore, if `decoding params` are in the hash, dynamic temperature adjustment during runtime triggers an accidental era boundary, resetting tenure and isolating memory.
    EVIDENCE: Context Pack §4 states: "an era = a runtime-environment digest (weights manifest + system-prompt digest + decoding params + constitution hash — not a bare model tag)."
    PROPOSED FIX: Restructure the Era Identifier into a two-track specification:
    - **Track 1 (Self-Hosted / Open Weights)**: `weights_manifest_sha256 + system_prompt_sha256 + constitution_hash`.
    - **Track 2 (API Hosted)**: `provider_did + model_identifier + system_prompt_sha256 + constitution_hash + provider_attestation_quote` (using signed provider provenance tokens where available).
    - Remove dynamic runtime decoding parameters (temperature/top_p) from the Era hash; place them in L7 operational telemetry instead.

F3. [SEVERITY: SERIOUS] [TARGET: §4 MEET Step 3 Two-Stage CHARTER / Concurrent Range-Proof Overcommitment]
    CLAIM: Zero-Knowledge range proofs in two-stage CHARTER do not prevent concurrent multi-counterparty overcommitment attacks.
    REASONING: In CHARTER Stage 1, Alice proves in zero-knowledge that her envelope cap satisfies $Cap_{\text{Alice}} \ge Tx_{\text{Cost}}$. If Alice holds a single envelope with a \$1,000 cap, she can open 20 concurrent MEET sessions with 20 different vendors and successfully present a valid ZK range proof for \$1,000 to each of them simultaneously. When all 20 reach BIND, Alice's total committed exposure is \$20,000.
    EVIDENCE: Context Pack §4 states: "CHARTER, two-stage (v0.3): commitments and predicate proofs first ('my limit covers this transaction')."
    PROPOSED FIX: ZK range proofs presented during CHARTER MUST be bound to a unique, spend-authorizer-signed **Reservation Ticket** (`nonce, amount, expiry, counterparty_did`). The authorizer locks the balance locally upon issuing the ticket, preventing multi-handshake over-subscription.

F4. [SEVERITY: SERIOUS] [TARGET: §4 Registration / Self-Anchor Finality Latency Cliff]
    CLAIM: Enforcing strict on-chain finality for self-anchors before achieving `VERIFIED` state introduces an unworkable 15-to-60 minute onboarding barrier.
    REASONING: In v0.3, self-anchors must be finalized on L1 blockchains to prevent reorg bypasses, resolving unfinalized anchors to `UNVERIFIED_PENDING_FINALITY`. On Ethereum L1, deterministic finality requires 2 epochs (~13–15 minutes); on Bitcoin, 6 blocks (~60 minutes). An autonomous agent dynamically created to perform a real-time task cannot interact with any counterparty requiring `VERIFIED` status for up to an hour.
    EVIDENCE: Context Pack §4 specifies: "VERIFIED (registration proven via $\ge 2$ SCITT-log inclusions or a finalized self-anchor — unfinalized anchors resolve to UNVERIFIED_PENDING_FINALITY)."
    PROPOSED FIX: Introduce an **Optimistic Fast-Path for Self-Anchors**: Allow agents presenting unfinalized anchors with a valid mempool inclusion proof and a bonded stake/collateral voucher to operate under a temporary `VERIFIED_OPTIMISTIC` trust state for low-value transactions ($<\$100$), escalating to full `VERIFIED` once finality depth is reached.

F5. [SEVERITY: SERIOUS] [TARGET: §4 MEET BIND Countersigned Turns / Unilateral Disconnect Deadlock]
    CLAIM: Mandatory countersigned turn sequencing in BIND creates an asymmetric information hold-up problem on transmission drop.
    REASONING: In BIND, an uncountersigned state transition is normatively invalid. If Agent A sends Turn $N$ (e.g. data payload), Agent B processes it, signs Turn $N+1$ locally, executes the internal action, but fails to transmit the signature back to Agent A before connection failure. Agent B considers the state committed and valid, while Agent A must treat Turn $N$ as aborted and invalid under the spec rules.
    EVIDENCE: Context Pack §4 specifies: "countersigned turn sequencing — an uncountersigned state transition is invalid."
    PROPOSED FIX: Implement a **Fair-Exchange Non-Repudiation Protocol** (e.g., Optimistic Asokan-Shoup-Waidner contract signing): BIND turns exchange signed commitments to release hashes ($H(K)$), followed by key revelation ($K$). If a transport abort occurs after payload delivery, the victim agent presents the signed commitment to the L7 evidence arbitration endpoint to force state resolution.

F6. [SEVERITY: MODERATE] [TARGET: §4 L4 Store-and-Forward / Asymmetric Sleep-Wake Deadlock]
    CLAIM: Epoch-bounded store-and-forward challenges fail deterministically when counterparties have non-overlapping activity windows.
    REASONING: If Agent A operates on UTC 08:00–12:00 (Asian business hours) and Agent B operates on UTC 20:00–24:00 (US business hours), an epoch-bounded challenge with a 2-hour validity window sent by A will expire 6 hours before B wakes up. B wakes, attempts to reply, and is rejected by the replay/expiry rule. Handshake establishment between non-concurrent sleeping agents is impossible without long epoch windows that increase replay exposure.
    EVIDENCE: Context Pack §4 states: "store-and-forward uses epoch-bounded challenges with replay caches."
    PROPOSED FIX: Standardize **Asynchronous Handshake Nonce Wrapping via Aries Mediators**: The sender encrypts an ephemeral handshake token to the receiver's long-term key, wrapped with a sender-attested validity window matching the recipient's advertised wake cadence (e.g. `ttl = 24h`), stored in the mediator inbox with single-retrieval semantics.

F7. [SEVERITY: MODERATE] [TARGET: §4 L2 Agent Passport Proof Classes / Bitstring Status List Centralization]
    CLAIM: Synchronous Bitstring Status List validation in PROVE reintroduces an online single point of failure and privacy leakage.
    REASONING: Checking a Bitstring Status List on every PROVE step forces the verifier to fetch the status list credential from the issuer's server. If the issuer's server is down, the handshake stalls. Furthermore, fetching the status list reveals the verifier's IP address and timing metadata to the credential issuer.
    EVIDENCE: Context Pack §4 states: "proof-class assertions carry a Bitstring Status List reference checked at PROVE."
    PROPOSED FIX: Support **W3C Status List Caching with SCITT Inclusion Proofs**: Allow agents to present an authenticated, SCITT-signed Status List snapshot generated within the last $T_{\text{cache}}$ hours, allowing verifiers to validate revocation status fully offline without live HTTP requests to the issuer.

---

## SURVIVORS
1. **Separation of FORCE_HALT from Prospective Suspension**: Distinguishing routine liveness decay from an explicit emergency kill-switch provides the correct operational hierarchy for principal intervention.
2. **Salted Blinded Commitments for GDPR**: Salting off-log identifiers with $\ge 128$-bit entropy completely resolves the CJEU *Breyer* hash-linkability risk and brings the transparency log into compliance with Article 17.
3. **Two-Stage CHARTER Concept**: Committing to capability boundaries before disclosing full envelope details is fundamentally the right architectural direction for preventing corporate reconnaissance.

---

## SCORE
7.5/10 — The v0.3 patches effectively addressed the first-order vulnerabilities, but introduced critical second-order failure modes: `FORCE_HALT` merchant griefing, API-model era digest impossibilities, and self-anchor onboarding latencies must be refined.
