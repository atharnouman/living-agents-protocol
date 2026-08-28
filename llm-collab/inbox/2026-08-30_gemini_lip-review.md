MODEL: Gemini 3.7 Flash
DIMENSION: 11-lip-full-review.md
DATE: 2026-08-30

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: `output/lip/LIP-2-meet-draft.md: §2`]
    CLAIM: MEET handshake lacks a symmetric session tie-breaker, causing bidirectional connection collisions and state deadlock when two agents initiate simultaneously.
    REASONING: In LIP-2 §2, `sid` is defined as `(initiator nonce || responder nonce)`. If Agent A and Agent B simultaneously transmit `HAIL` to each other, both consider themselves the "initiator" and the peer as the "responder". Each generates a different `sid` and initializes an independent transcript hash. When Agent A receives B's `HAIL`, it cannot determine whether it is a response to its own `HAIL` or a concurrent incoming session. Both handshakes stall or abort with `LAP_ERR_MEET_TRANSCRIPT`.
    EVIDENCE: LIP-2 §2 states: "`sid` is the session id (initiator nonce ‖ responder nonce)... every MEET message is a signed JSON envelope."
    PROPOSED FIX: Define a deterministic canonical session deduplication rule:
    ```
    sid = sha256(min(A.did, B.did) || ":" || max(A.did, B.did) || ":" || min(nonce_A, nonce_B) || ":" || max(nonce_A, nonce_B))[0..16]
    ```
    If an agent in `IDLE` or `HAILED` receives an incoming `HAIL` from a DID with which it has an outbound in-flight `HAIL`, the party with the lexicographically smaller DID becomes the designated initiator; the other party drops its outbound sequence and processes the incoming message as responder.

F2. [SEVERITY: FATAL] [TARGET: `output/lip/LIP-1-agent-passport-draft.md: §2, §6` & `LAP-founding-document.md: §26.1a`]
    CLAIM: LIP-1 provides no cryptographic transition schema for §26 HANDOFF mutations, causing mutated passports to fail Genesis verification.
    REASONING: Under §26.1a (HANDOFF), a living principal voluntarily transfers accountability to an incoming principal without changing agent title. The new principal signs a new passport with `principal.id = newPrincipalDid`. However, in LIP-1 §5, the Genesis Record immutably commits to `passport_sha256 = sha256(jcs(original_passport))`. When a verifier evaluates the new passport at Step 8 against the Genesis Record in the SCITT log, the SHA-256 hashes mismatch, and the verifier rejects the mutated passport with `LAP_ERR_REGISTRATION`.
    EVIDENCE: LIP-1 §5 states: `passport_sha256` is committed in Genesis; LIP-1 has no normative Re-issuance/Handoff record specification.
    PROPOSED FIX: Define a normative `PassportHandoffEvent` in LIP-1 §3:
    ```json
    {
      "v": "lip1-handoff-v0",
      "agent": "did:key:z6MksMrZ...",
      "prev_passport_sha256": "...",
      "new_passport_sha256": "...",
      "outgoing_sig": "<signature by old principal>",
      "incoming_sig": "<signature by new principal>",
      "effective_at": 1787050000
    }
    ```
    This event is submitted to the SCITT log; verifiers trace the hash-chain of `PassportHandoffEvent` receipts from the Genesis Record to the current active passport.

F3. [SEVERITY: SERIOUS] [TARGET: `output/lip/LIP-2-meet-draft.md: §2, §3`]
    CLAIM: `transcript_hash` computation is non-deterministic under asynchronous transport interleaving and duplicate delivery.
    REASONING: LIP-2 specifies `transcript_hash` as the SHA-256 of all prior messages in order. In distributed messaging (WebSocket, HTTP/2, Aries mediators), message delivery order can vary or duplicate packets can arrive. If Party A receives a duplicate message or if messages cross in flight during bidirectional steps, Party A and Party B construct divergent message arrays, causing all subsequent signatures to fail transcript verification.
    EVIDENCE: LIP-2 §2 specifies: "`transcript_hash` is the SHA-256 of all prior messages in order... a message whose transcript_hash disagrees... MUST abort."
    PROPOSED FIX: Mandate strict **Strict Lock-Step State Sequencing**:
    MEET messages MUST strictly alternate by state index. Duplicate `seq` numbers are silently dropped without updating the transcript array. The transcript hash input is defined as the canonical array of distinct completed state payloads:
    `transcript_hash(N) = sha256(jcs([Msg_HAIL_A, Msg_HAIL_B, Msg_PROVE_A, Msg_PROVE_B, ...]))`.

F4. [SEVERITY: SERIOUS] [TARGET: `output/lip/LIP-2-meet-draft.md: §3`]
    CLAIM: The STH gossip split-view detection rule lacks normative consistency proof verification criteria.
    REASONING: LIP-2 §3 states that a tree head "inconsistent with the anchored Merkle root, or two mutually unverifiable heads for one log, MUST downgrade the session to DEGRADED". It does not specify the mathematical criteria for consistency. Two tree heads of different sizes ($S_1 < S_2$) from the same SCITT log are normal in an active append-only log; they are only inconsistent if the Merkle Consistency Proof between $S_1$ and $S_2$ fails.
    EVIDENCE: LIP-2 §3 mentions STH gossip but omits the consistency proof algorithm.
    PROPOSED FIX: In LIP-2 §3, formally specify the verification check:
    When receiving an STH $T_2$ of size $N_2$ from a peer while holding STH $T_1$ of size $N_1$ ($N_1 \le N_2$):
    1. If $N_1 == N_2$ and $Root(T_1) \neq Root(T_2)$, emit `LAP_ERR_MEET_SPLIT_VIEW`.
    2. If $N_1 < N_2$, require a valid RFC 6962 / SCITT Merkle Consistency Proof from size $N_1$ to $N_2$. If the proof fails, emit `LAP_ERR_MEET_SPLIT_VIEW`.

F5. [SEVERITY: SERIOUS] [TARGET: `output/LAP-founding-document.md: §26.1` / Succession Hijacking via Escalation DoS]
    CLAIM: Involuntary succession triggered by "sustained failure of the principal's escalation contact" allows malicious successors to seize agent identities via network denial of service.
    REASONING: §26.1(b) permits a designated successor to trigger succession dormancy and involuntary CONVEY if there is "sustained failure of the principal's escalation contact". An attacker who discovers they are named as an estate successor (or who forges an unverified successor assertion) can launch a targeted DDoS or email-bombing attack against the principal's escalation endpoint. Once the endpoint fails to respond across the grace window, the attacker seizes the agent's identity and memory.
    EVIDENCE: §26.1(b) states: "on evidence of principal death/dissolution — a successor's attested claim, or sustained failure of the principal's escalation contact — the agent enters succession dormancy."
    PROPOSED FIX: Strip "sustained failure of the principal's escalation contact" as an independent ground for involuntary succession. Involuntary succession MUST require an attested legal death/dissolution certificate (e.g., eIDAS qualified attestation or court-sealed probate record) AND a mandatory 30-day challenge window published in the transparency log before ownership transfer can execute.

F6. [SEVERITY: SERIOUS] [TARGET: `output/lip/LIP-4-micro-core-draft.md: §1, §6`]
    CLAIM: Incompatible JWT header types (`typ`) and schema shapes break seamless upgrade from Micro-Core to LIP-1.
    REASONING: LIP-4 mandates header `typ: "lap-microcore+jwt"` and places the autonomy envelope inline under `payload.lap.envelope`. LIP-1 mandates `typ: "lap-passport+jwt"` and excludes inline envelopes (envelopes are separate L5 artifacts). A Micro-Core server upgraded to parse full LIP-1 passports will reject standard LIP-1 passports unless an adapter shim is explicitly standardized.
    EVIDENCE: LIP-4 §1 specifies `typ: "lap-microcore+jwt"`; LIP-1 §3 specifies `typ: "lap-passport+jwt"`.
    PROPOSED FIX: In LIP-4 §1, permit `typ` to be either `"lap-microcore+jwt"` or `"lap-passport+jwt"`. If a full LIP-1 passport is presented, allow the envelope to be provided via an accompanying `LAP-Envelope` header or OAuth RAR parameter.

F7. [SEVERITY: MODERATE] [TARGET: `output/lip/LIP-1-agent-passport-draft.md: §6`]
    CLAIM: Step 6 in LIP-1 verification lacks an explicit bypass clause for `self-asserted` proof classes.
    REASONING: Step 6 requires verifiers to "verify the proof-class backing credential and its status reference". For passports with `proof_class: "self-asserted"`, `principal.proof` is omitted. A strict implementation reading Step 6 will fail on `self-asserted` passports with `LAP_ERR_PROOF_CLASS`.
    EVIDENCE: LIP-1 §6 Step 6 does not mention handling for `self-asserted`.
    PROPOSED FIX: Amend Step 6: "If `principal.proof_class == 'self-asserted'`, skip credential verification; otherwise, verify the backing credential in `principal.proof` and check its status in the Bitstring Status List."

F8. [SEVERITY: MODERATE] [TARGET: `output/LAP-founding-document.md: §26.3` / Economic Retainer Depletion Attack]
    CLAIM: Publicly accessible agent endpoints allow competitors to weaponize economic mortality by exhausting witness retainers.
    REASONING: §26.3 states that when an agent's witness escrow retainer is exhausted, pulse-gated suspension fires. If an agent operates a public service endpoint, an adversary can submit thousands of unauthenticated requests or force high-cadence state logging, rapidly depleting the agent's witness retainer and causing unexpected economic suspension.
    EVIDENCE: §26.3(a) states: "an agent whose retainer is exhausted stops receiving witness attestations, and pulse-gated suspension fires."
    PROPOSED FIX: Require that witness attestation fees are debited on a fixed periodic time-epoch basis (e.g., \$5/month flat retainer per witness node), NOT per-transaction or per-invocation, decoupling runtime activity from witness solvency.

F9. [SEVERITY: MINOR] [TARGET: `output/lip/LIP-2-meet-draft.md: §4`]
    CLAIM: BIND fair-exchange turn closure protocol lacks message schemas for commitment $H(K)$ and revelation $K$.
    REASONING: LIP-2 §4 specifies optimistic fair exchange (ASW pattern) using $H(K)$ and $K$, but does not define the JSON wire fields. Without standard field names, independent implementations will use incompatible message formats.
    EVIDENCE: LIP-2 §4 describes fair exchange in prose without normative JSON fields.
    PROPOSED FIX: Define standard BIND turn envelope fields:
    ```json
    { "turn_seq": 1, "commit": "sha256:<hash-of-k>", "payload_hash": "..." }
    { "turn_seq": 1, "reveal_key": "<hex-k>", "sig": "..." }
    ```

---

## 5 SECTIONS MOST REQUIRING FORMAL STATE TABLES & WORKED EXAMPLES

1. **LIP-2 §2 (MEET State Machine & Abort Matrix)**: A complete $8 \times 8$ state transition table covering all valid inputs, unexpected message handling, timeout limits ($T_{\text{step}}$), and exact error transitions.
2. **LIP-1 §6 (Passport Lifecycle & Handoff Trace)**: A worked sequence diagram showing initial Genesis registration, voluntary HANDOFF to a new principal, key rotation, and how verifiers validate the updated passport.
3. **LIP-2 §4 (BIND Fair-Exchange Turn Sequence)**: A step-by-step worked trace of a 3-turn interaction, including a simulated network drop and subsequent dispute resolution via `lap-evidence-v0`.
4. **LIP-2 §3 (STH Gossip & Split-View Verification Algorithm)**: A concrete pseudocode algorithm demonstrating how two agents compare SCITT Signed Tree Heads and evaluate Merkle Consistency Proofs.
5. **LIP-4 §2 (Micro-Core RFC 9421 Signature Verification Flow)**: A complete, byte-accurate worked example of an HTTP request, its signature base string, canonical digest calculation, and response receipt line.

---

## SURVIVORS
1. **The Accountability Chain Invariant (§26.0)**: The principle that an agent must terminate in exactly one resolvable legal person at every moment of its existence provides an unshakeable legal and governance anchor.
2. **Transcript-Hashed Handshake Construction (LIP-2)**: Chaining all preceding handshake messages into every step's signature provides ironclad protection against phase reordering, cipher downgrades, and MITM tampering.
3. **Two-Stage CHARTER with Reservation Tickets (LIP-2 §7)**: Decoupling capability proof from full disclosure while enforcing authorizer-signed balance reservations solves the dual problems of corporate reconnaissance and concurrent over-commitment.

---

## PER-DOCUMENT READINESS SCORES
- **LIP-1 (Agent Passport & Genesis)**: **8.5/10** — Mature and ready for implementation; needs the `PassportHandoffEvent` schema to close the §26 lifecycle loop.
- **LIP-2 (MEET Handshake)**: **7.0/10** — Architecturally brilliant, but needs the session tie-breaker, lock-step sequencing rules, and STH consistency proof algorithms specified before multi-vendor interoperability is possible.
- **LIP-4 (Micro-Core)**: **9.0/10** — Extremely clean, implementable in an afternoon, and well-covered by test vectors.
- **Founding Document §26 (Lifecycle & Mortality)**: **8.0/10** — Excellent conceptual closure of zombie authority; needs hardening against succession DoS attacks and retainer exhaustion griefing.
