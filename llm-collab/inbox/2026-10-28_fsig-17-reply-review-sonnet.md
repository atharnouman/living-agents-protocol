# Review of the FSIG #17 reply draft: fresh Sonnet 5.5 agent, read-only (received 2026-10-28)

Verbatim hand-back. Model output, treated as a reviewer's opinion; the owner decides. Its corrected text is a candidate, merged with the Opus review's before posting.

---

**(1) Defects** (l. = line of the reply draft; fixes are applied in (2), except 10 and 12)

1. "A payment that never executed leaves no record ... nothing is consumed" (l.7): a tool that raises leaves an indeterminate claim (mcp_middleware.py:225-228); "consumed" is the venue's ledger term, absent here.
2. Missing: the in-flight and indeterminate states, King Yew's "held" payment. They keep the claim; a retry gets `LAP_ERR_REPLAY` under a cut (mcp_middleware.py:195-197; my run), untested with a replaced passport.
3. "never counted as a new operation", "Never re-executed" (l.7, 9): tenant defaults to `iss` (microcore.py:227), so a new issuer key executes again; the cache is in-process.
4. "arjun2075's rule in 3394, read literally" (l.9): his 2026-10-11 comment offers "proposed cases" and "negative vectors" for a future SEP, and leaves the response once permission is gone undefined.
5. "method, tool and content digest, not the authority digest" (l.11): identity is `@method`, `@target-uri`, `content-digest` (microcore.py:196-209); the reservation also stores the passport hash (mcp_middleware.py:209-211).
6. "held only under the same envelope until today" (l.13): 0.4.13 also replayed under a raise or a cut above the amount (my run); the quote's "A" is not the original's; the receipt sentence corrects the linked extension draft (line 310), not the comment; 0.4.13's other two faults are undisclosed.
7. "marker and ... claim record carry that" (l.13): `replayed` is unsigned (extension draft sec. 5.2); neither is checkable from the receipt.
8. "15 shared stateful vectors" (l.15): RP-02 to RP-06 have no cache steps; the vectors cover the cache and `check_invocation`, not the check order (only test_recognition_order.py).
9. Corpus case "another principal's `delegation.authorityDigest`" (l.11): draft -00 has `authorityDigest` and `delegation.subject`, no principal or tenant field; no manifest row I could read at 8f9cdc4a has the case (CS15/16 vary `limitDigest`; CS11/12/17 `operationKey`), so it is new.
10. Blocker: no `v0.4.14` tag exists; origin/main is 9 commits behind (no vectors file); PyPI and npm show 0.4.13. Post only when the pinned URL resolves and both show 0.4.14.
11. Minor: replay "result and receipt" holds for object results only (mcp_middleware.py:232-236); the draft is 488 words.
12. Spec: extension draft line 316 both forbids and asserts reading an envelope or cap refusal as not executed; line 348 says "adds five", lists seven.

Verified (both suites green; scripts on v0.4.13 and HEAD): check order (mcp_middleware.py:195-202), withheld path (:168-173), key reuse in every state (microcore.py:268-277), tenant scope (:212-230), identical receipts; no newer #17 comment. Tone plain; nothing sensitive exposed.

**(2) Corrected reply** (442 words)

---
@kingyewchoo, from the enforcement side: a call refused before the tool ran leaves no claim, so its retry is a first execution under the limit then in force (a raise lets it through, a cut refuses it). A call that executed, is running, or whose tool raised keeps its claim, keyed by tenant (by default the issuer's DID), agent key and the agent's signed idempotency key, never by the limit document. Replacing the limit neither drops it nor makes its retry a new operation.

My Python reference did not do what my 26 October comment said: it checked the envelope before the claim, so after a cut a retry of an executed payment got a cap error hiding the execution. Fixed in 0.4.14 (tag `v0.4.14`): recognition now follows the passport and signature checks. A completed key returns the stored result and receipt (object results), marked `replayed` (unsigned), if the authority presented now still covers the action, resource and unit; the amount is not compared with the cap, since a replay spends nothing. Otherwise the server says the key executed earlier and withholds the result; an in-flight or indeterminate key is refused. So an envelope or cap refusal on a retry means no execution is recorded under that key. This fits what arjun2075 proposed in modelcontextprotocol/modelcontextprotocol#3394; the disclosure check is my reading.

@astrogilda, from 0.4.14 your three cases hold: same key and request, one retry; same key and a different request, refused in every state, in flight and indeterminate included; a new key, a new operation even for identical bytes. Retry identity is method, target URI and content digest, not the passport hash. A case your corpus may want: the same `operationKey` and `requestDigest` from another principal (another authority document), a separate operation here since claims are scoped by tenant.

Corrections. In 0.4.13 a reused key returned the first result, principals sharing an agent key shared a claim, and "a retry with the same key gets the stored result back with the same receipt" held only if the current envelope would also admit a fresh call. Contrary to my linked draft, a receipt alone does not show that a retry did not execute again: identical request and response bytes under distinct keys give identical receipts (Ed25519 is deterministic). Whether the receipt should bind the operation key is open.

15 shared vectors for the claim cache and the envelope check, run by both test suites: https://github.com/atharnouman/living-agents-protocol/blob/v0.4.14/output/lip/test-vectors/microcore-replay-vectors.json. Not claimed: exactly-once; durability (the claim store is in-process); claims across an issuer key change; cumulative limits and held entries (yours and the spend authorizer's).

AI use: an AI assistant helped draft this; I reviewed it before posting.
---

**(3)** Yes, once the tag, URL and registry versions resolve, item 12 is fixed and #17 is rechecked; from the personal account.
