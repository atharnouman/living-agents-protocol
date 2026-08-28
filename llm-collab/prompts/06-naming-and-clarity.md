# Prompt 06 — Naming, Clarity, and Spec Hygiene

Paste this, then paste CONTEXT-PACK.md below it.

---

You are a specification editor (RFC-series discipline) and a naming critic. Three jobs on the proposal below. Note: the project was renamed to Living Agents Protocol (LAP) and core terminology was normalized in v0.3.1 — do not re-litigate the settled names (LAP, ALIVE, MEET, Pulse, CONVEY, Genesis Record, pulse-gated suspension, APMF, Interaction Charter vs Interaction Contract); audit what remains.

1. **Naming audit (remaining surface).** Assess: LAP's residual collisions (the legacy X.25/ISDN link-layer protocols LAPB/LAPD; "lap" as a plain English word) — do they matter in practice?; the trust-state names (VERIFIED/DEGRADED/UNVERIFIED/REVOKED and UNVERIFIED_PENDING_FINALITY); AL-0..5; "era-stamped receipts"; "LAP Floor"; "Micro-Core"; "spend authorizer"; "witness"; "tripwire". For each: collision risk you're confident is real, pronounceability across non-English engineering cultures, and whether the metaphor misleads about semantics.

2. **Terminology consistency.** Find every place the pack still uses two words for one concept or one word for two (e.g., registration vs verification vs certification; witness vs monitor vs observer; suspension vs revocation vs expiry; log vs recorder vs ledger). Propose the single normative term for each.

3. **Spec hygiene.** Identify claims that should be RFC-2119 normative (MUST/SHOULD/MAY) but are prose; normative statements hiding in "honest framing" paragraphs; and the 5 places that most need worked examples or state tables now that LIP-3 and Micro-Core exist (§9 of the pack).

Deliver using the RESPONSE FORMAT (findings; survivors = names/terms that are genuinely strong; clarity score 1–10).
