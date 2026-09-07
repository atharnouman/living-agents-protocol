# LIP-3: LAP-Core Scope Algebra v0 (draft v0.3)

*Status: DRAFT v0.4 (external hostile-review round merged 2026-09-08: closed scheme set, decoded-canonical patterns, budget-check corrected to the debit; property-based fuzzing merged the same day; round-2 corrections 2026-08-29). Origin: base design contributed by Gemini (round 1, inbox/2026-08-28_gemini_scope-algebra.md); soundness corrections contributed by Gemini 3.7 (round 2, inbox/2026-08-29_gemini37_design-review.md and _scope-algebra.md); triaged and refined by Claude+author. Resolves founding-document open problem §22.1; correction record in spec §25.1.*

## 1. Purpose and design stance

Every enforcement claim in LAP (attenuation proofs, CHARTER disclosure, conformance testing, audit, arbitration) consumes shared scope semantics. Attenuation cryptography (Biscuit/macaroon/UCAN chains) proves *derivation*; only inside a **closed, deliberately tiny algebra** does it also prove *semantic entailment* (child ⊆ parent). The humility rule is normative: **anything not expressible in the algebra requires a human decision.** Open vocabularies are where FIPA and the Semantic Web died; pressure to widen this algebra is the death-spiral to resist.

## 2. Scope object (normative shape)

```json
{
  "v": "lap-scope-v0",
  "act": "finance:pay",
  "res": "ap2://rails/stripe/invoices/**",
  "cap": { "max_per_tx": 2000, "max_cumulative": 10000, "unit": "USD", "window": "utc_day" },
  "cp":  { "allow": ["did:web:vendora.com"], "deny": [] },
  "depth": 2,
  "decay_max_sec": 300
}
```

- `v` — mandatory; unknown versions rejected (`UNSUPPORTED_ALGEBRA_VERSION`). Never default-allow unknown constructs.
- `act` — a verb from the **LIP Action Registry, which is an explicit versioned DAG** (v0.2 change): namespaces `data | finance | compute | comm | identity | governance`; every verb and every parent→child subsumption edge is registered by LIP with a reviewed narrowing rationale. **String prefixing confers nothing**: `compute:exec:unconfined` is not a child of `compute:exec` unless the registry declares that edge (it must not — "unconfined" broadens). Unregistered verbs are invalid outright.
- `res` — URI, scheme from a closed set (`mcp | a2a | ap2 | https`; `git` is reserved for the experimental lap-git commit binding), **segment-tokenized** path pattern: `*` = exactly one segment; `**` terminal only; matching is per whole segment (`finance_admin` is NOT a child of `finance`). **Closed syntax (v0.3):** a pattern is scheme, authority and path — nothing else. A query, a fragment, or an empty interior segment (`//`) MUST be rejected (`LAP_ERR_RES`), never default-allowed; one trailing slash is tolerated. **Decoded canonical text (v0.4):** a pattern MUST contain no percent-encoding, no backslash, and no control character — these are exactly the forms a downstream proxy resolves *after* authorization (`/safe/..\admin`, `/safe/%252e%252e/admin`), so with dot-segment rejection they close the traversal class; a verifier decodes and canonicalizes the request resource before matching. **Scheme is validated against the closed set (v0.4):** any other scheme (`http`, `file`, `gopher`, …) is refused, and `did`/`urn` are not resource patterns in v0: a DID identifies a counterparty (it belongs in `cp`), and URNs have no defined role in the algebra yet. A `*` pattern subsumes the identical `*` pattern at the same depth (they denote the same set — the fuzzer found the reference refusing an identical delegation); it never subsumes `**`.
- `cap` — see §4 (two-dimensional rule, v0.2).
- `cp` — explicit allow/deny sets of canonical identifiers; no patterns. **Effective-set semantics (v0.2)**: `E(X) = (X.allow ≠ ∅ ? X.allow : Universe) \ X.deny`.
- `depth` — remaining delegation hops (0–16).
- `decay_max_sec` — maximum tolerated pulse gap for this scope.

**Normalization before any comparison (v0.2)**: all DIDs/URIs to Unicode NFC; schemes and hostnames ASCII-lowercased; percent-encoding normalized (RFC 3986 §6.2.2). Canonical serialization for signing/hashing: RFC 8785 JCS or deterministic CBOR (RFC 8949 §4.2) — noting JCS canonicalizes JSON structure, not URI semantics, hence the separate normalization step.

## 3. Asset identifiers (v0.2 strict syntax)

Fiat: 3-letter uppercase ISO 4217 (`USD`, `EUR`). On-chain: full canonical CAIP-19 (`eip155:1/erc20:0xa0b8…eb48`). A bare token symbol ("USDC") is invalid — it is ambiguous across chains. Cross-unit attenuation is rejected at parse time (`INEVALUABLE`); no FX oracles in the trust core.

## 4. Caps — the two-dimensional rule (v0.2, replaces the withdrawn window lattice)

*v0.1's single lattice `tx ⊑ utc_hour ⊑ utc_day ⊑ epoch_total` was unsound: a `tx` window carries no rate bound, so a child with `window:tx` could spend a parent's hourly cumulative every few seconds. Withdrawn.*

Two independent dimensions, both mandatory in attenuation checks:
1. **Per-transaction ceiling**: `c.max_per_tx ≤ p.max_per_tx`.
2. **Time-bucket ceiling**: if the parent has a time window, the child MUST also carry a time window; `Duration(c.window) ≤ Duration(p.window)` with the child window equal to, or an integer subdivision of, the parent window; and `c.max_cumulative ≤ p.max_cumulative × (Duration(c.window) / Duration(p.window))`. A bare `tx` window cannot attenuate a windowed parent. (`tx` remains valid where the parent itself has no time window; `epoch_total` = one bucket spanning envelope validity.)

The proportional scaling is deliberately conservative (it forbids bursty-but-bounded children); deployments needing burst shaping express it at the spend authorizer, not in the static algebra. Windows are UTC epoch-aligned buckets (`bucket = floor(ts / size)`); rolling windows are prohibited in client-verifiable envelopes (authorizer-side only). Known limit, unchanged: bucket-boundary burst ≈ 2× at midnight straddles — mitigate with `max_per_tx`; rail-side authorizers remain the true budget enforcement locus.

**Cap schema validation (v0.2, round-4 audit F8 — MUST, before any arithmetic):** `max_per_tx` and `max_cumulative` MUST be non-negative integers within the implementation's exact-integer range (JS: `Number.isSafeInteger`; canonical decimal strings/BigInt above 2^53), `max_per_tx ≤ max_cumulative`, `unit` a non-empty string, and `window ∈ {tx, utc_hour, utc_day, epoch_total}`. A negative cumulative would otherwise *increase* remaining budget on subtraction (a "credit" scope). `tx` parents admit only `tx` children (a differently-based child would rate-expand a per-transaction budget). **Interop bound and exact arithmetic (v0.3):** envelopes travel as JSON and are consumed by JavaScript verifiers, so every implementation MUST reject values above 2^53−1, and window scaling and debit arithmetic MUST be exact-integer (no double-precision intermediates): the differential fuzzer found one-unit divergences between the two reference ports above ~10^11.

## 5. The subset relation (child scope c ⊑ parent scope p)

**Schema before semantics (v0.3 — MUST):** a scope is shape-validated before any comparison — `v` a string, `act` a string or a list of strings, `res` a string, `cp` allow/deny lists of strings, `cap` per §4, `depth` an integer 0–16, `decay_max_sec` a non-negative integer. A malformed scope is never compared: the single-scope predicate returns false, envelope verification fails loudly (`LAP_ERR_SCOPE_SCHEMA`; `LAP_ERR_CAP_SCHEMA` for caps), and resource syntax errors are `LAP_ERR_RES`. Implementations MUST NOT surface language-level type errors for malformed input (the fuzzer found both reference ports doing so, and one port comparing a missing `act` as "grants nothing ⊆ grants nothing").

c ⊑ p iff ALL of: (1) versions equal; (2) **action**: `p.act` is `*`, equal, or a **registry-DAG ancestor** of `c.act` (verbs may be a bare string or an array — compared by value, never by reference; both ports MUST agree, round-4 audit); (3) **resource**: segment-wise subsumption per §2, with dot-segments (`.`/`..`) and encoded separators (`%2f`/`%5c`/`%2e`) **rejected** so a `/safe/**` scope cannot authorize `/admin` after a proxy resolves the path (F10); (4) **caps**: the two-dimensional rule of §4 with identical `unit`; (5) **counterparties**: `E(c) ⊆ E(p)` and `p.deny ⊆ c.deny`; (6) **depth**: `c.depth ≤ p.depth − 1` (`p.depth == 0` forbids delegation); (7) **decay/witness**: `c.decay_max_sec ≤ p.decay_max_sec`, child witness quorum ≥ parent's.

**The exported single-scope predicate MUST include the cap conjunct (F9).** A named "does child ⊑ parent" function that omits caps is a trap for a direct caller (a policy engine): it returns `true` for a child whose cap is hundreds of times broader. `scopeSubsumes`/`scope_subsumes` therefore evaluate (4) themselves; envelope verification calls only the total predicate plus allocation accounting.

## 6. Envelope-level check: budget conservation (v0.2)

Scope-by-scope checking alone is insufficient: five narrow child scopes each carrying the full parent cap would replicate the budget fivefold. Verification therefore runs over the **scope sets**:

```
Verify-Envelope-Attenuation(P, C):
  normalize all scopes (§2); validate schema
  remaining[p] := p.cap.max_cumulative for each p in P
  for c in C (canonical sorted order):
    find first p in P (canonical sorted order) with c ⊑ p (§5) AND,
      if p.cap defined: debit(p.cap, c.cap) ≤ remaining[p]   // v0.4: the DEBIT, not the raw
    if none: REJECT(c)
    remaining[p] -= debit(p.cap, c.cap)    (when p.cap defined)
  ACCEPT

  where debit(pc, cc) = cc.max_cumulative × Duration(pc.window) / Duration(cc.window)
        for timed windows (integer floor), else cc.max_cumulative.
```

**Debit in the parent's window units (v0.2, round-4 audit F7 — MUST).** Subtracting a child's *raw* `max_cumulative` from a differently-windowed parent under-counts: 24 hourly children of a daily parent, each `max_cumulative = P/24`, individually pass §4 yet together permit 24 buckets × 24 sub-windows = a 24× daily expansion (worse across distinct resource paths). The debit MUST convert the child allocation into the parent window's units — a `utc_hour` child of a `utc_day` parent debits `max_cumulative × 24`, so one such child exhausts the parent. Even so, static accounting is not a substitute for the spend authorizer's atomic per-bucket ledger.

**Soundness/completeness note (normative documentation duty):** this greedy first-match procedure is *sound* (never accepts an invalid set) but *incomplete* — with overlapping parent scopes, evaluation order can reject a child set that a different parent assignment would satisfy. v0 accepts this conservatism and mandates the canonical sorted evaluation order above so all implementations agree on which sets pass. (Full completeness is a bipartite-matching/flow problem; out of scope for v0.)

**Sibling issuance caveat:** static verification covers one child envelope at a time. Conservation across *separately issued* sibling envelopes is an **issuer duty** — the principal/authorizer tracks allocations across everything it signs; the algebra makes per-envelope verification sound, not global accounting. (This is the §8-of-spec budget-enforcement-locus rule appearing at the delegation layer.)

## 7. Deliberate exclusions (features, not gaps)

No cross-currency math; no rolling windows in client-verifiable envelopes; no conditional/relational predicates (Interaction Contracts or authorizer policy instead); no pattern-matched counterparties; no unregistered verbs.

## 8. Adversarial test vectors (seed set — MUST ship with the reference implementation)

REJECT cases: `compute:exec` → `compute:exec:unconfined` (unregistered/broadening edge); windowed parent → `window:tx` child (rate unbounded); two children each carrying full parent cumulative (conservation); `allow:[] deny:[X]` parent → `allow:[X]` child (effective sets); `USD` → `EUR` (unit); `finance` → `finance_admin` path prefix (segmenting); NFC/case homoglyph DID pairs (normalization).
ACCEPT cases: the seven valid attenuations from the round-1 contribution, re-checked under the two-dimensional rule (the round-1 "window tightening" example is now a REJECT).

**Property-based fuzzing (v0.3 — shipped in both reference ports: `lap-reference/test/fuzz.test.js`, `lap-python/tests/test_fuzz.py`).** A deterministic generator, written identically in both languages, drives the same random scopes through both implementations. Properties: reflexivity one delegation hop down; transitivity along attenuation chains (with a non-vacuity floor on the accept rate); instantiation (a pattern covers every concrete path it generates); no widening (wildcard escalation and origin changes are always refused); agreement with an exact-integer oracle for the two-dimensional cap rule; agreement with an exact-integer oracle for budget conservation; typed errors only on malformed input; and a committed cross-port decision digest (`test-vectors/algebra-fuzz-digest.json`) that fails whenever the ports disagree on a single decision. The first run found three defects — an identical `*` delegation refused, language-level type errors on malformed scopes, and one-unit double-arithmetic divergence between the ports — all fixed before v0.3.

## 9. Embeddings (carrier formats)

Carrier-neutral; compiles to an OAuth RAR (RFC 9396) `authorization_details` type (`"type": "lap_envelope_v0"`), Biscuit datalog caveats (binary), or UCAN capability fields (JSON). The subset checker is identical in all carriers.

## 10. Open items before LIP-3 leaves draft

Action Registry v0 contents (the actual verb DAG with narrowing rationales); registry governance text; `epoch_total` duration semantics under envelope renewal; full test-vector suite from §8; reference subset-checker fuzzing — **done (v0.3, §8)**; the matching-order determinism proof.
