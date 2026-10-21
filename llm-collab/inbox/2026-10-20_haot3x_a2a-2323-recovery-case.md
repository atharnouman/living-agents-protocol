# External review on A2A #2323: the crash-after-effect recovery case (haot3x, 2026-10-20)

**Source.** A comment on the A2A proposal thread (https://github.com/a2aproject/A2A/issues/2323#issuecomment-6287548442) by GitHub user haot3x (author association NONE; an account since 2011 with 34 public repositories), with an MIT-licensed gist of probes: https://gist.github.com/haot3x/45d632be7c6386420c0e21b152b0f722. The gist says it is AI-assisted review with original probes run locally, and makes no audit or conformance claim.

**The comment, in full:**

> One recovery case beyond the held-before-start demo: an external effect completes, then the process dies before storing its receipt. Should the A2A binding keep that key indeterminate until reconciliation rather than retry automatically? I checked the documented process-local cache boundary here; a durable claim still needs an explicit recovery rule.

**The probe.** `lap_restart_window.py` imports the real `IdempotencyCache` from the published repository at commit 1c2c8af and runs two operating-system processes: the first reserves a key, writes a simulated effect to a file, then exits before storing the completion; the second, with a fresh in-memory cache, reserves the same key and repeats the effect. Observed: two effects. The gist states plainly that this is the cache's documented process-local limitation, not an undisclosed flaw, and that the seven MCP-extension tests passed unchanged. Its point is the next step: persisting the claim prevents the fresh reservation but leaves "how to reconcile an in-flight claim whose external effect may already have happened", and "the A2A profile should define that recovery decision rather than infer failure from absence of a receipt".

**Verdict: correct, and a gap in the specification.** LIP-4 said the claim must be durable and that in-flight duplicates are refused; it never said how an in-flight claim resolves once its executor is dead. The A2A issue text went further than the specification supports ("a signed idempotency key on every mutating message keeps resumed work from repeating an external effect"), which holds only when the claim is durable and written before the effect, and even then leaves the dead-executor case open.

**Accepted and done the same day.**
- LIP-4 §2 step 5 and a new hardening rule, "Recovery of an in-flight claim": reservation before the effect, completion after; a claim whose executor died between them is indeterminate; never re-executed, never released by time alone; resolved only by reconciliation against the system of record (completed with the reconciled result, or released if the effect verifiably did not happen); where the effect cannot be queried the decision is the deployment's, never inferred from a missing receipt; a refused client must not mint a new key for the same intent.
- The MCP extension draft v0.3: step 6, section 5.6, the security bullet and the `LAP_ERR_REPLAY` row.
- Both reference caches model the state (`mark_indeterminate` / `markIndeterminate`, `release`; `claim()` returns `indeterminate`), the Python middleware refuses an indeterminate key with a reason that names reconciliation, with tests in both ports.
- The A2A issue text to be narrowed with a dated edit note; the reply drafted for the owner's approval.

**Not done.** The in-process cache still cannot observe its own death; detecting dead executors (a lease) is the durable backend's job, now stated as a MUST.
