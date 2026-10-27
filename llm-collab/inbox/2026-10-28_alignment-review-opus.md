# Review 3: fresh Opus 5.5 agent, read-only, on the decided design and the 0.4.14 code (received 2026-10-28, after the owner asked whether Opus was aligned too)

Verbatim hand-back. Model output, treated as a reviewer's opinion; the owner decides. Its three blocking items and most non-blocking ones were fixed the same day (second pass of 0.4.14; see the improvements log).

---

**Verdict: not aligned.** I agree with the decided design (D1 and D2), but three defects in the implementation should block publishing 0.4.14.

Checked 2026-10-28 on commit 7f116fc: Python 186 pass; Node 85 pass, 1 skipped. Probes, with the repository untouched: `C:\Users\DELL\AppData\Local\Temp\claude\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\scratchpad\opus_probe_0414.py` (P1–P9) and `C:\Users\DELL\AppData\Local\Temp\claude\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\scratchpad\opus_probe_race.py`. Python files are in `E:\LivingAIAgents\lap-python\living_agents\`. "LIP-4" is `E:\LivingAIAgents\output\lip\LIP-4-micro-core-draft.md`; "ext" is `E:\LivingAIAgents\output\lip\LIP-4-mcp-extension-draft.md`.

**1. D1: I agree with B (cap magnitude exempt).** Neither option re-executes, and both tell the client the key executed. They differ only when the first response was lost and the authority was narrowed in between. Then A shows the result to an agent the principal deliberately narrowed. B waits for a reissue, which that same principal can grant. Withholding is worth that wait; Fable's "defeats recovery" overstates it.

The check (`mcp_middleware.py:168-177`) gives the same answer a fresh call would (P8):
- **Withheld:** when the passport has a cap but the tool has no amount (inner `LAP_ERR_CAP`, per F5), when the unit changed (inner CAP), and when the action was removed (inner ACT).
- **Replayed:** when there is no cap, or the cap is 0. So only removing the action stops disclosure.

The refusal reveals one bit (the key executed) plus an inner code the client can work out from its own passport. Withholding the receipt too is right: the hash of a `{"status":"declined"}` result reveals the outcome. The client can tell "executed, withheld" (`REPLAY_WITHHELD`) from "not executed" (ACT/RES/CAP), except in P1, P9 and P4 below.

**2. D2: I agree** with the new codes and the amended §6. The new codes ask the client for different actions, and older clients are no worse off. Two corrections:
- Ext §6 L325 says every code means the tool did not execute; it should say "for this request".
- `lap_tool` also passes a tool's own `ValueError` through as a refusal (`mcp_extension.py:255-256`). A tool that raises `ValueError("LAP_ERR_CAP: …")` reads as refused, yet it ran and its claim is indeterminate (P5).

**3. Identity rule.**
- **Signer change: I disagree with the default.** The tenant defaults to the normalised `iss` (`microcore.py:227`).
  - A raised limit signed by a second key of the same principal ran the payment again (P1: two executions).
  - A cut signed by that second key returned `LAP_ERR_CAP` for a key that had executed.
  - That is King Yew's case whenever the new limit has a different signer, and it contradicts LIP-4 L62. Sonnet flagged it; the converged design left it open.
  - Fix: fail closed by default. Look claims up by `(sub, key)` and refuse when the stored tenant differs. Keep separate per-tenant claims only when the server supplies `tenant_of`. With one key per intended execution (ext §3.2), that refusal fires only on a signer change.
- **Shared audience.** Fable raised this and the converged design dropped it. One cache serving two audiences replayed A's result to B's request, and B's payment never ran (P7). Scope claims by the server's configured audience, or require one store per server identity (F6).
- **Digest parsing.** The identity takes the *first* signed `content-digest` line (`microcore.py:201-209`; `E:\LivingAIAgents\lap-reference\src\microcore.js:104-112`). Verification accepts the server-recomputed line anywhere (`microcore.py:100-102`; `microcore.js:51-52`).
  - An agent executed request Y while the claim recorded X's digest. An honest X sent under the same key then got Y's result instead of `LAP_ERR_KEY_REUSE` (P2).
  - Fix: use the server-recomputed digest, as the converged design said, and refuse duplicate lines.
- **mcp 2.x vs 1.x.** Hashing the raw arguments (2.x) rather than the bound ones (1.x) can only cause an over-cautious `KEY_REUSE`.
- **Tenant mapping.** `tenant_of` must stay stable for the whole retention window. Its `LAP_ERR_ISSUER` at step 4 (`microcore.py:228-229`) is missing from ext §4.3 L251.

**4. Implementation.**
- **Claim stuck after the payment.** The `try` covers only `fn()` (`mcp_middleware.py:219-228`). Receipt minting and `complete()` (L231-239) sit outside it, and `jcs` raises on non-integer floats and non-JSON types (`crypto_util.py:183-184,194`). A tool returning `{"fee": 1.25}` paid, then the client got an error. The claim stayed in flight forever: every retry got `LAP_ERR_REPLAY`, and `release()` refused (P3).
- **Lookup-to-claim window.** A twin completed after this request's lookup, and the request still got `LAP_ERR_CAP` (P9). Look the key up again after a refusal on the fresh path.
- **A missing identity matches anything.** `complete()` on a never-claimed key stores no identity, and `_status` then matches any request (`microcore.py:270-272,306`; `microcore.js:153,184`). An unrelated request got the stored result (P6), and `test_idempotency_recovery.py:78` claims without an identity. Fix: require an existing claim, treat a missing identity as a mismatch, and deprecate the identity-blind legacy `check`/`store` (L344-354). The middleware never calls them, so `verify_envelope` has no bypass.
- **Non-dict results** get no replay marker and no receipt (`mcp_middleware.py:175-176,234-235`; `mcp_extension.py:257-258`). Their replays look like first executions (P4), so they fail ext §8 check (5).
- **Threads.** Python `claim()` checks and then writes (L294-299). In 719 of 3,000 eight-thread trials, two threads reserved the same key. This predates 0.4.14. `lap_tool` on mcp 1.29 cannot hit it, because sync tools run on the event loop (`fastmcp/utilities/func_metadata.py:114-115`), but threaded hosts can. Fix: add a lock.
- **Correct as built:**
  - the exception path: `NoEffect` frees the key, any other exception leaves the claim indeterminate;
  - the twin case: `settle` after `claim()` only replays or refuses;
  - no refusal reserves a claim;
  - the Node cache behaves the same as the Python one.
- **Vectors.** They test the cache and the envelope check separately, never their order. Add signed vectors that run the whole sequence.

**5. Spec text.**
- LIP-4 L62 and ext §5.6 L316 promise "never a fresh entry" and "ACT/RES/CAP on a retry means no execution is recorded". P1 and P9 break both; qualify them.
- L316 also says a client must not read those refusals as "not executed". Keep that MUST and make the "no execution recorded" clause informative.
- Ext §4.1 L224 ("no claim consumed" on any failure) contradicts step 7 (L232).
- LIP-4 step 5 L48 applies the cap only when the operation "carries an amount", which contradicts F5 and the code. That step now also governs disclosure.
- F6 L61 should require fencing on `complete()`, which does no state check (L302-307), so a slow executor cannot overwrite a newer claim.

**6. Changes required before publishing 0.4.14.**
1. **Blocking:** once `fn` returns, any later failure must either complete the claim (without a receipt if minting fails) or mark it indeterminate (P3).
2. **Blocking:** take the identity from the recomputed digest and refuse duplicate component lines (P2). Only the agent's own claims are affected, but it breaks the "refused in every state" rule that §5.6 relies on.
3. **Blocking:** the default must not execute twice on a signer change (P1). At minimum, qualify LIP-4 L62, ext §5.6 and §7, and the FSIG reply ("the same principal key, or keys the tenant mapping joins"), and add a vector.
4. **Non-blocking:**
   - P4: replay marker and receipt for non-dict results;
   - P5: keep tool exceptions apart from refusals;
   - P6: make a missing identity fail closed and retire the legacy API;
   - P7: put the audience in the scope;
   - P9: look the key up again after a fresh refusal;
   - add the thread lock and the full-sequence vectors;
   - make the section 5 text fixes.
