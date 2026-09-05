# LIP-1: Agent Passport & Genesis Record

*Status: DRAFT v0.1 — 2026-08-29. Layer: L2 (Identity). Requires: none. Required by: LIP-2 (MEET), LIP-4 (Micro-Core). Test vectors: `test-vectors/vectors.json` (deterministic; regenerate with `generate_vectors.py`). The key words MUST, MUST NOT, SHOULD, MAY are per RFC 2119. Each section separates **Normative** rules from *Informative* rationale.*

---

## 1. Purpose (Informative)

The passport answers, verifiably: *who is this agent, who answers for it, what policy does it claim to run, and where in its life is it?* It is the root artifact every other LAP mechanism references. Design constraints inherited from three review rounds: no behavioral over-claims (a policy hash is a commitment, not an attestation), no public presence schedules (privacy), labeled proof strength (no laundering weak attestations behind a uniform field), and profile-don't-invent (this is a W3C VC 2.0-compatible document with a JOSE serialization, not a new credential format).

## 2. Data model (Normative)

A passport is a JSON claims object. Two serializations are defined; conformant verifiers MUST accept the JWS form; the VC 2.0 envelope form is OPTIONAL for interop with credential wallets.

```json
{
  "v": "lip1-v0",
  "id": "did:key:z6MksMrZDkhaiLzXQo4kRmKLcU8qbVerEv4j1Jqon9CPPHEC",
  "principal": {
    "id": "did:key:z6MkekRLWHGBStebPB5RyBd3nNbfgKi2yjKLkjw4aLrms1TW",
    "proof_class": "self-asserted",
    "contact": "mailto:escalation@example.com"
  },
  "lineage": { "spawner": null, "generation": 1 },
  "constitution": { "sha256": "…64 hex…" },
  "autonomy_level": 3,
  "era": { "track": "api-hosted", "digest": "…64 hex…" },
  "presence_contact": "https://agent.example.com/lap/pulse",
  "revocation": "https://agent.example.com/lap/revocation",
  "iat": 1787000000,
  "exp": 1818536000
}
```

Field rules:

| Field | Req | Rule |
|---|---|---|
| `v` | MUST | `"lip1-v0"`. Unknown versions MUST be rejected (`LAP_ERR_VERSION`). |
| `id` | MUST | The agent's DID. `did:key` and `did:web` MUST be supported by verifiers; other methods MAY. |
| `principal.id` | MUST | DID of the legal person answerable for the agent. **No orphan agents**: a passport whose principal cannot be resolved to a responsible party MUST NOT reach VERIFIED. `principal.id == id` (self-ownership) MUST be rejected. |
| `principal.proof_class` | MUST | One of `self-asserted \| domain-validated \| org-validated \| gov-validated` (§4). |
| `principal.proof` | MUST for classes above self-asserted | The verifiable credential or attestation backing the class, including a status-list reference (§4). |
| `principal.contact` | MUST | Escalation URI (the Human Escalation Guarantee contact point). |
| `titleHolder` | MAY | DID; present only when title ≠ principal. Absent ⇒ principal holds title. |
| `custodian` | MAY | DID of the substrate operator when ≠ principal. |
| `lineage.spawner` | MUST (nullable) | DID of the creating agent, or `null` for human-created. `generation` = spawner.generation + 1, humans create generation 1. |
| `constitution.sha256` | MUST | SHA-256 (lowercase hex) of the governing charter text. This is a **public policy commitment, not a behavioral attestation** — verifiers MUST NOT present it as safety evidence. `constitution.uri` MAY point to the text. |
| `autonomy_level` | MUST | Integer 0–5 per the AL scale. Value 5 MUST NOT be certified. |
| `era.track` | MUST | `self-hosted` or `api-hosted` (two-track digest per spec §17.1). |
| `era.digest` | MUST | Track-appropriate runtime-environment digest. Decoding parameters MUST NOT enter the digest. |
| `substrate.attestation_class` | SHOULD | `none \| vendor-asserted \| tee-quote`; TEE quotes SHOULD accompany class `tee-quote`. |
| `presence_contact` | MUST | URI for bilateral presence negotiation. **Public passports MUST NOT contain schedules or quiet hours** (privacy: schedules leak the principal's sleep/travel patterns). |
| `revocation` | MUST | Revocation status endpoint. Verifiers MAY accept SCITT-sealed status snapshots within a freshness bound in place of live queries. |
| `iat`, `exp` | MUST | Seconds since epoch. Verifiers MUST apply ±60s default clock-skew tolerance. |

## 3. Signing (Normative)

- The passport is signed by the **principal's** key: JWS compact serialization, `alg: EdDSA` (Ed25519 MUST-implement; others MAY), header `typ: "lap-passport+jwt"`, `kid` = principal DID + fragment. All base64url segments MUST be canonical (RFC 4648 §5 unpadded; §3.5 zero trailing bits) and verifiers MUST reject non-canonical text (`LAP_ERR_ENCODING`): a passport has exactly one textual form, so hashes of that text (`lap-passport-hash`, denylists, log entries) are stable identifiers.
- The JWS payload MUST be the JCS (RFC 8785) canonical form of the claims. Before canonicalization, all DIDs and URIs MUST be normalized: Unicode NFC; schemes and hostnames ASCII-lowercased; percent-encoding normalized (RFC 3986 §6.2.2).
- Key rotation MUST emit a `KeyRotationEvent` dual-signed by old and new keys, logged before the new key's first use.

## 4. Proof classes (Normative)

| Class | Meaning | Backing |
|---|---|---|
| `self-asserted` | The principal claims the binding; nobody attests it. | none |
| `domain-validated` | Principal demonstrated control of a DNS domain bound in its DID. | e.g. did:web resolution + challenge |
| `org-validated` | An issuer attests the principal is a named organization. | VC from a recognized issuer; EU profile: eIDAS 2.0 QEAA |
| `gov-validated` | Government-grade identity attestation. | e.g. EUDI wallet attestation (OIDC4VCI issuance) |

Rules: verifiers MUST treat the **class**, not the field's presence, as the trust signal. Class-backing credentials MUST carry a revocation/status reference (W3C Bitstring Status List) checked at PROVE — a SCITT-sealed snapshot within the deployment's freshness bound satisfies the check. A passport MUST NOT claim a class its `proof` does not establish; over-claiming discovered post-hoc forfeits certification standing.

## 5. Genesis Record (Normative)

Created once, at the agent's creation:

```json
{ "v": "lip1-genesis-v0", "agent": "did:key:z6MksMrZ…PPHEC",
  "passport_sha256": "…", "created_at": 1787000000 }
```

- The Genesis Record MUST be submitted to ≥2 independent transparency logs (SCITT profile) or self-anchored to a recognized open chain. Age claims are valid only from the **witnessed** timestamp — `created_at` alone proves nothing.
- Registration proof rules and finality (including `UNVERIFIED_PENDING_FINALITY` for unfinalized self-anchors) are per spec §16.1/§19.
- **Passport amendment chain (v0.2, closes the §26 HANDOFF gap):** the Genesis Record binds the *original* passport hash; any later passport mutation (HANDOFF of principal, key rotation, era boundary) MUST be logged as a **PassportHandoffEvent**: `{ "v": "lip1-handoff-v0", "agent": …, "prev_passport_sha256": …, "new_passport_sha256": …, "outgoing_sig": <old principal>, "incoming_sig": <new principal>, "effective_at": … }`. Verifiers validate a current passport by tracing the event chain from Genesis to the presented hash; a passport whose hash is reachable by no chain from Genesis MUST fail with `LAP_ERR_REGISTRATION`.
- Principal references in any *public* log entry MUST be salted blinded commitments (≥128-bit salt held off-log), never plain hashes of personal identifiers.

## 6. Verification procedure (Normative)

A verifier resolving a passport MUST, in order: (1) parse and check `v`; (2) normalize strings (§3); (3) resolve the principal DID and verify the JWS signature (resolution MUST use SSRF-filtered, cached resolution — private and metadata IP ranges refused); (4) check `iat`/`exp` with skew tolerance; (5) reject if `principal.id == id`; (6) if `proof_class` is `self-asserted`, skip credential verification (there is nothing to verify — the class itself is the signal); otherwise verify the backing credential in `principal.proof` and its status reference; (7) check the revocation endpoint or an in-date sealed snapshot; (8) check registration proof (log inclusions or finalized self-anchor); (9) emit exactly one trust state per spec §16.1. Failures map to `LAP_ERR_{VERSION|SIG|EXPIRED|SELF_OWNED|PROOF_CLASS|REVOKED|REGISTRATION}`.

## 7. Security considerations (Informative)

Key custody is the root risk (spec §22.3): a stolen principal key signs valid-looking passports; time-locked root mutations and multi-sig custody are the recommended mitigations. Proof-class laundering via re-issuance is bounded by status-list checks plus era boundaries. DID resolution is an SSRF/DoS surface — hence the mandatory filtering in §6(3). TEE attestation, where present, bounds but does not eliminate substrate compromise (side-channel extraction; ratchet enclave keys per pulse epoch).

## 8. Privacy considerations (Informative)

The passport deliberately contains no schedule, no location, no human name (the principal is a DID; its legal identity lives in the proof credential, disclosed per its own policy). Public log entries carry only blinded commitments; GDPR erasure = salt destruction.

## 9. Test vectors (Normative reference)

`test-vectors/vectors.json` is generated deterministically (fixed seed labels) and contains: both keypairs' public keys and DIDs; the constitution text and hash; the passport claims, JCS canonical form, and principal-signed JWS; the Genesis Record and its hash. Conformant implementations MUST reproduce the canonical forms byte-for-byte and verify the signatures. (Vectors use `proof_class: self-asserted` — higher classes require issuer credentials out of scope for the seed set.)

## 10. Open items

VC 2.0 envelope example; did:web vector; a `gov-validated` example against an eIDAS test issuer; multi-sig principal custody profile; the KeyRotationEvent schema (shared with LIP-2); CBOR serialization decision.
