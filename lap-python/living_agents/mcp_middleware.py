"""
FastMCP & Tool Server Middleware for Living Agents Protocol (LAP) LIP-4 Micro-Core.
Provides the @verify_envelope decorator to authorize tool invocations and emit tripartite receipts.
"""

import contextvars
import copy
import functools
import inspect
import time
from typing import Any, Callable, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .crypto_util import jcs, sha256_hex
from .microcore import (
    IdempotencyCache,
    LapRefusal,
    NoEffect,
    check_invocation,
    claim_scope,
    mint_receipt,
    request_identity,
    verify_microcore_passport,
    verify_request_signature,
)

_CALL_META: "contextvars.ContextVar[Optional[Dict[str, Any]]]" = contextvars.ContextVar("lap_call_meta", default=None)


def last_call_meta() -> Optional[Dict[str, Any]]:
    """What the most recent successful ``verify_envelope`` call in this context produced:
    ``{"receipt": <receipt dict or None>, "replayed": bool}``. A dict result also carries the receipt
    as ``_lap_receipt`` and a replay as ``_lap_replayed``; for a result that is not a dict (a string,
    a list) this is the only way to get them, which is how ``lap_tool`` attaches them to the result
    ``_meta`` (0.4.14). Context-local, so concurrent calls do not see each other's values; ``None``
    after a refusal."""
    return _CALL_META.get()


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
    unit: Optional[str] = None,
    tenant_of: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
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
        expected_aud: Expected audience in the incoming passport JWT (required)
        allowed_issuers: Optional allow-list of principal DIDs (F1: identity is not authorization)
        min_proof_class: Optional floor on the passport's proof class (F1)
        bind_target: Compare the signed ``@target-uri`` to ``resource`` (default; LIP-4 F3)
        idempotency_cache: Mark the tool as MUTATING: ``lap_auth["idempotency_key"]`` becomes
            mandatory and must be a covered component of the signature. The key is recognised
            right after the passport and the signature verify, before the envelope is consulted
            (LIP-4 section 2 step 3, 0.4.14): a completed claim returns the stored result and
            receipt without re-executing, marked ``_lap_replayed`` (replayed only while the
            passport presented now still covers the action, resource and unit; otherwise
            ``LAP_ERR_REPLAY_WITHHELD``); an in-flight or indeterminate claim is refused
            (``LAP_ERR_REPLAY``); the same key for a different request is refused
            (``LAP_ERR_KEY_REUSE``); the same key under an issuer not mapped to the same tenant is
            refused (``LAP_ERR_ISSUER``). A fresh key is claimed atomically after every check passed
            (step 6, F6), in the slot ``(expected_aud, sub, key)`` with the tenant recorded. A tool
            that raises leaves its claim indeterminate unless it raises ``NoEffect``; a failure
            after the tool returned (receipt minting, storage) completes the claim with the result
            so that a retry replays it. The in-process cache is single-process only.
        unit: The fixed unit of the amount, for a capped tool that has no unit argument
            (``unit="USD"``); the alternative to ``unit_param``, never both.
        tenant_of: Maps the verified passport payload to the server's tenant for its issuer
            (LIP-4 F1). Default: the normalised ``iss`` itself, so a second signer presenting the
            same agent key and key is refused rather than joined or run again. Return ``None`` for
            an unknown principal (``LAP_ERR_ISSUER``).

    Refusals are raised as ``LapRefusal`` (a ``ValueError`` whose message starts with the
    ``LAP_ERR_*`` code) before the tool runs; a tool's own exceptions propagate unchanged.
    Configuration mistakes (a missing audience, an ``amount_param`` that is not one of the
    tool's parameters) raise ``TypeError`` when the decorator is applied, so a misconfigured
    server fails at startup rather than refusing every call.
    """

    def decorator(fn: Callable) -> Callable:
        # Startup checks (cold-start test, 2026-10-17): these used to surface only as a
        # refusal of every call, with a message that did not name the mistake.
        if not expected_aud:
            raise TypeError("verify_envelope: expected_aud (this server's identity) is required (LIP-4 F4)")
        if unit_param and unit:
            raise TypeError("verify_envelope: pass unit_param (an argument name) or unit (a fixed unit), not both")
        params = inspect.signature(fn).parameters
        accepts_any = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
        for label, name in (("amount_param", amount_param), ("unit_param", unit_param)):
            if name and name not in params and not accepts_any:
                raise TypeError(f"verify_envelope: {label}={name!r} is not a parameter of {fn.__name__}()")
        if amount_param and not (unit_param or unit):
            raise TypeError("verify_envelope: a capped tool needs its unit: pass unit_param (an argument name) or unit (a fixed unit)")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _CALL_META.set(None)
            # Extract lap_auth context if passed
            lap_auth: Optional[Dict[str, Any]] = kwargs.pop("lap_auth", None)
            if not lap_auth:
                raise LapRefusal("LAP_ERR_AUTH_MISSING: lap_auth context required")

            passport_jwt = lap_auth.get("passport_jwt")
            signature_base = lap_auth.get("signature_base")
            signature_b64url = lap_auth.get("signature_b64url")
            request_body = lap_auth.get("request_body")

            if not passport_jwt or not signature_base or not signature_b64url:
                raise LapRefusal("LAP_ERR_HEADERS: incomplete LAP authorization headers")

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

            scope = identity = idem_key = None
            try:
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

                amount = call_args.get(amount_param) if amount_param else None
                call_unit = call_args.get(unit_param) if unit_param else unit

                def settle(found: Dict[str, Any]) -> Any:
                    """An existing claim for this key, found before or at the reservation (0.4.14)."""
                    status = found["status"]
                    if status == "key_reuse":
                        # Sankalp's rule and draft-ietf-httpapi-idempotency-key-header: one key, one request.
                        raise LapRefusal("LAP_ERR_KEY_REUSE: idempotency key already used for a different request")
                    if status == "tenant_mismatch":
                        # The same agent key and key under a signer this server does not map to the
                        # tenant that holds the claim: neither replayed nor run again (fail closed).
                        raise LapRefusal("LAP_ERR_ISSUER: idempotency key already held under another issuer; "
                                         "no tenant mapping joins them")
                    if status == "in_flight":
                        raise LapRefusal("LAP_ERR_REPLAY: duplicate request already in flight")
                    if status == "indeterminate":
                        # LIP-4 recovery rule: the earlier execution may have completed; never run it
                        # again, never guess from the missing receipt; the operator reconciles.
                        raise LapRefusal("LAP_ERR_REPLAY: an earlier execution of this key may have completed; "
                                         "awaiting reconciliation, not retried")
                    # Completed: the result is evidence of an effect that happened under the authority
                    # valid then. It is disclosed only while the passport presented NOW still covers the
                    # stored request's action, resource and unit; the cap magnitude is exempt, a replay
                    # spends nothing. Otherwise the server says it executed and withholds the result:
                    # recognised, never re-executed, never a new entry (MCP spec issue 3394's split
                    # between recognition and disclosure).
                    try:
                        check_invocation(envelope, act=action, resource=resource, amount=amount, unit=call_unit,
                                         enforce_magnitude=False)
                    except ValueError as refusal:
                        raise LapRefusal("LAP_ERR_REPLAY_WITHHELD: this key executed earlier; its result is withheld "
                                         f"under the current envelope ({str(refusal).split(':')[0]})") from None
                    stored = copy.deepcopy(found["receipt"])  # the stored result, receipt included for a dict
                    receipt = found.get("lap_receipt")
                    if isinstance(stored, dict):
                        stored["_lap_replayed"] = True
                        receipt = receipt or stored.get("_lap_receipt")
                    _CALL_META.set({"receipt": receipt, "replayed": True})
                    return stored

                # Step 3 (LIP-4 section 2 step 3, 0.4.14): a mutating tool RECOGNISES an existing claim
                # before the envelope is consulted, so a retry after the authority was replaced is never
                # mistaken for a fresh request and refused by the cap. The key must sit inside the
                # signed base (LIP-4 section 1), so a captured key cannot be re-attached to a different
                # request; the reservation records the request's identity (signed method and target,
                # the server's own content digest), so the same key for a different request is refused
                # in every state. The lookup reserves nothing: a refusal consumes no claim.
                idem_key = lap_auth.get("idempotency_key")
                if idempotency_cache is not None:
                    if not idem_key:
                        raise LapRefusal("LAP_ERR_IDEMPOTENCY: idempotency_key required for a mutating tool")
                    if f'"idempotency-key": {idem_key}' not in signature_base.split("\n"):
                        raise LapRefusal("LAP_ERR_SIG_PARAMS: idempotency-key is not a covered component")
                    scope = claim_scope(passport_payload, tenant_of, aud=expected_aud)
                    identity = request_identity(signature_base, request_body)
                    known = idempotency_cache.lookup(scope, idem_key, identity)
                    if known["status"] != "absent":
                        return settle(known)

                # Steps 4-5: Verify Action, Resource Path, and Budget Cap (bound amount) for a FRESH
                # execution. The amount must be a non-negative exact integer; check_invocation refuses
                # anything else before comparing it with the cap (0.4.13). A twin may have completed
                # between the lookup and this check: its record wins over an envelope refusal, so a
                # refusal here always means that no execution is recorded under the key.
                try:
                    check_invocation(envelope, act=action, resource=resource, amount=amount, unit=call_unit)
                except ValueError:
                    if idempotency_cache is not None:
                        again = idempotency_cache.lookup(scope, idem_key, identity)
                        if again["status"] != "absent":
                            return settle(again)
                    raise

                # Step 6 (F6): claim the key atomically BEFORE executing. A twin may have won the slot
                # between the lookup and the claim, so every outcome is handled again (three-state claim,
                # v0.4.10; key reuse and tenant mismatch, 0.4.14). The reservation keeps the executing
                # passport hash and the time for reconciliation and audit.
                if idempotency_cache is not None:
                    claim = idempotency_cache.claim(scope, idem_key, identity,
                                                    meta={"passport_hash": "sha256:" + sha256_hex(passport_jwt),
                                                          "reserved_at": int(time.time())})
                    if claim["status"] != "reserved":
                        return settle(claim)
            except LapRefusal:
                raise
            except ValueError as refusal:  # a typed LAP_ERR_* refusal from a verification function
                raise LapRefusal(str(refusal)) from None

            # Step 7: execute the tool function. The reservation is held across the call: an exception
            # means the effect may or may not have happened, so the claim becomes INDETERMINATE (LIP-4
            # recovery rule) and a retry is refused until reconciliation, unless the tool itself says
            # the effect never began (NoEffect), in which case the key is free again.
            try:
                result = fn(*args, **kwargs)
            except NoEffect:
                if idempotency_cache is not None:
                    idempotency_cache.abandon(scope, idem_key)
                raise
            except BaseException:
                if idempotency_cache is not None:
                    idempotency_cache.mark_indeterminate(scope, idem_key)
                raise

            # Step 7, continued: mint the tripartite receipt if a server key is configured, and store the
            # result under the claim. The effect has happened by now, so a failure here (a result that
            # cannot be canonicalised, a storage error) must not strand the claim in flight: the result
            # is stored without a receipt so that a retry replays what happened, and only if even that
            # fails does the claim become indeterminate.
            receipt: Optional[Dict[str, str]] = None
            try:
                if server_private_key and server_did:
                    response_body = jcs(result) if isinstance(result, (dict, list)) else str(result)
                    receipt = mint_receipt(server_private_key, server_did, request_body, response_body)
                    if isinstance(result, dict):
                        result["_lap_receipt"] = receipt
                if idempotency_cache is not None:
                    # Single-process cache (F6): production backs this with a shared store.
                    idempotency_cache.complete(scope, idem_key, copy.deepcopy(result), lap_receipt=receipt)
            except BaseException:
                if idempotency_cache is not None:
                    try:
                        idempotency_cache.complete(scope, idem_key, copy.deepcopy(result), lap_receipt=receipt)
                    except BaseException:
                        try:
                            idempotency_cache.mark_indeterminate(scope, idem_key)
                        except ValueError:
                            pass  # already completed or already marked
                raise

            _CALL_META.set({"receipt": receipt, "replayed": False})
            return result

        return wrapper

    return decorator
