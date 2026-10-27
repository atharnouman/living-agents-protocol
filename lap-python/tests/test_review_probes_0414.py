"""Probes from the third independent review (Opus 5.5, 2026-10-28) of the 0.4.14 claim design,
each reproduced before the fix: a failure after the effect stranded the claim in flight (P3); a
second content-digest line gave a request another identity (P2); a second signer of the same
principal ran the payment again (P1); a tool's own ValueError read as a refusal (P5); one cache
serving two audiences replayed across them (P7); a twin completing between the lookup and the
envelope check lost to a cap refusal (P9); a row without an identity matched any request (P6);
threads could both reserve one key.
"""
import hashlib
import threading
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from living_agents import (
    EXTENSION_ID,
    IdempotencyCache,
    LapRefusal,
    b64url_encode,
    claim_scope,
    did_key_from_raw_public_key,
    jcs,
    lap_auth_from_meta,
    last_call_meta,
    request_identity,
    sha256_b64url,
    sign_jws,
    sign_tool_call,
    verify_envelope,
)
from living_agents import mcp_middleware

PAY = "mcp://tools.example.com/billing/pay"
SERVER_A = "did:web:tools.example.com"
SERVER_B = "did:web:other.example.com"
NOW = int(time.time())


def key_from(label):
    k = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(label.encode()).digest())
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


PRINCIPAL, PRINCIPAL_DID = key_from("probe principal")
PRINCIPAL_2, PRINCIPAL_2_DID = key_from("probe principal second key")
AGENT, AGENT_DID = key_from("probe agent")
SERVER, SERVER_DID = key_from("probe server")
ENVELOPE = {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
            "cap": {"max_per_tx": 1000, "unit": "USD", "window": "tx"}}
ARGS = {"invoice": "INV-1", "amount": 500, "unit": "USD"}


def passport(aud=SERVER_A, principal=PRINCIPAL, principal_did=PRINCIPAL_DID, env=ENVELOPE):
    return sign_jws({"iss": principal_did, "sub": AGENT_DID, "aud": aud, "iat": NOW, "exp": NOW + 600,
                     "lap": {"v": 0, "proof_class": "self-asserted", "envelope": env}},
                    principal, principal_did + "#key-1", "lap-microcore+jwt")


def tool(cache, aud=SERVER_A, result=None, **options):
    runs = []

    @verify_envelope(action="finance:pay", resource=PAY, amount_param="amount", unit_param="unit",
                     expected_aud=aud, server_private_key=SERVER, server_did=SERVER_DID,
                     idempotency_cache=cache, **options)
    def pay(invoice: str, amount: int, unit: str = "USD"):
        runs.append(invoice)
        return result(invoice) if result else {"status": "paid", "invoice": invoice, "amount": amount}

    return pay, runs


def auth_for(pp, args, key):
    return lap_auth_from_meta({EXTENSION_ID: sign_tool_call(args, PAY, pp, AGENT, AGENT_DID, NOW, key)}, args)


def scope(aud=SERVER_A, principal_did=PRINCIPAL_DID):
    return claim_scope({"iss": principal_did, "sub": AGENT_DID}, aud=aud)


def test_p3_a_failure_after_the_effect_completes_the_claim_so_a_retry_replays_it():
    cache = IdempotencyCache()
    pay, runs = tool(cache, result=lambda inv: {"fee": 1.25})     # canonical JSON refuses a non-integer float
    pp = passport()

    with pytest.raises(ValueError, match="integers only") as e:
        pay(lap_auth=auth_for(pp, ARGS, "k1"), **ARGS)
    assert not isinstance(e.value, LapRefusal)                     # the tool ran; this is not a refusal
    assert cache.lookup(scope(), "k1")["status"] == "completed"    # stored without a receipt, not stranded

    again = pay(lap_auth=auth_for(pp, ARGS, "k1"), **ARGS)
    assert again == {"fee": 1.25, "_lap_replayed": True} and runs == ["INV-1"]
    assert last_call_meta() == {"receipt": None, "replayed": True}


def test_p2_a_second_content_digest_line_is_refused_not_used_as_identity():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pp = passport()
    other = {"invoice": "INV-1", "amount": 900, "unit": "USD"}
    signed = sign_tool_call(ARGS, PAY, pp, AGENT, AGENT_DID, NOW, "k1")
    lines = signed["signature_base"].split("\n")
    forged = lines[:2] + [f'"content-digest": sha-256=:{sha256_b64url(jcs(other))}:'] + lines[2:]
    base = "\n".join(forged)                                       # two digest lines: the other request's first
    auth = {"passport_jwt": pp, "signature_base": base, "request_body": jcs(ARGS), "idempotency_key": "k1",
            "signature_b64url": b64url_encode(AGENT.sign(base.encode("ascii")))}

    with pytest.raises(LapRefusal, match="LAP_ERR_SIG_PARAMS: duplicate covered component"):
        pay(lap_auth=auth, **ARGS)
    assert runs == [] and cache.lookup(scope(), "k1")["status"] == "absent"


def test_p1_a_second_key_of_the_same_principal_is_refused_until_mapped():
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    raised = passport(principal=PRINCIPAL_2, principal_did=PRINCIPAL_2_DID,
                      env={**ENVELOPE, "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}})

    with pytest.raises(LapRefusal, match="LAP_ERR_ISSUER: idempotency key already held under another issuer"):
        pay(lap_auth=auth_for(raised, ARGS, "k1"), **ARGS)
    assert runs == ["INV-1"]                                       # not run again under the new signer

    joined = IdempotencyCache()
    pay, runs = tool(joined, tenant_of=lambda p: "acme" if p["iss"] in (PRINCIPAL_DID, PRINCIPAL_2_DID) else None)
    pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    assert pay(lap_auth=auth_for(raised, ARGS, "k1"), **ARGS)["_lap_replayed"] is True
    assert runs == ["INV-1"]                                       # mapped to one tenant: recognised


def test_p5_a_tool_exception_is_not_a_refusal():
    def boom(_inv):
        raise ValueError("LAP_ERR_CAP: a tool pretending to refuse")

    pay, runs = tool(IdempotencyCache(), result=boom)
    with pytest.raises(ValueError) as e:
        pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    assert not isinstance(e.value, LapRefusal) and runs == ["INV-1"]
    with pytest.raises(LapRefusal, match="LAP_ERR_REPLAY"):         # its claim is indeterminate
        pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    with pytest.raises(LapRefusal, match="LAP_ERR_CAP"):            # a real refusal is typed
        pay(lap_auth=auth_for(passport(), {**ARGS, "amount": 5000}, "k2"), **{**ARGS, "amount": 5000})


def test_p7_one_cache_serving_two_audiences_keeps_their_claims_apart():
    cache = IdempotencyCache()
    pay_a, runs_a = tool(cache, aud=SERVER_A)
    pay_b, runs_b = tool(cache, aud=SERVER_B)

    pay_a(lap_auth=auth_for(passport(SERVER_A), ARGS, "k1"), **ARGS)
    second = pay_b(lap_auth=auth_for(passport(SERVER_B), ARGS, "k1"), **ARGS)
    assert runs_a == ["INV-1"] and runs_b == ["INV-1"] and "_lap_replayed" not in second
    assert cache.lookup(scope(SERVER_B), "k1")["status"] == "completed"
    assert pay_a(lap_auth=auth_for(passport(SERVER_A), ARGS, "k1"), **ARGS)["_lap_replayed"] is True


def test_p9_a_twin_completing_in_the_window_wins_over_a_cap_refusal(monkeypatch):
    cache = IdempotencyCache()
    pay, runs = tool(cache)
    pp = passport()
    big = {**ARGS, "amount": 5000}
    identity = request_identity(sign_tool_call(big, PAY, pp, AGENT, AGENT_DID, NOW, "k1")["signature_base"], jcs(big))
    real = mcp_middleware.check_invocation
    stored = {"status": "paid", "invoice": "INV-1", "amount": 5000, "_lap_receipt": {"receipt_base": "x"}}

    def twin_completes_first(*a, **kw):
        if kw.get("enforce_magnitude", True) and cache.lookup(scope(), "k1")["status"] == "absent":
            cache.claim(scope(), "k1", identity)                   # a twin on another executor
            cache.complete(scope(), "k1", stored)                  # finishes before this check
        return real(*a, **kw)

    monkeypatch.setattr(mcp_middleware, "check_invocation", twin_completes_first)
    out = pay(lap_auth=auth_for(pp, big, "k1"), **big)              # the cap would refuse 5000 > 1000
    assert out["_lap_replayed"] is True and out["amount"] == 5000 and runs == []


def test_p6_a_row_without_an_identity_fails_closed_and_complete_needs_a_reservation():
    cache = IdempotencyCache()
    cache.store(("t", "did:key:a"), "k", {"r": 1})                 # legacy write, no identity
    assert cache.lookup(("t", "did:key:a"), "k") == {"status": "completed", "receipt": {"r": 1}}
    assert cache.lookup(("t", "did:key:a"), "k", ("m", "t", "d")) == {"status": "key_reuse"}
    with pytest.raises(ValueError, match="needs a reservation"):
        cache.complete(("t", "did:key:a"), "never", {"r": 2})
    cache.claim(("t", "did:key:a"), "k2", ("m", "t", "d"))
    cache.complete(("t", "did:key:a"), "k2", {"r": 2})
    with pytest.raises(ValueError, match="already completed"):      # a slow executor cannot overwrite it
        cache.complete(("t", "did:key:a"), "k2", {"r": 3})
    with pytest.raises(ValueError, match="another tenant"):
        cache.complete(("u", "did:key:a"), "k2", {"r": 3})


def test_claim_is_atomic_across_threads():
    cache = IdempotencyCache()
    gate, outcomes = threading.Barrier(16), []

    def worker():
        gate.wait()
        outcomes.append(cache.claim(("t", "did:key:a"), "k", ("m", "t", "d"))["status"])

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert outcomes.count("reserved") == 1 and outcomes.count("in_flight") == 15


def test_p4_a_result_that_is_not_a_dict_still_has_a_receipt_and_a_replay_marker():
    pay, runs = tool(IdempotencyCache(), result=lambda inv: f"paid {inv}")
    first = pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    receipt = last_call_meta()["receipt"]
    assert first == "paid INV-1" and receipt["server_did"] == SERVER_DID and last_call_meta()["replayed"] is False

    again = pay(lap_auth=auth_for(passport(), ARGS, "k1"), **ARGS)
    assert again == first and runs == ["INV-1"]
    assert last_call_meta() == {"receipt": receipt, "replayed": True}
