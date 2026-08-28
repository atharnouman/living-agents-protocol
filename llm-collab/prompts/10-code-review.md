# Prompt 10 — Code Review: Reference Library & Demo (round-3 priority #1)

*(For a reviewer with file access. No context pack needed — read the actual files.)*

---

You are a hostile senior engineer reviewing security-critical code before its first public release. You have file access. Read, in this order:

1. `E:\LivingAIAgents\lap-reference\src\` — all four modules (crypto-util, jws, algebra, microcore, merkle-log)
2. `E:\LivingAIAgents\lap-reference\test\` — the test suites
3. `E:\LivingAIAgents\lap-demo\demo.js` and `replay.js`
4. The specs the code claims to implement: `E:\LivingAIAgents\output\lip\LIP-1-agent-passport-draft.md`, `LIP-3-scope-algebra-v0-draft.md`, `LIP-4-micro-core-draft.md`

Attack on four axes:

**A. Crypto correctness.** Ed25519 usage, the DER/SPKI wrapping, base58 edge cases (leading zeros, empty input), JWS construction (is the JCS-canonical-header choice interoperable with standard JWT libraries, which sign the header bytes as-given rather than re-canonicalized?), signature-input construction, the RFC 6962 Merkle implementation (odd trees, single-leaf trees, the audit-path recursion), salt handling in commitments, timing-unsafe comparisons on secrets/hashes anywhere.

**B. Spec-vs-code conformance.** Line up each LIP's MUST rules against the code: which normative requirements are unimplemented, which code behaviors are unspecified, and where do text and code disagree (each disagreement is a bug in one of them — say which). Examples to check hard: LIP-3's counterparty rule vs `counterpartySubsumes` (the deny-inheritance direction), the window-subdivision math vs `capSubsumes`, LIP-4's six-step invariant vs what `microcore.js` actually enforces, LIP-1's nine-step verification vs `verifyPassport`'s five.

**C. Demo honesty.** Does `demo.js` do everything its console narration and `replay.js` report claim? Find any claim the code doesn't earn (e.g., what does "witness" mean when the counterparty is the only witness; is the reservation ticket actually enforced anywhere after CHARTER; is anything verified at demo-time but not re-verified at replay-time or vice versa).

**D. Test-coverage gaps.** Which attack from the earlier reviews (window inversion, budget replication, deny bypass, replay, audience confusion) lacks a test? Which module has the weakest coverage? Write the 5 most valuable missing test cases as actual runnable test code.

Rules: cite file and line-anchor text for every finding; severity FATAL/SERIOUS/MODERATE/MINOR; propose the fix as a concrete diff or corrected function; do NOT modify any existing file — deliver your review as a NEW file in `E:\LivingAIAgents\llm-collab\inbox\` named `YYYY-MM-DD_<model>_code-review.md`. End with: 3 things the code does genuinely well, and an implementability-confidence score 1–10 for a stranger reproducing the test suite from scratch.
