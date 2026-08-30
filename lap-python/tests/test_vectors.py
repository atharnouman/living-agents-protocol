"""
Cross-language test vector verification against output/lip/test-vectors/vectors.json.
Proves Python and Node.js reference implementations produce byte-identical canonical signatures.
"""

import json
from pathlib import Path

import pytest
from living_agents.crypto_util import (
    did_key_to_raw_public_key,
    jcs,
    sha256_hex,
)
from living_agents.jws import verify_jws, verify_passport
from living_agents.microcore import (
    check_invocation,
    make_idempotency_cache,
    verify_microcore_passport,
    verify_receipt,
    verify_request_signature,
)

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "vectors.json"


@pytest.fixture
def vectors():
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_did_key_decoding_matches_vectors(vectors):
    """Verify did:key decoding matches published public key hex bytes."""
    for role, key_info in vectors["keys"].items():
        raw = did_key_to_raw_public_key(key_info["did"])
        assert raw.hex() == key_info["public_key_hex"]


def test_jcs_canonicalization_matches_byte_for_byte(vectors):
    """Verify Python JCS produces byte-identical string to published vector."""
    claims = vectors["passport"]["claims"]
    canonical = jcs(claims)
    assert canonical == vectors["passport"]["canonical_jcs"]


def test_constitution_hash_reproduces(vectors):
    """Verify constitution text SHA-256 hash matches vector."""
    const_text = vectors["constitution"]["text"]
    const_hash = sha256_hex(const_text)
    assert const_hash == vectors["constitution"]["sha256"]


def test_passport_jws_verifies_under_lip1_rules(vectors):
    """Verify passport JWS verifies under LIP-1 rules."""
    jws_token = vectors["passport"]["jws"]
    payload = verify_passport(jws_token, now=1787000000)
    assert payload["v"] == "lip1-v0"
    assert payload["principal"]["id"] == vectors["keys"]["principal"]["did"]
    assert payload["id"] == vectors["keys"]["agent"]["did"]


def test_passport_tamper_rejection(vectors):
    """Verify modifying a single character in the payload causes signature failure."""
    jws_token = vectors["passport"]["jws"]
    h, p, s = jws_token.split(".")
    # Modify payload
    payload_dict = json.loads(vectors["passport"]["canonical_jcs"])
    payload_dict["autonomy_level"] = 4
    tampered_p = jcs(payload_dict).encode("utf-8")
    import base64
    tampered_b64 = base64.urlsafe_b64encode(tampered_p).decode("ascii").rstrip("=")
    tampered_jws = f"{h}.{tampered_b64}.{s}"

    with pytest.raises(ValueError, match="LAP_ERR_SIG"):
        verify_passport(tampered_jws, now=1787000000)


def test_genesis_hash_chain_reproduces(vectors):
    """Verify genesis record hash reproduces byte-for-byte."""
    genesis_claims = vectors["genesis"]["claims"]
    assert jcs(genesis_claims) == vectors["genesis"]["canonical_jcs"]
    assert sha256_hex(vectors["genesis"]["canonical_jcs"]) == vectors["genesis"]["sha256"]


def test_microcore_passport_jwt_verifies_with_audience(vectors):
    """Verify Micro-Core passport JWT with audience binding."""
    mc = vectors["micro_core"]
    payload = verify_microcore_passport(mc["passport_jwt"], expected_aud="did:web:tools.example.com", now=1787000000)
    assert payload["aud"] == "did:web:tools.example.com"
    assert payload["lap"]["envelope"]["act"] == ["finance:pay"]


def test_microcore_request_signature_binds_body_and_passport(vectors):
    """Verify RFC 9421 request signature verification."""
    mc = vectors["micro_core"]
    assert verify_request_signature(
        passport_jwt=mc["passport_jwt"],
        sub=vectors["keys"]["agent"]["did"],
        signature_base=mc["rfc9421_signature_base"],
        signature_b64url=mc["request_signature_b64url"],
        request_body=mc["request_body"],
    )


def test_microcore_invocation_checks(vectors):
    """Verify Micro-Core check_invocation enforces act, res, and cap."""
    mc = vectors["micro_core"]
    payload = verify_microcore_passport(mc["passport_jwt"], expected_aud="did:web:tools.example.com", now=1787000000)
    env = payload["lap"]["envelope"]

    # Valid invocation within cap
    assert check_invocation(env, act="finance:pay", resource="mcp://tools.example.com/billing/pay", amount=4200, unit="USD")

    # Invalid action
    with pytest.raises(ValueError, match="LAP_ERR_ACT"):
        check_invocation(env, act="data:read", resource="mcp://tools.example.com/billing/pay")

    # Invalid resource path
    with pytest.raises(ValueError, match="LAP_ERR_RES"):
        check_invocation(env, act="finance:pay", resource="mcp://tools.example.com/admin/keys")

    # Amount exceeding cap (5000 USD limit vs 6000 USD requested)
    with pytest.raises(ValueError, match="LAP_ERR_CAP"):
        check_invocation(env, act="finance:pay", resource="mcp://tools.example.com/billing/pay", amount=6000, unit="USD")


def test_receipt_verifies_against_tool_server_key(vectors):
    """Verify tripartite receipt verification."""
    mc = vectors["micro_core"]
    assert verify_receipt(
        receipt_base=mc["receipt_base"],
        receipt_signature_b64url=mc["receipt_signature_b64url"],
        server_did=vectors["keys"]["tool_server"]["did"],
        request_body=mc["request_body"],
        response_body='{"status":"paid","receipt":"R-77"}',
    )


def test_idempotency_cache():
    """Verify idempotency cache stores and retrieves receipts."""
    cache = make_idempotency_cache()
    agent_did = "did:key:z6MksMrZ..."
    key = "req-12345"
    receipt = {"status": "paid", "receipt_base": "sha256:a:sha256:b"}

    assert cache.check(agent_did, key) is None
    cache.store(agent_did, key, receipt)
    assert cache.check(agent_did, key) == receipt
    assert cache.check("did:key:z6MkOther...", key) is None
