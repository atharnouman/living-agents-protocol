# LAP — Context Pack for External Reviewers (round 2)

*You are reading a condensed, self-contained summary of the **Living Agents Protocol (LAP)**, spec **v0.3.1**, 2026-08-28 (renamed from "AEON" the same day). A prompt above this pack tells you which dimension to work on and what output format to use. Everything below is the material. This is a ROUND-2 pack: the proposal has already survived three review rounds (two adversarial rounds by Claude, one eight-dimension batch by Gemini, ~85 findings merged). Your job is to find what all of them missed, and to attack the fixes and the new draft designs in §9.*

---

## 1. What LAP is

Recent protocols gave AI agents tools (MCP), task exchange (A2A), and payments (AP2, x402). Nothing standardizes agent **existence**: identity that survives restarts, memory that survives vendor changes, authority that stays bounded while unsupervised, proof of liveness, ownership and transfer, and a human who ultimately answers. LAP is (a) a seven-layer OSI-style reference model that gives existing protocols coordinates and names the missing layers, (b) candidate mechanisms for those layers — deliberately specified as *profiles of existing standards* wherever real prior art exists, and (c) an honest open-problems agenda. It competes with nobody: MCP/A2A/AP2 are "the roads," LAP is the missing control plane — the TLS-handshake role, never the HTTP-payload role.

**Status honesty:** v0.3.1 draft by a lone author (plus AI assistance). No consortium, no certification program, no users yet. Strategy is code-first, "byline not a body": ship SDK + Micro-Core + a staged overnight demo, then essay, then arXiv, then file mechanisms as extensions into venues with distribution (~60% effort on MCP/A2A middleware; W3C AI Agent Protocol CG; OWASP agentic security; watching the new ITU agent-trust focus group and NIST AI Agent Standards Initiative). Institutional apparatus is deferred until ≥2 external parties implement something unprompted.

## 2. Scope — the fence

Eight concerns with no owning standard, plus two admitted amendments:
1. Persistent agent identity with principal binding, lineage, and policy commitment.
2. Presence & lifecycle (alive now? sleeping? retired?).
3. Autonomy envelopes (machine-readable unsupervised authority).
4. Portable memory with provenance/consent (format renamed **APMF**).
5. Delegation chains with auditable attenuation.
6. The stranger handshake.
7. The flight recorder (tamper-evident action log).
8. Death/retirement (no zombie authority).
+1 (conditional): store-and-forward for sleeping agents ("LAP Post") — Aries Pickup/DIDComm mediators must be profiled first; LAP claims only the wake-priority delta.
+2 (admitted v0.3): forensic evidence bundling & arbitration handshake (`lap-evidence-v0`) — extracts the dual-signed contract, recorder Merkle paths, and witness proofs into one package for an arbitrator.

## 3. The LAP-7 model

| # | Layer | Question | Slots in | LAP adds |
|---|---|---|---|---|
| L1 | Substrate | Where does it run? | OCI, microVMs, WASM, TEEs | runtime profile (tokens metered); migration/snapshot semantics |
| L2 | Identity | Who is it, provably? | **W3C VC 2.0**, SPIFFE/WIMSE, DIDs | Agent Passport profile; Genesis Record; no-orphan rule |
| L3 | Memory | What does it remember; whose is it? | vector stores, memory vendors | APMF portable memory; consent classes; forget-propagation |
| L4 | Vitality | Is it alive; where in its life? | DIDComm trust-ping concepts, queues | lifecycle states; Pulse + witness model; sleep-aware sessions; retirement/estate |
| L5 | Volition | What may it do without a human? | **OAuth RAR / GNAP**, Biscuit/UCAN carriers | Autonomy Envelope; pulse-gated suspension; AL-0..5 |
| L6 | Society | How does it deal with others? | **MCP, A2A, AP2/x402**, Noise AKE | MEET semantics; Interaction Charters/Contracts; trust states; era-stamped reputation; CONVEY (EPP-modeled) |
| L7 | Accountability | How do humans answer for it? | **OTel GenAI + RFC 3161/SCITT**, AI-Act duties | Flight Recorder profile; override verbs; Human Escalation Guarantee; crosswalk; evidence bundles |

ALIVE = condensed 5-layer profile (top-down: Accountability, Liaison, Intent, Vitality, Essence = L1–L3). Autonomy levels: AL-0 tool → AL-1 session → AL-2 supervised persistent → AL-3 bounded autonomous → AL-4 delegating → AL-5 self-governing fleet (defined, NOT certifiable). Registration logs are an **IETF SCITT Transparency Service profile** anchored to ≥2 open chains, with a self-anchoring escape hatch.

## 4. Mechanisms — current (v0.3.1) state

**Agent Passport + Genesis (L2).** A W3C VC 2.0 profile: agent DID; principal with labeled **proof class** (self-asserted / domain / org / gov — org/gov map to eIDAS 2.0 QEAA; proof-class assertions carry a Bitstring Status List reference checked at PROVE); lineage; **constitution hash** (a public policy *commitment*, not behavioral attestation); AL level; a presence *contact point* (public schedules were REMOVED in v0.3 — published quiet hours leaked the principal's sleep pattern; schedules negotiate bilaterally at PULSE); substrate-attestation class (TEE quote where available — SHOULD, not MUST); revocation endpoint. Genesis is witnessed in transparency logs at creation; age is unforgeable. No orphan agents; no self-ownership.

**Autonomy Envelope (L5).** Signed, attenuable mandate carried as an OAuth RAR object (Biscuit/UCAN binary/JSON carriers); scopes from the closed algebra in §9A. **Pulse-gated suspension** ("autonomy decay"): validity conditioned on heartbeats via named witnesses; hard-fail for money/PII scopes, soft-fail elsewhere; suspension is prospective-only, BUT (v0.3, closes a TOCTOU hole) a principal's explicit **FORCE_HALT revocation** is a distinct, immediately-effective act that DOES reach in-flight actions, and multi-stage commitments MUST re-verify trust state at each settlement **phase-gate**. Witness hardening: attestations bound to recent log checkpoints; witnesses selected verifiably at random from the pool; a witness must issue a challenge and see it unanswered before publishing non-liveness; suspension needs misses at ≥2 independent witnesses. **Budgets need an enforcement locus**: without a named spend authorizer (authorization-ONLY — it must never custody funds, else MSB/PSD licensing triggers) or rail-side caps, a budget is disclosure of intent, not a bound; authorizers issue pre-allocated sub-budget vouchers so fleets survive authorizer outages.

**Pulse (L4).** Signed heartbeat chained to the recorder head; proves **continuity of key custody and operational responsibility**, not "life"; its power is what absence triggers. Key rotation emits a `KeyRotationEvent` dual-signed by old+new keys before the new era's first pulse. Lifecycle: conceived → active ⇄ dormant → retired → archived; restart = nap; retirement revokes all, archives the recorder, disposes memory by consent class.

**MEET (L6).** HAIL → PROVE (challenge; revocation + registration + proof-class status checks; resolves a trust state) → **CHARTER, two-stage (v0.3)**: commitments and predicate proofs first ("my limit covers this transaction"), full Interaction-Charter disclosure deferred into the signed, dual-logged BIND Interaction Contract — because plaintext ceilings are attacker reconnaissance, while disclosure itself is a *legal shield* (actual notice of express authority limits defeats apparent-authority claims against the principal) → TUNE (transports; Noise-framework AKE for the wire) → BIND (contract incl. the Human Escalation Guarantee clause and a delegation-warranty claim; countersigned turn sequencing — an uncountersigned state transition is invalid) → PULSE (presence contract; store-and-forward uses epoch-bounded challenges with replay caches and aborts if passport/envelope mutated during dormancy).

**Trust states (L6).** VERIFIED (registration proven via ≥2 SCITT-log inclusions or a *finalized* self-anchor — unfinalized anchors resolve to UNVERIFIED_PENDING_FINALITY) / DEGRADED / UNVERIFIED / REVOKED. Mixed-delegation taint = a **liability rule, not a detector** (hidden internal delegation is unobservable; concealment forfeits standing). Ratchet horizon honest: 8–15 years, scope-by-scope; near-term engines are SDKs/marketplaces/procurement, insurers eventual.

**Ownership & CONVEY (L6/L7).** Principal (accountability) / Title Holder (property) / Custodian (runs the substrate). Transfer modeled on EPP (RFC 5730) states; at transfer: all envelopes auto-revoke, keys rotate, memory gets a provenance-verified **sanitization pass** (anti-Trojan-sale), the agent survives. Clones get fresh Genesis and zero tenure. **Era-stamped receipts**: an era = a **runtime-environment digest** (weights manifest + system-prompt digest + decoding params + constitution hash — not a bare model tag); tenure is receipts-weighted (counterparty standing, EigenTrust-style ring discounting), pulses alone prove only registration continuity.

**Registration (L2/L7).** SCITT-profiled append-only logs, Merkle-anchored to ≥2 unrelated open chains; principal references are **salted blinded commitments** (≥128-bit salt off-log) — plain hashes of personal identifiers are NOT GDPR-safe (CJEU *Breyer*); erasure = salt destruction. Self-anchoring is first-class registration. Known limit: operationally orphaned until a forcing function exists; candidate economics in §6.5.

**Flight Recorder (L7).** OTel-GenAI-formatted entries, hash-chained, RFC 3161/SCITT-sealed checkpoint heads (evidence-grade posture: business-records exception, eIDAS integrity presumption). Honest limit: tamper-evidence ≠ completeness — it records the agent's *admissions*; bilateral events are dual-entry via BIND.

**Micro-Core (adoption wedge #1).** See §9B — a one-page profile with single-player utility.

## 5. History lessons already internalized

FIPA had real implementations (JADE) and died of **no demand** — so every LAP mechanism must be adoptable piecemeal by a single operator with value before any ecosystem exists. The semantic layer is the graveyard (FIPA ontologies, Semantic Web) — hence the deliberately tiny closed scope algebra. UDDI, P3P, DTP, Solid, and the SSI/DIDComm/ToIP stack are demand-failure precedents, not templates. OSI's own protocols lost; the map survived — LAP expects concept-absorption and optimizes for attribution.

## 6. Open problems (§22 of the spec) — current state

1. **Scope algebra**: candidate design now EXISTS (§9A) — attack it rather than re-stating the problem. Open within it: verb registry contents, `epoch_total` window semantics, versioning governance.
2. **Principal proofing**: eIDAS 2.0 QEAA mapping adopted for EU org/gov classes; consumer-scale and non-EU proofing still open.
3. **Key custody & recovery**: directions adopted (multisig/social recovery SHOULD; time-locked root mutations in the log); consumer custody UX still open.
4. **Certification limits**: covert continuous auditing direction; certification certifies wire conformance, never behavioral safety.
5. **Witness/log economics**: candidate model — enterprise escrow retainers paying per-attestation micro-fees; x402-micro-paid verification queries. Unproven.
6. **Recorder completeness / attested delegation**: open (needs execution attestation beyond current hosted-model practice).
7. **CONVEY atomicity**: EPP-state modeling adopted; era/epoch grace-window engineering and in-flight-contract rules still open.

## 7. ALREADY FILED — zero credit for resubmitting any of this

Round 1–2 (Claude): no present buyer/pre-market timing; FIPA misdiagnosis (fixed); OSI-analogy absorption; certification circularity; insurance-lane incumbency (AIUC); extension-not-new-model argument; PMIF/APMF "ports the diary, not the mind"; pulses cheap to fake; principal-binding issuer gap; key custody absent; budget double-spend; taint undetectable; CONVEY atomicity; tenure purchasable via transfer; CHARTER reconnaissance; vocabulary-is-not-a-moat; lone-founder/consortium unviability; ATL operational orphanhood; self-anchor-vs-VERIFIED contradiction (fixed); portability-vs-tenure contradiction (fixed via era-stamps); scope-fence self-violation (fence now ceremony-gated).

Round 3 (Gemini batch, all MERGED in v0.3): prospective-suspension TOCTOU → FORCE_HALT + phase-gates; two-stage CHARTER with ZK direction; public presence schedule privacy leak (removed); witness sybil/replay hardening; era = runtime-environment digest; self-anchor finality rule; store-and-forward replay rules; delegation-warranty claim; Bitstring proof-class revocation; countersigned turn sequencing; KeyRotationEvent; principal-key multisig + time-locks; receipt-ring graph discounting; M-of-N chain diversity; authorizer vouchers; CONVEY memory sanitization; the SCITT/VC2.0/RAR-GNAP/Biscuit-UCAN/Noise/OTel/EPP/Aries profiling program; GDPR salted-commitment fix; EU-AI-Act deployer-article mapping; CHARTER-as-legal-shield; eIDAS QEAA mapping; authorization-only spend authorizers; habeas humanum → normative "Human Escalation Guarantee"; terminology normalization; code-first sequencing; numeric pull/kill gates; Micro-Core wedge; evidence-bundling fence amendment; witness-economics model.

## 8. What round 2 wants from you

In priority order: (1) **attack the v0.3 fixes themselves** — new race conditions, contradictions, or bypasses introduced by FORCE_HALT/phase-gates/two-stage CHARTER/finality rules/era digests; (2) **attack the concrete designs in §9** — the scope algebra and Micro-Core are now real text with real bugs; (3) find what three prior review rounds missed entirely; (4) real prior art still missing. Be adversarial; flattery is a failure mode; ground claims in this pack; name only prior art you are confident exists (citations are verified; invented ones are discarded and noted). Do NOT modify any existing files if you have file access — deliver your review as a NEW file in `inbox/` per README.

## 9. Draft designs under review — attack these

### 9A. LAP-Core Scope Algebra v0 (LIP-3 draft, condensed)

Scope object: `{"v":"lap-scope-v0","act":"finance:pay","res":"ap2://rails/stripe/invoices/**","cap":{"max_per_tx":2000,"max_cumulative":10000,"unit":"USD","window":"utc_day"},"cp":{"allow":["did:web:vendorA.com"],"deny":[]},"depth":2,"decay_max_sec":300}`.
Rules: closed verb namespaces (`data|finance|compute|comm|identity|governance`, additions by LIP only); resource paths **segment-tokenized** (`*` = exactly one segment; `**` terminal only; `finance_admin` is NOT a child of `finance`); caps require identical `unit` across attenuation (ISO 4217/CAIP-19; cross-currency = reject at parse); windows are UTC epoch-aligned buckets only (`tx ⊑ utc_hour ⊑ utc_day ⊑ epoch_total`; rolling windows prohibited in client-verifiable envelopes); counterparties = explicit allow/deny sets, no patterns; `c.depth ≤ p.depth − 1`; `c.decay_max_sec ≤ p.decay_max_sec`; child witness quorum ≥ parent's; canonical serialization RFC 8785 JCS or deterministic CBOR; unknown `v` → reject (`UNSUPPORTED_ALGEBRA_VERSION`). Subset relation: every child scope must be ⊑ some parent scope across version/action/resource/caps/counterparties/depth/decay. Known limits (already filed): bucket-boundary burst (~2× cap straddling midnight — mitigate with `max_per_tx`); no cross-resource conditionals (deliberate); expressivity ceiling is a feature.

### 9B. LAP Micro-Core (one-page adoption profile, condensed)

Every request carries an `LAP-Passport` header (VC 2.0/JWT): `{iss: principal DID, sub: agent key, lap: {v, proof_class, constitution_hash, envelope: {act[], res, cap{max_per_tx, unit, window:"tx"}, expires_at}}}`. Receiver MUST: (1) verify JWT signature against sub + iss DID doc; (2) check `expires_at`; (3) check act/res match the invocation; (4) if cap present, check amount ≤ max_per_tx. Response carries `LAP-Receipt: sha256(request):sha256(response):sig_server`; both parties append the tripartite entry to local append-only logs. Single-player utility: works agent→tool-server with no counterparty adoption; upgrade path to full MEET when both sides speak LAP.

---

*Deliver via RESPONSE-TEMPLATE.md. Name your model honestly. Findings that repeat §7 score zero.*
