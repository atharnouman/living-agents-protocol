MODEL: Gemini 3.7 Flash
DIMENSION: 10-code-review.md
DATE: 2026-08-30

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: `lap-reference/src/crypto-util.js:39-55`]
    CLAIM: `b58Decode` corrupts buffer lengths on leading zeros and empty inputs, decoding `1` to 2 zero-bytes instead of 1, and empty strings to 1 zero-byte instead of empty buffer.
    REASONING: In `b58Decode`, `n` is initialized to `0n`. If `s` is `"1"` (a single zero byte in base58), the character loop leaves `n = 0n`. `n.toString(16)` yields `"0"`, which is padded to `"00"`, creating `out = Buffer.from([0x00])` (1 byte). Then the pad loop counts one `"1"` (`pad = 1`) and executes `Buffer.concat([Buffer.alloc(1), out])`, returning `Buffer.from([0x00, 0x00])` (2 bytes!). For an empty string `""`, `n = 0n` produces `Buffer.from([0x00])` (1 byte) with `pad = 0`. This will cause key truncation/inflation panics if a DID key contains leading zero bytes.
    EVIDENCE: `crypto-util.js:46-54`:
    ```javascript
    let hex = n.toString(16);
    if (hex.length % 2) hex = "0" + hex;
    let out = Buffer.from(hex, "hex");
    let pad = 0;
    for (const ch of s) { if (ch === "1") pad++; else break; }
    return pad ? Buffer.concat([Buffer.alloc(pad), out]) : out;
    ```
    PROPOSED FIX:
    ```javascript
    export function b58Decode(s) {
      if (!s || s.length === 0) return Buffer.alloc(0);
      let n = 0n;
      for (const ch of s) {
        const v = B58.indexOf(ch);
        if (v < 0) throw new Error(`invalid base58 character: ${ch}`);
        n = n * 58n + BigInt(v);
      }
      let pad = 0;
      for (const ch of s) {
        if (ch === "1") pad++;
        else break;
      }
      if (n === 0n) return Buffer.alloc(pad);
      let hex = n.toString(16);
      if (hex.length % 2) hex = "0" + hex;
      const out = Buffer.from(hex, "hex");
      return pad ? Buffer.concat([Buffer.alloc(pad), out]) : out;
    }
    ```

F2. [SEVERITY: FATAL] [TARGET: `lap-reference/src/microcore.js:34-42`]
    CLAIM: `checkInvocation` performs literal array `.includes(act)` and fails when an envelope grants wildcard action `*` or a DAG parent verb.
    REASONING: If an agent holds an envelope with `act: ["*"]` or `act: ["finance:pay"]`, and invokes a tool expecting `act: "finance:pay:escrow"`, `envelope.act.includes("finance:pay:escrow")` evaluates to `false` and throws `LAP_ERR_ACT`. Micro-Core claims to support registered LIP-3 actions, but `checkInvocation` does not call `dagSubsumes` or handle `*`.
    EVIDENCE: `microcore.js:34-36`:
    ```javascript
    export function checkInvocation(envelope, { act, resource, amount, unit }) {
      if (!envelope.act.includes(act)) throw new Error("LAP_ERR_ACT");
    ```
    PROPOSED FIX: Wire `dagSubsumes` into `checkInvocation`:
    ```javascript
    import { pathSubsumes, dagSubsumes } from "./algebra.js";

    export function checkInvocation(envelope, { act, resource, amount, unit }) {
      const allowed = envelope.act.some((parentAct) => dagSubsumes(parentAct, act));
      if (!allowed) throw new Error("LAP_ERR_ACT");
      if (!pathSubsumes(envelope.res, resource)) throw new Error("LAP_ERR_RES");
      if (envelope.cap && amount !== undefined) {
        if (unit !== envelope.cap.unit) throw new Error("LAP_ERR_CAP: unit");
        if (amount > envelope.cap.max_per_tx) throw new Error("LAP_ERR_CAP");
      }
      return true;
    }
    ```

F3. [SEVERITY: SERIOUS] [TARGET: `lap-reference/src/jws.js:46-56`]
    CLAIM: `verifyPassport` omits mandatory LIP-1 Step 2 URI/DID string normalization prior to signature and claim validation.
    REASONING: LIP-1 §6 specifies a 9-step normative verification sequence where Step 2 mandates Unicode NFC and ASCII-lowercasing normalization (LIP-1 §3) before checking claims. `verifyPassport` skips normalization entirely and compares raw string fields (`payload.principal?.id === payload.id`). If a passport uses mixed-case DID strings or unnormalized unicode characters, identity matching and key resolution will fail or produce false matches.
    EVIDENCE: `jws.js:46-56` decodes and directly inspects `payload.principal?.id` without calling `normalizeUri`.
    PROPOSED FIX: Apply `normalizeUri` in `verifyPassport`:
    ```javascript
    export function verifyPassport(token, { now } = {}) {
      const { header, payload } = decodeJws(token);
      if (payload.v !== "lip1-v0") throw new Error("LAP_ERR_VERSION");
      if (header.alg !== "EdDSA") throw new Error(`LAP_ERR_SIG: alg ${header.alg}`);
      const principalDid = payload.principal?.id ? normalizeUri(payload.principal.id) : null;
      const agentDid = payload.id ? normalizeUri(payload.id) : null;
      if (!principalDid) throw new Error("LAP_ERR_SELF_OWNED: principal missing");
      if (principalDid === agentDid) throw new Error("LAP_ERR_SELF_OWNED");
      verifyJws(token, principalDid);
      checkTimeWindow(payload, now);
      return payload;
    }
    ```

F4. [SEVERITY: SERIOUS] [TARGET: `lap-reference/src/microcore.js:20-30`]
    CLAIM: RFC 9421 signature base parsing in `verifyRequestSignature` relies on fragile exact newline `split("\n")` matching that breaks on CRLF line endings or header spacing variations.
    REASONING: HTTP intermediaries and different server environments frequently normalize line endings (converting `\n` to `\r\n`) or adjust whitespace around colons. `verifyRequestSignature` checks for exact line strings via `.split("\n").includes(...)`. If a signature base arrives with `\r\n`, the string comparison fails even though the cryptographic signature is over the canonical bytes.
    EVIDENCE: `microcore.js:25-28`:
    ```javascript
    const expectedDigest = `"content-digest": sha-256=:${sha256B64url(requestBody)}:`;
    if (!signatureBase.split("\n").includes(expectedDigest)) throw new Error("LAP_ERR_DIGEST");
    const expectedPassportLine = `"lap-passport-hash": sha256:${sha256Hex(passportJwt)}`;
    if (!signatureBase.split("\n").includes(expectedPassportLine)) throw new Error("LAP_ERR_DIGEST: passport hash");
    ```
    PROPOSED FIX: Normalize newlines in signatureBase before parsing:
    ```javascript
    const lines = signatureBase.replace(/\r\n/g, "\n").split("\n").map(l => l.trim());
    if (!lines.includes(expectedDigest)) throw new Error("LAP_ERR_DIGEST");
    if (!lines.includes(expectedPassportLine)) throw new Error("LAP_ERR_DIGEST: passport hash");
    ```

F5. [SEVERITY: MODERATE] [TARGET: `lap-reference/src/algebra.js:108-110`]
    CLAIM: Floating-point arithmetic in `capSubsumes` without explicit integer floor truncation introduces precision jitter in sub-bucket time scaling.
    REASONING: `capSubsumes` evaluates `childCap.max_cumulative <= parentCap.max_cumulative * (cSec / pSec)`. In JavaScript, dividing integers (e.g. $100 \times (3600 / 86400) = 4.166666...$) produces floating point numbers. If an integer cap is tested against a float, rounding discrepancies across language ports (Python vs JS vs Rust) will produce divergent attenuation verdicts on edge numbers.
    EVIDENCE: `algebra.js:109`: `return childCap.max_cumulative <= parentCap.max_cumulative * (cSec / pSec);`
    PROPOSED FIX: Use integer floor arithmetic:
    ```javascript
    const scaledMax = Math.floor((parentCap.max_cumulative * cSec) / pSec);
    return childCap.max_cumulative <= scaledMax;
    ```

F6. [SEVERITY: MODERATE] [TARGET: `lap-reference/src/merkle-log.js:25-27` & `microcore.js:63-69`]
    CLAIM: Commitment and receipt verification uses early-exit string equality (`===`) vulnerable to timing side-channel attacks.
    REASONING: `verifyCommitment` checks `saltedCommitment(principalDid, saltHex).commitment === commitmentHex` using standard V8 string comparison. While salt entropy is high, using non-constant-time comparisons on secret commitments and signature-derived digests creates timing leakage surfaces.
    EVIDENCE: `merkle-log.js:26`: `return saltedCommitment(principalDid, saltHex).commitment === commitmentHex;`
    PROPOSED FIX: Use `crypto.timingSafeEqual`:
    ```javascript
    import { timingSafeEqual } from "node:crypto";

    export function verifyCommitment(commitmentHex, saltHex, principalDid) {
      const a = Buffer.from(saltedCommitment(principalDid, saltHex).commitment, "hex");
      const b = Buffer.from(commitmentHex, "hex");
      return a.length === b.length && timingSafeEqual(a, b);
    }
    ```

F7. [SEVERITY: MODERATE] [TARGET: `lap-demo/demo.js:131-137`, `173-203`]
    CLAIM: The Reservation Ticket generated and verified during MEET CHARTER is completely unreferenced and unenforced in subsequent `buy()` tool transactions.
    REASONING: In `demo.js:132-137`, Alice mints an authorizer-signed reservation ticket and Bob verifies it. However, when `buy()` executes at lines 173-203, Alice generates a standard `mcJwt` passport and passes the order directly. Bob never checks that the payment matches or consumes the pre-authorized reservation ticket nonce. The reservation ticket is demonstrated purely as an isolated handshake artifact rather than an integrated settlement constraint.
    EVIDENCE: `demo.js:176-193` does not include `ticket.nonce` in `mcClaims` or `base`, and Bob does not check the ticket during `buy()`.
    PROPOSED FIX: Bind the reservation ticket nonce into the Micro-Core request signature base (`"lap-reservation-nonce": ticket.nonce`) and verify in `checkInvocation` that the transaction amount is debited against the ticket.

F8. [SEVERITY: MODERATE] [TARGET: `lap-demo/demo.js:161-162`]
    CLAIM: The PULSE step in `demo.js` configures mutual 1-on-1 witnessing between transacting peers, contradicting the $\ge 2$ independent witness architecture.
    REASONING: In `demo.js:161-162`, Alice names `[bob.agent.did]` as her witness, and Bob names `[alice.agent.did]`. While functional for a 2-party demo script, mutual peer-witnessing means when Bob crashes, Bob cannot witness Alice, and Alice has no independent third-party witness to attest to Bob's non-liveness.
    EVIDENCE: `demo.js:161-162`:
    ```javascript
    meetSend(alice, "PULSE", { cadence: 30, witness: [bob.agent.did] });
    meetSend(bob, "PULSE", { cadence: 30, witness: [alice.agent.did] });
    ```
    PROPOSED FIX: Explicitly add a mock independent third-party witness node (`witnessNode.agent.did`) to the demo topology to demonstrate true multi-witness consensus before suspension.

F9. [SEVERITY: MINOR] [TARGET: `lap-reference/src/crypto-util.js:105-118`]
    CLAIM: `jcs()` throws on valid JSON floating point numbers instead of formatting per RFC 8785 section 3.2.2.3.
    REASONING: `jcs()` explicitly throws `new Error("JCS subset: integers only")` if `!Number.isInteger(value)`. While the current LAP subset restricts numeric caps to integers, a generic JSON payload containing standard floats will throw rather than canonicalizing, causing interoperability failures if upstream JSON contains float fields.
    EVIDENCE: `crypto-util.js:108`: `if (!Number.isInteger(value)) throw new Error("JCS subset: integers only");`
    PROPOSED FIX: Document explicitly in module docstrings that `jcs` is an integer-only subset, or implement RFC 8785 float serialization (ECMAScript `JSON.stringify` standard output for non-integers).

---

## 5 VALUABLE RUNNABLE TEST CASES (Test Coverage Gaps)

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { b58Decode, b58Encode, didKeyToRawPublicKey } from "../src/crypto-util.js";
import { dagSubsumes, capSubsumes } from "../src/algebra.js";
import { checkInvocation, makeIdempotencyCache } from "../src/microcore.js";

// Test 1: Action Wildcard and Hierarchy in checkInvocation (Addresses F2)
test("INVOCATION: checkInvocation supports wildcard and DAG parent actions", () => {
  const wildcardEnv = { act: ["*"], res: "mcp://tools/**" };
  // Should accept any registered verb under wildcard
  assert.ok(checkInvocation(wildcardEnv, { act: "data:read", resource: "mcp://tools/db" }));

  const parentEnv = { act: ["finance:pay"], res: "ap2://rails/**", cap: { max_per_tx: 100, unit: "USD" } };
  // Should accept registered child action finance:pay:escrow
  assert.ok(checkInvocation(parentEnv, { act: "finance:pay:escrow", resource: "ap2://rails/pay", amount: 50, unit: "USD" }));
});

// Test 2: Idempotency Key Caching Prevents Duplicate Execution (Addresses LIP-4 §2)
test("IDEMPOTENCY: makeIdempotencyCache prevents duplicate transaction execution", () => {
  const cache = makeIdempotencyCache();
  const agentDid = "did:key:z6MksMrZDkhaiLzXQo4kRmKLcU8qbVerEv4j1Jqon9CPPHEC";
  const idemKey = "req-uuid-12345";
  const receipt = { status: "paid", receipt_base: "sha256:abc:sha256:def" };

  assert.equal(cache.check(agentDid, idemKey), undefined);
  cache.store(agentDid, idemKey, receipt);
  assert.deepEqual(cache.check(agentDid, idemKey), receipt);
  // Different agent with same key must not collide
  assert.equal(cache.check("did:key:z6MkOtherAgent...", idemKey), undefined);
});

// Test 3: Base58 Decoder Zero-Byte & Empty String Boundary Invariants (Addresses F1)
test("CRYPTO: b58Decode correctly preserves exact byte lengths for leading zeros and empty inputs", () => {
  assert.equal(b58Decode("").length, 0);
  assert.deepEqual(b58Decode("1"), Buffer.from([0x00]));
  assert.deepEqual(b58Decode("11"), Buffer.from([0x00, 0x00]));
  assert.deepEqual(b58Decode("111"), Buffer.from([0x00, 0x00, 0x00]));

  const raw32WithZero = Buffer.concat([Buffer.from([0x00]), Buffer.alloc(31, 0xFF)]);
  const encoded = b58Encode(raw32WithZero);
  assert.deepEqual(b58Decode(encoded), raw32WithZero);
});

// Test 4: Epoch Total Window Attenuation Rules
test("ALGEBRA: epoch_total window allows attenuation only to epoch_total with cap reduction", () => {
  const parent = { max_per_tx: 500, max_cumulative: 5000, unit: "USD", window: "epoch_total" };
  const okChild = { max_per_tx: 100, max_cumulative: 1000, unit: "USD", window: "epoch_total" };
  const badWindowChild = { max_per_tx: 100, max_cumulative: 1000, unit: "USD", window: "utc_day" };
  const badAmountChild = { max_per_tx: 100, max_cumulative: 6000, unit: "USD", window: "epoch_total" };

  assert.equal(capSubsumes(parent, okChild), true);
  assert.equal(capSubsumes(parent, badWindowChild), false);
  assert.equal(capSubsumes(parent, badAmountChild), false);
});

// Test 5: Audience and Malformed DID Rejection
test("CRYPTO: didKeyToRawPublicKey rejects unsupported methods and malformed multicodecs", () => {
  assert.throws(() => didKeyToRawPublicKey("did:web:example.com"), /unsupported DID method/);
  assert.throws(() => didKeyToRawPublicKey("did:key:"), /unsupported DID method/);
  // z6Ls is secp256k1 multicodec (0xe701), not Ed25519 (0xed01)
  assert.throws(() => didKeyToRawPublicKey("did:key:z6Ls..."), /invalid base58 character|not an ed25519-pub/);
});
```

---

## SURVIVORS (3 Things the Code Does Genuinely Well)

1. **Zero-Dependency Architectural Discipline**: Implementing complete Ed25519 JWS verification, RFC 6962 Merkle logging, Base58/JCS encoding, and capability algebra in under 600 lines of clean Node.js built-ins is exceptional engineering.
2. **Deterministic Test-Vector Interoperability**: `vectors.test.js` successfully proves byte-for-byte canonical JCS and SHA-256 reproducibility between Python and JavaScript implementations.
3. **Rigorous Merkle Tree Path Implementation**: The RFC 6962 `#mth` and `#path` recursive tree algorithms in `merkle-log.js` correctly handle odd tree sizes and single-leaf bounds without off-by-one errors.

---

## SCORE
8.5/10 — The reference library is extraordinarily compact, clean, and faithful to the specifications. Fixing the Base58 leading-zero decoder bug and connecting `dagSubsumes` to `checkInvocation` will make this a gold-standard reference implementation.
