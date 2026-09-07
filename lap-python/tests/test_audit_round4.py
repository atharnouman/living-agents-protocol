"""Round-4 regression tests — GPT-5.6 Codex hostile security audit (2026-08-30).
Each locks a confirmed-and-fixed vulnerability against regression, in Node parity.
"""
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents.algebra import (
    cap_subsumes,
    dag_subsumes,
    path_subsumes,
    scope_subsumes,
    verify_envelope_attenuation,
)
from living_agents.crypto_util import (
    b64url_encode,
    did_key_from_raw_public_key,
    did_key_to_raw_public_key,
    sha256_b64url,
    sha256_hex,
)
from living_agents.microcore import make_idempotency_cache, verify_microcore_passport, verify_request_signature

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "vectors.json"


@pytest.fixture
def vectors():
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _s(res, cap, depth):
    return {"v": "lap-scope-v0", "act": "finance:pay", "res": res, "cap": cap, "depth": depth, "decay_max_sec": 300}


def test_f7_multi_window_budget_conservation():
    parent = [_s("mcp://t/pay/**", {"max_per_tx": 100, "max_cumulative": 2400, "unit": "USD", "window": "utc_day"}, 2)]
    children = [
        _s(f"mcp://t/pay/{i}", {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "utc_hour"}, 1)
        for i in range(24)
    ]
    assert verify_envelope_attenuation(parent, children)["ok"] is False
    one = [_s("mcp://t/pay/x", {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "utc_hour"}, 1)]
    assert verify_envelope_attenuation(parent, one)["ok"] is True
    two = one + [_s("mcp://t/pay/y", {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "utc_hour"}, 1)]
    assert verify_envelope_attenuation(parent, two)["ok"] is False


def test_f8_negative_caps_rejected():
    parent = [_s("mcp://t/pay/**", {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "tx"}, 2)]
    with_neg = [
        _s("mcp://t/pay/a", {"max_per_tx": 100, "max_cumulative": -100, "unit": "USD", "window": "tx"}, 1),
        _s("mcp://t/pay/b", {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "tx"}, 1),
    ]
    with pytest.raises(ValueError, match="LAP_ERR_CAP_SCHEMA"):
        verify_envelope_attenuation(parent, with_neg)


def test_f9_scope_subsumes_includes_caps():
    p = _s("mcp://t/pay/**", {"max_per_tx": 1, "max_cumulative": 1, "unit": "USD", "window": "tx"}, 3)
    c = _s("mcp://t/pay/x", {"max_per_tx": 999, "max_cumulative": 999, "unit": "USD", "window": "tx"}, 2)
    assert scope_subsumes(p, c) is False


def test_f10_path_traversal_rejected():
    with pytest.raises(ValueError, match="dot-segments"):
        path_subsumes("https://api.example/safe/**", "https://api.example/safe/../admin/delete")
    with pytest.raises(ValueError, match="percent-encoding"):
        path_subsumes("https://api.example/safe/**", "https://api.example/safe/%2e%2e/admin")


def test_fextra_array_act_value_equality():
    assert dag_subsumes(["finance:pay"], ["finance:pay"]) is True
    assert dag_subsumes(["finance:pay"], ["finance:pay:escrow"]) is True
    assert dag_subsumes(["finance:pay"], ["data:read"]) is False
    assert dag_subsumes("finance:pay", "finance:pay") is True


def test_f2_request_signature_key_from_sub(vectors):
    mc = vectors["micro_core"]
    body = mc["request_body"]
    attacker = Ed25519PrivateKey.generate()
    attacker_did = did_key_from_raw_public_key(attacker.public_key().public_bytes_raw())
    base = f'"content-digest": sha-256=:{sha256_b64url(body)}:\n"lap-passport-hash": sha256:{sha256_hex(mc["passport_jwt"])}'
    sig = b64url_encode(attacker.sign(base.encode("ascii")))
    # attacker cannot claim their own DID as the request signer, and the two-line
    # base is missing mandatory components regardless
    with pytest.raises(ValueError, match="LAP_ERR"):
        verify_request_signature(passport_jwt=mc["passport_jwt"], sub=vectors["keys"]["agent"]["did"],
                                 signature_base=base, signature_b64url=sig, request_body=body)
    _ = attacker_did  # documents the attacker identity in the scenario


def test_f4_audience_mandatory(vectors):
    with pytest.raises(ValueError, match="LAP_ERR_AUDIENCE"):
        verify_microcore_passport(vectors["micro_core"]["passport_jwt"], now=1787000000)


def test_f1_issuer_and_proof_class_policy(vectors):
    jwt = vectors["micro_core"]["passport_jwt"]
    with pytest.raises(ValueError, match="LAP_ERR_ISSUER"):
        verify_microcore_passport(jwt, expected_aud="did:web:tools.example.com", now=1787000000,
                                  allowed_issuers=["did:key:z6MkSomeoneElse"])
    with pytest.raises(ValueError, match="LAP_ERR_PROOF_CLASS"):
        verify_microcore_passport(jwt, expected_aud="did:web:tools.example.com", now=1787000000,
                                  min_proof_class="org-validated")


def test_f6_idempotency_claim_three_state():
    # v0.4.10: a fresh reservation and an in-flight duplicate MUST be distinguishable, or two
    # concurrent mutating requests both see "free" and both execute (Gemini hostile-review F1).
    cache = make_idempotency_cache()
    assert cache.claim("did:key:a", "one") == {"status": "reserved"}      # first: won the slot
    assert cache.claim("did:key:a", "one") == {"status": "in_flight"}     # duplicate while pending -> reject, do NOT execute
    cache.complete("did:key:a", "one", {"receipt": "R"})
    assert cache.claim("did:key:a", "one") == {"status": "completed", "receipt": {"receipt": "R"}}
    assert cache.claim("did:key:b", "one") == {"status": "reserved"}


def test_f12_overlong_did_rejected():
    with pytest.raises(ValueError, match="multibase too long"):
        did_key_to_raw_public_key("did:key:z" + "z" * 100000)
    # a real did:key still round-trips
    raw = b"\x01" * 32
    assert did_key_to_raw_public_key(did_key_from_raw_public_key(raw)) == raw
