# Go/no-go review: open budget-enforcement conformance suite (Claude Fable 5.1 subagent, 2026-10-17)

The main session proposed reviving LAP as an open conformance suite for AI spending limits: adversarial scenarios, a runner and per-product adapters, validated first against LiteLLM in about 8-12 hours. This independent review was asked for a plain go/no-go. The text below is the reviewer's, lightly trimmed; the main session's verification follows it.

## 1. Verdict

Not as proposed. The budget problem at LiteLLM is real, frequent and slowly fixed, but the open bugs are overwhelmingly multi-replica cache, Redis and reset-scheduler *state* bugs that a single-instance mock sandbox cannot reproduce. LiteLLM already runs an 82-file spend integration suite, including an AI-generated contract-test programme that found #46363 itself. The nearest prior artifact, AgentShield's MIT "Eval Gym (74 scenarios)", offered explicitly as fixtures for spend-control implementations, got 2 stars and was abandoned within weeks. Half the proposed scenarios (negative/NaN/fractional amounts, mixed currencies) cannot apply to gateways, because the client never supplies an amount; they apply to caller-declared payment caps, which is LAP's own domain. Do the ten-hour version: fix LAP's cap bug, publish the delegation-slice vectors (the 24x trap is the one thing nobody in A2A #2121 has), and let that test demand.

## 2. Findings

| Claim checked | What was found | V/O | Conf. |
|---|---|---|---|
| #26672 open, enforcement bug | Open, 21 comments. The only maintainer reply could not reproduce; the thread's best hypothesis is a stale per-pod cached `max_budget` across replicas sharing Redis; no fix PR. https://github.com/BerriAI/litellm/issues/26672 | V | High |
| #46363 reset leaves key refused | Open, filed 2026-10-14 out of the Devin-generated PR #44736 (https://github.com/BerriAI/litellm/pull/44736, merged 10-14; 8 budget contracts, 2 skipped as bugs). Real, self-found. | V | High |
| #39713, #14457 | Both open: the cache-hit path skips end-user RPM; an early stream disconnect drops usage (open since 2025-09). | V | High |
| Budgets niche? | 87 open issues with "budget" in the title; 75 closed since 2026-07-01, median about 67 days among 13 visible, several `not_planned`. Seven-plus budget levels, reservation before the call on by default, fail-closed modes (https://docs.litellm.ai/docs/proxy/users). Not niche; slow triage. | V | High |
| OpenClaw #42475 | Open, P2, `needs-product-decision`, 26 comments, zero maintainer comments, mostly vendor pitches. No budgets exist to test. | V | High |
| A2A #2121 vectors | 12 comments, all `NONE`. roy-tong's AgentMeasure (218 stars) vectors cover delegation count, depth and cost roll-up, not child-versus-parent caps or windows. elang2 (10-16) favours slices. | V | High |
| Nothing like it exists | No runner-plus-adapters found. But AgentShield (https://github.com/kindrat86/agentshield): "Eval Gym (74 scenarios)", MIT, 2 stars, last push 2026-08-24; arXiv 2606.04056 (https://arxiv.org/abs/2606.04056): a 63-incident catalog of budget overruns; a2a-cost-gateway race test (0 stars). | V | High |
| h2spec/Autobahn precedent | h2spec is single-author, 737 stars, in hyperium/h2 CI. Both test normative RFCs; budgets have no spec. JSONTestSuite (published comparison matrix) is the better model. | V/O | High/Med |
| AI-infra conformance kits | MCP conformance and a2a-tck are organisation-owned; no third-party suite found in any gateway's CI. | V | Med |
| LiteLLM policy | security.md: private GitHub advisory; "Reports that do not include a video demonstrating the exploit will be closed without review"; budget bypass not addressed. CONTRIBUTING: CLA required for code; proxy PRs need a mocked test. | V | High |
| OpenClaw policy | Private GHSA; "parity-only findings are treated as hardening"; cites a "high volume of AI-generated scanner findings"; most features go to plugins. | V | High |
| Client-supplied amounts | `auth_checks.py` compares stored spend against `max_budget`; no request field carries money; cost is computed from tokens. | V | High |

## 3. Answers (condensed)

1. **Real, frequent, slow.** Of twelve open enforcement issues checked (mostly by title), roughly two-thirds are cache, replica, Redis or reset-scheduler bugs; the rest are missed-path logic. A mock sandbox reproduces none of #26672, #46879, #39713 or #46363.
2. **Would maintainers use an external suite? Evidence says no.** LiteLLM generates its own budget contracts. The kits actually used in AI infrastructure are first-party. What moves maintainers is a failing test in *their* harness, with a video, or a public ranking table; the first needs their infrastructure, the second is 40+ hours against real products.
3. **Unique as an assembly, not in its parts**, and the nearest attempt died at 2 stars. Here uniqueness reads as absent demand.
4. **Feasibility.** LiteLLM budgets need Postgres; interrupted streams, concurrency and window rollover need a controllable provider, two workers, Redis and a reset scheduler. Realistic: 25-40 hours, not 8-12. A smarter first target: LAP's own two ports and the #2121 thread.
5. **Policy.** A tenant-exploitable bypass is P2 at LiteLLM: private, video mandatory, no bounty; code PRs need a CLA, issues do not. Operator-side under-enforcement is an ordinary public bug (LiteLLM's own contributors filed #46363 publicly). Neither project bans AI-assisted issues; both filter on reproduction.
6. **"LAP revival" is a rationalization.** A runner would use only LIP-3 §4/§6 (the two-dimensional cap rule, debit in parent-window units); passports, receipts, MEET, liveness and Merkle logs go unused. Standalone, citing LIP-3, would be strictly better.
7. **Better uses:** (a) fix the cap bug and ship negative/NaN/fraction vectors, owed regardless; (b) post a ~12-vector slice checker, including the 24x hourly-children trap, on #2121, scoping out concurrent shared pools: about six hours, no infrastructure, the only audience currently discussing exactly these vectors (no maintainer is in that thread, so treat it as peer review, not adoption); (c) skip OpenClaw and payment SDKs.

## 4. Verdict

A smaller version, at most ten hours. Kill criterion: if by 2026-12-01 no maintainer, draft author or identifiable project owner (elang2, roy-tong, or anyone with association above `NONE`) runs or answers the vectors, park LAP and leave the vectors as the artifact. First step: fix the cap check in both ports (reject `-5`, `NaN`, `999.5`, `true`, `"abc"`, and `max_per_tx > max_cumulative`, per LIP-3 §4's own MUST), regenerate the fuzz digest, and commit those cases as standalone JSON vectors. Do not build the LiteLLM adapter.

## Verified by the main session (same day)

- #26672: the maintainer comment of 2026-06-02 says "I am not able to reproduce this" and asks for a screen recording or script; a later comment asks reporters to reproduce on the latest release. Confirmed.
- PR #44736 "test(integration): cover budgets_spend endpoint contracts", opened by `devin-ai-integration[bot]`, merged 2026-10-14. Confirmed.
- AgentShield: 2 stars, MIT, last push 2026-08-24, README section "Eval Gym (74 scenarios)". Confirmed.
- LiteLLM security.md requires a video with every report; budgets are not mentioned. Confirmed.
- arXiv 2606.04056 exists: "Token Budgets: An Empirical Catalog of 63 LLM-Agent Budget-Overrun Incidents, with an Affine-Typed Rust Mitigation as a Case Study". Confirmed.
- AgentMeasure has 218 stars. Confirmed.
- **Nuance:** in the 2026-10-16 comment on #2121, elang2 favours roy-tong's shape (a), "a child given a slice", and asks one participant for "the test cases you offered"; it is not a general call for vectors, though elang2 is drafting the proposal and reads other people's vectors closely.
- Not re-checked: the 82-file count, the closure statistics, the two-thirds split by bug type, the Postgres requirement.
