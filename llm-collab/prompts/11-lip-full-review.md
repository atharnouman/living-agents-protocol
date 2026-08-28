# Prompt 11 — Full-Text LIP Review + §26 Lifecycle Review (round-3 priority #2)

*(For a reviewer with file access. Earlier rounds saw only condensed sketches; these are the real spec texts, most never externally reviewed.)*

---

You are an RFC-series specification editor and protocol reviewer. Read the full texts:

1. `E:\LivingAIAgents\output\lip\LIP-1-agent-passport-draft.md` (passport — round 2 saw only a sketch)
2. `E:\LivingAIAgents\output\lip\LIP-2-meet-draft.md` (MEET handshake — **never externally reviewed**)
3. `E:\LivingAIAgents\output\lip\LIP-4-micro-core-draft.md` (Micro-Core)
4. `E:\LivingAIAgents\output\LAP-founding-document.md` — **§26 only** (Accountability Chain, succession, HANDOFF, bounded lifespans, economic mortality — added after round 2, never reviewed)

Prior findings are all merged; do not resubmit anything from `E:\LivingAIAgents\llm-collab\IMPROVEMENTS-LOG.md`. Attack:

**LIP-2 (deepest — it's had zero external eyes):** walk the state machine as an implementer — is every transition's timeout, retry, and abort defined? What happens on duplicate messages, on messages arriving in a state that doesn't expect them, on a HAIL from an agent you're already ACTIVE with (session dedup)? Is the transcript-hash rule well-defined when messages interleave bidirectionally (who orders them)? Can CHARTER-A commitments be replayed across sessions? Is the fair-exchange sketch in §4 actually implementable from this text alone? Does the STH-gossip rule define what "inconsistent" means precisely enough to code?

**LIP-1:** the nine-step verification vs the field table — any field with no verification step, any step with no defined failure code? Is the two-serialization rule (JWS + optional VC envelope) a fork in disguise? Succession/HANDOFF (§26) implies passport mutations — but LIP-1 has no amendment/reissue section: what's the rule when the principal field changes?

**LIP-4:** is the upgrade path (§6) real — can a Micro-Core deployment actually move to full LIP-1/MEET without breaking, or are there incompatible choices (e.g., the JWT `typ`, the envelope subset)?

**§26:** attack the Accountability Chain — race conditions between HANDOFF and in-flight envelopes; what evidence suffices for "principal death" and who adjudicates it (can a hostile successor fake it?); the insolvency grace period vs FORCE_HALT; can economic mortality be weaponized (drain a competitor's witness retainer)?

Deliver as a NEW file `E:\LivingAIAgents\llm-collab\inbox\YYYY-MM-DD_<model>_lip-review.md` (never modify existing files): findings with severity + section cites + concrete corrected text; the 5 places most needing a state table or worked example; survivors; per-document readiness scores 1–10.
