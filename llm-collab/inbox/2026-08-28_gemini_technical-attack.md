MODEL: Gemini (Advanced Coding & Reasoning)
DIMENSION: 01-technical-attack.md
DATE: 2026-08-28

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §4 MEET Handshake Step 3 (CHARTER) & Reconnaissance Leakage]
    CLAIM: Asymmetric disclosure of envelope limits at CHARTER before mutual contract binding (BIND) allows malicious counterparties to harvest uncommitted budget, scope, and escalation topologies with zero accountability.
    REASONING: In MEET, Alice discloses her autonomy envelope slice at Step 3 (CHARTER). A malicious counterparty Bob can accept Step 3, parse Alice's maximum spend authority, internal rate limits, and principal escalation contacts, and then deliberately abort the connection at Step 4 (TUNE) by timing out. Because Step 5 (BIND) was never reached, no signed bilateral interaction contract exists, and Bob's Flight Recorder records nothing actionable.
    EVIDENCE: Context Pack §4 acknowledges "disclosure is attacker reconnaissance" but leaves selective disclosure / ZK proofs as "flagged future work."
    PROPOSED FIX: Split CHARTER into a two-stage cryptographic commit: (1) In CHARTER-A, both parties exchange zero-knowledge range commitments or blind threshold proofs (e.g., `spend_cap >= tx_requirement`); (2) Full envelope scope slices are only revealed in Step 5 (BIND) inside the mutually signed and dual-logged interaction contract.

F2. [SEVERITY: FATAL] [TARGET: §4 Autonomy Decay & Prospective-Only Suspension]
    CLAIM: Prospective-only suspension creates a critical TOCTOU race condition where a compromised agent can execute large, long-running asynchronous commitments immediately prior to deliberate heartbeat cessation.
    REASONING: If an agent's keys are compromised, the attacker can initiate an asynchronous multi-day batch settlement or bulk data exfiltration contract with a third party. If the principal detects compromise and stops issuing Pulses, the agent enters "suspended" state. However, because suspension is "prospective only" and in-flight contracts MUST complete, counterparties will honor and execute the malicious in-flight transaction to completion.
    EVIDENCE: Context Pack §4 states: "suspension is prospective only (in-flight actions complete/roll back per contract; recovery on pulse resumption is automatic)."
    PROPOSED FIX: Introduce an active, signed Emergency Revocation Broadcast (`FORCE_HALT_NULLIFY`) in L7 Accountability that overrides prospective-only grace semantics. Counterparties verifying in-flight obligations MUST query a revocation tombstone endpoint before final settlement phases of multi-stage contracts.

F3. [SEVERITY: SERIOUS] [TARGET: §4 Pulse & Witness Model]
    CLAIM: $\ge 2$ independent witness threshold is vulnerable to Sybil and co-location collusions on public clouds without cryptographically verified routing diversity.
    REASONING: An attacker controlling two cloud instances in the same AS/provider can register two witness endpoints. Alternatively, a network partition isolating an agent from 2 out of 3 witnesses triggers false-positive suspension unless witness consensus requires verifiable latency/epoch watermarks. Stale witness attestations can also be replayed if not bound to an ephemeral monotonic counter or blockhash.
    EVIDENCE: Context Pack §4 specifies: "suspension requires misses across $\ge 2$ independent witnesses (anti-DoS)."
    PROPOSED FIX: Witness attestations MUST include an epoch timestamp signed over the latest blockhash of an anchored L1 blockchain or transparency log checkpoint. Witnesses MUST register public keys with cryptographic AS-diversity/domain proof in the Agent Transparency Log (ATL).

F4. [SEVERITY: SERIOUS] [TARGET: §4 Ownership & CONVEY / Era-Stamped Receipts]
    CLAIM: Era boundaries do not account for hidden substrate parameterization drifts (system prompt modifications, quantization, LoRA adapter swaps), enabling behavioral laundering under identical model tags.
    REASONING: Era-stamps bind to `(model class + constitution hash)`. If an operator switches a local model from FP16 to 4-bit quantization, swaps out a LoRA adapter, or modifies temperature/sampling hyper-parameters, the model class identifier remains `llama-3-70b` and the constitution text is identical. However, safety margins and behavioral determinism degrade significantly.
    EVIDENCE: Context Pack §4 defines era-stamped receipts as recording `(model class + constitution hash)`.
    PROPOSED FIX: Broaden the Era Identifier to include an immutable `runtime_environment_digest`: SHA-256 over `(model_weights_manifest_digest + system_prompt_digest + decoding_parameters_canonical_json + constitution_hash)`.

F5. [SEVERITY: SERIOUS] [TARGET: §4 Registration / Self-Anchoring vs VERIFIED State]
    CLAIM: Self-anchoring escape hatch introduces unhandled blockchain finality delays and reorg vulnerabilities during MEET verification.
    REASONING: An agent asserting `VERIFIED` via direct L1 blockchain anchoring submits a raw transaction hash or Merkle path during PROVE. If the counterparty checks an unconfirmed mempool transaction or an unfinalized block on a Proof-of-Stake/Rollup network, a block reorganization can invalidate the anchor post-handshake, leaving the counterparty with an unanchored, un-revocable agent interaction.
    EVIDENCE: Context Pack §4 states "a direct on-chain anchor is first-class registration and satisfies VERIFIED."
    PROPOSED FIX: Define strict finality requirements for self-anchored verification: verification rules MUST require a minimum of $K$ confirmations (e.g., 64 epochs on Ethereum, 6 blocks on Bitcoin) or an attested ZK-state proof from a finalized light-client header. Handshakes presenting unfinalized anchors MUST resolve to `UNVERIFIED_PENDING_FINALITY`.

F6. [SEVERITY: SERIOUS] [TARGET: §4 MEET Handshake & Sleeping Agents (Store-and-Forward)]
    CLAIM: Asynchronous store-and-forward handshake allows replay of stale challenge nonces and state-confusion attacks across agent sleep-wake cycles.
    REASONING: If Agent A sends a HAIL/PROVE challenge to Agent B while B is dormant, the message sits in an untrusted mediator queue. When B wakes up (potentially hours or days later, perhaps after a key rotation or envelope expiry), replying to the original ephemeral challenge exposes B to signature replay or interaction binding under expired constraints.
    EVIDENCE: Context Pack §2 and §4 mention store-and-forward messaging across sleep cycles and PULSE presence contracts.
    PROPOSED FIX: Store-and-forward MEET handshakes MUST NOT use raw ephemeral transport nonces. They MUST use timestamped, epoch-bounded challenges (`valid_until_utc`) with replay caches maintained by both endpoints, and MUST abort if the local envelope or passport has mutated during dormancy.

F7. [SEVERITY: MODERATE] [TARGET: §4 Trust States & Mixed-Delegation Taint]
    CLAIM: Reframing delegation taint as a "liability rule" without a cryptographic non-repudiation binding allows root principals to plausibly deny unlogged downstream sub-delegations.
    REASONING: If Agent A delegates to Agent B, and Agent B internally invokes untrusted Agent C via an unlogged MCP call, Context Pack §4 asserts that "concealment discovered post-hoc forfeits standing." However, in a post-incident dispute, Principal A can claim Agent B was compromised or acted ultra vires, shifting liability into an evidentiary vacuum.
    EVIDENCE: Context Pack §4 states "chain trust = weakest link, with the graph disclosed at CHARTER — honestly a liability rule, not a detector."
    PROPOSED FIX: In L6 BIND, require the parent agent to sign an explicit `delegation_warranty_claim` inside the interaction contract, binding the legal principal to joint-and-several liability for all downstream tool outputs unless a cryptographically countersigned child envelope was explicitly registered at BIND time.

F8. [SEVERITY: MODERATE] [TARGET: §4 Agent Passport & Proof Classes]
    CLAIM: Proof class hierarchy lacks a revocation distribution mechanism, permitting revoked credentials (e.g., revoked domain DNS or suspended corporate charter) to pass as valid.
    REASONING: An agent passport marked `org-validated` carries a signed credential from an enterprise CA or trust provider. If the enterprise fires the employee or terminates the agent project, counterparties checking the passport offline or against a cached Genesis record will continue treating the agent as `org-validated`.
    EVIDENCE: Context Pack §4 describes proof classes (self-asserted / domain / org / gov-validated) and passport revocation endpoints, but does not specify credential status protocols for the proof class claim itself.
    PROPOSED FIX: Require proof class assertions to be formatted as W3C Verifiable Credentials 2.0 with a mandatory `statusListCredential` (Bitstring Status List v1.0) endpoint checked during MEET Step 2 (PROVE).

F9. [SEVERITY: MODERATE] [TARGET: §4 Flight Recorder & Dual-Logging]
    CLAIM: Bilateral dual-entry logging in BIND deadlocks in adversarial disputes where each party submits contradictory Flight Recorder logs to arbitrators.
    REASONING: If Agent A logs interaction state $S_A$ and Agent B logs $S_B$, and both claim the other refused to countersign the final state transition, an external auditor cannot determine which agent faulted without a third-party non-repudiable ordering notary.
    EVIDENCE: Context Pack §4 notes "bilateral events become dual-entry via BIND."
    PROPOSED FIX: Mandate that every BIND interaction contract defines a deterministic sequence numbering scheme where each interaction turn requires an aggregated Schnorr/BLS signature over `(seq_no, prev_turn_hash, payload_hash)`. An un-countersigned state transition is normatively invalid.

F10. [SEVERITY: MINOR] [TARGET: §4 L2 Key Custody vs L4 Pulse Continuity]
    CLAIM: Key rotation ceremony invalidates historical Pulse hash-chains without a defined cross-key transition witness.
    REASONING: Pulse is chained to the audit-log head using key $K_{\text{old}}$. When $K_{\text{new}}$ is rotated during maintenance, the subsequent Pulse signed with $K_{\text{new}}$ breaks the cryptographic continuity check of counterparties validating the chain across the rotation epoch.
    EVIDENCE: Context Pack §4 states Pulse proves "continuity of key custody and operational responsibility."
    PROPOSED FIX: Define a `KeyRotationEvent` log entry signed by *both* $K_{\text{old}}$ and $K_{\text{new}}$ (or by the Master Principal Key) and anchored into the Flight Recorder before the first Pulse of the new key era is emitted.

---

## DESIGNS

### MEET Handshake State Machine & Error Transition Table

```
   +--------+      HAIL (Passport Exch)      +-------+
   |  IDLE  | -----------------------------> | HAIL  |
   +--------+                                +-------+
        ^                                        |
        | Timeout / Bad Passport (ERR_AUTH)      | PROVE (Challenge/Resp)
        +----------------------------------------v
   +--------+                                +-------+
   | CLOSED | <----------------------------- | PROVE |
   +--------+   Revoked / Bad Sig (ERR_PROVE)+-------+
        ^                                        |
        |                                        | CHARTER (ZK Scope Commit)
        | Abort / Mismatch (ERR_SCOPE)           v
        |                                    +---------+
        +----------------------------------- | CHARTER |
        |                                    +---------+
        |                                        |
        | Transport Fail (ERR_TUNE)              | TUNE (Transport / TLS)
        +----------------------------------------v
        |                                    +-------+
        |                                    | TUNE  |
        |                                    +-------+
        |                                        |
        | Unsigned / Contract Reject (ERR_BIND)  | BIND (Dual-Signed Contract)
        +----------------------------------------v
        |                                    +-------+
        |                                    | BIND  |
        |                                    +-------+
        |                                        |
        | Pulse Failure (ERR_PULSE)              | PULSE (Cadence Established)
        +----------------------------------------v
                                             +--------+
                                             | ACTIVE |
                                             +--------+
```

#### State Transition & Error Specification

| Current State | Event / Message | Next State | Actions / Invariants | Error / Abort Path |
|---|---|---|---|---|
| **IDLE** | Send/Recv `HAIL` | **HAIL_SENT** / **HAIL_RCVD** | Verify Passport schema, verify DID document, check initial ATL registration anchor. | Invalid DID / Schema $\to$ emit `ERR_BAD_PASSPORT`, state $\to$ **CLOSED**. |
| **HAIL** | Send/Recv `PROVE` | **PROVING** | Mutual challenge nonce verification (crypto challenge-response); query Bitstring Status List for revocation. | Sig verification fail / Revoked $\to$ emit `ERR_AUTH_FAILED`, state $\to$ **CLOSED**. |
| **PROVE** | Send/Recv `CHARTER` | **CHARTERED** | Disclose zero-knowledge envelope limit commitment; match purpose constraints against local policy. | Incompatible envelope scopes $\to$ emit `ERR_SCOPE_INCOMPATIBLE`, state $\to$ **CLOSED**. |
| **CHARTER** | Send/Recv `TUNE` | **TUNED** | Negotiate protocol transport (A2A / MCP / HTTPS), establish ephemeral session keys (Noise / TLS 1.3). | Cipher mismatch / Transport fail $\to$ emit `ERR_TRANSPORT_NEGOTIATION`, state $\to$ **CLOSED**. |
| **TUNE** | Send/Recv `BIND` | **BOUND** | Generate bilateral `InteractionContract`, both parties append co-signatures over contract hash. Append to local Flight Recorder. | Signature refusal / Hash mismatch $\to$ emit `ERR_BINDING_REJECTED`, state $\to$ **CLOSED**. |
| **BIND** | Send/Recv `PULSE` | **ACTIVE** | Establish heartbeat cadence, exchange witness endpoint lists, initialize store-and-forward session resume token. | Witness validation failure $\to$ emit `ERR_PULSE_UNSATISFIED`, state $\to$ **CLOSED**. |
| **ACTIVE** | Session Teardown | **CLOSED** | Exchange final state countersignatures; write session closing record to Flight Recorder. | Abrupt drop $\to$ record unilateral disconnection in Flight Recorder. |

---

## PRIOR ART
- **TLS 1.3 (RFC 8446)**: Adopt explicit state machine transition tables and encrypted handshake phase boundaries (preventing reconnaissance before key exchange).
- **Noise Protocol Framework**: Adopt patterns for authenticated key exchange with identity hiding (Noise_XX or Noise_IK) for the MEET wire layer.
- **W3C Bitstring Status List v1.0**: Adopt for compact, privacy-preserving, high-speed credential revocation checking in PROVE step.
- **IETF SCITT (draft-ietf-scitt-architecture)**: Adopt Signed Statements and Transparent Receipts for Flight Recorder dual-logging anchoring.

---

## SURVIVORS
1. **Prospective Suspension Separation**: Distinguishing in-flight contract resolution from future authorization bounds correctly mirrors real-world legal agency doctrines.
2. **Era-Stamped Receipts**: Tying reputation to explicit model+constitution eras is the only viable architectural solution to the model-upgrade reputation laundering vulnerability.
3. **Dual-Logged BIND Interaction Contracts**: Anchoring bilateral commitments locally into each agent's tamper-evident recorder creates a verifiable audit trail without requiring real-time consensus.

---

## SCORE
7/10 — The v0.2 mechanisms represent a massive improvement over naive decentralized identity proposals, but critical protocol race conditions remain: CHARTER reconnaissance, prospective-only suspension bypasses, and unfinalized self-anchoring must be hardened before any production release.
