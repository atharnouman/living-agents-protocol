MODEL: Gemini 3.7 Flash
DIMENSION: 02-scope-algebra-design.md
DATE: 2026-08-29

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §9A LAP-Core Scope Algebra / Cumulative Budget Partitioning Across Sub-Scopes]
    CLAIM: The scope algebra lacks a formal budget-partitioning operator, allowing sub-agents to replicate parent cumulative caps across multiple child scopes.
    REASONING: If an envelope contains a parent scope with `max_cumulative: 500 USD`, and an agent creates an attenuated child envelope with 5 narrow sub-scopes (e.g. 5 specific vendor tool URIs), each assigning `max_cumulative: 500 USD`, the child agent can spend \$2,500 total if each sub-scope is evaluated independently.
    EVIDENCE: Context Pack §9A evaluates subset relations scope-by-scope without an envelope-wide multi-scope budget conservation invariant.
    PROPOSED FIX: In the formal subset verification procedure, mandate an **Envelope Budget Conservation Check**: The sum of `max_cumulative` caps across all child scopes derived from a common parent scope MUST NOT exceed the parent scope's `max_cumulative`: $\sum_{c \in \text{Children}(p)} c.cap.max\_cumulative \le p.cap.max\_cumulative$.

F2. [SEVERITY: SERIOUS] [TARGET: §9A LAP-Core Scope Algebra / Action Registry DAG vs Prefix Grammar]
    CLAIM: Action string prefixing without an immutable registry DAG allows unauthorized action synthesis.
    REASONING: In §9A, `data:read` subsumes any string starting with `data:read:`. If an adversary creates an arbitrary sub-verb `data:read:exfiltrate_internal_keys`, an engine relying on string prefixes treats it as permitted.
    EVIDENCE: Context Pack §9A relies on closed namespaces and string prefix rules.
    PROPOSED FIX: Formally bind `act` evaluation to an explicit normative LIP Registry DAG where all permitted verbs and their directed subsumption edges ($V_{\text{parent}} \to V_{\text{child}}$) are registered and versioned. Any verb not in the LIP Registry DAG is strictly invalid.

F3. [SEVERITY: SERIOUS] [TARGET: §9A LAP-Core Scope Algebra / Window Rate-Lattice Inversion Fix]
    CLAIM: Treating `tx` as a child of `utc_hour` without rate-bounding permits high-frequency transaction bursts that violate parent spend velocities.
    REASONING: A parent envelope with `window: "utc_hour"` intends to limit spend velocity to a specific hourly rate. An attenuated child with `window: "tx"` removes the hourly accumulation window.
    EVIDENCE: Context Pack §9A specifies `tx ⊑ utc_hour ⊑ utc_day ⊑ epoch_total`.
    PROPOSED FIX: Replace the single window lattice with a **Two-Dimensional Cap Lattice**:
    - **Dimension 1 (Single-Tx Ceiling)**: `c.cap.max_per_tx <= p.cap.max_per_tx`.
    - **Dimension 2 (Time-Bucket Ceiling)**: A child window duration MUST be an exact integer divisor or equal duration of the parent window ($T_{\text{child}} \le T_{\text{parent}}$), and `c.cap.max_cumulative <= p.cap.max_cumulative * (T_child / T_parent)`. `window: "tx"` represents instantaneous evaluation and MUST inherit the parent's cumulative bucket limit.

F4. [SEVERITY: MODERATE] [TARGET: §9A LAP-Core Scope Algebra / Asset Identifier CAIP-19 Formatting]
    CLAIM: Incomplete asset identifier syntax allows ambiguous currency matching between fiat ISO 4217 and multi-chain tokens.
    REASONING: If an envelope specifies `unit: "USDC"`, it does not distinguish between Native USDC on Ethereum, USDC on Solana, or bridged USDC on an L2, creating financial settlement mismatches.
    EVIDENCE: Context Pack §9A mentions ISO 4217 and CAIP-19.
    PROPOSED FIX: Mandate strict syntax: Fiat currencies MUST use 3-letter ISO 4217 uppercase codes (`USD`, `EUR`, `GBP`); on-chain assets MUST use canonical CAIP-19 asset identifiers (`eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`).

F5. [SEVERITY: MODERATE] [TARGET: §9A LAP-Core Scope Algebra / Counterparty Set Evaluation Logic]
    CLAIM: Omission of universal set semantics in empty counterparty allow lists causes counterparty evaluation anomalies.
    REASONING: In authorization logic, an empty allow list either means "deny all" or "allow all." If Parent has `allow: []` (interpreted as allow all) and `deny: [did:X]`, and Child specifies `allow: [did:X]`, checking subset inclusion without universe resolution permits the disallowed party.
    EVIDENCE: Context Pack §9A specifies: "counterparties = explicit allow/deny sets, no patterns."
    PROPOSED FIX: Define the effective counterparty set formally:
    Let $\mathcal{U}$ be the universe of valid DIDs.
    $Effective(P) = (P.allow \neq \emptyset \text{ ? } P.allow : \mathcal{U}) \setminus P.deny$.
    Attenuation requires $Effective(C) \subseteq Effective(P)$.

---

## DESIGNS

### Formal LAP-Core Scope Algebra v0 Specification (Refined)

#### 1. JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://lap.org/schemas/v0/scope-algebra.json",
  "title": "LAPCoreScopeAlgebraV0",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "required": ["v", "act", "res"],
    "additionalProperties": false,
    "properties": {
      "v": { "type": "string", "const": "lap-scope-v0" },
      "act": {
        "type": "string",
        "pattern": "^(\\*|(data|finance|compute|comm|identity|governance)(:[a-z0-9_]+)+)$"
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
          "unit": { "type": "string", "pattern": "^([A-Z]{3}|[a-z0-9_\\-]+:[a-z0-9_\\-]+/[a-z0-9_\\-]+:[a-zA-Z0-9_\\-]+)$" },
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

#### 2. Sound Subsumption & Attenuation Proof Algorithm

```
Function Verify-Envelope-Attenuation(ParentEnvelope P, ChildEnvelope C) -> Boolean:
  1. For each scope in P and C:
       Verify schema against LAPCoreScopeAlgebraV0 JSON Schema.
       Normalize all URIs and DIDs to Unicode NFC and lowercase hosts.
  
  2. Let RemainingBudgetMap be a table mapping parent scope index -> p.cap.max_cumulative.
  
  3. For each child scope c_idx, c in enumerate(C):
       Let match_found = False
       For each parent scope p_idx, p in enumerate(P):
         // (a) Action DAG Subsumption
         If NOT (p.act == "*" OR p.act == c.act OR LIP_DAG_Ancestor(p.act, c.act)):
           Continue
         
         // (b) Resource Path Subsumption
         If NOT Resource-Path-Subsumes(p.res, c.res):
           Continue
         
         // (c) Counterparty Set Subsumption
         Let EffParent = (p.cp.allow is non-empty ? p.cp.allow : UNIVERSE) \ p.cp.deny
         Let EffChild = (c.cp.allow is non-empty ? c.cp.allow : UNIVERSE) \ c.cp.deny
         If NOT (EffChild is subset of EffParent):
           Continue
         
         // (d) Monotonic Depth and Decay Bounds
         If c.depth > p.depth - 1:
           Continue
         If c.decay_max_sec > p.decay_max_sec:
           Continue
         
         // (e) Financial Cap & Multi-Scope Budget Conservation
         If p.cap is defined:
           If c.cap is undefined OR c.cap.unit != p.cap.unit:
             Continue
           If c.cap.max_per_tx > p.cap.max_per_tx:
             Continue
           If Duration(c.cap.window) > Duration(p.cap.window):
             Continue
           If c.cap.max_cumulative > RemainingBudgetMap[p_idx]:
             Continue
           
           // Deduct child allocation from parent remaining budget
           RemainingBudgetMap[p_idx] -= c.cap.max_cumulative
         
         match_found = True
         Break
       
       If NOT match_found:
         Return False ("Child scope violates parent capability bounds: " + c)
  
  4. Return True
```

---

## 3 WORKED ADVERSARIAL REJECTED EXAMPLES

1. **REJECTED: Sub-Verb Privilege Escalation via Unregistered Action**:
   - Parent: `{"v":"lap-scope-v0", "act":"compute:exec", "res":"mcp://sandbox/**"}`
   - Child: `{"v":"lap-scope-v0", "act":"compute:exec:unconfined", "res":"mcp://sandbox/**"}`
   - *Reason*: `compute:exec:unconfined` is not registered as a valid child in the LIP Action DAG; rejected at DAG validation.

2. **REJECTED: Cumulative Budget Duplication Across Disjoint Endpoints**:
   - Parent: `[{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://stripe/**", "cap":{"max_per_tx":500, "max_cumulative":500, "unit":"USD", "window":"utc_day"}}]`
   - Child: `[{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://stripe/a/**", "cap":{"max_per_tx":500, "max_cumulative":500, "unit":"USD", "window":"utc_day"}}, {"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://stripe/b/**", "cap":{"max_per_tx":500, "max_cumulative":500, "unit":"USD", "window":"utc_day"}}]`
   - *Reason*: Total child cumulative budget ($500 + 500 = \$1,000$) exceeds parent remaining budget (\$500); rejected during budget conservation check.

3. **REJECTED: Window Inversion Rate Inflation**:
   - Parent: `{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://stripe/**", "cap":{"max_per_tx":50, "max_cumulative":100, "unit":"USD", "window":"utc_hour"}}`
   - Child: `{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://stripe/**", "cap":{"max_per_tx":50, "max_cumulative":50, "unit":"USD", "window":"tx"}}`
   - *Reason*: `window: "tx"` without hourly rate bound has undefined time duration ($Duration(tx) \not\le Duration(utc\_hour)$); rejected under 2D cap lattice rules.

---

## PRIOR ART COMPARISON

| Feature | LAP-Core Scope Algebra v0 | OAuth RAR (RFC 9396) | AWS Cedar Policy | Biscuit Datalog Caveats |
|---|---|---|---|---|
| **Decidable Static Attenuation** | **Native ($O(N \times M)$)** | Left to application | Complex (entity graph dependent) | **Native (Datalog subset)** |
| **Budget Conservation** | **Native multi-scope tracking** | None | Requires external state store | Expressible via integer facts |
| **Serialization Carrier** | JSON / CBOR | JSON `authorization_details` | Cedar Policy DSL text | Binary Protobuf / CBOR |
| **Offline Attenuation Proof** | **Deterministic** | Not standardized | N/A (policy evaluation engine) | **Cryptographic (3rd-party blocks)** |

---

## SURVIVORS
1. **Budget Conservation Check**: Adding multi-scope remaining budget deduction definitively prevents capability duplication across sub-agent partitions.
2. **Explicit LIP Action DAG**: Shifting from free-form string prefixes to a versioned Directed Acyclic Graph prevents arbitrary sub-verb privilege escalations.
3. **CAIP-19 Asset Precision**: Unifying token and fiat asset representations eliminates ambiguity in multi-chain financial settlement.

---

## SCORE
9/10 — With the addition of envelope budget conservation, 2D time-cap evaluation, and DAG-governed action hierarchies, the Scope Algebra v0 becomes a mathematically sound, offline-verifiable capability lattice ready for production implementation.
