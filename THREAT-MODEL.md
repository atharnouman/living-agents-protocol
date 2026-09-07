# Threat model

*What the Living Agents Protocol defends against, how the reference implementations prove it, and what it deliberately does not defend against. Written for spec v0.4.9; every LIP change should touch this file.*

Read this together with [SECURITY.md](SECURITY.md) (how to report), [CONFORMANCE.md](CONFORMANCE.md) (what a conforming Micro-Core must refuse), and [`llm-collab/IMPROVEMENTS-LOG.md`](llm-collab/IMPROVEMENTS-LOG.md) (every finding to date — merged, softened, or rejected, with reasons).

## 1. Scope

Covered: the Agent Passport and Genesis Record (LIP-1), the MEET handshake (LIP-2), the Scope Algebra (LIP-3), Micro-Core (LIP-4), the transparency-log bindings (RFC 6962 Merkle log, Sigstore Rekor), `lap-git`, and the two reference ports (`lap-reference/`, `lap-python/`). Each defended threat below names the mechanism, where it is enforced, and the test that fails if the defence regresses. Where a defence is a *deployment* duty rather than code, it says so.

## 2. Assets

| Asset | Held by | If compromised |
|---|---|---|
| Principal signing key | the responsible human or organisation | Passports can be minted for any agent, within that principal's own standing. Proof class bounds the damage (a `self-asserted` principal has no standing beyond itself). |
| Agent key | the running agent | The attacker can act within the passport envelope until `exp`. Nothing more: every check is enforced by the verifier, not by the agent. |
| Passport (JWT) | presented on every request | Alone, useless: bound to one audience, one agent key, one expiry, one envelope. |
| Envelope / scopes | inside the passport | Defines unsupervised authority; the algebra bounds what any delegate can derive from it. |
| Tool-server key | the tool server | Receipts for that server become forgeable. Persist and publish the DID; rotate like any service key. |
| Receipts and recorder logs | both parties | The evidence trail. Losing it turns a dispute into assertion against assertion. |
| Genesis Record and log inclusion | public logs | Birth is witnessed by an operator that verified the principal's signature before admission. One operator is not yet the ≥2 the spec requires for certification. |
| MEET transcript and reservation tickets | the two counterparties | Fair-exchange closure and replay protection for stranger-agent sessions. |
| The maintainers' `lap-git` agent key | this repository | Commits inside the maintainer envelope could be signed by an impostor. The envelope still bounds *which paths*. |

## 3. Actors and trust boundaries

- **Principal → agent.** The principal delegates by signing a passport. The agent is never trusted to stay inside its envelope; every verifier enforces it.
- **Agent → tool server (LIP-4).** The server trusts nothing in a request except what verifies against keys named in the passport. A valid passport is *identity*, not authorization: the server maps the verified issuer to a local tenant and applies its own policy.
- **Agent ↔ stranger agent (LIP-2).** Mutual proof of keys, then a transcript-hashed handshake with reservation tickets, so neither side can rewrite what was agreed.
- **Everyone → transparency-log operator.** Trust-minimised: the verifier checks the inclusion proof and the log's signed timestamp itself. Today one operator (Rekor) is bound; certification needs two unrelated ones.
- **The network.** Assumed hostile: capture, replay, modification, and delay are all in scope.
- **Proxies and routers between the verifier and the resource.** They normalise paths *after* authorization, which is why the algebra refuses dot-segments, encoded separators, queries, fragments, and empty segments instead of interpreting them.
- **The project's own AI agents.** Commits by agents carry a passport whose audience is this repository and whose envelope lists the paths the agent may touch; the commit is refused before it exists if a staged path falls outside.

## 4. Attacker model

Assumed capabilities: full control of the network; the ability to run any number of agents and principals (self-asserted passports cost nothing); crafting arbitrary JSON, envelopes, and URIs; possession of a captured, valid header pair; control of a tool server; being a legitimate delegate that tries to widen its own authority; and being an insider agent with commit access to a repository.

Not assumed: breaking Ed25519 or SHA-256; holding both the principal key and the agent key; controlling both a transparency log and its timestamp key.

## 5. Threats and defences

| # | Threat | Defence | Enforced in | Regression tests |
|---|---|---|---|---|
| 1 | Forged or altered passport claims | Ed25519 JWS over JCS-canonical claims; `did:key` needs no network to resolve (LIP-1 §3, §6) | `lap-reference/src/jws.js`, `microcore.js`; `lap-python/living_agents/jws.py` | `test/vectors.test.js`, `tests/test_vectors.py` (tamper ⇒ `LAP_ERR_SIG`; CONFORMANCE check 5) |
| 2 | A valid passport replayed at a different server | Audience is mandatory and checked; a verifier with no configured audience fails closed (LIP-4 F4) | `verifyMicroCorePassport` / `verify_microcore_passport` | `test/round4.test.js`, `tests/test_audit_round4.py::test_f4_audience_mandatory` |
| 3 | A captured header pair replayed elsewhere, or with a different body | Holder-of-key: the request-signature key is derived from the verified passport's `sub`, never from the request (F2); the RFC 9421 base must cover method, target, content digest, and passport hash (F3) | `verifyRequestSignature` / `verify_request_signature` | `round4.test.js`, `test_audit_round4.py::test_f2_request_signature_key_from_sub`, CONFORMANCE check 8, the MCP CI job (tampered arguments refused with `LAP_ERR_DIGEST`) |
| 4 | A signature or token re-encoded to evade text-keyed state (idempotency keys, dedup, denylists) while still verifying | Strict canonical base64url; non-canonical input is `LAP_ERR_ENCODING` (LIP-4 v0.4.8) | `crypto-util.js` `b64urlDecode`; `crypto_util.py` `b64url_decode` | `test/encoding.test.js`, `tests/test_encoding.py` |
| 5 | A delegate widens its authority: sub-verb escalation, path-prefix escape, wildcard widening, dot-segment or encoded-separator traversal, window inversion, cross-currency caps, deny-list bypass, budget replication across siblings, depth or decay loosening | The Scope Algebra (LIP-3): registry DAG with no string prefixing; whole-segment matching with terminal-only wildcards; closed URI syntax; two-dimensional caps; conservation debited in parent-window units (F7); schema before semantics (F8, v0.3); caps inside the single-scope predicate (F9); effective-set counterparties | `algebra.js`, `algebra.py` | `test/algebra.test.js`, `round4.test.js`, `tests/test_algebra.py`, and the property-based fuzzers `test/fuzz.test.js` / `tests/test_fuzz.py` (eight properties plus a committed cross-port decision digest) |
| 6 | Identity mistaken for authorization: any valid passport gets in | Server policy hooks `allowedIssuers` / `minProofClass`; the spec requires mapping the verified issuer to a local tenant and refusing `self-asserted` for money or PII unless configured (F1) | `microcore.js`; `mcp_middleware.py` | `round4.test.js`, `tests/test_middleware.py::test_mcp_server_policy_can_refuse_a_valid_passport` |
| 7 | Cap bypass through argument binding (positional arguments, missing amount) | Middleware binds the real invocation with defaults applied; a capped operation with an indeterminate amount is refused (F5) | `mcp_middleware.py` | `tests/test_middleware.py::test_verify_envelope_positional_args_cannot_bypass_cap`; the MCP CI job (over-cap refused) |
| 8 | A signature over one set of tool arguments reused for another | The signed body is derived from the server's own bound arguments, with the auth context excluded | `mcp_middleware.py` | `tests/test_middleware.py::test_mcp_signature_does_not_transfer_to_different_args` |
| 9 | Duplicate execution of a retried mutating call | Atomic `(agent, Idempotency-Key)` claim before execution (F6); distributed backing is a production MUST | `IdempotencyCache` in both ports | `test_audit_round4.py::test_f6_idempotency_claim_atomic` |
| 10 | Repudiation: "that response was never produced" | Tripartite receipt signed by the server over the request and response hashes; both parties log it (LIP-4 §3) | `mintReceipt` / `verifyReceipt` | CONFORMANCE check 10; the MCP example verifies every receipt |
| 11 | Acting on a counterparty that is no longer there (fake liveness) | Pulse-gated suspension: authority suspends when pulses stop, held work resumes on recovery, every transition dual-signed | `lap-demo/` (single-process replay: 191 checks; `lap-demo/net/` over real sockets with a real crash) | `node demo.js && node replay.js` in CI, including tamper detection |
| 12 | Rewritten history, or a birth nobody witnessed | RFC 6962 Merkle log with inclusion proofs; Rekor registration verified with LAP's own root reconstruction and Rekor's signed entry timestamp; documents Bitcoin-timestamped via OpenTimestamps | `merkle-log.js`, `rekor.js`; `output/anchors/` | `test/merkle-log.test.js`, `test/rekor.test.js` (offline fixture of a real public entry) |
| 13 | Unattributed or out-of-scope commits by AI agents | `lap-git`: passport with `aud = git://<repo>`, path envelope enforced before the commit exists, tree signature in trailers (spec §20.2) | `lap-git/lap-git.mjs` | `lap-git selftest` in CI; the story in [CASE-STUDY.md](CASE-STUDY.md) |
| 14 | Parser abuse: oversized identifiers, malformed input that crashes a verifier | Length-bounded `did:key` decoding (F12); strict base64url; schema before semantics; typed errors only | `crypto-util.js` / `crypto_util.py`, `algebra.*` | `test_audit_round4.py::test_f12_overlong_did_rejected`, fuzz property 7 in both ports |
| 15 | Two conforming verifiers disagreeing on the same envelope | Shared deterministic vectors; a committed cross-port decision digest; values above 2^53−1 rejected by every port; exact-integer window arithmetic | `output/lip/test-vectors/` | `test/vectors.test.js`, `tests/test_vectors.py`, fuzz property 8 (`algebra-fuzz-digest.json`) |
| 16 | Corruption of this repository's own artifacts (an earlier incident: silent digit and glyph swaps in the spec) | Integrity canaries in the test suite; every release restamped and recorded in `output/anchors/ANCHORS.md` | `test/integrity.test.js` | runs on every CI job |

## 6. Out of scope, and residual risk

Stated plainly, because a threat model that lists only wins is marketing.

- **A compromised agent key** acts inside its envelope until `exp`. In Micro-Core a short expiry *is* the revocation; there is no revocation infrastructure yet (LIP-1 open items, LIP-4 §4).
- **A compromised or dishonest principal.** Proof classes are claims about proofing, and `self-asserted` means none. Principal proofing is open problem §22.2 of the founding document.
- **Clones.** Keys are copyable, so two instances of one agent can fork MEET state and receipts. Open problem §22.8; the spec sketches an instance lease, nothing ships.
- **Key custody and recovery** (§22.3) and **witness economics** for liveness (§22.5) are unsolved.
- **Cumulative budgets** are not enforced by Micro-Core; `max_cumulative` is informational there and belongs to a spend authorizer with an atomic per-bucket ledger.
- **Sibling envelopes issued separately** are the issuer's accounting duty (LIP-3 §6); the algebra makes one envelope's verification sound, not global accounting.
- **Bucket-boundary bursts** of roughly 2× at window edges (LIP-3 §4); mitigate with `max_per_tx`.
- **Greedy incompleteness.** Attenuation checking is sound but can reject a child set that a different parent assignment would satisfy (LIP-3 §6).
- **Transport binding over stdio.** The MCP example cannot observe method and target; over HTTP the headers and the observed target must be bound by the transport layer.
- **One log operator.** Certification requires inclusion proofs from at least two unrelated operators; the reference binds one.
- **Clock skew** of ±60 s is tolerated by design.
- **Timing side channels.** Hash comparisons are constant-time where the conformance checklist requires it; the ports have not been audited for timing behaviour more broadly.
- **Denial of service** against servers is deployment territory; LIP-2 §6 bounds handshake cost only.
- **Privacy of public logs.** Principal references in public records must be salted commitments (founding document §14.5); the demos use pseudonymous `did:key` identifiers.
- **Supply chain.** The Node library has zero dependencies and the Python port one (`cryptography`); releases are tagged but not yet signed with Sigstore.
- **These are reference implementations,** reviewed adversarially by models and by their author, not audited by an independent human security firm, not formally verified, and not yet backed by production incident data.

## 7. Assurance so far

- Five adversarial review rounds across three model families, about 150 verified fixes, with rejections logged and reasoned.
- One purely hostile third-model code audit: twelve findings, every one reproduced before it was fixed, in both ports.
- Self-found since then: base64url malleability surfaced by a flaky self-test (2026-09-06), and a property-based fuzzing round that found an identical `*` delegation being refused, language-level type errors on malformed scopes, one-unit floating-point divergence between the ports, and a missing effective-set rule in the Python port (2026-09-08).
- Continuous checks on every push: both test suites, the overnight demo with replay and tamper detection, the MCP round-trip, and the `lap-git` self-test. Current counts are on the README badge.
- Not yet done: fuzzing of the JWS and DID parsers (only the algebra is fuzzed), an external human audit, formal verification.

## 8. Reporting

See [SECURITY.md](SECURITY.md). Reports that advance an open problem are as welcome as defects.
