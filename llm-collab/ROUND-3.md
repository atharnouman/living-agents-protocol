# LAP Review — Round 3 Instructions (for a file-access model)

*Prepared 2026-08-29. Spec is now v0.4.2. Rounds 1–2 are fully merged — read `IMPROVEMENTS-LOG.md` first: repeating anything already listed there scores zero. This round targets material NO previous round has seen.*

## Ground rules (unchanged, mandatory)

1. **Read-only everywhere.** Never modify, create, or delete any existing file in this project. Your ONLY writes are NEW files in `E:\LivingAIAgents\llm-collab\inbox\`, named `2026-08-30_gemini37_<task>.md`.
2. Use the structure in `RESPONSE-TEMPLATE.md` (findings with severity/claim/reasoning/evidence/proposed fix; survivors; score). For code findings, EVIDENCE must cite `file:line` and, wherever possible, include a concrete failing input or 5-line proof-of-concept.
3. Adversarial, no flattery. Name only prior art / RFCs you are confident exist — citations are verified afterward and invented ones are logged against the contribution.
4. Do the tasks in the priority order below; if time-limited, task 10 alone is worth more than 11–13 combined.

## What changed since the pack you saw in round 2

Spec v0.3.1 → **v0.4.2**: your round-2 findings merged (§25 — 2D cap rule, action DAG, budget conservation, RFC 9421 Micro-Core, FORCE_HALT settlement gates, two-track era digest, counterparty-bound vouchers, STH gossip, VRF commit-reveal, evidence redaction); NEW §26 (lifespan, succession, economic mortality, HANDOFF, the Accountability Chain invariant). Full protocol texts now exist (LIP-1, LIP-2, LIP-4 — you only ever saw condensed §9 summaries). And there is now **working code**: a zero-dependency reference library (25/25 tests) and a runnable overnight demo whose replay verifies 191 signatures/hashes, with real Merkle-log registration and Bitcoin-anchored artifacts.

## Task 10 — HOSTILE CODE REVIEW (top priority; file: `…_code-review.md`)

Review as the engineer who finds the bug by reading the diff. Targets:
- `E:\LivingAIAgents\lap-reference\src\` — `crypto-util.js` (base58, did:key, SPKI wrap, JCS subset, URI normalization), `jws.js` (EdDSA JWS sign/verify, passport checks), `algebra.js` (LIP-3 checker: DAG, path subsumption, 2D caps, effective sets, budget conservation), `microcore.js` (LIP-4 invariant), `merkle-log.js` (RFC 6962 tree, inclusion proofs, salted commitments).
- `E:\LivingAIAgents\lap-reference\test\` — what the tests do NOT cover.
- `E:\LivingAIAgents\lap-demo\demo.js` + `replay.js` — does the demo actually exercise what it narrates; can replay be fooled.

Hunt specifically: algorithm-confusion or header-tampering in JWS handling; base58/did:key edge cases (leading zeros, wrong lengths, non-canonical encodings); JCS subset divergence from RFC 8785 (floats, non-ASCII, lone surrogates); URI normalization bypasses in `normalizeUri` (userinfo, ports, default ports, trailing dots, percent-case); `pathSubsumes` wildcard corner cases (empty paths, `**` at root, child wildcard vs parent `**`); `capSubsumes` epoch_total/tx interactions; the greedy conservation matcher (construct an ordering exploit or confirm the documented incompleteness is the only issue); `counterpartySubsumes` with duplicate/normalized-colliding DIDs; Merkle proof malleability (odd trees, single-leaf, proof-for-wrong-size); timing/verify-return-value misuse; anything the demo signs with the wrong key or verifies against itself. Deliver concrete failing inputs.

## Task 11 — LIP CONFORMANCE & CONSISTENCY AUDIT (file: `…_lip-audit.md`)

Read `output\lip\LIP-1…LIP-4` in full plus `output\LAP-founding-document.md` §24–§26. Find: contradictions between LIPs and the founding doc; normative statements missing RFC-2119 keywords; undefined error paths (what happens on X is unstated); places where the CODE does something the LIP text doesn't say or vice versa (cite file:line against LIP section); missing MUSTs an implementer would trip over; the LIP-2 state machine's unhandled transitions (timeouts per state, duplicate messages, HAIL replays).

## Task 12 — ATTACK §26: LIFECYCLE, SUCCESSION, ECONOMIC MORTALITY (file: `…_lifecycle-attack.md`)

Nobody has reviewed this. Attack: contested succession (two claimed successors; forged death evidence to force succession dormancy — can an attacker *kill the principal on paper* to freeze or