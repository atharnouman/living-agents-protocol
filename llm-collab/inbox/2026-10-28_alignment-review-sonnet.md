# Review 2 of 2: fresh Sonnet 5.5 agent, read-only, on the brief `2026-10-28_alignment-review-brief.md` (received 2026-10-28)

Verbatim hand-back. Model output, treated as a reviewer's opinion; the owner decides. The reviewer built a scratchpad prototype (repository untouched) and reports 160 Python tests passing on it after three call-site edits, plus 26 of its own scenarios; those runs are its statement, not checked here.

---

**Verdicts**
- **P1: change.** Recognising before the act/res/cap checks is right for in-flight and indeterminate claims (REPLAY, not CAP). For `completed`, "whatever the current envelope says" is Option A and wrong: return the stored result only if the presented passport still grants this act, res and unit, skipping only `amount <= max_per_tx`; else a new typed refusal, never re-execution. Unsafe without P2.
- **P2: agree, with changes.** Identity = signed `@method` + `@target-uri` + server-recomputed content digest (not passport hash, `created` or key), stored at reservation as components (reconciliation needs the digest to mint a receipt), refused in every state, new `LAP_ERR_KEY_REUSE`.
- **P3: change.** Scope is (tenant, sub, key). "Never a fresh entry" is false after `release()` or eviction, and extension draft :329 lets entries be evicted after the longest passport lifetime, defeating the goal: a reissued passport passes `exp` (arjun2075, 2026-10-12: approval and recognition lifetimes are separate).

**Rule set (mutating tools)**
- R1 Order: passport, call signature, key present and covered, RECOGNISE, act/res, cap, CLAIM, execute, receipt, complete.
- R2 Scope (tenant, sub, key); tenant = F1 mapping of normalised `iss`. Default `iss` isolates but a signer change without a mapping starts a new entry; a one-tenant default keeps `(sub,key)` and leaves isolation to F1 configuration. Never passport, envelope or `aud`.
- R3 RECOGNISE is a non-reserving `lookup`: key_reuse gives KEY_REUSE; in_flight gives REPLAY; indeterminate gives REPLAY naming reconciliation; completed goes to R4; absent continues.
- R4 Completed: return stored result and receipt iff the passport verifies now and act, res, unit, cap schema and amount binding pass; magnitude is exempt (a replay spends nothing). Else `LAP_ERR_REPLAY_WITHHELD` ("executed earlier; result withheld"): no execution, no new entry, receipt retained.
- R5 `claim()` stays the only atomic gate and handles all five outcomes; it stores request components, tenant and executing passport hash. A refused request creates nothing.
- R6 Replay returns the stored bytes, SHOULD add an unsigned `replayed: true`, and appends its own log line.
- R7 Retention is published, independent of passport lifetime.
- R8 A tool exception marks the claim indeterminate (`mcp_middleware.py:162` leaves it in flight forever; reproduced).

**1. Option.** B with the cap magnitude exempt (R3/R4). Reject A: any valid passport for that `sub` becomes a read key, and F5/F8 are skipped (an uncapped tool under a capped passport is refused fresh, `microcore.py:162`, but would replay; ran). Reject C: after a cut the client reads "not executed" and may split the payment (reproduced: `LAP_ERR_CAP`, claim still present). If you treat the cap as a disclosure tier, take full B: one flag. Upstream separates recognition from disclosure: ryjen, 2026-10-11 ("historical execution evidence, not continuing authorization to disclose"); arjun2075's reply (quote verified by API). Audit: the receipt hashes request and response only (`microcore.py:261-264`), so the claim must keep the executing passport hash and each replay appends its own line (`audit_record.py:59-61,319-322` has `replay`, `idempotency_key`, `authority_hash`).

**2. Identity.** Another tenant is a separate operation in a separate namespace: no collision, no existence oracle. Today the reverse (ran): a second issuer with the same agent key, key and args gets the first tenant's receipt and its own payment silently does not run; with other args it still gets the first result. F1 holds: scope is identity, disclosure needs authority.

**3. Key reuse.** A new code: REPLAY (keep the key) and IDEMPOTENCY (add a key) prompt opposite client actions. Refuse in all states, since identity is recorded at reservation; never echo it; the leak is confined to (tenant, sub). IETF -08 (fetch summary): reuse MUST NOT, 422 SHOULD, in flight 409, missing 400; Sankalp's rule is identical. LIP-4 :49 gives 401/403 for everything; add 422/409/400.

**4. Ordering.** Recognise after the signature (earlier, a passport thief probes states) and after passport checks (expired gets `LAP_ERR_EXPIRED`; issuer policy applies; ran). Never reserve-then-release on refusal: extension :224 says no claim is consumed, and a crash would leave a false indeterminate claim. API (Python; Node camelCase): `lookup(scope,key,request_id)`; `claim(scope,key,request_id,meta)` gains `key_reuse`; `check_invocation(..., enforce_magnitude=True)`; `request_identity(...)`; public `claim_scope(payload,tenant_of)`. Scratchpad prototype (repo untouched): +90/-32 library lines; 160 tests pass after three call-site edits; 26 scenarios pass.

**5. Misses.**
- Tenant scope breaks `cache.check(sub,key)` callers (`lap_chain.py:74`, `test_idempotency_recovery.py:75-81`); tests compare `claim()` dicts exactly (`test_audit_round4.py:112-120`, `round4.test.js:93-101`), so add fields only; `lap_chain.py:27` needs the new codes.
- Durable store: unique (scope,key), immutable identity, fencing token on `complete()` (`microcore.py:220` has none), linearizable lookup, legacy rows compare as unknown.
- Indeterminate: recognising first is right (REPLAY, not CAP). The receipt verifies under a new passport (ran); it binds none.
- Extension :310 (a receipt already held shows the retry did not execute again) is unsound: distinct keys with equal content give byte-identical receipts (ran).
- Check 5 (:342) needs "under a passport that still permits the action". A `replayed` member inside the receipt object breaks `client.py:117`.

**6. To Sankalp and King Yew.** At the tool server, a held payment that never executed leaves no record, so its retry is a first execution under the limit in force: a raise lets it through, a cut refuses it and consumes nothing. For one that executed, the duplicate record is keyed by tenant, agent key and the agent's signed operation key, never the limit document, so replacing the limit creates no new entry. The 0.4.13 reference gets one case wrong: it checks the new limit first, so a retry of an executed payment gets a cap error that hides the earlier execution; the fix under review recognises the key first, never re-executes, and returns the stored result only while the presented authority still covers the action and resource, else says it executed earlier and withholds it. A reused key with a different request will be refused, as Sankalp's rule has it. Not claimed: exactly-once. Micro-Core enforces only a per-transaction cap (cumulative limits and pre-submission held entries belong to the spend authorizer and the audit record's own key rule), the shipped cache is single-process, records expire after a published window, and a receipt alone does not prove one execution.

**7. Placement.** Library 0.4.14: `microcore.py`, `mcp_middleware.py`, `mcp_extension.py:230` (`tenant_of` pass-through), Node `microcore.js`. New unanchored `test-vectors/microcore-replay-vectors.json`, like the cap vectors (`vectors.json` is anchored). LIP-4 §2: renumber steps, add a hardening rule "recognition is independent of authority", codes at :49. Extension v0.4: §4.1, §4.3 (two rows), §5.6, §7 (replace :329), §8 (split check 5), changelog; :319 demands a new identifier for error-contract changes (precedent: v0.2, v0.3). List the vectors as an extra set, not CONFORMANCE check 11 (it would unconvert implementers).

**Overclaims or errors in the proposal**
- P1's "whatever the current envelope says" contradicts the principle it cites and breaks F5/F8 on replay.
- P3's "a retry is never a fresh entry": false after release or eviction; :329 contradicts it.
- "Keyed by (sub, key), independent of the passport": survives replacement by any signer, including another tenant's, which collides (ran); reproduction 2 then returns that tenant's result.
- "Both ports": Node has no composed middleware; it needs the cache, a `checkInvocation` option and vectors, and the spec order carries the rest.
- The receipt-equality claim (:310).
- The 3394 principle is a proposed vector, not an MCP requirement; say "consistent with", not "implements".

Scratch probes and prototype: C:\Users\DELL\AppData\Local\Temp\claude\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\scratchpad\scripts and \proto.
