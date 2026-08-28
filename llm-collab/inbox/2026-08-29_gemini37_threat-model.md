MODEL: Gemini 3.7 Flash
DIMENSION: 04-threat-model.md
DATE: 2026-08-29

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §4 Autonomy Envelope & Spend Authorizer Vouchers / Persona (b)]
    CLAIM: Spend Authorizer Offline Voucher Replay and Double-Spend across Unsynchronized Counterparties.
    REASONING: In v0.3, spend authorizers issue pre-allocated sub-budget vouchers so agent fleets survive authorizer network outages. A compromised agent holding a \$500 offline voucher presents the voucher to Counterparty A and receives \$500 of compute. Because Counterparty B is also operating offline or cannot query the authorizer in real-time, the compromised agent presents the exact same voucher to Counterparty B to receive another \$500 of compute. By the time counterparties settle with the authorizer, the principal's account is overdrawn by \$500.
    EVIDENCE: Context Pack §4 specifies: "authorizers issue pre-allocated sub-budget vouchers so fleets survive authorizer outages."
    PROPOSED FIX: Spend vouchers MUST NOT be bearer tokens. Vouchers MUST be **Counterparty-Specific & Single-Use**: the voucher payload MUST include the counterparty's DID (`audience: did:web:vendor.com`), a unique sequential voucher nonce, and a strict short expiry ($T \le 3600\text{s}$). If an agent needs to transact with unknown counterparties, it MUST obtain an ephemeral signed voucher bound to the counterparty's DID during MEET Step 4 (TUNE).

F2. [SEVERITY: FATAL] [TARGET: §4 Forensic Evidence Bundling (`lap-evidence-v0`) / Privacy & IP Exfiltration]
    CLAIM: Forensic Evidence Bundles Leak Proprietary Prompts, Trade Secrets, and Third-Party PII to Arbitrators.
    REASONING: In v0.3, `lap-evidence-v0` extracts the dual-signed contract, Flight Recorder Merkle paths, and OTel GenAI telemetry into a package for dispute resolution. Flight Recorders formatted with OTel GenAI conventions contain full prompts, tool responses, internal chain-of-thought traces, and raw customer data. In a minor billing dispute, an adversary can trigger arbitration to compel the target agent to submit an un-redacted evidence bundle, exfiltrating proprietary system prompts and confidential business records.
    EVIDENCE: Context Pack §2 and §4 introduce `lap-evidence-v0` and OTel-GenAI-formatted Flight Recorder entries.
    PROPOSED FIX: Mandate **Selective-Disclosure Redaction with Merkle Subtree Proofs** in `lap-evidence-v0`: Evidence bundles MUST redact sensitive prompt payloads and internal tool arguments, replacing them with salt-blinded leaf hashes, disclosing only the cryptographic transition proofs, spend timestamps, and external API receipts required to arbitrate the specific disputed claim.

F3. [SEVERITY: SERIOUS] [TARGET: §4 Pulse Witness VRF Selection / Persona (e) + (f) Collusion]
    CLAIM: Predictable VRF Randomness Seeds Enable Hostile Witness Pool Pre-Computation and Targeted Sybil Paralyzation.
    REASONING: In v0.3, witnesses are selected "verifiably at random from the pool" using blockchain blockhashes or log checkpoints. Because blockchain blockhashes are public minutes in advance, a sophisticated attacker operating a pool of 50 witness nodes can calculate future VRF selections. When the target agent's pulse cycle aligns with a window where the attacker's nodes are selected as the primary $\ge 2$ witnesses, the attacker withholds pulse signatures, triggering an artificial prospective suspension.
    EVIDENCE: Context Pack §4 specifies: "witnesses selected verifiably at random from the pool."
    PROPOSED FIX: Compute the witness selection seed using a **Two-Party Commit-Reveal Seed**: Seed = `HMAC(Blockhash, Agent_Ephemeral_Secret_Nonce)`. Because the attacker does not know the agent's ephemeral secret nonce until the pulse is broadcast, pre-computing which witness nodes will be selected is computationally impossible.

F4. [SEVERITY: SERIOUS] [TARGET: §4 Registration / SCITT Split-View Attack by Rogue Log Operators / Persona (e)]
    CLAIM: Rogue SCITT Log Operators Can Execute Split-View Attacks to Mask Agent Revocations from Target Victims.
    REASONING: A malicious or coerced SCITT Transparency Service presents Tree Head A (containing a valid `FORCE_HALT` revocation) to auditors and the principal, while serving Tree Head B (an older, unrevoked checkpoint) to a target merchant counterparty. The merchant verifies the SCITT Merkle inclusion proof against Tree Head B and permits the compromised agent to execute a high-value purchase.
    EVIDENCE: Context Pack §4 and §6.5 rely on SCITT Transparency Services anchored to open chains.
    PROPOSED FIX: Mandate **Gossip-Based Tree Head Validation** (RFC 9162 / SCITT Gossip Protocol): In MEET Step 2 (PROVE), counterparties exchange their latest known SCITT Signed Tree Heads (STHs). If an agent or counterparty presents an STH that is partitioned or inconsistent with the peer's observed blockchain Merkle root, the handshake MUST immediately downgrade to `DEGRADED` and halt execution.

F5. [SEVERITY: SERIOUS] [TARGET: §4 MEET Step 2 PROVE / ZK Verification Resource-Exhaustion DoS / Persona (a)]
    CLAIM: Malicious Counterparties Can Exhaust Agent Compute by Flooding Computationally Intensive ZK Proof Challenges.
    REASONING: In MEET Step 2/3, agents exchange zero-knowledge range proofs for capability verification. Generating or verifying complex SNARK/STARK proofs requires significant CPU and memory. A botnet of lightweight client agents can initiate thousands of concurrent MEET handshakes against an enterprise agent endpoint, forcing it to generate and verify ZK proofs continuously, exhausting its CPU budget and crashing the runtime.
    EVIDENCE: Context Pack §4 adopts ZK range proof commitments in MEET.
    PROPOSED FIX: Enforce a **Proof-of-Work (PoW) or Pre-Auth Rate Limit** before entering CHARTER: Require initiating counterparties to solve a lightweight computational puzzle (e.g. mTLS handshake challenge or RFC 9261 token) before the receiving agent allocates compute for ZK verification.

F6. [SEVERITY: MODERATE] [TARGET: §4 Substrate Attestation / TEE Side-Channel Key Extraction / Persona (g)]
    CLAIM: Platform Cloud Providers Can Bypass TEE Substrate Attestation via Physical Side-Channels (AEP / Transient Execution).
    REASONING: An agent relies on a hardware TEE quote (Intel TDX / AMD SEV-SNP) in its Passport to claim a hardened substrate class. A malicious cloud hypervisor operator executing side-channel attacks (e.g. CacheWarp, Downfall, or Rowhammer) extracts the agent's private signing key from the enclave memory without invalidating the static hardware attestation certificate.
    EVIDENCE: Context Pack §4 states: "substrate-attestation class (TEE quote where available — SHOULD, not MUST)."
    PROPOSED FIX: Require **Continuous Enclave Ephemeral Key Ratcheting**: Enclave signing keys MUST be ephemeral and ratcheted every $N$ pulses using hardware TRNG entropy derived internally within the secure enclave, ensuring that a compromised key lifetime is strictly bounded to a single pulse epoch.

F7. [SEVERITY: MODERATE] [TARGET: §4 Human Escalation Guarantee / Social Engineering & Harassment Flooding / Persona (a)]
    CLAIM: Adversarial Counterparties Can Abuse the Human Escalation Guarantee to Harass Human Principals and Trigger Denial-of-Attention.
    REASONING: Under the "Human Escalation Guarantee," any counterparty can demand and reach the responsible human in bounded time. An attacker can deploy 10,000 automated agents that deliberately trigger trivial edge-case disputes during MEET/BIND, forcing the protocol to emit high-priority escalation alerts to the human principal's emergency contact, inducing notification fatigue and operational paralysis.
    EVIDENCE: Context Pack §4 specifies: "Human Escalation Guarantee clause... reach the responsible human in bounded time."
    PROPOSED FIX: Require an **Escalation Stake / Fee Bond** for Human Escalation: To trigger a formal Human Escalation Guarantee event, the demanding counterparty MUST post a verifiable micro-bond (e.g. \$10–\$50 in escrow). If the dispute is judged frivolous or automated harassment by the arbitrator, the bond is forfeited to the human principal.

---

## TOP 5 ATTACKS TO HARDEN BEFORE PRODUCTION RELEASE

1. **Spend Voucher Multi-Counterparty Double Spend (F1)**: Pre-allocated vouchers without counterparty audience binding will drain principal funds across offline vendors.
2. **Arbitration Evidence Bundle IP Exfiltration (F2)**: Over-disclosing Flight Recorder OTel spans in dispute bundles will leak proprietary system prompts and confidential business data.
3. **VRF Witness Selection Manipulation (F3)**: Public blockchain seed predictability allows hostile witness cartels to deliberately target and suspend specific agents.
4. **SCITT Split-View Revocation Masking (F4)**: Malicious log operators serving bifurcated Merkle trees can conceal `FORCE_HALT` revocations from counterparties.
5. **ZK Verification Compute Exhaustion (F5)**: Unmetered ZK range proof requests during MEET handshakes expose agent servers to resource-depletion DoS attacks.

---

## SURVIVORS
1. **Settlement Phase-Gates**: Structuring multi-stage transactions with explicit authorization checkpoints provides the indispensable foundation for stopping rogue agent runaway.
2. **Off-Log Salted Commitments**: Blinded cryptographic commitments effectively shield natural person identities from permanent public ledger exposure.
3. **Layered Trust States**: The progressive degradation model (`VERIFIED` $\to$ `DEGRADED` $\to$ `UNVERIFIED` $\to$ `REVOKED`) provides nuanced, resilient policy handling under network partitions.

---

## SCORE
7.8/10 — The threat posture of v0.3.1 is significantly mature compared to early drafts, but urgent mitigations are required for offline voucher double-spending, evidence bundle data leakage, and cryptographic seed predictability in witness pools.
