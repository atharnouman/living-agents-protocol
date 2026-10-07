# Add LAP to your MCP server in 15 minutes

By the end you will have an MCP server whose sensitive tool **refuses to run** unless the calling agent presents a valid passport, a signature over the exact arguments, and an envelope that permits the action; whose retried calls **never execute twice**; and whose every successful call returns a **server-signed receipt**. One decorator on the server; one helper call on the client. The passport and signature travel in MCP's own request metadata (`_meta`), as the draft MCP extension `io.github.atharnouman/lap-microcore` specifies: [the specification](../../output/lip/LIP-4-mcp-extension-draft.md).

```
examples/mcp-server/
  server.py   # MCP server (FastMCP on mcp 1.x, MCPServer on 2.x); one tool protected by @lap_tool
  client.py   # LAP-aware client: mints a passport, signs calls into _meta, verifies receipts from _meta
```

## 0. What you get (and what you don't)

**Enforced before your tool code runs:**
1. A principal-signed **passport** is presented in the request `_meta`, addressed to *this* server (audience check: a passport minted for another server is refused).
2. The call is **signed by the agent named in the passport** (holder-of-key: a stolen passport is useless without the agent's key).
3. The signature covers the **exact arguments** (canonical JSON) and **this tool's resource**: a signature cannot be replayed with different arguments or against another tool.
4. The **action and resource** are inside the passport's envelope.
5. The **amount** is within the envelope's per-transaction cap, in the declared unit.
6. For a mutating tool, the **signed idempotency key** is claimed before execution: a retry returns the cached receipt, never a second payment, and a concurrent duplicate is refused.

**Not provided by this example** (stated plainly): authentication of the connection (over HTTP, combine with MCP's authorization framework; over stdio the client process is the boundary); a distributed idempotency store (the in-process cache is single-process); and principal *proofing*: the demo passport is `self-asserted`, which is why the decorator offers `min_proof_class`.

## 1. Install (2 min)

```bash
pip install "living-agents[mcp]>=0.4.12"   # the LAP library from PyPI plus the official MCP SDK (1.2+ or 2.x; both run in CI)
# from a checkout instead:  pip install -e ../../lap-python mcp
```

## 2. Protect a tool (one decorator): `server.py`

```python
from living_agents import IdempotencyCache, lap_tool, microcore_extension

PAYMENTS = IdempotencyCache()   # single-process; back it with a shared store in production

@lap_tool(
    mcp,                                   # registers the tool, in place of @mcp.tool()
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount", unit_param="unit",
    server_private_key=SERVER_KEY, server_did=SERVER_DID,   # for signing receipts
    expected_aud=SERVER_ID,                                 # the audience every passport must name
    idempotency_cache=PAYMENTS,                             # a mutating tool
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD") -> dict:
    return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}
```

What the decorator does: it keeps your function's own signature in `tools/list` (no auth argument, no context argument) and marks the tool as requiring the extension in its `_meta`; on each call it reads the extension object from the request `_meta` through the SDK's context, runs the LIP-4 checks before your function, converts a refusal into the SDK's `ToolError` so that the `LAP_ERR_*` reason reaches the caller, and returns a `CallToolResult` whose `_meta` carries the receipt.

The only SDK-major difference is the server import: 2.x renamed `FastMCP` to `MCPServer` and has a server-side extension registry, so `server.py` passes `microcore_extension(SERVER_ID, server_did=SERVER_DID)` to advertise the extension and this server's audience in `server/discover`; 1.x has no registry, and the tool enforces the extension per call anyway.

Two details that matter:
- **`expected_aud` is mandatory.** Without an audience a passport would be valid for every server; the spec calls that fail-open, and the decorator refuses to run that way.
- **Mutating tools pass `idempotency_cache`.** The request must then carry a signed idempotency key; without one it is refused (`LAP_ERR_IDEMPOTENCY`).

Optional server policy, because *a valid passport is identity, not authorization*:
```python
    allowed_issuers=["did:key:z6Mk..."],   # only these principals may call this tool
    min_proof_class="org-validated",       # refuse self-asserted passports
```

## 3. The client mints a passport and signs each call: `client.py`

Two keys: the **principal** (who is responsible) issues the passport; the **agent** (the software) signs calls. The passport says: *this agent, for this principal, may do these things (`envelope`), when talking to this server (`aud`), until this time (`exp`).*

```python
ENVELOPE = {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
            "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}}
PASSPORT = sign_jws({"iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
                     "lap": {"v": 0, "proof_class": "self-asserted", "envelope": ENVELOPE, ...}},
                    principal_key, principal_did + "#key-1", "lap-microcore+jwt")
```

Each call signs an RFC 9421-style base over the canonical JSON of the arguments, the tool's resource, the passport hash and the idempotency key, with the **agent** key, and sends it as request metadata:

```python
meta = {EXTENSION_ID: sign_tool_call(args, RESOURCE, PASSPORT, agent_key, agent_did, NOW, "pay-1001")}
result = await session.call_tool("pay_invoice", args, meta=meta)
receipt = result.meta[EXTENSION_ID]            # verify it with verify_receipt(...)
```

On mcp 2.x the client also declares the extension in its capabilities (`ClientSession(..., extensions={EXTENSION_ID: {}})`) and reads the server's settings from `server/discover`; 1.x has no hook for either, and the server enforces per call regardless.

## 4. Run it (1 min)

```bash
python client.py
```

You should see two paid calls (the second a retry that got the cached receipt back) and five refusals, each with its reason:

```
  PAID     in-scope: $4200 (cap $5000)          -> paid INV-1001 $4200  receipt verified (server did:key:z6Mk...)
  PAID     retry with the same idempotency key  -> paid INV-1001 $4200  receipt verified (server did:key:z6Mk...)
           same receipt, no second payment: yes
  REFUSED  over cap: $6000                      -> LAP_ERR_CAP: amount 6000 exceeds max_per_tx 5000
  REFUSED  tampered: signed $100, sent $4200    -> LAP_ERR_DIGEST: content-digest line mismatch
  REFUSED  wrong unit: EUR                      -> LAP_ERR_CAP: unit mismatch (EUR vs USD)
  REFUSED  no idempotency key                   -> LAP_ERR_IDEMPOTENCY: idempotency_key required for a mutating tool
  REFUSED  no passport at all (plain call)      -> LAP_ERR_AUTH_MISSING: request _meta lacks io.github.atharnouman/lap-microcore
```

Every refusal happens **before** `pay_invoice` runs. The receipt (result `_meta`) is a tripartite line, request hash, response hash, server signature, that both sides can log; the client verifies it against the server's DID with `verify_receipt`.

## 5. Take it to production

- **HTTP transport:** the same decorator works over Streamable HTTP; add MCP's authorization framework for connection authentication. The HTTP-header form of LIP-4 (`LAP-Passport` / `LAP-Signature`, via `@verify_envelope`) remains available for servers that are not MCP.
- **Persist the server key** and publish its DID, so receipts remain verifiable across restarts (a restart is a nap, not a death). Clients pin that DID.
- **Set policy:** `allowed_issuers` and `min_proof_class` for anything touching money or PII.
- **Idempotency store:** back `IdempotencyCache` with a shared store (a unique constraint, `SET NX`) when you run more than one replica.
- **Send every argument explicitly** on mcp 1.x: the SDK hides the raw request from tools, so the reference derives the signed body from the bound arguments; an omitted default would fail the digest check (closed, not open). On 2.x the raw arguments are used.
- **Register births:** `lap-demo/register-genesis.mjs` shows how to put an agent's genesis in Sigstore's public Rekor log.

Spec references: [the MCP extension draft](../../output/lip/LIP-4-mcp-extension-draft.md) (this binding), [LIP-4 Micro-Core](../../output/lip/LIP-4-micro-core-draft.md) (the server invariant), [LIP-3 Scope Algebra](../../output/lip/LIP-3-scope-algebra-v0-draft.md) (what `act`/`res`/`cap` mean), [LIP-1 Passport](../../output/lip/LIP-1-agent-passport-draft.md).
