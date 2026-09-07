MODEL: Gemini 3.8 Flash (executing with local checkout at commit adf9d6d4124fddf247775441acfc7664e76b65f5, spec v0.4.9)
DIMENSION: Task B — Hostile review of newest material (THREAT-MODEL.md, LIP-3 v0.3, fuzz.test.js)
DATE: 2026-09-08

## TASK CHOSEN AND WHY
Task B: Hostile review of the newest material. The recent addition of THREAT-MODEL.md, LIP-3 v0.3 (closed URI syntax, exact integer bounds), and the property-based fuzzer (`lap-reference/test/fuzz.test.js`) represents the current perimeter of the protocol's formal claims. Attacking this perimeter tests whether the defences cited in the threat matrix actually withstand adversarial evaluation or merely test self-fulfilling tautologies.

---

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: THREAT-MODEL.md §5 Row 9 / `lap-reference/src/microcore.js:88-93` / `lap-python/living_agents/microcore.py:160-165`]
    CLAIM: `IdempotencyCache.claim()` conflates initial reservations with concurrent in-flight requests by returning `null` (Python: `None`) in both cases, allowing concurrent mutating requests to execute duplicates.
    REASONING: The claim helper was introduced to resolve F6 (closing the check-then-store race). However, in both Node (`microcore.js:88-93`) and Python (`microcore.py:160-165`), `claim(agentDid, idempotencyKey)` returns `null`/`None` when reserving a fresh slot AND when checking a slot that is already pending (before `complete()` is called). Any calling server attempting `if (cache.claim(...) === null) { execute(); }` will execute every concurrent request that arrives while the first execution is awaiting completion. The regression test cited in THREAT-MODEL.md Row 9 (`test_audit_round4.py::test_f6_idempotency_claim_atomic` and `round4.test.js:93-96`) passes only because it literally asserts that `claim()` returns `null` for both calls.
    EVIDENCE:
    Node reproduction:
    ```bash
    node -e "import('./lap-reference/src/microcore.js').then(({ makeIdempotencyCache }) => {
      const c = makeIdempotencyCache();
      const r1 = c.claim('did:key:a', 'k1');
      const r2 = c.claim('did:key:a', 'k1');
      console.log('r1:', r1, 'r2:', r2, 'distinguishable:', r1 !== r2);
    })"
    ```
    Output:
    `r1: null r2: null distinguishable: false`

    Python reproduction:
    ```bash
    python -c "from living_agents.microcore import make_idempotency_cache; c = make_idempotency_cache(); print(c.claim('a','k') is c.claim('a','k'))"
    ```
    Output:
    `True` (both return `None`).

    Cited test in `round4.test.js:95-96`:
    `assert.equal(cache.claim("did:key:a", "one"), null); // first claim reserves`
    `assert.equal(cache.claim("did:key:a", "one"), null); // still pending, not re-executable-as-fresh`
    The test asserts `null` on both calls, proving callers cannot distinguish a fresh slot from a pending race.
    PROPOSED FIX:
    `claim()` must return distinct results for the three lifecycle states: fresh reservation, pending in-flight, and completed receipt.
    In `lap-reference/src/microcore.js`:
    ```diff
    --- a/lap-reference/src/microcore.js
    +++ b/lap-reference/src/microcore.js
    @@ -88,4 +88,5 @@ export function makeIdempotencyCache() {
         claim(agentDid, idempotencyKey) {
           const key = k(agentDid, idempotencyKey);
    -      if (seen.has(key)) return seen.get(key); // completed receipt, or null if pending
    -      seen.set(key, null); // reserve atomically (synchronous — no await between has/set)
    -      return null;
    +      if (seen.has(key)) {
    +        const val = seen.get(key);
    +        return val === null ? { status: "pending" } : { status: "completed", receipt: val };
    +      }
    +      seen.set(key, null);
    +      return { status: "claimed" };
         },
    ```
    Apply the identical three-state enum or tuple in `lap-python/living_agents/microcore.py`.

F2. [SEVERITY: FATAL] [TARGET: LIP-3 §2, §5 / `lap-reference/src/algebra.js:52-76` / `lap-python/living_agents/algebra.py:75-105`]
    CLAIM: `parseRes` fails to reject raw backslashes and double-encoded percent sequences, permitting dot-segment path traversal bypasses (e.g. `/safe/..dmin`) under `/**` wildcards.
    REASONING: LIP-3 §5 explicitly requires: "resource: segment-wise subsumption per §2, with dot-segments (./..) and encoded separators (%2f/%5c/%2e) rejected so a /safe/** scope cannot authorize /admin after a proxy resolves the path (F10)".
    However, `parseRes` only checks `/%2f|%5c|%2e/i` for percent-encoded separators and splits path on `/`. It does not reject literal backslash `\` (`0x5c`).
    When presented with `mcp://tools.example.com/safe/..dmin`, `path.split("/")` produces segments `["safe", "..dmin"]`. The check `segments.includes("..")` evaluates to false because `"..dmin"` is treated as a single opaque segment.
    Because the first segment `"safe"` matches parent `["safe"]` under `**`, `pathSubsumes` returns `true`.
    However, standard WHATWG URL parsers (e.g. `new URL()` in browsers/Node.js, as well as Nginx, Cloudflare, and Windows web servers) normalize `\` to `/` and resolve dot-segments, rewriting `/safe/..dmin` to `/admin`. An agent granted `/safe/**` thus successfully authorizes an action routed to `/admin`.
    Similarly, double-encoded dot-segments like `mcp://tools.example.com/safe/%252e%252e/admin` evade `/%2e/i` and return `true`.
    EVIDENCE:
    ```bash
    node -e "import('./lap-reference/src/algebra.js').then(m => {
      console.log('Subsumed:', m.pathSubsumes('mcp://tools.example.com/safe/**', 'mcp://tools.example.com/safe/..\\admin'));
      console.log('URL resolves to:', new URL('https://tools.example.com/safe/..\\admin').pathname);
    })"
    ```
    Output:
    `Subsumed: true`
    `URL resolves to: /admin`

    In Python:
    ```bash
    python -c "from living_agents.algebra import path_subsumes; print(path_subsumes('mcp://tools.example.com/safe/**', 'mcp://tools.example.com/safe/..\\admin'))"
    ```
    Output:
    `True`
    PROPOSED FIX:
    In `parseRes` (both `algebra.js` and `algebra.py`), reject raw backslashes and percent characters in path patterns:
    ```diff
    --- a/lap-reference/src/algebra.js
    +++ b/lap-reference/src/algebra.js
    @@ -64,4 +64,5 @@ function parseRes(res) {
       // AFTER authorization, letting /safe/** authorize /admin. Fail closed.
    -  if (/%2f|%5c|%2e/i.test(path)) throw new Error("LAP_ERR_RES: encoded path separators not allowed");
    +  if (/[\%]/.test(path)) throw new Error("LAP_ERR_RES: raw backslashes and percent-encoding not allowed in resource patterns");
    ```

F3. [SEVERITY: SERIOUS] [TARGET: LIP-3 §2 line 25 vs `lap-reference/src/algebra.js:59-60`]
    CLAIM: `parseRes` rejects valid `did:` and `urn:` resource patterns specified by LIP-3 §2, while accepting arbitrary undeclared schemes such as `file://` and `gopher://`.
    REASONING: LIP-3 §2 line 25 normatively declares: "`res` — URI, scheme from a closed set (`mcp | a2a | ap2 | https | did | urn`), segment-tokenized path pattern".
    In `algebra.js` line 59, the URI regex is `^([a-z0-9+.-]+):\/\/([^/]+)(\/.*)?$`.
    This regex strictly requires `://`. Standard DIDs (`did:key:...`, `did:web:...`) and URNs (`urn:isbn:...`) do not use `://`. Consequently, passing any valid `did:` or `urn:` pattern throws `LAP_ERR_RES: invalid resource URI`.
    Conversely, any arbitrary scheme containing `://` (e.g. `gopher://`, `file://`, `ftp://`) is admitted without being validated against the closed set.
    EVIDENCE:
    ```bash
    node -e "import('./lap-reference/src/algebra.js').then(m => console.log(m.pathSubsumes('did:key:z6MkA/**', 'did:key:z6MkA/service')))"
    ```
    Output:
    `Error: LAP_ERR_RES: invalid resource URI: did:key:z6MkA/**`

    And for arbitrary schemes:
    ```bash
    node -e "import('./lap-reference/src/algebra.js').then(m => console.log(m.pathSubsumes('gopher://evil.com/**', 'gopher://evil.com/x')))"
    ```
    Output:
    `true`
    PROPOSED FIX:
    Validate `scheme` against `const CLOSED_SCHEMES = new Set(["mcp", "a2a", "ap2", "https", "did", "urn"])`. For `did` and `urn`, support standard URI colon-delimited authority/path separation or clarify the exact syntax profile in LIP-3.

F4. [SEVERITY: SERIOUS] [TARGET: LIP-3 §6 normative pseudocode line 67-69]
    CLAIM: LIP-3 §6 normative pseudocode checks raw child cumulative cap rather than the parent-scaled debit against remaining parent budget, which causes remaining budget to become negative when implemented as written.
    REASONING: In `output/lip/LIP-3-scope-algebra-v0-draft.md:66-70`:
    ```
    for c in C (canonical sorted order):
      find first p in P (canonical sorted order) with c ⊑ p (§5) AND,
        if p.cap defined: c.cap.max_cumulative ≤ remaining[p]
      if none: REJECT(c)
      remaining[p] -= debit(p.cap, c.cap)    (when p.cap defined)
    ```
    Line 68 checks `c.cap.max_cumulative <= remaining[p]`.
    Line 70 then debits `debit(p.cap, c.cap)`.
    If parent has `window: utc_day` and `remaining = 100`, and child has `window: utc_hour` and `c.cap.max_cumulative = 100`:
    `c.cap.max_cumulative <= remaining[p]` (100 <= 100) passes.
    Line 70 then debits `100 * 24 = 2400`.
    `remaining[p]` becomes `100 - 2400 = -2300`.
    The reference implementation in `algebra.js:232` diverged from the pseudocode by testing `if (debit > remaining[i]) continue;`, but a clean-room implementer implementing LIP-3 §6 verbatim will construct a flawed verifier.
    EVIDENCE: `output/lip/LIP-3-scope-algebra-v0-draft.md:67-70`.
    PROPOSED FIX:
    In `output/lip/LIP-3-scope-algebra-v0-draft.md`, update line 68 to read:
    `if p.cap defined: debit(p.cap, c.cap) ≤ remaining[p]`

F5. [SEVERITY: MODERATE] [TARGET: `lap-reference/test/fuzz.test.js:279-297` / `lap-python/tests/test_fuzz.py`]
    CLAIM: Fuzz property 6 claims to prove budget conservation against an exact integer oracle, but its generator cannot reach multi-parent envelopes or cross-parent greedy allocation.
    REASONING: Fuzz property 6 is titled `"fuzz 6: budget conservation agrees with an exact-integer oracle (single parent)"`. In line 286, `verifyEnvelopeAttenuation([parent], children)` is passed only a single parent.
    The generator never exercises multi-parent envelopes (`parents.length > 1`).
    While LIP-3 §6 documents that greedy matching across multiple parents is incomplete (conservative), it claims that it is sound. Single-parent fuzzing does not verify soundness when multiple parent scopes share children with competing resource patterns.
    EVIDENCE: `lap-reference/test/fuzz.test.js:285-286`:
    `const parent = g.scope();`
    `for (let k = 0; k < n; k++) children.push(g.attenuate(parent));`
    `got = verifyEnvelopeAttenuation([parent], children).ok;`
    PROPOSED FIX:
    Extend Property 6 with a multi-parent generator that tests overlapping parent scopes against an exact bipartite matching oracle to ensure no multi-parent assignment allows total debit to exceed the sum of parent cumulative budgets.

F6. [SEVERITY: SERIOUS] [TARGET: THREAT-MODEL.md §5 Row 3 / `lap-python/living_agents/mcp_middleware.py:88`]
    CLAIM: FastMCP `@verify_envelope` omits `expected_method` and `expected_target` during request signature verification, enabling cross-endpoint request signature reuse.
    REASONING: THREAT-MODEL.md Row 3 states that captured header pairs cannot be replayed elsewhere because the RFC 9421 signature binds `@method` and `@target-uri`.
    However, `verify_request_signature` in `microcore.py` and `microcore.js` makes `expected_method` and `expected_target` optional.
    In `mcp_middleware.py:88`, the decorator executes:
    `verify_request_signature(passport_jwt, sub, signature_base, signature_b64url, request_body)`
    without passing `expected_target=resource` or `expected_method`.
    Consequently, `verify_request_signature` only checks that *some* `@target-uri:` string exists in the signature base; it never checks that it matches the invoked tool's resource URI. An attacker who intercepts a signature intended for `mcp://tools.example.com/billing/query` can reuse that signature against `mcp://tools.example.com/billing/pay` as long as both match the envelope.
    EVIDENCE: `lap-python/living_agents/mcp_middleware.py:87-89`:
    `verify_request_signature(passport_jwt, sub, signature_base, signature_b64url, request_body)`
    Notice `expected_target` is not supplied.
    PROPOSED FIX:
    In `mcp_middleware.py:88`, pass `expected_target=resource` and `expected_method="POST"` into `verify_request_signature`.

F7. [SEVERITY: MODERATE] [TARGET: `lap-reference/src/microcore.js:16` / `lap-python/living_agents/microcore.py:27`]
    CLAIM: `verifyMicroCorePassport` leaks unhandled language `SyntaxError` exceptions when parsing malformed JWT payloads before signature verification.
    REASONING: To extract `iss` prior to verifying the JWS, `verifyMicroCorePassport` executes:
    `JSON.parse(b64urlDecode(passportJwt.split(".")[1]).toString()).iss`
    If an attacker sends a compact token whose payload segment is valid base64url but invalid JSON, `JSON.parse` throws an unhandled language `SyntaxError` (in Node) or `json.decoder.JSONDecodeError` (in Python).
    This violates the protocol invariant that malformed input produces typed `LAP_ERR_*` errors.
    EVIDENCE:
    ```bash
    node -e "import('./lap-reference/src/microcore.js').then(m => m.verifyMicroCorePassport('eyJhbGciOiJFZERTQTEifQ.bm90X2pzb24.sig', { expectedAud: 'x' }))"
    ```
    Output:
    `SyntaxError: Unexpected token 'o', "not_json" is not valid JSON`
    PROPOSED FIX:
    Wrap the pre-verification payload decoding in a `try...catch` and throw `LAP_ERR_PASSPORT: malformed token payload`.

F8. [SEVERITY: NIT] [TARGET: `lap-reference/src/jws.js:15` / `lap-python/living_agents/jws.py:46`]
    CLAIM: `decodeJws` crashes with unhandled `TypeError` / `AttributeError` on non-string input instead of emitting `LAP_ERR_SIG`.
    REASONING: `decodeJws(token)` directly invokes `token.split(".")` without validating `typeof token === "string"`. If passed `null`, `undefined`, or non-string inputs, it crashes with raw runtime exceptions.
    EVIDENCE:
    `node -e "import('./lap-reference/src/jws.js').then(m => m.decodeJws(null))"` throws `TypeError: Cannot read properties of null (reading 'split')`.
    PROPOSED FIX:
    Add `if (typeof token !== "string") throw new Error("LAP_ERR_SIG: token must be a string");`.

---

## DESIGNS

### Three-State Idempotency Reservation Model (Fix for F1)
Replace the binary `null` return in `IdempotencyCache` with an explicit atomic lifecycle contract:
- `claim(agentDid, idempotencyKey, requestHash)`:
  - If key is unseen: store `{ status: "pending", requestHash, ts: now() }` and return `{ ok: true, state: "reserved" }`.
  - If key is seen and status is `"pending"`: return `{ ok: false, state: "in_flight" }`.
  - If key is seen and status is `"completed"`:
    - If stored `requestHash` != provided `requestHash`: return `{ ok: false, state: "key_reused_different_body" }` (fail closed).
    - Else: return `{ ok: true, state: "cached", receipt: storedReceipt }`.
- Mutating tools only proceed if `claim()` yields `state: "reserved"`. If `state: "in_flight"`, return HTTP 409 Conflict with a `Retry-After` header.

---

## PRIOR ART
- **RFC 3986 §3.3 & WHATWG URL Standard §4.3:** Path segment resolution rules stipulate that backslashes `\` in scheme-relative URLs for special schemes are treated as `/`. Security gateways that evaluate paths without converting or rejecting raw backslashes consistently suffer path-traversal bypasses against reverse proxies.
- **IETF RFC 9421 HTTP Message Signatures §2.1:** Verifiers MUST match signature parameters against transport-observed metadata, not merely inspect the signature base string for presence of component keys.

---

## SURVIVORS
1. **Strict Base64url Canonicalization (`b64urlDecode`):** The enforcement of canonical trailing bits and rejection of leniency/padding (`test/encoding.test.js`) is rock solid. It completely prevents textual signature re-encoding attacks against hash-indexed logs.
2. **Exact-Integer Window Scaling (`BigInt`):** The transition to integer-floor scaling (`scaleFloor`) and the rejection of values above `2^53 - 1` completely eliminated double-precision floating point divergence between JavaScript and Python across the tested 9 quadrillion range.

---

## SCORE
6/10 — The cryptographic foundations (Ed25519, strict base64url, JCS canonicalization) and single-scope algebra are exceptionally clean, but the newest perimeter defences have critical leaks: `IdempotencyCache.claim()` does not prevent concurrent duplicate execution, `parseRes` permits backslash path traversal bypasses, and the FastMCP middleware fails to bind the signature's target URI. Fixing the `IdempotencyCache` state machine and rejecting raw backslashes in `parseRes` will immediately raise this to 9/10.
