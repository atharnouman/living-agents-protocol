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
    )
    def pay_tool(invoice: str, amount: int, unit: str):
        return {"status": "paid"}

    lap_auth = {
        "passport_jwt": mc["passport_jwt"],
        "agent_did": vectors["keys"]["agent"]["did"],
        "signature_base": mc["rfc9421_signature_base"],
        "signature_b64url": mc["request_signature_b64url"],
        "request_body": mc["request_body"],
        "now": 1787000000,
    }

    # 6000 USD exceeds 5000 USD cap
    with pytest.raises(ValueError, match="LAP_ERR_CAP"):
        pay_tool(invoice="INV-1001", amount=6000, unit="USD", lap_auth=lap_auth)
