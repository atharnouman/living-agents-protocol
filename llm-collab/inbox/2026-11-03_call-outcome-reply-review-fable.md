# Review of the call-outcome reply draft (Fable 5.1, independent, read-only, 2026-11-03)

Checked: all 25 comments on FSIG #17 by API (a 25th, glanitcom 11-03 09:49 UTC, is an unrelated SealedRun note; no reply needed); run.py, README, both saved outputs (identical apart from the version line); microcore.py, mcp_middleware.py, mcp_extension.py. Ran run.py on mcp 1.29.1: exit 0, output matches the saved file. Ran a scratchpad copy with the closure and the worker check removed: exactly K2c, K3c and K4 fail, as the commit says. Note: origin/main..HEAD is five commits (9529a4a plus four log/runbook commits); Part 3 is not public.

## A. Facts against the code and outputs

- "Cases 1 to 4: one booking each." True in count (rows 1, 1b, 2, 3, 4, 4b all show 1). But case 2's one booking is a fresh run under the *same* key after the fixture's `release`; the draft would close the key and expect a new one. "No duplicate" is the safe claim.
- "counted only on the cancellation event." True by construction: the fake's `cancellations` list is both the acknowledgment and the event. VibeMirror's "never from an HTTP ack alone" case has no run.
- "an unresolved cancellation stayed refused until an operator reconciled it." That is 4b (executor died after the effect), not case 4 as posed (cancel times out): in this binding a timeout leaves a completed claim that replays (row 4: `lost > replayed`).
- Bullet 2 matches K1 (`tool_error > unknown > unresolved > occurred`, bookings 1). "Delivery" there is a queued worker resuming; K2 covers the delayed-request reading and also books once.
- Bullet 3: counts match (K2, K3: 1; K2c, K3c: 0). The sentence "A key closed before delivery ... one booking each ... because my reference has no closure" misleads: in K2 and K3 nothing is closed; the runs simply have no closure. `release` forgets the claim so the key runs again: matches `IdempotencyCache.release`. The delayed request is simulated by dropping it and re-presenting identical bytes (`created` is the fixed `NOW`, so the signed base is identical); equivalent server-side, but say "arrives" or "re-sent".
- Point 2: "A unique reference at the system of record then keeps it to one booking" is **not shown**. K4 runs with `BookingSystem()` (unique=False); the repeat was refused by the closed key, so uniqueness was never exercised. The unique-reference result is Part 2 case 2c (a claim released too early), a different mechanism. Drop it. "Sid's rule ran as described": the window is a `close()` call by the fixture, no timer; "as Sid described, with the window's end as a closure" is honest.
- Point 3's first clause (a window where the system of record cannot accept the effect afterwards) has no run: K4's system of record accepts the late effect. Only the "elsewhere" branch ran.

## B. Does Part 3 test what King Yew asked?

King Yew: "I'd also delay a booking until after a lookup miss. Expect `unknown`, then deliver it while the quote is valid and check for one booking. In separate runs, close the key before delivery or while the worker is queued. Check for zero bookings after delivery or resumption."

- Run 1 (deliver, one booking): K1 and K2. Fair. Quote validity is not modelled (no time). In K1 the claim stays `indeterminate` after the worker books: the server never learns of the delivery, so a later repeat would be refused, not replayed. Not claimed, but visible in the output.
- Run 2 (closed before delivery, zero): K2c. Fair.
- Run 3 (closed while queued, zero after resumption): K3c. Fair as far as it goes, but the worker's check is a cooperative read (`checks_first`) in one process. King Yew named the race ("closure and dispatch compete for the same atomic transition"); the fixture cannot show it and the post's not-tested list omits it (the README has it). Add it.

ClosingCache: `self._status` dispatches to the override from both `lookup` and `claim`, so admission, the twin re-check and the post-cap re-check all refuse a closed key; `release` refuses a closed entry (state is not `indeterminate`), so closure cannot be undone by release. Holes, none exercised by a K case: (a) `complete()` on a closed entry overwrites it to `completed` (it refuses only an already completed one), so an operator completion, or a tool finishing after a close on an in-flight claim, silently un-closes; (b) `close()` accepts a reserved (executing) claim, which is exactly the race; (c) `mark_indeterminate`/`abandon` raise on a closed entry, which inside the middleware's except handler would replace the tool's exception. Wrong-reason check: in K2c, without the override the tombstone (`claim` with identity None) would still refuse the late request, but as KEY_REUSE ("refused"); the asserted "unresolved" kind catches it, so the override is load-bearing. In K3c and K4 the `retry == "unresolved"` assertion proves nothing about closure (an indeterminate claim is refused the same way); closure is proven by `none` and the count only.

## C. The three points

1. The first sentence restates the draft's own rule in the author's vocabulary, and "release" clashes with the thread's usage (Sid, VibeMirror: releasing held spend). The useful content is the second sentence: the draft says what a tool returns while unresolved (`unknown`, `isError`) but not what it returns for a call under a closed key. Keep that only.
2. Correctly attributed to Sid (11-03: "Closing the key stops only what is still at the MCP server"; "cancelled once, using its own cancellation key"). The unique-reference sentence is unsupported. As a point "for the draft" it proposes no change; merge with 3.
3. Fair reading of King Yew's rule (`none` only when the system of record rules out a past effect and nothing can still cause it) and of Sid (window-end `none`, automatic, hold released, late booking cancelled once). The conditional clause is a legitimate way to satisfy King Yew's rule from Sid's "it won't be booked in Murex either". But "Elsewhere `none` stays provisional" is a proposed relaxation of King Yew's rule, not a reading, and it labels Sid's `none` provisional, which Sid may not accept (for him it is final for the hold; cancellation is the backstop). State it as a suggestion.

## D. Landing

Tone is right: it does his checks, in his vocabulary, and says where the reference fails them. The AI line matches the thread. About 330 words; 250 is enough. "my reference" three times keeps the author's implementation in the foreground Peder asked to leave; once is enough, the thread knows it. "Happy to share the fixture" reads oddly: the fixture is already linked from the 1 November comment (pinned to 15896e6), and Part 3 sits in an unpushed commit, so no one can check these claims. Best: push 9529a4a (owner's call) before posting and write "Part 3 of the fixture in my 1 November comment", checkable with no new link. If it is not pushed by Thursday, say the runs are not yet public. Nothing here should irritate King Yew, Sankalp (not mentioned) or Peder; the one risk with Sid is "provisional", fixed above.

## E. Verdict

Post with changes: drop the unique-reference sentence; reword bullet 3 (nothing was closed in K2/K3); "no duplicate" instead of "one booking each", with case 2's release noted; point 1 reduced to the closed-key answer, no "release"; points 2 and 3 merged and stated as a suggestion; the closure/dispatch race added to not-tested; one "my reference"; cite the 1 November fixture after pushing. Revised text:

---

@kingyewchoo I ran the four cases and your three extra runs: the official Python SDK, the fault between the client and server sessions, a fake system of record that counts bookings and cancellations, and the lookup as the fixture's own function, answering `occurred`, `none` or `unknown` (Part 3 of the fixture in my 1 November comment).

- Cases 1 to 4: no duplicate booking or cancellation. Cancellation had its own key; one whose executor died after the effect stayed refused until an operator completed it. Case 2 ended with a release, which lets the key run again; your draft would close it instead.
- A booking delayed past a lookup miss: `unknown`, the repeat held, one booking on delivery.
- A key closed before delivery, and one closed while the worker was queued: without a closure (my reference has only complete and release) both booked once. With one added in the fixture, a tombstone that refuses admission, also for a key the server never saw, and that the worker reads before its effect, both booked none.

Two points for the draft:

1. A call under a closed key needs an answer of its own. The draft returns `unknown` with `isError` while the effect is unresolved; nothing says what a closed key returns, and the nearest refusal I have reads as unresolved.
2. As @siddhartha1310 says, closing stops only what is still at the server. In a run of his window, the key closed at its end, a booking already past the server landed after `none` and was cancelled once under its own key; a second pass replayed. Your rule gives `none` only when nothing can still cause the effect, so his window-end `none` would stay `unknown`. The draft could let a declared validity window close the key and report `none`, and say that an effect landing after `none` is reversed once under its own key.

Not tested: the race between closure and dispatch, a durable store, real middleware hops, held spend.

AI use: an AI assistant helped write the fixture and draft this; I reviewed both before posting.
