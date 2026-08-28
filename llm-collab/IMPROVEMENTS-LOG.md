# LAP Improvements Log

*Every merged contribution, with source attribution. Spec versions refer to LAP-founding-document.md (named AEON-founding-document.md before the 2026-08-28 rename).*

| Date | Source | Dimension | Contribution (short) | Merged into |
|---|---|---|---|---|
| 2026-08-28 | Claude (3× adversarial subagents) | demand / technical / adoption | Full three-round review: 40+ findings; FIPA correction; 3 contradictions; strategy pivot to publish-then-infiltrate | v0.1 → v0.2 (§23 changelog) |
| 2026-08-28 | Gemini (8 reviews via llm-collab kit) | all eight dimensions | See detailed triage below | v0.2 → v0.3 (§23–§24) |
| 2026-08-28 | User decision + Claude namespace verification | naming | Project renamed AEON → **Living Agents Protocol (LAP)**; AIPs→LIPs; all live files renamed; "agent passport" kept lowercase-generic (Workday now ships a product with the capitalized name) | v0.3.1 |
| 2026-08-29 | Gemini 3.7 Flash (4 reviews, round 2) | design-review / technical / threats / algebra | See round-2 triage below | v0.3.1 → v0.4 (§25) |
| 2026-08-30 | Gemini 3.7 Flash (3 reviews, round 3) | code-review / lip-review / publish-readiness | See round-3 triage below | v0.4.2 → v0.4.3 |

---

## v0.3 triage detail (Gemini batch, 2026-08-28)

### MERGED — verified and folded into the spec

**Security (inline fixes in §4/§6/§8/§19 + §24.2):**
- TOCTOU on prospective-only suspension → FORCE_HALT revocation distinct from suspension + settlement phase-gates *(tech F2 ≡ threat F1, deduped — the batch's standout catch)*
- CHARTER reconnaissance → two-stage CHARTER: ZK/range commitments first, full disclosure at BIND *(tech F1 ≡ threat F4, deduped)*
- Public presence schedule = principal sleep/travel-pattern leak → removed from passport; bilateral at PULSE *(threat F8 — genuine privacy catch)*
- Witness hardening: checkpoint-bound attestations, random witness selection, challenge-before-non-liveness *(tech F3 ≡ threat F3)*
- Era = runtime-environment digest, not bare model tag (quantization/LoRA/params drift) *(tech F4)*
- Self-anchor finality: UNVERIFIED_PENDING_FINALITY until chain-appropriate finality *(tech F5)*
- Store-and-forward handshake: epoch-bounded challenges, replay caches, abort on dormancy mutation *(tech F6)*
- delegation_warranty_claim strengthening of the taint liability rule *(tech F7)*
- Proof-class revocation via W3C Bitstring Status List, checked at PROVE *(tech F8)*
- Countersigned turn sequencing in BIND (kills dual-log dispute deadlock) *(tech F9)*
- KeyRotationEvent dual-signed continuity *(tech F10)*
- Principal-key multisig/social recovery + time-locked root mutations *(threat F2; advances §22.3)*
- Receipt-graph weighting against farming rings *(threat F5; extends §14.1)*
- M-of-N diverse-network anchor verification *(threat F6)*
- Spend-authorizer DoS → pre-allocated sub-budget vouchers *(threat F9)*
- Pre-CONVEY memory poisoning → sanitization pass at transfer *(threat F10)*

**Scope Algebra (§24.3 + AIP-3 draft):** complete candidate design — segment-tokenized paths (prefix-escape fix), single-currency invariant, epoch-aligned buckets only, set-only counterparties, monotonic depth, decay/quorum monotonicity, JCS/CBOR canonicalization, version-reject-unknown, EBNF + JSON Schema + 10 worked examples *(scope-algebra F1–F8 + design — resolves open problem §22.1 to "candidate under refinement")*

**Prior-art profiling (§24.1):** ATL→IETF SCITT profile; Passport→W3C VC 2.0 + SPIFFE/WIMSE mapping; Envelope→OAuth RAR (RFC 9396)/GNAP (RFC 9635) + Biscuit/UCAN carriers; MEET→Noise AKE (+optional DIDComm packaging); Recorder→OTel GenAI + RFC 3161/SCITT seals; CONVEY→EPP (RFC 5730) transfer states (advances §22.7); Pulse→cite-and-differ vs DIDComm Trust Ping/XMPP *(prior-art F1–F8; novelty-after-sweep honestly assessed at ~4/10 — remaining novel core: pulse-gated envelopes, era-stamps, constitution commitments, BIND contracts)*

**Legal (§24.4):** GDPR hash-linkability fix — salted blinded commitments, salt-destruction erasure (CJEU Breyer C-582/14; WP29 05/2014) *(legal F1 — corrected a real overclaim)*; EU AI Act mapping to deployer duties (Art. 12 / Art. 26 / Art. 14 / Art. 50 — article-level only, paragraphs pending lawyer verification) *(legal F2)*; CHARTER = actual notice = apparent-authority shield (Restatement (Third) Agency §§2.03/3.03) — resolved our open question: disclosure legally protects the principal *(legal F3)*; proof classes ↔ eIDAS 2.0 QEAA/OIDC4VCI (advances §22.2) *(legal F4)*; spend authorizers MUST be authorization-only, never custody funds (MSB/PSD trigger) *(legal F5)*; habeas humanum → normative "Human Escalation Guarantee" as BIND clause *(legal F6 + naming F3)*; RFC 3161/SCITT-sealed logs for evidence admissibility *(legal F7)*

**Naming & terminology (§24.5):** Constitution/Envelope/Interaction Charter/Interaction Contract split *(naming F5)*; Principal/Title Holder/Custodian triad *(naming F6)*; PMIF→APMF (ISO collision) *(naming F4)*; OpenAEON/aeon-spec packaging (AEON retail/magazine/crypto collisions) *(naming F1)*; RFC-2119 normative/informative split adopted as AIP editorial rule *(naming F7)*; 5 sections flagged for state tables *(carried into AIP work)*

**Adoption ops (§24.6–24.7):** code-first sequencing (SDK+demo → essay → arXiv) *(adoption F2)*; ~60% effort on MCP/A2A middleware route *(adoption F1)*; conformance = CLI tool, certification blueprint stays non-normative reserve *(adoption F3, partially — see softened)*; NOTICE-file + canonical URL + OpenTimestamps release stamping *(adoption F4)*; numeric pull/kill gates *(adoption F6)*; witness/log economics model (escrow retainers + x402 query micro-fees) as §22.5 direction *(freeform F1)*; 3-line SDK decorator ergonomic bar *(freeform F2)*; **Micro-Core one-pager as Wedge #1** *(freeform design — possibly the batch's highest-leverage adoption idea)*; MEET state-machine table seeded into AIP-2 *(tech design)*

**Scope fence (§24.8):** Concern #10 admitted by ceremony — Forensic Evidence Bundling & Arbitration Handshake (`aeon-evidence-v0`) *(freeform F3)*

### SOFTENED — accepted in principle, weakened on verification or judgment
- "TEE MUST for AL-3+" → SHOULD + substrate-attestation class labels (API-hosted models cannot produce TEE quotes; a MUST would exclude the entire hosted-model world) *(threat F7)*
- "Drop AEON Post for Aries Pickup v2" → profile Aries/DIDComm mediators first; AEON claims only the wake-priority delta *(prior-art F9)*
- "Cut certification blueprint from the spec entirely" → kept as explicitly non-normative reserve (§9/§10 already deferred); active artifact is the CLI only *(adoption F3)*
- "Drop insurer track entirely for 2026" → deprioritized to opportunistic-only, not deleted *(adoption F5)*
- Full rename of "autonomy decay" → concept keeps its name; normative mechanism named "pulse-gated suspension" *(naming F2)*
- EU AI Act paragraph-level citations → merged at article level only; paragraph numbers flagged for qualified-lawyer verification *(legal F2)*

### REJECTED — with reasons
- Specific champion name/role pairings ("David Recordon / A2A maintainers", "Travis Fischer / MCP Community") — could not be verified as accurate role attributions; risk of embarrassing outreach. The *tactic* (three named maintainers with tailored hooks) is accepted; names to be re-researched from actual repo maintainer lists. *(adoption F7 — textbook example of why the verification step exists)*
- 2029 "CloudReserve" post-mortem narrative — accepted as informative storytelling material for the essay/demo, not spec content. *(freeform design — reclassified, not rejected on merits)*

### DEDUPES
tech F1 ≡ threat F4 (CHARTER recon) · tech F2 ≡ threat F1 (TOCTOU) · tech F3 ≡ threat F3 (witness collusion) · naming F3 ≡ legal F6 (habeas humanum register split)

---

## Round-2 triage detail (Gemini 3.7 batch, 2026-08-29)

### MERGED — verified and folded into spec v0.4 + LIP-3 v0.2
**Algebra (the round's core):** window-lattice inversion → 2D cap rule *(design F1 ≡ algebra F3 — standout catch, confirmed by construction)*; action prefix escalation → registry DAG *(design F3 ≡ algebra F2)*; multi-scope budget replication → envelope budget conservation *(design F5 ≡ algebra F1)*; deny-list bypass → effective-set semantics *(design F7 ≡ algebra F5)*; strict ISO-4217/CAIP-19 syntax *(algebra F4)*; NFC/URI normalization *(design F9)*; three adversarial scope-pair vectors adopted into the LIP-3 test seed.
**Micro-Core:** RFC 9421/DPoP request+audience binding *(design F2)*; idempotency keys *(design F4)*; ±60s clock skew + iat *(design F8)*; SSRF-filtered cached DID resolution *(design F6)*.
**v0.3-fix second-order bugs:** FORCE_HALT buyer-exit-scam → action vs settlement phase-gates, "halt stops authority, never debts" *(tech F1)*; era digest impossible for hosted APIs → two-track digest, decoding params excluded *(tech F2)*; concurrent ZK over-commitment → authorizer Reservation Tickets *(tech F3)*; countersign transport deadlock → ASW-style fair exchange with L7 arbitration fallback *(tech F5)*; sleep-window challenge mismatch → wake-cadence-scaled TTL, mediator single-retrieval *(tech F6)*; Bitstring status-list availability/privacy → SCITT-sealed snapshots *(tech F7)*.
**Threats:** voucher double-spend → counterparty-bound single-use vouchers *(threat F1 — fixed a hole introduced by our own v0.3 fix)*; evidence-bundle exfiltration → Merkle selective-disclosure redaction *(threat F2)*; VRF pre-computation → commit-reveal seed with agent nonce *(threat F3)*; SCITT split-view → STH gossip at PROVE, downgrade + log disqualification *(threat F4)*; ZK verification DoS → pre-auth throttling *(threat F5, mechanism only — see rejected)*; TEE side-channels → pulse-epoch key ratcheting *(threat F6)*.

### SOFTENED
- `VERIFIED_OPTIMISTIC` fifth trust state → posture guidance instead (treat PENDING_FINALITY as DEGRADED-equivalent for low-stakes non-money/non-PII scopes) *(tech F4)*.
- Flat escalation bond → graduated friction (rate limits; refundable micro-bond only for repeated/automated demands); the anti-DoS-vs-unconditioned-right tension documented in-spec *(threat F7)*.

### REJECTED / CORRECTED AT TRIAGE
- "RFC 9261" as the pre-auth mechanism citation — imprecise (that is TLS Exported Authenticators); mechanism merged, citation discarded.
- Contributed verification algorithm accepted **with a triage-added caveat the reviewer missed**: greedy first-match + budget draw-down is sound but incomplete under overlapping parent scopes; canonical evaluation order mandated, conservatism documented (LIP-3 §6).

### DEDUPES
design F1≡algebra F3 · design F3≡algebra F2 · design F5≡algebra F1 · design F7≡algebra F5.

### Round-2 meta-observation
Volume halved vs round 1 (~30 findings vs ~45) while severity concentrated on the two draft designs — the intended effect of packing §9 with real spec text. Convergence signal: the reference model itself drew zero new structural findings; everything actionable now lives at the mechanism/wire level, which is implementation territory. **The bottleneck is now building, not reviewing.**

## Round-3 triage detail (Gemini 3.7 batch, 2026-08-30)

### MERGED — verified (several by direct execution) and folded into code + LIPs + docs
**Code (library now 31/31):** b58Decode leading-zero/empty bug — confirmed by trace and test, fixed *(code F1, the batch's standout)*; passport DID normalization *(code F3 — accepted with a triage CORRECTION: the reviewer's proposed `normalizeUri` fix would have lowercased case-sensitive did:key identifiers and corrupted keys; implemented a DID-safe `normalizeDid` instead, plus a regression test proving the distinction)*; integer-floor cap scaling *(code F5)*; timing-safe commitment comparison *(code F6)*; wildcard acts rejected loudly in Micro-Core *(code F2, adapted — see softened)*; jcs integer-subset documented *(code F9)*; 5 contributed tests adopted (one adapted to LIP-4 semantics).
**Demo honesty:** reservation tickets now enforced at settlement — nonce in the signature base, single-use, per-order re-issue *(code F7)*; independent third witness added, suspension requires 2 observers *(code F8)*.
**LIP-2:** symmetric session tie-breaker for simultaneous HAIL *(lip F1)*; lock-step sequencing + duplicate-drop + canonical transcript definition *(lip F3)*; normative STH consistency criteria — size-equal root mismatch vs RFC 6962 consistency proof *(lip F4)*; fair-exchange wire fields *(lip F9)*.
**LIP-1:** PassportHandoffEvent + amendment-chain verification, closing the §26 HANDOFF↔Genesis contradiction *(lip F2)*; self-asserted step-6 bypass *(lip F7)*.
**LIP-4:** dual-`typ` upgrade compatibility + `LAP-Envelope` header *(lip F6)*.
**§26:** succession hardening — unreachability ⇒ dormancy only, involuntary transfer needs attested legal evidence + 30-day logged challenge window *(lip F5)*; flat per-epoch witness fees (anti-griefing) *(lip F8)*.
**Publish:** essay de-jargoned (habeas humanum → Human Escalation Guarantee framing; blockchain line → SCITT/timestamping language) *(pub F1, F3)*; paper abstract reframed profiles-first *(pub F2)*; brief TLS-comparison toned *(pub F4 — partial, kept the role analogy)*; References section (10 entries) + formal Appendix A + measured benchmarks added to paper *(arXiv mandatory revisions 1–3 satisfied)*; claims audit applied — 31/31 tests (audit said 25; more were added during triage), 191 checks, ~140 fixes, 26 sections, v0.4.3/v1.0-draft version consistency; anchors tense honest ("pending calendar attestation").

### SOFTENED / REJECTED
- Micro-Core DAG/wildcard support *(code F2 as proposed)* — REJECTED as contrary to LIP-4 §2(3) equality-only minimalism; merged the real defect (silent wildcard never-match) as loud rejection + spec line. Contributed Test 1 adapted accordingly.
- CRLF-tolerant signature-base parsing *(code F4)* — REJECTED: RFC 9421 signatures bind exact bytes; transit mutation already fails signature verification; tolerance would loosen semantics.
- Reviewer's `normalizeUri`-on-DIDs fix — corrected at triage (above).

### Incident note
Second external-tool file-corruption event: after the round-3 read-only review, `LAP-position-paper.md` was found overwritten on disk with `*`→`D` and stripped `#` characters (same class as the round-2 prompt-06 corruption). Restored in full from the in-session copy. The kit's read-only rule stands; version control for the project directory is now urgent.

## Pending triage
*(none — inbox batches of 2026-08-28, 2026-08-29, and 2026-08-30 fully processed)*
