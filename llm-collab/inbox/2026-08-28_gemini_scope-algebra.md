MODEL: Gemini (Advanced Coding & Reasoning)
DIMENSION: 02-scope-algebra-design.md
DATE: 2026-08-28

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §4 Autonomy Envelope & §6.1 Scope Algebra]
    CLAIM: Wildcard expansion across hierarchical URI paths without explicit terminal separators allows scope escape and privilege escalation during attenuation.
    REASONING: If an envelope grants `mcp://tools/finance/*` and an attenuated child requests `mcp://tools/finance_admin/transfer`, a naive prefix check `strings.HasPrefix(child, parent_without_wildcard)` treats `finance_admin` as a child of `finance`. Path-based capability models require strict boundary-tokenized segment lattices.
    EVIDENCE: Context Pack §6.1 acknowledges attenuation crypto proves derivation, not semantic entailment, but leaves the path algebra undefined.
    PROPOSED FIX: Mandate strict segment-wise prefix subsumption: path $P_1 \subseteq P_2$ if and only if each path segment of $P_2$ exactly matches the corresponding segment of $P_1$, and wildcards `*` only match a single path segment while `**` is restricted to terminal segment position.

F2. [SEVERITY: SERIOUS] [TARGET: §4 Autonomy Envelope Budget Enforcement]
    CLAIM: Rolling time-window budget accounting is undecidable and non-deterministic without a synchronized, attested state store across distributed counterparties.
    REASONING: If an envelope authorizes "spend <= 500 USD per rolling 24h", counterparty A cannot know what counterparty B processed 23 hours ago without querying the spend authorizer. If the authorizer uses local sliding windows while counterparties compute calendar days, budget limits drift.
    EVIDENCE: Context Pack §4 notes "a budget without a named spend authorizer is disclosure of intent," but does not define the canonical time-bucket evaluation algorithm for the authorizer.
    PROPOSED FIX: Restrict v0 time-window accounting strictly to UTC epoch-aligned fixed buckets (e.g., `WINDOW_UTC_HOUR`, `WINDOW_UTC_DAY`) identified by `bucket_index = floor(timestamp / bucket_size)`. Prohibit continuous rolling sliding-window evaluations in client-side verifiable envelopes.

F3. [SEVERITY: SERIOUS] [TARGET: §4 Autonomy Envelope & §6.1 Scope Algebra]
    CLAIM: Multi-currency or commodity cap attenuation is undecidable at verification time without an external trusted oracle.
    REASONING: If a parent envelope grants 1000 USD and a sub-agent envelope specifies 900 EUR or 0.5 ETH, validating whether `Child <= Parent` requires exchange rate knowledge, turning a deterministic authorization check into a volatile external dependency.
    EVIDENCE: Context Pack §6.1 states "single-currency numeric caps" as a direction.
    PROPOSED FIX: Enforce strict single-currency invariant: an attenuated envelope MUST inherit the exact `currency_code` (ISO 4217 or CAIP-19 asset ID) of the parent. Any currency transformation MUST be rejected at parse time as `INEVALUABLE`.

F4. [SEVERITY: SERIOUS] [TARGET: §4 Autonomy Envelope Attenuation]
    CLAIM: Absence of an explicit monotonic delegation depth constraint allows infinite delegation chains that degrade flight recorder auditability and inflate verification latency.
    REASONING: An agent with an envelope can recursively spawn child envelopes with infinitesimal attenuations. When counterparty verifies the leaf envelope, it must verify $N$ cryptographic signatures and evaluate $N-1$ subset proofs.
    EVIDENCE: Context Pack §4 mentions "signed, attenuable mandate" but specifies no maximum chain length or hop decrement.
    PROPOSED FIX: Include a mandatory integer field `delegation_depth` in every envelope. Attenuated child envelope MUST have `child.delegation_depth = parent.delegation_depth - 1`. If `parent.delegation_depth == 0`, further delegation MUST fail validation.

F5. [SEVERITY: MODERATE] [TARGET: §6.1 Scope Algebra Counterparty Lattice]
    CLAIM: Open-ended counterparty matching (regex or arbitrary wildcard strings) creates non-deterministic subset validation.
    REASONING: Determining whether regular language $L_1 \subseteq L_2$ is PSPACE-complete for general regular expressions and undecidable for extended regexes with lookaheads.
    EVIDENCE: Context Pack §6.1 states "closed counterparty registries" as direction.
    PROPOSED FIX: Prohibit pattern matching in counterparty constraints. Counterparty filters MUST be explicit sets of canonical identifiers (`did:*`, `dns:*`, or URI in a declared registry). $C_1 \subseteq C_2$ evaluates strictly as set inclusion $C_{1,\text{allow}} \subseteq C_{2,\text{allow}} \land C_{2,\text{deny}} \subseteq C_{1,\text{deny}}$.

F6. [SEVERITY: MODERATE] [TARGET: §4 Autonomy Envelope Decay & Pulse]
    CLAIM: Coupling scope attenuation to variable decay timeouts enables sub-agents to bypass principal oversight if child envelopes specify longer decay tolerances than parents.
    REASONING: If Parent specifies `heartbeat_timeout = 300s` and Child specifies `heartbeat_timeout = 3600s`, the child agent could operate for 55 minutes after the parent is unresponsive.
    EVIDENCE: Context Pack §4 defines autonomy decay conditioned on heartbeat continuity.
    PROPOSED FIX: In the subset relation, constraint attenuation MUST require `child.max_decay_seconds <= parent.max_decay_seconds` and `child.witness_quorum >= parent.witness_quorum`.

F7. [SEVERITY: MODERATE] [TARGET: §4 Autonomy Envelope]
    CLAIM: Lack of canonical JSON/CBOR serialization rules prevents deterministic signature validation over scope sets across heterogeneous language runtimes.
    REASONING: JSON key ordering, floating point representations, and unicode normalization differences cause byte-level signature verification failures.
    EVIDENCE: Context Pack §4 and §6.1 describe signed envelopes but omit canonical wire encoding.
    PROPOSED FIX: Mandate RFC 8785 (JSON Canonicalization Scheme - JCS) or deterministic CBOR (RFC 8949 §4.2) for envelope signing and hashing.

F8. [SEVERITY: MINOR] [TARGET: §6.1 Scope Algebra Schema Versioning]
    CLAIM: Forward compatibility without an explicit schema version identifier will cause legacy verifiers to misinterpret unknown action verbs as permitted wildcards.
    REASONING: If version 1 adds a verb `execute_destructive` under a namespace, a version 0 verifier unaware of the verb hierarchy might default-allow or crash.
    EVIDENCE: Context Pack §6.1 notes "versioned; state the governance rule for additions."
    PROPOSED FIX: Include mandatory `algebra_version: "aeon-scope-v0"` in every scope object. Verifiers MUST reject any envelope with an unrecognized `algebra_version` with error `UNSUPPORTED_ALGEBRA_VERSION`.

---

## DESIGNS

### AEON-Core Scope Algebra v0 Specification

#### 1. Formal EBNF Grammar

```ebnf
EnvelopeScopeSet  ::= '[' Scope ( ',' Scope )* ']'
Scope             ::= '{' 
                        '"v"' ':' '"aeon-scope-v0"' ','
                        '"act"' ':' Action ','
                        '"res"' ':' ResourcePattern ','
                        ( '"cap"' ':' NumericCap ',' )?
                        ( '"cp"' ':' CounterpartyConstraint ',' )?
                        ( '"depth"' ':' NonNegativeInteger ',' )?
                        ( '"decay_max_sec"' ':' PositiveInteger )?
                      '}'

Action            ::= VerbHierarchy | VerbWildcard
VerbWildcard      ::= '"*"'
VerbHierarchy     ::= '"' Namespace ':' SubVerb ( ':' SubVerb )* '"'
Namespace         ::= 'data' | 'finance' | 'compute' | 'comm' | 'identity' | 'governance'
SubVerb           ::= [a-z][a-z0-9_]*

ResourcePattern   ::= '"' Scheme '://' PathPattern '"'
Scheme            ::= 'mcp' | 'a2a' | 'ap2' | 'https' | 'did' | 'urn'
PathPattern       ::= Segment ( '/' Segment )* ( '/**' | '/*' )?
Segment           ::= [a-zA-Z0-9_\-\.\:\@]+

NumericCap        ::= '{'
                        '"max_per_tx"' ':' PositiveInteger ','
                        '"max_cumulative"' ':' PositiveInteger ','
                        '"unit"' ':' AssetIdentifier ','
                        '"window"' ':' TimeWindow
                      '}'
AssetIdentifier   ::= [A-Z]{3,5} | CAIP19AssetId
TimeWindow        ::= '"tx"' | '"utc_hour"' | '"utc_day"' | '"epoch_total"'

CounterpartyConstraint ::= '{'
                             ( '"allow"' ':' StringArray ',' )?
                             ( '"deny"' ':' StringArray )?
                           '}'
StringArray       ::= '[' ( '"' [^"]+ '"' ( ',' '"' [^"]+ '"' )* )? ']'
NonNegativeInteger ::= '0' | [1-9][0-9]*
PositiveInteger   ::= [1-9][0-9]*
```

#### 2. JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://aeon.org/schemas/v0/scope-algebra.json",
  "title": "AEONCoreScopeAlgebraV0",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "required": ["v", "act", "res"],
    "additionalProperties": false,
    "properties": {
      "v": { "type": "string", "const": "aeon-scope-v0" },
      "act": {
        "type": "string",
        "pattern": "^(\\*|(data|finance|compute|comm|identity|governance)(:[a-z][a-z0-9_]*)+)$"
      },
      "res": {
        "type": "string",
        "pattern": "^(mcp|a2a|ap2|https|did|urn)://[a-zA-Z0-9_\\-\\.\\:\\@]+(/[a-zA-Z0-9_\\-\\.\\:\\@]+)*(/\\*\\*|/\\*)?$"
      },
      "cap": {
        "type": "object",
        "required": ["max_per_tx", "max_cumulative", "unit", "window"],
        "additionalProperties": false,
        "properties": {
          "max_per_tx": { "type": "integer", "minimum": 1 },
          "max_cumulative": { "type": "integer", "minimum": 1 },
          "unit": { "type": "string", "pattern": "^[A-Z]{3,5}$" },
          "window": { "type": "string", "enum": ["tx", "utc_hour", "utc_day", "epoch_total"] }
        }
      },
      "cp": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "allow": { "type": "array", "items": { "type": "string", "format": "uri" }, "uniqueItems": true },
          "deny": { "type": "array", "items": { "type": "string", "format": "uri" }, "uniqueItems": true }
        }
      },
      "depth": { "type": "integer", "minimum": 0, "maximum": 16 },
      "decay_max_sec": { "type": "integer", "minimum": 10, "maximum": 604800 }
    }
  }
}
```

#### 3. Semantic Subset Relation & Proof of Attenuation ($S_{child} \subseteq S_{parent}$)

Given two scope sets $\mathcal{P}$ (parent) and $\mathcal{C}$ (child), $\mathcal{C} \subseteq \mathcal{P}$ holds if and only if for every scope $c \in \mathcal{C}$, there exists at least one scope $p \in \mathcal{P}$ such that $c \sqsubseteq p$, defined as:

1. **Version Match**: $c.v == p.v == \text{"aeon-scope-v0"}$.
2. **Action Subsumption ($c.act \preceq p.act$)**:
   - If $p.act == "*"$ then TRUE.
   - If $p.act == c.act$ then TRUE.
   - If $p.act$ is a namespace prefix of $c.act$ (e.g. $p.act = \text{"finance:pay"}, c.act = \text{"finance:pay:escrow"}$) then TRUE.
   - Else FALSE.
3. **Resource Subsumption ($c.res \preceq p.res$)**:
   - Parse URIs into scheme, host, and path segments.
   - Schemes and hosts must match exactly.
   - If $p.res$ ends in `/**`, $c.res$ path must share all preceding segments.
   - If $p.res$ ends in `/*`, $c.res$ must match exactly one additional segment.
   - Else, literal exact string equality is required.
4. **Cap Subsumption ($c.cap \preceq p.cap$)**:
   - If $p.cap$ is undefined, $c.cap$ can be anything (unconstrained $\to$ constrained is valid).
   - If $p.cap$ is defined:
     - $c.cap$ MUST be defined.
     - $c.cap.unit == p.cap.unit$ (exact match).
     - $c.cap.max\_per\_tx \le p.cap.max\_per\_tx$.
     - $c.cap.max\_cumulative \le p.cap.max\_cumulative$.
     - Window tightness lattice: $\text{"tx"} \sqsubseteq \text{"utc\_hour"} \sqsubseteq \text{"utc\_day"} \sqsubseteq \text{"epoch\_total"}$. Child window must be $\sqsubseteq$ parent window.
5. **Counterparty Subsumption ($c.cp \preceq p.cp$)**:
   - If $p.cp.allow$ exists, $c.cp.allow \subseteq p.cp.allow$.
   - If $p.cp.deny$ exists, $p.cp.deny \subseteq c.cp.deny$.
6. **Delegation Depth Subsumption ($c.depth \preceq p.depth$)**:
   - If $p.depth$ is present, $c.depth$ MUST be present and $c.depth \le p.depth - 1$.
7. **Decay Timeout Subsumption ($c.decay\_max\_sec \preceq p.decay\_max\_sec$)**:
   - If $p.decay\_max\_sec$ is present, $c.decay\_max\_sec \le p.decay\_max\_sec$.

#### 4. Worked Examples

##### 7 Valid Examples (Permitted Attenuations)
1. **Root Read-All to Narrow Read**:
   - Parent: `{"v":"aeon-scope-v0", "act":"data:read", "res":"mcp://storage/corp/**"}`
   - Child: `{"v":"aeon-scope-v0", "act":"data:read", "res":"mcp://storage/corp/public/*"}`
2. **Budget Attenuation**:
   - Parent: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/stripe/**", "cap":{"max_per_tx":10000, "max_cumulative":50000, "unit":"USD", "window":"utc_day"}}`
   - Child: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/stripe/invoices/**", "cap":{"max_per_tx":2000, "max_cumulative":10000, "unit":"USD", "window":"utc_day"}}`
3. **Counterparty Whitelist Narrowing**:
   - Parent: `{"v":"aeon-scope-v0", "act":"comm:send", "res":"a2a://network/chat/**", "cp":{"allow":["did:web:vendorA.com","did:web:vendorB.com"]}}`
   - Child: `{"v":"aeon-scope-v0", "act":"comm:send", "res":"a2a://network/chat/**", "cp":{"allow":["did:web:vendorA.com"]}}`
4. **Depth Decrement**:
   - Parent: `{"v":"aeon-scope-v0", "act":"compute:exec", "res":"mcp://sandbox/python/**", "depth":3}`
   - Child: `{"v":"aeon-scope-v0", "act":"compute:exec", "res":"mcp://sandbox/python/**", "depth":2}`
5. **Decay Tightening**:
   - Parent: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "decay_max_sec":300}`
   - Child: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "decay_max_sec":60}`
6. **Window Tightening (Cumulative to Per-Tx)**:
   - Parent: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":5000, "max_cumulative":20000, "unit":"USD", "window":"utc_day"}}`
   - Child: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":5000, "max_cumulative":20000, "unit":"USD", "window":"tx"}}`
7. **Action Sub-verb Specialization**:
   - Parent: `{"v":"aeon-scope-v0", "act":"finance:transact", "res":"ap2://escrow/**"}`
   - Child: `{"v":"aeon-scope-v0", "act":"finance:transact:release", "res":"ap2://escrow/**"}`

##### 3 Invalid Examples (MUST be Rejected as Inexpressible / Violations)
8. **REJECTED (Cross-Currency Translation Attempt)**:
   - Parent: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":100, "max_cumulative":100, "unit":"USD", "window":"tx"}}`
   - Child: `{"v":"aeon-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":90, "max_cumulative":90, "unit":"EUR", "window":"tx"}}`
   - *Reason*: `unit` mismatch. Dynamic FX conversion is inexpressible and rejected at parse time.
9. **REJECTED (Non-Decidable Natural Language Constraint)**:
   - Request: `{"v":"aeon-scope-v0", "act":"data:read", "res":"mcp://db/**", "condition":"only if sentiment is polite"}`
   - *Reason*: `additionalProperties: false` triggers schema failure; semantic predicates require human escalation.
10. **REJECTED (Privilege Escalation on Delegation Depth)**:
    - Parent: `{"v":"aeon-scope-v0", "act":"compute:exec", "res":"mcp://wasm/**", "depth":0}`
    - Child: `{"v":"aeon-scope-v0", "act":"compute:exec", "res":"mcp://wasm/**", "depth":0}`
    - *Reason*: Parent depth is 0; cannot issue child delegations.

---

## SELF-ATTACK & COMPARISON

### Self-Attack
1. **Expressivity Leak**: The algebra cannot express inter-resource dependencies (e.g., "may write to Resource B only if read from Resource A"). This is a deliberate feature: relational invariants belong in L7 Flight Recorder audit rules or L6 Interaction Contracts, not in static attenuation envelopes.
2. **Timezone/Bucket Boundary Jitter**: UTC day bucket resets at 00:00:00Z. An agent could execute a transaction at 23:59:59Z and another at 00:00:01Z, effectively consuming $2\times$ daily budget in 2 seconds. Mitigation: Applications requiring strict rate pacing must set `max_per_tx` alongside `max_cumulative`.

### Comparison with Prior Art
- **OAuth RAR (RFC 9396)**: RAR standardizes the `authorization_details` JSON array format but explicitly leaves authorization algebra, subset derivation, and attenuation logic out of scope. AEON v0 can be directly serialized as an OAuth RAR data type (`type: "aeon_envelope_v0"`).
- **Cedar (AWS)**: Cedar is a full policy language with boolean logic and entity stores. It is expressive but Turing-complete in entity evaluation, making client-side offline cryptographic attenuation verification heavy.
- **Biscuit / Macaroons**: Biscuit uses Datalog blocks with cryptographic third-party caveats. AEON Scope Algebra v0 is isomorphic to a restricted Datalog fragment with fixed predicates (`action()`, `resource_prefix()`, `cap_lte()`). AEON can compile directly to Biscuit caveats for implementations using Biscuit as their L5 wire token format.

---

## PRIOR ART
- **OAuth RAR (RFC 9396)**: Adopt JSON structure; serialize AEON envelope as RAR object.
- **Biscuit Token Spec (biscuitsec.org)**: Profile Biscuit Datalog caveats as an optional binary carrier for L5 envelopes.
- **UCAN v0.10**: Adopt capability attenuation chain structure; differ by enforcing closed verb/cap algebra rather than open W3C capability strings.
- **RFC 8785 (JSON Canonicalization Scheme - JCS)**: Adopt for cryptographic digest calculation over envelope JSON structures.

---

## SURVIVORS
1. **Single-Currency Invariant**: Resisting dynamic FX in the core algebra keeps subset checking strictly $O(1)$ and deterministic.
2. **Explicit Attenuation Depth**: Bounding recursive delegation chains eliminates verification DoS attacks.
3. **Closed Verbs & Fixed Schemas**: Refusing open-ended natural language predicates maintains cryptographic decidability.

---

## SCORE
8/10 — The proposed AEON-Core Scope Algebra v0 delivers a mathematically closed, decidable, and statically verifiable capability lattice that fully resolves §6.1. It trades esoteric conditional policy expressivity for deterministic security and clean embedding into OAuth RAR and Biscuit.
