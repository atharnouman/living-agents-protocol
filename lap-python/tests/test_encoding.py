"""Strict-canonical base64url (self-found 2026-09-06 via a flaky lap-git self-test).

A lenient decoder gives one signature many textual forms: the final character of an
Ed25519 signature carries only two data bits, so 'A'->'B' changes padding bits alone and
the bytes still verify. Anything keyed by the TEXT (lap-passport-hash, dedup keys,
denylists, log entries) could then be evaded by re-encoding. Decoders MUST reject.
"""
import base64
import json
from pathlib import Path

import pytest
from living_agents import (
    b64url_decode, b64url_encode, sha256_hex, verify_microcore_passport, verify_request_signature,
)

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "vectors.json"
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
NOW = 1787000000
AUD = "did:web:tools.example.com"


@pytest.fixture
def vectors():
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _non_canonical(s: str) -> str:
    """Change padding-only bits in the final character: same bytes under a lenient decoder."""
    return s[:-1] + ALPHA[ALPHA.index(s[-1]) + 1]


def _lenient(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def test_b64url_decode_is_strict_canonical(vectors):
    sig = vectors["micro_core"]["request_signature_b64url"]
    assert len(sig) == 86
    assert b64url_encode(b64url_decode(sig)) == sig  # canonical round-trip
    sig2 = _non_canonical(sig)
    assert _lenient(sig2) == _lenient(sig), "premise: lenient decoding conflates the two forms"
    with pytest.raises(ValueError, match="LAP_ERR_ENCODING: non-canonical"):
        b64url_decode(sig2)
    for bad in (sig + "==", sig[:10] + "$" + sig[10:], sig.replace("-", "+").replace("_", "/") + "+", sig + "AAA"):
        with pytest.raises(ValueError, match="LAP_ERR_ENCODING"):
            b64url_decode(bad)
    with pytest.raises(ValueError, match="LAP_ERR_ENCODING"):
        b64url_decode(None)  # type: ignore[arg-type]
    assert b64url_decode("") == b""


def test_malleated_signature_text_is_rejected_end_to_end(vectors):
    mc = vectors["micro_core"]
    agent_did = vectors["keys"]["agent"]["did"]
    with pytest.raises(ValueError, match="LAP_ERR_ENCODING"):
        verify_request_signature(mc["passport_jwt"], agent_did, mc["rfc9421_signature_base"],
                                 _non_canonical(mc["request_signature_b64url"]), mc["request_body"])
    h, p, s = mc["passport_jwt"].split(".")
    jwt2 = f"{h}.{p}.{_non_canonical(s)}"
    assert sha256_hex(mc["passport_jwt"]) != sha256_hex(jwt2), "a hash-keyed denylist would miss the re-encoded token"
    with pytest.raises(ValueError, match="LAP_ERR_ENCODING"):
        verify_microcore_passport(jwt2, expected_aud=AUD, now=NOW)
    # and the canonical original still verifies
    assert verify_microcore_passport(mc["passport_jwt"], expected_aud=AUD, now=NOW)["sub"] == agent_did
