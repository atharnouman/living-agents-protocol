"""
FastMCP & Tool Server Middleware for Living Agents Protocol (LAP) LIP-4 Micro-Core.
Provides the @verify_envelope decorator to authorize tool invocations and emit tripartite receipts.
"""

import copy
import functools
import inspect
from typing import Any, Callable, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .crypto_util import jcs
from .microcore import (
    IdempotencyCache,
    check_invocation,
    mint_receipt,
    verify_microcore_passport,
    verify_request_signature,
)


def verify_envelope(
    action: str,
    resource: str,
    amount_param: Optional[str] = None,
    unit_param: Optional[str] = None,
    server_private_key: Optional[Ed25519PrivateKey] = None,
    server_did: Optional[str] = None,
    expected_aud: Optional[str] = None,
    allowed_issuers: Optional[list] = None,
    min_proof_class: Optional[str] = None,
    bind_target: bool = True,
    idempotency_cache: Optional[IdempotencyCache] = None,
) -> Callable:
    """
    Decorator for MCP tool functions enforcing LAP LIP-4 Micro-Core authorization.

    Args:
        action: Registered action string (e.g. "finance:pay", "data:read")
        resource: Target resource URI (e.g. "mcp://tools.example.com/billing/pay")
        amount_param: Name of the function argument containing the transaction amount
        unit_param: Name of the function argument containing the currency/unit string
        server_private_key: Tool server Ed25519 private key for minting receipts
        server_did: Tool server did:key identifier
        expected_aud: Expected audience in the incoming passport JWT
        allowed_issuers: Optional allow-list of principal DIDs (F1: identity is not authorization)
        min_proof_class: Optional floor on the passport's proof class (F1)
        bind_target: Compare the signed ``@target-uri`` to ``resource`` (default; LIP-4 F3)
        idempotency_cache: Mark the tool as MUTATING: ``lap_auth["idempotency_key"]`` becomes
            mandatory and must be a covered component of the signature; ``(sub, key)`` is
            claimed atomically before execution (LIP-4 section 2 step 5, F6). A completed
            claim returns the cached result and receipt without re-executing; an in-flight
            duplicate is refused. The in-process cache is single-process only.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract lap_auth context if passed
            lap_auth: Optional[Dict[str, Any]] = kwargs.pop("lap_auth", None)
            if not lap_auth:
                raise ValueError("LAP_ERR_AUTH_MISSING: lap_auth context required")

            passport_jwt = lap_auth.get("passport_jwt")
            signature_base = lap_auth.get("signature_base")
            signature_b64url = lap_auth.get("signature_b64url")
            request_body = lap_auth.get("request_body")

            if not passport_jwt or not signature_base or not signature_b64url:
                raise ValueError("LAP_ERR_HEADERS: incomplete LAP authorization headers")

            # F5: bind the REAL invocation arguments (defaults applied) so positional
            # args cannot bypass the cap. In production the raw request bytes AND the
            # transport method/target MUST come from the trusted MCP/ASGI context, not
            # from this application-supplied lap_auth dict — the cap is enforced on the
            # bound amount regardless.
            bound = inspect.signature(fn).bind(*args, **kwargs)
            bound.apply_defaults()
            call_args = dict(bound.arguments)
            call_args.pop("lap_auth", None)  # never part of the signed body (it carries the signature)

            # Preferred: no caller-supplied body at all — the signed bytes are derived from the
            # server's OWN bound arguments (canonical JSON), so the signature is bound to what
            # actually executes. A caller-supplied request_body is accepted for transports that
            # deliver raw bytes (HTTP), where the transport layer must supply them.
            if request_body is None:
                request_body = jcs(call_args)

            # Step 1: Verify Passport JWT (expected_aud is mandatory downstream)
            now = lap_auth.get("now")
            passport_payload = verify_microcore_passport(
                passport_jwt, expected_aud=expected_aud, now=now,
                allowed_issuers=allowed_issuers, min_proof_class=min_proof_class,
            )
            envelope = passport_payload["lap"]["envelope"]
            sub = passport_payload["sub"]  # F2: holder-of-key from the verified passport

            # Step 2: Verify RFC 9421 Request Signature against the verified subject.
            # F6 (v0.4.10): bind the signed @target-uri to THIS tool's resource by default
            # (LIP-4 F3 — the server compares the signed target to what it serves), so a
            # signature scoped to one tool cannot be replayed against another under one
            # envelope. MCP clients set @target-uri to the tool resource (see examples/mcp-server).
            # `bind_target=False` is for transports whose signed target is a distinct URL that a
            # different layer verifies. Method binding is transport-specific and left to that layer.
            verify_request_signature(
                passport_jwt, sub, signature_base, signature_b64url, request_body,
                expected_target=(resource if bind_target else None),
            )

            # Steps 3-4: Verify Action, Resource Path, and Budget Cap (bound amount)
            amount = call_args.get(amount_param) if amount_param else None
            unit = call_args.get(unit_param) if unit_param else None
            check_invocation(envelope, act=action, resource=resource, amount=amount, unit=unit)

            # Step 5 (LIP-4 section 2 step 5, F6): a mutating tool claims (sub, idempotency key)
            # atomically BEFORE executing. The key must sit inside the signed base (LIP-4 section 1),
            # so a captured key cannot be re-attached to a different request. A completed claim
            # returns the cached result (with its receipt) without re-executing; a concurrent
            # in-flight duplicate is refused rather than run twice (three-state claim, v0.4.10).
            idem_key = lap_auth.get("idempotency_key")
            if idempotency_cache is not None:
                if not idem_key:
                    raise ValueError("LAP_ERR_IDEMPOTENCY: idempotency_key required for a mutating tool")
                if f'"idempotency-key": {idem_key}' not in signature_base.split("\n"):
                    raise ValueError("LAP_ERR_SIG_PARAMS: idempotency-key is not a covered component")
                claim = idempotency_cache.claim(sub, idem_key)
                if claim["status"] == "completed":
                    return copy.deepcopy(claim["receipt"])  # the stored result, receipt included
                if claim["status"] == "in_flight":
                    raise ValueError("LAP_ERR_REPLAY: duplicate request already in flight")

            # Execute the tool function
            result = fn(*args, **kwargs)

            # Step 6: Mint Tripartite Receipt if server key is configured
            if server_private_key and server_did:
                response_body = jcs(result) if isinstance(result, (dict, list)) else str(result)
                receipt = mint_receipt(server_private_key, server_did, request_body, response_body)
                if isinstance(result, dict):
                    result["_lap_receipt"] = receipt

            if idempotency_cache is not None:
                # Single-process cache (F6): production backs this with a shared store.
                idempotency_cache.complete(sub, idem_key, copy.deepcopy(result))

            return result

        return wrapper

    return decorator
