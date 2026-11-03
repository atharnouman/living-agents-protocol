# Review of the unposted FSIG 17 reply (call-outcome checks), Sonnet 5.5, 2026-11-03

**Done.** Read the draft, `run.py`, the README, both saved outputs and the 29 Oct group notes. Re-ran `run.py` on mcp 1.29.1 and 2.3.0: exit 0, identical to the saved outputs. Read all 25 comments on #17; the newest (an unrelated SealedRun note, 09:49 UTC) needs no answer. Probes: `C:\Users\DELL\AppData\Local\Temp\claude\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\scratchpad\probe1.py` and `probe2.py`. No project file changed, nothing posted, the other reviewer's file not opened.

## E. Verdict: post with named changes

No printed number is false. Six items need fixing (they say more than the runs show, or omit what the draft itself names), and point 3 is muddled. Revised text below (2,147 characters; original 2,022; thread median 1,074, 90th percentile 2,350).

## A. Facts, against code and output

Correct: every bookings/cancels count and step list; `release` deletes the claim; the reconciliation acts are `complete` and `release`; a closed key's refusal reads as unresolved; K2 and K3 give 1, K2c and K3c give 0.

Wrong or too strong:
1. "The lookup... in your three words" holds for the extra runs only. Cases 1 to 4 use the Part 2 lookup (`booked`, `not_found`, `cancelled`); none asserts `occurred`, `none` or `unknown`.
2. Bullet 1 puts cases 4 and 4b under one head. Case 4 as suggested (cancel times out) did not stay unresolved: the claim completed and the retry replayed. Only 4b (executor dies) stayed refused until an operator reconciled. That differs from VibeMirror's mapping; King Yew should see it.
3. "A key closed... one booking each": nothing was closed in K2 or K3, and "the reference cannot close" (K2 docstring; README line 101) is too strong. Probe E1: on the plain `IdempotencyCache`, an operator's `claim()` on the unseen key refuses the delayed request (`LAP_ERR_KEY_REUSE`), 0 bookings, and `release` cannot undo it. Missing is a closed marker (for `none`, for a worker to read) and a reply of its own. Say "no closed state".
4. Point 2, "a unique reference... keeps it to one booking": K4 does not show it. It prints identically with a unique and a non-unique booking system (E2); the retry is refused at the closed key and never reaches it. Uniqueness matters only if a fresh key follows `none` (E3: 2 bookings, 1 if unique), which no row runs.
5. "Sid's rule ran as described... a second pass cancelled nothing": the second pass is a same-key resend answered by a replay; the script makes every decision. Say "scripted".
6. "Not tested" omits the race between closure and dispatch, which the draft names for queued work (E4: a `complete()` after `close()` overwrites `closed`), and the wire format (no `get-outcome`, no `outcome` on the tool result, no host hold).

## B. Does Part 3 test what was asked?

King Yew asked for the four cases (cancellation on its own key, counted only on a confirmed event; an unresolved one to operations), a booking delayed past a miss (expect `unknown`, deliver, one booking), then in separate runs the key closed before delivery or while queued: "Check for zero bookings after delivery or resumption."

- **Cases 1 to 4:** own key yes; the count is the booking system's, so "counted only on the event" holds by design; operations appears only in 4b. Counts are checked, three-word outcomes are not.
- **K1:** delay is a queued job (tool raises, claim indeterminate); `unknown` is the function's rule, not an observation; quote validity is not modelled. K2 is the in-transit version (a dropped request plus a resend of the same key, equivalent for a claim store).
- **K2c, K3c:** fair as a state check, not as a test of the draft's adjectives (authorized: no check; durable: memory; atomic: no). The K2c zero comes from any slot existing (E1; reverting only the admission override leaves the count at 0 and changes the answer kind); the K3c zero from the worker predicate the fixture injects (without it, 1 booking). Queued work is more naturally in flight than indeterminate, and closure against completion is then the race the draft names.
- **K4:** not asked for; Sid's scenario. Its `none` comes from a rule weaker than the draft's (closed plus a miss, without the draft's condition that no delayed request or worker can still cause the effect); that gap is its point.

A fair reader will say "you wrote the closure and the worker to pass". The comment discloses the closure; do not present the zeros as a result about the draft.

## C. The points

1. Mostly restates the draft (separate act, blocks admission); "release" is the reference's word. New: the reply to a request that reaches a closed key.
2. Sound; correctly attributed to Sid apart from the unique-reference sentence.
3. Right direction, muddled text. "`none` stays provisional" is not in the draft's vocabulary (its rule gives `unknown` there). "Where the system of record cannot accept the effect afterwards" is the author's condition, not Sid's: Sid says a request past the server can still land, and handles it with cancel-once. "The cancellation rule" is unnamed. State the choice instead: `unknown` until reconciliation (King Yew) or a declared window with cancel-once (Sid). Merged into point 2 below.

## D. Landing

- Little promotion feel: no link, protocol-shaped points. But "my reference" appears three times and the opening calls the SDK, the fault and the fake "my reference". Define it once.
- King Yew answered the author's two 11-01 questions by name; the draft never acknowledges it (one clause added). "Ran as described" can read as validating FX practice with a toy.
- **No link: the right call, but "if it helps" is weak.** Part 3 exists only at local 9529a4a (the 11-01 pin predates it), a fourth own-repo link after Peder's guidance costs more than it gains, and every claim is a short step list. The revised text gives the sequences and the untested list. If asked, paste the six step lists, or push (needs "publish") and link once.
- Post before the 11-05 call, outside 19:00 to 02:00 UTC, after re-reading the thread. Before any push, fix the README and docstring wording from A3 and the revert sentence (K2c's count does not change when only admission is reverted).

## Revised text (post exactly this)

@kingyewchoo thanks for the client-side answers. I ran the four cases and your three extra runs on the official Python SDK, with a relay that drops messages, a fake booking system that counts bookings and cancellations, and my reference claim store. The lookup is the fixture's own function; in the extra runs it answers in your three words.

- Cases 1 to 4: one booking each, no duplicate; the cancellation had its own key and was counted at the booking system. A timed-out cancellation (case 4) replayed instead of staying `unknown`; one whose executor died stayed refused until an operator reconciled it.
- A booking delayed past a lookup miss (a queued job): `unknown`, the repeat refused, then one booking on delivery.
- Without a closure, a delayed request and a queued job each booked once, not zero: my store has no closed state, and `release` forgets the claim so the key runs again. With one added in the fixture (it refuses admission, also for a key the server never saw, and the worker reads it first), both gave zero.

Two points for the draft:

1. A request that reaches a closed key needs a defined reply. In my run it was refused as an unfinished call while the lookup said `none`; the draft could say it returns `none`.
2. As @siddhartha1310 says, closing stops only what is still at the server. Run as Sid describes (window ends, key closed, `none`), a booking that had already left the server landed afterwards: `none`, then `occurred`. So with hops, closure cannot show that no delayed worker remains, and `none` needs another basis: `unknown` until reconciliation, as your rule has it, or a declared validity window after which the booking cannot land, as Sid says. A window would let `none` follow without an operator; a booking that still lands is cancelled once under its own key (Sid's rule, scripted: one booking, one cancellation, a repeat replayed).

Not tested: a durable store, real middleware hops, the race between closure and dispatch, held spend, your methods and `outcome` field. I can share the fixture if useful.

AI use: an AI assistant helped write the fixture and draft this; I reviewed both before posting.
