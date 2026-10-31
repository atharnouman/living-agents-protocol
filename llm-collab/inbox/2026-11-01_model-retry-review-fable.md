# Review of the model-retry fixture, the spec note and the two draft comments (Fable 5.1, 2026-11-01)

Brief: `llm-collab/inbox/2026-11-01_model-retry-review-brief.md`. Hard limits kept: nothing in the repository was written except this file; scratch work (thread dumps, an mcp 2.3.0 venv, the experiment script `exp.py`) lives in the session scratchpad; nothing was committed, pushed, posted or signed in; GitHub was read through the public unauthenticated API; terminalstate's repository was read only through the thread text (no download). The fixture was imported in place with bytecode writing off (`python -B`), so no `__pycache__` was written to the repository.

One note on the tree: `git status` during the review showed `output/LAP-shipping-runbook.md` modified as well as the three files the brief names. It is not part of the brief; it was neither read nor touched.

## What was verified by running or reading

- `python run.py` on mcp 1.29.1 (the installed SDK): exit 0, "all outcomes as asserted". Every cell of the README's two tables and of the comment's six-row table matches the printed output.
- The same on mcp 2.3.0, in a scratch venv with `living_agents` imported from `lap-python/` source: exit 0, output identical to the 1.29.1 run except the version line. So "1.x and 2.x" and "identical output" hold. The CI step sits in the `mcp-example` job whose matrix is `mcp>=1.2,<2` and `mcp>=2,<3`, so "on both majors in CI" holds once pushed.
- Breaking the middleware changes the output. With `IdempotencyCache.lookup` patched to always return `absent` and `claim` to always reserve, 10 of the 24 Part 1 cells changed (the "key from arguments" and "resolves first" columns went to 2 and 3) and Part 2 case 1 failed ("DIFFERENT", 2 bookings). The numbers come from the claim store and the middleware, not from the harness.
- The timeout selection is not load-bearing. "Response lost, model repeats" with new-key-per-call gives 2 refunds, 5 of 5 runs, at client timeouts of 0.1, 0.01, 0.001, 0.0001 and 0.00001 s: the request is already through the memory stream and the synchronous tool has run before the SDK's cancellation can act. A slow machine cannot turn a committed effect into a non-effect here, and the 30 s timeout on fault-free calls cannot produce a false "lost".
- The module-level `CURRENT` is not an artifact: `faults` is replaced on every `connected()`, the passport is replaced only inside the expiry case and restored afterwards, and the cases run one after another.
- The relay classifies correctly for what the fixture exercises: only `tools/call` on the three mutating tools is dropped, the read tool is never dropped, and a server response is dropped only when its id was watched. An unknown tool on mcp 1.x returns an `isError` result ("Unknown tool"), not an `SdkError`, so in this fixture only the SDK's timeout reaches the `lost` branch.
- `sign_jws` is deterministic (fixed header, JCS payload, Ed25519), so `mint_passport()` twice gives the same string (finding 5).
- Both dangers in findings 1 and 2 were reproduced against the unmodified fixture code (counts below).
- The threads were read in full: 3394 (45 comments, through yaredmengistu04-arch 2026-10-31; Ben-Home's comment 9 in its edited form of 2026-10-31), FSIG #17 (20 comments, through PederHP 2026-10-30), FSIG #19 (4 comments), and the 29 October call notes.

Everything marked "judgement" below is mine and not a result of a run.

## Findings, most important first

### 1. "Client resolves first" treats `LAP_ERR_REPLAY_WITHHELD` as a refusal, drops the hold, and runs the operation again once authority is restored. This is the case the draft's own section 5.6 forbids.

Files and text:
- `examples/model-retry/run.py` line 168: `AFTER_RECOGNITION = ("LAP_ERR_ACT", "LAP_ERR_RES", "LAP_ERR_CAP", "LAP_ERR_KEY_REUSE", "LAP_ERR_REPLAY_WITHHELD")`, lines 189-190 (`return Answer("refused", text)`), line 196 `DEFINITE = ("done", "replayed", "refused")`, line 301 `if first.kind in ("done", "replayed"):`.
- `examples/model-retry/README.md` line 34: "It tells the model the outcome is unknown only when it cannot find out. A refusal from before recognition, such as an expired passport, does not count as definite."
- `output/lip/LIP-4-mcp-extension-draft.md` section 7, new bullet: "and send nothing new on that tool until it has a definite answer; a refusal at step 1, 2 or 3 of section 4.1 is not definite."
- `outreach/MCP-3394-comment-recut-2026-11-01.md` line 20 and `outreach/FSIG-17-reply-2026-11-01.md` line 7 state the same rule.

Verified by running (scratch experiment D): "client resolves first", response lost twice (held, model told "unknown"); the passport replaced by one whose `res` no longer covers the billing tool; the model calls again. The re-presented key gets `LAP_ERR_REPLAY_WITHHELD: this key executed earlier; its result is withheld under the current envelope (LAP_ERR_RES)`. `present` classes it `refused`, `DEFINITE` contains `refused`, so the hold is deleted and the model sees a refusal. The scripted model repeats: a new key, refused by the envelope. The original passport is restored; the model repeats: a new key, executed. Two refunds. Answer kinds in order: `unknown, refused, refused, done`; `held` empty at the end.

Why it is wrong: section 5.6 says of this refusal "The client **MUST NOT** read that refusal as "not executed" and mint a new key." The wiring does exactly that, through the model. It also contradicts README line 34: the client *did* find out (the key executed) and told the model something else. The classification list does not match sections 4.1 and 4.3 either: `LAP_ERR_REPLAY_WITHHELD` (step 4) is definite in the *executed* direction, not a refusal; `LAP_ERR_KEY_REUSE` (steps 4 and 7) says a claim exists under the key for another request and nothing about its state, so it is not definite (unreachable by `ResolveFirst` as written, which re-presents the same bytes, but wrong as a stated rule); and the spec note's "a refusal at step 1, 2 or 3 ... is not definite" leaves the step 4 and 7 refusals (`LAP_ERR_REPLAY`, `LAP_ERR_ISSUER` tenant mismatch, `LAP_ERR_IDEMPOTENCY`, `LAP_ERR_SIG_PARAMS`, `LAP_ERR_KEY_REUSE`) implicitly definite, when the fixture's own code treats `LAP_ERR_REPLAY` as unresolved. This is the authority-change case ryjen, arjun2075 (10-11), madeinplutofabio and King Yew (10-27) are all watching; a table column that quietly gets it wrong is the worst thing to post into either thread.

Replacement, `run.py`:
```python
# Recognition runs after the passport and signature checks (draft 4.1 step 4). Only LAP_ERR_ACT, LAP_ERR_RES and
# LAP_ERR_CAP say that nothing ran under the key (draft 5.6); LAP_ERR_REPLAY_WITHHELD says that it ran. Every other
# refusal, LAP_ERR_REPLAY included, says nothing about the held call.
AFTER_RECOGNITION = ("LAP_ERR_ACT", "LAP_ERR_RES", "LAP_ERR_CAP")
```
in `present`, before the `AFTER_RECOGNITION` test:
```python
        if "LAP_ERR_REPLAY_WITHHELD:" in text:
            return Answer("withheld", text)  # it executed; the result is withheld under the current authority
```
`DEFINITE = ("done", "replayed", "refused", "withheld")`; in `model_repeats`, `if first.kind in ("done", "replayed", "withheld"):`; and a ninth case row that is experiment D, expected `(2, 1, 1)`: "lost twice, authority narrowed, re-presented, then restored". Add the kind to the `Answer` docstring.

Replacement, README line 34, after "does not count as definite": "A result withheld under replaced authority (`LAP_ERR_REPLAY_WITHHELD`) is definite the other way: the call ran, and the model is told that, not given a refusal to call again."

Replacement, draft section 7 bullet, for "and send nothing new on that tool until it has a definite answer; a refusal at step 1, 2 or 3 of section 4.1 is not definite": "and send nothing new on that tool, and nothing concurrent with it, until it has a definite answer. Definite are a result, replayed or not; `LAP_ERR_ACT`, `LAP_ERR_RES` and `LAP_ERR_CAP`, which say that nothing ran under the key (section 5.6); and `LAP_ERR_REPLAY_WITHHELD`, which says that it ran and which the client reports as an execution, never as a refusal to call again (section 5.6). Every other refusal, `LAP_ERR_REPLAY` included, says nothing about the held call."

The two comments' sentences can stay once the fixture is fixed; the 3394 table's "client resolves first" column should not be posted before it is.

### 2. Two concurrent calls on one tool overwrite the hold; the first lost call is forgotten and runs again, and the model is told another call's outcome as its own.

Files and text: `run.py` line 230 `self.held = {}` and line 246 `self.held[tool] = (args, key)` (no in-flight guard); `README.md` line 63 "One held call per tool."; draft section 7 bullet "send nothing new on that tool until it has a definite answer"; the same rule in both comments.

Verified by running (scratch experiment E): "client resolves first", two refunds for different captures (CAP-1, CAP-2) issued concurrently on `create_refund` in a task group, every answer lost (`drop_responses=4`). Both calls return `unknown`; `held` holds only CAP-2 (it overwrote CAP-1). The model repeats CAP-1: the wiring re-presents the *CAP-2* call, which replays, and answers `earlier_done` with CAP-2's text as "your earlier call". The model repeats CAP-1 again: not held, new key, executed. Three refunds: CAP-1 twice.

Why it is wrong: the rule as stated in a security section is for real clients, and agent frameworks issue parallel tool calls. "One held call per tool" reads as a capacity limit, not as "a second concurrent call silently replaces the hold". The same hole affects the `earlier_done` message, which can report the wrong call. Judgement: the fix is small and should go in before either comment describes the rule.

Replacement, `run.py` `ResolveFirst`: add `self.locks = {}` in `__init__` and wrap the body of `call` in `async with self.locks.setdefault(tool, anyio.Lock()):` so that one call is in flight per tool; comment: `# one call in flight per tool: a concurrent second call would overwrite the hold`. Replacement, README line 63: "One held call per tool, and one call in flight per tool: the client serialises calls on a tool, since a concurrent second call would replace the hold and the first lost call would be forgotten, then run again on the model's retry." Replacement in the draft bullet: the words "and nothing concurrent with it" (already in finding 1's text). In both comments, "sends nothing new on that tool" becomes "sends nothing new or concurrent on that tool".

### 3. "Peder's point holds on my side" understates it, and "rather than the key's place" claims a comparison the fixture did not make.

File and text: `outreach/FSIG-17-reply-2026-11-01.md` line 7: "Peder's point holds on my side: only a client that implements the extension gets anything from it. Given that client change, what held was a client rule rather than the key's place:".

Verified by reading: Peder's comment (FSIG #17, 2026-10-30) says `_meta` "can be fine ... if they are app-directed and not model directed", that such data "become locked to the system that recognizes them" so "uptake becomes predicated on wider adoption, which is a very difficult bar to clear", and that arguments or the return schema "just works". The binding does not merely give an unmodified client nothing: `lap_tool` refuses the call before the tool runs (`LAP_ERR_AUTH_MISSING`, `mcp_extension.py` line 252; README line 38 says so). The fixture varied the client wiring, never the key's place; the argument form is untested, as the next sentence admits. So "rather than the key's place" is not shown.

Replacement for the two sentences: "The key is app-directed, which is Peder's condition for `_meta`, and Peder's downside holds on my side, harder: a client without the extension is refused before the tool runs, so the tool is unusable until clients adopt it. With a client that has it, the count was decided by a client rule, not by the key: keep a call whose answer said nothing definite, re-present it with its key, and send nothing new or concurrent on that tool until the answer is definite. I did not test the argument form; there the same rule falls to whoever holds the arguments across attempts, the client or the model."

### 4. The four booking cases are attributed to nobody, two were run in a different shape from the one suggested, and "run directly against the claim store" is not what the code does.

Files and text: `examples/model-retry/README.md` line 44: "These are the four synthetic cases suggested on FSIG issue 17, run directly against the claim store with a client that keeps its key."; `run.py` line 12 "Part 2 runs the four booking cases proposed on FSIG issue 17."; `outreach/FSIG-17-reply-2026-11-01.md` line 9: "I ran the four suggested cases against my own reference (same link). Cases 1, 3 and 4 gave no duplicate."

Verified by reading: the four cases were suggested by VibeMirror-coder ("Jamenbin AUCS, operated for HumanMirror", a disclosed AI agent account) on 2026-10-30, and King Yew then pointed Sid at them as a first piece *against King Yew's draft once it is up*. Jamenbin's case 1 is "booking committed, response lost, lookup finds the same reference"; the fixture's case 1 needs no lookup and its 1b (executor death) is the one with a lookup. Jamenbin's case 4 is "cancellation request times out, so the operation stays indeterminate"; the fixture runs it as an executor death after the effect (`run.py` line 487 `faults.die_after_effect = 1`), because in this binding a plain timeout leaves a completed claim that replays. Jamenbin's per-case assertion "no release of held spend before authoritative reconciliation" is not asserted (held spend is stated as not covered). Every Part 2 call goes through `present(session, ...)`, the SDK session and the middleware; only the operator's reconciliation (`cache.complete`, `cache.release`) acts directly on the store.

Replacement, README line 44: "These are the four synthetic cases Jamenbin (VibeMirror-coder) suggested on FSIG issue 17 on 30 October, as 1, 2, 3 and 4, with 1b and 2b added, run over the same session with a client that keeps its key; the operator's reconciliation acts directly on the claim store. Case 4 is run as an executor death after the effect, since a timeout in this binding leaves a completed claim that replays; the suggestion's held-spend assertion is not covered." Replacement, `run.py` line 12: "Part 2 runs the four booking cases suggested on FSIG issue 17 (30 October), two of them reshaped; see the README." Replacement, FSIG reply line 9, first two sentences: "I ran the four cases Jamenbin suggested on 30 October against my own reference, with two changes of shape: in this binding a timeout leaves a completed claim that replays, so the unknown-outcome cases (1 with a lookup, and 4) are run as an executor death after the effect, and the held-spend assertion is not covered. Cases 1, 3 and 4 gave no duplicate."

### 5. The "renewed" passport is the first passport again, byte for byte.

File and text: `run.py` line 319 `CURRENT["passport"] = mint_passport()` under the docstring "the passport expires before the model repeats, and is renewed before it repeats again"; README row "Lost twice, passport expires, then renewed".

Verified by running: `mint_passport() == CURRENT["passport"]` is `True` (deterministic JWS over an identical payload). The row therefore re-presents the original passport, not a reissued one. The row's claim is nevertheless true: with `mint_passport(iat=NOW + 1, exp=NOW + 601)` (different bytes) both "key from arguments" and "resolves first" still give 1 refund, last answer `replayed`, because the claim is not keyed by the passport. The code just does not exercise what the row says.

Replacement, `run.py` line 319: `CURRENT["passport"] = mint_passport(iat=NOW + 1, exp=NOW + 601)  # new bytes: a reissued passport, not the first one again`.

### 6. The 3394 comment repeats five points the thread already has; what it adds is not named; the link is not pinned.

File and text: `outreach/MCP-3394-comment-recut-2026-11-01.md`, the table row "Two refunds wanted, no fault", the paragraph "**When a lookup is authoritative.**", the sentence "The first thing the model would see after a lost answer is the client's own timeout, so a server cannot label that moment. Only the client can.", the words "gave two bookings" (line 24), and line 26 "https://github.com/atharnouman/living-agents-protocol/tree/main/examples/model-retry".

Verified by reading the thread: the model as the retrying party is Baktiyarsan's (10-14, 900 episodes) and terminalstate's (10-29); an argument-derived key collapsing an intentional repeat is Majny's and arjun2075's (10-18, "it cannot generally distinguish a retry from an intentional repeat with identical arguments"); the first timeout being visible only to the client is Ben-Home's ("the application has to choose a policy with no information") and theblueskies's dispatch boundary; the negative read that proves nothing is terminalstate's, ryjen's row C, arjun2075's X02 and Srivatsa03's; a single-flight hold is Ben-Home's and jay18coder's description. What the thread lacks and the fixture gives: the same scripted retry run through three client wirings side by side with a ledger oracle, and the limit that a held call which never arrived runs when re-presented. "Two bookings" arrives without the booking tool having been introduced. The header requires the link pinned to a commit; the text has `tree/main`.

Replacement: cut the "Two refunds wanted" row (settled by arjun2075 on 10-18 and by PetrefiedThunder); cut the "When a lookup is authoritative" paragraph to one sentence: "A second tool in the fixture, a booking, gave the negative-read trap: a negative read, an operator's release of the claim, then the first effect landing late made two bookings, since the reference has no horizon." Open the "**Stable identity.**" paragraph with what is new: "What the fixture adds is the same scripted retry through three client wirings against one ledger." Replace `tree/main` with `tree/<commit>` at posting. Keep the "Unresolved outcome" paragraph but credit the point in four words: "as Ben-Home said, the first thing the model sees is the client's own timeout". Judgement: with these cuts the comment is about 230 words plus a five-row table, which is the right size for a 45-comment thread where the author is new.

### 7. The FSIG reply leads with the author's project twice, which is what Peder asked the group not to do, and its offer to Sid cuts across King Yew's plan.

File and text: `outreach/FSIG-17-reply-2026-11-01.md` line 7 "I ran the lost-response case ... ([results](...))" and line 9 "against my own reference (same link)" and "If it helps before a reviewer is agreed, I can run your shapes on this fixture and report back."

Verified by reading: the 29 October call notes record "PederHP mentioned that getting traction on audit trails and idempotency is best done by describing the desired additions to the protocol / shape of the extension instead of focusing on external projects"; on #19 Peder wrote "I greatly appreciate that the document doesn't mention a specific project". King Yew (10-30) told Sid the first piece is to check the four cases against King Yew's draft once it is up, and that who reviews is still to be agreed. The reply's one protocol-shaped sentence, "the draft may need to say who keeps the key across attempts, wherever it travels", is the part King Yew can use; it comes last.

Replacement, judgement: lead the King Yew paragraph with the shape point and keep one link in parentheses: "@kingyewchoo for your draft, on `_meta` or argument: two things the draft may need to say whichever it picks. Who keeps the key across attempts, since after a lost answer the party that calls again is often the model, which never sees a `_meta` key and may not copy an argument one. And who labels the unknown outcome at the first attempt, since the first thing the model sees is the client's own timeout, which the server cannot label; the server can label only the retry. I ran the lost-response case with a signed key in `_meta` and a scripted model that always repeats (fixture at <pinned link>): [finding 3's sentences]." For Sid: keep the results in two sentences, tie the limit to Sid's own step 2 ("your fixed listening window is what this reference lacks: released on a negative read with no horizon, a late commit made two bookings"), and replace the last sentence with "Once King Yew's draft is up, the fixture can check the four cases against its semantics too, if that helps." Delete the offer to run Sid's shapes unless Athar will do that work; it also positions the author as the implementer Sid asked for before the group has agreed one.

### 8. "The fault below the SDK" overstates where the relay sits.

Files and text: `README.md` (repository root) table row: "over a real MCP session with the fault below the SDK"; `.github/workflows/ci.yml` step name "fault below the SDK session"; the 3394 comment line 7 "fault injected below the client session".

Verified by reading `run.py` lines 134-150: the relay is two tasks on anyio memory streams between the SDK's `ClientSession` and the SDK's low-level server `run`. There is no transport. That is the same class of fault as arjun2075's hook (jarrettdustinqq: "The relay drops only the response matching the first recorded tools/call ID"), not the transport-level drop Ben-Home asked for in the comment edited on 10-31 ("a TCP reset after the handler completed"). "Below the client session" is literally true; "below the SDK" is not, since the SDK's transports are not involved.

Replacement, root README: "over a real MCP session, the fault injected between the two SDK sessions where a transport would sit". CI step name: "fault between the SDK sessions". 3394 comment: "fault injected between the two sessions, where a transport would sit, not at a transport".

## Areas where nothing else was found

- **A, harness honesty.** Beyond findings 1, 2 and 5, the numbers are real: the relay, the timeout selection, `CURRENT`, the scripted model and the `present` classification were each checked (see the verification list). Weakest remaining sentence: `run.py` line 183's comment "the SDK's request timeout: nothing says whether the tool ran", because `SdkError` would also cover a JSON-RPC error that says the request never reached a tool; on mcp 1.x an unknown tool comes back as an `isError` result, so in this fixture only the timeout reaches that branch, but a wiring that copies the pattern should test the error code.
- **B, fairness of a security bullet.** Judgement: the subject belongs in section 7, since whether the binding's duplicate protection works at all depends on it, and section 7 already carries client-facing rules (concurrency and recovery). The bullet as written is a tour of three wirings, which is README material; with finding 1's text it becomes a rule with two limits, which is what a security section should hold.
- **C, claims otherwise true.** Checked and holding: the shape attributed to terminalstate (comment 44: "one effect committed, its response replaced by a transport error, then a read that is correct for what it was asked but whose scope cannot contain the effect"; the fixture's `list_transactions` filtered by the capture id cannot return the refund row, as PayPal's cannot); arjun2075's three requirements (comment 43); "shares a code with an in-flight claim" (`LAP_ERR_REPLAY` for both, `mcp_middleware.py` lines 184 and 188); "no status-only probe" and the stale-call limit; "the reference has no horizon" and that releasing is an operator's act (`release()` only after `mark_indeterminate`); "none of that repository's code is used" (`run.py` imports only the SDK, anyio, cryptography and `living_agents`); the eight Part 1 rows and six Part 2 rows; open question 9's dates (arjun2075 10-29 in 3394; Peder and King Yew 10-30 in #17). Weakest remaining sentence: fixture README line 9, "terminalstate's runs measure that": they measured 70 of 600 trials under two prompts against recorded toolkit answers and local fakes, which is a rate under those conditions rather than a measure of how often a model retries.
- **The 10-28 text it replaces.** The recut rightly drops the answers to arjun2075's 10-26 questions (pavancharak answered for Parmana on 10-28 and the thread moved to terminalstate's data). Nothing from the earlier text is needed back.

## Verdicts

### D. Each comment

**FSIG #17 reply: post with named changes.** The changes: findings 3, 4 and 7, the pinned link, and the fixture fixes of findings 1 and 2 pushed first (the rule the reply states in words must be the rule the linked code runs). It adds what the thread lacks: a point King Yew can write into the draft (who keeps the key across attempts; who labels the first timeout), with a run behind it, before 12 November. It should not repeat Peder; it should agree with Peder's condition and say where Peder's downside bites harder. Length after the cuts: about 200 words. It is the better single venue if only one comment is posted, because King Yew is drafting now and asked exactly "`_meta` or as an argument", Sid asked for a first piece, the author is already a participant there, and the group was told on 29 October to describe the shape of the extension rather than external projects, which the revised text does.

**3394 recut: post with named changes, and not before the FSIG reply or the fixture fixes.** The changes: findings 1, 2 and 6, the pinned link, finding 8's wording. If Athar will not fix finding 1, do not post: the "client resolves first" column would advertise a rule that mints a new key after a withheld replay, in the thread where ryjen, arjun2075, madeinplutofabio and King Yew defined that case. It should not answer yaredmengistu04-arch: their split (duplicate suppression versus preserved authorization) is ryjen's and arjun2075's of 10-11, the thread already treats the two separately, and the author's own client side gets that case wrong until finding 1 is fixed. Judgement on what it adds: modest but real (the side-by-side wirings and the never-arrived-call limit); arjun2075 welcomes fixtures, and the thread tolerates project links with disclosure. Judgement on a better venue for the *fixture*: arjun2075 has asked every contributor for runnable cases in `arjun2075/mcp-b1-lost-response-repro` PR #2; a comment that neither offers that nor says it will not is one more data point. Say which in one line, and offer the case only if Athar will do the work.

### E. Order and timing

1. Fix findings 1, 2 and 5 in the fixture (small edits), rerun on both majors, pin the links, push on Athar's "publish".
2. Post the FSIG #17 reply first, within the next few days, so King Yew can use it before the 12 November draft. The thread has been quiet since Peder's comment of 30 October, so there is nothing to wait for.
3. Post the 3394 comment no sooner than a week after the FSIG reply, and preferably once King Yew's draft is up, so that the comment can point to a group draft and not only to the author's repository; the earlier reviewers' warning about two same-day comments in two MCP repositories stands, and the last comment on 3394 is a product mention that a second project-linked comment should not follow directly. Posting after arjun2075's next substantive move (the mapping of terminalstate's case into the matrix) is the natural moment.
4. If only one: the FSIG reply.

## Second pass (2026-11-01, after local commits 5726c34 and 3d60c13)

Scope as set by the coordinator: whether findings 1, 2, 4, 5 and 8 are fixed; whether the new `ResolveFirst` introduces a wrong outcome; whether the two final texts carry a factual error. Venue, tone and order not re-reviewed. Hard limits kept: nothing in the repository written except this file (`git status` after the pass shows only the pre-existing runbook modification and the untracked inbox files); the fixture was run and imported in place with `python -B`, so no `__pycache__` appeared in `examples/model-retry/`; probes (`exp2.py`, `exp3.py`, `exp4.py`) live in the scratchpad; the independent report `..._review-sonnet.md` was not read.

What was run: `git show` of both commits; `python -B run.py` on mcp 1.29.1 (exit 0) and, from the scratch venv with `living_agents` imported from source, on mcp 2.3.0 (exit 0). Both outputs are byte-identical to the committed `output-mcp-1.29.1.txt` and `output-mcp-2.3.0.txt`, and differ from each other only in the version line. Every cell quoted in the README and in the two texts was checked against those outputs.

### 1. Are findings 1, 2, 4, 5 and 8 fixed?

- **Finding 1 (withheld replay classed as a refusal; the classification list; "step 1, 2 or 3"): yes.** `present` returns `withheld` for `LAP_ERR_REPLAY_WITHHELD` (run.py 208-209); `ResolveFirst` keeps the record and returns it as an execution (268-269); the scripted model stops on it (`SETTLED`, 320); the row "response lost, authority narrowed, then restored" is asserted (432-433) and gives `1 replayed` for that wiring, where the first-pass probe gave two refunds. `LAP_ERR_REPLAY_WITHHELD` is out of the refusal list (183). README line 47 and the draft's section 7 bullet state the rule; section 6 carries the "steps 1 to 3" clause instead. Keeping `LAP_ERR_KEY_REUSE` in the list is defensible: a refusal received for a call's first presentation means that presentation did not run. Nothing left.
- **Finding 2 (concurrent calls overwrite the hold): yes.** One `anyio.Lock` per tool (250, 253); the row "two different refunds in flight, answers lost" asserts `2 done` for that wiring with `ledger.wrong` checking that the two refunds are CAP-1 and CAP-2 (379, 436-437); README lines 42 and 55; the draft bullet says "handles one call at a time per tool". Nothing left.
- **Finding 4 (the four cases: attribution, shape, "run directly against the claim store"): yes.** VibeMirror-coder and the date are named (run.py 11-12; README 64); case 4 now runs in the suggested shape (a timeout, which replays) with the executor death as 4b, and README line 77 says why; case 1 now includes the lookup; "All run through the middleware over the same session ... The operator's lookup, completion and release act directly on the system of record and the claim store" (README 64); the suggestion's held-spend assertion is stated as not run (83). Nothing left.
- **Finding 5 (the "renewed" passport was the first one again): yes.** `reissued()` mints `iat=NOW + 1, exp=NOW + 601` with the comment "new bytes" (86-87); the row is renamed "then reissued". Nothing left.
- **Finding 8 ("below the SDK"): yes.** Root README, the CI step name, run.py lines 7 and 94, fixture README line 5 ("It is not a transport-level fault") and the 3394 text all say between the two sessions, where a transport would sit. Nothing left.

### 2. Does the new `ResolveFirst` introduce a wrong outcome?

Three new behaviours were checked.

- **Refusals end a call only on its first presentation.** Probe: request lost twice (never reached the server), then the cap cut, then the model repeats. Answers `unknown, unknown, unknown`, no refund, the record kept. No duplicate and no false "executed"; a false "unknown" in the safe direction, since the lost attempts could have run. Correct for that case. But the rule is coarser than the evidence it rests on, and that produces a wrong outcome of its own (finding 2 below).
- **The attempt is counted before the send.** The row "client killed mid-call, restarts, record kept" passes (`1 replayed`). A crash in the window between the count and the send leaves a record that re-presents into an absent claim and runs once; a cap cut in that window gives `unknown` (conservative). No wrong outcome.
- **The record is kept after `LAP_ERR_REPLAY_WITHHELD`.** Correct for the same call. Wrong for a different call on that tool (finding 1 below).

### Findings

**1. After a withheld replay, a call for something else on that tool is reported as "withheld", that is, as executed, though it was never sent.**

File and text: `examples/model-retry/run.py` lines 268-269:
```python
            if answer.kind == "withheld":
                return answer  # reported as an execution, never as a refusal to call again
```
Verified by running (probe `exp2.py`, part 1): response lost with the authority narrowed on the loss; the model's CAP-1 call ends `withheld` and the record stays; the model then asks for a CAP-2 refund; the wiring re-presents CAP-1 and returns its `withheld` answer, text "this key executed earlier; its result is withheld", as the answer to the CAP-2 request, with no "this call was not sent". Under restored authority the next CAP-2 call gets `earlier_done` (the correct form of that message), and only the one after that sends CAP-2. Counts are right (CAP-1 once, CAP-2 once); the report to the model is false once: a model that believes it would never place CAP-2, or would place it under a new intent later. The `done`/`replayed` path two lines below handles the same situation correctly, so this is an ordering slip in the new code.

Replacement, run.py 268-269:
```python
            if answer.kind == "withheld":  # reported as an execution, never as a refusal to call again
                if held_args == args:
                    return answer
                return Answer("earlier_withheld", "your earlier call executed; its result is withheld under the current "
                                                  "authority; this call was not sent: " + answer.text)
```
add `earlier_withheld` to the kinds in the `Answer` comment (188), and add the case, whose cells were computed with the fix applied in a scratch subclass (`exp3.py`): the committed class fails its `wrong` check, the fixed one passes:
```python
async def authority_narrowed_then_other(app, world):
    world.faults.on_lost = lambda: CURRENT.update(passport=mint_passport(envelope=NARROWED))
    await app.call(TOOL, ARGS)
    other = await app.call(TOOL, OTHER)
    world.ledger.wrong = other.kind == "withheld"  # a call that was not sent must not be reported as executed
    CURRENT["passport"] = reissued()
    await app.call(TOOL, OTHER)
    return await app.call(TOOL, OTHER)
```
row: `("response lost, authority narrowed, model asks for another refund", 2, dict(drop_responses=1), authority_narrowed_then_other, ("3 done", "2 replayed", "2 done")),` README table row: `| Response lost, authority narrowed, model asks for another refund | 2 | 3* | 2 | 2 |`; README line 47, add: "A call for something else on that tool while the record stays is told that it was not sent." Regenerate both output files. No change to either public text, which do not describe this case.

**2. "A refusal ends a call only on its first presentation" says "unknown" when every attempt was itself refused, which README line 42 promises it never does.**

Files and text: run.py 181-183 (`ENDS_A_FIRST_CALL` and its comment), 243 ("A refusal ends a call only on its first presentation"), 262 (`record[2] == 1`); README line 48 ("end a call only on its first presentation. After an earlier attempt they show only that the server holds no claim now"); draft section 7 bullet ("or, on a call's first presentation only, ... On a re-presentation a refusal at step 5 or 6 shows only that no claim is held now"). README line 42: "It tells the model the outcome is unknown only when it cannot find out."

Verified by running (probe `exp4.py`): passport expired, so both presentations of a fresh call get `LAP_ERR_EXPIRED`; then a valid passport with the cap cut; the third presentation gets `LAP_ERR_CAP`. Answers `unknown, unknown, unknown`; no refund; the record kept with four attempts; the tool held until a person. Yet each refusal received proves that attempt did not run (draft section 6: "every code means the tool did not execute for this request"), so the client could find out, and the truthful answer is "did not run; refused now". Judgement: the uncertainty the rule guards against comes only from attempts with no received answer (lost, tool error, crash), so the rule should key on those, not on the presentation count; the count-before-send already records a crash.

Replacement, run.py: the record becomes `[args, key, attempts, answered]`:
```python
                record = self.held[tool] = [args, uuid.uuid4().hex, 0, 0]  # args, key, attempts, attempts answered
```
in the loop, after `answer = await present(...)`:
```python
                if answer.kind in ("refused", "says_nothing", "unresolved"):
                    record[3] += 1  # a refusal received: this attempt did not run (draft, section 6)
                if answer.kind in ("done", "replayed", "withheld") or (answer.kind == "refused" and record[3] == record[2]):
                    break
```
rename `ENDS_A_FIRST_CALL` to `ENDS_AN_ANSWERED_CALL` with the comment: "These end a call only while every attempt of it was answered with a refusal, since a refusal received means that attempt did not run (draft, section 6). After an attempt whose answer was lost, that ended in a tool error or that a crash cut off, they show only that the server holds no claim now, which proves nothing after a restart of an in-process store or past a retention window (draft 5.6, 7)." Docstring line 243: "A refusal ends a call only while every attempt of it was answered with one." Existing rows keep their cells ("response lost, server restarts, cap cut" stays `1 unknown`, since its first answer was lost); add a row for the probe: `("passport expired twice, then cap cut", 1, dict(), expired_then_cut, ("1 refused", "1 refused", "1 refused"))` with `expired_then_cut` as in the probe, wanted 0 refunds if the harness allows a zero, else keep it in `stale_call_limit`'s style.
README line 48: "**`LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP` or `LAP_ERR_KEY_REUSE`** end a call only while every attempt of it was answered with a refusal, since a refusal received means that attempt did not run (draft, section 6). After an attempt whose answer was lost, that ended in a tool error or that a crash cut off, they show only that the server holds no claim now, which proves nothing after a restart of an in-process store. Then the record stays and the model is told the outcome is unknown ("Response lost, server restarts, cap cut")."
Draft bullet, for "or, on a call's first presentation only, `LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP` or `LAP_ERR_KEY_REUSE`. Any other answer is not definite. On a re-presentation a refusal at step 5 or 6 shows only that no claim is held now, which proves nothing after a restart of an in-process store or past the retention window (section 9, question 8).": "or `LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP` or `LAP_ERR_KEY_REUSE` while every attempt of the call was answered with a refusal, since a refusal received means that attempt did not run (section 6). Any other answer is not definite. After an attempt whose answer was lost, that ended in a tool error or that a crash cut off, a refusal at step 5 or 6 shows only that no claim is held now, which proves nothing after a restart of an in-process store or past the retention window (section 9, question 8)." Neither public text states the first-presentation rule, so no text change.

**3. The FSIG reply misdescribes Baktiyarsan's experiment.**

File and text: `outreach/FSIG-17-reply-2026-11-01.md` line 11: "I did not vary where the key travels; Baktiyarsan tried the argument form with a prompt sentence on [spec issue 3394](...) (14 October, contributor-reported)."

Verified by reading Baktiyarsan's comment of 14 October: the runs were "with and without (a) an idempotency key in the tool schema and (b) one system-prompt sentence asking the agent to report "unknown" unless the result was confirmed", so the key in the schema and the prompt sentence were varied separately, and the prompt sentence was about reporting an unknown outcome, not about copying the key; "with a prompt sentence" reads as a prompt to copy it. "Contributor-reported" is the label arjun2075 attached to Baktiyarsan's registry figures (18 October) and to silentxtrader's result, not to the agent runs, of which Baktiyarsan said "The code is not public yet". Baktiyarsan would correct the first point.

Replacement: "I did not vary where the key travels. Baktiyarsan tried a key in the tool schema, with models driving the retry, on [spec issue 3394](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3394) (14 October), with and without a separate prompt sentence on reporting an unknown outcome; that code is not yet public."

**4. "Which no server can label" overreaches, and the Ben-Home credit puts the author's inference in Ben-Home's mouth.**

Files and text: FSIG reply line 9: "And who labels an unknown outcome, since the first thing the model sees is the client's own timeout, which no server can label."; 3394 recut line 11: "as Ben-Home said, after a lost answer the first signal is the client's own timeout, so only the client can mark it unresolved."

Verified by reading: Ben-Home (comment 9, edited 31 October) wrote that "The timeout is not observable as a timeout" and that the application "has to choose a policy with no information to distinguish" a committed-and-lost effect from one that never ran; Ben-Home did not say that the timeout is the first signal nor that only the client can mark it, and Ben-Home's own conclusion was a protocol-reachable idempotency surface and spec text on what a client should do with the timeout. "No server can label" states an impossibility: a server that answers a mutating call with an accepted-but-pending result (the Tasks pattern the draft's own open question 5 names) labels the moment before any timeout; King Yew, whose draft carries "an outcome-unknown result", could read the sentence as denying that such a result can exist. What is true is the order of arrival: after a lost answer nothing from the server reaches the model before the client's timeout, so a server can label only an answer that arrives.

Replacement, FSIG line 9: "And who labels an unknown outcome at the first attempt, since after a lost answer the first thing the model sees is the client's own timeout, before anything from the server arrives; a server can label only an answer that does arrive, on the retry or as an accepted-but-pending result."
Replacement, 3394 line 11: "On the second requirement: as Ben-Home said, the timeout tells the client nothing; it is also the first signal the model sees, so only the client can mark that moment unresolved, and a server can label only an answer that arrives."

### Checked and holding

Against Sid's comment of 26 October: "which yours rejects" (Sid: "Even if the same request were resent by mistake, the booking system rejects it, because each booking reference is unique"; case 2c models it); "Your fixed listening window is what my reference lacks" (Sid's step 2: "waits a fixed listening window for a late reply, then searches the booking system by its own booking reference"; the reference has no horizon and `release` is an operator's act at any time); "at the old price in your case" and "your never-retry, look-up-by-reference practice" (Sid's steps 1 and 2). Against the output: "gave no duplicate" for the four suggested cases (lines 27, 29, 32 and 33 of both output files: one booking or one cancel each; the suggestion's held-spend assertion is stated as not covered two sentences later); "Case 4 stays unresolved here only if the executor dies; a plain timeout replays" (lines 33-34); "In case 2 the claim stayed refused until released" (29); "two bookings, but only in a fake that accepts a repeated reference" (30-31); "A new key per model call ran the refund twice", "swallowed an intended repeat", "ran it once, with the limits listed there" (rows 1 and 9; the limits, record lost and key rotated, are listed in the README); the 3394 figures "2; 1 ...; 1" (row 1); "a record that survives a restart, one call at a time per tool and the same agent key" (rows 10-15); "runs a call that never arrived even if the model has since changed its mind" (the limit line); "the first answer in my reference is a plain tool error, and only the retry names reconciliation" (row 5; `mcp_middleware.py` line 188). Against the threads: "your first and second requirements" (arjun2075, 29 October); "what you and terminalstate ask for" (terminalstate, 29 October: "a result that says 'outcome unknown' distinctly from a failure"); "Peder's point holds for my extension, harder: a client without it cannot call these tools at all" (`LAP_ERR_AUTH_MISSING`, `mcp_extension.py` line 252); "the four cases VibeMirror-coder suggested" (30 October); King Yew's "`_meta` or as an argument" (30 October). "Fixture, commands and output on 1.29.1 and 2.3.0, at a pinned commit" holds once 5726c34 is pushed: the README carries the commands, the two output files the versions and raw output.

Weakest remaining sentence: FSIG line 13, "Once King Yew's draft is up, I can rerun the cases against it if that helps." A draft is text; the cases can be checked against its semantics, not rerun against it. If kept: "Once King Yew's draft is up, I can check the cases against it if that helps."
