# LAP receipts as audit-record-contract records: fit report

*2026-10-16. Tested against "Tamper-Evident Audit Record Contract" 1.0.0 (canonical form `audit-record-contract/1`) by Notboatanchor Labs LLC, https://github.com/notboatanchor/audit-record-contract (Apache-2.0), at commit `ddead4dca2`. Written in public as promised in the MCP Security IG meeting thread. Prepared with AI assistance (Claude), reviewed and published by the LAP author.*

## Result in one paragraph

LAP's per-call decision and receipt fit the contract cleanly as one extension, and the contract gives LIP-4's "both parties MUST keep an append-only log of receipts" a ready, vector-tested format. The LAP Python library now carries an independent implementation of the contract, written from the specification text, without running or copying upstream code. It reproduces both published known-answer digests, emits the two-extension preimage byte for byte as the specification prints it, and passes a clean-room port of all 30 conformance vectors. The MCP tutorial's seven calls, recorded with a proposed `delegated-authority` extension, form a chain that verifies, rebuilds byte-identical from fixed seeds, detects edits and deletions, and still lets anyone re-verify the server's LAP receipt from the record alone. The one hard blocker is registration: extension type ids come from the contract's curated registry, and `delegated-authority` is not in it, so these records are conforming in every respect except clause C-REC-1's "registered type id".

## Evidence

| Check | Result | Where |
|---|---|---|
| Single-extension known-answer digest `d494769c…` | reproduced | `lap-python/tests/test_audit_record.py`, vector V-REC3-kat |
| Two-extension known-answer digest `f733fed9…`, preimage byte-identical to the specification's printed string | reproduced | same |
| The 30 conformance vectors, C-REC-1 to C-REC-7, ported from reading | 30 of 30 pass | same, `test_audit_record_contract_vector` |
| LAP chain: 7 records (2 allowed, one an idempotent replay; 5 denied with LAP_ERR_* codes) | verifies; rebuilds byte-identical | `lap-chain.jsonl`, `lap_chain.py` |
| LAP receipt re-verified from a record alone; a forged response hash rejected | yes | `test_lap_receipt_reverifies_from_the_record_alone` |
| Edit of `amount` after commit; deletion of a record | both detected | `test_lap_chain_detects_edits_and_deletions` |

Reproduce:

```bash
python examples/audit-record-contract/lap_chain.py
cd lap-python && python -m pytest tests/test_audit_record.py -q
```

## What fits

- **Canonical form.** On valid input the contract's sorted-key JSON coincides with the RFC 8785 canonical JSON LAP already uses: values are strings, booleans or null, keys are ASCII, and minimal escaping matches. What LAP had to add were the contract's string rules (NFC, trimming of U+0020 only, rejection of control characters and unpaired surrogates, the length cap).
- **Roles divide cleanly.** The chain proves the recorder's log was not edited after commit. The LAP receipt, a server signature over the request and response hashes, proves who decided. The `delegated-authority` data proves under whose authority: issuer, subject, audience, a hash of the presented passport and a hash of its envelope.
- **Outcome binding is direct.** `ok` maps to `allowed`, including an idempotent replay; every `LAP_ERR_*` refusal maps to `denied`; a failure of verification itself maps to `error`. Reason codes stay in the extension, as section 2.1.1 requires.
- **No numbers.** LAP amounts and caps are carried as decimal strings, such as `"4200"`, as section 2.3 asks.

## What does not fit yet

1. **Registration.** Type ids are flat names from a curated registry (section 2.2); reverse-DNS ids are not used. `delegated-authority` is proposed below and is not registered, so a strict verifier rejects these records under C-REC-1. `validate_extensions` reports exactly that unless called with `allow_proposed=True`.
2. **The word "principal".** The contract's `principal_id` is the governed identity that acted: in LAP terms, the agent, the passport's `sub`. LAP's "principal", the responsible person or organisation, is the passport's `iss` and goes in `issuer_id`. Any registration needs one sentence on this.
3. **`caller-governance` co-emission.** Its required `purpose_declared` has no LAP source. LAP records carry `delegated-authority` alone unless the host application supplies a declared purpose.
4. **Attribution of refused calls.** The core needs a `principal_id` on every record. When the passport or the call signature fails, the record names the claimed subject with `authority_verified: "false"`, or `anonymous` when no passport was sent. Whether unverified attribution is acceptable is the registry's call.
5. **Two holders, two chains.** A LAP receipt is held by client and server alike; a chain belongs to one recorder. The two chains join on `request_hash` and `receipt_signature`; linking chains is outside version 1 of the contract.
6. **Append-only by convention.** The demo appends to a JSON Lines file. A real deployment declares its actual mechanism in the attestation manifest (section 2.7).

## Proposed registration: `delegated-authority` (draft)

All values are strings, following the `runtime-security` convention. OPTIONAL fields follow the `caller-governance` presence rule: absent means not recorded, null means recorded with no value.

- **REQUIRED:** `authority_format` (the authority artifact's format, here `lap-microcore/0`), `authority_verified` (`"true"` only if the artifact and the caller's proof of possession both verified), `decision_code` (`ok`, `error`, or the emitter's refusal code), `action`, `resource`.
- **OPTIONAL:** `authority_hash`, `issuer_id`, `subject_id`, `audience_id`, `proof_class`, `scope_hash`, `amount`, `unit`, `cap_max_per_tx`, `request_hash`, `response_hash`, `receipt_signature`, `receipt_signer_id`, `signature_base_hash`, `request_signature`, `idempotency_key`, `replay` (`first` or `replayed`).
- **event_type vocabulary:** `tool_call`: one record for every call to a tool that requires an authority check, allowed or refused (section 2.9); emission never blocks the call.
- **Outcome binding:** `ok` to `allowed`; any refusal code to `denied`; `error` to `error`.
- **Format-neutral by design:** `authority_format` names the artifact, so delegated-authority formats other than LAP's (OAuth rich authorization requests, macaroons, UCAN, payment mandates) could record into the same fields. LAP does not need to own this extension; the fields matter more than the name.

## Observations on contract 1.0.0, offered as questions

Each was reproduced against the files at `ddead4dca2`.

1. **The outcome vocabulary in the C-REC-5 fixtures.** Section 2.1.1 (spec line 110) closes the vocabulary to `allowed`, `denied`, `deferred` and `error`, and C-REC-1 (line 565) asks for "a legal `outcome` disposition". The three C-REC-5 fixtures use `outcome: 'recorded'` (`vectors/vectors.ts` lines 504, 539, 565). The reference verifier deliberately does not enforce the list (`vectors/audit-record-contract.ts` lines 75-79), so nothing fails. A legal value in those fixtures, or one vector that pins the list, would close the gap.
2. **Bare numbers.** Section 2.3 (lines 272-273) and C-REC-2 (line 570) exclude bare numbers from protected values, and Q-C (line 667) defers any number rule to a later canonical-form version. The reference canonicalizer still serializes numbers (`vectors/audit-record-contract.ts` lines 158 and 167-169), and no vector rejects one. A record containing a number is therefore hashed by the reference implementation but rejected by a spec-strict one such as this. A rejecting vector would settle it.
3. **Arrays.** The same section restricts values to strings, booleans and null, but the reference canonicalizer serializes arrays (line 172). The same suggestion applies.

## Files

- `lap-python/living_agents/audit_record.py`: the contract (canonical form, sealing, chain and manifest checks) and the LAP mapping (`lap_tool_call_record`, `verify_lap_receipt_in_record`).
- `lap-python/tests/test_audit_record.py`: the vector port, the strict readings above, and tests over the LAP chain.
- `examples/audit-record-contract/lap_chain.py` and `lap-chain.jsonl`: the deterministic scenario and its committed output (keys from the seed labels of `output/lip/test-vectors/vectors.json`).
