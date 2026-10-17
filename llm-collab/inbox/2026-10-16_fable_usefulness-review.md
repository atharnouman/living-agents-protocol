# Usefulness review (Claude Fable 5.1, 2026-10-16): "make it really useful; it should solve a real problem"

*Source: a read-only subagent on Claude Fable 5.1. Report condensed below: the verdict and recommendations as delivered, the ranked table summarized, its source links listed in this note. Checked the same day: lap-git is a wrapper (`lap-git/lap-git.mjs` line 131) and no hook is installed; the Karakun write-up (151 and 723 files deleted on two `main` branches; a written rule failed in 2 of 7 runs; branch protection plus a pre-push hook as the fix; the force push was `--force-with-lease` and Git rejected it), the Cursor Plan Mode thread (about 70 files; staff: "a critical bug in Plan Mode constraint enforcement"), The Register's Gemini report (28,745 lines), HN 47911524 (860 points; the title says production database), HN 47182387 (99 points), HN 49861047 (84 points), anthropics/claude-code #3275 (closed 2025-07-10; the "by design" wording was not checked) and #90450 (open since 2026-08-28), the Claude Code sandboxing page (off by default; macOS, Linux, WSL2; native Windows unsandboxed; file tools, MCP servers and hooks outside it), damage-control (480 stars), Vectimus (38 stars), mcp-guardian (archived). Not checked: the LiteLLM, OpenRouter, Docker, Pomerium, Stripe, GitHub rulesets and Help Net Security pages, the tianpan.co post, the MCP tool-scopes page. AgentGuard (2025-07-31) and #3275 fall outside the requested 12 months.*

*Correction found later the same day (GitHub search and the projects' own READMEs): the claim that nothing is tool-agnostic at the commit level is wrong. sembl (executor-neutral scope gate on the agent's real diff, pre-commit and GitHub Action), chock (policies compiled into git hooks, CI gates or each agent's pre-tool hook) and overscope (scope creep against Claude Code or Codex sessions, as a pre-commit gate) already do commit- or CI-level scope checks for several agents; cc-safety-net (1,638 stars) blocks destructive commands for Claude Code, Codex, Cursor, Gemini CLI and Copilot CLI on Windows, macOS and Linux; Vectimus covers five coding agents on Windows with signed receipts in its own log; block/aittributor adds unsigned agent co-author trailers. What none of the READMEs read claims is a signed authorization carried in the commit itself.*

---

## Verdict

Park the protocol; ship one tool. Last-12-month evidence of real, repeated pain is almost entirely about **AI coding agents destroying or overstepping files and git history**, not stranger agents, passports or liveness. LAP has one asset that touches that pain, `lap-git`, and today it is a wrapper command (`git commit -q -F` inside `lap-git/lap-git.mjs`), not a hook: an agent running plain `git commit` bypasses it, and no hook is installed even in this repo (`.git/hooks` holds only samples). Turn it into git hooks plus a CI verifier for any agent, then measure. Everything else has no demand signal: 0 stars, 0 forks, 0 issues nine days after launch; npm/PyPI downloads the owner's own log attributes to mirrors; the A2A proposal has one outside review and no maintainer reply.

## Ranked candidates (summary of the delivered table)

1. **Coding agent commits, pushes or deletes outside its task** (solo developers and small teams on Claude Code, Cursor, Codex, Gemini CLI). Evidence: the Karakun write-up, the Cursor Plan Mode thread, HN 47911524 and 47182387, The Register's Gemini report, claude-code #3275 and #90450. Existing options: the Claude Code sandbox, path rules and hooks (vendor-specific); damage-control (Claude Code only); Vectimus (Cedar hooks with signed receipts); GitHub rulesets. Gap: nothing tool-agnostic, commit-level and verifiable from the commit alone. LAP fit 4/5; confidence high.
2. **Runaway LLM API spend.** Evidence: HN 49861047, HN 44742710. LiteLLM and OpenRouter already provide hard budgets; LAP is not on the LLM call path. Fit 1/5.
3. **Retries re-executing mutating tools.** Pattern write-ups only, no named incident. LAP's signed idempotency key fits but is single-process. Fit 4/5; confidence low.
4. **Amount caps and cumulative budgets on mutating MCP tools.** Docker MCP Cedar policy, ToolHive, Pomerium, agentgateway, ContextForge and Stripe Issuing cover much of it; LAP checks per-transaction caps only at runtime, and `lap_tool` refuses any client without a passport, so stock MCP clients cannot call it. Fit 3/5; confidence low to medium.
5. **Tamper-evident tool-call logs for compliance.** Regulation exists, developer demand not shown. Fit 3/5; confidence low.

## Smallest useful products

**A. `lap-git` as hooks (top pick).** An installer writes three hooks: pre-commit refuses staged paths outside the envelope when an agent is detected (environment variables such as `CLAUDECODE` and `CODEX_THREAD_ID`); commit-msg appends the existing LAP trailers and tree signature; pre-push refuses agent force-pushes and deletions of most of the tree. `lap-git verify` ships as a GitHub Action that fails a PR containing an agent commit outside its envelope; human commits pass untouched. Honest limit: `--no-verify` and a readable key file make the local hook a seatbelt; the enforcement point is CI or pre-receive, paired with GitHub's "require signed commits".

**B. `lap-fence`, an MCP stdio proxy (only if A finds users):** per-call caps, a daily cumulative ledger in SQLite, retry dedupe, hash-chained receipts, no client or server changes.

**C. Budget caps on LLM spend: do not build.**

## Hours (top pick)

Reused: `crypto-util.js`, `jws.js`, `verifyMicroCorePassport`, `pathSubsumes`, the signing base and `verify` in `lap-git.mjs`. New: hook installer and three hooks (12 h); agent detection and passport selection (3 h); Windows paths, CRLF, renames (4 h); GitHub Action (4 h); packaging (3 h); README with a short refusal demo (4 h). About 30 to 35 hours.

## First three users

The people who already described this pain in public: the Karakun author, the claude-file-recovery author, the Cursor Plan Mode poster. Show the refusal demo; ask which path their agent last touched that it should not have, whether they will run it for a week and report every refusal, and what would make them uninstall it. Comment on claude-code #3275 and #90450 with the hook as a concrete workaround, never as a pitch. Count refusals reported, not stars.

## Stop doing

Standards filings and their upkeep, audit-record interop, restamping and Bitcoin anchors, launch-log and runbook maintenance, essay and paper corrections, Python parity work, new review rounds. Freeze the spec at v0.4.10; keep CI green.

## Blunt answer and the three-week test

A real but narrow problem: bounded, attributable commits by coding agents. Worth about a month of evenings as a utility, not a protocol; a vendor could close the gap with one feature, so move fast and stay small. Test, decided in advance: (1) three strangers install the hooks and report at least one refusal; (2) one named person or one agent-tool maintainer keeps it running for two weeks; (3) at least one unsolicited issue or PR. Zero of three: archive `lap-git` too and leave the repository as a reference.
