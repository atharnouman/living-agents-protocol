"""
audit-record-contract/1, written independently from the specification text, plus a mapping of
LAP Micro-Core decisions and receipts into those records.

Source specification: "Tamper-Evident Audit Record Contract" 1.0.0 by Notboatanchor Labs LLC,
https://github.com/notboatanchor/audit-record-contract (Apache-2.0), commit ddead4dca2. No code
from that repository is included or executed here; section numbers below refer to its spec.

Spec-strict where the reference implementation is lenient, and said so in
interop/audit-record-contract/README.md:
- protected values must be strings, booleans or null (section 2.3): bare numbers and arrays are
  rejected rather than serialized;
- validate_skeleton enforces the closed outcome vocabulary of section 2.1.1 (clause C-REC-1).

The LAP side uses a PROPOSED extension type id, `delegated-authority`, which is not in the
contract's curated registry. validate_extensions therefore reports it as unregistered unless
called with allow_proposed=True.
"""

import hashlib
import io
import json
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple

CANONICAL_FORM_VERSION = "audit-record-contract/1"
CORE_PROTECTED = ("event_id", "occurred_at", "principal_id", "event_type", "tool_name", "outcome", "previous_hash")
CORE_REQUIRED = CORE_PROTECTED + ("event_hash", "extensions")
OUTCOMES = ("allowed", "denied", "deferred", "error")
MAX_FIELD_LEN = 8192          # UTF-16 code units, measured on the normalized value (section 2.3)
MAX_DEPTH = 64
MANIFEST_REQUIRED = ("storage_mechanism", "chain_algorithm", "canonical_form_version", "verification_procedure_ref")

_CC = re.compile("[\u0000-\u001f\u007f-\u009f]")
_OCCURRED_AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

REGISTERED_PROFILES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "caller-governance": {
        "required": ("purpose_declared",),
        "optional": ("session_id", "invoked_by_principal_id", "flagged", "sources_touched",
                     "sensitivity_encountered", "output_disposition", "human_actor_id"),
    },
    "runtime-security": {
        "required": ("drift_status", "severity", "quarantine_decision", "policy_id"),
        "optional": ("evidence_hash",),
    },
    "admission-control": {"required": (), "optional": ()},
}

# Proposed by LAP, NOT registered. All values are strings (the runtime-security convention),
# OPTIONAL fields follow the caller-governance presence rule (absent = not recorded,
# null = recorded with no value).
DELEGATED_AUTHORITY = "delegated-authority"
PROPOSED_PROFILES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    DELEGATED_AUTHORITY: {
        "required": ("authority_format", "authority_verified", "decision_code", "action", "resource"),
        "optional": ("authority_hash", "issuer_id", "subject_id", "audience_id", "proof_class", "scope_hash",
                     "amount", "unit", "cap_max_per_tx", "request_hash", "response_hash", "receipt_signature",
                     "receipt_signer_id", "signature_base_hash", "request_signature", "idempotency_key", "replay"),
    },
}


class AuditRecordError(ValueError):
    """A value that has no canonical form under audit-record-contract/1."""


def normalize_string(s: str) -> str:
    """Section 2.3: reject Cc controls and unpaired surrogates, NFC, trim U+0020 only, length cap."""
    if _CC.search(s):
        raise AuditRecordError("control character in protected string field")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in s):
        raise AuditRecordError("unpaired surrogate in protected string field")
    n = unicodedata.normalize("NFC", s).strip(" ")
    if len(n.encode("utf-16-le")) // 2 > MAX_FIELD_LEN:
        raise AuditRecordError("protected string field exceeds length cap")
    return n


def _string(s: str) -> str:
    # Minimal escaping: only '"' and '\' (controls were rejected above); everything else literal.
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def canonicalize(value: Any, depth: int = 0) -> str:
    """Sorted-key canonical JSON over string, boolean and null values (section 2.3)."""
    if depth > MAX_DEPTH:
        raise AuditRecordError("protected value nesting exceeds depth cap")
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _string(normalize_string(value))
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):                      # code-point order == UTF-8 byte order
            if not isinstance(key, str):
                raise AuditRecordError("object keys must be strings")
            parts.append(_string(key) + ":" + canonicalize(value[key], depth + 1))
        return "{" + ",".join(parts) + "}"
    if isinstance(value, (int, float)):
        raise AuditRecordError("bare number in a protected value (section 2.3: encode numbers as strings)")
    if isinstance(value, (list, tuple)):
        raise AuditRecordError("array in a protected value (section 2.3: string, boolean or null only)")
    raise AuditRecordError(f"uncanonicalizable value of type {type(value).__name__}")


def canonical_body(record: Dict[str, Any]) -> Dict[str, Any]:
    body = {f: record[f] for f in CORE_PROTECTED if f in record}
    if "extensions" in record:
        body["extensions"] = record["extensions"]
    return body


def canonical_preimage(record: Dict[str, Any]) -> str:
    return canonicalize(canonical_body(record))


def compute_event_hash(record: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_preimage(record).encode("utf-8")).hexdigest()


def seal(record: Dict[str, Any]) -> Dict[str, Any]:
    sealed = dict(record)
    sealed["event_hash"] = compute_event_hash(sealed)
    return sealed


# --------------------------------------------------------------------------- verification

def verify_record_hash(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    try:
        expected = compute_event_hash(record)
    except AuditRecordError as e:
        return False, [f"canonicalization failed on {record.get('event_id')}: {e}"]
    if expected != record.get("event_hash"):
        return False, [f"event_hash mismatch on {record.get('event_id')}"]
    return True, []


def verify_chain_segment(records: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Section 2.6: every record's hash recomputes, and previous_hash threads the segment."""
    failures: List[str] = []
    for i, rec in enumerate(records):
        failures += verify_record_hash(rec)[1]
        if i == 0:
            if rec.get("previous_hash") is not None:
                failures.append(f"segment head {rec.get('event_id')} must have null previous_hash")
        elif rec.get("previous_hash") != records[i - 1].get("event_hash"):
            failures.append(f"broken link at {rec.get('event_id')}")
    return not failures, failures


def validate_skeleton(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Clause C-REC-1, core part, including the closed outcome vocabulary of section 2.1.1."""
    failures = [f"missing required field: {f}" for f in CORE_REQUIRED if f not in record]
    for f in ("event_id", "occurred_at", "principal_id", "event_type", "outcome", "event_hash"):
        if f in record and not isinstance(record[f], str):
            failures.append(f"{f} must be a string")
    if "outcome" in record and record["outcome"] not in OUTCOMES:
        failures.append(f"outcome {record['outcome']!r} is not in the closed vocabulary {OUTCOMES}")
    if isinstance(record.get("occurred_at"), str) and not _OCCURRED_AT.match(record["occurred_at"]):
        failures.append("occurred_at must be RFC 3339 UTC with millisecond precision and Z")
    if "tool_name" in record and record["tool_name"] is not None and not isinstance(record["tool_name"], str):
        failures.append("tool_name must be a string or null")
    prev = record.get("previous_hash")
    if "previous_hash" in record and prev is not None and not (isinstance(prev, str) and _HEX64.match(prev)):
        failures.append("previous_hash must be lowercase hex or null")
    ext = record.get("extensions")
    if "extensions" in record and not isinstance(ext, dict):
        failures.append("extensions must be a keyed object")
    return not failures, failures


def validate_extensions(record: Dict[str, Any], allow_proposed: bool = False) -> Tuple[bool, List[str]]:
    """Clause C-REC-1, extension part: at least one registered type id, required fields non-null."""
    registry = dict(REGISTERED_PROFILES)
    if allow_proposed:
        registry.update(PROPOSED_PROFILES)
    entries = list((record.get("extensions") or {}).items())
    failures = [] if entries else ["extensions must declare at least one registered type"]
    for type_id, data in entries:
        spec = registry.get(type_id)
        if spec is None:
            failures.append(f"unregistered extension type: {type_id}")
            continue
        fields = data or {}
        failures += [f"extension {type_id} requires {f}" for f in spec["required"] if fields.get(f) is None]
    return not failures, failures


def validate_manifest(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Clause C-REC-7: the attestation manifest is structured, not a bare claim."""
    failures = [f"attestation manifest missing or empty: {f}" for f in MANIFEST_REQUIRED
                if not isinstance(manifest.get(f), str) or not manifest[f].strip()]
    return not failures, failures


class AuditChain:
    """An append-only record chain. With `path`, each sealed record is appended to a JSON Lines file.
    The file is append-only by convention here; declare the real mechanism in the manifest."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.records: List[Dict[str, Any]] = []
        self.path = path

    def append(self, record: Dict[str, Any]) -> Dict[str, Any]:
        rec = dict(record)
        rec["previous_hash"] = self.records[-1]["event_hash"] if self.records else None
        sealed = seal(rec)
        self.records.append(sealed)
        if self.path:
            with io.open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(sealed, ensure_ascii=False, sort_keys=True) + "\n")
        return sealed

    def verify(self) -> Tuple[bool, List[str]]:
        return verify_chain_segment(self.records)

    @staticmethod
    def load_jsonl(path: str) -> List[Dict[str, Any]]:
        with io.open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]


def manifest(verification_procedure_ref: str, storage_mechanism: str = "append-only-file") -> Dict[str, str]:
    return {"storage_mechanism": storage_mechanism, "chain_algorithm": "sha-256",
            "canonical_form_version": CANONICAL_FORM_VERSION,
            "verification_procedure_ref": verification_procedure_ref}


# --------------------------------------------------------------------------- LAP mapping

def utc_millis(epoch_seconds: float) -> str:
    """The section 2.3 timestamp form, e.g. 2026-10-16T12:00:00.000Z, from the recorder's clock."""
    import datetime
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def lap_tool_call_record(
    *,
    event_id: str,
    occurred_at: str,
    tool_name: Optional[str],
    decision_code: str,
    action: str,
    resource: str,
    passport_jwt: Optional[str] = None,
    verified_payload: Optional[Dict[str, Any]] = None,
    amount: Any = None,
    unit: Optional[str] = None,
    request_body: Optional[str] = None,
    receipt: Optional[Dict[str, str]] = None,
    signature_base: Optional[str] = None,
    request_signature: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    replay: Optional[bool] = None,
    extra_extensions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """One unsealed record for one LAP-governed tools/call (allowed or refused).

    decision_code is "ok" for an executed (or idempotently replayed) call, a LAP_ERR_* code for a
    refusal, or "error" when verification itself failed. The core outcome is bound to it:
    ok -> allowed, LAP_ERR_* -> denied, error -> error. principal_id is the passport's subject
    (LAP's agent; the contract's "governed identity"); LAP's principal, the passport's issuer,
    goes in issuer_id. A refused call whose passport did not verify keeps the CLAIMED identities
    with authority_verified "false"; a call with no passport is attributed to "anonymous".
    """
    from .crypto_util import jcs, sha256_hex
    from .jws import decode_jws

    da: Dict[str, Any] = {"authority_format": "lap-microcore/0", "decision_code": decision_code,
                          "action": action, "resource": resource,
                          "authority_verified": "true" if verified_payload is not None else "false"}
    claims: Optional[Dict[str, Any]] = verified_payload
    if passport_jwt:
        da["authority_hash"] = "sha256:" + sha256_hex(passport_jwt)
        if claims is None:
            try:
                claims = decode_jws(passport_jwt)["payload"]
            except ValueError:
                claims = None
    else:
        da["authority_hash"] = None
    if claims:
        lap = claims.get("lap") or {}
        envelope = lap.get("envelope")
        for field, claim in (("issuer_id", "iss"), ("subject_id", "sub"), ("audience_id", "aud")):
            if isinstance(claims.get(claim), str):
                da[field] = claims[claim]
        if isinstance(lap.get("proof_class"), str):
            da["proof_class"] = lap["proof_class"]
        if isinstance(envelope, dict):
            da["scope_hash"] = "sha256:" + sha256_hex(jcs(envelope))
            cap = envelope.get("cap")
            if isinstance(cap, dict) and cap.get("max_per_tx") is not None:
                da["cap_max_per_tx"] = str(cap["max_per_tx"])
    if amount is not None:
        da["amount"] = str(amount)
    if unit is not None:
        da["unit"] = unit
    if receipt:
        req, resp = receipt["receipt_base"].split(":")[1], receipt["receipt_base"].split(":")[3]
        da.update({"request_hash": "sha256:" + req, "response_hash": "sha256:" + resp,
                   "receipt_signature": receipt["receipt_signature_b64url"],
                   "receipt_signer_id": receipt["server_did"]})
    elif request_body is not None:
        da["request_hash"] = "sha256:" + sha256_hex(request_body)
    if signature_base is not None:
        da["signature_base_hash"] = "sha256:" + sha256_hex(signature_base)
    if request_signature is not None:
        da["request_signature"] = request_signature
    if idempotency_key is not None:
        da["idempotency_key"] = idempotency_key
    if replay is not None:
        da["replay"] = "replayed" if replay else "first"

    if decision_code == "ok":
        outcome = "allowed"
    elif decision_code == "error":
        outcome = "error"
    else:
        outcome = "denied"
    extensions: Dict[str, Dict[str, Any]] = {DELEGATED_AUTHORITY: da}
    extensions.update(extra_extensions or {})
    return {"event_id": event_id, "occurred_at": occurred_at, "principal_id": da.get("subject_id", "anonymous"),
            "event_type": "tool_call", "tool_name": tool_name, "outcome": outcome,
            "previous_hash": None, "extensions": extensions}


def verify_lap_receipt_in_record(record: Dict[str, Any], request_body: Optional[str] = None,
                                 response_body: Optional[str] = None) -> bool:
    """Re-verify the LAP receipt carried in a record, from the record alone (plus optional bodies)."""
    from .microcore import verify_receipt
    da = record["extensions"][DELEGATED_AUTHORITY]
    return verify_receipt(da["request_hash"] + ":" + da["response_hash"], da["receipt_signature"],
                          da["receipt_signer_id"], request_body=request_body, response_body=response_body)
