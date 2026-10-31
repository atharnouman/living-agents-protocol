# Review of the model-retry fixture, spec note and two draft comments (Sonnet 5.5, 2026-11-01)

Brief: `llm-collab/inbox/2026-11-01_model-retry-review-brief.md`. Nothing was posted, committed, pushed or signed in; this file is the only repository file I wrote. Pronouns: they/them for anyone whose pronouns are not stated. Third-party text is paraphrased, not quoted.

## What I ran and read

**Verified by running**, always from scratch copies in my own directory with `python -B` (no file written under `E:\LivingAIAgents`):
- `run.py` unmodified on mcp 1.29.1 (the machine's Python) and on mcp 2.3.0 (a venv the caller had left in the session scratch folder; I installed nothing). Both end "all outcomes as asserted"; the output is identical except the version header line. The Part 1 counts in `examples/model-retry/README.md` and in the recut comment match the printed counts row by row; so do the six Part 2 rows.
- Nine breaks of the middleware (M1 to M9), three changes of the harness (H3, H4, H6), seven extra scenarios (S1 to S7) against the fixture's own `ResolveFirst`, and a patched copy of `present`/`ResolveFirst` (given after finding 3). With the patch the eight Part 1 rows, the stale-call line and the six Part 2 rows print identically on both SDKs.

**Verified by reading**: the three threads through `api.github.com` without credentials (3394: 45 comments, newest 2026-10-31 16:02 UTC; FSIG 17: 20 comments, newest 2026-10-30 11:19 UTC; FSIG 19: 4 comments), the group notes (public export, section of 29 October), the reference code, the LIP-4 draft and its diff, the CI file, the tutorial.

**Not done**: terminalstate's repository was not read; no CI run exists for the new step; `git status` shows `output/LAP-shipping-runbook.md` modified since the session began (a metrics row), not by me.

## Findings, most important first

### 1. Two calls in flight on one tool: `ResolveFirst` overwrites a held call and gives the model the wrong outcome

**Where.** `examples/model-retry/run.py` 222 to 251 (`self.held = {}` line 230; `self.held[tool] = (args, key)` line 246); `examples/model-retry/README.md` line 34 ("sends nothing new on that tool until it has a definite answer") and line 63 ("One held call per tool."); the same sentence in the spec bullet (`output/lip/LIP-4-mcp-extension-draft.md` line 336).

**Why wrong.** The hold is one slot per tool and is written only after a call's first non-definite answer. Two calls on one tool sent together are both "new" when they go out, so the second hold replaces the first. The first call is never re-presented, and the model that repeats it is told the other call's result as the outcome of "your earlier call". "One held call per tool" in Limits reads as a cap; it is a silent loss.

**Verified (S1, both SDKs).** Refund A (2000) and refund B (500) sent together, four answers dropped. Held afterwards: B only. Ledger: A and B once each. The model repeats A and is told `earlier_done` with B's refund (REF-2) as A's outcome; repeating A once more refunds A a second time (notes A, B, A).

**Judgement.** Parallel tool calls are ordinary in agent frameworks. Keying the hold by tool name also treats any later call on the tool as a retry of the held one (the changed-argument row depends on that), and it does not order related tools (a cancel is not held back by an unresolved booking).

**Replacement.** The patch after finding 3 (a lock per tool; the record is written before the send). It fixes S1: A is executed once, B is held back and told the outcome is unknown, nothing is duplicated (refunds: A). Wording for README lines 34 and 63 is given after the patch.

### 2. The record is written after the first send and does not name the agent identity

**Where.** `run.py` line 246; `README.md` line 34 ("keeps a call whose answer said nothing definite, with its key") and the last Part 1 row; the draft bullet ("keep a call whose answer said nothing definite, with its key, in durable storage").

**Why wrong.** (a) A durable table written after the first non-definite answer still loses a call when the client dies while the first call is in flight; the restarted client's model repeats with a new key. The "client restarts" row only covers a restart after two losses. (b) The claim scope is (audience, tenant, agent DID, key). The record does not name the agent key, and the fixture and the tutorial both generate the agent key at process start (`run.py` 65 to 67; `examples/mcp-server/client.py` 38 to 39), so a real restart changes the scope even when the table survives. The approved 28 October text said this ("a rotated agent key is a new scope and the retry runs again"); the recut and the bullet dropped it.

**Verified.** S4: the client task is cancelled 30 ms into the first call (effect committed, answer dropped): 1 refund, nothing recorded; a restarted client's model repeats: 2 refunds. S3: the held call re-presented under a rotated agent key (new passport `sub`): 2 refunds. With the patch S4 gives 1 (`replayed`); a durable table also turns the restart row from 2 to 1 (tested: in memory 2, shared table 1). S3 is not fixable in the fixture: the record has to name the agent key and issuer, and if the client can no longer sign as that agent the record goes to a person.

**Judgement.** The fixture's "durable storage" is untested (the table is a dict), and the order of the write is the part a real client gets wrong.

### 3. "Definite" is mis-drawn in three places, and the spec sentence does not match the list

**Where.** `run.py` 168 (`AFTER_RECOGNITION`), 177 to 193 (line 189: `any(code in text for code in AFTER_RECOGNITION)`), 196 (`DEFINITE`); README line 34; draft bullet: "a refusal at step 1, 2 or 3 of section 4.1 is not definite"; draft 5.6 (lines 314 to 318) and section 6 (line 325).

**Why wrong.**
- (a) A refusal at step 5 or 6 (`LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP`) is classed definite and the hold is dropped. It shows only that no claim is held now. After a restart of an in-process store, or past a retention window (open question 8), the key is absent whether or not the effect happened.
- (b) `LAP_ERR_REPLAY_WITHHELD` means the key executed, but it shares the kind `refused` with the not-executed refusals and the hold is dropped; draft 5.6 says the client MUST NOT read it as not executed.
- (c) Matching is `code in text` anywhere in the text. On mcp 1.29.1 the SDK appends a tool's own exception message to the error text, so a message that quotes a code is read as a definite refusal.
- (d) The spec sentence names steps 1 to 3 only. The fixture also leaves `LAP_ERR_IDEMPOTENCY`, `LAP_ERR_ISSUER`, `LAP_ERR_REPLAY` and unknown codes not definite, and counts `KEY_REUSE` and `WITHHELD` as definite, which the sentence does not say.

**Verified.** S2: refund made, response lost twice, server restarted (empty claim store), passport cut to a 1000 cap: the re-presentation answers `LAP_ERR_CAP`, kind `refused`, hold dropped, refunds made 1; a model that retries with 1000 brings the total to 3000 against 2000 wanted. With the store kept, the same sequence returns `replayed` (recognition first works). S6/S6b: after `WITHHELD` the hold is dropped; a restored passport and a repeated call mint a new key: 2 refunds. S5 (mcp 1.29.1 only): a tool that commits and then raises a message quoting `LAP_ERR_CAP` is classed `refused`, hold dropped, 2 refunds; on 2.3.0 the SDK reports only "Error executing tool create_refund", so it does not occur there.

**Judgement.** Section 6 says every code means the tool did not execute for this request. That is true of "this request" and is the trap: a refusal before the key lookup says nothing about an earlier request under the same key.

**Replacement (tested; covers findings 1 to 3).** In `run.py`, replace the `AFTER_RECOGNITION` line, the tail of `present`, and the whole `ResolveFirst` class:

```python
import re
# The code must open the text (after the SDK's own prefix). A refusal ends a call only on its FIRST presentation.
NOT_EXECUTED_IF_FIRST = ("LAP_ERR_ACT", "LAP_ERR_RES", "LAP_ERR_CAP", "LAP_ERR_KEY_REUSE")
CODE = re.compile(r"^(?:Error executing tool \S+: )?(LAP_ERR_[A-Z_]+):")

    # in present(), after `text = ...`:
    if getattr(result, "is_error", getattr(result, "isError", False)):
        found = CODE.match(text)
        code = found.group(1) if found else None
        if code == "LAP_ERR_REPLAY":
            return Answer("unresolved", text)
        if code == "LAP_ERR_REPLAY_WITHHELD":      # the key EXECUTED; only the result is withheld
            return Answer("withheld", text)
        if code in NOT_EXECUTED_IF_FIRST:
            return Answer("refused", text)
        return Answer("says_nothing" if code else "tool_error", text)
    entry = (getattr(result, "meta", None) or {}).get(EXTENSION_ID, {})
    return Answer("replayed" if entry.get("replayed") else "done", text)


class ResolveFirst:
    """Record the call and its key BEFORE the first send; one call at a time per tool; re-present the record after any
    answer that is not definite. A refusal ends the call only on its first presentation (after an earlier attempt it shows
    only that no claim is held now). WITHHELD means the key executed: the record stays, so no new key is minted."""
    label = "client resolves first"

    def __init__(self, session, table=None):
        self.session = session
        self.held = table if table is not None else {}   # tool -> [args, key, attempts]; durable in a real client
        self.locks = {}

    async def call(self, tool, args):
        async with self.locks.setdefault(tool, anyio.Lock()):
            if tool in self.held:
                held_args, key, attempts = self.held[tool]
            else:
                held_args, key, attempts = args, uuid.uuid4().hex, 0
                self.held[tool] = [held_args, key, attempts]            # written before the first send
            fresh = attempts == 0
            for _ in range(2 if fresh else 1):                           # a fresh call gets one immediate re-present
                answer = await present(self.session, tool, held_args, key)
                attempts += 1
                self.held[tool][2] = attempts
                if answer.kind in ("done", "replayed", "withheld") or (answer.kind == "refused" and attempts == 1):
                    break
            else:
                return Answer("unknown", "the outcome of this call is unknown; nothing new will be sent on this tool until it is resolved"
                              if fresh else "the outcome of your earlier call is unknown; nothing new was sent")
            if answer.kind != "withheld":
                del self.held[tool]
            if held_args == args or answer.kind == "withheld":
                return answer
            return Answer("earlier_done", "your earlier call has this outcome; this call was not sent: " + answer.text)
```

Also add `withheld` to the kinds in the `Answer` comment. Results with the patch, both SDKs: S1 refunds A only (B held back); S2 with a restart: `unknown`, hold kept, 1 refund; S4: 1 refund; S5: 1 refund; S6: `withheld`, hold kept, still 1 refund after the passport is restored (`replayed`). S3 still gives 2 (see finding 2).

Wording that goes with it:

- `README.md` line 34, replace with: "**Client resolves first** records each call and its key before it sends the call, one call at a time per tool, and re-presents the record after any answer that is not definite, sending nothing else on that tool until then. A result (fresh or marked `replayed`) clears the record. `LAP_ERR_REPLAY_WITHHELD` means the key executed: the record stays, so no new key is minted. A refusal at step 5 or 6 (`LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP`) or `LAP_ERR_KEY_REUSE` ends the call only on its first presentation; after an earlier attempt it shows only that the server holds no claim now, so the record stays and the model is told the outcome is unknown. A timeout, a tool error, `LAP_ERR_REPLAY` and a refusal from before recognition, such as an expired passport, are not definite. There is no wire change, but the record has to be durable and has to name the agent key: here it lives in memory (the restart rows show the cost) and the agent key is fixed for the run."
- `README.md` line 63 (Limits), replace with: "A scripted model, not an LLM. A claim store in memory, one process, lost on a server restart; after a restart a refusal at step 5 or 6 no longer shows that nothing ran. The client's record is in memory too. The agent key and issuer are fixed for a run: a different agent key is a new scope and runs the call again. One hold blocks every other call on its tool until a definite answer or a person. Python only."
- Add the row "Lost twice, client restarts, record durable | 1 | 2* | 1 | 1" (tested).

### 4. FSIG reply: attribution, an unsupported inference, a result Sid will answer first

**Where.** `outreach/FSIG-17-reply-2026-11-01.md` lines 7 and 9.

**Why wrong.**
- (a) Line 7, "what held was a client rule rather than the key's place": the fixture never varied where the key travels, so it cannot say the place does not matter, and the place is what Peder's point is about.
- (b) Line 7, "which I did not test": the argument form has outside data in the 3394 thread that King Yew does not have a pointer to (Baktiyarsan, 14 October, 900 episodes, contributor-reported, code not public: two frontier models had no failures with a key in the tool schema plus one prompt sentence, a small local model 4.7%; modsuperagi, 6 October, a smaller deterministic run).
- (c) Line 7, "Peder's point holds on my side": the direction is right and understated. Peder (an organisation member, comment of 30 October 11:17 UTC) said `_meta` is fine for app-directed receipts and audit data but ties uptake to wide adoption, and that keys or receipts in the arguments or return schema work without that. For this extension the cost is not "gets nothing": a client that does not implement it cannot call these tools at all (draft 2.5; README line 38 of the fixture).
- (d) Line 9, "the four suggested cases": they are VibeMirror-coder's (FSIG 17, 30 October 06:53 UTC); King Yew pointed to them at 10:05. Sid did not suggest them. The reply does not say whose they are. Also the fixture's case 4 uses an executor that dies after the effect; the suggested case says the cancellation times out.
- (e) Line 9, "a late commit made two bookings": that is the author's own variant (2b), not one of the four, and it needs a booking system that accepts a repeated reference. Sid's own account (26 October) is that the booking system rejects a repeat of a unique booking reference, and that a deal is never retried because the price has expired. Telling Sid "two bookings" without that is the sentence Sid will answer first. The stale-call limit (a held call re-sent later books at the old price) is the fixture's result most relevant to Sid's domain and the reply does not say it.
- (f) Line 9, last sentence: it offers to run Sid's shapes. The file's header already says to delete it unless the author will do the work.
- (g) After Peder's guidance on the call (describe the protocol additions or the shape of the extension, not external projects), paragraph 2 reads as results from "my own reference". Reframe as what the protocol would need.

**Verified.** (a), (c), (d), (e), (f) by reading the threads, the notes and the code; (e) also by `BookingSystem.book` (run.py 383 to 384), which appends without a uniqueness check.

**Replacement** (after the patch of finding 3 is applied; about 200 words; the link must be pinned):

```
@kingyewchoo for your draft, on `_meta` or argument: in a lost-response run with a signed key in `_meta` and a scripted model that always repeats ([fixture and output](PINNED LINK)), who keeps the key across attempts decided the outcome. A new key per model call ran the refund twice; a key derived from the arguments swallowed an intended repeat; a client that records the call and its key before sending, and re-presents it until the answer is definite, ran it once. I did not vary where the key travels; Baktiyarsan tried the argument form, with a prompt sentence, on the MCP spec issue 3394 (14 October, contributor-reported). Peder's point of 30 October holds for my extension: a client that does not implement it cannot call these tools at all. So the draft may need to say who keeps the key across attempts, wherever it travels.

@siddhartha1310 the four cases VibeMirror-coder suggested, run against my reference (same link): 1, 3 and 4 gave no duplicate. In 2 the claim stayed refused until released; releasing on a negative read, with the effect landing late, gave two bookings, but only because my fake booking system accepts a duplicate reference, which yours would reject. Re-sending a held call also books at the old price, so for an expiring deal your never-retry, look-up-by-reference practice is safer. The lookup was my own function with no typed outcome; held spend is not covered.

AI use: an AI assistant helped write the fixture and draft this; I reviewed both before posting.
```

If the patch is not applied before posting, replace "records the call and its key before sending, and re-presents it until the answer is definite, ran it once" with "keeps a call whose answer was not definite, with its key, and re-presents it ran it once, when one call was in flight at a time and the client was not restarted".

### 5. 3394 recut: several sentences say more than the code shows, and the text adds little that the thread lacks

**Where.** `outreach/MCP-3394-comment-recut-2026-11-01.md` lines 7, 20, 22, 24, 26.

**Why wrong.**
- (a) Line 7, "It runs terminalstate's shape": the shape's distinctive element, a read that is correct for what it asked and cannot contain the effect, is in the script but decides nothing. Deleting the `list_transactions` call leaves every count unchanged (S7, three wirings, both with and without the read: 2, 1, 1). Say "the lost answer and the repeat".
- (b) Line 22, "so a client must read the reason text. That falls short of your second requirement": the fixture's client does not read reason text; `present` (run.py 187) matches the code `LAP_ERR_REPLAY:`, which does distinguish an unresolved outcome from a refusal. What the shared code leaves open is "try again shortly" against "ask an operator". The line also leaves out the real gap: the first answer after an executor dies is a plain tool error (the run prints `tool_error > unresolved`), although the server knows at that moment that the claim is indeterminate. Only the retry names reconciliation. That is the part of terminalstate's complaint (answers that never say the outcome is unknown) which the reference does not meet.
- (c) Line 24: the two-bookings result is constructed (a stall injected, the release made by the harness, a booking system that accepts a repeated reference); "This supports your point" is true by construction. Say so or cut the paragraph.
- (d) Line 26: the link is `tree/main`. arjun2075 asks each contributor for a pinned commit, versions, run commands and raw output (comments of 14, 19 and 26 October); a moving branch cannot be rerun. The header already says to pin.
- (e) Line 20: it states the restart and stale-call limits only. Without the record-before-send, one-call-at-a-time and same-agent-key conditions (findings 1 and 2) the last column (client resolves first) will be corrected by the first reader who reruns it. The approved 28 October text stated the rotated-key limit and "not submitted anywhere; one author"; the recut dropped both, and this would be the author's first comment in the thread.
- (f) Length: 2,668 characters, 482 words. The thread's median is 1,271 characters and its 90th percentile 2,649.

**What it adds.** The wiring comparison and the stale-call limit are new to the thread. The timeout-moment point is in comments of 2 October (Ben-Home) and 18 October (theblueskies); the scope-and-consistency point is arjun2075's own (29 October) and ryjen's matrix (18 October). Its best sentence is one it never writes: the third wiring realises on the client side what terminalstate concluded the model needs (a key the caller keeps across attempts and an outcome-unknown result), and the fixture hands the model such a result (it does not test what a model does with it).

**Verified.** (a), (b) by running (S7; the Part 2 step lists); (d), (f) by counting and reading the thread.

**Replacement if it is posted at all** (about 200 words, after the patch; pinned link):

```
@arjun2075 on your first and second requirements, one data point from a draft extension by one author, not submitted anywhere. Official Python SDK 1.x and 2.x, the response dropped below the client session, a fake provider with no idempotency of its own, a scripted model that always repeats: it shows what each client wiring does if the model retries, not how often it does. With a signed key in `_meta` that the model never sees, refunds made when one was wanted: new key per call 2; key derived from the arguments 1, but an intended repeat swallowed; a client that records the call and its key before sending, re-presents it, and sends nothing else on that tool until the answer is definite 1. That is a client rule, not a wire change. It needs a record that survives a restart, one call at a time per tool and the same agent key, and with no status-only probe it runs a call that never arrived even if the model has since changed its mind. On the second requirement: after a lost answer the first signal is the client's own timeout, so only the client can mark it unresolved; after an executor dies, the first answer in my reference is a plain tool error and only the retry names reconciliation. Fixture and output on 1.29.1 and 2.3.0: PINNED LINK. Not claimed: how often models retry, or durability.

AI use: an AI assistant helped write the fixture and draft this; I reviewed both before posting.
```

### 6. Spec note: strength, placement, and claims elsewhere that the fixture now contradicts

**Where.** `output/lip/LIP-4-mcp-extension-draft.md` line 336 (bullet), 363 (open question 9), 325 (section 6), 314 to 318 (5.6); `README.md` line 36; `examples/mcp-server/README.md` line 3.

**Why wrong.**
- (a) The bullet sits among server MUSTs in "Security considerations" and recommends a rule that was run once, with a scripted model, with an in-memory table, and that fails in five ways (findings 1 to 3: concurrency, a client killed mid-call, a rotated agent key, a refusal after the store was lost, a withheld result filed as a refusal). It says "in durable storage" (the fixture's is a dict) and the write order is after the answer (finding 2).
- (b) It says "the same intended execution is the client's judgement", next to 5.6's MUST NOT choose a new key for the same intended execution. Say that the MUST NOT can only be met by a client that holds the key.
- (c) "even if the model has since changed its mind": the same holds when the terms have expired (a price, a quote), which is the case in the FSIG thread.
- (d) Two existing lines are now contradicted by the first column of the fixture's own table: `README.md` line 36, comment "a mutating tool: a retry never pays twice", and `examples/mcp-server/README.md` line 3, "whose retried calls never execute twice". Both are true only for a retry that carries the same key.
- (e) Open question 9 says the need was "raised ... 2026-10-29 and 2026-10-30". What was raised then (arjun2075 and terminalstate on 29 October; King Yew and VibeMirror-coder on 30 October) is an outcome-unknown result distinct from a failure; the split of `LAP_ERR_REPLAY` into two codes is the author's, and the fixture's client does not need it.

**Judgement.** The topic belongs in the draft (it is where the "never executes twice" claim holds or does not). The strength and the place do not: put the recipe in 5.6 as an informative paragraph, keep two sentences in section 7, and do not claim more than a scripted model showed.

**Replacement for the bullet at line 336** (or the same text in 5.6, with the bullet cut to its first two sentences and a pointer):

```
- **Model-driven retry (informative, added 2026-11-01).** After a lost answer the party that calls again is often the model, which never sees the key, so "the same intended execution" (section 5.6) is the client's judgement, and the MUST NOT of 5.6 can only be met by a client that holds the key. A client that mints a key per model tool call turns the model's retry into a new operation, and this binding runs it; a key derived from the arguments swallows an intended repeat and treats a changed argument as new. In a scripted-model test ([`examples/model-retry`](../../examples/model-retry/)) one wiring ran each operation once: the client records the call and its key in durable storage before the first send, handles one call at a time per tool, re-presents the record after any answer that is not definite, and sends nothing else on that tool until then, always under the same agent key and issuer. An answer is definite when it is a result (fresh or marked `replayed`), `LAP_ERR_REPLAY_WITHHELD` (the key executed; keep the key, mint no new one), or, on a call's first presentation only, `LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP` or `LAP_ERR_KEY_REUSE`. Any other answer is not: a timeout, a tool error, `LAP_ERR_REPLAY`, a refusal at steps 1 to 3. A refusal at step 5 or 6 on a re-presentation shows only that no claim is held now; it shows nothing after a restart of an in-process store or past the retention window (open question 8). A different agent key is a new scope and runs again; the same agent key under an issuer the server does not map to the claim's tenant is refused (`LAP_ERR_ISSUER`), which is not definite. This binding has no status-only probe, so re-presenting a call that never arrived runs it, even if the model has since changed its mind or the terms have expired. A client that cannot be changed gets none of this.
```

**Other replacements.**
- Line 363 (open question 9), second sentence: "A related question: whether an indeterminate claim should have its own code rather than sharing `LAP_ERR_REPLAY` with an in-flight one, so that a client can tell \"try again shortly\" from \"ask an operator\" without reading the reason (the need for an outcome-unknown result distinct from a failure was raised on the MCP specification's lost-response discussion on 2026-10-29 and in the Financial Services IG on 2026-10-30; the split of this code is the author's; added 2026-11-01)."
- Section 6, line 325, after "...did not execute for this request (v0.4)": add "; a refusal before the key lookup (steps 1 to 3) says nothing about an earlier request under the same key".
- `README.md` line 36: `# a mutating tool: a retry with the same key never pays twice`.
- `examples/mcp-server/README.md` line 3: "whose retries with the same idempotency key never execute twice (a client that mints a new key per call makes a new operation: see [`examples/model-retry`](../model-retry/))".
- Change log (line 367): add "Restamped." once it is true (finding 8).

### 7. What the fixture does and does not notice, and wording that claims more than the code shows

**Verified by breaking things (scratch copies of the reference).**

| Break | Output changes? |
|---|---|
| M1 no deduplication at all | Yes: rows flip, Part 2 case 1 prints DIFFERENT, a later case ends in a traceback, exit 1 |
| M2 `mark_indeterminate` does nothing | Part 1 identical; Part 2 case 2 raises at `release` (exit 1) |
| M3 replay marker never set | Counts identical; kinds change; Part 2 prints four DIFFERENT |
| M8 expired passport accepted | Yes: the expiry row changes (exit 1) |
| M4 recognition moved after the envelope check (the 0.4.14 fix reverted) | **No: byte-identical** |
| M5 same key for a different request replayed | **No** |
| M6 indeterminate reported as in-flight | **No** (same code) |
| M7 `release` allowed from any state | **No** |
| M9 reservation hidden from a twin | **No** (no concurrency in the fixture) |

Harness: removing the response drop makes seven assertions fail (H6); a 1 ms wait instead of 0.1 s changes nothing (H4), so the timeout selection is not producing the rows; counting an expired passport as definite flips the expiry row (H3); the model's read is decorative (S7).

**So.** Every printed number is real and comes from the SDK and the middleware. But the property the draft's "definite" rule rests on (recognition before the envelope check) is never exercised: no row produces a refusal from step 5 or 6, `LAP_ERR_KEY_REUSE` or `LAP_ERR_REPLAY_WITHHELD`, and the entries `ACT`, `RES`, `CAP`, `KEY_REUSE`, `WITHHELD` of the list could be deleted without any output changing. The fixture also uses `last.kind` only for display (run.py 355); the README says every outcome is asserted.

**Replacements.**
- Fixture `README.md` line 15, first sentence: "Every refund count below is asserted (the answer kinds in brackets are printed, not asserted), the failures included, and the script exits 1 on a difference."
- Add rows (tested unless marked): "Response lost, passport cut, store kept" (ResolveFirst replays: 1; would catch M4; the PerCall and SameArguments cells are not tested); "Lost twice, client restarts, record durable" (2*, 1, 1); "Two refunds in flight, answers lost" (ResolveFirst 1*, B held back not duplicated); "Client killed mid-call, record durable" (1); "Server restarted, passport cut" (ResolveFirst 1, `unknown`).
- Fixture `README.md` lines 42 and 44, `run.py` lines 13 and 509, and the root `README.md` table row: "the four booking cases" becomes "the four suggested cases and two variants of the author's (1b, 2b)" (Part 2 prints six rows); "run directly against the claim store" becomes "run through the middleware over the same session, with the operator's lookup, completion and release applied to the claim store directly".
- The folder has no install line. Add above the run line: `pip install "living-agents[mcp]>=0.4.14"` (the repository's `lap-python` equals tag v0.4.14, since `git diff v0.4.14 HEAD -- lap-python` is empty; I did not check the PyPI artifact itself).

### 8. Before anything is posted

- **Restamp.** `README.md` and `output/lip/LIP-4-mcp-extension-draft.md` are OpenTimestamps-anchored (`README.md.ots`, `output/lip/LIP-4-mcp-extension-draft.md.ots`) and both changed. The project's practice (commit 2665413, "README, both LIP-4 drafts and the cap vectors re-stamped") is to restamp after such an edit. The 2026-11-01 change-log note does not say it was done.
- **"and on both majors in CI"** (fixture README line 15) is not yet true of any run. The legs `mcp>=1.2,<2` and `mcp>=2,<3` resolve to the newest releases, not 1.29.1 and 2.3.0. Keep the sentence only after the pushed run is green on both legs, or write "on 1.29.1 and 2.3.0, and in CI on the newest of each major".
- **Pin the links** in both drafts (both use `tree/main`) and put the two outputs (1.29.1, 2.3.0) next to the fixture.
- **Re-read both threads** immediately before posting: 3394's newest comment is from 31 October, FSIG 17's from 30 October.

## Area check

**A, is the fixture honest?** Nothing found that makes a printed number false. The relay, the classification of an expired passport and the middleware's deduplication each change the output when broken. Weakest sentence: recut line 7, "It runs terminalstate's shape" (finding 5a).

**B, is "client resolves first" sound?** Not as described: findings 1 to 3. One limit that is fair but worth saying: one unresolved hold blocks every other call on its tool until a person acts. As a security-section item: the topic is fair, the strength and the place are not (finding 6).

**C, claim check.**
- Table counts (README, recut): true. "Identical output on 1.29.1 and 2.3.0": true. "On both majors in CI": not yet (finding 8).
- "The shape comes from 3394 (terminalstate, 2026-10-29)": true as to the lost answer and the repeat (the 29 October comments of 06:29 and 16:18 UTC); the read is decorative.
- "Four synthetic cases suggested on FSIG issue 17": true as to count and origin; the reply does not say whose, and case 4 differs (finding 4).
- Fixture README line 9, "terminalstate's runs measure" how often a model retries: true (29 October, 06:29 UTC: money moved twice in 70 of 600 trials, 47 of 300 with a plain prompt and 23 of 300 with a check-first prompt). Another contributor reported no duplicates in 60 runs per frontier model after a lost response when a read-back tool existed (Baktiyarsan, 14 October). So "how often" is contested in the thread, and the drafts rightly do not claim it.
- arjun2075's three requirements (29 October 14:38 UTC): the recut maps correctly.
- "Peder's point holds on my side": true in direction, understated, and the inference built on it is unsupported (finding 4).
- "In `_meta` only the client can keep it across attempts": true for this design. "A client that cannot be changed gets none of this": true; it cannot call the tool at all.
- "The reference has no horizon": true (`release()` has no time check). "No status-only probe": true.
- Open question 9's attribution: partly (finding 6e).
- Weakest sentence overall: FSIG line 7, "what held was a client rule rather than the key's place".

## Verdicts

### D. Each comment, one verdict

**3394 recut: do not post (now).** Reasons: it adds little the thread lacks (finding 5); at 482 words it is above the thread's 90th percentile, with a table, and would be the author's first appearance there, in a thread that already carries about ten own-project comments (most disclosed); the call notes record Peder advising that traction comes from describing the protocol additions or the shape of the extension, not from focusing on external projects, and this text opens on "my own draft extension"; its last column (client resolves first) would be challenged by the first reader who reruns it (findings 1 to 3); and it asks arjun2075 to read an unpinned link when arjun2075 asks every contributor for a pinned, rerunnable fixture. If the author overrides: apply 5(a) to (f), use the cut text above, pin the link, and post no sooner than seven days after the FSIG reply.

**FSIG reply: post with named changes.** The changes are those of finding 4 (the inference in line 7, the argument-form evidence, the attribution of the four cases, the duplicate-reference and expiring-price points for Sid, the deleted last sentence), plus the fixture patch of findings 1 to 3 or the limits stated. The draft is 254 words (1,515 characters; the thread's median is 898 and its 90th percentile 2,350), the replacement about 205: within the thread's range. It answers a question King Yew asked, its central point (who keeps the key across attempts) is protocol-shaped as Peder asked, and Sid asked for an implementer.

**Should it answer yaredmengistu04-arch? No.** Their comment (31 October) is addressed to maintainers, makes a general point about preserving authorization across retries, and points to their own site; the recut is addressed to arjun2075. The fixture has no row that tests a retry under narrowed authority, and the one case of that kind I ran (S6) shows the fixture filing a withheld result as a refusal (finding 3b), so it cannot back an answer. The approved 28 October text had a paragraph on the point and the recut dropped it. A reply would add a second plug to the thread.

**Better single venue.** FSIG 17: King Yew's draft is due by 12 November and asks exactly `_meta` or argument; the group asked for protocol-shaped input; the thread is small, and the author already has standing there. For 3394, the better future contribution is a short review of ndreno's retry-identity SEP draft once one exists (none was public in the thread as of 31 October).

### E. Order and timing

**Recommend only one now: the FSIG reply.** Sequence:
1. Fix findings 1 to 3 (the patch changes no printed row), the wording of 6 and 7, restamp, push on the author's "publish", and wait for CI to be green on both legs.
2. Post the FSIG reply on Monday 2 or Tuesday 3 November (UTC morning), after a re-read of the thread. That leaves about nine days before King Yew's draft is due, and it lands as input to the draft rather than a reaction to it.
3. Hold the 3394 note. Reassess after King Yew's draft (12 November). If it is still worth posting, post the ~200-word text, not within seven days of the FSIG reply, only if the thread is still on retry identity, and not on the same day as any other comment in an MCP repository. The earlier reviewers' warning about two same-day comments in two MCP repositories stands, and here both comments cite one fixture: if the fixture draws a correction in one venue, it should be fixed before the other.
