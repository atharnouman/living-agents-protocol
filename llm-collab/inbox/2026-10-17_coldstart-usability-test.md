# Cold-start usability test (fresh agent, 2026-10-17)

**Method.** A fresh agent with no project context played a Python developer who builds MCP servers and found the repository on GitHub. It worked in a throwaway virtual environment, installed `living-agents` 0.4.12 and `mcp` 2.3.0 from PyPI, read only the public README, tutorial and linked docs, and signed in nowhere. It went through three phases: a first impression from the top of the README, the 15-minute MCP tutorial followed literally, and its own protected tool written in 20 minutes without copying the example. (It also saw a one-line memory index naming the project, loaded automatically; it says it did not use it, and that line explains nothing about usage.)

## First impression (top of the README only)

It read the project as identity, a responsible human, bounded authority, liveness and audit receipts for always-on agents, with an MCP add-on. It would give it 15 minutes "on the strength of `pip install "living-agents[mcp]"`". Hesitations: a metaphor-heavy pitch with no code above the fold; "spec v0.4.10 (draft)" and packages nine days old; a "Bitcoin-timestamped" badge that reads as crypto-flavoured; review and test-count badges that do not say what the developer gets. "If the next screen doesn't show me a 5-10 line 'protect this MCP tool' snippet, I'd probably bounce."

## Tutorial

Works as documented: two paid calls (the second a cached retry) and five refusals with the documented reasons. Agent time 2 min 43 s; estimated human time 15-20 minutes. Friction: the tutorial is linked only from the repository map; it never says how to get `server.py` and `client.py` after `pip install`; jargon (did:key, did:web, JWS typ, act/res/cap).

## Own code

Reached a protected `transfer(to, amount)` with a verified receipt and a cap refusal (estimated human time 25-35 minutes), but only by borrowing key, DID and receipt-verification code from the example files: neither the tutorial nor the docstrings show them. The first run failed with `LAP_ERR_CAP: unit mismatch (None vs USD)` because the tool has no unit parameter.

## Friction, ranked

1. No instructions for getting the example files after `pip install` (add a clone line or ship `python -m living_agents.demo`).
2. Snippets in tutorial sections 2-3 are not runnable: `mcp`, `SERVER_KEY`, `SERVER_DID`, `SERVER_ID`, `principal_did`, `agent_key` and `NOW` are undefined; key and DID creation is never shown; the passport claims contain a literal `...`.
3. "One helper call" on the client understates the work: hand-built JWT claims, a `kid` and `typ`, seven positional arguments to `sign_tool_call`, five arguments plus `jcs()` to verify a receipt. Suggested helpers: `new_identity()`, `mint_passport(...)`, `receipt_ok(result, args)`.
4. Tools without a unit are refused with no hint (allow `lap_tool(..., unit="USD")` and document it).
5. Configuration errors surface only at call time and are vague (a missing `expected_aud` or a mistyped `amount_param` is accepted at startup). Async tools are refused with `TypeError: lap_tool supports synchronous tool functions only`, which the tutorial does not mention.

## Verdict (the agent's)

It would use the library "only where I write both the agent and the server ... Not for servers that people reach from Claude Desktop or Cursor." Biggest barrier: standard MCP hosts cannot call protected tools (`LAP_ERR_AUTH_MISSING`), the extension "has not been submitted anywhere", and nothing says where the principal key lives in production or who issues a new passport when a ten-minute one expires. The one change: a complete copy-paste quickstart built on helpers that runs straight from the pip package.

## Reproduced by the main session (same day)

| Finding | Python 0.4.12 | Node | Spec |
|---|---|---|---|
| Cap check accepts negative amounts (-5, -1,000,000,000) | yes; end to end, -500,000 executed under a 1,000 cap | yes | LIP-4 §2 step 4 says only `amount <= max_per_tx`; LIP-3 F5/F8 intend bounded, exact-integer amounts |
| Cap check accepts NaN, -inf, a fraction (999.5) and boolean `True`; Node also accepts `"abc"` | yes | yes | as above |
| Same idempotency key with different, properly signed arguments returns the first call's result without error | yes (one execution) | not tested | LIP-4 §2 step 5 returns the cached receipt; the IETF idempotency-key draft says SHOULD reject (422) |
| A one-hour-old signature `created` is accepted while the passport is valid | yes | not tested | MAY reject (extension draft); hardening only |
| Unregistered verb `finance:transfer` accepted | yes (`is_registered_verb` is False) | not tested | MUST list registered actions (LIP-3, extension draft) |
| `cap_is_valid()` rejects the tutorial's Micro-Core cap | yes (it requires `max_cumulative`); Micro-Core applies no cap schema check | not tested | LIP-3 F8 makes the schema check a MUST before arithmetic |

The cap result is the serious one: the per-transaction cap is the tutorial's headline guarantee against a misbehaving agent, and it does not bound negative or non-integer amounts. Six AI review rounds and both test suites missed it; ten minutes of hands-on use found it.
