"""
Unit tests for FastMCP @verify_envelope middleware decorator.
"""

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from living_agents.crypto_util import did_key_from_raw_public_key
from living_agents.mcp_middleware import verify_envelope
from living_agents.microcore import verify_receipt

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "vectors.json"


@pytest.fixture
def vectors():
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_verify_envelope_decorator_success(vectors):
    """Test @verify_envelope executes tool and attaches valid tripartite receipt."""
    server_priv = Ed25519PrivateKey.generate()
    server_pub_raw = server_priv.public_key().public_bytes_raw()
    server_did = did_key_from_raw_public_key(server_pub_raw)

    mc = vectors["micro_core"]

    @verify_envelope(
        action="finance:pay",
        resource="mcp://tools.example.com/billing/pay",
        amount_param="amount",
        unit_param="unit",
        server_private_key=server_priv,
        server_did=server_did,
        expected_aud="did:web:tools.example.com",
        bind_target=False,  # HTTP vector: @target-uri is the https transport URL, not the mcp resource
    )
    def pay_tool(invoice: str, amount: int, unit: str):
        return {"status": "paid", "invoice": invoice, "paid_amount": amount}

    lap_auth = {
        "passport_jwt": mc["passport_jwt"],
        "agent_did": vectors["keys"]["agent"]["did"],
        "signature_base": mc["rfc9421_signature_base"],
        "signature_b64url": mc["request_signature_b64url"],
        "request_body": mc["request_body"],
        "now": 1787000000,
    }

    result = pay_tool(invoice="INV-1001", amount=4200, unit="USD", lap_auth=lap_auth)

    assert result["status"] == "paid"
    assert "_lap_receipt" in result
    receipt = result["_lap_receipt"]
    assert receipt["server_did"] == server_did

    # Verify the minted receipt
    assert verify_receipt(
        receipt_base=receipt["receipt_base"],
        receipt_signature_b64url=receipt["receipt_signature_b64url"],
        server_did=server_did,
        request_body=mc["request_body"],
        response_body='{"invoice":"INV-1001","paid_amount":4200,"status":"paid"}',
    )


def test_verify_envelope_decorator_cap_rejection(vectors):
    """Test @verify_envelope rejects invocations exceeding per-tx cap."""
    mc = vectors["micro_core"]

    @verify_envelope(
        action="finance:pay",
        resource="mcp://tools.example.com/billing/pay",
        amount_param="amount",
        unit_param="unit",
        expected_aud="did:web:tools.example.com",
        bind_target=False,  # HTTP vector: @target-uri is the https transport URL, not the mcp resource
    )
    def pay_tool(invoice: str, amount: int, unit: str):
        return {"status": "paid"}

    lap_auth = {
        "passport_jwt": mc["passport_jwt"],
        "signature_base": mc["rfc9421_signature_base"],
        "signature_b64url": mc["request_signature_b64url"],
        "request_body": mc["request_body"],
        "now": 1787000000,
    }

    # 6000 USD exceeds 5000 USD cap
    with pytest.raises(ValueError, match="LAP_ERR_CAP"):
        pay_tool(invoice="INV-1001", amount=6000, unit="USD", lap_auth=lap_auth)


def test_verify_envelope_positional_args_cannot_bypass_cap(vectors):
    """F5 regression: positional args must be bound so the cap still applies."""
    mc = vectors["micro_core"]

    @verify_envelope(
        action="finance:pay",
        resource="mcp://tools.example.com/billing/pay",
        amount_param="amount",
        unit_param="unit",
        expected_aud="did:web:tools.example.com",
        bind_target=False,  # HTTP vector: @target-uri is the https transport URL, not the mcp resource
    )
    def pay_tool(invoice: str, amount: int, unit: str):
        return {"status": "paid"}

    lap_auth = {
        "passport_jwt": mc["passport_jwt"],
        "signature_base": mc["rfc9421_signature_base"],
        "signature_b64url": mc["request_signature_b64url"],
        "request_body": mc["request_body"],
        "now": 1787000000,
    }

    # Positional 6000 must be caught by the cap, not silently skipped
    with pytest.raises(ValueError, match="LAP_ERR_CAP"):
        pay_tool("INV-1001", 6000, "USD", lap_auth=lap_auth)


# ---------------------------------------------------------------------------
# MCP-shaped tools (see examples/mcp-server): the tool declares `lap_auth` so it
# appears in the MCP tool schema; the decorator must derive the signed body from
# the server's OWN bound arguments (defaults applied) with `lap_auth` removed.
# ---------------------------------------------------------------------------
from typing import Optional

from living_agents import b64url_encode, jcs, sha256_b64url, sha256_hex, sign_jws

SERVER_ID = "did:web:tools.example.com"
RESOURCE = "mcp://tools.example.com/billing/pay"
NOW = 1787000000


def _keypair():
    k = Ed25519PrivateKey.generate()
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


def _mint(principal_key, principal_did, agent_did, proof_class="self-asserted"):
    return sign_jws(
        {
            "iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
            "lap": {
                "v": 0, "proof_class": proof_class, "constitution_hash": sha256_hex("c\n"),
                "envelope": {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
                             "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}},
            },
        },
        principal_key, principal_did + "#key-1", "lap-microcore+jwt",
    )


def _auth(passport, signing_key, agent_did, signed_args):
    """Exactly what examples/mcp-server/client.py sends: an RFC 9421-style base over the
    canonical JSON of the tool arguments, signed by the agent key."""
    body = jcs(signed_args)
    base = "\n".join([
        '"@method": tools/call',
        f'"@target-uri": {RESOURCE}',
        f'"content-digest": sha-256=:{sha256_b64url(body)}:',
        f'"lap-passport-hash": sha256:{sha256_hex(passport)}',
        f'"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash");created={NOW};keyid="{agent_did}#key-1"',
    ])
    return {"passport_jwt": passport, "signature_base": base,
            "signature_b64url": b64url_encode(signing_key.sign(base.encode("ascii"))), "now": NOW}


def _mcp_tool(**policy):
    @verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
                     expected_aud=SERVER_ID, **policy)
    def pay_invoice(invoice: str, amount: int, unit: str = "USD", lap_auth: Optional[dict] = None):
        return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}
    return pay_invoice


def test_mcp_signed_body_is_bound_args_without_lap_auth():
    """Regression: `lap_auth` must never leak into the derived signed body (it did before the
    MCP example landed — the client-signed digest could not match), and defaults must be bound."""
    pkey, pdid = _keypair()
    akey, adid = _keypair()
    passport = _mint(pkey, pdid, adid)
    tool = _mcp_tool()

    args = {"invoice": "INV-1", "amount": 4200, "unit": "USD"}
    out = tool(**args, lap_auth=_auth(passport, akey, adid, args))
    assert out["status"] == "paid" and out["amount"] == 4200

    # `unit` omitted by the caller: the server binds the default, and the client signed it.
    signed = {"invoice": "INV-2", "amount": 1, "unit": "USD"}
    assert tool(invoice="INV-2", amount=1, lap_auth=_auth(passport, akey, adid, signed))["status"] == "paid"


def test_mcp_signature_does_not_transfer_to_different_args():
    pkey, pdid = _keypair()
    akey, adid = _keypair()
    passport = _mint(pkey, pdid, adid)
    auth = _auth(passport, akey, adid, {"invoice": "INV-3", "amount": 100, "unit": "USD"})
    with pytest.raises(ValueError, match="LAP_ERR_DIGEST"):
        _mcp_tool()(invoice="INV-3", amount=4200, unit="USD", lap_auth=auth)


def test_mcp_stolen_passport_is_useless_without_the_agent_key():
    """Holder-of-key (F2): the base names the passport's agent, but a different key signed it."""
    pkey, pdid = _keypair()
    _, adid = _keypair()
    thief_key, _ = _keypair()
    passport = _mint(pkey, pdid, adid)
    args = {"invoice": "INV-4", "amount": 10, "unit": "USD"}
    with pytest.raises(ValueError, match="LAP_ERR_REQ_SIG"):
        _mcp_tool()(**args, lap_auth=_auth(passport, thief_key, adid, args))


def test_mcp_server_policy_can_refuse_a_valid_passport():
    """F1 passthrough (identity is not authorization): allowed_issuers / min_proof_class."""
    pkey, pdid = _keypair()
    akey, adid = _keypair()
    _, other_principal = _keypair()
    passport = _mint(pkey, pdid, adid)
    args = {"invoice": "INV-5", "amount": 10, "unit": "USD"}

    assert _mcp_tool(allowed_issuers=[pdid])(**args, lap_auth=_auth(passport, akey, adid, args))["status"] == "paid"
    with pytest.raises(ValueError, match="LAP_ERR_ISSUER"):
        _mcp_tool(allowed_issuers=[other_principal])(**args, lap_auth=_auth(passport, akey, adid, args))
    with pytest.raises(ValueError, match="LAP_ERR_PROOF_CLASS"):
        _mcp_tool(min_proof_class="org-validated")(**args, lap_auth=_auth(passport, akey, adid, args))


def test_mcp_missing_lap_auth_is_refused_before_the_tool_runs():
    ran = []

    @verify_envelope(action="finance:pay", resource=RESOURCE, expected_aud=SERVER_ID)
    def tool(invoice: str, lap_auth: Optional[dict] = None):
        ran.append(invoice)
        return {"status": "paid"}

    with pytest.raises(ValueError, match="LAP_ERR_AUTH_MISSING"):
        tool(invoice="INV-6")
    assert ran == []


def _auth_with_target(passport, signing_key, agent_did, signed_args, target):
    """Like _auth, but lets the caller forge a different @target-uri (to prove the server binds it)."""
    body = jcs(signed_args)
    base = "\n".join([
        '"@method": tools/call',
        f'"@target-uri": {target}',
        f'"content-digest": sha-256=:{sha256_b64url(body)}:',
        f'"lap-passport-hash": sha256:{sha256_hex(passport)}',
        f'"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash");created={NOW};keyid="{agent_did}#key-1"',
    ])
    return {"passport_jwt": passport, "signature_base": base,
            "signature_b64url": b64url_encode(signing_key.sign(base.encode("ascii"))), "now": NOW}


def test_mcp_signature_target_is_bound_to_the_tool():
    """F6 (Gemini hostile review): the middleware binds the signed @target-uri to the tool's
    resource by default, so a signature scoped to one tool cannot be replayed against another
    under the same envelope. bind_target=False restores the un-bound behaviour for HTTP profiles."""
    pkey, pdid = _keypair()
    akey, adid = _keypair()
    passport = _mint(pkey, pdid, adid)
    args = {"invoice": "INV-9", "amount": 10, "unit": "USD"}
    assert _mcp_tool()(**args, lap_auth=_auth(passport, akey, adid, args))["status"] == "paid"  # correct target
    forged = _auth_with_target(passport, akey, adid, args, "mcp://tools.example.com/billing/refund")
    with pytest.raises(ValueError, match="LAP_ERR_TARGET"):
        _mcp_tool()(**args, lap_auth=forged)                                  # sibling-tool target -> refused
    assert _mcp_tool(bind_target=False)(**args, lap_auth=forged)["status"] == "paid"  # opt-out
