# Implement LAP Micro-Core in an afternoon

A conformance challenge. **Scope: LIP-4 Micro-Core server-side verification plus LIP-1 passport verification — not the whole protocol.** It is deliberately small: a few hundred lines in any language with an Ed25519 library, and you can prove your implementation correct without trusting us, because the oracle is a set of deterministic test vectors.

## What you need

| Primitive | Standard | Notes |
|---|---|---|
| Ed25519 sign/verify | RFC 8032 | any mainstream crypto library |
| SHA-256 | FIPS 180-4 | hex and base64url forms both used |
| base58btc | Bitcoin alphabet | for `did:key` (multicodec prefix `0xed01` + 32-byte key); preserve leading zeros |
| base64url (no padding) | RFC 4648 §5 | JWS segments, digests, signatures |
| Canonical JSON | RFC 8785 (JCS) | the vectors use only ASCII strings, integers, booleans, null, objects, arrays — a JCS subset is sufficient |
| JWS compact, `alg: EdDSA` | RFC 7515 | header/payload are JCS-canonical before base64url |

## The oracle

[`output/lip/test-vectors/vectors.json`](output/lip/test-vectors/vectors.json) — generated from fixed seeds. Use `now = 1787000100` wherever a clock is needed; it sits inside every validity window.

## The checklist — pass all ten and you conform

1. **`did:key` decoding.** For each of `keys.principal`, `keys.agent`, `keys.tool_server`: decode `did` → the raw 32-byte public key's hex MUST equal `public_key_hex`.
2. **Canonicalization is byte-identical.** `JCS(passport.claims)` MUST equal `passport.canonical_jcs` exactly; likewise `JCS(genesis.claims)` = `genesis.canonical_jcs`.
3. **Constitution hash.** `sha256hex(constitution.text)` = `constitution.sha256`.
4. **Passport verifies under LIP-1 (steps 1–5).** `passport.jws`: signature verifies with the *principal's* key (`principal.id` in the claims); `v == "lip1-v0"`; the agent is not its own principal; `iat`/`exp` valid at `now` with ±60 s skew.
5. **Tamper rejection.** Change any one claim, re-encode the payload, keep the original signature → MUST reject with `LAP_ERR_SIG`.
6. **Genesis chain.** `sha256hex(passport.canonical_jcs)` = `genesis.claims.passport_sha256`, and `sha256hex(genesis.canonical_jcs)` = `genesis.sha256`.
7. **Micro-Core passport JWT.** `micro_core.passport_jwt` verifies with `expected_aud = "did:web:tools.example.com"`; a different audience MUST reject (`LAP_ERR_AUDIENCE`); **a verifier called with no expected audience MUST also reject** — fail closed, never fail open.
8. **Request signature (RFC 9421-style base).** `micro_core.request_signature_b64url` verifies over the exact bytes of `micro_core.rfc9421_signature_base` using the **agent's** key (the passport's `sub` — never a caller-supplied identifier). The base MUST contain lines for `"@method"`, `"@target-uri"`, `"content-digest"`, `"lap-passport-hash"`, and `"@signature-params"`; the `content-digest` line MUST equal `sha-256=:` + base64url(sha256(`micro_core.request_body`)) + `:`; the passport-hash line MUST equal `sha256:` + sha256hex(`passport_jwt`). Changing one byte of the body MUST reject (`LAP_ERR_DIGEST`); a base missing any required line MUST reject (`LAP_ERR_SIG_PARAMS`). Do **not** trim or normalize line endings — signatures bind exact bytes. A signature string that is not canonical base64url — padding characters, characters outside the URL-safe alphabet, or non-zero trailing bits (replace the final character of `request_signature_b64url`, an `A`, with `B`: a lenient decoder returns the same bytes) — MUST reject (`LAP_ERR_ENCODING`). A signature has exactly one textual form.
9. **Invocation check.** With the JWT's envelope (`act: ["finance:pay"]`, a `billing/**` resource, a per-transaction cap in USD): `act finance:pay`, resource `mcp://tools.example.com/billing/pay`, amount `4200 USD` → allowed; `act data:read` → `LAP_ERR_ACT`; resource `mcp://tools.example.com/admin/keys` → `LAP_ERR_RES`; amount `6000` → `LAP_ERR_CAP`; an envelope containing `"*"` as an act → reject loudly. Resource matching is segment-wise with terminal-only wildcards; a child `**` may never widen a parent `*`; dot-segments are rejected.
10. **Receipt.** `micro_core.receipt_base` + `receipt_signature_b64url` verify against `keys.tool_server.did`, and the two embedded hashes match `sha256hex(micro_core.request_body)` and `sha256hex('{"status":"paid","receipt":"R-77"}')`. Compare hashes in constant time.

Error names to emit: `LAP_ERR_{PASSPORT_SIG | SIG | AUDIENCE | EXPIRED | REQ_SIG | SIG_PARAMS | DIGEST | ACT | RES | CAP | ISSUER | PROOF_CLASS | REPLAY}`.

## If you get stuck

Two reference implementations pass exactly this checklist from the same vectors: [`lap-reference/`](lap-reference/) (Node, zero dependencies) and [`lap-python/`](lap-python/) (Python, one dependency). Read them freely; the point of the challenge is an *independent* implementation, so match the vectors, not our code.

## Submitting

Open a pull request adding `implementations/<language>-<name>/` containing a README and a script that runs the ten checks and prints pass/fail — or simply open an issue with a link. Every conforming implementation is listed in the main README with credit. Spec text is CC-BY-4.0; your code stays yours under whatever license you choose.

## An honest note on what this counts for

This project's adoption gate distinguishes **unsolicited** implementations (someone found LAP worth implementing on their own) from **solicited** ones (someone took up this challenge). Both are welcome and both are listed; only the first is treated as a strong demand signal, because we refuse to game our own metrics. Take the challenge for the reason it deserves: it is a small, well-specified, cryptographically honest protocol, and building it teaches you exactly how an agent proves who it is, whose authority it carries, and what it is allowed to do.
