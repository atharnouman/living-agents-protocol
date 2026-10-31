# Review brief, 2026-11-01: model-retry fixture, spec note, and two draft public comments

You are an independent reviewer. Find what is wrong. Do not approve out of politeness, and do not take any claim in these files on trust. Nothing here has been published.

**Hard limits.** Read-only on the repository except for your one report file. Scratch work goes in your own temporary directory. Do not commit, push, post, or sign in anywhere. GitHub reads go through the public unauthenticated API. Do not download or run third-party repositories (read terminalstate's over the web if you need to).

## Background

Living Agents Protocol (LAP) is a one-author open-source project with no adoption. Its MCP binding is a draft extension: a principal-signed passport, an agent signature over the call, and, for a mutating tool, a signed idempotency key carried in `params._meta`. The model never sees the key. The server recognises the key after the passport and signature checks.

Three public threads matter. Read them in full:
- https://api.github.com/repos/modelcontextprotocol/modelcontextprotocol/issues/3394/comments?per_page=100 (the last five comments above all, from terminalstate, arjun2075 and yaredmengistu04-arch; Ben-Home's was edited recently)
- https://api.github.com/repos/modelcontextprotocol/financial-services-interest-group/issues/17/comments?per_page=100 (the last eight comments above all; the author's own comments are by atharnouman)
- https://api.github.com/repos/modelcontextprotocol/financial-services-interest-group/issues/19/comments (Peder's stated preferences about use-case files and about naming specific projects)

Notes of the group's 29 October call: https://docs.google.com/document/d/19HwCw7i4k-omABGnRYGGuLdMJNXQc3rs_QRgJxPhQU8/export?format=txt (section "FSIG Meeting — October 29, 2026").

## What to review

Repository root: `E:\LivingAIAgents`.

1. `examples/model-retry/run.py` and `examples/model-retry/README.md` (new). Run it: `cd examples/model-retry && python run.py`. It has been run on mcp 1.29.1 and 2.3.0; a venv for 2.3.0 is not provided, so make your own only if you need it.
2. `git diff` of `output/lip/LIP-4-mcp-extension-draft.md` (a security bullet, an open question, a change-log note), `.github/workflows/ci.yml`, `README.md`.
3. `outreach/MCP-3394-comment-recut-2026-11-01.md`: the text after the `---` line would be posted on issue 3394. The earlier approved text it replaces is `outreach/MCP-3394-comment-2026-10-28.md`.
4. `outreach/FSIG-17-reply-2026-11-01.md`: the text after the `---` line would be posted on issue 17.

Reference code: `lap-python/living_agents/mcp_extension.py`, `mcp_middleware.py`, `microcore.py`; the draft `output/lip/LIP-4-mcp-extension-draft.md`.

## Questions

A. **Is the fixture honest?** Does each number come from the real SDK and middleware, or could any be an artifact of the harness (the relay, the timeout selection, how `present` classifies an answer, the module-level `CURRENT`, the scripted model)? Does a table row claim more than the code shows? Would a failure in the middleware actually change the output? Try breaking something in a scratch copy to see.

B. **Is "client resolves first" sound, or does it hide a danger** beyond the two limits stated (restart, and running a stale call)? Think about concurrency, several calls on one tool, a refusal classed as definite that is not, a re-present under replaced authority, and whether the classification list `AFTER_RECOGNITION` matches section 4.1 and 4.3 of the draft. Is it a fair thing to put in a security section?

C. **Are the claims in the spec note, README and both comments true?** Check each against the code and the threads: what terminalstate reported, what arjun2075 asked, what Peder said, which four cases were suggested and by whom, what the reference does and does not do. Check "Peder's point holds on my side" in particular.

D. **Is each comment right for its venue?** Length, focus, whether it adds anything the thread lacks, whether it repeats someone, whether it reads as promotion after what the call notes and Peder said. Should it be posted at all? Should it be cut further? Is there a better single venue? Should it answer yaredmengistu04-arch? Give one verdict on each comment: post as is, post with named changes, or do not post.

E. **Order and timing.** The earlier reviewers warned against two same-day comments in two MCP repositories. King Yew's draft is due by 12 November. Recommend an order, or recommend only one.

## Report

Write your report to the file named in your instructions. At most eight findings, most important first. Each finding has the exact file and text, why it is wrong, and exact replacement wording. Separate what you verified by running or reading from what is judgement. End with your verdicts for D and E. If you find nothing in an area, say so and name the weakest remaining sentence.
