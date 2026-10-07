"""A LAP-aware MCP client: mints an agent passport + envelope, signs each tool call,
and verifies the server's receipt. Spawns server.py over stdio.

Run:  python client.py
"""
import asyncio
import json
import sys
import time
from importlib.metadata import version as _pkg_version
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from living_agents import (
    b64url_encode, did_key_from_raw_public_key, jcs, sha256_b64url, sha256_hex, sign_jws, verify_receipt,
)

if hasattr(sys.stdout, "reconfigure"):            # Windows consoles default to cp1252; keep the check marks printable
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER_ID = "did:web:tools.example.com"           # must match the server's expected audience
RESOURCE = "mcp://tools.example.com/billing/pay"  # the tool's declared resource
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


def lap_auth_for(args: dict) -> dict:
    """Sign a call. The signed body is the canonical JSON of the tool arguments — exactly
    what the server derives from its own bound arguments — so a signature can never be
    reused for different arguments."""
    body = jcs(args)
    base = "\n".join([
        '"@method": tools/call',
        f'"@target-uri": {RESOURCE}',
        f'"content-digest": sha-256=:{sha256_b64url(body)}:',
        f'"lap-passport-hash": sha256:{sha256_hex(PASSPORT)}',
        f'"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash");created={NOW};keyid="{agent_did}#key-1"',
    ])
    return {"passport_jwt": PASSPORT, "signature_base": base, "signature_b64url": b64url_encode(agent_key.sign(base.encode("ascii")))}


def _structured(result):  # mcp 2.x uses snake_case field names, 1.x camelCase
    return getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)


def _is_error(result):
    return bool(getattr(result, "is_error", getattr(result, "isError", False)))


def parse(result):
    sc = _structured(result)
    if isinstance(sc, dict) and "status" in sc:
        return sc
    text = result.content[0].text if result.content else "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": text}


async def _run():
    print(f"\nmcp SDK   {_pkg_version('mcp')} (this example runs on 1.2+ and 2.x)")
    print(f"agent     {agent_did}\nprincipal {principal_did}\nenvelope  {jcs(ENVELOPE)}\n")
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], cwd=str(HERE))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [t.name for t in (await session.list_tools()).tools]
            print(f"connected to server; tools: {tools}\n")

            async def call(label, args, auth=None):
                res = await session.call_tool("pay_invoice", {**args, "lap_auth": auth if auth is not None else lap_auth_for(args)})
                out = parse(res)
                if _is_error(res):
                    reason = (out.get("error") or res.content[0].text).split("Error executing tool pay_invoice: ")[-1]
                    print(f"  REFUSED  {label:<34} -> {reason[:90]}")
                    return
                receipt = out.pop("_lap_receipt", None)
                ok = bool(receipt) and verify_receipt(
                    receipt["receipt_base"], receipt["receipt_signature_b64url"], receipt["server_did"],
                    request_body=jcs(args), response_body=jcs(out),
                )
                print(f"  PAID     {label:<34} -> {out['status']} {out['invoice']} ${out['amount']}  receipt {'verified ✓' if ok else 'INVALID ✗'} (server {receipt['server_did'][:24]}…)")

            await call("in-scope: $4200 (cap $5000)", {"invoice": "INV-1001", "amount": 4200, "unit": "USD"})
            await call("over cap: $6000", {"invoice": "INV-1002", "amount": 6000, "unit": "USD"})
            # Tamper: sign for $100, then send $4200 with that signature -> digest mismatch.
            await call("tampered: signed $100, sent $4200", {"invoice": "INV-1003", "amount": 4200, "unit": "USD"},
                       auth=lap_auth_for({"invoice": "INV-1003", "amount": 100, "unit": "USD"}))
            await call("wrong unit: EUR", {"invoice": "INV-1004", "amount": 10, "unit": "EUR"})
            res = await session.call_tool("pay_invoice", {"invoice": "INV-1005", "amount": 10, "unit": "USD"})
            reason = (parse(res).get("error") or res.content[0].text).split("Error executing tool pay_invoice: ")[-1]
            print(f"  REFUSED  {'no passport at all':<34} -> {reason[:90]}")
    print("\nEvery refusal happened BEFORE the tool ran. Every success carries a server-signed receipt.\n")


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
