"""
Tests for the MCP extension binding (io.github.atharnouman/lap-microcore): the request _meta object
round-trips through verify_envelope, and mutating tools claim their idempotency key before executing.
No MCP SDK needed: the SDK-independent half is exercised with the same vectors the ports share.
"""

import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import IdempotencyCache, did_key_from_raw_public_key, jcs, sha256_hex, sign_jws, verify_envelope, verify_receipt
from living_agents.mcp_extension import (
    EXTENSION_ID,
    META_KEY,
    lap_auth_from_meta,
    sign_tool_call,
    signature_base_for_tool_call,
    tool_meta,
)

SERVER_ID = "did:web:tools.example.com"
RESOURCE = "mcp://tools.example.com/billing/pay"
NOW = 1787000000


def _keypair():
    k = Ed25519PrivateKey.generate()
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


@pytest.fixture
def actors():
    principal_key, principal_did = _keypair()
    agent_key, agent_did = _keypair()
    server_key, server_did = _keypair()
    passport = sign_jws(
        {
            "iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
            "lap": {"v": 0, "proof_class": "self-asserted", "constitution_hash": sha256_hex("x"),
                    "envelope": {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
                                 "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}}},
        },
        principal_key, principal_did + "#key-1", "lap-microcore+jwt",
    )
    return {"agent_key": agent_key, "agent_did": agent_did, "server_key": server_key,
            "server_did": server_did, "passport": passport}


def _tool(actors, cache=None):
    calls = []

    @verify_envelope(
        action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
        server_private_key=actors["server_key"], server_did=actors["server_did"],
        expected_aud=SERVER_ID, idempotency_cache=cache,
    )
    def pay(invoice: str, amount: int, unit: str = "USD"):
        calls.append(invoice)
        return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}

    return pay, calls


def _meta(actors, args, idempotency_key=None):
    return {META_KEY: sign_tool_call(args, RESOURCE, actors["passport"], actors["agent_key"],
                                     actors["agent_did"], NOW, idempotency_key)}


def test_identifier_follows_the_meta_key_rules():
    prefix, name = EXTENSION_ID.split("/")
    assert all(label[0].isalpha() and label[-1].isalnum() for label in prefix.split("."))
    assert prefix.split(".")[1] not in ("modelcontextprotocol", "mcp")  # reserved for MCP itself
    assert name[0].isalnum() and name[-1].isalnum()
    assert META_KEY == EXTENSION_ID


def test_request_meta_round_trips_through_verify_envelope(actors):
    pay, calls = _tool(actors)
    args = {"invoice": "INV-1001", "amount": 4200, "unit": "USD"}
    lap_auth = lap_auth_from_meta(_meta(actors, args), raw_arguments=args)
    assert lap_auth["request_body"] == jcs(args)

    result = pay(lap_auth={**lap_auth, "now": NOW}, **args)

    assert calls == ["INV-1001"] and result["status"] == "paid"
    receipt = result.pop("_lap_receipt")
    assert receipt["server_did"] == actors["server_did"]
    assert verify_receipt(receipt["receipt_base"], receipt["receipt_signature_b64url"], actors["server_did"],
                          request_body=jcs(args), response_body=jcs(result))


def test_signed_arguments_cannot_be_swapped(actors):
    pay, calls = _tool(actors)
    signed = {"invoice": "INV-1003", "amount": 100, "unit": "USD"}
    sent = {"invoice": "INV-1003", "amount": 4200, "unit": "USD"}
    lap_auth = lap_auth_from_meta(_meta(actors, signed), raw_arguments=sent)
    with pytest.raises(ValueError, match="LAP_ERR_DIGEST"):
        pay(lap_auth={**lap_auth, "now": NOW}, **sent)
    assert calls == []


def test_absent_extension_object_yields_none_on_both_meta_shapes(actors):
    assert lap_auth_from_meta(None) is None
    assert lap_auth_from_meta({"progressToken": 1}) is None

    class PydanticLikeMeta:  # mcp 1.x keeps unknown _meta keys in model_extra
        def __init__(self, extra):
            self.model_extra = extra

    assert lap_auth_from_meta(PydanticLikeMeta({})) is None
    args = {"invoice": "INV-1", "amount": 1, "unit": "USD"}
    auth = lap_auth_from_meta(PydanticLikeMeta(_meta(actors, args)))
    assert auth["passport_jwt"] == actors["passport"] and "request_body" not in auth


def test_mutating_tool_replays_the_cached_result_without_re_executing(actors):
    cache = IdempotencyCache()
    pay, calls = _tool(actors, cache)
    args = {"invoice": "INV-2001", "amount": 10, "unit": "USD"}
    auth = {**lap_auth_from_meta(_meta(actors, args, "k-1"), raw_arguments=args), "now": NOW}

    first = pay(lap_auth=auth, **args)
    second = pay(lap_auth=auth, **args)

    assert calls == ["INV-2001"]  # executed once
    assert second == first and second is not first  # same result and receipt, a copy
    assert second["_lap_receipt"]["receipt_base"] == first["_lap_receipt"]["receipt_base"]

    other = {**lap_auth_from_meta(_meta(actors, args, "k-2"), raw_arguments=args), "now": NOW}
    pay(lap_auth=other, **args)
    assert calls == ["INV-2001", "INV-2001"]  # a fresh key executes again


def test_mutating_tool_requires_a_signed_idempotency_key(actors):
    pay, calls = _tool(actors, IdempotencyCache())
    args = {"invoice": "INV-3001", "amount": 10, "unit": "USD"}

    without_key = {**lap_auth_from_meta(_meta(actors, args), raw_arguments=args), "now": NOW}
    with pytest.raises(ValueError, match="LAP_ERR_IDEMPOTENCY"):
        pay(lap_auth=without_key, **args)

    # The key is present in _meta but was not a covered component of the signature.
    unsigned_key = {**lap_auth_from_meta(_meta(actors, args), raw_arguments=args), "idempotency_key": "k-9", "now": NOW}
    with pytest.raises(ValueError, match="LAP_ERR_SIG_PARAMS"):
        pay(lap_auth=unsigned_key, **args)
    assert calls == []


def test_signature_base_shape_and_tool_meta(actors):
    base = signature_base_for_tool_call({"b": 1, "a": 2}, RESOURCE, actors["passport"], actors["agent_did"], NOW, "k")
    lines = base.split("\n")
    assert lines[0] == '"@method": tools/call' and lines[1] == f'"@target-uri": {RESOURCE}'
    assert lines[4] == '"idempotency-key": k'
    assert lines[-1].startswith('"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash" "idempotency-key");created=')
    assert tool_meta("finance:pay", RESOURCE, "amount", "unit", mutating=True) == {
        META_KEY: {"action": "finance:pay", "resource": RESOURCE, "amount_param": "amount", "unit_param": "unit", "mutating": True}
    }
