# FSIG issue #17: replies to the outline comment (Sankalp Gilda and King Yew Choo, 2026-10-27)

**Source.** https://github.com/modelcontextprotocol/financial-services-interest-group/issues/17, comments of 2026-10-27 05:05 UTC (astrogilda) and 09:49 UTC (kingyewchoo), in reply to the outline comment of 2026-10-26 (reviewed by two models before posting).

## Sankalp Gilda (champion of the FSIG "Regulatory audit & attestation" item; author of draft-gilda-audit-agent-audit-record)

> both questions land on real gaps, and the first was a bug in #213.

- Rule 1 had keyed a retry on the request digest (section 5.3: action, arguments, resource), which carries no intent. **The next draft adds `decision.operationKey`, taken from the agent's signed request, and each held entry carries it.** Under one limit digest: the same key and request digest is one retry; the same key with a different digest is malformed and refused; a new key is a new operation even when the digest matches (Sid's new deal with a new booking reference, "and his reference is your idempotency key").
- The limit digest is the authority digest only where the passport states the cumulative limit; in LAP's design the spend authorizer does, so they differ (as the comment had said).
- Both are now cases CS1 to CS17 in vectors-agent-audit-record at commit 8f9cdc4a (not yet in a release), with two identical payments under distinct keys as the control. The manifest at that commit names, among others: "CS1 with decision.operationKey removed", "CS1 with limitDigest equal to delegation.authorityDigest, the authority document stating the limit itself", "CS4 under another operationKey: the same intended payment again, a new operation counted", "CS4 with the held entry's requestDigest another request's: one operation key reused for a different request", and "CS7 ... the check keys on the operation key and not on the request digest". Runnable with `uvx --from git+https://github.com/probityai/agent-evidence-vectors@8f9cdc4a agent-evidence-vectors --corpus vectors-agent-audit-record` (third-party code; not run here).

## King Yew Choo (co-champion, finance cases)

> One case still open: a payment is held when the limit document is replaced, say for a raise or a cut. Your retry rule and both checks across records run under one `limitDigest`, so the held entry could drop out unseen, or its retry count as new. Does it carry over?

He cites spec issue 3394's comment of 2026-10-11 (arjun2075): an authorization change must not turn the same logical operation into a fresh deduplication entry; "the recovery path needs to preserve recognition of the earlier execution while independently checking current permission to return its result"; the different-tenant case needs an explicit identity rule.

## What this means for LAP (checked 2026-10-27, reproduced against 0.4.13 plus the local recovery changes)

- The champion of a venue workstream adopted a LAP concept into his draft (`decision.operationKey` = the agent's signed idempotency key) and his public corpus, in answer to a question from our comment. The first venue-level uptake of anything from LAP.
- Two behaviours of the reference, reproduced to answer King Yew from the enforcement side:
  1. A key reused with a different request returns the first call's result instead of being refused (a documented limitation since the cold-start test; Sankalp's rule refuses it as malformed, and the IETF idempotency-key draft says the same).
  2. A retry with the same key and the same request after the limit was cut below the amount is refused by the cap check (`LAP_ERR_CAP`) before the stored result is found, so the client cannot recover the receipt of an execution that already happened. The claim itself is keyed by (sub, key), independent of the authority document, so it survives a replacement and a retry is never a fresh entry; the gap is the order of checks, which is what arjun2075's "preserve recognition of the earlier execution while independently checking current permission to return its result" describes.
- Proposed alignment (owner to decide): store the request digest with the claim and refuse a reused key whose digest differs (`LAP_ERR_IDEMPOTENCY`); recognise an existing claim right after the passport and signature checks, before the cap check, so a completed call is replayed under any valid passport for the same agent key and an in-flight or indeterminate claim is refused as such; the cap check applies only to a fresh execution. Both ports, tests, LIP-4 §2 and the extension draft §4.1 and §5.6.
