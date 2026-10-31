# Review of the draft comment for MCP spec issue 3394 (Sonnet 5.5, 2026-10-28)

Independent of the Opus review (I did not open `scratchpad\opus3394`). Read-only: this is the only file I wrote in the repository tree; my probes are in my scratchpad. The owner decides; this is advice.

## 0. Inputs and what I ran

- Read: the brief; `outreach\MCP-3394-comment-2026-10-28.md` (draft 1: 3,907 characters raw, 3,727 with links shown as their text); `outreach\FSIG-17-reply-2026-10-28.md`; the whole extension draft; `mcp_middleware.py`, `mcp_extension.py`, `microcore.py`; the four named test files plus `test_mcp_extension.py`; all 18 vectors; the tutorial (`README.md`, `server.py`, `client.py`); `.github/workflows/ci.yml`; `lap-reference/test/replay-vectors.test.js`; the thread.
- Tag `v0.4.14` is commit 249555f. HEAD 7e5f3fb differs from it only in `.ots` proofs and anchor notes (`git diff --stat v0.4.14 HEAD`), so the code, tests and drafts I read are the tagged ones.
- Ran: `python -m pytest -q` in `lap-python`: 199 passed. `node --test test/replay-vectors.test.js`: 19 of 19 (18 vectors and the coverage check). The tutorial (`python client.py`) on mcp 1.29.1: 2 "receipt verified", 7 REFUSED, "same receipt ... marked replayed: yes", as README lines 134 to 143 show. Probes P1 to P7 in `scratchpad\probe_3394.py` (rotated agent key, new key with identical bytes, an unknown claim 30 days later, a revoked-but-valid old passport, a restart, refusal order, message texts) and `scratchpad\probe_raw_refusal.py` (raw refusal text, `initialize` capabilities).
- Not done: mcp 2.x is not installed here, so what is said about the 2.x leg (advertisement in `server/discover`, the CI result on GitHub) rests on `ci.yml` and the README. No network: I could not re-read #3394 for comments newer than the saved file, or check PyPI, npm or the Actions run.
- Two problems with the inputs. (1) The thread path in the brief does not exist. The file is `C:\Users\DELL\.claude\projects\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\tool-results\bt6b3rwrp.txt`. (2) It is not verbatim: every comment is cut to a preview ending "[...]", including ryjen's vector, madeinplutofabio's expiry case and Majny's cases. I checked those against the API copy in the session scratchpad (`scratchpad\ghdata\c1.json`: 40 comments up to 2026-10-26T23:05Z). pavancharak's 2026-10-28 03:20 reply is in neither in full, so the draft header's "refused with a 409, no recovery path" cannot be verified ("no recovery path" goes beyond the visible "A retry with the [...]"). The comment body does not use it; keep it that way.

## 1. Verdict

**Post with the changes listed**: five wording fixes (section 2, issues 1, 2, 4, 5 and 6), one repository fix (issue 3), and the shortened text in section 6. Not as is: draft 1 overstates in places arjun2075 is likely to test (a rotated agent key, ryjen's revocation vector, discovery on mcp 1.x, retention), and the draft it links contradicts it on the different-tenant rule. Not "do not post": the factual core is sound (section 7), arjun2075's questions are two days old, and an implementation-backed answer is what he asked for.

## 2. Blocking issues

### 1. "A replaced, cut or reissued authorization never turns the operation into a fresh entry" is false when the reissue names a different agent key

Draft line 19. Evidence:
- The claim slot is audience, agent DID (`sub`) and key (`microcore.py:301-303`, `_slot`). The `claim_scope` docstring (`microcore.py:231-247`) says a claim survives replacement "by the same signer or a mapped one".
- P1: same principal, passport reissued naming agent 2, same key, identical bytes: the tool ran again (`['INV-1', 'INV-1']`).
- Your own FSIG-17 reply, posted this morning, says "a rotated agent key is a new scope" (`FSIG-17-reply...md` line 9). The LIP-4 erratum scopes its own "never" to "a reissue by the same signer or by one the server maps to the same tenant", right after defining the claim as keyed by audience, agent key and key (`LIP-4-micro-core-draft.md:62`). The comment drops that scope.
- Why it matters: arjun2075's 10-11 worry is exactly a delegation change creating a fresh dedup entry. This is the case where it does.

Fix: "...never turns the operation into a fresh entry (same agent key; a rotated agent key is a new scope)".

### 2. Discovery: the reference does not advertise on mcp 1.x, and nothing asserts the 2.x advertisement

Draft line 17: "advertises the extension under `capabilities.extensions` (the `initialize` result; `server/discover` from 2026-07-28)". Line 21 then says the tutorial runs on 1.x and 2.x. Evidence:
- On mcp 1.29.1 the `initialize` result has `capabilities.extensions` = None (probe output) and the tutorial prints "server advertises it in capabilities: no (mcp 1.x has no server-side extension registry)" (`client.py:97`; README 67 and 123; extension draft 346). `microcore_extension` is mcp 2.x only (`mcp_extension.py:273-283`).
- No test calls `microcore_extension` or reads `capabilities.extensions` (grep of `lap-python/tests`), and `ci.yml:57-60` asserts only the receipt count, the replay line, `LAP_ERR_KEY_REUSE` and 7 REFUSED. The 2.x advertisement is shown by the example client's output, not asserted anywhere.

Fix: say it is advertised on 2.x, that 1.x has no server registry (only the tool `_meta` and the refusal tell the client), and label it as shown by the example client, not asserted in CI.

### 3. The linked draft contradicts the comment on the different-tenant rule

- Extension draft line 348, conformance check (7): "a claim is scoped by tenant, so another principal's call with the same agent key and key executes as a separate operation."
- Same file, line 229 (step 4): "the same key under an issuer the server does not map to that tenant is refused (`LAP_ERR_ISSUER`), neither replayed nor run again"; also lines 251, 316 and 334. Code: `microcore.py:307-308` returns `tenant_mismatch`, the middleware raises `LAP_ERR_ISSUER` (`mcp_middleware.py:178-182`). Vector RP-11 expects `tenant_mismatch`; `test_recognition_order.py:173-195`; `THREAT-MODEL.md:62` also says refused.
- The sentence is unchanged since 7f116fc, where the tenant sat in the claim slot and it was true. The second pass (249555f) changed the behaviour to refuse ("a second signer of the same agent key is refused, not joined or run again") and fixed the other places, not (7).
- Why it matters: this is the rule arjun2075 asked to be explicit ("separate operation or a rejected context change"). The comment links the draft at the tag, which is immutable (PyPI, npm and the release are out).
- Related: the posted FSIG reply says "under another principal's (separate here: claims are scoped by tenant)" (line 13). That holds only if the other principal brings its own agent key; with the same agent key it is refused. The comment must name the agent key, and the two texts then agree with FSIG line 9.

Fix, in order of preference: (a) correct (7) in the draft ("...same agent key and key under an issuer the server does not map to the claim's tenant is refused (`LAP_ERR_ISSUER`), neither replayed nor run again; another agent key is a separate scope"), add a change-log line, restamp (the draft is Bitcoin-anchored: `LIP-4-mcp-extension-draft.md.ots`), and link the comment to the corrected commit, not the tag; (b) leave the draft and add one sentence to the comment (204 characters): *Section 8 check 7 of that draft still says a second principal on the same agent key "executes as a separate operation"; that sentence is stale, and section 4.1 step 4 and vector RP-11 (refused) are right.*; (c) not recommended: post and hope nobody opens section 8. Consider fixing line 13 of the posted FSIG comment as well ("refused if it reuses the agent key, separate if the agent key differs").

### 4. "ryjen's vector" is claimed without the revocation limit

ryjen 2026-10-11 (full text, API copy): "2. P's relevant authorization is revoked (epoch B). P retries K/X with a fresh JSON-RPC request ID. 3. ... finding a cached K/X result must not bypass the *current* authorization check on whether P can receive that result."
- The reference has no revocation: `LIP-4-micro-core-draft.md:77` ("no revocation infrastructure (short `exp` is the revocation)"); extension draft lines 17 and 339. "The authorization presented now" is the passport on the retry.
- P4: after the principal issues a narrower passport, a retry with the narrower one is withheld (`LAP_ERR_REPLAY_WITHHELD`), but a retry with the old, still-valid passport replays. The reference meets the "current authorization" half only as far as the caller presents the current document.
- Draft line 19 pairs the withheld case with "ryjen's vector" and states no limit.

Fix: "No revocation channel: 'now' is the passport on the retry." Keep the attribution only with that sentence.

### 5. "One execution" and "executor died" need the in-process qualifier beside them

- Draft line 13: "Same key, same request: one execution." Line 19: "executor died after the effect may have happened, refused with a reason naming reconciliation".
- The store cannot see a death: `microcore.py:286-293` ("This in-process map cannot observe its own death"); extension draft 335 ("single-process only"). The unknown state is reached in the middleware when the tool raises (`mcp_middleware.py:268-271`) or when storing the result fails twice (`:288-296`), and in tests when `mark_indeterminate` is called by hand (`test_recognition_order.py:143, 164`; `test_idempotency_recovery.py:82`). Reconciliation is a manual `complete()` or `release()` (`microcore.py:354-394`); there is no reconciler. P5: a fresh cache (a restart) lets the same key and bytes run again.
- The caveat is in the draft, but only in the last paragraph ("In-process claim store", "simulated crash"). Other commenters report real process kills over durable stores (Srivatsa03, 10-22: K1 and K2 with `os._exit`, SQLite and Postgres), so the qualifier has to sit next to the claim.

Fix: "one execution while the store lives"; name what makes a claim unknown in the reference (the tool raised); add "reconciliation is a manual `complete` or `release`" to the limits.

### 6. Retention: "a window the server publishes" implies a capability the reference lacks

- Draft line 19: "Retention is a window the server publishes, independent of authorization lifetime". The advertisement has no retention member (extension draft 2.3 table, lines 98-103). Neither port evicts: no eviction in `microcore.py`; in `microcore.js` `seen.delete` appears only in `release` and `abandon` (lines 233, 240). "Published retention window" is a spec statement (`microcore.py:293`; extension draft 316, 335), not a mechanism.
- ndreno 2026-10-13: the server should "advertise its retention window and reject a key it can no longer vouch for", which needs the key "to carry, or be tied to, a creation time". The reference's key is an opaque string; the signed `created` is per call. It cannot do that either.

Fix: "Retention: the reference never evicts; post-window behaviour is open (madeinplutofabio's day-2 case)."

## 3. Other fixes (not blocking)

1. "RFC 9421 base" (line 13): RFC 9421-shaped, not conformant. `@method` is `tools/call`; the digest is base64url without padding where RFC 9530 uses standard base64 (extension draft 187; open question 2, line 355). Say "RFC 9421-style" or drop it; the SEP does not need it.
2. "another method" (line 13): `@method` is constant in this binding (extension draft 265). Say "another tool or other arguments". Another tool is refused only if the tools share one claim store (`test_recognition_order.py:198-206`; README 161).
3. "Recognition runs before the authorization checks, so an authorization refusal on a retry means no execution is recorded" (line 19): recognition runs after the passport checks (audience, expiry, issuer, proof class) and the call signature, and before the envelope checks. Only an envelope or cap refusal (ACT, RES, CAP) means "no execution recorded". An expired-passport refusal says nothing, which the draft states one sentence later, so the two read as a contradiction. Use the FSIG-17 wording (line 11; extension draft 316).
4. Claims about other servers and SDKs (line 15): "a server without the extension ignores the `_meta` key", "not an SDK or protocol change", "the wire [is] untouched". Only the reference server and the Python SDK were tried (`call_tool(..., meta=...)`, mcp 1.29.1 `client/session.py:386-405`). "As the core specification requires of unknown keys" is in the draft (143, 322); I could not check it. Scope the sentence ("Python SDK checked only").
5. Quotation marks on "executed, result withheld" (line 19): not a message. The text is `LAP_ERR_REPLAY_WITHHELD: this key executed earlier; its result is withheld under the current envelope (LAP_ERR_ACT)` (`mcp_middleware.py:200-201`). Name the code or drop the quotes.
6. Label the author's reading, as FSIG-17 did ("the amount exemption is my reading", line 11). The draft credits "your 10-11 split", but what counts as current permission (action, resource and unit; not the amount) is the author's choice.
7. In flight and unknown share `LAP_ERR_REPLAY` (`mcp_middleware.py:184` and `188`; extension draft 262) and differ only in the reason text. arjun2075 asked how a client tells a stored result from an unknown outcome, and ndreno (10-06) wants "a distinct outcome for 'key reserved, result unknown'". "One of four answers" suggests four typed outcomes. Say that two share a code.
8. Evidence mixing (line 21): the "seven typed refusals" are one `KEY_REUSE`, one `IDEMPOTENCY` and five about cap, digest or a missing object, so mostly not about retries. The cases "after completion, in flight, after a simulated crash and under a replaced authorization" come from unit tests (`test_recognition_order.py:113-128, 140-146, 152-170`), not from the tutorial in the sentence before. Nothing in the tutorial counts executions; the unit tests do (`runs`).
9. The tutorial infers non-execution from receipt equality: `README.md:136` and `client.py:119` print "same receipt, no second payment: yes", and `ci.yml:58` gates on that line. Extension draft 314 and your FSIG-17 correction (line 15) say equal receipts prove nothing. The comment's "marked replay with the same receipt" is fine; do not let it stand as the evidence. Consider changing the tutorial line to "marked replayed: yes".
10. Spec against reference on the refusal text: extension draft 237 and conformance (3) say the first text block "begins with the error code". The reference's raw text is `Error executing tool pay_invoice: LAP_ERR_AUTH_MISSING: ...` (probe; `client.py:75` strips the prefix). "Typed refusal" in the comment is fine, but arjun2075 builds executable vectors and will hit this. Fix it in the same docs commit as check (7).
11. Opening (line 11): "from an implementation rather than a proposal" contrasts with the SEP effort and is inaccurate in this thread (Parmana, Shrimp, Srivatsa03's store and others are implementations). "ships" can suggest a released extension, whereas the draft "has not been submitted anywhere" (front matter). "four questions": the header lists five items; say "questions".
12. "claim store and authorization check" (line 21): the shared vectors cover the claim store and the envelope check (RP-02 to RP-06 are `check_invocation` only). "Authorization check" suggests passport verification, which they do not cover. FSIG-17 says "replay check". Use one phrase in both texts: "envelope check".
13. "no claim of exactly-once past the effect boundary" (line 21) differs from FSIG-17's "Not claimed: exactly-once; durability (in-process store)". Use the FSIG form.

## 4. Line edits to draft 1 (if you prefer editing to adopting section 6)

| Line | Draft says | Change to |
|---|---|---|
| 11 | "answering your four questions from an implementation rather than a proposal: an MCP extension my project ships" | "answers to your 26 October questions, from a design I maintain: a draft MCP extension (not submitted anywhere) with a Python reference" |
| 11 | "One author; no adoption claimed." | delete (covered by "not submitted anywhere") or keep |
| 13 | "(RFC 9421 base: method, target, content digest, passport hash, key)" | "(an RFC 9421-style base: target, content digest, passport hash, key)" |
| 13 | "Same key, same request: one execution." | "Same key, same request: one execution while the store lives (in-process)." |
| 13 | "(another method, target or content digest)" | "(another tool or other arguments)" |
| 13 | add after "keeps it across the lost response." | "The JSON-RPC id plays no part: the example client's retry gets a fresh id from the SDK and is still recognised." |
| 13 | add at the end | "A mutating call with no key is refused; there is no server-derived fallback." |
| 15 | "Tool arguments and the wire are untouched, and a server without the extension ignores the `_meta` key, but the client application has to build and sign the object. A client-side library, not an SDK or protocol change." | "The client application has to build and sign the `_meta` object (Python SDK checked only); without it the call is refused (`LAP_ERR_AUTH_MISSING`) and does not run." |
| 17 | "(the `initialize` result; `server/discover` from 2026-07-28)" | "on mcp 2.x (shown by the example client, not asserted in CI); mcp 1.x has no server registry, so there only the tool `_meta` and the refusal tell the client" |
| 19 | "A retry with the same key gets one of four answers" | "A retry with the same key and request gets one of four answers" |
| 19 | "executor died after the effect may have happened" | "the tool raised (unless it said nothing was sent) or its executor died" and add "in flight and unknown share one code and differ in the reason text" |
| 19 | `refused as "executed, result withheld"` | "refused as `LAP_ERR_REPLAY_WITHHELD`" |
| 19 | "(your 10-11 split ...; ryjen's vector)" | "(your 10-11 split; ryjen's case; the amount is not re-compared, which is my choice). No revocation channel: 'now' is the passport on the retry." |
| 19 | "Recognition runs before the authorization checks, so an authorization refusal on a retry means ..." | "Recognition runs after the passport and signature verify and before the envelope, so an envelope or cap refusal on a retry means ..." |
| 19 | "a replaced, cut or reissued authorization never turns the operation into a fresh entry" | add "(same agent key; a rotated agent key is a new scope)" |
| 19 | "the same key from a principal the server does not map to that tenant" | "the same agent key and key from an issuer the server does not map to that tenant" |
| 19 | "Retention is a window the server publishes, independent of authorization lifetime; what happens after the window is not defined in the draft" | "Retention: the reference never evicts; post-window behaviour is open" |
| 21 | "(claim store and authorization check; both reference suites)" | "(claim store and envelope check; Python and Node)" |
| 21 | the tutorial sentence | say the retry carries a fresh JSON-RPC id; say the in-flight, crash and replaced-authorization cases are unit tests |
| 21 | "no claim of exactly-once past the effect boundary" | "Not claimed: exactly-once, durability." Add "reconciliation is a manual `complete` or `release`". |

## 5. The brief's other questions

**Does it answer the questions, in the author's terms, without pitching?** It answers all of them (the 10-26 comment holds five items: obtain and carry, before the first call, unmodified client, discovery, stored result against unknown). It does not pitch, but it leads with the project and its identifier, spends its first paragraph on extension machinery the SEP does not need (passport, RFC 9421), and puts the stored-against-unknown answer in one 1,356-character paragraph. The most SEP-relevant facts are missing: the JSON-RPC id plays no part (the thread's central premise, ndreno 9-28 and Ben-Home 10-02), a keyless mutating call is refused with no server-derived fallback (Majny's open question, Baktiyarsan's `key ?? randomUUID()` point), and the two unknown-like states share one code. Section 6 adds them.

**The thread's own cases.**

| Case | Where | Draft maps it? | Notes |
|---|---|---|---|
| Stored result is evidence, not authority to disclose | ryjen 10-11 | Partly | Withheld when the presented passport no longer covers action, resource or unit (`test_recognition_order.py:113-128`); no revocation channel (issue 4). |
| Same K/X, different tenant | ryjen 10-11; arjun2075 10-11 | Yes, in the code | Refused, neither replayed nor run (RP-11). The draft's check (7) says the opposite (issue 3). Note ryjen asks to bind identity to "authorization context" too; the reference deliberately does not, which is arjun2075's point. |
| Authorization change must not create a fresh entry | arjun2075 10-11 | Yes for the same agent key | Rotated agent key is a new scope (issue 1). |
| Expiry | madeinplutofabio 10-12 | Yes | Expired passport refused first; reissued replays (`test_recognition_order.py:235-244`, P6). |
| Retention separate from approval lifetime; day-2 case | arjun2075 and madeinplutofabio 10-12 | Labelled open, correctly | But "published" overstates (issue 6). |
| Intentional repeat against retry | Majny 10-18 | Yes | New key executes (RP-12; `test_mcp_extension.py:131-133`; P2). |
| Effect committed, then error | Majny 10-18; arjun2075 10-18 | Not in the body (header only) | A tool that raises leaves the claim unknown; the retry is refused and sends nothing (`test_recognition_order.py:209-232`). The reference does not "cache only successes". The caller gets a refusal, not a result. |
| Identity survives the retry | arjun2075 10-14 | Implicit | Say the JSON-RPC id is irrelevant. |
| Server-derived key when the client sends none | Majny 10-18 | Not mentioned | The reference refuses a keyless mutating call (`LAP_ERR_IDEMPOTENCY`). |

**Timing and venue.** Post, shortened, today, once the fixes are in; do not reduce it to a pointer. Reasons: the questions were put on 10-26 and are the stated test for "what needs a shared contract" (arjun2075, 10-26); ndreno had no draft branch on 10-13 and arjun2075 is building the vectors in PR #2 now, so early input is worth more than late; the thread routinely carries disclosed own-project comments (PIC Standard, RIGHTCLICK, Parmana, Cellaflow, Shrimp); a pointer would make him read a 46 KB draft to find five answers. Before posting: fix issue 3 (or add the sentence), re-read #3394 (pavancharak's reply may have drawn a follow-up that changes a question; I could not check), confirm the Actions run for v0.4.14 is green on both mcp legs (the comment says the example runs there; I could only run the 1.x leg), and be ready to answer within a day. The FSIG comment this morning is not a reason to wait: it is a different repository and a direct reply. The reason to keep this one short is that two long project-linked comments in one day read as promotion; the trimmed text mostly states limits. The offer to map onto the matrix is worth making only if you will do it within days: arjun2075 asks contributors for runnable PRs with a README and stated assumptions (10-19).

**Tone and length.** In the 40 comments up to 10-26 the median is 1,256 characters; 22 are between 1,000 and 3,000; one is longer (3,649, Baktiyarsan, two data sections). Draft 1 (3,907) would be the longest in the thread. The trimmed text in section 6 (3,145 raw, 3,035 with the link shown as its text) would be the second longest, which is the price of answering the thread's own cases; an answers-only cut (delete the Authorization paragraph, shorten the limits to one line) is about 2,000 characters but leaves ryjen, madeinplutofabio and arjun2075's 10-11 points unanswered, so I would not. Tone is neutral and scoped; the only slips are the "rather than a proposal" contrast and "ships". The AI-use line matches FSIG-17 and the thread (7 of the 40 comments carry one).

**@-mentions.** Only `@arjun2075`, which is right: he is the addressee. ryjen, madeinplutofabio, Majny and ndreno are named without `@`, so nobody is notified. Keep it that way, and keep pavancharak out of the body (the draft already does).

**Risks.**
- Claims about SDKs or other servers: the "ignores the `_meta` key" and "not an SDK change" sentences (section 3, item 4). The trimmed text says "Python SDK checked only".
- Claims about other commenters' tools: none in the body. README line 159 names Claude Desktop and Cursor as clients that "get `LAP_ERR_AUTH_MISSING`"; that is an untested claim about other products. Do not bring it into the comment.
- Maintainers' intent: none. "a SEP should separate them" was cut from the trimmed text to keep it to facts; add it back only if you want the recommendation on the record.
- The comment will be read next to the FSIG reply and the linked draft. Three places can disagree: the rotated agent key (issue 1), "separate here" against "refused" (issue 3), and "envelope or cap refusal" against "authorization refusal" (section 3, item 3). The trimmed text uses the FSIG wording.
- Standing rules: personal account only (the pane signed in as atharnouman), your explicit OK on the final text, nothing posted by me.

## 6. Trimmed version (ready to paste)

Counts: **3,145 characters raw, 3,035 with the link shown as its text** (the draft URL is 106 of them); draft 1 is 3,907 and 3,727. It answers the five items, keeps the thread's cases, states the limits next to the claims, and uses the FSIG-17 wording where the two overlap. Optional: append the offer, *I can map these onto the matrix in arjun2075/mcp-b1-lost-response-repro#2.* (+75, only if you will do it); if the draft is not corrected first, add the 204-character sentence from issue 3(b) after the Authorization paragraph. To bring the rendered text under 3,000, drop the name attributions "(Majny's case)", "(ryjen's case)", "(madeinplutofabio's day-2 case)" and "; Majny's effect-then-error case" (about -90).

````markdown
@arjun2075 answers to your 26 October questions, from a design I maintain: a draft MCP extension (not submitted anywhere) with a Python reference ([draft at v0.4.14](https://github.com/atharnouman/living-agents-protocol/blob/v0.4.14/output/lip/LIP-4-mcp-extension-draft.md)).

**Key.** The client mints it before the first call, sends it in `params._meta` (not the tool arguments) and keeps it; the server never issues one. The JSON-RPC id plays no part (the example client's retry has a fresh id and is still recognised). Same key and request (tool plus canonical arguments): one execution while the store lives. Same key with other arguments, or another tool on a shared store: refused in every state. A new key is a new operation even for identical bytes, so an intentional repeat (Majny's case) differs from a retry. No key on a mutating call: refused, no server-derived fallback.

**Unmodified client:** no; the application must add the `_meta` object (Python SDK checked only), else the call is refused (`LAP_ERR_AUTH_MISSING`) and does not run. **Discovery** (shown by the example client, not asserted in CI): the tool's `tools/list` `_meta` marks it (action, resource, key required); mcp 2.x also lists it in `capabilities.extensions`; mcp 1.x has no server registry, so there only that `_meta` and the refusal tell the client.

**Stored result or unknown outcome** (same key and request). Completed: the stored result and receipt, marked `replayed: true`. In flight: refused. Unknown (the tool raised unless it said nothing was sent, or its executor died; Majny's effect-then-error case): refused naming reconciliation, never released by time, resolved only against the system of record; the client must not mint a new key. In flight and unknown share one code, differing only in reason text.

**Authorization.** Recognition runs after the signed passport and call signature verify and before the envelope (action, resource, cap), so an envelope or cap refusal on a retry means no execution is recorded under that key. If the authorization presented now no longer covers action, resource or unit, the key is reported as executed and the result withheld (ryjen's case); the amount is not re-compared (my choice: a replay spends nothing). No revocation channel: "now" is the passport on the retry. An expired passport is refused first; a reissued one replays. Another issuer on the same agent key and key is refused unless the server maps both to one tenant; a rotated agent key is a new scope. Retention: the reference never evicts; post-window behaviour is open (madeinplutofabio's day-2 case).

**Evidence and limits.** 18 shared claim-store vectors (`test-vectors/microcore-replay-vectors.json`, Python and Node); Python tests of the order (execution count and disclosure asserted separately); a stdio example in CI on mcp 1.x and 2.x. No dropped response injected; crashes simulated; the store is in-process (a restart loses every claim) and reconciliation is a manual `complete` or `release`. Full order in Python only. Not claimed: exactly-once, durability.

AI use: an AI assistant helped draft this; I reviewed it before posting.
````

## 7. Checked and found correct

Code and tests (all at the tag; pytest 199 passed; Node replay vectors 19 of 19):
- Check order: passport (audience, expiry, issuer, proof class), call signature, recognition, envelope and cap, claim, tool (`mcp_middleware.py:150-252, 263`).
- Client-chosen key covered by the signature; keyless mutating call refused (`LAP_ERR_IDEMPOTENCY`); uncovered key refused (`LAP_ERR_SIG_PARAMS`) (`test_mcp_extension.py:136-148`).
- Same key and request replays the stored result and receipt marked `replayed`; a new key with identical bytes runs again (`test_recognition_order.py:97-110`; RP-12; P2).
- Same key, different request: refused when completed, in flight or unknown, and across tools sharing a store (`test_recognition_order.py:131-149, 198-206`; RP-07 to RP-10).
- In flight is refused; unknown names reconciliation, is not released by time (P3: 30 days later, still refused) and resolves only through `complete` or `release` (RP-14; `test_idempotency_recovery.py`); the held case under a cut passport (`test_recognition_order.py:152-170`).
- Withheld when the presented passport no longer covers action, resource or unit; a cut cap alone does not withhold (RP-01 to RP-06; `test_recognition_order.py:97-128`). Expired passport refused first; a reissued one replays (`:235-244`; P6). A refusal before the claim reserves nothing (`:257-265`). Tenant: another issuer refused, a mapped one replays, an unknown one has no scope (`:173-195`; RP-11).
- 18 vectors (RP-01 to RP-18) loaded by both suites; Node has the cache and `checkInvocation` only, so the full order is Python-only, as the draft says.
- Tutorial: 2 paid (second marked `replayed`, same receipt) and 7 refusals with `LAP_ERR_` codes before the tool runs (my run on mcp 1.29.1; `ci.yml:40-60` for the 1.x and 2.x matrix over stdio). The retry carries a fresh JSON-RPC id (`shared/session.py:256-257`) and is still recognised.
- No dropped response is injected ("in flight" is a cache reservation, "crash" is `mark_indeterminate`); the draft says "simulated" and claims no HTTP or TypeScript coverage.

The thread (API copy and saved file): dates, authors and quotations match (arjun2075 10-26 13:37; ryjen 10-11; arjun2075 10-11 and 10-12; madeinplutofabio's 24-hour record and 7-day approval; Majny's three cases; arjun2075 10-14; PR #2). The saved file has 41 comments. Neither the project nor its author appears in the 40 comments of the API copy. No `@`-mention beyond arjun2075; the AI-use line matches the convention. Consistent with FSIG-17 on: recognition before the envelope, release while action, resource and unit are covered, amount exempt, an envelope or cap refusal meaning no execution recorded, tenant refusal, 18 vectors with the order tested in Python only; the differences are listed under Risks in section 5. Facts header: `mcp_middleware.py` lines 177 to 200 and README lines 134 to 143 are right; published status (PyPI, npm, release) is not checkable offline (the 7e5f3fb log records it as verified).
