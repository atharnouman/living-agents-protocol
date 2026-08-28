# LIP-2: MEET — the Stranger-Agent Handshake

*Status: DRAFT v0.1 — 2026-08-29. Layer: L6 (Society). Requires: LIP-1 (passports), LIP-3 (envelope scopes). Incorporates round-1's contributed state machine and round-2's corrections (reservation tickets, fair-exchange closure, STH gossip, sleep-scaled challenges — spec §25.3/§25.4). RFC 2119 keywords apply; Normative and Informative text are separated.*

## 1. Purpose (Informative)

MEET is what happens when two agents that have never met want to transact: identification, mutual verification, limit disclosure, transport agreement, a signed contract, and a presence plan — each step leaving signed evidence. It plays the TLS-handshake role for agent relationships: it never carries the work (that's A2A/MCP/payment rails); it decides *whether and under what authority* the work may flow.

## 2. States and messages (Normative)

```
IDLE → HAILED → PROVEN → CHARTERED → TUNED → BOUND → ACTIVE → CLOSED
```

Every MEET message is a signed JSON envelope: `{ sid, seq, transcript_hash, body, sig }`. **Session identity and collision tie-break (v0.2)**: `sid = sha256(min(didA,didB) ‖ max(didA,didB) ‖ min(nonceA,nonceB) ‖ max(nonceA,nonceB))` — symmetric, so simultaneous HAILs from both sides resolve to ONE session: on receiving a HAIL from a peer to whom an outbound HAIL is in flight, the party with the lexicographically smaller DID is the initiator; the other MUST drop its outbound attempt and respond. **Lock-step sequencing (v0.2)**: messages strictly alternate; a duplicate `seq` MUST be silently dropped without touching the transcript; a message arriving in a state that does not expect it MUST abort (`LAP_ERR_MEET_TRANSCRIPT`). The transcript is the canonical ordered array of distinct accepted messages, and **`transcript_hash` is the SHA-256 of that array** — every signature therefore covers the entire preceding conversation, which makes downgrade and message-reordering attacks self-evident (the TLS transcript-hash lesson). A message whose `transcript_hash` disagrees with the receiver's own computation MUST abort the session (`LAP_ERR_MEET_TRANSCRIPT`).

| Step | State after | Body carries | MUST-checks on receipt | Abort error |
|---|---|---|---|---|
| 1 HAIL | HAILED | Both passports (LIP-1), fresh nonces, supported profile list | passport schema + version | `…_BAD_PASSPORT` |
| 2 PROVE | PROVEN | Challenge signatures; registration proofs; proof-class status; **latest observed STHs (gossip)** | full LIP-1 §6 verification; revocation; registration (≥2 log inclusions or finalized self-anchor); STH consistency | `…_AUTH`, `…_REVOKED`, `…_SPLIT_VIEW` |
| 3 CHARTER-A | CHARTERED | Commitments & predicate proofs ("cap covers X"), **Reservation Ticket** for monetary predicates | predicate verification (behind pre-auth throttle, §6); ticket signature + counterparty binding + expiry | `…_SCOPE`, `…_TICKET` |
| 4 TUNE | TUNED | Transport & profile negotiation (A2A / MCP / rails; Noise AKE parameters) | mutual profile intersection non-empty | `…_TRANSPORT` |
| 5 BIND | BOUND | The Interaction Contract (§4) **including full Interaction-Charter disclosure** (CHARTER-B), dual-signed | contract schema; charter consistency with stage-A commitments (a commitment that stage-B disclosure contradicts ⇒ abort + log) | `…_BINDING`, `…_CHARTER_MISMATCH` |
| 6 PULSE | ACTIVE | Presence contract (§5) | witness endpoints resolvable | `…_PULSE` |
| teardown | CLOSED | Signed closing receipt (both directions) | — | (unilateral drop is itself logged) |

Trust-state output: PROVE resolves the counterparty to exactly one of VERIFIED / DEGRADED / UNVERIFIED / REVOKED (spec §16.1); local policy then decides whether to continue. `UNVERIFIED_PENDING_FINALITY` MAY be treated as DEGRADED-equivalent for non-money, non-PII scopes only.

## 3. PROVE details (Normative)

Mutual challenge–response over the session nonces (both directions). Registration proof per LIP-1 §5–6. Proof-class status via Bitstring Status List or an in-date SCITT-sealed snapshot. **STH gossip**: each side includes the newest signed tree heads it has observed for the logs the counterparty's proofs cite. Consistency criteria (v0.2, normative): given peer STH T₂ of size N₂ and held STH T₁ of size N₁ ≤ N₂ for the same log — (a) if N₁ = N₂ and roots differ ⇒ `LAP_ERR_MEET_SPLIT_VIEW`; (b) if N₁ < N₂, an RFC 6962 consistency proof from N₁ to N₂ MUST verify, else `LAP_ERR_MEET_SPLIT_VIEW` (different sizes alone are normal for an active log, never an inconsistency). On split-view: downgrade the session to DEGRADED, report to the log-monitoring endpoint, preserve both heads as evidence.

## 4. BIND: the Interaction Contract (Normative)

Fields (all MUST unless noted): parties (passport hashes); purpose; permitted data classes and retention; logging duties (dual-entry rule); dispute endpoint (`lap-evidence-v0` compatible); the **Human Escalation Guarantee clause** (contact path + bounded response time); **delegation warranty** (each party warrants its disclosed delegation graph is complete — the taint liability rule made contractual); the full Interaction Charter of each side (the CHARTER-B disclosure); expiry/renewal terms (MAY).

**Turn sequencing with fair-exchange closure**: post-BIND interaction turns are numbered and countersigned — `sig(seq, prev_turn_hash, payload_hash)` — and an uncountersigned transition is invalid. To prevent transport-drop deadlock (one side holding a signature the other never received), turn closure uses optimistic fair exchange: commit `H(K)` first, reveal `K` second; a party left with a commitment but no reveal after timeout MUST resolve via the contract's dispute endpoint, which can force closure from the committed evidence. Wire fields (v0.2, normative): commit message `{ "turn_seq": n, "commit": "sha256:<H(K)>", "payload_hash": "…", "sig": … }`; reveal message `{ "turn_seq": n, "reveal_key": "<hex K>", "sig": … }`. *(Informative: this is the Asokan–Shoup–Waidner pattern with the L7 evidence layer as the optimistic third party.)*

## 5. PULSE: the presence contract (Normative)

Agreed fields: heartbeat cadence and witness endpoints (per spec §4 L5 observer model); store-and-forward mediator (Aries Pickup / DIDComm mediator profile) with **single-retrieval semantics**; resumption keys **bound to passports, not processes** (a restart resumes; it does not re-MEET); wake priorities ("deliver on wake" vs "wake if ≥ urgent").

**Sleep-scaled challenges**: any challenge or nonce intended to survive a sleep gap MUST carry a validity window scaled to the recipient's *advertised wake cadence* (from the presence contract), not a fixed short TTL. On waking, an agent MUST abort and restart any handshake if its own passport or envelope mutated during dormancy; receivers MUST reject replayed challenges via per-session replay caches.

## 6. Anti-DoS (Normative)

Verifying predicate proofs and registration evidence is expensive. Endpoints MUST gate CHARTER-A processing behind cheap pre-authorization (per-source rate limits and/or a client puzzle) and SHOULD bound concurrent in-flight handshakes per source. Handshake state before BIND MUST be evictable without obligation.

## 7. Reservation Tickets (Normative)

A monetary predicate proof ("my cap covers this amount") says nothing about *concurrent* commitments. Where CHARTER-A asserts spending capacity, the assertion MUST be backed by a spend-authorizer-signed Reservation Ticket `{nonce, amount, unit, expiry, counterparty}` — balance is locked at issuance, tickets are single-use and counterparty-bound. A bare predicate proof without a ticket is *disclosure*, and the counterparty MUST treat it as carrying no reservation.

## 8. Error codes (Normative)

`LAP_ERR_MEET_{BAD_PASSPORT | AUTH | REVOKED | SPLIT_VIEW | SCOPE | TICKET | TRANSPORT | BINDING | CHARTER_MISMATCH | PULSE | TRANSCRIPT | TIMEOUT | THROTTLED}`. Every abort MUST be written to the local recorder with the transcript hash at abort time.

## 9. Security considerations (Informative)

Reconnaissance is bounded by the two-stage CHARTER (commitments before disclosure; full charter only inside the signed, dual-logged contract — which is simultaneously the principal's apparent-authority legal shield). Downgrade and reordering are bound by the transcript hash. Split-view by rogue logs is surfaced by gossip. Verification DoS is bounded by §6. Replay across sleep is bounded by §5. Residual risks: metadata (who MEETs whom is visible to mediators and witnesses — minimization is future work), and everything inherited from LIP-1 key custody.

## 10. Open items

Full message schemas + a handshake transcript test vector (reference library); the Noise profile parameters (IK vs XX selection rules); mediator discovery; CHARTER-A predicate-proof format selection (BBS+ vs Bulletproofs-class range proofs — needs a cryptographer's review); timeout constants per state.
