# Living Agents Protocol (LAP) — Python Reference & FastMCP Middleware

Official Python implementation of the **Living Agents Protocol (LAP)**:
- **LIP-1 Agent Passport**: Ed25519 JWS identity documents with responsible-human principal binding.
- **LIP-3 Scope Algebra (v0.4)**: capability attenuation, a registered action DAG, segment-wise resource matching with terminal-only wildcards, two-dimensional caps, and exact-integer budget conservation.
- **LIP-4 Micro-Core**: server-side authorization middleware, RFC 9421 request signature validation, signed tripartite receipts, and the MCP extension binding `io.github.atharnouman/lap-microcore` (passport and call signature in request `_meta`, receipt in result `_meta`, idempotent retries) for the official MCP SDK, 1.x and 2.x.

Zero runtime dependencies beyond `cryptography`.

---

## Installation

```bash
pip install living-agents            # the library (one dependency: cryptography)
pip install "living-agents[mcp]>=0.4.12"   # plus the official MCP SDK, 1.x or 2.x (0.4.12 adds the MCP extension binding)
```

From a checkout, for development:

```bash
cd lap-python
pip install -e ".[dev]"
```

---

## MCP tool server integration (one decorator)

*Works with `FastMCP` (mcp 1.x) and `MCPServer` (mcp 2.x) alike; the MCP SDK is imported lazily, so `import living_agents` stays dependency-free.*

> **Complete runnable example (server + client, verified in CI on both SDK lines):** [`../examples/mcp-server/`](../examples/mcp-server/), the 15-minute tutorial. **Specification:** [the MCP extension draft](../output/lip/LIP-4-mcp-extension-draft.md) (`io.github.atharnouman/lap-microcore`).

```python
from mcp.server.fastmcp import FastMCP          # mcp 1.x; on mcp 2.x: from mcp.server.mcpserver import MCPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from living_agents import IdempotencyCache, did_key_from_raw_public_key, lap_tool

mcp = FastMCP("billing-tools")
server_key = Ed25519PrivateKey.generate()                 # signs receipts; persist it in production
server_did = did_key_from_raw_public_key(server_key.public_key().public_bytes_raw())

@lap_tool(
    mcp,                                                  # registers the tool, in place of @mcp.tool()
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount",
    unit_param="unit",
    server_private_key=server_key,
    server_did=server_did,
    expected_aud="did:web:tools.example.com",             # the audience every passport must name
    idempotency_cache=IdempotencyCache(),                 # a mutating tool: a signed idempotency key is mandatory
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD") -> dict:
    """Pay a vendor invoice up to authorized envelope limits."""
    return {"status": "paid", "invoice": invoice, "amount": amount}
```

When an agent calls `pay_invoice`, before your function runs:
1. the passport in the request `_meta` is verified against the principal's `did:key`, its audience and its validity window;
2. the agent's RFC 9421 signature is verified over the canonical arguments, this tool's resource and the passport hash;
3. the action, the resource and the spending cap (`amount <= max_per_tx`, in the right unit) are checked against the envelope;
4. the signed idempotency key is claimed, so a retry returns the cached receipt instead of paying twice.

A refusal reaches the caller as a tool error with its typed `LAP_ERR_*` reason. A success returns a `CallToolResult` whose `_meta` carries a receipt signed by the server; the client verifies it with `verify_receipt`. The transport-independent decorator `@verify_envelope` remains available for servers that carry the passport and signature in HTTP headers (LIP-4).

---

## Running Cross-Language Tests

Run the complete test suite:

```bash
pytest tests/ -v
```

The test suite validates byte-for-byte reproducibility against the shared deterministic test vectors (`output/lip/test-vectors/vectors.json`), ensuring full interoperability with the Node.js reference implementation.

---

## License

Apache-2.0. Part of the [Living Agents Protocol](../README.md) project.
