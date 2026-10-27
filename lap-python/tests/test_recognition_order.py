"""Recognition before authority (LIP-4 section 2 step 3, 0.4.14): a mutating tool recognises an
existing idempotency claim right after the passport and the call signature verify, before the
envelope is consulted. Two independent reviews (2026-10-28) reproduced three faults in 0.4.13:
a retry after a cap cut was refused by the cap before the stored result was found; one key
reused for a different request, or by another tool sharing the cache, replayed the first result;
and a second principal with the same agent key replayed the first principal's execution.
"""
import hashlib
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import (
    EXTENSION_ID,
    IdempotencyCache,
    NoEffect,
    claim_scope,
    did_key_from_raw_public_key,
    jcs,
    lap_auth_from_meta,
    request_identity,
    sign_jws,
    sign_tool_call,
    verify_envelope,
    verify_receipt,
)

PAY = "mcp://tools.example.com/billing/pay"
REFUND = "mcp://tools.example.com/billing/refund"
SERVER_ID = "did:web:tools.example.com"
NOW = int(time.time())


def key_from(label):
    k = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(label.encode()).digest())
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


PRINCIPAL_A, PRINCIPAL_A_DID = key_from("recognition principal A")
PRINCIPAL_B, PRINCIPAL_B_DID = key_from("recognition principal B")
AGENT, AGENT_DID = key_from("recognition agent")
SERVER, SERVER_DID = key_from("recognition server")


def envelope(act=("finance:pay",), res="mcp://tools.example.com/billing/**", cap=1000, unit="USD"):
    env = {"act": list(act), "res": res}
    if cap is not None:
        env["cap"] = {"max_per_tx": cap, "unit": unit, "window": "tx"}
    return env


def passport(env, principal=PRINCIPAL_A, principal_did=PRINCIPAL_A_DID, iat=NOW, ttl=600):
    return sign_jws(
        {"iss": principal_did, "sub": AGENT_DID, "aud": SERVER_ID, "iat": iat, "exp": iat + ttl,
         "lap": {"v": 0, "proof_class": "self-asserted", "envelope": env}},
        principal, principal_did + "#key-1", "lap-microcore+jwt",
    )


def tool(cache, resource=PAY, action="finance:pay", behaviour=None, **options):
    runs = []

    @verify_envelope(action=action, resource=resource, amount_param="amount", unit_param="unit",
                     expected_aud=SERVER_ID, server_private_key=SERVER, server_did=SERVER_DID,
                     idempotency_cache=cache, **options)
    def pay(invoice: str, amount: int, unit: str = "USD"):
        runs.append(invoice)
        if behaviour is not None:
            behaviour(invoice)
        return {"status": "paid", "invoice": invoice, "amount": amount}

    return pay, runs


def call(fn, pp, args, key, resource=PAY, now=None):
    signed = sign_tool_call(args, resource, pp, AGENT, AGENT_DID, NOW, key)
    auth = lap_auth_from_meta({EXTENSION_ID: signed}, args)
    if now is not None:
        auth["now"] = now
    return fn(lap_auth=auth, **args)


def refuses(fn, pp, args, key, code, **kw):
    with pytest.raises(ValueError, match=code) as e:
        call(fn, pp, args, key, **kw)
    return str(e.value)


def scope_a():
    return claim_scope({"iss": PRINCIPAL_A_DID, "sub": AGENT_DID})


ARGS = {"invoice": "INV-1", "amount": 500, "unit": "USD"}


def test_a_retry_after_the_cap_was_cut_replays_the_stored_result_and_receipt():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    first = call(pay, passport(envelope(cap=1000)), ARGS, "k1")
    cut = passport(envelope(cap=100))                                   # the authority was replaced

    again = call(pay, cut, ARGS, "k1")                                  # same key, same request

    assert runs == ["INV-1"]                                            # not executed again
    assert again.pop("_lap_replayed") is True and "_lap_replayed" not in first
    assert again == first                                               # the stored result, receipt included
    assert cache.lookup(scope_a(), "k1")["status"] == "completed"       # no new entry
    refuses(pay, cut, {**ARGS, "invoice": "INV-2"}, "k2", "LAP_ERR_CAP")  # a fresh one is refused by the cut
    assert runs == ["INV-1"]


def test_a_retry_after_the_action_was_removed_is_recognised_but_withheld():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    first = call(pay, passport(envelope()), ARGS, "k1")

    reason = refuses(pay, passport(envelope(act=("data:read",))), ARGS, "k1", "LAP_ERR_REPLAY_WITHHELD")
    assert "LAP_ERR_ACT" in reason and runs == ["INV-1"]
    assert cache.lookup(scope_a(), "k1")["status"] == "completed"       # recognised: not a new entry, not key reuse

    reason = refuses(pay, passport(envelope(res="mcp://tools.example.com/admin/**")), ARGS, "k1", "LAP_ERR_REPLAY_WITHHELD")
    assert "LAP_ERR_RES" in reason
    reason = refuses(pay, passport(envelope(unit="EUR")), ARGS, "k1", "LAP_ERR_REPLAY_WITHHELD")
    assert "LAP_ERR_CAP" in reason                                      # the unit changed; the magnitude alone is exempt

    restored = call(pay, passport(envelope()), ARGS, "k1")              # authority restored: the result is released
    assert restored.pop("_lap_replayed") is True and restored == first and runs == ["INV-1"]


def test_the_same_key_for_a_different_request_is_refused_in_every_state():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pp = passport(envelope())
    call(pay, pp, ARGS, "k1")
    other = {**ARGS, "amount": 900}

    refuses(pay, pp, other, "k1", "LAP_ERR_KEY_REUSE")                  # completed
    identity = request_identity(sign_tool_call(ARGS, PAY, pp, AGENT, AGENT_DID, NOW, "k2")["signature_base"])
    cache.claim(scope_a(), "k2", identity)                              # in flight (a twin holds it)
    refuses(pay, pp, other, "k2", "LAP_ERR_KEY_REUSE")
    refuses(pay, pp, ARGS, "k2", "LAP_ERR_REPLAY: duplicate request already in flight")
    cache.mark_indeterminate(scope_a(), "k2")                           # its executor died
    refuses(pay, pp, other, "k2", "LAP_ERR_KEY_REUSE")
    refuses(pay, pp, ARGS, "k2", "awaiting reconciliation")
    assert runs == ["INV-1"]

    call(pay, pp, other, "k3")                                          # a new key is a new operation
    assert runs == ["INV-1", "INV-1"]


def test_two_principals_sharing_an_agent_key_never_share_a_claim():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pp_a = passport(envelope())
    pp_b = passport(envelope(), PRINCIPAL_B, PRINCIPAL_B_DID)

    call(pay, pp_a, ARGS, "k1")
    second = call(pay, pp_b, ARGS, "k1")                                # same agent key, key and arguments
    assert runs == ["INV-1", "INV-1"] and "_lap_replayed" not in second  # a separate operation, executed

    one_tenant = IdempotencyCache()
    pay, runs = tool(one_tenant, tenant_of=lambda payload: "tenant-shared")
    call(pay, pp_a, ARGS, "k1")
    assert call(pay, pp_b, ARGS, "k1").pop("_lap_replayed") is True     # mapped to one tenant: recognised
    assert runs == ["INV-1"]

    pay, runs = tool(IdempotencyCache(), tenant_of=lambda payload: None)
    refuses(pay, pp_a, ARGS, "k1", "LAP_ERR_ISSUER")                    # an unknown principal has no scope
    assert runs == []


def test_two_tools_sharing_one_cache_do_not_replay_each_other():
    cache = IdempotencyCache()
    pay, pay_runs = tool(cache, resource=PAY)
    refund, refund_runs = tool(cache, resource=REFUND, action="finance:pay")
    pp = passport(envelope())

    call(pay, pp, ARGS, "k1")
    refuses(refund, pp, ARGS, "k1", "LAP_ERR_KEY_REUSE", resource=REFUND)
    assert pay_runs == ["INV-1"] and refund_runs == []


def test_a_tool_exception_leaves_the_claim_indeterminate_unless_it_raises_no_effect():
    cache = IdempotencyCache()

    def fail(invoice):
        if invoice == "INV-crash":
            raise RuntimeError("the gateway timed out after the call went out")
        if invoice == "INV-noeffect":
            raise NoEffect("invoice already settled; nothing was sent")

    pay, runs = tool(cache, behaviour=fail)
    pp = passport(envelope())

    with pytest.raises(RuntimeError):
        call(pay, pp, {**ARGS, "invoice": "INV-crash"}, "k1")
    assert cache.lookup(scope_a(), "k1")["status"] == "indeterminate"
    refuses(pay, pp, {**ARGS, "invoice": "INV-crash"}, "k1", "awaiting reconciliation")
    assert runs == ["INV-crash"]                                        # never run again on its own

    with pytest.raises(NoEffect):
        call(pay, pp, {**ARGS, "invoice": "INV-noeffect"}, "k2")
    assert cache.lookup(scope_a(), "k2")["status"] == "absent"          # the key is free again
    with pytest.raises(NoEffect):
        call(pay, pp, {**ARGS, "invoice": "INV-noeffect"}, "k2")
    assert runs == ["INV-crash", "INV-noeffect", "INV-noeffect"]


def test_an_expired_passport_gets_no_replay_until_reissued():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    old = passport(envelope())
    first = call(pay, old, ARGS, "k1", now=NOW)

    refuses(pay, old, ARGS, "k1", "LAP_ERR_EXPIRED", now=NOW + 10_000)  # nothing to an unauthenticated caller
    reissued = passport(envelope(), iat=NOW + 10_000)
    again = call(pay, reissued, ARGS, "k1", now=NOW + 10_000)
    assert again.pop("_lap_replayed") is True and again == first and runs == ["INV-1"]


def test_the_replayed_receipt_verifies_under_the_new_passport():
    pay, _ = tool(IdempotencyCache())
    call(pay, passport(envelope(cap=1000)), ARGS, "k1")
    again = call(pay, passport(envelope(cap=100)), ARGS, "k1")
    receipt = again.pop("_lap_receipt")
    again.pop("_lap_replayed")
    assert verify_receipt(receipt["receipt_base"], receipt["receipt_signature_b64url"], receipt["server_did"],
                          request_body=jcs(ARGS), response_body=jcs(again))


def test_a_refusal_before_the_claim_reserves_nothing():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pp = passport(envelope(cap=1000))

    refuses(pay, pp, {**ARGS, "amount": 5000}, "k1", "LAP_ERR_CAP")
    assert cache.lookup(scope_a(), "k1")["status"] == "absent"          # no claim consumed on failure
    call(pay, pp, ARGS, "k1")                                           # the key is still usable
    assert runs == ["INV-1"]


def test_the_binding_marks_a_replay_in_the_result_meta():
    types = pytest.importorskip("mcp.types")
    from living_agents.mcp_extension import META_KEY, _call_tool_result

    receipt = {"receipt_base": "sha256:a:sha256:b", "receipt_signature_b64url": "c", "server_did": SERVER_DID}
    fresh = _call_tool_result(types, {"status": "paid"}, receipt)
    replay = _call_tool_result(types, {"status": "paid"}, receipt, replayed=True)
    meta = lambda r: (r.meta or {}) if hasattr(r, "meta") else r.model_dump(by_alias=True)["_meta"]
    assert meta(fresh)[META_KEY] == receipt
    assert meta(replay)[META_KEY] == {**receipt, "replayed": True}       # an optional, unsigned member
