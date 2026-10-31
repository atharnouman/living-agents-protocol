# Review brief: draft comment for MCP spec issue 3394 (2026-10-28)

Two independent, read-only reviews are asked for (Sonnet 5.5 and Opus 5.5), each written to its own file in this folder. The owner decides; the reviewer's text is advice.

## What is being reviewed

`E:\LivingAIAgents\outreach\MCP-3394-comment-2026-10-28.md`: a draft comment on https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3394, answering four questions arjun2075 (the issue's author, who is assembling executable vectors for a retry-identity SEP that ndreno drafts) put to another commenter on 2026-10-26: how a client obtains a retry identity and carries it across a lost response, whether it exists before the first call, whether an unmodified MCP client works, how support is discovered, and how a stored result is told from an unknown outcome. The draft answers from the shipped reference (libraries 0.4.14, released 2026-10-28) and states its limits.

## Context the reviewer must read first

1. The whole thread, saved verbatim (issue body and 41 comments, authors and dates): `C:\Users\DELL\AppData\Local\Temp\claude\E--LivingAIAgents\1249a6be-fd55-4e13-8248-38de49debdca\tool-results\bt6b3rwrp.txt` (31 KB). Note its conventions: narrow claim boundaries; executed results distinguished from "contributor-reported" and from "proposed vectors"; effect count and result disclosure checked separately; the immediate non-normative guidance kept separate from the SEP; AI-use disclosure lines; the author of the thread labels and scopes every contribution.
2. The extension draft at the tag: `E:\LivingAIAgents\output\lip\LIP-4-mcp-extension-draft.md` (sections 2.2 to 2.5, 3.2, 4.1, 4.3, 5.6, 7, 8).
3. The code and tests the claims rest on: `E:\LivingAIAgents\lap-python\living_agents\mcp_middleware.py`, `mcp_extension.py`, `microcore.py`; `E:\LivingAIAgents\lap-python\tests\test_recognition_order.py`, `test_review_probes_0414.py`, `test_idempotency_recovery.py`, `test_replay_vectors.py`; the vectors `E:\LivingAIAgents\output\lip\test-vectors\microcore-replay-vectors.json`; the tutorial `E:\LivingAIAgents\examples\mcp-server\README.md`, `server.py`, `client.py`.
4. For consistency, the comment posted this morning on the Financial Services IG issue 17 (same author, same facts): `E:\LivingAIAgents\outreach\FSIG-17-reply-2026-10-28.md`. The two texts must not contradict each other.

## What to check

- **Every factual claim** in the draft against the code, the tests and the draft at the tag. Run the Python suite if useful (`cd E:\LivingAIAgents\lap-python && python -m pytest -q`). Quote the line that supports or contradicts each claim you dispute.
- **Does it answer the four questions**, in the author's terms, without pitching the project? The project's rule is code-first: the comment should be useful to the SEP whether or not anyone adopts the extension.
- **Claim boundary.** Anything that overstates (adoption, exactly-once, fault injection, platform coverage) must go. Anything the reference does not do should be stated or omitted, never implied.
- **The thread's own cases**: ryjen's disclosure vector, arjun2075's "no fresh entry on an authorization change" and the different-tenant rule, the expiry and retention points (madeinplutofabio, arjun2075), Majny's intentional repeat and effect-then-error, the identity-survives-retry point. Does the draft map to them correctly and only where the code supports it?
- **Tone and length.** The thread's substantive comments run about 1,000 to 3,000 characters; draft 1 is about 3,900. Propose a version under about 3,000 characters that loses no answer. Flag @-mentions beyond arjun2075 (the draft names ryjen, madeinplutofabio and Majny without @).
- **Timing and venue.** Should this be posted at all, now, given that ndreno and arjun2075 are drafting the SEP, and that the author's related comment on issue 17 went up this morning? Say so plainly if you think it should wait or be shortened to a pointer.
- **Risks.** Anything in the text that could be read as a claim about MCP's SDKs, about other commenters' tools, or about the maintainers' intent.

## What to hand back

A file `E:\LivingAIAgents\llm-collab\inbox\2026-10-28_mcp-3394-comment-review-<model>.md` with: (1) a verdict: post as is, post with the changes listed, or do not post; (2) blocking issues, each with the evidence; (3) line edits; (4) your trimmed version of the comment, complete, ready to paste; (5) anything you checked and found correct, briefly. Do not modify any other file. Do not post anything anywhere.
