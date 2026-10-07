"""A LAP-aware MCP client for the io.github.atharnouman/lap-microcore extension: mints an agent
passport + envelope, signs each tool call into the request _meta, and verifies the receipt that
comes back in the result _meta. Spawns server.py over stdio.

Run:  python client.py
"""
import asyncio
import inspect
import json
import sys
import time
from importlib.metadata import version as _pkg_version
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from living_agents import (
    EXTENSION_ID, did_key_from_raw_public_key, jcs, sha256_hex, sign_jws, sign_tool_call, verify_receipt,
)

if hasattr(sys.stdout, "reconfigure"):            # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER_ID = "did:web:tools.example.com"           # must match the server's expected audience
RESOURCE = "mcp://tools.example.com/billing/pay"  # the tool's declared resource (also in its _meta)
HERE = Path(__file__).parent


def keypair():
    k = Ed25519PrivateKey.generate()
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


# Two identities: the PRINCIPAL (the human/org who is responsible) issues the passport;
# the AGENT (the software that acts) signs each call. Authority flows principal -> agent.
principal_key, principal_did = keypair()
agent_key, agent_did = keypair()

# The envelope: what this agent may do unsupervised. Anything outside it is refused.
ENVELOPE = {
    "act": ["finance:pay"],
    "res": "mcp://tools.example.com/billing/**",
    "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"},
}
NOW = int(time.time())
PASSPORT = sign_jws(
    {
        "iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
        "lap": {"v": 0, "proof_class": "self-asserted",
                "constitution_hash": sha256_hex("Act only within the signed envelope; escalate on ambiguity.\n"),
                "envelope": ENVELOPE},
    },
    principal_key, principal_did + "#key-1", "lap-microcore+jwt",
)


def lap_meta(args: dict, idempotency_key: str | None) -> dict:
    """The request _meta for one call: the passport plus the AGENT's signature over the canonical
    arguments, this tool's resource, the passport hash and the idempotency key. One helper call."""
    return {EXTENSION_ID: sign_tool_call(args, RESOURCE, PASSPORT, agent_key, agent_did, NOW, idempotency_key)}


def _structured(result):  # mcp 2.x uses snake_case field names, 1.x camelCase
    return getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)


def _is_error(result):
    return bool(getattr(result, "is_error", getattr(result, "isError", False)))


def _reason(result):
    text = result.content[0].text if result.content else ""
    return text.split("Error executing tool pay_invoice: ")[-1]


async def _run():
    print(f"\nmcp SDK   {_pkg_version('mcp')} (this example runs on 1.2+ and 2.x)")
    print(f"agent     {agent_did}\nprincipal {principal_did}\nenvelope  {jcs(ENVELOPE)}\n")
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], cwd=str(HERE))
    # mcp 2.x lets a client declare the extension in its capabilities (SEP-2133 negotiation);
    # mcp 1.x has no hook for that, and the server enforces the extension per call regardless.
    session_kw = {"extensions": {EXTENSION_ID: {}}} if "extensions" in inspect.signature(ClientSession.__init__).parameters else {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, **session_kw) as session:
            # mcp 2.x speaks the per-request protocol: server/discover returns the capabilities, including
            # the extension's settings (this server's audience and receipt key); 1.x has the initialize handshake.
            if hasattr(session, "discover"):
                caps = (await session.discover()).capabilities.model_dump(by_alias=True, exclude_none=True)
            else:
                caps = (await session.initialize()).capabilities.model_dump(by_alias=True, exclude_none=True)
            advertised = (caps.get("extensions") or {}).get(EXTENSION_ID)
            tools = {t.name: t for t in (await session.list_tools()).tools}
            requires = (tools["pay_invoice"].meta or {}).get(EXTENSION_ID)
            print(f"connected; tools: {list(tools)}\npay_invoice requires the extension (tool _meta): {requires}")
            print(f"server advertises it in capabilities: {advertised or 'no (mcp 1.x has no server-side extension registry)'}\n")

            async def call(label, args, key, meta=None):
                res = await session.call_tool("pay_invoice", args, meta=meta if meta is not None else lap_meta(args, key))
                if _is_error(res):
                    print(f"  REFUSED  {label:<36} -> {_reason(res)[:90]}")
                    return None
                out = _structured(res) or json.loads(res.content[0].text)
                receipt = (res.meta or {}).get(EXTENSION_ID) or {}
                ok = bool(receipt) and verify_receipt(
                    receipt["receipt_base"], receipt["receipt_signature_b64url"], receipt["server_did"],
                    request_body=jcs(args), response_body=jcs(out),
                )
                print(f"  PAID     {label:<36} -> {out['status']} {out['invoice']} ${out['amount']}  "
                      f"receipt {'verified' if ok else 'INVALID'} (server {receipt.get('server_did', '?')[:24]}...)")
                return receipt

            args = {"invoice": "INV-1001", "amount": 4200, "unit": "USD"}
            first = await call("in-scope: $4200 (cap $5000)", args, "pay-1001")
            again = await call("retry with the same idempotency key", args, "pay-1001")
            print(f"           same receipt, no second payment: {'yes' if again and again == first else 'NO'}")
            await call("over cap: $6000", {"invoice": "INV-1002", "amount": 6000, "unit": "USD"}, "pay-1002")
            # Tamper: sign for $100, then send $4200 with that signature -> digest mismatch.
            await call("tampered: signed $100, sent $4200", {"invoice": "INV-1003", "amount": 4200, "unit": "USD"}, "pay-1003",
                       meta=lap_meta({"invoice": "INV-1003", "amount": 100, "unit": "USD"}, "pay-1003"))
            await call("wrong unit: EUR", {"invoice": "INV-1004", "amount": 10, "unit": "EUR"}, "pay-1004")
            await call("no idempotency key", {"invoice": "INV-1005", "amount": 10, "unit": "USD"}, None)
            await call("no passport at all (plain call)", {"invoice": "INV-1006", "amount": 10, "unit": "USD"}, "pay-1006", meta={})
    print("\nEvery refusal happened BEFORE the tool ran. Every success carries a server-signed receipt in the"
          "\nresult _meta, and the retry got the cached receipt back instead of a second payment.\n")


async def main():
    try:
        await _run()
    except Exception as e:  # the server process died, or the SDK is incompatible
        print(f"\nFAILED: {type(e).__name__}: {str(e)[:140]}")
        print("If the server exited, its own traceback is printed above this line (its stderr is passed through).")
        print("Check the installed SDK with `pip show mcp`; this example runs on mcp 1.2+ and mcp 2.x.")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
