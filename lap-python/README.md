# Living Agents Protocol (LAP) — Python Reference & FastMCP Middleware

Official Python implementation of the **Living Agents Protocol (LAP)**:
- **LIP-1 Agent Passport**: Ed25519 JWS identity documents with responsible-human principal binding.
- **LIP-3 Scope Algebra (v0.2)**: Capability attenuation, DAG action lattices, resource prefix matching, and integer budget conservation.
- **LIP-4 Micro-Core**: FastMCP middleware for server-side authorization, RFC 9421 request signature validation, and signed tripartite audit receipts.

Zero runtime dependencies beyond `cryptography`.

---

## Installation

Not yet published to PyPI — install from the repository:

```bash
cd lap-python
pip install -e ".[dev]"
```

---

## FastMCP Tool Server Integration (3 Lines)

> **Complete runnable example (server + client, verified in CI):** [`../examples/mcp-server/`](../examples/mcp-server/) — the 15-minute tutorial.

Wrap any MCP tool function with `@verify_envelope` to enforce authorization bounds and emit tripartite receipts:

```python
from mcp.server.fastmcp import FastMCP
from living_agents import verify_envelope
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

mcp = FastMCP("billing-tools")

# Server Ed25519 signing key for receipts
server_key = Ed25519PrivateKey.generate()
server_did = "did:key:z6MknvBY..."

@mcp.tool()
@verify_envelope(
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount",
    unit_param="unit",
    server_private_key=server_key,
    server_did=server_did,
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD") -> dict:
    """Pay a vendor invoice up to authorized envelope limits."""
    return {"status": "paid", "invoice": invoice, "amount": amount}
```

When an agent invokes `pay_invoice`:
1. `LAP-Passport` is verified against the principal's `did:key`.
2. RFC 9421 `LAP-Signature` is validated over the canonical body digest.
3. Envelope spending cap is enforced (`amount <= max_per_tx`).
4. An immutable `_lap_receipt` is signed by the server and returned to the caller.

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
