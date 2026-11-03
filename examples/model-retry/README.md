# Model retry: what keeps an operation's identity when the model decides to call again

A signed idempotency key stops a second execution only if the retry carries the same key. After a lost answer, the party that decides to call again is often the model, and in this binding the model never sees the key. So the client's wiring decides the outcome.

This fixture runs that case over a real MCP session: the official Python SDK's client and server sessions, the LAP extension middleware and its claim store. A relay between the two sessions, where a transport would sit, drops the message. It is not a transport-level fault. The fake provider takes no idempotency key of its own, so a second call is a second refund.

The case comes from [MCP spec issue 3394](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3394) (terminalstate, 2026-10-29): the effect commits, the answer is lost, and the model calls again. The fixture is written from that description; no code from any repository in that thread is used.

**The model is a script that always repeats when it has no definite answer.** It also runs a read that cannot contain the effect, as in terminalstate's account, but the read decides nothing here. So this shows what each wiring does if the model retries, not how often a model does. For rates under their own conditions, see the comments by terminalstate and Baktiyarsan in that thread, which differ.

```bash
pip install "living-agents[mcp]>=0.4.14"
cd examples/model-retry && python run.py
```

Every count and every answer kind is asserted, the failures included, and the script exits 1 on a difference. The outputs on mcp 1.29.1 and 2.3.0 are saved next to this file ([1.29.1](output-mcp-1.29.1.txt), [2.3.0](output-mcp-2.3.0.txt)) and are identical apart from the version line. CI runs it on the newest release of each major. Reverting the middleware's recognition order, so that the envelope is checked first, changes two cells and fails the script.

## Part 1: three client wirings

Refunds made. A star marks a count other than the refunds wanted. The saved outputs also show the last answer the model saw.

| Case | Wanted | New key per call | Key from arguments | Client resolves first |
|---|---|---|---|---|
| Response lost, model repeats | 1 | 2* | 1 | 1 |
| Response lost twice, model repeats | 1 | 2* | 1 | 1 |
| Lost twice, model changes one argument | 1 | 2* | 2* | 1 |
| Request lost, model repeats | 1 | 1 | 1 | 1 |
| Executor dies after the effect, model repeats | 1 | 2* | 1 | 1 |
| Lost twice, passport expires, then reissued | 1 | 2* | 1 | 1 |
| Response lost, cap cut below the amount | 1 | 1 | 1 | 1 |
| Response lost, authority narrowed, then restored | 1 | 2* | 1 | 1 |
| Response lost, authority narrowed, model asks for another refund | 2 | 3* | 2 | 2 |
| Passport expired, model repeats | 0 | 0 | 0 | 0 |
| Two refunds wanted, no fault | 2 | 2 | 1* | 2 |
| Two different refunds in flight, answers lost | 2 | 5* | 2 | 2 |
| Lost twice, client restarts, record lost | 1 | 2* | 1 | 2* |
| Lost twice, client restarts, record kept | 1 | 2* | 1 | 1 |
| Client killed mid-call, restarts, record kept | 1 | 2* | 1 | 1 |
| Response lost, server restarts, cap cut | 1 | 1 | 1 | 1 |
| Response lost, agent key rotated | 1 | 2* | 2* | 2* |

- **New key per call** is the wiring a wrapper reaches for first. The key's rule works as written, a new key is a new operation, and a retry that follows a committed effect runs again unless something else refuses it.
- **Key from arguments** keeps an identical retry together and survives a restart. It also swallows a repeat the model meant, and a changed argument is a new operation.
- **Client resolves first** records each call and its key before it sends the call, one call at a time per tool. It re-presents the record after any answer that is not definite, and sends nothing else on that tool until then. It tells the model the outcome is unknown only when it cannot find out.

What counts as definite for that third wiring:

- **A result**, fresh or marked `replayed`, clears the record.
- **`LAP_ERR_REPLAY_WITHHELD`** means the key executed. The record stays, so no new key is minted, and the model is told it ran, not given a refusal to call again. A call for something else on that tool while the record stays is told that it was not sent.
- **A refusal** ends a call only while every attempt of it was answered with a refusal, since a refusal received means that attempt did not run (draft, section 6). After an attempt whose answer was lost, that ended in a tool error or that a crash cut off, a refusal shows less. One from before recognition, such as an expired passport, says nothing about the key. One from after it shows only that the server holds no claim now, which proves nothing after a restart of an in-process store. So the record stays and the model is told the outcome is unknown ("Response lost, server restarts, cap cut").
- **Anything else is not definite:** a timeout, a tool error and `LAP_ERR_REPLAY`.

There is no wire change, but that wiring has costs and limits:

- **The record has to be durable.** Here it is a dict. "Record lost" shows the cost, and "record kept" shows what a durable table gives.
- **The record has to name the agent key and issuer.** A different agent key is a new scope, so the call runs again ("agent key rotated").
- **One hold blocks every other call on its tool** until a definite answer or a person. It does not order related tools: an unresolved booking does not hold back a cancel.
- **The binding has no status-only probe.** Re-presenting a held call that never arrived runs it. If the model has since changed its mind, or the terms have expired, the earlier call still executes and the model is told afterwards. The script asserts this too. So a hold should be short, and a long one belongs with a person.

A client without this extension gets none of this, because the binding refuses a call without the extension object. A key in the tool arguments would reach such a client and the model, and would then depend on the model copying it. That form is not tested here.

After a lost answer the first signal is the client's own timeout, so only the client can mark that moment as unresolved. After an executor dies, the first answer in this reference is a plain tool error, and only the retry names reconciliation. That is a gap (draft, section 9, question 9).

## Part 2: the booking cases

Cases 1, 2, 3 and 4 are the four synthetic cases VibeMirror-coder suggested on [FSIG issue 17](https://github.com/modelcontextprotocol/financial-services-interest-group/issues/17) on 2026-10-30. Cases 1b, 2b, 2c and 4b are the author's variants. All run through the middleware over the same session, with a client that keeps its key. The operator's lookup, completion and release act directly on the system of record and the claim store. By default the fake system of record accepts a repeated reference, to show what the claim store does alone.

| Case | Bookings | Cancels | What the client saw |
|---|---|---|---|
| 1. Booked, response lost | 1 | 0 | timeout, then a marked replay; the lookup agrees, and was not needed |
| 1b. Booked, executor dies | 1 | 0 | tool error, refused naming reconciliation, the operator's lookup finds it and completes the claim, marked replay |
| 2. Not committed, executor dies | 1 | 0 | tool error, refused, lookup negative, still refused, operator releases, runs once |
| 2b. Released on a negative read, the effect lands late | **2** | 0 | tool error, lookup negative, operator releases, runs again, the first effect lands |
| 2c. The same, reference unique at the system of record | 1 | 0 | the same steps; the system of record rejects the repeat |
| 3. Cancelled and confirmed | 1 | 1 | done, then a marked replay |
| 4. Cancel times out | 1 | 1 | timeout, then a marked replay |
| 4b. Cancel, executor dies | 1 | 1 | tool error, refused, the operator's lookup finds it and completes the claim, marked replay |

Case 4 as suggested stays indeterminate. In this binding a timeout leaves a completed claim that replays, so the outcome stays unresolved only when the executor dies, which is case 4b.

Case 2b is the limit, and the fixture asserts it. The release is the fixture's own act, and the double booking needs a system that accepts a repeated reference; case 2c shows a unique reference stopping it at the effect boundary. A negative read proves nothing until a horizon has passed, and this reference has no horizon: nothing stops an operator releasing a claim too early.

Not covered here:

- **Held spend.** The reference enforces a per-call cap only; a cumulative hold is the spend authorizer's. The suggested cases also assert no release of held spend, and that part does not run here.
- **A typed lookup.** The lookup above is the fixture's own function, run by the operator. The binding defines no lookup tool and no typed outcome.

## Part 3: the checks asked for on the call-outcome draft

On 2026-11-02 King Yew Choo posted a draft extension on [FSIG issue 17](https://github.com/modelcontextprotocol/financial-services-interest-group/issues/17), `io.github.kingyewchoo/call-outcome`: an operation key per mutating call, a lookup that answers `occurred`, `none` or `unknown`, and closing a key as a separate operator act that durably blocks admission. It asked for the four booking cases above, plus a booking delayed past a lookup miss, and a key closed before delivery or while the worker is queued. The outcomes below are in the draft's words, from the fixture's own lookup (`call_outcome`): `occurred` when the claim completed or the system of record holds the booking, `none` only for a closed key with nothing at the system of record, otherwise `unknown`.

| Case | Bookings | Cancels | What the client and the lookup saw |
|---|---|---|---|
| K1. Booking delayed past a lookup miss, then delivered | 1 | 0 | tool error; lookup `unknown`; the repeat is held; delivered; `occurred` |
| K2. Request delayed, no closure (the reference) | 1 | 0 | timeout; `unknown`; the delayed request arrives and runs |
| K2c. The same, key closed before delivery | 0 | 0 | timeout; `unknown`; closed, `none`; the delayed request is refused |
| K3. Job queued at the server, no closure (the reference) | 1 | 0 | tool error; `unknown`; the worker resumes and books |
| K3c. The same, key closed, the worker checks the claim first | 0 | 0 | tool error; closed, `none`; a repeat is refused |
| K4. The window closes the key, the booking lands late past the server | 1 | 1 | tool error; `unknown`; the window ends, `none`; the repeat is refused; the late booking, `occurred`; cancelled once under its own key; a second pass replays |

- **The reference has no closed state.** Its reconciliation acts are `complete` and `release`, and `release` forgets the claim so that the key can run again, the opposite of closing. In K2 and K3 the operator does nothing, and each books once where the draft expects none. An operator could still block an unseen key by claiming it in its place: the late request is then refused as key reuse, and the lookup says `unknown`, not `none`. K2c, K3c and K4 use `ClosingCache`, a subclass in this fixture: a tombstone that refuses admission, also for a key the server has not seen, and that a worker reads before its effect.
- **A closed key has no answer of its own here.** The refusal reads as unresolved (`LAP_ERR_REPLAY`); only the lookup says `none`.
- **Closing stops only what is still at the server.** K4 follows the FX practice described on the issue (siddhartha1310, 2026-11-03): the key lives as long as the quote's listening window and is closed when it ends. A booking already past the server lands anyway, and is cancelled once under a cancellation key of its own. The `none` in K4 is the fixture's rule (a closed key, nothing at the system of record); the draft also requires that nothing can still cause the effect, and the late booking shows that was not so.
- **Not modelled:** the race between closure and dispatch (one process cannot race; in this store a completion after a closure overwrites it), a durable tombstone (a restart would forget the closure; the draft requires intact claim history), the draft's lookup method and `outcome` field, real middleware hops, held spend.

Reverting the closure in a copy of the script (the closed state no longer answered at admission, the worker no longer checking) fails K2c on the answer kind, K3c on the count and K4 on the answer kind.

## Limits

A scripted model, not an LLM. A claim store in memory, one process, lost on a server restart. The client's record is in memory too. The agent key and issuer are fixed for a run except in the rotation case. Python only.
