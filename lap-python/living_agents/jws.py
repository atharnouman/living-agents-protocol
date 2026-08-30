"""
LIP-1 / LIP-4 JWS signing and verification: Compact EdDSA JWS, passport claims check.
"""

import json
import time
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .crypto_util import (
    b64url_decode,
    b64url_encode,
    jcs,
    normalize_did,
    public_key_from_did,
    verify_ed25519,
)

SKEW_SECONDS = 60  # Default clock-skew tolerance in seconds


def sign_jws(
    payload: Dict[str, Any],
    private_key: Ed25519PrivateKey,
    kid: str,
    typ: str = "lap-passport+jwt",
) -> str:
    """Produce a compact EdDSA JWS over the JCS canonical form of payload."""
    header = {"alg": "EdDSA", "kid": kid, "typ": typ}
    header_b64 = b64url_encode(jcs(header).encode("utf-8"))
    payload_b64 = b64url_encode(jcs(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = private_key.sign(signing_input)
    return f"{header_b64}.{payload_b64}.{b64url_encode(sig)}"


def decode_jws(token: str) -> Dict[str, Any]:
    """Decode a compact JWS into header, payload, signature, and signing input."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("LAP_ERR_SIG: not a compact JWS (expected 3 parts)")
    h_b64, p_b64, s_b64 = parts
    header = json.loads(b64url_decode(h_b64).decode("utf-8"))
    payload = json.loads(b64url_decode(p_b64).decode("utf-8"))
    signature = b64url_decode(s_b64)
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    return {
        "header": header,
        "payload": payload,
        "signature": signature,
        "signing_input": signing_input,
    }


def verify_jws(token: str, signer_did: str) -> Dict[str, Any]:
    """Verify a compact EdDSA JWS using the signer's did:key."""
    decoded = decode_jws(token)
    header = decoded["header"]
    if header.get("alg") != "EdDSA":
        raise ValueError(f"LAP_ERR_SIG: alg {header.get('alg')} (expected EdDSA)")
    pub_key = public_key_from_did(signer_did)
    if not verify_ed25519(pub_key, decoded["signing_input"], decoded["signature"]):
        raise ValueError("LAP_ERR_SIG: signature invalid")
    return {"header": header, "payload": decoded["payload"]}


def check_time_window(
    payload: Dict[str, Any],
    now: Optional[int] = None,
    skew_seconds: int = SKEW_SECONDS,
) -> None:
    """Validate iat and exp timestamps with clock skew tolerance."""
    if now is None:
        now = int(time.time())
    iat = payload.get("iat")
    exp = payload.get("exp")
    if not isinstance(iat, (int, float)):
        raise ValueError("LAP_ERR_EXPIRED: iat missing or not numeric")
    if not isinstance(exp, (int, float)):
        raise ValueError("LAP_ERR_EXPIRED: exp missing or not numeric")
    if now < iat - skew_seconds or now > exp + skew_seconds:
        raise ValueError("LAP_ERR_EXPIRED: token expired or issued in the future")


def verify_passport(token: str, now: Optional[int] = None) -> Dict[str, Any]:
    """
    LIP-1 §6 passport verification (steps 1-5 of 9).
    Validates version, signature, principal existence, anti-self-ownership, and validity window.
    """
    decoded = decode_jws(token)
    header = decoded["header"]
    payload = decoded["payload"]

    if payload.get("v") != "lip1-v0":
        raise ValueError("LAP_ERR_VERSION: unsupported passport version")
    if header.get("alg") != "EdDSA":
        raise ValueError(f"LAP_ERR_SIG: alg {header.get('alg')}")

    principal_id = payload.get("principal", {}).get("id")
    agent_id = payload.get("id")
    if not principal_id:
        raise ValueError("LAP_ERR_SELF_OWNED: principal missing")
    if normalize_did(principal_id) == normalize_did(agent_id or ""):
        raise ValueError("LAP_ERR_SELF_OWNED: agent cannot be its own principal")

    verify_jws(token, principal_id)
    check_time_window(payload, now)
    return payload
