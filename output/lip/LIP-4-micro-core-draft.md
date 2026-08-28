# LIP-4: LAP Micro-Core

*Status: DRAFT v0.1 — 2026-08-29 (hardened per spec §25.2). Layer: profile over L2+L5. Requires: LIP-1 (passport), LIP-3 (algebra subset). Test vectors: `test-vectors/vectors.json` (`micro_core` section — real Ed25519 signatures). RFC 2119 keywords apply.*

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
3. Check the invoked operation matches `envelope.act` (registered-verb equality — no prefix logic in Micro-Core) and the target path matches `envelope.res` segment-wise.
4. If `cap` present and the operation carries an amount: check `amount ≤ max_per_tx` in the exact `unit`. *(Micro-Core enforces per-transaction caps only; cumulative budgets require a spend authorizer — servers MUST treat any `max_cumulative` field as informational.)*
5. For mutating requests: if `(sub, Idempotency-Key)` was already executed, return the cached receipt WITHOUT re-executing.
6. On failure, return the matching error: `LAP_ERR_{PASSPORT_SIG | AUDIENCE | EXPIRED | REQ_SIG | DIGEST | ACT | RES | CAP | REPLAY}` with HTTP 401/403.

## 3. The receipt (Normative)

Success responses carry:

```
LAP-Receipt: sha256:<request-body-hash>:sha256:<response-body-hash>:<server-signature-b64url>
```

signed by the server's key over the two hashes. Both parties MUST append `(timestamp, method, target, passport-hash, receipt)` to a local append-only log. *Informative:* this tripartite line is the seed of the Flight Recorder — a portable, dual-held proof that *this request produced this response*, which is what a billing dispute actually needs.

## 4. What Micro-Core is NOT (Normative scope fence)

No cumulative budget enforcement (authorizer territory), no revocation infrastructure (short `exp` is the revocation), no MEET, no pulses, no registries, no trust states. A server MAY additionally verify LIP-1 proof classes and registration proofs; that is the upgrade ramp, not the requirement.

## 5. Afternoon checklist (Informative)

Client: mint one Ed25519 keypair per principal and agent (~5 lines with any JOSE lib); build the JWT; sign requests per RFC 9421 (libraries exist for JS/Python/Go). Server: ~120 lines — JWS verify, five checks of §2, receipt signing, an idempotency cache (any KV store). Interop target: verify the `micro_core` section of `vectors.json` byte-for-byte — the passport JWT, the RFC 9421 signature base, and the receipt line are all real signatures over the shown bytes.

## 6. Upgrade path (Informative)

Same passport → LIP-1 full verification (proof classes, registration, revocation). Same envelope grammar → LIP-3 full algebra (attenuation, delegation). Same receipt line → Flight Recorder entries. Add MEET (LIP-2) when the counterparty is a stranger agent rather than your own tool server. Nothing is thrown away.
