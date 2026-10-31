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
- **`LAP_ERR_REPLAY_WITHHELD`** means the key executed. The record stays, so no new key is minted, and the model is told it ran, not given a refusal to call again.
- **`LAP_ERR_ACT`, `LAP_ERR_RES`, `LAP_ERR_CAP` or `LAP_ERR_KEY_REUSE`** end a call only on its first presentation. After an earlier attempt they show only that the server holds no claim now, which proves nothing after a restart of an in-process store. So the record stays and the model is told the outcome is unknown ("Response lost, server restarts, cap cut").
- **Anything else is not definite:** a timeout, a tool error, `LAP_ERR_REPLAY`, and a refusal from before recognition, such as an expired passport.

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

## Limits

A scripted model, not an LLM. A claim store in memory, one process, lost on a server restart. The client's record is in memory too. The agent key and issuer are fixed for a run except in the rotation case. Python only.
