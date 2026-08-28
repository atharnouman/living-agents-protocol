# LIP-3: LAP-Core Scope Algebra v0 (draft v0.2)

*Status: DRAFT v0.2 (round-2 corrections merged 2026-08-29). Origin: base design contributed by Gemini (round 1, inbox/2026-08-28_gemini_scope-algebra.md); soundness corrections contributed by Gemini 3.7 (round 2, inbox/2026-08-29_gemini37_design-review.md and _scope-algebra.md); triaged and refined by Claude+author. Resolves founding-document open problem §22.1; correction record in spec §25.1.*

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
- `res` — URI, scheme from a closed set (`mcp | a2a | ap2 | https | did | urn`), **segment-tokenized** path pattern: `*` = exactly one segment; `**` terminal only; matching is per whole segment (`finance_admin` is NOT a child of `finance`).
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

## 5. The subset relation (child scope c ⊑ parent scope p)

c ⊑ p iff ALL of: (1) versions equal; (2) **action**: `p.act` is `*`, equal, or a **registry-DAG ancestor** of `c.act`; (3) **resource**: segment-wise subsumption per §2; (4) **caps**: the two-dimensional rule of §4 with identical `unit`; (5) **counterparties**: `E(c) ⊆ E(p)` and `p.deny ⊆ c.deny`; (6) **depth**: `c.depth ≤ p.depth − 1` (`p.depth == 0` forbids delegation); (7) **decay/witness**: `c.decay_max_sec ≤ p.decay_max_sec`, child witness quorum ≥ parent's.

## 6. Envelope-level check: budget conservation (v0.2)

Scope-by-scope checking alone is insufficient: five narrow child scopes each carrying the full parent cap would replicate the budget fivefold. Verification therefore runs over the **scope sets**:

```
Verify-Envelope-Attenuation(P, C):
  normalize all scopes (§2); validate schema
  remaining[p] := p.cap.max_cumulative for each p in P
  for c in C (canonical sorted order):
    find first p in P (canonical sorted order) with c ⊑ p (§5) AND,
      if p.cap defined: c.cap.max_cumulative ≤ remaining[p]
    if none: REJECT(c)
    remaining[p] -= c.cap.max_cumulative   (when p.cap defined)
  ACCEPT
```

**Soundness/completeness note (normative documentation duty):** this greedy first-match procedure is *sound* (never accepts an invalid set) but *incomplete* — with overlapping parent scopes, evaluation order can reject a child set that a different parent assignment would satisfy. v0 accepts this conservatism and mandates the canonical sorted evaluation order above so all implementations agree on which sets pass. (Full completeness is a bipartite-matching/flow problem; out of scope for v0.)

**Sibling issuance caveat:** static verification covers one child envelope at a time. Conservation across *separately issued* sibling envelopes is an **issuer duty** — the principal/authorizer tracks allocations across everything it signs; the algebra makes per-envelope verification sound, not global accounting. (This is the §8-of-spec budget-enforcement-locus rule appearing at the delegation layer.)

## 7. Deliberate exclusions (features, not gaps)

No cross-currency math; no rolling windows in client-verifiable envelopes; no conditional/relational predicates (Interaction Contracts or authorizer policy instead); no pattern-matched counterparties; no unregistered verbs.

## 8. Adversarial test vectors (seed set — MUST ship with the reference implementation)

REJECT cases: `compute:exec` → `compute:exec:unconfined` (unregistered/broadening edge); windowed parent → `window:tx` child (rate unbounded); two children each carrying full parent cumulative (conservation); `allow:[] deny:[X]` parent → `allow:[X]` child (effective sets); `USD` → `EUR` (unit); `finance` → `finance_admin` path prefix (segmenting); NFC/case homoglyph DID pairs (normalization).
ACCEPT cases: the seven valid attenuations from the round-1 contribution, re-checked under the two-dimensional rule (the round-1 "window tightening" example is now a REJECT).

## 9. Embeddings (carrier formats)

Carrier-neutral; compiles to an OAuth RAR (RFC 9396) `authorization_details` type (`"type": "lap_envelope_v0"`), Biscuit datalog caveats (binary), or UCAN capability fields (JSON). The subset checker is identical in all carriers.

## 10. Open items before LIP-3 leaves draft

Action Registry v0 contents (the actual verb DAG with narrowing rationales); registry governance text; `epoch_total` duration semantics under envelope renewal; full test-vector suite from §8; reference subset-checker (TypeScript + Python) fuzzed against prefix-escape, unit-mismatch, window-inversion, and conservation classes; the matching-order determinism proof.
