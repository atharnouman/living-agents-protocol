"""
audit-record-contract/1 conformance (clean-room port of the 30 vectors of notboatanchor/audit-record-contract
1.0.0, commit ddead4dca2, written from reading them; none of that code is run here), plus the LAP interop chain.
"""
import copy
import importlib.util
from pathlib import Path

import pytest

from living_agents.audit_record import (
    AuditChain, AuditRecordError, canonical_preimage, compute_event_hash, seal, validate_extensions,
    validate_manifest, validate_skeleton, verify_chain_segment, verify_lap_receipt_in_record, verify_record_hash,
)

KAT_HASH_CG = "d494769c1ae442ea88dd190068747abf63c0568a3b856f85791b1a50a99d48b4"
KAT_HASH_2X = "f733fed9cc757165f810b778e4baba1f51a45504988e937707aaab4361b2f064"
SID = "55555555-5555-5555-5555-555555555555"
PRINCIPAL = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
NINES = "99999999-9999-9999-9999-999999999999"
CG1 = {"session_id": SID, "invoked_by_principal_id": None, "purpose_declared": "reconcile June invoices", "flagged": False}
RS_BOTH = {"drift_status": "confirmed", "policy_id": "example.org/runtime-drift@3", "quarantine_decision": "quarantine",
           "severity": "high", "evidence_hash": "sha256:b2c547e2c8f17eafc72ef5c2d4d7b6b4d0f7437ab52bae573a9af14ff5e2d9be"}


def make(event_id, second, outcome, previous, extensions, event_type="tool_call"):
    return seal({"event_id": event_id, "occurred_at": f"2026-06-06T12:00:0{second}.000Z", "principal_id": PRINCIPAL,
                 "event_type": event_type, "tool_name": "export", "outcome": outcome, "previous_hash": previous,
                 "extensions": extensions})


rec1 = make(NINES, 0, "deferred", None, {"caller-governance": dict(CG1)})
rec2 = make("22222222-2222-2222-2222-222222222222", 1, "allowed", rec1["event_hash"],
            {"caller-governance": dict(CG1, purpose_declared="bulk export", flagged=True)})
recBoth = make(NINES, 0, "deferred", None, {"caller-governance": dict(CG1), "runtime-security": dict(RS_BOTH)})
recRS = make("33333333-3333-3333-3333-333333333333", 2, "allowed", rec1["event_hash"],
             {"runtime-security": {"drift_status": "observed", "severity": "medium", "quarantine_decision": "release",
                                   "policy_id": "example.org/runtime-drift@3"}}, event_type="policy_evaluation")
GOOD_CHAIN, MIXED_CHAIN = [rec1, rec2], [rec1, recRS]
MANIFEST_GOOD = {"storage_mechanism": "revoked-dml-rls", "chain_algorithm": "sha-256",
                 "canonical_form_version": "audit-record-contract/1",
                 "verification_procedure_ref": "https://github.com/notboatanchor/audit-record-contract/tree/main/vectors"}
REQUIRED_LIFECYCLE = ["session_start", "session_close", "session_expired", "session_rejected_closed"]


def c(r):
    return copy.deepcopy(r)


def cg(r):
    return r["extensions"]["caller-governance"]


def matches(a, b):
    return (a == b, [] if a == b else ["mismatch"])


def differs(a, b):
    return (a != b, [] if a != b else ["collision"])


def seal_or_reject(base):
    try:
        return verify_record_hash(seal(base))
    except AuditRecordError as e:
        return False, [f"rejected at emission: {e}"]


def with_cg(field, value, base=rec1):
    r = c(base)
    cg(r)[field] = value
    return r


def without(record, field, inner=False):
    r = c(record)
    del (cg(r) if inner else r)[field]
    return r


def emitted(types, session=True):
    # The 1.0.0 fixtures use outcome "recorded", outside the closed vocabulary; see test_observation_outcome_vocabulary.
    ext = {"purpose_declared": "lifecycle"}
    if session:
        ext["session_id"] = SID
    return [{"event_id": f"e{i}", "event_type": t, "outcome": "allowed", "extensions": {"caller-governance": dict(ext)}}
            for i, t in enumerate(types)]


def completeness(rows):
    failures = [f"missing {t}" for t in REQUIRED_LIFECYCLE if not any(r["event_type"] == t for r in rows)]
    failures += [f"{r['event_type']} unlinked" for r in rows if cg(r).get("session_id") is None]
    return not failures, failures


def astral():
    r = with_cg("purpose_declared", "export \U0001F512 locked")
    pre = canonical_preimage(r)
    if "export \U0001F512 locked" not in pre or "\ud83d" in pre.lower():
        return False, ["astral character not serialized literally"]
    return verify_record_hash(seal(r))


def tampered(chain, i, mutate):
    t = [c(r) for r in chain]
    mutate(t[i])
    return verify_chain_segment(t)


def tampered_record(record, mutate):
    r = c(record)
    mutate(r)
    return verify_record_hash(r)


VECTORS = [
    ("V-REC1-good", True, lambda: validate_skeleton(rec1)),
    ("V-REC1-missing-core", False, lambda: validate_skeleton(without(rec1, "previous_hash"))),
    ("V-REC1-missing-extensions", False, lambda: validate_skeleton(without(rec1, "extensions"))),
    ("V-REC1-extension-required-field", False, lambda: validate_extensions(without(rec1, "purpose_declared", inner=True))),
    ("V-REC1-unregistered-extension", False, lambda: validate_extensions(
        dict(c(rec1), extensions={"caller-governance": dict(CG1), "not-a-real-extension": {"foo": "bar"}}))),
    ("V-REC2-determinism", True, lambda: matches(canonical_preimage(rec1), canonical_preimage(
        dict(reversed(list(dict(c(rec1), extensions={"caller-governance": dict(reversed(list(CG1.items())))}).items())))))),
    ("V-REC2-injective-core", True, lambda: differs(canonical_preimage(rec1), canonical_preimage(dict(c(rec1), outcome="denied")))),
    ("V-REC2-injective-extension", True, lambda: differs(canonical_preimage(rec1), canonical_preimage(with_cg("purpose_declared", "exfiltration")))),
    ("V-REC2-null-vs-empty", True, lambda: differs(canonical_preimage(dict(c(rec1), tool_name=None)),
                                                   canonical_preimage(dict(c(rec1), tool_name="")))),
    ("V-REC2-normalization", True, lambda: matches(canonical_preimage(with_cg("purpose_declared", "café audit")),
                                                   canonical_preimage(with_cg("purpose_declared", "café audit ")))),
    ("V-REC2-control-char", False, lambda: seal_or_reject(with_cg("purpose_declared", "line1\nline2"))),
    ("V-REC2-c1-control", False, lambda: seal_or_reject(with_cg("purpose_declared", "line1\u0085line2"))),
    ("V-REC2-unpaired-surrogate", False, lambda: seal_or_reject(with_cg("purpose_declared", "lone \ud83d surrogate"))),
    ("V-REC2-astral-literal", True, astral),
    ("V-REC3-kat", True, lambda: matches((compute_event_hash(rec1), compute_event_hash(recBoth)), (KAT_HASH_CG, KAT_HASH_2X))),
    ("V-REC3-kat-core-altered", False, lambda: matches(compute_event_hash(dict(c(rec1), outcome="allowed")), KAT_HASH_CG)),
    ("V-REC3-kat-extension-altered", False, lambda: matches(compute_event_hash(with_cg("purpose_declared", "something else")), KAT_HASH_CG)),
    ("V-REC4-good-chain", True, lambda: verify_chain_segment(GOOD_CHAIN)),
    ("V-REC4-tamper-core", False, lambda: tampered(GOOD_CHAIN, 0, lambda r: r.update(outcome="denied"))),
    ("V-REC4-tamper-purpose", False, lambda: tampered(GOOD_CHAIN, 0, lambda r: cg(r).update(purpose_declared="authorized maintenance"))),
    ("V-REC4-delete-record", False, lambda: verify_chain_segment([c(rec2)])),
    ("V-REC5-emission", True, lambda: completeness(emitted(REQUIRED_LIFECYCLE))),
    ("V-REC5-emission-incomplete", False, lambda: completeness(emitted([t for t in REQUIRED_LIFECYCLE if t != "session_close"]))),
    ("V-REC5-emission-unlinked", False, lambda: completeness(emitted(["session_start"], session=False))),
    ("V-REC6-mixed-extension-chain", True, lambda: verify_chain_segment(MIXED_CHAIN)),
    ("V-REC6-extension-fields-chained", False,
     lambda: tampered(MIXED_CHAIN, 1, lambda r: r["extensions"]["runtime-security"].update(severity="low"))),
    ("V-REC6-two-extension-record", True, lambda: verify_record_hash(recBoth)),
    ("V-REC6-two-extension-tamper", False,
     lambda: tampered_record(recBoth, lambda r: r["extensions"]["runtime-security"].update(severity="low"))),
    ("V-REC7-manifest-good", True, lambda: validate_manifest(MANIFEST_GOOD)),
    ("V-REC7-manifest-bare", False, lambda: validate_manifest({})),
]


def test_the_port_has_all_thirty_vectors():
    assert len(VECTORS) == 30 and len({v[0] for v in VECTORS}) == 30


@pytest.mark.parametrize("vector_id,conformant,evaluate", VECTORS, ids=[v[0] for v in VECTORS])
def test_audit_record_contract_vector(vector_id, conformant, evaluate):
    ok, failures = evaluate()
    assert ok is conformant, f"{vector_id}: expected {'conformant' if conformant else 'nonconformant'}, got {failures}"


# ---------------------------------------------------------------- spec-strict readings (reported upstream as observations)

def test_observation_outcome_vocabulary_is_closed():
    # Section 2.1.1 closes the vocabulary; the 1.0.0 C-REC-5 fixtures use "recorded", which this check rejects.
    ok, failures = validate_skeleton(dict(c(rec1), outcome="recorded"))
    assert not ok and any("closed vocabulary" in f for f in failures)


@pytest.mark.parametrize("bad", [4200, 1.5, ["a"]])
def test_spec_strict_protected_values_are_string_bool_or_null(bad):
    # Section 2.3 and C-REC-2: no bare numbers (and no arrays). The 1.0.0 reference canonicalizer serializes numbers.
    with pytest.raises(AuditRecordError):
        compute_event_hash(with_cg("purpose_declared", bad))


def test_occurred_at_must_be_millisecond_utc():
    assert not validate_skeleton(dict(c(rec1), occurred_at="2026-06-06T12:00:00Z"))[0]


# ---------------------------------------------------------------- the LAP interop chain (examples/audit-record-contract)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "examples" / "audit-record-contract" / "lap-chain.jsonl"


def load_builder():
    spec = importlib.util.spec_from_file_location("lap_chain", ROOT / "examples" / "audit-record-contract" / "lap_chain.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def chain():
    return AuditChain.load_jsonl(str(FIXTURE))


def test_committed_lap_chain_verifies_and_rebuilds_byte_identical(chain):
    assert verify_chain_segment(chain) == (True, [])
    rebuilt = load_builder().build_chain().records
    assert [r["event_hash"] for r in rebuilt] == [r["event_hash"] for r in chain]


def test_lap_chain_outcomes_bind_to_decision_codes(chain):
    da = [r["extensions"]["delegated-authority"] for r in chain]
    assert [r["outcome"] for r in chain] == ["allowed", "allowed"] + ["denied"] * 5
    assert [d["decision_code"] for d in da] == ["ok", "ok", "LAP_ERR_CAP", "LAP_ERR_DIGEST", "LAP_ERR_CAP",
                                                 "LAP_ERR_IDEMPOTENCY", "LAP_ERR_AUTH_MISSING"]
    assert (da[0]["replay"], da[1]["replay"]) == ("first", "replayed")
    assert da[0]["receipt_signature"] == da[1]["receipt_signature"]  # the retry returned the stored receipt


def test_lap_chain_attribution(chain):
    first, last = chain[0], chain[-1]
    da = first["extensions"]["delegated-authority"]
    assert first["principal_id"] == da["subject_id"] != da["issuer_id"]          # agent acts, principal granted
    assert (last["principal_id"], last["extensions"]["delegated-authority"]["authority_hash"]) == ("anonymous", None)
    assert chain[3]["extensions"]["delegated-authority"]["authority_verified"] == "false"  # tampered call


def test_lap_receipt_reverifies_from_the_record_alone(chain):
    assert verify_lap_receipt_in_record(chain[0])
    forged = c(chain[0])
    forged["extensions"]["delegated-authority"]["response_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError):
        verify_lap_receipt_in_record(forged)


def test_lap_chain_detects_edits_and_deletions(chain):
    assert not tampered(chain, 0, lambda r: r["extensions"]["delegated-authority"].update(amount="42"))[0]
    assert not verify_chain_segment(chain[:2] + chain[3:])[0]


def test_delegated_authority_is_proposed_not_registered(chain):
    ok, failures = validate_extensions(chain[0])
    assert not ok and failures == ["unregistered extension type: delegated-authority"]
    assert validate_extensions(chain[0], allow_proposed=True) == (True, [])
