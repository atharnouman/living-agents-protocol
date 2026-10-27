"""Build the LAP interop chain: the MCP tutorial's seven calls, recorded as audit-record-contract/1
records with the proposed `delegated-authority` extension. Fully deterministic (fixed seeds, times
and ids; Ed25519 signatures are deterministic), so the output is a reproducible fixture.

    python examples/audit-record-contract/lap_chain.py          # rebuild lap-chain.jsonl and verify it
"""
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import IdempotencyCache, claim_scope, did_key_from_raw_public_key, jcs, sha256_hex, sign_jws, verify_envelope
from living_agents.audit_record import (AuditChain, lap_tool_call_record, manifest, utc_millis,
                                        validate_extensions, validate_manifest, validate_skeleton,
                                        verify_chain_segment, verify_lap_receipt_in_record)
from living_agents.jws import decode_jws
from living_agents.mcp_extension import sign_tool_call

HERE = Path(__file__).parent
FIXTURE = HERE / "lap-chain.jsonl"
NOW = 1787000000                                    # the shared vectors' clock
SERVER_ID = "did:web:tools.example.com"
RESOURCE = "mcp://tools.example.com/billing/pay"
# Steps that run only after the passport AND the agent's call signature verified (LIP-4 section 2, steps 4-6).
POST_AUTH_CODES = {"LAP_ERR_ACT", "LAP_ERR_RES", "LAP_ERR_CAP", "LAP_ERR_IDEMPOTENCY", "LAP_ERR_REPLAY",
                   "LAP_ERR_KEY_REUSE", "LAP_ERR_REPLAY_WITHHELD"}  # the last two from 0.4.14 (LIP-4 section 2 step 3)


def key_from(label: str):
    k = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(label.encode()).digest())
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


def build_chain(path=None):
    principal_key, principal_did = key_from("LAP LIP-1 test vector principal seed 001")
    agent_key, agent_did = key_from("LAP LIP-1 test vector agent seed 001")
    server_key, server_did = key_from("LAP LIP-4 test vector tool-server seed 001")
    passport = sign_jws(
        {"iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
         "lap": {"v": 0, "proof_class": "self-asserted",
                 "constitution_hash": sha256_hex("Act only within the signed envelope; escalate on ambiguity.\n"),
                 "envelope": {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
                              "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}}}},
        principal_key, principal_did + "#key-1", "lap-microcore+jwt")
    claims = decode_jws(passport)["payload"]
    cache = IdempotencyCache()

    @verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
                     server_private_key=server_key, server_did=server_did, expected_aud=SERVER_ID,
                     idempotency_cache=cache)
    def pay_invoice(invoice: str, amount: int, unit: str = "USD"):
        return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}

    chain = AuditChain(path)
    calls = [  # (label, arguments, idempotency key, signed-for arguments or None, send a passport?)
        ("in scope", {"invoice": "INV-1001", "amount": 4200, "unit": "USD"}, "pay-1001", None, True),
        ("retry, same key", {"invoice": "INV-1001", "amount": 4200, "unit": "USD"}, "pay-1001", None, True),
        ("over cap", {"invoice": "INV-1002", "amount": 6000, "unit": "USD"}, "pay-1002", None, True),
        ("tampered", {"invoice": "INV-1003", "amount": 4200, "unit": "USD"}, "pay-1003",
         {"invoice": "INV-1003", "amount": 100, "unit": "USD"}, True),
        ("wrong unit", {"invoice": "INV-1004", "amount": 10, "unit": "EUR"}, "pay-1004", None, True),
        ("no idempotency key", {"invoice": "INV-1005", "amount": 10, "unit": "USD"}, None, None, True),
        ("no passport", {"invoice": "INV-1006", "amount": 10, "unit": "USD"}, "pay-1006", None, False),
    ]
    for i, (label, args, key, signed_for, with_passport) in enumerate(calls):
        auth, sig = None, None
        if with_passport:
            sig = sign_tool_call(signed_for or args, RESOURCE, passport, agent_key, agent_did, NOW, key)
            auth = {"passport_jwt": sig["passport"], "signature_base": sig["signature_base"],
                    "signature_b64url": sig["signature"], "request_body": jcs(args), "now": NOW}
            if key is not None:
                auth["idempotency_key"] = key
        # Claims live in the scope (tenant, agent): the tenant is the verified issuer by default (0.4.14).
        replay = (cache.check(claim_scope(claims), key) is not None) if (with_passport and key) else None
        receipt = None
        try:
            if auth is None:
                pay_invoice(**args)                 # the decorator refuses: LAP_ERR_AUTH_MISSING
            result = pay_invoice(lap_auth=auth, **args)
            receipt, code = result.get("_lap_receipt"), "ok"
        except ValueError as e:
            code = str(e).split(":")[0]
        verified = claims if (with_passport and (code == "ok" or code in POST_AUTH_CODES)) else None
        chain.append(lap_tool_call_record(
            event_id=f"lap-interop-{i + 1:02d}", occurred_at=utc_millis(NOW + i), tool_name="pay_invoice",
            decision_code=code, action="finance:pay", resource=RESOURCE,
            passport_jwt=passport if with_passport else None, verified_payload=verified,
            amount=args["amount"], unit=args["unit"], request_body=jcs(args), receipt=receipt,
            signature_base=sig["signature_base"] if sig else None, request_signature=sig["signature"] if sig else None,
            idempotency_key=key, replay=replay if code == "ok" else None))
    return chain


def main() -> int:
    if FIXTURE.exists():
        FIXTURE.unlink()
    chain = build_chain(str(FIXTURE))
    ok, failures = verify_chain_segment(AuditChain.load_jsonl(str(FIXTURE)))
    print(f"{len(chain.records)} records written to {FIXTURE.name}; chain verifies: {ok} {failures or ''}")
    for r in chain.records:
        da = r["extensions"]["delegated-authority"]
        print(f"  {r['event_id']}  {r['outcome']:<8} {da['decision_code']:<20} authority_verified={da['authority_verified']:<5} "
              f"replay={da.get('replay', '-'):<8} {r['event_hash'][:16]}")
    shapes = all(validate_skeleton(r)[0] and validate_extensions(r, allow_proposed=True)[0] for r in chain.records)
    print("core and proposed-extension shape valid on every record:", shapes)
    print("receipt re-verifies from the record alone:", verify_lap_receipt_in_record(chain.records[0]))
    print("manifest structured:", validate_manifest(manifest("examples/audit-record-contract/lap_chain.py"))[0])
    return 0 if ok and shapes else 1


if __name__ == "__main__":
    sys.exit(main())
