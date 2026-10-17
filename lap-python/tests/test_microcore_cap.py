"""LIP-4 Micro-Core cap vectors (output/lip/test-vectors/microcore-cap-vectors.json), shared with
the Node port: the per-transaction cap check refuses every amount that is not a non-negative exact
integer, and every malformed cap, BEFORE comparing. Found by the cold-start usability test of
2026-10-17: both ports compared ``-500000 <= 1000`` as true and executed the payment.
"""
import json
import math
import time
from decimal import Decimal
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import (
    EXTENSION_ID,
    check_invocation,
    did_key_from_raw_public_key,
    is_exact_amount,
    lap_auth_from_meta,
    microcore_cap_is_valid,
    sign_jws,
    sign_tool_call,
    tool_meta,
    verify_envelope,
)

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "microcore-cap-vectors.json"
V = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _verdict(envelope, amount, unit):
    try:
        check_invocation(envelope, act=V["invocation"]["act"], resource=V["invocation"]["resource"],
                         amount=amount, unit=unit)
        return "ok"
    except ValueError as e:
        return str(e).split(":")[0]


@pytest.mark.parametrize("vec", V["amount_vectors"], ids=[v["id"] for v in V["amount_vectors"]])
def test_amount_vector(vec):
    assert _verdict(V["envelope"], vec["amount"], vec["unit"]) == vec["expect"], vec["note"]


@pytest.mark.parametrize("vec", V["cap_vectors"], ids=[v["id"] for v in V["cap_vectors"]])
def test_cap_schema_vector(vec):
    envelope = {**V["envelope"], "cap": vec["cap"]}
    assert _verdict(envelope, V["probe"]["amount"], V["probe"]["unit"]) == vec["expect"], vec["note"]


def test_amounts_json_cannot_express_are_refused():
    # nan and the infinities compare without raising; an integral float and a Decimal are not exact ints.
    for bad in (math.nan, math.inf, -math.inf, 1000.0, Decimal("10"), -0.5):
        assert _verdict(V["envelope"], bad, "USD") == "LAP_ERR_CAP", repr(bad)
    assert is_exact_amount(0) and is_exact_amount(2**53 - 1)
    assert not is_exact_amount(2**53) and not is_exact_amount(True) and not is_exact_amount(-1)
    assert microcore_cap_is_valid({"max_per_tx": 0, "unit": "USD"})
    assert not microcore_cap_is_valid({"max_per_tx": float("nan"), "unit": "USD"})


# --- end to end through the middleware: the refusal happens before the tool runs -------------------

RESOURCE = "mcp://tools.example.com/billing/pay"
SERVER_ID = "did:web:tools.example.com"


def _keypair():
    k = Ed25519PrivateKey.generate()
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


def _passport(envelope):
    principal_key, principal_did = _keypair()
    agent_key, agent_did = _keypair()
    now = int(time.time())
    jwt = sign_jws(
        {"iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": now, "exp": now + 600,
         "lap": {"v": 0, "proof_class": "self-asserted", "envelope": envelope}},
        principal_key, principal_did + "#key-1", "lap-microcore+jwt",
    )
    return jwt, agent_key, agent_did, now


def _signed_call(fn, envelope, args, key="k-1"):
    jwt, agent_key, agent_did, now = _passport(envelope)
    auth = lap_auth_from_meta({EXTENSION_ID: sign_tool_call(args, RESOURCE, jwt, agent_key, agent_did, now, key)}, args)
    return fn(lap_auth=auth, **args)


def test_negative_amount_is_refused_before_the_tool_runs():
    runs = []

    @verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
                     expected_aud=SERVER_ID)
    def pay(invoice: str, amount: int, unit: str = "USD"):
        runs.append(amount)
        return {"paid": invoice, "amount": amount}

    env = V["envelope"]
    assert _signed_call(pay, env, {"invoice": "INV-1", "amount": 250, "unit": "USD"})["amount"] == 250
    with pytest.raises(ValueError, match="LAP_ERR_CAP: amount must be a non-negative exact integer"):
        _signed_call(pay, env, {"invoice": "INV-2", "amount": -500000, "unit": "USD"})
    # A fractional amount is refused one layer earlier: the JCS subset used for the signed body has
    # no floats, so it cannot even be canonicalized (closed either way; check_invocation is the backstop).
    with pytest.raises(ValueError, match="integers only|LAP_ERR_CAP"):
        _signed_call(pay, env, {"invoice": "INV-3", "amount": 999.5, "unit": "USD"})
    assert runs == [250]


def test_fixed_unit_for_a_tool_without_a_unit_argument():
    @verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit="USD",
                     expected_aud=SERVER_ID)
    def transfer(to: str, amount: int):
        return {"to": to, "amount": amount}

    assert _signed_call(transfer, V["envelope"], {"to": "ACME", "amount": 250})["amount"] == 250
    with pytest.raises(ValueError, match="LAP_ERR_CAP: amount 5000 exceeds max_per_tx 1000"):
        _signed_call(transfer, V["envelope"], {"to": "ACME", "amount": 5000})
    assert tool_meta("finance:pay", RESOURCE, "amount", unit="USD")[EXTENSION_ID]["unit"] == "USD"


def test_configuration_mistakes_fail_at_startup_not_on_the_first_call():
    def pay(invoice: str, amount: int, unit: str = "USD"):
        return {}

    with pytest.raises(TypeError, match="expected_aud"):
        verify_envelope(action="finance:pay", resource=RESOURCE)(pay)
    with pytest.raises(TypeError, match="amount_param='amt' is not a parameter of pay"):
        verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amt", expected_aud=SERVER_ID)(pay)
    with pytest.raises(TypeError, match="not both"):
        verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
                        unit="USD", expected_aud=SERVER_ID)(pay)
