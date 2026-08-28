# Prompt 09 — Design Review: Scope Algebra + Micro-Core (round-2 priority)

Paste this, then paste CONTEXT-PACK.md below it.

---

You are a merciless spec implementer — the engineer who finds the bug by trying to write the code. Round 2's highest-value target is §9 of the pack: two concrete draft designs. Attack them as if you had to ship them Monday.

**§9A — LAP-Core Scope Algebra v0.** Try to break it: construct concrete scope pairs where the subset relation gives the WRONG answer (child judged ⊑ parent but semantically broader, or vice versa); attack the action-hierarchy rule (`finance:pay` ⊒ `finance:pay:escrow` — is verb-prefix subsumption actually safe, or can a sub-verb mean something broader than its parent?); attack the window lattice (is `tx ⊑ utc_hour` even coherent — what does it mean for a per-transaction cap to be "tighter than" an hourly cumulative?); the `epoch_total` semantics; the interaction of `deny` lists with attenuation; what happens when a parent has multiple overlapping scopes and the child matches parts of several (the cover problem — is per-scope matching against ONE parent scope sound, or does it wrongly reject valid unions / wrongly accept invalid splits?); canonicalization edge cases (unicode in DIDs, case sensitivity of verbs/schemes); and the governance question (what stops the verb registry from bloating into FIPA's ontology graveyard?). Write at least 3 concrete adversarial scope-pair examples with the verdict the spec gives vs the verdict it should give.

**§9B — LAP Micro-Core.** Attack it as the first thing real developers touch: replay of the JWT header across requests (no nonce/audience binding?); the missing binding between the passport and the specific request (can a captured header authorize a different call?); `window:"tx"` semantics with retries; receipt collision/omission (server signs receipt but client never stores it — what's the dispute story?); clock skew on `expires_at`; whether verification step 3 (act/res "match the invocation") is decidable without the full algebra; DoS cost of DID resolution per request; and what a malicious tool server can do with a valid passport it has seen. Then judge: is Micro-Core actually implementable in an afternoon as claimed? List what's missing for that to be true (test vectors, error codes, key discovery).

Deliver using the RESPONSE FORMAT: findings with severity + concrete failing examples + proposed fixes; a DESIGNS section with corrected rule text where you have it; survivors; an implementability score 1–10 for each of the two designs.
