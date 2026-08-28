# Prompt 04 — Systematic Threat Model

Paste this, then paste CONTEXT-PACK.md below it.

---

You are a security architect producing a systematic threat model for the proposal below — STRIDE discipline crossed with the CSA MAESTRO agentic layers and OWASP's agentic-security threat taxonomy. Not a vibe review: enumerate, per mechanism, attacker goals, capabilities, and concrete attack paths.

Attacker personas to run: (a) a malicious counterparty agent; (b) a compromised-but-certified agent; (c) a malicious principal (insider); (d) a thief of the principal's key; (e) a hostile ATL/witness operator; (f) a competitor performing economic denial (reputation sabotage, decay-triggering, receipt-ring pollution); (g) a platform vendor with custody of keys/memory; (h) a state-level censor. For each: what do they attack (passport, envelope, pulse/witness quorum, MEET steps, receipts/tenure, CONVEY, recorder, registration), what do they gain, what stops them in v0.2, and what doesn't.

Special attention: collusion attacks the single-adversary framing misses (witness+counterparty collusion; buyer+seller receipt farming across eras; principal+auditor); attacks on the *fixes* (can prospective-only suspension be exploited by starting long-running in-flight actions before going dark? can proof-class labels be laundered through re-issuance?); and privacy attacks (what does the MEET/registry/receipt graph leak about humans — who-meets-whom metadata, quiet-hours as burglary intel).

Deliver using the RESPONSE FORMAT: each finding = one attack (severity = impact × feasibility), with a PROPOSED FIX (mitigation or explicit residual-risk statement). End with the top-5 attacks the spec must address before any implementation ships, plus survivors and a security-posture score 1–10.
