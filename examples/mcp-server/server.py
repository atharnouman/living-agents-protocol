"""A minimal MCP server whose payment tool is protected by LAP Micro-Core, bound to MCP as the
extension io.github.atharnouman/lap-microcore (draft: output/lip/LIP-4-mcp-extension-draft.md).

Run it directly (stdio transport):  python server.py
Or let client.py spawn it.

What the extension enforces on EVERY call, before your code runs:
  1. the request _meta carries a principal-signed LAP passport addressed to THIS server (audience);
  2. the call is signed by the agent named in that passport (holder-of-key);
  3. the signature covers the exact tool arguments (canonical JSON) and this tool's resource;
  4. the action and resource are inside the passport's envelope;
  5. the amount is within the envelope's per-transaction cap, in the right unit;
  6. the signed idempotency key is claimed before execution: a retry gets the cached receipt,
     never a second payment.
On success the result _meta carries a tripartite receipt signed by this server.
"""
import logging

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import IdempotencyCache, did_key_from_raw_public_key, lap_tool, microcore_extension

# This server's own identity: it signs receipts. Generated per run for the demo;
# persist it (and publish the DID) in production so receipts stay verifiable.
SERVER_KEY = Ed25519PrivateKey.generate()
SERVER_DID = did_key_from_raw_public_key(SERVER_KEY.public_key().public_bytes_raw())

# The audience every passport MUST name. A passport minted for another server is refused.
SERVER_ID = "did:web:tools.example.com"

logging.basicConfig(level=logging.WARNING)  # keep the demo output clean on both majors

# Both majors of the official SDK. mcp 2.x renamed FastMCP to MCPServer and has a server-side
# extension registry, so it advertises the extension (and this server's audience) in its
# capabilities; mcp 1.x has no such registry, and the tool enforces the extension per call anyway.
try:
    from mcp.server.mcpserver import MCPServer                       # mcp >= 2
    mcp = MCPServer("billing-tools", extensions=[microcore_extension(SERVER_ID, server_did=SERVER_DID)])
except ImportError:
    from mcp.server.fastmcp import FastMCP                           # mcp 1.x
    mcp = FastMCP("billing-tools", log_level="WARNING")

# Mutating tools claim (agent, idempotency key) before executing. This in-process cache is
# single-process only: back it with a shared store in production (LIP-4 F6).
PAYMENTS = IdempotencyCache()


@lap_tool(
    mcp,                                      # registers the tool, in place of @mcp.tool()
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount",
    unit_param="unit",
    server_private_key=SERVER_KEY,
    server_did=SERVER_DID,                    # for signing receipts
    expected_aud=SERVER_ID,                   # the audience every passport must name
    idempotency_cache=PAYMENTS,               # a mutating tool: the signed idempotency key is mandatory
    # Optional server policy (LIP-4 rule F1: identity is not authorization):
    #   allowed_issuers=["did:key:z6Mk..."],  # only these principals may call
    #   min_proof_class="org-validated",      # refuse self-asserted passports
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD") -> dict:
    """Pay a vendor invoice. Refused unless the caller presents a valid LAP passport whose envelope permits it."""
    # Your business logic: it only runs after every check above passed.
    return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}


if __name__ == "__main__":
    mcp.run()
