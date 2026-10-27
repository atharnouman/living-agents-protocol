# Review of the FSIG #17 reply draft: fresh Opus 5.5 agent, read-only (received 2026-10-28)

Verbatim hand-back. Model output, treated as a reviewer's opinion; the owner decides. Its corrected text is a candidate, merged with the Sonnet review's before posting.

---

## 1. Defects (MW = E:\LivingAIAgents\lap-python\living_agents\mcp_middleware.py, MC = …\microcore.py)

1. **Not ready to post.** There is no `v0.4.14` tag, locally or on GitHub, and PyPI's latest is 0.4.13. 7f116fc is not pushed (public main is 33d32aa). Tag and push, open both links, link the vectors at the tag, and keep "not yet on PyPI" unless you publish.
2. **"never executed leaves no record … nothing is consumed."** In-flight and indeterminate claims are records (MW:225-228). That is King Yew's held case, and the draft leaves it unanswered. Probe: both get `LAP_ERR_REPLAY` after a cut. "Consumed" is a ledger field in #213, and the raise or cut here is only the per-call cap.
3. **"replacing the limit creates no new entry … never counted."** The scope is (tenant, sub) (MC:212-230). Probe: a rotated agent key, or a principal key `tenant_of` does not map, executed twice. "Counted" repeats the 26 October review's correction.
4. **"consulted the new envelope before the claim."** True (v0.4.13 MW:135 runs before :148). But 0.4.13 also replayed the first result to a reused key with another request, and to another principal through the same agent key; "now matches" hides that. **"held only under the same envelope":** it replayed under any passport that still allowed the whole call.
5. **"arjun2075's rule in 3394, read literally."** A principle in a clarification issue. Read literally, checking current permission before returning the result would include the cap. The exemption is yours; his 12 October comment separating permission to disclose a result from permission for a new effect supports it.
6. **"method, tool and content digest, not the authority digest."** The identity uses the signed `@target-uri` line (MC:196-209), and the passport hash is stored beside it (MW:209-211).
7. **Corpus case keyed on `delegation.authorityDigest`.** That digest also changes in King Yew's same-principal case. Name the pair by principal instead.
8. **"15 … run by both of my test suites."** Count right; both suites pass (Python 186; Node 85, one unrelated skip). But the vectors test the cache and `check_invocation` separately (test_replay_vectors.py:25-53). The check order is tested only in Python, and Node has no middleware.
9. **Smaller points.** The replay marker is unsigned (extension §5.2). The store is also in-memory (MC:257-258). "A wait would be on another operation" is unclear. The draft runs to 488 words. Code: marker and receipt exist only for dict results (MW:175, 234).
10. **Before the push.** It also publishes the tracked `llm-collab/inbox` notes on both leads, including "The first venue-level uptake of anything from LAP".

**Verified as accurate:** MW:126-197, MW:163-177 and MC:269-277; identical receipts (reproduced).

## 2. Corrected reply (449 words)

@kingyewchoo on the open case, from the enforcement side. A payment refused at the tool server, or reported unsent by its tool, leaves no claim, so its retry is checked as new: a raised per-call cap admits it, a cut one refuses it. Any other payment has a claim keyed by the server's tenant for the principal, the agent key and the signed idempotency key, never by the limit or authority document; its retry is refused while that claim is in flight or indeterminate, replayed once completed. Replacing the limit adds no entry, but a rotated agent key, or a principal key not mapped to the same tenant, is a new scope where the retry can run again.

My 26 October comment overstated the reference: it checked the new envelope before the claim, so a retry after a cut got a cap error hiding the execution, and returned the first result to the same key presented for another request, or by another principal through the same agent key. Fixed at tag [`v0.4.14`](https://github.com/atharnouman/living-agents-protocol/tree/v0.4.14) (not yet on PyPI): recognition now follows the passport and signature checks. A completed key gets its stored result and receipt, marked as a replay, if the passport presented now covers the action, resource and unit (not the amount: replays spend nothing); otherwise the server says the key executed and withholds the result. So an envelope or cap refusal on a retry means only that no execution is recorded under that key. That is consistent with arjun2075's split in 3394 between recognition and disclosure; the amount exemption is mine.

@astrogilda the reference now follows your three cases: same key and request, one execution; same key, different request, refused in every state; new key, new operation even for identical bytes. Request identity: signed method, target and content digest, not the passport hash. A pair your corpus may want: the same operation key and request under the same principal's replaced authority (one operation) and another principal's (separate on my side: claims are scoped by tenant).

One more correction: identical request and response bytes under distinct keys give identical receipts (deterministic signature), so a receipt alone cannot show that a retry did not run again; only the server's claim record and unsigned replay marker say so. Binding the operation key into the receipt is an open question in my draft.

Vectors (15, claim store and replay check, run by my Python and Node suites; check order is tested only in the Python middleware): https://github.com/atharnouman/living-agents-protocol/blob/v0.4.14/output/lip/test-vectors/microcore-replay-vectors.json. Not claimed: exactly-once; the shipped claim store is in-memory, single-process; cumulative limits and held entries stay with the spend authorizer and your record.

AI use: an AI assistant helped draft this; I reviewed it before posting.

## 3. Verdict

Yes, once the tag, push and links are live and the notes checked.
