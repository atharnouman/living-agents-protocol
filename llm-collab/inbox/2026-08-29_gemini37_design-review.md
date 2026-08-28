MODEL: Gemini 3.7 Flash
DIMENSION: 09-design-review.md
DATE: 2026-08-29

## FINDINGS

F1. [SEVERITY: FATAL] [TARGET: §9A LAP-Core Scope Algebra / Window Lattice Inversion]
    CLAIM: The window lattice relation `tx ⊑ utc_hour ⊑ utc_day ⊑ epoch_total` is mathematically inverted and allows unbounded budget inflation during delegation.
    REASONING: In capability delegation, $Child \sqsubseteq Parent$ means the child's permitted authority is a strict subset of the parent's. If a parent grants `max_per_tx: 50, max_cumulative: 100, window: utc_hour` (capping spending at $100 per hour), and a child attenuates the window to `window: tx` (with `max_per_tx: 50, max_cumulative: 50`), the child envelope contains no hourly cumulative constraint. If the child executes 1,000 transactions in one hour, it consumes $50,000 in that hour—violating the parent's $100/hour limit. A per-transaction window without a time-rate bound is *broader* in aggregate rate than a time-bucket window.
    EVIDENCE: §9A defines window tightness as `tx ⊑ utc_hour ⊑ utc_day ⊑ epoch_total`.
    PROPOSED FIX: Split cap attenuation into two independent, mandatory checks: (1) Instantaneous cap: `child.max_per_tx <= parent.max_per_tx`; (2) Rate cap: `child.rate_per_second <= parent.rate_per_second`, where rate is computed as `max_cumulative / window_duration_seconds`. A child window is valid if and only if `child.max_cumulative <= parent.max_cumulative` AND `child.window_duration_seconds <= parent.window_duration_seconds`.

F2. [SEVERITY: FATAL] [TARGET: §9B LAP Micro-Core / Missing Request Body & Audience Binding]
    CLAIM: The `LAP-Passport` HTTP header lacks cryptographic binding to the HTTP request payload and target audience, enabling cross-server replay and MITM payload mutation.
    REASONING: The Micro-Core JWT header contains the agent's key and envelope, but does not sign over `(http_method, http_uri, sha256(http_body), aud)`. A malicious Tool Server A that receives a valid `LAP-Passport` header during a benign `data:read` call can extract the header and replay it against Tool Server B to execute unauthorized actions, or an eavesdropper on unencrypted internal networks can attach the captured header to a mutated destructive request payload.
    EVIDENCE: §9B specifies: "Every request carries an LAP-Passport header (VC 2.0/JWT)... Receiver MUST (1) verify JWT signature against sub + iss DID doc; (2) check expires_at; (3) check act/res match the invocation."
    PROPOSED FIX: Replace raw static JWT headers with HTTP Message Signatures (RFC 9421) or an ephemeral DPoP-bound token (RFC 9449). The request MUST include an `LAP-Signature` header signing over `"@method", "@target-uri", "content-digest", "lap-passport-hash"`, with a mandatory `aud` (audience) claim matching the recipient's canonical DID/URI.

F3. [SEVERITY: FATAL] [TARGET: §9A LAP-Core Scope Algebra / Action-Prefix Semantic Inversion]
    CLAIM: Monotonic action-prefix subsumption (`A:B ⊒ A:B:C`) fails when sub-verbs add execution modalities or escalate authority rather than specializing restrictions.
    REASONING: The rule assumes every suffix extension is a strict restriction (e.g. `finance:pay` $\to$ `finance:pay:escrow`). However, in real-world API verbs, sub-verbs often represent compound or elevated actions: `data:read:all_tenants`, `finance:pay:recurring`, `compute:exec:unconfined`, or `governance:revoke:cascade`. Under naive prefix matching, an agent holding `data:read` can attenuate to `data:read:all_tenants` or `compute:exec` to `compute:exec:unconfined`.
    EVIDENCE: §9A states: "If p.act is a namespace prefix of c.act then TRUE."
    PROPOSED FIX: Action subsumption MUST NOT use free-form prefix string parsing. The action lattice MUST be governed by an explicit, normative Directed Acyclic Graph (DAG) in the LIP registry where parent-child relationships are declared with explicit subsumption edges. Any sub-verb not explicitly registered with a `subsumed_by` pointer in the registry DAG evaluates to `NON_SUBSUMING`.

F4. [SEVERITY: SERIOUS] [TARGET: §9B LAP Micro-Core / Tool Execution Asymmetry & Retry Double-Spend]
    CLAIM: Unilateral receipt generation without a 2-phase commit protocol causes unresolvable state drift and double spending on network retries.
    REASONING: When a client invokes a tool with `window: "tx"`, the tool server executes the action, updates internal state, and formats `LAP-Receipt`. If the connection drops before the HTTP response reaches the client (or the server crashes mid-response), the client timeout triggers a retry. Because Micro-Core lacks an idempotency key bound to the passport, the server processes the retry as a second independent transaction, executing the charge/action twice.
    EVIDENCE: §9B specifies: "Response carries LAP-Receipt... both parties append the tripartite entry to local append-only logs."
    PROPOSED FIX: Mandate an `Idempotency-Key` (IETF RFC draft-ietf-httpapi-idempotency-key-header) in all Micro-Core mutating requests, cryptographically bound into the request signature. Tool servers MUST cache receipt responses by `(agent_sub, idempotency_key)` and return the cached receipt without re-executing.

F5. [SEVERITY: SERIOUS] [TARGET: §9A LAP-Core Scope Algebra / Multiple Scope Matching & Union Cover Fallacy]
    CLAIM: Evaluating child scopes independently against single parent scopes fails for disjoint resource partitioning and multi-scope composition.
    REASONING: If Parent holds Scope 1: `{act: "data:read", res: "mcp://storage/us/**", cap: 100 USD}` and Scope 2: `{act: "data:read", res: "mcp://storage/eu/**", cap: 100 USD}`, a sub-agent attempting to create an envelope covering both `{act: "data:read", res: "mcp://storage/**"}` is correctly rejected. However, if a sub-agent requests two scopes: Scope C1 `{res: "mcp://storage/us/logs/*", cap: 100 USD}` and Scope C2 `{res: "mcp://storage/us/metrics/*", cap: 100 USD}`, naive 1-to-1 matching validates both against Scope 1, allowing the sub-agent to claim $2 \times 100 = 200\text{ USD}$ total budget, exceeding the parent's $100 cap.
    EVIDENCE: §9A specifies: "every child scope must be ⊑ some parent scope."
    PROPOSED FIX: Enforce Cumulative Cap Invariant across Scope Sets: When multiple child scopes match the same parent scope, the sum of child cumulative caps sharing that parent scope MUST NOT exceed the parent scope's `max_cumulative`: $\sum c_i.cap.max\_cumulative \le p.cap.max\_cumulative$.

F6. [SEVERITY: SERIOUS] [TARGET: §9B LAP Micro-Core / Synchronous DID Resolution DoS & SSRF]
    CLAIM: Synchronous resolution of `iss` and `sub` DIDs on every HTTP request exposes tool servers to request-amplification DoS and Server-Side Request Forgery (SSRF).
    REASONING: In Micro-Core Step 1, the receiver resolves the `iss` DID document. An attacker sending requests with `did:web:attacker-controlled-site.com` or `did:web:169.254.169.254` (cloud metadata endpoint) forces the tool server to perform synchronous outbound HTTP fetches, inducing latency spikes, worker thread exhaustion, and internal network scanning.
    EVIDENCE: §9B Step 1: "verify JWT signature against sub + iss DID doc."
    PROPOSED FIX: Require tool servers to use an authenticated DID caching layer with strict SSRF filtering (disallowing non-routable/private IP ranges) and rate-limiting. For high-throughput Micro-Core endpoints, support pre-shared public key discovery or `did:key` formats that require zero network resolution.

F7. [SEVERITY: MODERATE] [TARGET: §9A LAP-Core Scope Algebra / Counterparty Deny-List Attenuation Bypass]
    CLAIM: Incomplete set difference logic in counterparty filtering allows sub-agents to bypass parent deny lists by omitting deny fields.
    REASONING: If Parent specifies `allow: []` (any counterparty permitted) and `deny: ["did:web:competitor.com"]`, and Child specifies `allow: ["did:web:competitor.com"]` and `deny: []`, evaluating $c.cp.deny \supseteq p.cp.deny$ detects the violation. But if the evaluation engine only checks allow set inclusion ($c.allow \subseteq p.allow$), an empty parent allow list can be misinterpreted as permitting any explicit child allow entry.
    EVIDENCE: §9A notes: "counterparties = explicit allow/deny sets, no patterns."
    PROPOSED FIX: Formally define the effective counterparty set $E(C) = (\text{if } C.allow \neq \emptyset \text{ then } C.allow \text{ else } \mathcal{U}) \setminus C.deny$. Subsumption requires $E(Child) \subseteq E(Parent)$, and $Parent.deny \subseteq Child.deny$.

F8. [SEVERITY: MODERATE] [TARGET: §9B LAP Micro-Core / Clock Skew Rejections in Serverless Runtimes]
    CLAIM: Strict `expires_at > now_utc()` evaluation without clock-skew tolerance causes false-positive authorization failures across distributed cloud runtimes.
    REASONING: Serverless functions (AWS Lambda, Cloudflare Workers) routinely experience clock drift of $\pm 500\text{ms}$ to $5\text{s}$. A short-lived Micro-Core token (e.g. 30s TTL) generated on a client with a slightly forward clock will be rejected immediately by a tool server whose clock is 2 seconds behind.
    EVIDENCE: §9B Step 2: "check expires_at."
    PROPOSED FIX: Adopt standard JWT validation semantics (RFC 7519 §4.1.4): provide a default $\pm 60\text{-second}$ clock skew tolerance window, and require an issued-at (`iat`) claim with `iat - skew <= now_utc() <= expires_at + skew`.

F9. [SEVERITY: MINOR] [TARGET: §9A LAP-Core Scope Algebra / DID Canonicalization & Unicode Normalization]
    CLAIM: Unnormalized string comparisons in DID and URI matching create security bypasses via Unicode equivalence and Punycode spoofing.
    REASONING: `did:web:example.com` and `did:web:EXAMPLE.COM` or internationalized domain names (IDNs) with homoglyphs will fail direct string equality or allow filter evasion.
    EVIDENCE: §9A requires canonical serialization via RFC 8785 JCS, but JCS normalizes only JSON formatting, not semantic URI/DID string contents.
    PROPOSED FIX: All DID strings and Resource URIs MUST be normalized to Unicode Normalization Form C (NFC), ASCII lowercased for schemes and hostnames, and percent-encoding normalized (RFC 3986 §6.2.2) prior to subset evaluation.

---

## 3 CONCRETE ADVERSARIAL SCOPE PAIRS (Spec Verdict vs Correct Verdict)

### Example 1: The Sub-Verb Privilege Escalation Attack
- **Parent Scope**: `{"v":"lap-scope-v0", "act":"compute:exec", "res":"mcp://sandbox/**"}`
- **Child Scope**: `{"v":"lap-scope-v0", "act":"compute:exec:unconfined", "res":"mcp://sandbox/**"}`
- **Spec v0.3.1 Verdict**: **VALID (ALLOWED)**. The spec checks `strings.HasPrefix("compute:exec:unconfined", "compute:exec")` and passes action subsumption.
- **Correct Security Verdict**: **MUST BE REJECTED**. `unconfined` removes execution sandboxing, escalating privilege rather than restricting it.

### Example 2: The Window Lattice Inversion Rate-Explosion
- **Parent Scope**: `{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":50, "max_cumulative":100, "unit":"USD", "window":"utc_hour"}}`
- **Child Scope**: `{"v":"lap-scope-v0", "act":"finance:pay", "res":"ap2://rails/**", "cap":{"max_per_tx":50, "max_cumulative":50, "unit":"USD", "window":"tx"}}`
- **Spec v0.3.1 Verdict**: **VALID (ALLOWED)**. Because `tx ⊑ utc_hour`, the lattice treats `tx` as tighter than `utc_hour`.
- **Correct Security Verdict**: **MUST BE REJECTED**. In 1 hour, the child can issue 1,000 transactions spending \$50,000, violating the parent's \$100/hour cumulative limit.

### Example 3: The Multi-Scope Budget Split Attack
- **Parent Scope Set**:
  - `Scope P1`: `{"v":"lap-scope-v0", "act":"data:read", "res":"mcp://db/**", "cap":{"max_per_tx":100, "max_cumulative":100, "unit":"USD", "window":"utc_day"}}`
- **Child Scope Set**:
  - `Scope C1`: `{"v":"lap-scope-v0", "act":"data:read", "res":"mcp://db/users/**", "cap":{"max_per_tx":100, "max_cumulative":100, "unit":"USD", "window":"utc_day"}}`
  - `Scope C2`: `{"v":"lap-scope-v0", "act":"data:read", "res":"mcp://db/orders/**", "cap":{"max_per_tx":100, "max_cumulative":100, "unit":"USD", "window":"utc_day"}}`
- **Spec v0.3.1 Verdict**: **VALID (ALLOWED)**. Each child scope independently subsumes under `P1`.
- **Correct Security Verdict**: **MUST BE REJECTED**. Together, C1 and C2 permit spending \$200/day against a parent envelope capped at \$100/day.

---

## DESIGNS

### Corrected Formal Scope Subsumption & Attenuation Rules

```
Algorithm: Evaluate-Scope-Set-Attenuation(ParentScopeSet P, ChildScopeSet C)
-----------------------------------------------------------------------------
1. Normalize all URIs, DIDs, and Verbs to NFC, lowercase host/scheme.
2. Initialize ParentBudgetTracker: for each p in P, remaining_cap[p] = p.cap.max_cumulative.
3. For each child scope c in C:
     matched = FALSE
     For each parent scope p in P:
       If c.v == p.v AND
          DAG-Subsumes(p.act, c.act) AND
          Path-Subsumes(p.res, c.res) AND
          Counterparty-Subsumes(p.cp, c.cp) AND
          c.depth <= p.depth - 1 AND
          c.decay_max_sec <= p.decay_max_sec:
          
          If p.cap is defined:
             If c.cap is UNDEFINED or c.cap.unit != p.cap.unit: CONTINUE
             If c.cap.max_per_tx > p.cap.max_per_tx: CONTINUE
             If Duration(c.cap.window) > Duration(p.cap.window): CONTINUE
             If c.cap.max_cumulative > remaining_cap[p]: CONTINUE
             
             remaining_cap[p] -= c.cap.max_cumulative
          
          matched = TRUE
          BREAK
     If NOT matched:
       RETURN ERROR("Child scope cannot be soundly attenuated from parent set", c)
4. RETURN SUCCESS
```

---

## SURVIVORS
1. **Segment-Tokenized Path Invariant**: Enforcing strict segment delimiters prevents classic `/finance` vs `/finance_admin` prefix escape vulnerabilities.
2. **Explicit Attenuation Depth Decrement**: The monotonic `c.depth <= p.depth - 1` rule decisively prevents unbounded capability delegation chains.
3. **Single-Currency Invariant**: Rejecting dynamic exchange rate conversions at parse time keeps subset checking deterministic and offline-verifiable.

---

## SCORE
- **§9A Scope Algebra Implementability**: 6/10 — The foundation is solid, but the inverted window lattice, naive sub-verb prefixing, and multi-scope budget leakage must be patched to prevent catastrophic privilege escalations.
- **§9B Micro-Core Implementability**: 5/10 — As written, it is vulnerable to cross-server replay and HTTP desync; adding RFC 9421 HTTP Message Signatures and Idempotency Keys makes it a 9/10 weekend implementation.
