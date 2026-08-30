"""
Living Agents Protocol (LAP) — Python Reference Library & FastMCP Middleware.
"""

from .algebra import (
    ACTION_REGISTRY_V0,
    WINDOW_SECONDS,
    cap_subsumes,
    counterparty_subsumes,
    dag_subsumes,
    path_subsumes,
    scope_subsumes,
    verify_envelope_attenuation,
)
from .crypto_util import (
    b58decode,
    b58encode,
    b64url_decode,
    b64url_encode,
    did_key_from_raw_public_key,
    did_key_to_raw_public_key,
    jcs,
    normalize_did,
    normalize_uri,
    public_key_from_did,
    public_key_from_raw,
    sha256_b64url,
    sha256_hex,
    verify_ed25519,
)
from .jws import (
    decode_jws,
    sign_jws,
    verify_jws,
    verify_passport,
)
from .mcp_middleware import verify_envelope
from .microcore import (
    IdempotencyCache,
    check_invocation,
    make_idempotency_cache,
    mint_receipt,
    verify_microcore_passport,
    verify_receipt,
    verify_request_signature,
)

__version__ = "0.4.3"

__all__ = [
    "b58encode",
    "b58decode",
    "b64url_encode",
    "b64url_decode",
    "sha256_hex",
    "sha256_b64url",
    "jcs",
    "normalize_did",
    "normalize_uri",
    "did_key_to_raw_public_key",
    "public_key_from_raw",
    "public_key_from_did",
    "did_key_from_raw_public_key",
    "verify_ed25519",
    "sign_jws",
    "decode_jws",
    "verify_jws",
    "verify_passport",
    "dag_subsumes",
    "path_subsumes",
    "cap_subsumes",
    "counterparty_subsumes",
    "scope_subsumes",
    "verify_envelope_attenuation",
    "verify_microcore_passport",
    "verify_request_signature",
    "check_invocation",
    "make_idempotency_cache",
    "IdempotencyCache",
    "mint_receipt",
    "verify_receipt",
    "verify_envelope",
    "ACTION_REGISTRY_V0",
    "WINDOW_SECONDS",
]
