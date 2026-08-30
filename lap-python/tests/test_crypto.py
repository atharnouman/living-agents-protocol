"""
Unit tests for LAP Python crypto utilities.
"""

import pytest
from living_agents.crypto_util import (
    b58decode,
    b58encode,
    did_key_from_raw_public_key,
    did_key_to_raw_public_key,
    jcs,
    normalize_did,
    normalize_uri,
)


def test_b58_zero_invariants():
    """Verify base58 encoding and decoding preserves leading zeros exactly."""
    assert b58decode("") == b""
    assert b58decode("1") == b"\x00"
    assert b58decode("11") == b"\x00\x00"
    assert b58decode("111") == b"\x00\x00\x00"

    assert b58encode(b"") == ""
    assert b58encode(b"\x00") == "1"
    assert b58encode(b"\x00\x00") == "11"
    assert b58encode(b"\x00\x00\x00") == "111"

    raw32 = b"\x00" + b"\xff" * 31
    encoded = b58encode(raw32)
    assert b58decode(encoded) == raw32


def test_b58_invalid_character():
    """Verify invalid base58 characters raise ValueError."""
    with pytest.raises(ValueError, match="invalid base58 character"):
        b58decode("0OIl")  # 0, O, I, l are excluded from Base58


def test_did_normalization():
    """Verify DID normalization lowercases method prefix but preserves case-sensitive identifier."""
    assert normalize_did("DID:KEY:z6MksMrZ") == "did:key:z6MksMrZ"
    assert normalize_did("did:web:EXAMPLE.COM") == "did:web:EXAMPLE.COM"
    assert normalize_did("did:key:z6MksMrZ") == "did:key:z6MksMrZ"


def test_uri_normalization():
    """Verify URI normalization lowercases scheme and host."""
    assert normalize_uri("HTTPS://Tools.Example.COM/billing/pay") == "https://tools.example.com/billing/pay"
    assert normalize_uri("mcp://TOOLS.EXAMPLE.COM/Tools/Pay") == "mcp://tools.example.com/Tools/Pay"


def test_jcs_canonicalization():
    """Verify JCS canonicalization produces sorted keys, compact separators, and no trailing whitespace."""
    obj = {"b": 2, "a": 1, "c": [3, 2, {"z": True, "y": None}]}
    expected = '{"a":1,"b":2,"c":[3,2,{"y":null,"z":true}]}'
    assert jcs(obj) == expected


def test_jcs_float_rejection():
    """Verify non-integer floating point numbers raise ValueError."""
    with pytest.raises(ValueError, match="JCS subset: integers only"):
        jcs({"amount": 42.5})


def test_did_key_roundtrip():
    """Verify did:key conversion round-trips correctly."""
    raw = b"\x01" * 32
    did = did_key_from_raw_public_key(raw)
    assert did.startswith("did:key:z")
    assert did_key_to_raw_public_key(did) == raw
