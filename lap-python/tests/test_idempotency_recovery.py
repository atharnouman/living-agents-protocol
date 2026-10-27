"""Recovery of an in-flight idempotency claim after a crash (LIP-4 recovery rule, 2026-10-21,
raised by an external review on A2A #2323): an external effect completes, then the process dies
before storing its completion. The claim is INDETERMINATE: refused on retry, never re-executed,
never released by time alone, resolved only by reconciliation.
"""
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import (
    EXTENSION_ID,
    IdempotencyCache,
    claim_scope,
    did_key_from_raw_public_key,
    lap_auth_from_meta,
    request_identity,
    sign_jws,
    sign_tool_call,
    verify_envelope,
)

RESOURCE = "mcp://tools.example.com/billing/pay"
SERVER_ID = "did:web:tools.example.com"
ENVELOPE = {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
            "cap": {"max_per_tx": 1000, "unit": "USD", "window": "tx"}}


def test_an_indeterminate_claim_is_refused_until_reconciliation_completes_it():
    cache = IdempotencyCache()
    assert cache.claim("did:key:a", "k") == {"status": "reserved"}
    cache.mark_indeterminate("did:key:a", "k")                    # the executor died after reserving
    assert cache.claim("did:key:a", "k") == {"status": "indeterminate"}   # a retry is refused, not run
    assert cache.check("did:key:a", "k") is None                  # no receipt exists yet
    with pytest.raises(ValueError, match="only an in-flight claim"):
        cache.mark_indeterminate("did:key:a", "never-claimed")
    cache.complete("did:key:a", "k", {"paid": True, "reconciled": True})   # the effect had happened
    assert cache.claim("did:key:a", "k") == {"status": "completed", "receipt": {"paid": True, "reconciled": True}}


def test_release_after_reconciliation_found_no_effect_lets_the_same_key_run_fresh():
    cache = IdempotencyCache()
    cache.claim("did:key:a", "k")
    with pytest.raises(ValueError, match="only an indeterminate claim"):
        cache.release("did:key:a", "k")                            # in flight: the executor may be running
    cache.mark_indeterminate("did:key:a", "k")
    cache.release("did:key:a", "k")                                # reconciliation: nothing happened
    assert cache.claim("did:key:a", "k") == {"status": "reserved"}


def test_middleware_refuses_an_indeterminate_key_without_executing_and_replays_the_reconciled_result():
    principal_key = Ed25519PrivateKey.generate()
    principal_did = did_key_from_raw_public_key(principal_key.public_key().public_bytes_raw())
    agent_key = Ed25519PrivateKey.generate()
    agent_did = did_key_from_raw_public_key(agent_key.public_key().public_bytes_raw())
    now = int(time.time())
    passport = sign_jws(
        {"iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": now, "exp": now + 600,
         "lap": {"v": 0, "proof_class": "self-asserted", "envelope": ENVELOPE}},
        principal_key, principal_did + "#key-1", "lap-microcore+jwt",
    )
    cache, runs = IdempotencyCache(), []

    @verify_envelope(action="finance:pay", resource=RESOURCE, amount_param="amount", unit_param="unit",
                     expected_aud=SERVER_ID, idempotency_cache=cache)
    def pay(invoice: str, amount: int, unit: str = "USD"):
        runs.append(invoice)
        return {"status": "paid", "invoice": invoice, "amount": amount}

    args = {"invoice": "INV-9", "amount": 5, "unit": "USD"}

    def call():
        auth = lap_auth_from_meta({EXTENSION_ID: sign_tool_call(args, RESOURCE, passport, agent_key, agent_did, now, "k1")}, args)
        return pay(lap_auth=auth, **args)

    # A durable backend found the executor of this claim dead after the effect may have happened.
    # Claims live in the slot (audience, agent, key) with the tenant (the verified issuer by default)
    # and the request identity recorded (0.4.14); a reservation without an identity would fail closed.
    scope = claim_scope({"iss": principal_did, "sub": agent_did}, aud=SERVER_ID)
    identity = request_identity(sign_tool_call(args, RESOURCE, passport, agent_key, agent_did, now, "k1")["signature_base"])
    cache.claim(scope, "k1", identity)
    cache.mark_indeterminate(scope, "k1")
    with pytest.raises(ValueError, match="LAP_ERR_REPLAY: .*awaiting reconciliation"):
        call()
    assert runs == []                                               # never executed again
    # Reconciliation against the system of record: the payment had gone through.
    cache.complete(scope, "k1", {"status": "paid", "invoice": "INV-9", "amount": 5, "reconciled": True})
    assert call()["reconciled"] is True                             # the retry gets the reconciled result
    assert runs == []
