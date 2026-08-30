"""
LIP-4 Micro-Core: Server-side verification invariant, idempotency cache, and tripartite receipts.
"""

import hmac
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .algebra import path_subsumes
from .crypto_util import (
    b64url_decode,
    b64url_encode,
    normalize_did,
    normalize_uri,
    public_key_from_did,
    sha256_b64url,
    sha256_hex,
    verify_ed25519,
)
from .jws import check_time_window, decode_jws, verify_jws

PROOF_CLASS_ORDER = ["self-asserted", "domain-validated", "org-validated", "gov-validated"]


def verify_microcore_passport(
    passport_jwt: str,
    expected_aud: Optional[str] = None,
    now: Optional[int] = None,
    allowed_issuers: Optional[List[str]] = None,
    min_proof_class: Optional[str] = None,
) -> Dict[str, Any]:
    """Step 1: Verify the principal-signed passport JWT, audience, and time window.

    F4: ``expected_aud`` is MANDATORY — a missing audience is fail-open cross-server
    replay. F1: ``allowed_issuers``/``min_proof_class`` let a server refuse self-asserted
    or unknown principals. A valid passport proves identity + envelope integrity; it is
    NOT by itself authority over a server-owned resource.
    """
    if not expected_aud:
        raise ValueError("LAP_ERR_AUDIENCE: expected_aud (this server's identity) is required")
    decoded = decode_jws(passport_jwt)
    iss = decoded["payload"].get("iss")
    if not iss:
        raise ValueError("LAP_ERR_PASSPORT: iss missing")
    verified = verify_jws(passport_jwt, iss)
    payload = verified["payload"]

    aud = payload.get("aud")
    if not aud:
        raise ValueError("LAP_ERR_AUDIENCE: aud missing")
    if normalize_uri(aud) != normalize_uri(expected_aud):
        raise ValueError(f"LAP_ERR_AUDIENCE: expected {expected_aud}, got {aud}")

    check_time_window(payload, now)
    if not payload.get("lap", {}).get("envelope"):
        raise ValueError("LAP_ERR_PASSPORT_SIG: envelope missing")

    if allowed_issuers is not None and normalize_did(iss) not in [normalize_did(a) for a in allowed_issuers]:
        raise ValueError("LAP_ERR_ISSUER: issuer not in server allow-list")
    if min_proof_class:
        have = payload.get("lap", {}).get("proof_class")
        if have not in PROOF_CLASS_ORDER or PROOF_CLASS_ORDER.index(have) < PROOF_CLASS_ORDER.index(min_proof_class):
            raise ValueError("LAP_ERR_PROOF_CLASS: below required floor")
    return payload


def verify_request_signature(
    passport_jwt: str,
    sub: str,
    signature_base: str,
    signature_b64url: str,
    request_body: str,
    expected_method: Optional[str] = None,
    expected_target: Optional[str] = None,
) -> bool:
    """Step 2: Verify the AGENT's RFC 9421 signature.

    F2: the verification key is derived from the verified passport's ``sub``
    (holder-of-key), never from a caller-supplied DID. F3: the mandatory covered
    components must be present, compared to server-observed method/target when given.
    Byte-exact line matching stays strict (CRLF/trim tolerance rejected three times).
    """
    if not sub:
        raise ValueError("LAP_ERR_REQ_SIG: sub (verified passport subject) required")
    key = public_key_from_did(sub)
    sig_bytes = b64url_decode(signature_b64url)
    if not verify_ed25519(key, signature_base.encode("ascii"), sig_bytes):
        raise ValueError("LAP_ERR_REQ_SIG: request signature invalid")

    lines = signature_base.split("\n")

    def find_line(prefix: str) -> Optional[str]:
        return next((line for line in lines if line.startswith(prefix)), None)

    for comp in ('"@method":', '"@target-uri":', '"content-digest":', '"lap-passport-hash":', '"@signature-params":'):
        if find_line(comp) is None:
            raise ValueError(f"LAP_ERR_SIG_PARAMS: missing covered component {comp}")

    expected_digest = f'"content-digest": sha-256=:{sha256_b64url(request_body)}:'
    if expected_digest not in lines:
        raise ValueError("LAP_ERR_DIGEST: content-digest line mismatch")
    expected_passport_line = f'"lap-passport-hash": sha256:{sha256_hex(passport_jwt)}'
    if expected_passport_line not in lines:
        raise ValueError("LAP_ERR_DIGEST: passport hash mismatch")

    if expected_method is not None and find_line('"@method":') != f'"@method": {expected_method}':
        raise ValueError("LAP_ERR_METHOD: signed method does not match transport")
    if expected_target is not None and find_line('"@target-uri":') != f'"@target-uri": {expected_target}':
        raise ValueError("LAP_ERR_TARGET: signed target does not match transport")
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
    if cap:
        # F5: a capped tool with an indeterminable amount MUST fail closed.
        if amount is None:
            raise ValueError("LAP_ERR_CAP: capped operation requires an amount")
        if unit != cap.get("unit"):
            raise ValueError(f"LAP_ERR_CAP: unit mismatch ({unit} vs {cap.get('unit')})")
        if amount > cap.get("max_per_tx", 0):
            raise ValueError(f"LAP_ERR_CAP: amount {amount} exceeds max_per_tx {cap.get('max_per_tx')}")

    return True


class IdempotencyCache:
    """Helper: in-memory idempotency cache keyed by (agent_did, idempotency_key).

    F6: claim() reserves atomically within one process, closing the check-then-store
    race. NOT distributed - production deployments MUST back this with a shared store
    (Redis SET NX / DB unique constraint) or a load balancer replays a signed key
    once per replica.
    """

    def __init__(self) -> None:
        self._seen: Dict[str, Any] = {}

    @staticmethod
    def _key(agent_did: str, idempotency_key: str) -> str:
        return f"{agent_did}\u0000{idempotency_key}"

    def claim(self, agent_did: str, idempotency_key: str) -> Optional[Any]:
        key = self._key(agent_did, idempotency_key)
        if key in self._seen:
            return self._seen[key]
        self._seen[key] = None
        return None

    def complete(self, agent_did: str, idempotency_key: str, receipt: Any) -> None:
        self._seen[self._key(agent_did, idempotency_key)] = receipt

    def check(self, agent_did: str, idempotency_key: str) -> Optional[Any]:
        return self._seen.get(self._key(agent_did, idempotency_key))

    def store(self, agent_did: str, idempotency_key: str, receipt: Any) -> None:
        self._seen[self._key(agent_did, idempotency_key)] = receipt


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
