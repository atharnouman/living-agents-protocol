"""
LIP-4 Micro-Core: Server-side verification invariant, idempotency cache, and tripartite receipts.
"""

import hmac
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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


COVERED_COMPONENTS = ('"@method":', '"@target-uri":', '"content-digest":', '"lap-passport-hash":', '"@signature-params":')


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
    components must be present, exactly once each, compared to server-observed method/target
    when given. Byte-exact line matching stays strict (CRLF/trim tolerance rejected three times).
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

    for comp in COVERED_COMPONENTS + ('"idempotency-key":',):
        count = sum(1 for line in lines if line.startswith(comp))
        if count == 0 and comp != '"idempotency-key":':
            raise ValueError(f"LAP_ERR_SIG_PARAMS: missing covered component {comp}")
        if count > 1:
            # One line per component (0.4.14): a second content-digest line could carry another
            # request's digest beside the one the server matches, and so another request's identity.
            raise ValueError(f"LAP_ERR_SIG_PARAMS: duplicate covered component {comp}")

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


MAX_SAFE_AMOUNT = 2**53 - 1  # LIP-3 §4 interop bound: envelopes are JSON read by JavaScript verifiers too


def is_exact_amount(value: Any) -> bool:
    """A cap-comparable amount: a non-negative exact integer no larger than 2^53-1.

    Not a bool (a subclass of int in Python), not a float (999.5, nan, inf), not a string.
    Anything else compared with ``<=`` either passes a negative or compares nonsense, so the
    check refuses it before comparing (cold-start test, 2026-10-17: both ports ran -500000
    under a 1000 cap).
    """
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_SAFE_AMOUNT


def microcore_cap_is_valid(cap: Any) -> bool:
    """LIP-4 cap schema, checked before any comparison: ``max_per_tx`` a non-negative exact
    integer within the interop bound, ``unit`` a non-empty string. ``max_cumulative`` and
    ``window`` are informational in Micro-Core (LIP-4 §2 step 5), so they are not validated
    here; the full LIP-3 shape is ``algebra.cap_is_valid``. Returns False, never raises."""
    if not isinstance(cap, dict):
        return False
    unit = cap.get("unit")
    return is_exact_amount(cap.get("max_per_tx")) and isinstance(unit, str) and unit != ""


def check_invocation(
    envelope: Dict[str, Any],
    act: str,
    resource: str,
    amount: Optional[int] = None,
    unit: Optional[str] = None,
    enforce_magnitude: bool = True,
) -> bool:
    """Steps 4-5: Registered-verb equality, resource path matching, and per-tx cap.

    ``enforce_magnitude=False`` is the disclosure check of a replay (LIP-4 §2 step 3, 0.4.14): the
    action, the resource, the cap schema, the amount's presence and type and the unit are still
    checked against the envelope presented now, but ``amount <= max_per_tx`` is not compared,
    because a replay spends nothing. Everything else is identical to a fresh execution's check.
    """
    env_act = envelope.get("act", [])
    if "*" in env_act:
        raise ValueError("LAP_ERR_ACT: wildcard not allowed in Micro-Core envelopes")
    if act not in env_act:
        raise ValueError(f"LAP_ERR_ACT: {act} not in {env_act}")

    if not path_subsumes(envelope.get("res", ""), resource):
        raise ValueError(f"LAP_ERR_RES: {resource} not covered by {envelope.get('res')}")

    cap = envelope.get("cap")
    if cap is not None:  # a present-but-empty cap is malformed, not "no cap"
        # Schema before arithmetic (LIP-3 §4 F8): a malformed cap never reaches a comparison.
        if not microcore_cap_is_valid(cap):
            raise ValueError("LAP_ERR_CAP: malformed cap (max_per_tx must be a non-negative exact integer, unit a non-empty string)")
        # F5: a capped tool with an indeterminable amount MUST fail closed.
        if amount is None:
            raise ValueError("LAP_ERR_CAP: capped operation requires an amount")
        # The amount is compared only once it is known to be a non-negative exact integer:
        # ``-500 <= cap`` is true, and nan/inf/bool/str compare to nonsense or raise.
        if not is_exact_amount(amount):
            raise ValueError(f"LAP_ERR_CAP: amount must be a non-negative exact integer (got {amount!r})")
        if unit != cap["unit"]:
            raise ValueError(f"LAP_ERR_CAP: unit mismatch ({unit} vs {cap['unit']})")
        if enforce_magnitude and amount > cap["max_per_tx"]:
            raise ValueError(f"LAP_ERR_CAP: amount {amount} exceeds max_per_tx {cap['max_per_tx']}")

    return True


# --------------------------------------------------------------------------- idempotency (step 3 and step 6)

Scope = Union[str, Tuple[Optional[str], str], Tuple[Optional[str], Optional[str], str]]
# a bare agent did (no tenant, no audience); (tenant, agent did); or (audience, tenant, agent did)
Identity = Tuple[str, str, str]  # the signed "@method" and "@target-uri" lines and the server's content-digest line


class LapRefusal(ValueError):
    """A typed ``LAP_ERR_*`` refusal raised by the middleware before the tool ran; the message
    starts with the code. A tool's own exceptions are never wrapped in it, so a binding can tell
    a refusal from the failure of a tool that did run (0.4.14)."""


class NoEffect(Exception):
    """Raised by a mutating tool to say that its external effect did not begin (an input it refused,
    a precondition that failed before any call out). The middleware then abandons the reservation,
    so the same key may be retried fresh. Any other exception leaves the claim INDETERMINATE
    (LIP-4 recovery rule): the effect may have happened, and only reconciliation can say."""


def request_identity(signature_base: str, request_body: Optional[str] = None) -> Identity:
    """The identity of a request for idempotency purposes (LIP-4 §2 step 3, 0.4.14): the signed
    ``@method`` and ``@target-uri`` lines of a VERIFIED signature base, and the content-digest line
    the server computes itself from ``request_body`` (when given; otherwise the base's single
    content-digest line). Not the passport hash (a retry under a replaced passport is the same
    request), not the key itself. Each component must appear exactly once."""
    lines = signature_base.split("\n")

    def only_line(prefix: str) -> str:
        found = [line for line in lines if line.startswith(prefix)]
        if len(found) != 1:
            raise ValueError(f"LAP_ERR_SIG_PARAMS: expected exactly one {prefix} line")
        return found[0]

    method, target, signed_digest = only_line('"@method":'), only_line('"@target-uri":'), only_line('"content-digest":')
    digest = f'"content-digest": sha-256=:{sha256_b64url(request_body)}:' if request_body is not None else signed_digest
    return (method, target, digest)


def claim_scope(
    passport_payload: Dict[str, Any],
    tenant_of: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    aud: Optional[str] = None,
) -> Tuple[str, ...]:
    """The scope an idempotency claim lives in, from a VERIFIED passport payload: ``(tenant, sub)``,
    or ``(aud, tenant, sub)`` when the server's audience is given, so that one store serving two
    server identities keeps their claims apart.

    The tenant is the server's F1 mapping of the verified issuer (``tenant_of(payload)``), by
    default the normalised ``iss`` itself. A claim records its tenant: the same agent key and key
    under an issuer the server does not map to the same tenant is refused (``tenant_mismatch``,
    reported as ``LAP_ERR_ISSUER``), neither replayed nor run again, so a signer change never
    executes an operation twice and never discloses it across principals. A ``tenant_of`` that
    returns nothing is an unknown principal (``LAP_ERR_ISSUER``). Never the passport hash or the
    envelope: a claim survives authority replacement by the same signer or a mapped one.
    """
    sub = passport_payload.get("sub")
    if not sub:
        raise ValueError("LAP_ERR_PASSPORT: sub missing")
    tenant = tenant_of(passport_payload) if tenant_of is not None else normalize_did(passport_payload.get("iss", ""))
    if not isinstance(tenant, str) or not tenant:
        raise ValueError("LAP_ERR_ISSUER: no tenant for this issuer")
    return (aud, tenant, sub) if aud else (tenant, sub)


def _split_scope(scope: Scope) -> Tuple[str, str, str]:
    """``(audience, tenant, agent did)`` with ``""`` for an absent audience or tenant."""
    if isinstance(scope, str):
        return "", "", scope
    if len(scope) == 2:
        tenant, sub = scope
        return "", tenant or "", sub
    aud, tenant, sub = scope
    return aud or "", tenant or "", sub


class IdempotencyCache:
    """Helper: in-memory idempotency cache. A slot is ``(audience, agent_did, key)``; the entry
    records the tenant that reserved it, the request identity, the state, the result and its receipt.

    F6: ``claim()`` reserves atomically within one process (a lock closes the check-then-store
    race between threads). NOT distributed: production deployments MUST back this with a shared
    store (a unique constraint on (audience, agent, key) whose row also holds the tenant and the
    identity, or Redis ``SET NX`` with a value) and fence ``complete()`` to the reservation it
    belongs to, or a load balancer replays a signed key once per replica.

    Request identity (0.4.14): a reservation records the identity of the request it was made for
    (``request_identity``); a later request with the same key and a different identity is
    ``key_reuse`` in every state, never a replay and never a second execution. A row without an
    identity (the legacy ``store()``) fails closed against a lookup that carries one. A reservation
    also records its tenant; a lookup from another tenant is ``tenant_mismatch``. ``lookup()`` reads
    without reserving, so a server can recognise an existing claim before it consults the envelope
    (LIP-4 §2 step 3) and refuse without creating anything.

    Recovery rule (LIP-4, 2026-10-21; raised on A2A #2323): the reservation is written before the
    external effect, the completion after it. A claim whose executor died between the two is
    INDETERMINATE: the effect may or may not have happened. It is refused on retry, never
    re-executed, never released by time alone, and resolves only by reconciliation against the
    effect's system of record: ``complete()`` with the reconciled result if the effect happened,
    ``release()`` if it verifiably did not. This in-process map cannot observe its own death; a
    durable backend detects dead executors (for example through a lease the executor renews) and
    marks their claims. Retention is a published server policy, independent of passport lifetime.
    """

    def __init__(self) -> None:
        self._seen: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _slot(scope: Scope, idempotency_key: str) -> str:
        aud, _tenant, sub = _split_scope(scope)
        return f"{aud}\u0000{sub}\u0000{idempotency_key}"

    @staticmethod
    def _status(entry: Dict[str, Any], tenant: str, identity: Optional[Identity]) -> Dict[str, Any]:
        if entry["tenant"] != tenant:
            return {"status": "tenant_mismatch"}
        if identity is not None and (entry["identity"] is None or tuple(identity) != tuple(entry["identity"])):
            return {"status": "key_reuse"}
        if entry["state"] == "reserved":
            return {"status": "in_flight"}
        if entry["state"] == "indeterminate":
            return {"status": "indeterminate"}
        out: Dict[str, Any] = {"status": "completed", "receipt": entry["result"]}
        if entry["lap_receipt"] is not None:
            out["lap_receipt"] = entry["lap_receipt"]
        return out

    def _entry(self, scope: Scope, idempotency_key: str) -> Optional[Dict[str, Any]]:
        entry = self._seen.get(self._slot(scope, idempotency_key))
        if entry is not None and entry["tenant"] != _split_scope(scope)[1]:
            raise ValueError("LAP_ERR_ISSUER: this claim belongs to another tenant")
        return entry

    def lookup(self, scope: Scope, idempotency_key: str, identity: Optional[Identity] = None) -> Dict[str, Any]:
        """Recognise without reserving: ``absent``, ``tenant_mismatch``, ``key_reuse``, ``in_flight``,
        ``indeterminate`` or ``completed`` (with the stored result under ``receipt`` and, when one
        was minted, its receipt object under ``lap_receipt``). Nothing is written."""
        with self._lock:
            entry = self._seen.get(self._slot(scope, idempotency_key))
            if entry is None:
                return {"status": "absent"}
            return self._status(entry, _split_scope(scope)[1], identity)

    def claim(self, scope: Scope, idempotency_key: str, identity: Optional[Identity] = None,
              meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """F1 (v0.4.10): atomic reservation. Callers proceed ONLY on {"status": "reserved"};
        "in_flight" is a duplicate to reject; "indeterminate" is a duplicate to reject until
        reconciliation; "completed" returns the stored result; "key_reuse" (0.4.14) is the same key
        presented for a different request, and "tenant_mismatch" the same key under an issuer the
        server does not map to this tenant, both refused in every state. ``meta`` (the executing
        passport hash, the reservation time) is kept with the reservation for reconciliation and audit."""
        with self._lock:
            slot = self._slot(scope, idempotency_key)
            entry = self._seen.get(slot)
            if entry is None:
                self._seen[slot] = {"state": "reserved", "tenant": _split_scope(scope)[1],
                                    "identity": tuple(identity) if identity else None,
                                    "result": None, "lap_receipt": None, "meta": dict(meta or {})}
                return {"status": "reserved"}
            return self._status(entry, _split_scope(scope)[1], identity)

    def complete(self, scope: Scope, idempotency_key: str, receipt: Any, lap_receipt: Optional[Dict[str, str]] = None) -> None:
        """Store the result (``receipt`` is its legacy parameter name; ``lap_receipt`` is the receipt
        object, kept apart so that a result that is not a dict still has one) for a reserved claim,
        or for an indeterminate one once reconciliation found that the effect happened. Fenced:
        there must be a reservation, in this tenant, and a completed claim is never overwritten."""
        with self._lock:
            entry = self._entry(scope, idempotency_key)
            if entry is None:
                raise ValueError("LAP_ERR_REPLAY: complete() needs a reservation (claim() first)")
            if entry["state"] == "completed":
                raise ValueError("LAP_ERR_REPLAY: claim already completed; a slow executor must not overwrite it")
            entry["state"], entry["result"], entry["lap_receipt"] = "completed", receipt, lap_receipt

    def mark_indeterminate(self, scope: Scope, idempotency_key: str) -> None:
        """The executor holding this in-flight claim is known to have died (or raised) before
        storing its completion. Only an in-flight claim can become indeterminate."""
        with self._lock:
            entry = self._entry(scope, idempotency_key)
            if entry is None or entry["state"] != "reserved":
                raise ValueError("LAP_ERR_REPLAY: only an in-flight claim can become indeterminate")
            entry["state"] = "indeterminate"

    def release(self, scope: Scope, idempotency_key: str) -> None:
        """Reconciliation found that the effect did not happen: forget the claim, so the next
        request with this key executes fresh. Only an indeterminate claim can be released;
        an in-flight one may still be executing."""
        with self._lock:
            entry = self._entry(scope, idempotency_key)
            if entry is None or entry["state"] != "indeterminate":
                raise ValueError("LAP_ERR_REPLAY: only an indeterminate claim can be released, after reconciliation")
            del self._seen[self._slot(scope, idempotency_key)]

    def abandon(self, scope: Scope, idempotency_key: str) -> None:
        """The executor that holds this reservation reports that the effect never began
        (``NoEffect``): forget the reservation. Only the reserving executor may say so, and only
        for an in-flight claim; a dead executor's claim goes through ``mark_indeterminate``."""
        with self._lock:
            entry = self._entry(scope, idempotency_key)
            if entry is None or entry["state"] != "reserved":
                raise ValueError("LAP_ERR_REPLAY: only the in-flight claim of a tool that raised NoEffect can be abandoned")
            del self._seen[self._slot(scope, idempotency_key)]

    def meta(self, scope: Scope, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """What the reservation recorded (tenant, identity, executing passport hash, time), for reconciliation."""
        with self._lock:
            entry = self._seen.get(self._slot(scope, idempotency_key))
            if entry is None:
                return None
            return {"state": entry["state"], "tenant": entry["tenant"], "identity": entry["identity"], **entry["meta"]}

    def check(self, scope: Scope, idempotency_key: str) -> Optional[Any]:
        """Legacy read (pre-0.4.10): the stored result of a completed claim in this tenant, else None."""
        with self._lock:
            entry = self._seen.get(self._slot(scope, idempotency_key))
            if entry is None or entry["tenant"] != _split_scope(scope)[1] or entry["state"] != "completed":
                return None
            return entry["result"]

    def store(self, scope: Scope, idempotency_key: str, receipt: Any, identity: Optional[Identity] = None) -> None:
        """Legacy write (pre-0.4.10): complete without a prior reservation. Deprecated: the middleware
        never uses it, and a row stored without an identity fails closed against any lookup that
        carries one. Prefer ``claim`` then ``complete``."""
        with self._lock:
            self._seen[self._slot(scope, idempotency_key)] = {
                "state": "completed", "tenant": _split_scope(scope)[1],
                "identity": tuple(identity) if identity else None,
                "result": receipt, "lap_receipt": None, "meta": {}}


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
    """LIP-4 §3: Verify a tripartite receipt line with constant-time equality.

    Returns True, or raises ``ValueError`` carrying the typed reason (``LAP_ERR_RECEIPT_SIG`` for
    a bad signature, ``LAP_ERR_RECEIPT`` for a malformed line or a hash mismatch). It never
    returns False, so callers wrap it in ``try``/``except ValueError``; the Node port throws too.
    """
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
