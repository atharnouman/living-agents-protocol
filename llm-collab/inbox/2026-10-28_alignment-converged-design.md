# Converged design after two independent reviews (2026-10-28): the idempotency claim under authority replacement and key reuse

Inputs: `2026-10-28_alignment-review-brief.md`, `2026-10-28_alignment-review-fable.md`, `2026-10-28_alignment-review-sonnet.md`. Every code and spec citation used below was re-checked in the repository on 2026-10-28. Status: DRAFT until the owner decides the one open fork (D1) and gives the go.

## Where the two reviews agree (adopted)

1. Recognition of an existing claim moves to right after the passport and call-signature checks (with the key's coverage checked there too), before action, resource and cap. In flight → `LAP_ERR_REPLAY`; indeterminate → `LAP_ERR_REPLAY` naming reconciliation. A cap, action or resource refusal on a retry then means "no execution recorded under this key".
2. Request identity = the signed `@method`, `@target-uri` and server-recomputed `content-digest` lines (never the passport hash, never the key), stored at reservation, compared before the state is read; a reused key with a different identity is refused in every state, and the stored identity is never echoed.
3. Claim scope = (tenant, sub, key), tenant = the server's F1 mapping of the normalised `iss`, default the normalised `iss` itself. Never the passport hash, envelope or `aud`. A different tenant with the same agent key and key is a separate operation. (Both reviewers reproduced the current cross-principal replay.)
4. `claim()` stays the single atomic gate; recognition is a non-reserving `lookup`; a refused request creates nothing (extension §4.1 "no claim consumed on failure"); the reservation also records the executing passport hash and time.
5. A replay returns the stored result and the same receipt, plus an unsigned `replayed: true` in the result `_meta`, outside the receipt object.
6. The extension draft §7 eviction sentence ("entries older than the longest passport lifetime can be evicted: a replay after that fails on exp") is wrong today and becomes a double-execution rule under recognition-first; replaced by a published retention window independent of passport lifetime.
7. The legacy `check`/`store` cache API is retired or made scope- and identity-aware; `examples/audit-record-contract/lap_chain.py:74` and the recovery tests follow; existing tests that compare `claim()` dicts exactly get added fields only.
8. "Both ports" is an overclaim: Node has the cache and building blocks, no composed middleware. 0.4.14 gives Node the cache change, a `checkInvocation` magnitude option and shared scenario vectors (`test-vectors/microcore-replay-vectors.json`, unanchored like the cap vectors); conformance check 5 in the extension draft is split (replay before the cap under a replaced passport; refusal of a reused key with a different request; isolation across tenants).
9. Reply wording: "reference", not "both ports"; "from 0.4.14", since the 10-26 comment's "a retry with the same key gets the stored result back" was false under a replaced envelope; "consistent with" the 3394 comment, not "implements"; no exactly-once, no durability beyond the in-process cache.

## Found by the reviews beyond the brief (all re-checked; all go into 0.4.14 or the v0.4 text)

- A tool exception leaves the claim in flight forever (`mcp_middleware.py:162` has no handler): it must mark the claim indeterminate and re-raise.
- Two executions with identical request and response bytes under distinct keys yield byte-identical receipts (Ed25519 is deterministic; the receipt base is `req_hash:resp_hash`, `microcore.py:261-264`), so §5.6's "a client that receives a receipt it already holds knows the retry did not execute again" is unsound; soften it, and list "bind the operation key into the receipt" as an open question (a receipt-base change needs a new identifier under §6).
- One cache shared by several tools replays `pay`'s result to `refund` for the same key; fixed by the request identity (2) and a tutorial note.
- LIP-4 §2 step 6 gives HTTP 401/403 for everything; add 422 (key reuse), 409 (in flight), 400 (missing key) in line with draft-ietf-httpapi-idempotency-key-header-08.

## The one fork, for the owner (D1)

- **A (Fable):** a completed claim is replayed under any valid passport for the same tenant and agent. The envelope bounds effects; a replay has none; the result is evidence of an effect that happened under authority valid at the time; withholding it defeats the recovery path and leaves the log one-sided.
- **B with the magnitude exempt (Sonnet):** replayed only if the presented passport still covers the stored request's action, resource and unit; `max_per_tx` is not compared (a replay spends nothing). Otherwise `LAP_ERR_REPLAY_WITHHELD`: "executed earlier; result withheld under the current authority": no execution, no new entry, the receipt retained server-side. The literal reading of the 3394 comment ("preserve recognition ... while independently checking current permission to return its result") and of the thread's "historical execution evidence, not continuing authorization to disclose".
- King Yew's own case (a limit cut) replays under both. They differ only when the action, resource or unit was removed.
- **Session's recommendation: B with the magnitude exempt.** It fails closed on disclosure under a narrowed authority, still never double-executes and never opens a new entry, matches the venue's stated principle word for word, and costs one typed refusal. The principal who narrowed the authority can reissue to release the receipt.

## The second, smaller fork (D2): new codes versus the identifier rule

`LAP_ERR_KEY_REUSE` (and, under B, `LAP_ERR_REPLAY_WITHHELD`) ask the client to do something different from `LAP_ERR_REPLAY` (keep the key, retry later) and `LAP_ERR_IDEMPOTENCY` (add a key), so a reason string under an existing code (Fable) would make clients parse prose. Extension §6 says a change to the error contract needs a new identifier; v0.3 changed the `LAP_ERR_REPLAY` row's meaning under the same identifier. **Recommendation:** add the codes and amend §6 so that a new refusal code is a compatible addition (every `LAP_ERR_*` is a refusal with the tool not executed; a client MUST treat an unknown code as a refusal it does not retry on its own).

## Scope of 0.4.14 once D1 and D2 are decided

Python: `IdempotencyCache` (scope, identity, `lookup`, five outcomes, passport hash and time at reservation), `verify_envelope` (reorder; key coverage before lookup; `tenant_of` hook; exception → indeterminate; `replayed` marker; magnitude-exempt replay check under B), `mcp_extension.py` pass-through. Node: cache mirror, `checkInvocation` option. Tests in both ports for: retry after a cut (replay), retry after the action was removed (B: withheld / A: replay), key reuse with a different request in all three states, cross-tenant isolation, cross-tool reuse, tool exception → indeterminate, receipt verifies under the new passport. Specs: LIP-4 §2 (new step, HTTP codes, hardening rule "recognition is independent of authority", retention), extension v0.4 (§4.1, §4.3, §5.6, §6, §7, §8, §9 open question, §10). Then the reply to Sankalp and King Yew, two-model reviewed, before the FSIG call of 2026-10-29 16:00 UTC if the go comes in time.
