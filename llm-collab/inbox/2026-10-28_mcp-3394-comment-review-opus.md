# Review: draft comment for MCP spec issue 3394 (Opus 5.5, 2026-10-28)

Reviewed: `outreach/MCP-3394-comment-2026-10-28.md` (draft 1, body 3,907 characters, 569 words). I checked it against the extension draft, the middleware, the claim store, the binding, the tests, the vectors, the tutorial and CI, and the posted FSIG-17 reply. The working tree equals tag `v0.4.14` for every file I reviewed (`git diff v0.4.14 HEAD` over them is empty), and both packages are at 0.4.14.

What I ran (nothing in the repository was changed: `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):
- the Python suite: 199 passed;
- the Node replay vectors (`node --test test/replay-vectors.test.js`): 19 of 19;
- the tutorial (`examples/mcp-server/client.py`) on the installed mcp 1.29.1: 2 PAID (the replay was marked and had the same receipt) and 7 REFUSED, and it printed "server advertises it in capabilities: no (mcp 1.x has no server-side extension registry)";
- two probe scripts in the session scratchpad: `...\scratchpad\opus3394\probe_3394.py` and `probe_refusal_text.py`. Their results are quoted below.

Thread source: the brief's path does not exist. The file is at `C:\Users\DELL\.claude\projects\E--LivingAIAgents\1249a6be-...\tool-results\bt6b3rwrp.txt`, and it is **not verbatim**: 29 of the 41 comments are cut off with "[...]", pavancharak's 10-28 answer among them. For full texts I used the API dump `...\scratchpad\ghdata\c1.json` (40 comments, up to 10-26 23:05 UTC). I could read pavancharak's 10-28 answer only in part.

## 1. Verdict

**Post with the changes listed, not as is.** Draft 1 answers all four questions and its tone is mostly right. But six statements are wrong or too broad against the code. Four of them also contradict the FSIG-17 reply posted this morning. Those statements are about the very authorization-change and tenant rules this thread cares about most. The trimmed version in section 4 (2,998 characters) fixes them and drops no answer.

**Timing and venue.** Post it, but not straight away:
- **After the fixes.**
- **After arjun2075 has answered pavancharak's 10-28 reply, or after about a day, whichever comes first.** The questions were put to pavancharak, who answered them at 03:20 UTC. A longer parallel answer an hour or two later reads as crowding him out. A day costs nothing: there is no public SEP branch yet (ndreno's plan of 10-13 is still the latest word), and implementation evidence is most useful before the wire format is fixed.
- **Ideally on a later day than the FSIG post.** Two comments from the author in two MCP repos on the same day, both citing 3394, can read as a campaign.
- **After the two link-target problems in B7 are fixed on main.**

Do **not** shorten it to a pointer. The thread expects answers that stand on their own. A pointer to a 367-line draft in LAP vocabulary would leave the mapping work to arjun2075, and the draft at the tag has a stale line on exactly the tenant rule (B7).

**Preconditions:**
- Athar's OK.
- Posted from the personal account.
- #3394 re-read for newer comments.
- The CI log of the `mcp>=2,<3` lane at the tag shows "server advertises it in capabilities: {...}". CI does not assert that line (see section 5), and mcp 2.x is not installed here. If the log does not show it, say "not on mcp 1.x" instead of "mcp 2.x only".

## 2. Blocking issues

**B1. "Recognition runs before the authorization checks, so an authorization refusal on a retry means no execution is recorded under that key"** (draft line 19). This is false, and the next sentence of the draft contradicts it.
- **Order in the code.** Recognition runs **after** the passport checks (signature, audience, expiry, issuer allow-list, proof-class floor) and the call-signature checks, and **before** the envelope checks: `mcp_middleware.py` 148-167, then 210-227, then 229-241.
- **What a passport-level refusal means.** On a retry it says nothing about execution. `test_recognition_order.py` 235-244 gets `LAP_ERR_EXPIRED` on a key that completed. Probe C did the same on a completed key with `LAP_ERR_EXPIRED`, `LAP_ERR_PROOF_CLASS` (the server raised its floor) and `LAP_ERR_ISSUER` (issuer removed from the allow-list).
- **The precise rule** is in the extension draft (line 316): "An envelope or cap refusal (`LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP`) on a retry ... means that no execution is recorded under that key".
- **The FSIG reply** (line 11) says the same: "recognition now follows the passport and signature checks ... So an envelope or cap refusal on a retry means only that no execution is recorded".
- **Fix:** "Recognition follows the passport and signature checks and precedes the envelope checks, so an envelope or cap refusal on a retry means no execution is recorded under that key."

**B2. "a replaced, cut or reissued authorization never turns the operation into a fresh entry"** (line 19). This is too broad, and it fails on the exact case arjun2075 raised on 10-11 ("If the policy/delegation epoch simply becomes part of the lookup key, a retry after revocation could miss the original record").
- **The slot includes the agent key.** It is (audience, agent key, idempotency key): `microcore.py` 268-303 (`_slot`), and extension draft line 229, "the claim for `(sub, key)`".
- **What happens on rotation.** A passport reissued by the same principal to a **new agent key** starts a new slot, and the retry executes again. Probe A: "first call (agent 1): executed / retry, reissued to agent 2: executed / tool executions: 2".
- **The FSIG reply** (line 9) already says so: "a rotated agent key is a new scope".
- **Fix:** add "for the same agent key; a rotated agent key starts a new slot and the retry runs again".

**B3. "The claim is scoped by the server's tenant for the principal: the same key from a principal the server does not map to that tenant is refused, neither replayed nor run"** (line 19). This is only true when the **agent key** is also the same.
- **Code and tests.** `claim_scope` and `_status` (`microcore.py` 231-254, 306-310); test 173-195; vector RP-11.
- **Another principal with its own agent key** and the same idempotency key runs as a separate operation. Probe B: "principal B / agent 2: executed"; "principal B / agent 1 (shared): LAP_ERR_ISSUER".
- **Conflict with the FSIG reply.** Read without that qualifier, the sentence contradicts FSIG line 13, which says another principal's request is "separate here".
- **Fix:** "another principal through the same agent key is refused, neither replayed nor run, unless the server maps both to one tenant; one with its own agent key is a separate operation." This also gives arjun2075 the defined rule he asked for on 10-11 ("Whether that request represents a separate operation or a rejected context change should be defined").

**B4. Discovery overstates platform coverage** (line 17: "advertises ... under `capabilities.extensions` (the `initialize` result; `server/discover` from 2026-07-28)").
- **Only mcp 2.x advertises.** The reference does so only on mcp 2.x, through `server/discover`. `microcore_extension` is "mcp 2.x only" (`mcp_extension.py` 280-282); the extension draft says "a 1.x server enforces the extension per tool but does not advertise it" (line 346); the README says so at line 67; my run on 1.29.1 printed "no".
- **The `initialize` path is never exercised** by the reference.
- **Why it matters.** The same comment says the tutorial runs on 1.x and 2.x, so a reader will assume both advertise.
- **Fix:** "(in the reference, mcp 2.x only; 1.x has no server-side extension registry)".

**B5. "Retention is a window the server publishes"** (line 19) implies a mechanism that does not exist.
- **No field to publish it.** The server settings table (extension draft 2.3, lines 98-103) and `microcore_extension` advertise `aud`, `receipts`, `min_proof_class` and `server_did`, and no retention member.
- **The reference never evicts.** `IdempotencyCache` is a plain dict with no TTL (`microcore.py` 296-298), and it does not survive a restart. Probe D: "before restart: executed / after restart: executed". A restart is the reference's own version of madeinplutofabio's day-2 lookup miss.
- **Fix:** "Retention is independent of authorization lifetime (a claim is never evicted because its passport expired), but the draft defines neither how the window is published nor what follows it; the reference store never evicts and does not survive a restart."

**B6. "no claim of exactly-once past the effect boundary"** (line 21) reads as a claim of exactly-once inside the boundary.
- The FSIG reply says "Not claimed: exactly-once" (line 17).
- The brief lists exactly-once as an overclaim.
- The reference also does not survive a restart (B5), so not even "exactly once inside the server" holds across restarts.
- **Fix:** "no exactly-once claim".

**B7. The link target contradicts the comment** (not the comment's own text; fix before posting or link elsewhere).
- **Stale conformance check.** Extension draft line 348, conformance check (7), says: "a claim is scoped by tenant, so another principal's call with the same agent key and key **executes as a separate operation**." That is the first-pass rule. It contradicts the same draft's 4.1 step 4 (line 229), the 4.3 table (line 251), 5.6 (line 316) and section 7 (line 334), and the code, the tests and RP-11, all of which refuse.
- **Who will read it.** arjun2075 builds vectors and will read section 8.
- **Fix in the draft on main.** Correct the check to: "...is refused (`LAP_ERR_ISSUER`), neither replayed nor run, unless the server maps both to one tenant". Then link the draft at that commit. Alternatively, keep the tag link and accept the risk; the tag is anchored and cannot change.
- **A second mismatch in the same document, not blocking.** Section 4.2 and conformance check (3) say the refusal's first text block "begins with the error code". On mcp 1.29.1 it begins with the SDK's prefix (`probe_refusal_text.py`: `'Error executing tool pay_invoice: LAP_ERR_AUTH_MISSING: ...'`, `begins with LAP_ERR_: False`). The tutorial's `_reason()` strips that prefix, which hides it.

## 3. Line edits to draft 1

These apply if you fix draft 1 instead of using section 4. Line numbers are those of the draft file.

1. **Line 11:**
   - Change "answering your four questions from an implementation rather than a proposal: an MCP extension my project ships" to "your four questions to pavancharak, answered for one more design: an MCP extension I maintain".
   - Why: the questions were put to another commenter. "Rather than a proposal" sets this against others' proposed vectors. "Ships" suggests production.
   - Keep "One author; no adoption claimed." No @ for pavancharak; naming him without @ is enough.
2. **Line 13:**
   - Change "(RFC 9421 base: ...)" to "(an RFC 9421-style base: ...)". The draft uses RFC 9421 "for the shape" (1.3).
   - Optional: "even for identical bytes" to "even for identical arguments". The key is inside the signed base, so the bytes differ. FSIG used "identical bytes", so this is optional.
3. **Line 15:**
   - Change "Tool arguments and the wire are untouched, and a server without the extension ignores the `_meta` key, but the client application has to build and sign the object" to "No SDK change (the tutorial passes the object through the Python SDK's `call_tool(..., meta=...)`, `client.py` 100, CI on 1.x and 2.x), but the client application has to build and sign it".
   - Why: the `_meta` entry is on the wire. "A server without the extension ignores the key" is an untested claim about other servers.
4. **Line 17:** B4.
5. **Line 19, the indeterminate answer:**
   - Change "executor died after the effect may have happened" to "the tool raised, or its executor died, after the effect may have happened (Majny's effect-then-error)".
   - Why: a tool that raises is how the reference actually reaches this state (`mcp_middleware.py` 262-271; test 209-225). Probe E: the retry is refused with "awaiting reconciliation", and the tool ran once.
   - Change "resolved only against the effect's system of record" to "resolved only by reconciliation". The reference provides `complete`/`release` for an operator and does not reconcile on its own.
6. **Line 19:**
   - Add "both `LAP_ERR_REPLAY`, told apart by the reason text" for in-flight and indeterminate (`mcp_middleware.py` 183-189; draft 4.3 line 262).
   - Why: this is the "key reserved, result unknown" distinction ndreno wants on the wire, and here it is not a separate code.
7. **Line 19:**
   - Change 'refused as "executed, result withheld"' to "refused with `LAP_ERR_REPLAY_WITHHELD` (this key executed earlier; its result is withheld)".
   - Why: the quoted words are not the actual text (`mcp_middleware.py` 200-201).
8. **Line 19:**
   - Change "(your 10-11 split ...; ryjen's vector)" to "(your 10-11 split; there is no revocation list, so ryjen's case holds only as expiry plus a narrower passport)".
   - Why: revocation is out of scope (draft 1.1; section 7, "there is no revocation list in Micro-Core"). An unexpired broader passport still gets the result disclosed.
9. **Line 19:** B1, B2, B3, B5. Also add "(same agent key)" to "a reissued one replays".
10. **Line 21:** "(claim store and authorization check ...)" becomes "(claim store and envelope check ...)". The vectors run `check_invocation` only, never the passport or signature checks. FSIG says "replay check".
11. **Line 21:** "after a simulated crash" becomes "after a tool raised and after a simulated executor death" (`test_idempotency_recovery.py` 76-89; test 143, 164, 209-225).
12. **Line 21:** B6, and add "(a restart forgets every claim)" after "In-process claim store".
13. **Optional, useful to the SEP:** add one sentence that answers arjun2075's closing question ("whether existing MCP mechanisms already provide a sufficient interoperable approach"): "Existing mechanisms (`_meta`, extension negotiation, tool `_meta`) carried all of this, but only between peers that both implement this one extension."
14. **Optional offer** ("I can map these onto ...#2"): it was cut from section 4 for length. Add back "Happy to map these onto arjun2075/mcp-b1-lost-response-repro#2." (+64 characters) if wanted. Keep the full cross-repo reference: a bare "#2" would link to issue 2 of the spec repo.

## 4. Trimmed version (2,998 characters, 444 words; ready to paste)

```
@arjun2075 your questions to pavancharak, answered for one more design: an MCP extension I maintain (one author, no adoption claimed; [draft and code at v0.4.14](https://github.com/atharnouman/living-agents-protocol/blob/v0.4.14/output/lip/LIP-4-mcp-extension-draft.md)).

**Identity.** The client picks the key before the first mutating call and keeps it across a lost response; the server never issues it. It rides in request `_meta` with a principal-signed passport, under the agent's signature over tool, arguments and key. Same key and request: one execution. Same key, different request: refused in every state. New key: a new operation, so an intentional repeat (Majny's case) is not a retry.

**Unmodified client:** no. The Python SDK is unchanged (`call_tool(..., meta=...)`), but the application must build and sign the object; without it the call is refused, typed, before the tool runs.

**Discovery.** `capabilities.extensions` (reference: mcp 2.x only) and, per tool, `tools/list` `_meta`: action, resource, amount argument, whether a key is required.

**Stored result vs unknown outcome.** Before any execution, a same-key retry gets:
- completed: stored result and receipt, marked `replayed: true`;
- in flight: `LAP_ERR_REPLAY`;
- indeterminate (the tool raised, or its executor died, after the effect may have happened; Majny's effect-then-error): `LAP_ERR_REPLAY` with a reason naming reconciliation, never released by time; the client must not mint a new key;
- executed, but the passport presented now no longer covers its action, resource or unit: `LAP_ERR_REPLAY_WITHHELD` (your 10-11 split; no revocation list, so ryjen's case holds only via expiry plus a narrower passport).

Recognition follows the passport and signature checks and precedes the envelope checks, so an envelope or cap refusal on a retry means no execution is recorded. Claims sit in (audience, agent key, key) and outlive the passport: an expired one's refusal says nothing; the same principal's replacement is recognised as above, but a rotated agent key starts a new slot (the retry runs again); another principal through the same agent key is refused, neither replayed nor run, unless mapped to the same tenant; with its own agent key, a separate operation. Retention: publication and post-window behaviour are undefined (madeinplutofabio's day-2 case is open).

**Evidence and limits.** 18 stateful vectors (claim store and envelope check, Python and Node); the full check order in Python only; a tutorial in CI on mcp 1.x and 2.x over stdio (a marked replay with the same receipt; seven typed refusals). No dropped response is injected; tests repeat the key after completion, in flight, after a raise or simulated executor death, under a replaced passport. In-process store (a restart forgets all claims), synchronous tools, no exactly-once claim. Existing mechanisms carry this, but only between peers that both implement it.

AI use: an AI assistant helped draft this; I reviewed it before posting.
```

What was cut relative to draft 1, all recoverable from the linked draft:
- the extension identifier;
- the protocol-revision detail of discovery;
- the RFC 9421 component list;
- the sentence "a server without the extension ignores `_meta`";
- the offer (edit 14).

What was added:
- the qualifiers in B1 to B6;
- the shared `LAP_ERR_REPLAY` code;
- the explicit mapping of the effect-then-error case;
- the caveat that there is no revocation list;
- the one-line answer to arjun2075's "existing mechanisms" question.

The trimmed version is consistent with every statement in the FSIG reply:
- recognition follows the passport and signature checks (FSIG line 11);
- an envelope or cap refusal means no execution is recorded (line 11);
- a rotated agent key is a new scope (line 9);
- an unmapped principal key is refused (line 9);
- another principal's request is "separate" (line 13): true here when it comes with its own agent key;
- "Not claimed: exactly-once; durability" (line 17).

@-mentions: only @arjun2075. pavancharak, ryjen, Majny and madeinplutofabio are named without @, which is right: no pings.

## 5. Checked and found correct

- **Identity and request shape**
  - The client chooses the key and the server never issues one (draft 3.2; `sign_tool_call`). It is placed in request `_meta`, and the signature base covers method, target, content digest, passport hash and key (draft 3.4; `signature_base_for_tool_call`; `test_mcp_extension.py` 151-159).
  - Same key and same request: one execution. A new key is a new operation (`test_mcp_extension.py` 117-133; RP-12; test 148-149).
  - The same key for a different request is refused while completed, in flight or indeterminate (test 131-146; RP-07 to RP-09; tutorial line 137).
- **Discovery and refusals**
  - The tool declares the extension in its `tools/list` `_meta` (`tool_meta`; the tutorial prints it).
  - A call without the object gets a typed refusal and the tool does not run (`lap_tool` 251-252; tutorial line 143).
- **The four answers**
  - All four come before execution (`settle`, `mcp_middleware.py` 172-208).
  - Completed: `replayed: true` sits in the result `_meta` (`mcp_extension.py` 172-190; test 268-277; tutorial).
  - Indeterminate: the reason names reconciliation; there is no release by time (no TTL); the client must not mint a new key (draft 5.6).
  - Withheld: when the passport no longer covers the action, resource or unit (test 113-128; RP-03 to RP-05), while a cut to the cap amount alone still replays (test 97-110).
- **Expiry and reissue**
  - An expired passport is refused before recognition.
  - A reissue by the same principal to the same agent key replays (test 235-244).
- **Evidence**
  - 18 shared vectors, loaded by both suites (I ran both).
  - Full check order: Python only (draft section 8).
  - Tutorial: 2 paid calls, the second a marked replay with the same receipt, and 7 typed refusals. Confirmed locally on mcp 1.29.1. The CI matrix covers `mcp>=1.2,<2` and `mcp>=2,<3` and greps for exactly those lines.
  - No dropped response is injected. The tests present the same key again in flight (by a direct `claim`), after `mark_indeterminate`, after a tool raised, and under a replaced passport.
  - Limits as stated: in-process store, synchronous tools only (`lap_tool` refuses `async def`), sequence in Python only.
- **Thread conventions, and the cases draft 1 maps correctly**
  - The AI-use line and the disclosure match the thread's conventions.
  - Nothing is claimed about Parmana or other commenters' tools, or about maintainers' intent.
  - Intentional repeat (Majny); expiry (madeinplutofabio and arjun2075, 10-12); retention kept separate from authorization lifetime; the day-2 case left open; the identity surviving the retry, given the client keeps the agent key.
- **Not verified here** (no network): the PyPI, npm and GitHub release state; the CI run status at the tag; mcp 2.x behaviour (not installed). CI asserts neither the advertisement line on 2.x nor any pytest of `microcore_extension`.

Outside the comment, for the errata list:
- **LIP-4 micro-core draft.** Its bullet "Recognition is independent of authority" says "a reissue by the same signer ... never turns the same operation into a fresh entry". That is the same too-broad statement as B2, with no agent-key condition. The posted FSIG reply has the caveat; LIP-4 does not.
- **Extension draft 2.3.** It needs a retention member if sections 5.6 and 7 are to keep saying the server "publishes" the window.
- **Draft 4.2 and conformance check (3)** against the SDK's error prefix (B7).
