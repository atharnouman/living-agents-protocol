MODEL: GPT-5.6 Codex
DIMENSION: 2026-08-30_openai_redteam.md (user-supplied hostile security audit prompt)
DATE: 2026-08-30

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: LIP-4 issuer authorization / Micro-Core passport verification]
    CLAIM: A self-signed `did:key` passport is treated as authorization for the server's resources, with no server-side trust-anchor or principal-to-tenant/account binding.
    REASONING: `verifyMicroCorePassport` obtains `iss` from the untrusted payload and verifies the JWS with that very DID; this proves only that the presenter controls a new key. It never asks whether that principal is an issuer the tool server recognizes, whether it owns the target account, or whether its `proof_class` is acceptable. LIP-4 calls the five steps its whole server-side invariant and deliberately permits `self-asserted` passports, so a server using the advertised Micro-Core as its authorizer accepts an arbitrary newly generated principal, arbitrary envelope, and arbitrary action/resource list addressed to itself. This is an authorization vacuum, not merely an identity-format issue.
    EVIDENCE: `lap-reference/src/microcore.js:8-16` and `lap-python/living_agents/microcore.py:23-45` verify only self-selected `iss`, audience, time, and envelope presence. Neither API accepts an issuer allow-list, trust policy, tenant binding, nor required proof class. `output/lip/LIP-4-micro-core-draft.md:5,11-29,41-49` presents this as a standalone server authorization invariant. A local Node check accepted a freshly generated key as both `iss` and `sub` with `expectedAud` set: `verifyMicroCorePassport(signJws(freshPayload, freshPrivateKey, ...), { expectedAud, now })` returned the payload.
    PROPOSED FIX: Make a server trust-policy input mandatory: map canonical `iss` (and proof class/credential chain) to a locally authenticated tenant/principal and to the concrete account or resource namespace being acted upon. Reject self-asserted passports for money, PII, or any operation not explicitly configured to accept them. State normatively that a valid passport is not by itself authority over a server-owned resource.

F2. [SEVERITY: FATAL] [TARGET: LIP-4 agent-key binding]
    CLAIM: The request signer is never required to equal the passport's authorized agent (`sub`), so possession of a captured passport is sufficient for any unrelated key holder to use it.
    REASONING: Passport verification returns its payload, but request verification accepts a separately supplied `agentDid` and verifies against that key. No JS or Python path compares normalized `payload.sub` with normalized `agentDid`. Thus an attacker who has a valid passport but not the agent key creates a keypair, signs an otherwise acceptable signature base, supplies its DID as `agentDid`, and passes both checks. This defeats the stated non-bearer property of the second header.
    EVIDENCE: `lap-reference/src/microcore.js:8-30`; `lap-python/living_agents/microcore.py:23-74`; and the middleware bridge at `lap-python/living_agents/mcp_middleware.py:63-70`. LIP-4 requires the signature be by the agent `sub` at `output/lip/LIP-4-micro-core-draft.md:31-37,44-45`. Reproduction against the Node reference returned `true` after signing the two accepted digest lines with a newly generated attacker key while reusing the shipped `micro_core.passport_jwt`:

    ```js
    // Deliberately no passport-sub private key is used here.
    const attackerDid = didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(k.publicKey));
    const base = '"content-digest": sha-256=:' + sha256B64url(body) +
      ':\n"lap-passport-hash": sha256:' + sha256Hex(passportJwt);
    const sig = sign(null, Buffer.from(base), k.privateKey).toString('base64url');
    console.log(verifyRequestSignature({ passportJwt, agentDid: attackerDid,
      signatureBase: base, signatureB64url: sig, requestBody: body })); // true
    ```

    PROPOSED FIX: Derive the verification key exclusively from the verified passport payload. Require `sub` to be present, canonicalize it with DID-safe normalization, reject an externally supplied `agentDid` unless it byte-for-byte/canonically equals `sub`, and bind that checked value into the request-signature verification result.

F3. [SEVERITY: SERIOUS] [TARGET: RFC 9421 request-signature verification]
    CLAIM: The implementation verifies an arbitrary signed newline string, not an RFC 9421 signature over the actual HTTP method, target URI, and required covered-component set.
    REASONING: The code only asks whether the signed text contains one exact content-digest line and one exact passport-hash line. It never parses or verifies `@signature-params`, never requires `@method` or `@target-uri`, and receives no trusted transport method/target to compare against. A signer can therefore submit the two-line base shown in F2; the reference accepts it even though it omits every method/target/signature-parameters requirement in LIP-4. This is distinct from the already-triaged request-binding idea: the documented fix exists in prose, but its reference implementation does not enforce it.
    EVIDENCE: `lap-reference/src/microcore.js:21-30` and `lap-python/living_agents/microcore.py:48-74`; the F2 reproduction contains no `@method`, `@target-uri`, or `@signature-params` and returned `true`. The mandatory components are explicit in `output/lip/LIP-4-micro-core-draft.md:31-45`.
    PROPOSED FIX: Accept parsed RFC 9421 `Signature-Input`/`Signature` structured fields, require exactly the minimum component identifiers (including `@method`, `@target-uri`, `content-digest`, `lap-passport-hash`, and `idempotency-key` where required), construct the signature base from server-observed method, canonical target URI, raw body bytes, and headers, then verify it. Reject duplicate components, missing `@signature-params`, and any component list differing from the profile.

F4. [SEVERITY: SERIOUS] [TARGET: audience enforcement]
    CLAIM: Audience binding is fail-open because `expectedAud` is optional; omitting one configuration argument accepts a passport for any audience.
    REASONING: Both implementations only compare `aud` when an optional expected audience was passed. With the default, a non-empty audience such as `https://other.example` succeeds. That reverses LIP-4's MUST that `aud` name this server and makes the previously merged cross-server replay mitigation deployment-optional.
    EVIDENCE: `lap-reference/src/microcore.js:8-13`; `lap-python/living_agents/microcore.py:23-40`; `lap-python/living_agents/mcp_middleware.py:20-28,63-65`. A local Node check generated a passport with `aud: "https://other.example"` and called `verifyMicroCorePassport(token, { now: 1500 })`; it returned that audience. LIP-4 says a different audience MUST be rejected at `output/lip/LIP-4-micro-core-draft.md:25,43-45`.
    PROPOSED FIX: Require a non-empty server identity/expected audience at verifier construction, not per call; canonicalize and compare it unconditionally. Make the unsafe compatibility behavior impossible in the public API (or require an explicit test-only opt-out that cannot be enabled in production).

F5. [SEVERITY: FATAL] [TARGET: Python FastMCP `@verify_envelope` argument/body binding]
    CLAIM: The Python decorator can authorize a signed benign request body while executing different positional arguments, including an amount above the cap.
    REASONING: The decorator accepts `lap_auth["request_body"]` as authoritative; it does not recompute it from the tool invocation. If absent, it serializes only `kwargs`, losing all positional arguments. It also obtains `amount` and `unit` only from `kwargs`. Calling a decorated `pay(invoice, amount, unit)` positionally therefore makes `amount is None`, skips `check_invocation`'s cap branch, and executes the supplied amount. The existing vector's signature over the 4,200-USD body can accompany `pay("INV-1001", 6000, "USD", lap_auth=vector_auth)`; the wrapper checks neither the raw body/arguments equality nor the positional amount.
    EVIDENCE: `lap-python/living_agents/mcp_middleware.py:44-74` (trusted caller body, kwargs-only serialization, kwargs-only amount extraction); `lap-python/living_agents/microcore.py:94-101` (cap skipped when amount is `None`). The equivalent core condition is directly observable in Node: `checkInvocation(envelopeWithMaxPerTx1, { ..., amount: undefined, unit: undefined })` returns `true`. The shipped middleware tests use keyword arguments only at `lap-python/tests/test_middleware.py:52,92-93`, so this path is untested.
    PROPOSED FIX: Bind invocation arguments with `inspect.signature(fn).bind(*args, **kwargs)` and apply defaults before extracting policy fields. Obtain raw request bytes and transport metadata from the trusted MCP/ASGI request context, never from an application-provided `lap_auth` dictionary; verify those bytes before parsing. Refuse a capped tool if its amount/unit cannot be unambiguously extracted from the bound invocation.

F6. [SEVERITY: SERIOUS] [TARGET: idempotency cache atomicity and clustered deployment]
    CLAIM: The provided idempotency helper has a check-then-store race and is intrinsically ineffective across worker processes or Kubernetes replicas.
    REASONING: The helper exposes separate `check` and `store` operations with no atomic claim, pending state, lock, TTL, or shared backing store. Any ordinary mutating handler performs `check`, awaits the side effect, then stores; all simultaneous requests can observe a miss before the first store. The Node event loop does not prevent this because the interleaving occurs at the awaited mutation. Independently, each pod/worker has its own map, so a load balancer can execute the same signed `(sub, Idempotency-Key)` once per replica. This attacks the adequacy of the merged idempotency-key fix, rather than re-submitting the already logged fact that caching is needed.
    EVIDENCE: `lap-reference/src/microcore.js:49-62` and `lap-python/living_agents/microcore.py:104-118`. The following read-only local check printed `1000`, not `1`:

    ```js
    const cache = makeIdempotencyCache(); let executions = 0;
    await Promise.all(Array.from({length: 1000}, async () => {
      if (!cache.check('did:key:a', 'one')) {
        await Promise.resolve();       // stand-in for the mutation
        executions++; cache.store('did:key:a', 'one', 'receipt');
      }
    }));
    console.log(executions); // 1000
    ```

    LIP-4 mandates replay-safe execution at `output/lip/LIP-4-micro-core-draft.md:39,48`, while the helper is memory-local.
    PROPOSED FIX: Specify and supply an atomic durable `claim(sub, key, request_hash)` primitive (for example a database unique constraint/transaction or Redis `SET NX` plus a pending record). Store the request hash and reject same-key/different-body reuse; cache only the completed canonical response/receipt. Use a shared backend, bounded TTL/size, and lease recovery for pending claims; do not present an in-memory Map/dict as a production-ready helper.

F7. [SEVERITY: FATAL] [TARGET: LIP-3 multi-window budget conservation]
    CLAIM: Combining the 2-D proportional-cap rule with raw child-budget subtraction permits a 24-fold daily budget expansion.
    REASONING: Let parent P have `max_cumulative=2400, window=utc_day`. A child with `max_cumulative=100, window=utc_hour` is individually valid because `100 <= floor(2400/24)`. The envelope verifier subtracts only 100 from P's remaining daily total for each child. It therefore accepts 24 distinct hourly child scopes (remaining becomes zero), yet each of the 24 scopes may spend 100 in each of 24 hours: `24 children × 24 hours × 100 = 57,600/day`, versus P's 2,400/day. Different resource paths make the grants independently usable. This is not the previous "five full siblings" issue; it is a dimensional-unit error in the purported fix.
    EVIDENCE: `lap-reference/src/algebra.js:91-113,127-149`; `lap-python/living_agents/algebra.py:125-155,214-241`; and the normative pseudocode in `output/lip/LIP-3-scope-algebra-v0-draft.md:41-67`. This reference reproduction returned `{"ok":true}`:

    ```js
    const P = [S('mcp://t/pay/**', {max_per_tx:100, max_cumulative:2400,
      unit:'USD', window:'utc_day'}, 2)];
    const C = Array.from({length:24}, (_, i) =>
      S('mcp://t/pay/' + i, {max_per_tx:100, max_cumulative:100,
        unit:'USD', window:'utc_hour'}, 1));
    console.log(verifyEnvelopeAttenuation(P, C)); // { ok: true }
    ```

    PROPOSED FIX: Perform allocation accounting in a common parent-window unit. For a timed child, debit `child.max_cumulative × parent_duration / child_duration` (with integer-safe rounding and aligned-bucket semantics) from its parent allocation, or prohibit mixed-window sibling allocations until a formally verified flow model exists. Static checks do not replace the spend authorizer; that authorizer must also enforce an atomic per-parent bucket ledger.

F8. [SEVERITY: SERIOUS] [TARGET: LIP-3 schema validation and numeric domain]
    CLAIM: No implementation validates cap values before arithmetic, allowing negative "credit" scopes to manufacture remaining budget and creating unsafe JS/Python numeric divergence.
    REASONING: The LIP says to validate schema before computing conservation, but neither port checks that caps are finite non-negative integers, that `max_per_tx`/`max_cumulative` have sane relationships, or that values are within a common exact numeric range. A negative child budget is accepted by the `<=` tests and then subtracted from remaining, increasing it. With parent 100/day, child A -100/day, and children B/C 100/day, canonical resource order A/B/C makes the reference accept B+C (200 positive allocation) from a 100 parent. JavaScript additionally uses IEEE-754 Number without `Number.isSafeInteger`, whereas Python uses unbounded `int`, so signed JSON above 2^53 cannot have a cross-port security meaning.
    EVIDENCE: missing validation at `lap-reference/src/algebra.js:91-113,129-143` and `lap-python/living_agents/algebra.py:125-155,219-235`; `output/lip/LIP-3-scope-algebra-v0-draft.md:57` nevertheless requires `validate schema`. A local Node reproduction with paths `a`, `b`, and `c`, caps `-100`, `100`, and `100`, and a 100 parent returned `{"ok":true}`. No JSON Schema is shipped alongside the LIP or invoked by either reference checker.
    PROPOSED FIX: Define a mandatory wire schema and validate before normalization/sorting: unit grammar, allowed windows, `0 <= max_per_tx <= max_cumulative`, bounded depth/decay, and exact integer representation. Either cap all numeric minor-unit values at `Number.MAX_SAFE_INTEGER` or use canonical decimal strings/BigInt in both ports. Reject unknown fields/types rather than relying on JS coercion or Python exceptions.

F9. [SEVERITY: SERIOUS] [TARGET: exported `scopeSubsumes` predicate]
    CLAIM: The function documented and named as the full LIP-3 subset predicate omits caps entirely and returns true for a child whose cap is hundreds of times broader.
    REASONING: LIP-3 §5 says caps are one of the conjuncts of `c ⊑ p`, but both `scopeSubsumes` implementations check action, resource, counterparty, depth, and decay only. `verifyEnvelopeAttenuation` happens to add a separate cap check, but the publicly exported predicate is unsafe for any direct caller, exactly the natural API a policy engine will use. This is an API/spec divergence, not an incompleteness trade-off in matching order.
    EVIDENCE: `lap-reference/src/algebra.js:115-124` and `lap-python/living_agents/algebra.py:191-211`, compared with `output/lip/LIP-3-scope-algebra-v0-draft.md:47-50`. The Node reference printed `true` for `scopeSubsumes(parent cap=1 tx, child cap=999 tx)` with every other field strictly attenuated.
    PROPOSED FIX: Make `scopeSubsumes` call `capSubsumes(parent.cap, child.cap)` itself and test it directly. Have envelope verification call only this total predicate plus allocation accounting, so a future caller cannot accidentally omit a security conjunct.

F10. [SEVERITY: SERIOUS] [TARGET: URI/resource canonicalization]
    CLAIM: Resource authorization compares an unnormalized path grammar while real HTTP URI processing removes dot segments, enabling a scope for `/safe/**` to authorize `/admin`.
    REASONING: `normalizeUri` lowercases scheme/authority but leaves path semantics untouched; `parseRes` treats `..` and percent-encoded dot segments as ordinary segments. A resource `https://api.example/safe/../admin/delete` is therefore judged inside `https://api.example/safe/**`, while standard URI resolution yields `/admin/delete`. A proxy, URL library, gateway, or backend router can normalize it after LAP has authorized it. This attacks the adequacy of the merged NFC/URI-normalization fix: the code implements only case folding, not RFC 3986 path normalization or a single canonical routing representation.
    EVIDENCE: `lap-reference/src/crypto-util.js:106-114`, `lap-reference/src/algebra.js:36-66`; Python parity at `lap-python/living_agents/crypto_util.py:141-151` and `lap-python/living_agents/algebra.py:70-122`. Local result: `pathSubsumes('https://api.example/safe/**', 'https://api.example/safe/../admin/delete')` returned `true`, while `new URL(theChild).pathname` returned `/admin/delete`. LIP-3 requires URI normalization at `output/lip/LIP-3-scope-algebra-v0-draft.md:25,31`.
    PROPOSED FIX: Define one strict URI parser shared with routing. Reject userinfo, fragments, ambiguous authorities, raw `%2f`/`%5c`, dot segments, and noncanonical percent encodings in scopes and requests, or normalize both with RFC 3986 remove-dot-segments plus a scheme-specific canonicalizer before signing, matching, and dispatch. Compare the same canonical target the transport will execute.

F11. [SEVERITY: FATAL] [TARGET: LAP-7 identity/vitality and MEET single-writer assumption]
    CLAIM: LAP equates a copyable key/passport with one living agent, so normal snapshot, restore, autoscaling, or active-active deployment can create indistinguishable concurrent clones that fork MEET state, receipts, and commitments.
    REASONING: A Kubernetes deployment or restored snapshot can run two copies with the same DID key, passport, memory, and resumption material. Both see the same accepted turn `n`, then each signs a different valid turn `n+1` using the same `prev_turn_hash`; each can also emit valid pulses. Lock-step sequencing and replay caches only work if there is a single globally linearizable state store, which the protocol neither requires nor identifies. The founding document simultaneously lists Kubernetes and snapshot/migration/key custody as L1 mechanisms, says a pulse proves continuity of key custody, binds session resumption to the passport rather than process, and asserts that migration never multiplies one identity. Those statements are false for ordinary copyable cloud credentials. Detection after fork is not prevention when a payment, disclosure, or fair-exchange reveal has already happened.
    EVIDENCE: `output/LAP-founding-document.md:87-110,354-358`; `output/lip/LIP-2-meet-draft.md:12,15,37,41-43`. The specification supplies per-session replay caches but no identity-wide single-writer lease, fencing token, quorum log, or required linearizable store.
    PROPOSED FIX: Decide explicitly whether a LAP identity is a singleton execution or a logical fleet. For singleton semantics, require a durable identity-instance lease with monotonically increasing fencing epoch; every PULSE, MEET transition, receipt, reservation, and externally visible action must carry the epoch and be rejected if stale. The lease authority must be linearizable and key custody must prevent stale replicas from signing (or counterparties must verify a quorum/lease proof). For fleet semantics, replace the “one being” claim with a replicated-state-machine profile and define deterministic conflict handling, accounting, and attestation for replicas.

F12. [SEVERITY: MODERATE] [TARGET: `did:key` / Base58 parsing availability]
    CLAIM: The Base58 key parser has no input-length bound and performs expensive growing-BigInt work before rejecting an invalid key length, enabling inexpensive CPU exhaustion without any regex backtracking.
    REASONING: Both decoders multiply an ever-growing integer for every supplied Base58 character, then only after decoding check the 32-byte Ed25519 key length. `iss` is read from an untrusted JWT payload before passport verification, and `agentDid` is an untrusted request field, so this happens before authentication. This is not a catastrophic-backtracking regex finding—the reviewed regexes are anchored and linear—but it is an algorithmic parsing DoS. On the reviewed Node 20.17 runtime, `didKeyToRawPublicKey('did:key:z' + 'z'.repeat(100000))` took about 1.7 seconds before rejection; a modest concurrent request set is enough to starve a tool server.
    EVIDENCE: `lap-reference/src/crypto-util.js:39-66` and `lap-python/living_agents/crypto_util.py:62-100`; reachability from `lap-reference/src/microcore.js:8-9,21-23` and `lap-python/living_agents/microcore.py:29-33,55-58`.
    PROPOSED FIX: Enforce tight HTTP header/token limits before decoding; for `did:key` Ed25519, reject a textual multibase payload outside a small fixed bound before Base58 conversion, then require exactly the expected multicodec and raw-key lengths. Apply the same bounded parsing to JWS segments and signature bases, with per-source request/concurrency limits.

## DESIGNS

1. **Micro-Core binding object.** Give the verifier a trusted transport object `{method, canonical_target_uri, raw_body_bytes, idempotency_key, server_id}` and return a verified object `{issuer, subject, tenant, envelope, request_hash}`. The verifier, not the caller, constructs RFC 9421's base and enforces `subject == signing_key_did`; policy maps `issuer/tenant` to resource authority. This removes the current five independently caller-supplied strings.

2. **Dimensionally sound cap allocation.** Represent every timed child allocation in the parent's bucket units before deducting it: `debit_p(c) = c.max_cumulative * duration(p.window) / duration(c.window)`. Reject nonintegral conversions or use a conservative ceiling. Store allocations as durable parent-bucket reservations, not as a static list alone; only the authorizer may debit actual spends.

3. **Identity Instance Lease (IIL).** Create `{agent_did, epoch, holder_attestation, expires_at, prev_epoch_hash}` in a linearizable service. A signing/KMS policy signs operational messages only for the current epoch. Every receiver retains the highest epoch per DID and rejects lower epochs; equal-epoch conflicting state transitions are quarantine evidence. This is the minimum additional primitive needed for the protocol's “one agent across migration” claim to survive Kubernetes and regional failover.

## PRIOR ART

- **RFC 9421, HTTP Message Signatures:** parse `Signature-Input` structured fields and build the signature base from observed message components; a signed ad-hoc string is not an implementation of the profile.
- **RFC 3986, URI Generic Syntax:** apply a defined normalization/routing profile, especially dot-segment and percent-encoding handling, before making authorization decisions.
- **Kubernetes Lease API / fencing-token pattern:** leader election alone is insufficient; consumers and signing systems must reject stale lease epochs to prevent split brain.

## SURVIVORS

- Terminal-only `*`/`**` handling and the rejection of non-terminal wildcards are materially safer than ordinary prefix matching—provided URI canonicalization is completed before that matcher runs.
- The direct parent/child timed-cap predicate correctly rejects a bare `tx` child under a timed parent and uses integer-floor scaling; the fatal defect is the subsequent cross-scope aggregation unit.
- The decision to keep signature-base bytes strict rather than trim/CRLF-normalize remains correct. The missing enforcement is component parsing and transport binding, not line-ending tolerance.

## SCORE

2/10 — the repository has several thoughtful first-order fixes, but the reference implementation still fails the core claims that a passport identifies an authorized signer, a request is bound to its transport, and a daily budget is conserved. The Kubernetes/snapshot clone problem also means the protocol's central “one living identity” property is currently a policy assertion, not an enforceable distributed-systems invariant.
