# LIP-4: LAP Micro-Core

*Status: DRAFT v0.1 — 2026-08-29 (hardened per spec §25.2; erratum 2026-10-17 on the amount rule in §2 step 5; erratum 2026-10-28 on recognition before authority, §2 step 3). Layer: profile over L2+L5. Requires: LIP-1 (passport), LIP-3 (algebra subset). Test vectors: `test-vectors/vectors.json` (`micro_core` section — real Ed25519 signatures), `test-vectors/microcore-cap-vectors.json` (amount and cap schema) and `test-vectors/microcore-replay-vectors.json` (the idempotency claim under authority replacement and key reuse). RFC 2119 keywords apply.*

**The pitch (Informative):** Micro-Core is the afternoon-sized subset of LAP with single-player utility — one HTTP header pair answers "*what may this agent do here, on whose authority?*" between an agent and any MCP/A2A tool server, with a receipt trail. No registries, no witnesses, no handshake required. It is deliberately the first thing anyone implements, and everything in it upgrades losslessly to full LAP.

---

## 1. The two request headers (Normative)

**`LAP-Passport`** — a JWT (JWS compact, `alg: EdDSA`) issued and signed by the *principal*, carrying the agent's authority:

```json
{ "iss": "did:key:z6MkekRLWH…ms1TW",          // principal
  "sub": "did:key:z6MksMrZDk…PPHEC",          // agent key
  "aud": "did:web:tools.example.com",          // THIS recipient — MUST be present
  "iat": 1787000000, "exp": 1787000600,
  "lap": { "v": 0, "proof_class": "self-asserted",
           "constitution_hash": "…",
           "envelope": { "act": ["finance:pay"],
                          "res": "mcp://tools.example.com/billing/**",
                          "cap": { "max_per_tx": 5000, "unit": "USD", "window": "tx" } } } }
```

- `aud` MUST name the recipient (DID or canonical origin). A token without an audience, or with a different audience, MUST be rejected — this kills cross-server replay.
- **Upgrade compatibility (v0.2)**: servers MUST accept `typ` of either `"lap-microcore+jwt"` or `"lap-passport+jwt"`; when a full LIP-1 passport is presented (which carries no inline envelope), the envelope arrives in an accompanying `LAP-Envelope` header (an OAuth RAR object per LIP-3), covered by the request signature. This makes the Micro-Core→full-LAP upgrade a strict addition, never a breaking change.
- `envelope.act` entries MUST be literal registered verbs — `"*"` is invalid in Micro-Core and MUST be rejected loudly (`LAP_ERR_ACT`), not silently never-matched.
- `exp − iat` SHOULD be short (minutes–hours). ±60s skew tolerance MUST be applied; `iat` MUST be present.
- `act`/`res`/`cap` use the LIP-3 algebra subset (registered verbs, segment-tokenized paths, strict units).

**`LAP-Signature`** — per-request proof of agent key possession, profiled on **HTTP Message Signatures (RFC 9421)**, signed by the *agent* (`sub`) key over at minimum:

```
"@method" "@target-uri" "content-digest" "lap-passport-hash"
```

where `content-digest` is the SHA-256 of the request body (RFC 9530 form) and `lap-passport-hash` is the SHA-256 of the presented `LAP-Passport` value. A request whose signature omits any of these components MUST be rejected. (DPoP, RFC 9449, is an acceptable alternative profile.) *Informative:* this binds passport → request → body → recipient; a captured header pair authorizes nothing anywhere else, and a mutated body breaks the digest.

**`Idempotency-Key`** — MUST accompany every mutating request, and MUST be a covered component of `LAP-Signature`.

## 2. Server verification invariant (Normative — the whole server-side spec)

On each request the server MUST, in order:
1. Verify `LAP-Passport` JWS against `iss` (SSRF-filtered, cached DID resolution; `did:key` needs no network); check `iat`/`exp` with skew; check `aud` names *this* server.
2. Verify `LAP-Signature` against `sub`, covering method, target URI, content digest, passport hash (and idempotency key when present); recompute the body digest.
3. For mutating requests: **recognise** the key before consulting the envelope *(erratum 2026-10-28; library 0.4.14)*. Look up the claim `(tenant, sub, Idempotency-Key)`, where the tenant is the server's F1 mapping of the verified `iss` (by default the normalised `iss` itself), together with the request identity: the signed method, target URI and content digest. The same key with a different identity is refused in every state (`LAP_ERR_KEY_REUSE`); an in-flight claim is refused (`LAP_ERR_REPLAY`); an indeterminate one is refused until reconciled (recovery rule below); a completed one returns the stored result and receipt WITHOUT re-executing, provided the envelope presented now still covers the stored request's action, resource and unit (step 4, and the schema, presence and unit parts of step 5, with `amount ≤ max_per_tx` not compared: a replay spends nothing), otherwise the server says the key executed earlier and withholds the result (`LAP_ERR_REPLAY_WITHHELD`), without executing and without a new claim. The lookup reserves nothing. Only an absent key continues to step 4.
4. Check the invoked operation matches `envelope.act` (registered-verb equality — no prefix logic in Micro-Core) and the target path matches `envelope.res` segment-wise.
5. If `cap` present and the operation carries an amount: check `amount ≤ max_per_tx` in the exact `unit`. The amount MUST be a non-negative exact integer no larger than 2^53−1; a negative, fractional, boolean, non-numeric, NaN or infinite amount MUST be refused (`LAP_ERR_CAP`) before any comparison, and the cap MUST pass schema validation first (`max_per_tx` a non-negative exact integer, `unit` a non-empty string; LIP-3 §4). *(Erratum 2026-10-17: the amount rule was implied by LIP-3 §4 but not stated here; both reference ports compared `-500000 ≤ 1000` as true until library 0.4.13. Micro-Core enforces per-transaction caps only; cumulative budgets require a spend authorizer — servers MUST treat any `max_cumulative` field as informational.)*
6. For mutating requests: claim `(tenant, sub, Idempotency-Key)` atomically before executing, recording the request identity, the passport hash and the time with the reservation; every outcome of step 3 is handled again here, since a twin may have won the slot in between. The reservation is held across the execution: if the tool raises, the claim becomes indeterminate (recovery rule below), unless the tool itself reports that the effect never began, which frees the key.
7. On failure, return the matching error: `LAP_ERR_{PASSPORT_SIG | AUDIENCE | EXPIRED | REQ_SIG | SIG_PARAMS | DIGEST | ACT | RES | CAP | ISSUER | PROOF_CLASS | IDEMPOTENCY | KEY_REUSE | REPLAY | REPLAY_WITHHELD}`: HTTP 401 for a passport or signature failure; 403 for an envelope or cap refusal and for a withheld replay; 400 for a missing idempotency key; 409 for a key in flight or indeterminate; 422 for a key reused with a different request (the status codes of draft-ietf-httpapi-idempotency-key-header).

**Hardening rules (v0.2, round-4 audit — all MUST):**
- **Identity is not authorization (F1).** A verified passport proves who the agent is and that its envelope is intact; it does NOT grant authority over a server-owned resource. A server acting on its own accounts MUST map the verified `iss` (and its proof class) to a locally recognized tenant/account, and MUST refuse `self-asserted` passports for money/PII unless explicitly configured to accept them. Micro-Core with `self-asserted` is a single-operator self-serve wedge, not a cross-tenant authorizer.
- **Holder-of-key (F2).** The `LAP-Signature` verification key MUST be derived from the *verified passport's* `sub`, never from a request-supplied identifier — otherwise a captured passport plus any attacker keypair passes.
- **Canonical encoding (v0.4.8).** `LAP-Signature`, receipt signatures, and every base64url field MUST be canonical base64url (RFC 4648 §5, unpadded, zero trailing bits); verifiers MUST reject anything else (`LAP_ERR_ENCODING`). A lenient decoder gives one signature many textual forms, and text-keyed state (passport hashes, idempotency and dedup keys, denylists) becomes evadable by re-encoding while the signature still verifies.
- **Covered components (F3).** The signature base MUST include `@method`, `@target-uri`, `content-digest`, `lap-passport-hash`, and `@signature-params`; the server MUST reconstruct method/target from the trusted transport and compare. A short ad-hoc base missing components MUST be rejected. A server that maps a tool to a resource MUST compare the signed `@target-uri` to that resource (the reference FastMCP middleware binds it by default, v0.4.10), so a signature scoped to one tool cannot be replayed against another under one envelope.
- **Audience is mandatory (F4).** The server identity/expected audience is required at verification; a verifier with no configured audience MUST fail closed, not accept any audience.
- **Capped operation, indeterminate amount ⇒ reject (F5).** If `cap` is present and the amount cannot be unambiguously bound from the invocation, the request MUST be refused. Middleware MUST bind positional and keyword arguments (never read only keywords).
- **Amount and cap are exact non-negative integers (erratum 2026-10-17).** A comparison is only meaningful between two non-negative exact integers: `-500 ≤ 1000` is true, NaN compares false both ways, and a loosely typed verifier coerces strings and booleans. Verifiers MUST type-check the amount and the cap before comparing, and MUST refuse a present-but-malformed cap (an empty object is not "no cap"). Shared vectors: `test-vectors/microcore-cap-vectors.json`.
- **Reservation is three-state (v0.4.10).** A reference `claim()` MUST distinguish a fresh reservation from an in-flight one from a completed receipt, so a concurrent duplicate of a mutating request is refused, not re-executed. Since 0.4.14 it also carries the request identity and reports `key_reuse`.
- **Idempotency (F6).** The `(tenant, sub, Idempotency-Key)` claim MUST be atomic and durable across replicas in production (e.g., a DB unique constraint or Redis `SET NX`), and the request identity MUST land in the same atomic write; an in-process map is single-process only and MUST NOT be presented as production-ready.
- **Recognition is independent of authority (erratum 2026-10-28; library 0.4.14).** A claim is keyed by the tenant, the agent key and the idempotency key, never by the passport hash, the envelope or the audience, so replacing the authority document (a raise, a cut, a reissue) never turns the same operation into a fresh entry. Recognition (step 3) precedes the envelope checks; the passport presented now decides whether the stored result is *disclosed* (its action, resource and unit must still be covered), never whether the operation runs again, and a server MUST NOT answer a retry of an executed key with an envelope or cap refusal: a `LAP_ERR_ACT`, `LAP_ERR_RES` or `LAP_ERR_CAP` on a retry therefore means that no execution is recorded under that key. The identity of the request (signed method, target, content digest; not the passport hash) MUST be recorded with the reservation, and the same key with a different identity MUST be refused in every state (`LAP_ERR_KEY_REUSE`); a new key is a new operation even for an identical request. Claims are kept for a published retention window independent of passport lifetime: a claim MUST NOT be evicted because the passport that made it expired, since a reissued passport passes `exp`. Two executions with identical request and response bytes under distinct keys produce byte-identical receipts (Ed25519 is deterministic), so a receipt alone does not prove that a retry did not execute again; the claim record and the replay marker do. A tool that raises leaves its claim indeterminate unless it reports that the effect never began. *Found by two independent model reviews on 2026-10-28, which reproduced three faults in 0.4.13: a retry after a cap cut refused by the cap before the stored result was found; one key reused for a different request, or by another tool sharing the cache, replaying the first result; and a second principal with the same agent key replaying the first principal's execution. Shared vectors: `test-vectors/microcore-replay-vectors.json`.*
- **Recovery of an in-flight claim (2026-10-21).** The reservation MUST be written durably before the external effect begins, and the completion (result and receipt) after it. A claim whose executor is known to have died between the two is *indeterminate*: the effect may or may not have happened. An indeterminate claim MUST NOT be executed again, MUST NOT be released by the passage of time alone, and resolves only by reconciliation against the effect's system of record: if the effect happened, the claim is completed with the reconciled result and a receipt minted over it, and the audit record SHOULD say the result came from reconciliation; if it verifiably did not, the claim is released and the next request with that key executes fresh. Where the effect cannot be queried, the decision belongs to the deployment (a compensating action or a person) and MUST NOT be inferred from the absence of a receipt. So that reconciliation has something to query, the reservation SHOULD record a stable identifier for the effect at its system of record: the idempotency key itself when that system accepts one, otherwise the identifier the system returns, written as soon as it is known; without such an identifier the claim stays indeterminate until a person or a compensating action resolves it (added 2026-10-22 from the same review). A client refused because its key is indeterminate MUST NOT choose a new key for the same intended execution. The reference caches carry the state (`mark_indeterminate` / `markIndeterminate`, `release`); an in-process map cannot observe its own death, so a durable backend MUST detect dead executors (for example through a lease the executor renews) and mark their claims. Raised by an external review of the A2A binding (A2A #2323, 2026-10-20), whose two-process probe reproduced the documented process-local limit.

## 3. The receipt (Normative)

Success responses carry:

```
LAP-Receipt: sha256:<request-body-hash>:sha256:<response-body-hash>:<server-signature-b64url>
```

signed by the server's key over the two hashes. Both parties MUST append `(timestamp, method, target, passport-hash, receipt)` to a local append-only log. *Informative:* this tripartite line is the seed of the Flight Recorder — a portable, dual-held proof that *this request produced this response*, which is what a billing dispute actually needs.

## 4. What Micro-Core is NOT (Normative scope fence)

No cumulative budget enforcement (authorizer territory), no revocation infrastructure (short `exp` is the revocation), no MEET, no pulses, no registries, no trust states. A server MAY additionally verify LIP-1 proof classes and registration proofs; that is the upgrade ramp, not the requirement.

## 5. Afternoon checklist (Informative)

Client: mint one Ed25519 keypair per principal and agent (~5 lines with any JOSE lib); build the JWT; sign requests per RFC 9421 (libraries exist for JS/Python/Go). Server: ~150 lines — JWS verify, the six checks of §2 (recognition of the idempotency key before the envelope included), receipt signing, an idempotency cache (any KV store that can hold the request identity with the reservation). Interop target: verify the `micro_core` section of `vectors.json` byte-for-byte — the passport JWT, the RFC 9421 signature base, and the receipt line are all real signatures over the shown bytes.

## 6. Upgrade path (Informative)

Same passport → LIP-1 full verification (proof classes, registration, revocation). Same envelope grammar → LIP-3 full algebra (attenuation, delegation). Same receipt line → Flight Recorder entries. Add MEET (LIP-2) when the counterparty is a stranger agent rather than your own tool server. Nothing is thrown away.
