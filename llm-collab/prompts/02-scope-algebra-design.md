# Prompt 02 — Design the Scope Algebra (most-wanted contribution)

Paste this, then paste CONTEXT-PACK.md below it.

---

You are a language/type-system designer with authorization experience (Cedar, Biscuit/macaroon caveats, OAuth RAR/rich authorization requests, UCAN capabilities). The proposal below needs its single most load-bearing open problem solved: **LAP-Core Scope Algebra v0** (pack §6.1) — a deliberately tiny, closed vocabulary for autonomy-envelope scopes in which *semantic subset-checking is decidable*, so delegation attenuation can be cryptographically AND semantically verified.

Design it. Required properties: enumerated verb registry (versioned; state the governance rule for additions); numeric caps with explicit units and evaluation semantics (single settlement currency per envelope; define time-window accounting precisely — rolling vs calendar day, timezone rule); counterparty classes only as references to named closed registries; a wildcard/hierarchy lattice with a defined ⊆ relation and proof-of-subset procedure; explicit UNDEFINED semantics ("anything not expressible requires a human"); and a worked grammar (EBNF or JSON Schema) plus 10 worked examples including at least 3 that MUST be rejected as inexpressible.

Then attack your own design: where does it leak? What real-world mandate can't it express, and is that a feature? How does it version without breaking old envelopes? Compare honestly against OAuth RAR, Cedar policies, and Biscuit caveats — why not just use one of those (or: show how to embed yours in one of them).

Deliver: the design (grammar + examples), the self-attack, prior-art comparison, and the RESPONSE FORMAT sections (findings/survivors/score) from the end of the pack.
