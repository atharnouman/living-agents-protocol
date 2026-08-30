"""
LIP-4 Micro-Core: Server-side verification invariant, idempotency cache, and tripartite receipts.
"""

import hmac
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .algebra import path_subsumes
from .crypto_util import (
    b64url_decode,
    b64url_encode,
    normalize_uri,
    public_key_from_did,
    sha256_b64url,
    sha256_hex,
    verify_ed25519,
)
from .jws import check_time_window, decode_jws, verify_jws


def verify_microcore_passport(
    passport_jwt: str,
    expected_aud: Optional[str] = None,
    now: Optional[int] = None,
) -> Dict[str, Any]:
    """Step 1: Verify the principal-signed passport JWT, audience, and time window."""
    decoded = decode_jws(passport_jwt)
    iss = decoded["payload"].get("iss")
    if not iss:
        raise ValueError("LAP_ERR_PASSPORT: iss missing")
    verified = verify_jws(passport_jwt, iss)
    payload = verified["payload"]

    aud = payload.get("aud")
    if not aud:
        raise ValueError("LAP_ERR_AUDIENCE: aud missing")
    if expected_aud and normalize_uri(aud) != normalize_uri(expected_aud):
        raise ValueError(f"LAP_ERR_AUDIENCE: expected {expected_aud}, got {aud}")

    check_time_window(payload, now)
    if not payload.get("lap", {}).get("envelope"):
        raise ValueError("LAP_ERR_PASSPORT_SIG: envelope missing")
    return payload


def verify_request_signature(
    passport_jwt: str,
    agent_did: str,
    signature_base: str,
    signature_b64url: str,
    request_body: str,
) -> bool:
    """Step 2: Verify the agent's RFC 9421 signature over the signature base."""
    key = public_key_from_did(agent_did)
    sig_bytes = b64url_decode(signature_b64url)
    if not verify_ed25519(key, signature_base.encode("ascii"), sig_bytes):
        raise ValueError("LAP_ERR_REQ_SIG: request signature invalid")

    # Strict byte-exact line matching. Trim/CRLF tolerance was twice proposed and
    # twice REJECTED at triage: RFC 9421 signature bases bind exact bytes, and the
    # signature above already fails on any transit mutation — loosening here only
    # weakens conformance. (Parity with the Node reference.)
    lines = signature_base.split("\n")
    expected_digest = f'"content-digest": sha-256=:{sha256_b64url(request_body)}:'
    if expected_digest not in lines:
        raise ValueError("LAP_ERR_DIGEST: content-digest line mismatch")

    expected_passport_line = f'"lap-passport-hash": sha256:{sha256_hex(passport_jwt)}'
    if expected_passport_line not in lines:
        raise ValueError("LAP_ERR_DIGEST: passport hash mismatch")

    return True


def check_invocation(
    envelope: Dict[str, Any],
    act: str,
    resource: str,
    amount: Optional[int] = None,
    unit: Optional[str] = None,
) -> bool:
    """Steps 3-4: Registered-verb equality, resource path matching, and per-tx cap."""
    env_act = envelope.get("act", [])
    if "*" in env_act:
        raise ValueError("LAP_ERR_ACT: wildcard not allowed in Micro-Core envelopes")
    if act not in env_act:
        raise ValueError(f"LAP_ERR_ACT: {act} not in {env_act}")

    if not path_subsumes(envelope.get("res", ""), resource):
        raise ValueError(f"LAP_ERR_RES: {resource} not covered by {envelope.get('res')}")

    cap = envelope.get("cap")
    if cap and amount is not None:
        if unit != cap.get("unit"):
            raise ValueError(f"LAP_ERR_CAP: unit mismatch ({unit} vs {cap.get('unit')})")
        if amount > cap.get("max_per_tx", 0):
            raise ValueError(f"LAP_ERR_CAP: amount {amount} exceeds max_per_tx {cap.get('max_per_tx')}")

    return True


class IdempotencyCache:
    """Helper: In-memory idempotency cache keyed by (agent_did, idempotency_key)."""

    def __init__(self) -> None:
        self._seen: Dict[str, Any] = {}

    def check(self, agent_did: str, idempotency_key: str) -> Optional[Any]:
        return self._seen.get(f"{agent_did}\u0000{idempotency_key}")

    def store(self, agent_did: str, idempotency_key: str, receipt: Any) -> None:
        self._seen[f"{agent_did}\u0000{idempotency_key}"] = receipt


def make_idempotency_cache() -> IdempotencyCache:
    return IdempotencyCache()


def mint_receipt(
    server_private_key: Ed25519PrivateKey,
    server_did: str,
    request_body: str,
    response_body: str,
) -> Dict[str, str]:
    """LIP-4 §3: Mint a tripartite receipt signed by the tool server."""
    req_hash = f"sha256:{sha256_hex(request_body)}"
    resp_hash = f"sha256:{sha256_hex(response_body)}"
    receipt_base = f"{req_hash}:{resp_hash}"
    sig = server_private_key.sign(receipt_base.encode("ascii"))
    return {
        "receipt_base": receipt_base,
        "receipt_signature_b64url": b64url_encode(sig),
        "server_did": server_did,
    }


def verify_receipt(
    receipt_base: str,
    receipt_signature_b64url: str,
    server_did: str,
    request_body: Optional[str] = None,
    response_body: Optional[str] = None,
) -> bool:
    """LIP-4 §3: Verify a tripartite receipt line with constant-time equality."""
    key = public_key_from_did(server_did)
    sig_bytes = b64url_decode(receipt_signature_b64url)
    if not verify_ed25519(key, receipt_base.encode("ascii"), sig_bytes):
        raise ValueError("LAP_ERR_RECEIPT_SIG: signature invalid")

    parts = receipt_base.split(":")
    if len(parts) != 4 or parts[0] != "sha256" or parts[2] != "sha256":
        raise ValueError("LAP_ERR_RECEIPT: malformed receipt base")

    req_part = f"sha256:{parts[1]}"
    resp_part = f"sha256:{parts[3]}"

    if request_body is not None:
        expected_req = f"sha256:{sha256_hex(request_body)}"
        if not hmac.compare_digest(req_part, expected_req):
            raise ValueError("LAP_ERR_RECEIPT: request hash mismatch")

    if response_body is not None:
        expected_resp = f"sha256:{sha256_hex(response_body)}"
        if not hmac.compare_digest(resp_part, expected_resp):
            raise ValueError("LAP_ERR_RECEIPT: response hash mismatch")

    return True
