"""A minimal MCP server whose payment tool is protected by LAP Micro-Core.

Run it directly (stdio transport):  python server.py
Or let client.py spawn it.

What the decorator enforces on EVERY call, before your code runs:
  1. a principal-signed LAP passport is presented, addressed to THIS server (audience);
  2. the call is signed by the agent named in that passport (holder-of-key);
  3. the signature covers the exact arguments the server bound (canonical JSON);
  4. the action and resource are inside the passport's envelope;
  5. the amount is within the envelope's per-transaction cap, in the right unit.
On success the result carries a tripartite receipt signed by this server.
"""
import functools
import logging

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Both majors of the official SDK: mcp 2.x renamed FastMCP to MCPServer (mcp.server.mcpserver);
# the @server.tool() decorator and server.run() are unchanged, so the LAP decorator below is too.
try:
    from mcp.server.mcpserver import MCPServer as Server   # mcp >= 2
    _SERVER_KW = {}
except ImportError:
    from mcp.server.fastmcp import FastMCP as Server        # mcp 1.x
    _SERVER_KW = {"log_level": "WARNING"}
try:
    from mcp.server.mcpserver.exceptions import ToolError   # mcp >= 2
except ImportError:
    from mcp.server.fastmcp.exceptions import ToolError     # mcp 1.x

from living_agents import did_key_from_raw_public_key, verify_envelope

logging.basicConfig(level=logging.WARNING)  # keep the demo output clean on both majors
mcp = Server("billing-tools", **_SERVER_KW)


def lap_refusals_as_tool_errors(fn):
    """The LAP decorator raises a plain ValueError (it knows nothing about the SDK). The SDK
    reports a ToolError's message to the caller but deliberately hides any other exception as a
    generic 'error executing tool', so convert here: the caller sees the LAP_ERR_* reason and
    nothing else about the server leaks."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            raise ToolError(str(e)) from e
    return wrapper

# This server's own identity: it signs receipts. Generated per run for the demo;
# persist it (and publish the DID) in production so receipts stay verifiable.
SERVER_KEY = Ed25519PrivateKey.generate()
SERVER_DID = did_key_from_raw_public_key(SERVER_KEY.public_key().public_bytes_raw())

# The audience every passport MUST name. A passport minted for another server is refused.
SERVER_ID = "did:web:tools.example.com"


@mcp.tool()
@lap_refusals_as_tool_errors
@verify_envelope(
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount",
    unit_param="unit",
    server_private_key=SERVER_KEY,
    server_did=SERVER_DID,
    expected_aud=SERVER_ID,
    # Optional server policy (spec LIP-4 hardening rule F1 — identity is not authorization):
    #   allowed_issuers=["did:key:z6Mk…"],   # only these principals may call
    #   min_proof_class="org-validated",     # refuse self-asserted passports
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD", lap_auth: dict | None = None) -> dict:
    """Pay a vendor invoice. Refused unless the caller presents a valid LAP passport whose envelope permits it."""
    # Your business logic — it only runs after every check above passed.
    return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}


if __name__ == "__main__":
    mcp.run()
