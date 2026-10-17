# Cold-start retest after 0.4.13 (fresh agent, 2026-10-17, afternoon)

**Method.** Same setup as the morning test: a fresh agent with no project context, playing a Python developer who builds MCP servers, in a throwaway virtual environment, installing from PyPI (living-agents 0.4.13, mcp 2.3.0) and reading only the public README and tutorial as published after the morning's fixes. It did not open the example files during the own-code phase. Three phases: first impression, the tutorial, its own `transfer(to, amount)` tool with no unit argument.

## What changed since the morning

- **First impression:** it now reads the project correctly from the top of the README (a passport-gated tool guard with signed receipts), identifies the audience (people who control both sides), and says the status statement makes it "evaluate yes, depend no"; the candour counts as a plus.
- **Tutorial:** every step ok; the clone instruction worked; the ten PAID/REFUSED lines matched the docs line for line (the only difference is the elided server DID in the docs).
- **Own code:** first accepted, receipted call about 3 minutes into the phase, without opening the example files; `unit="USD"` worked for the unit-less tool; a misspelled `amount_param` failed at startup with the documented `TypeError`; a negative amount was refused before the tool ran.

## Friction that remained (five, ranked by the agent)

1. Key and DID generation never shown in the tutorial (found via `living_agents.__all__`).
2. `verify_receipt` is annotated `-> bool` but raises `ValueError` on a bad DID; it crashed the agent's client once.
3. A capped tool with neither `unit_param` nor `unit` is not a startup error; every call fails with `unit mismatch (None vs USD)`.
4. No code for how a 2.x client learns `server_did` and `aud` (`initialize().capabilities.extensions` is `None` on 2.x; the settings come from `server/discover`).
5. The tutorial does not say `client.py` launches `server.py` itself, and never gives the 2.x import `from mcp.server import MCPServer`.

## Verdict (the agent's)

Use at prototype level for internal agent-to-tool pipelines where one party writes both sides (payout, refund, purchase tools); not for anything called from Claude Desktop or Cursor. Biggest barrier unchanged: a protected tool needs a LAP-aware client. Second: one author, draft spec, may be parked. The one change: make tutorial sections 2 and 3 a complete, copy-pasteable server and client in the text.

## Fixed the same afternoon

All five: keys and DIDs in sections 2 and 3; `verify_receipt` documented as returning True or raising, with the `try`/`except` shown; the missing-unit case made a startup `TypeError` (from 0.4.14; documented for 0.4.13); the `server/discover` line and DID pinning added; the subprocess sentence and the 2.x import added. The passport snippet's `...` is gone.
