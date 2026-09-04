# Living Agents Protocol (LAP)

**Identity, authority, and lifecycle for always-on ("living") AI agents — an open reference model and research agenda.**

*Founding document — draft v0.4.6, 2026-08-30 (full revision history in §23; renamed from AEON to the Living Agents Protocol on 2026-08-28 by author decision; reconstructed 2026-08-29 after external-tool file corruption — see IMPROVEMENTS-LOG incident notes). Author: Athar Nouman (with Claude; external review contributions from Gemini). License intent: CC-BY-4.0 (spec text), Apache-2.0 (code).*

---

## 1. The idea in one page

OSI standardized how **machines talk** (ISO 7498, 1984). TCP/IP standardized how **networks route**. TLS and PKI standardized how **strangers trust**. HTTP standardized how **documents link**. In 2024–2026, MCP standardized how **agents reach tools**, and A2A standardized how **agents exchange tasks**.

Nothing standardizes how agents **exist**.

A "living" agent — always-on, persistent, acting while its human sleeps — is not a request/response endpoint. It is an entity with a lifecycle. It has an identity that must survive restarts, memory that must survive vendor changes, authority that must be bounded while unsupervised, a pulse that proves it is alive and well, relationships and commitments to other agents, and a human who must ultimately answer for it. Every one of those is unstandardized today. Every one of them is a prerequisite for the agent economy everyone is predicting.

**LAP is the existence stack.** It is three things:

1. **LAP-7** — a seven-layer reference model (the OSI homage) that gives every existing protocol its place and names the missing layers.
2. **ALIVE** — a five-layer implementer's profile (the TCP/IP analog) plus a certification program blueprint: *ALIVE Certified, Autonomy Level 0–5*.
3. **The Living Agents Alliance** — an open institutional design (Apache/CC licensed, RFC-style process) held in reserve until adoption earns it.

The analogy to OSI is exact in one more way: OSI did not replace Ethernet or invent TCP — it gave them coordinates. LAP does not compete with MCP, A2A, or AP2 — it slots them into Layer 6 and standardizes the six layers of *being* underneath and the layer of *answering* above.

---

## 2. Why now — the rhyme of history

| Year | Layer solved | Standard | What it unlocked |
|---|---|---|---|
| 1974 | Packets move | TCP/IP | Networks |
| 1983 | Names resolve | DNS | A usable network |
| 1984 | A shared map | OSI 7-layer | An industry that could talk about itself |
| 1994–95 | Strangers trust | SSL/TLS + PKI | E-commerce |
| 2007 | Delegated authority | OAuth | The API economy |
| 2024 | Agents reach tools | MCP | The tool ecosystem |
| 2025 | Agents exchange tasks | A2A / ACP | Multi-agent workflows |
| 2025 | Agents pay | AP2, x402 | Agent commerce (beginning) |
| **2026 → ?** | **Agents exist, persist, and are trusted** | **— nothing —** | **The agent economy proper** |

The trust-and-existence layer always arrives *after* the communication layer and *immediately before* the economic explosion. TLS was the 1994 moment for the web. This is the 1994 moment for agents.

Three forces make the window now:

- **Technical**: MCP/A2A/AP2 shipped; agents now have hands, mouths, and wallets — but no birth certificate, no leash, no black box, and no estate plan.
- **Regulatory**: the EU AI Act's logging and post-market-monitoring duties, NIST AI RMF, and ISO/IEC 42001 all demand exactly the artifacts LAP standardizes — but none of them define a *wire format*.
- **Economic**: enterprises will not deploy unsupervised 24/7 agents they cannot insure; insurers will not underwrite what they cannot audit; auditors need a format. The flight-recorder format *is* the insurability of the agent economy.

---

## 3. Landscape and the white space

What already exists (embrace, don't compete):

| Concern | Existing work | Status |
|---|---|---|
| Agent ↔ tools/context | **MCP** (Anthropic, 2024) | De-facto standard, industry-wide adoption |
| Agent ↔ agent tasks | **A2A** (Google → Linux Foundation, 2025), ACP (IBM/BeeAI) | Growing; Agent Cards ≈ proto-passports |
| Agent payments | **AP2** (mandates), **x402** (HTTP 402), Agentic Commerce Protocol | Early |
| Decentralized agent identity | **ANP** (DID-based), ERC-8004, MIT NANDA registry | Fragmented, no dominant design |
| Workload identity | SPIFFE/SPIRE, mTLS, TEE attestation | Solid, but not agent-shaped (no principal binding, no lineage) |
| Bot authentication on the web | IETF Web Bot Auth drafts (HTTP message signatures) | Early, browser/CDN-driven |
| Agent security threats | OWASP Agentic Security Initiative, CSA MAESTRO | Threat lists, not protocols |
| Governance frameworks | EU AI Act, NIST AI RMF, ISO/IEC 42001, IEEE 7000-series | Obligations, not wire formats |
| Observability | OpenTelemetry GenAI semantic conventions | Traces, not accountable records |
| Academic heritage | KQML (1990s), FIPA-ACL (1996→IEEE 2005), Contract Net (1980) | Right questions, thirty years early; FIPA had real implementations (JADE ran for a decade) and died of **no demand** |

The white space — concerns with **no standard at all**:

1. **Persistent agent identity** with principal binding ("who does it act for?"), lineage ("who spawned it?"), and constitution attestation ("what policy does it run?").
2. **Presence and lifecycle** — is the agent alive *right now*; sleeping; incapacitated; retired? No heartbeat, no lifecycle states, no store-and-forward norm for agents that sleep in different time zones.
3. **Autonomy envelopes** — a machine-readable, signed, *attenuable* statement of what an agent may do unsupervised: budgets, scopes, counterparty classes, quiet hours, escalation tree.
4. **Portable memory** — no interchange format for an agent's episodic/semantic/procedural memory. Memory is 100% vendor-locked today.
5. **Delegation chains** — A hires B, B spawns C; nobody can audit the chain of mandate or prove C's authority ⊆ B's ⊆ A's.
6. **The handshake** — when two persistent agents meet as strangers, there is no standard ceremony for mutual verification, envelope disclosure, and commitment.
7. **The flight recorder** — no tamper-evident, privacy-tiered, replayable record format that an insurer, court, or regulator can consume.
8. **Death** — no standard for retirement, revocation, archival, and memory bequest. Agents that never legally die accumulate zombie authority forever.

Items 1–8 are LAP's scope (amended by ceremony: + LAP Post conditionally, §20; + evidence bundling, §24.8). Nothing else is.

---

## 4. The LAP-7 Reference Model

Seven layers, bottom-up. Each answers one question, exposes artifacts to the layer above, and slots existing tech rather than reinventing it. Security is not a layer; it is a per-layer conformance requirement (as in OSI).

### L1 — Substrate  *(Where does it run?)*
- **Scope**: runtime, isolation, resource metering, checkpoint/restore, migration.
- **Slots in**: OCI containers, microVMs, WASM/WASI, Kubernetes, TEEs.
- **LAP defines**: the *Agent Runtime Profile* (token spend and wall-clock as first-class metered resources alongside CPU/RAM) and the *Snapshot format* — a checkpoint of state + memory refs + key custody so an agent can migrate hosts **without dying**. Continuity of existence is a Layer-1 property.

### L2 — Identity  *(Who is it, provably?)*
- **Scope**: cryptographic identity, principal binding, lineage, attestation, revocation.
- **Slots in**: W3C DIDs/VCs, SPIFFE, x.509, TPM/TEE attestation; optional decentralized profiles (ANP, ERC-8004).
- **LAP defines**: the **Agent Passport** — a signed document carrying: agent ID (DID), *principal* (the human/org it acts for, with proof), *lineage* (spawner, generation), *constitution hash* (digest of its governing policy/system charter — honestly framed: a **public policy commitment**, not a behavioral attestation. It proves which rules were promised, enabling post-hoc review of logged actions against the charter's *mechanical* rules; fidelity to values-level language is only qualitatively reviewable — see Open Problems §22.4), model attestation where available, declared Autonomy Level, capability summary, a presence *contact point* (v0.3 privacy fix: public schedules were removed from the passport — published quiet hours revealed the principal's sleep and travel patterns; schedules are now negotiated bilaterally at the PULSE step), revocation endpoint. **The "no orphan agents" rule**: every passport must resolve to a responsible legal person or organization.

### L3 — Memory  *(What does it remember, and whose is it?)*
- **Scope**: durable memory, provenance, consent, portability, forgetting.
- **Slots in**: vector stores, memory vendors (Mem0/Zep/Letta-class), GDPR portability rights.
- **LAP defines**: **APMF — Agent Portable Memory Format**. Typed memories (episodic / semantic / procedural / relational), each with provenance (source, consent class, retention clock). Export/import lets a principal move their agent's *mind* between models and vendors. **Forget-propagation**: a deletion request cascades through every delegation chain the memory traveled. Ownership rule: memory belongs to the **principal**, never the platform.

### L4 — Vitality  *(Is it alive right now, and where in its life is it?)*  ⟵ the signature layer
- **Scope**: lifecycle states, presence, heartbeats, sessions that survive restarts, incapacity, death.
- **Slots in**: health-check conventions, message queues, XMPP-style presence concepts.
- **LAP defines**:
  - **Lifecycle**: `conceived → active ⇄ dormant → incapacitated? → retired → archived`.
  - **Pulse**: periodic signed heartbeats carrying status: `active | dozing | hibernating | degraded | incapacitated`. Honest semantics: a pulse proves **continuity of key custody and operational responsibility** — that the signing authority is present and answering — not inner "life"; status fields are self-reported. Its power lies in what its *absence* triggers (autonomy decay), not in what its presence proves.
  - **Store-and-forward** with wake priorities, so agents in different "time zones of existence" converse across sleep.
  - **Session continuity**: resumption tokens bound to the *passport*, not the process — a restart is a nap, not a death.
  - **Estate protocol**: retirement revokes credentials, archives the flight recorder, and executes a *memory bequest* (which memories pass to a successor agent, which are destroyed). No zombie authority.

### L5 — Volition  *(What may it do without a human?)*
- **Scope**: mandates, budgets, autonomy levels, escalation, kill switches.
- **Slots in**: OAuth 2.x / GNAP, AP2 mandates, macaroon/biscuit-style attenuable tokens, policy engines (Cedar/OPA).
- **LAP defines**:
  - The **Autonomy Envelope** — a signed, machine-readable mandate: action scopes, budgets (money / tokens / hours), rate limits, permitted counterparty classes, time windows and quiet hours, jurisdictions, escalation tree, expiry. Envelopes are **attenuable**: a delegated child envelope is provably a restriction of its parent (within the closed algebra of LIP-3). Renewal is a deliberate human ceremony — mandates rot unless re-blessed.
  - **Autonomy Levels AL-0…AL-5** (SAE-style, see §7).
  - **Autonomy decay**: an envelope's validity is *conditioned on Layer-4 pulses* — an agent that goes dark loses its powers by protocol, not by cleanup script. Web PKI learned that hard-fail revocation turns infrastructure blips into outages, so decay is specified with engineering care, not slogan: (a) an explicit **observer model** — pulses are delivered to named witness endpoints (the principal's, plus optional independent liveness monitors) whose signed last-seen attestations are what counterparties consult; (b) **fail postures per scope class** — hard-fail (suspend on miss) for money-movement and PII scopes, soft-fail with staleness labels for low-stakes scopes; (c) **prospective-only suspension** — in-flight actions begun under a valid envelope run to completion or rollback per their interaction contract, and re-validation after an outage is automatic on pulse resumption (the human re-blessing ceremony is for *expiry*, never for blips); (d) **anti-DoS quorum** — since jamming a competitor's pulse path would convert an availability attack into an authority attack, suspension requires misses across ≥2 independent witnesses; (e) **revocation ≠ suspension (v0.3, closes a TOCTOU hole)** — prospective-only grace applies to *passive* suspension from missed pulses; a principal's *explicit emergency revocation* (`FORCE_HALT`) is a distinct, signed, immediately-effective act that DOES reach in-flight actions — otherwise a compromised agent could launch a long-running settlement and then go dark behind the grace rule. v0.4 refinement (closes the mirror-image abuse — buyer exit-scams via halt): **halt stops authority, never debts.** Phase-gates split into two classes: *action gates* (new PII release, new execution stages) MUST halt on FORCE_HALT; *settlement gates* (paying for milestones already rendered and attested in countersigned BIND turns) MUST execute against pre-locked escrow even after a halt — revocation is not repudiation; (f) **phase-gates** — multi-stage commitments MUST re-verify the counterparty's trust state and pulse continuity before each settlement phase, not only at BIND; (g) **witness hardening** — witness attestations MUST be bound to a recent transparency-log checkpoint (replay resistance), witnesses SHOULD be selected verifiably at random from the registered pool rather than agent-pinned (collusion resistance), and a witness MUST issue a signed challenge to the agent and see it unanswered before publishing a non-liveness attestation. Normative terminology: the mechanism's formal name is **pulse-gated suspension**; "autonomy decay" remains the concept's informal name.

### L6 — Society  *(How does it deal with others?)*
- **Scope**: discovery, the handshake, interaction contracts, delegation, negotiation, reputation, payments bindings.
- **Slots in**: **MCP** (tool use), **A2A/ACP** (tasking), **AP2/x402** (payment), Contract-Net heritage.
- **LAP defines**: **MEET** — the Living Agent Handshake (§6); **Interaction Contracts** — small signed agreements per relationship: purpose, data-handling terms, retention, logging obligations, dispute pointer; both sides log them; **delegation chains** — envelope attenuation across agent "org charts", with depth limits and full auditability; **portable reputation** — counterparty-signed completion receipts, so reputation is evidence you carry, not a score a platform owns.

### L7 — Accountability  *(How do humans see, steer, and answer for it?)*
- **Scope**: audit, override, escalation to humans, compliance, incidents, insurance.
- **Slots in**: OpenTelemetry GenAI, EU AI Act logging duties, NIST AI RMF, ISO/IEC 42001, incident databases.
- **LAP defines**: the **Flight Recorder** — hash-chained, tamper-evident, privacy-tiered event log with a replay schema; the **Human Escalation Guarantee** (informally "habeas humanum") — the standing right of any counterparty to demand, and reach within a bounded time, the responsible human behind an agent; **override norms** — standardized stop/pause/constrain verbs every conformant agent must honor; **compliance crosswalk** — maintained mappings from LAP artifacts to EU AI Act articles, NIST AI RMF functions, ISO 42001 controls; **LAP-IR** — incident reporting format.

**The Layer-8 joke, retired.** Network engineers joke that OSI's real eighth layer is "people and politics." LAP's answer is that humans are not a joke above the stack — Accountability *is* the top layer. The stack is not finished until it terminates in a responsible human.

---

## 5. ALIVE — the five-layer profile

LAP-7 is the reference model for standards work. **ALIVE** is the condensed implementer's profile — the TCP/IP to LAP's OSI. Read top-down, the stack spells its own name:

| | Profile layer | Absorbs LAP-7 | One-line duty |
|---|---|---|---|
| **A** | **Accountability** | L7 | A human answers. |
| **L** | **Liaison** | L6 | Strangers can meet, verify, and commit. |
| **I** | **Intent** | L5 (Volition) | Authority is explicit, bounded, and decays. |
| **V** | **Vitality** | L4 | Aliveness is proven, sleep is normal, death is clean. |
| **E** | **Essence** | L1–L3 | One being: a body (substrate), a self (identity), a past (memory). |

*Every certified agent is, literally, ALIVE: it has an Essence, a Vitality, an Intent, a Liaison, and an Accountability.*

---

## 6. MEET — the Living Agent Handshake

What happens when two persistent agents encounter each other as strangers. Six steps; steps 3, 5, and 6 exist in no current protocol and are the core novelty. (Full state machine: LIP-2.)

1. **HAIL — discovery.** Exchange Agent Passports. (A2A Agent Cards satisfy the capability portion; the passport adds principal, lineage, constitution hash, autonomy level.)
2. **PROVE — mutual verification.** Cryptographic challenge–response; revocation and registration checks; principal-binding verification; signed-tree-head gossip against split-view registries. *"Who do you act for?"* answered with proof, not a string.
3. **CHARTER — envelope disclosure (normative name: the Interaction Charter).** Each side reveals the *relevant slice* of its Autonomy Envelope: "I may spend up to $50/day with class-B counterparties; I cannot sign contracts." Strangers learn each other's limits before transacting. Two v0.3 refinements: (a) **disclosure is a legal shield** — under agency doctrine (Restatement (Third) of Agency §§2.03/3.03 and civil-law analogues), a disclosed envelope puts the counterparty on *actual notice* of the agent's express authority limits, defeating later apparent-authority claims against the principal; (b) **but plaintext ceilings are attacker reconnaissance**, so CHARTER is split: commitments and predicate proofs first ("my limit covers this transaction" — backed by authorizer-signed Reservation Tickets, LIP-2 §7), with full slice disclosure deferred into the signed, dual-logged BIND contract.
4. **TUNE — capability & protocol negotiation.** Agree transports and vocabularies (A2A for tasking, MCP resources, AP2/x402 if payment is in scope) — ALPN for agents.
5. **BIND — interaction contract.** Sign the small contract: purpose, data-handling, retention, logging obligations, the Human Escalation Guarantee clause, dispute pointer. Both flight recorders log it. Relations between agents become *evidence*, not vibes.
6. **PULSE — presence contract.** Agree heartbeat cadence and witnesses, store-and-forward behavior for sleep, and session-resumption keys bound to passports. The relationship survives restarts and sleeps by design.

Teardown mirrors setup: a signed receipt of what was done, which feeds portable reputation (L6) and both recorders (L7).

---

## 7. Autonomy Levels (AL-0 … AL-5)

SAE gave self-driving its shared vocabulary (J3016). Agents need the same. The level is declared in the passport, bounded by the envelope, and printed on the certification.

| Level | Name | Meaning |
|---|---|---|
| **AL-0** | Tool | Runs only when directly invoked. No persistence. |
| **AL-1** | Session agent | Multi-step autonomy within a session; nothing survives the session. |
| **AL-2** | Supervised persistent | Persists, schedules its own wake-ups; every outward action requires human approval. |
| **AL-3** | Bounded autonomous | Acts unsupervised **inside** a signed envelope (budgets, scopes, hours); escalates outside it. The 24/7 workhorse. |
| **AL-4** | Delegating autonomous | May spawn/hire sub-agents and attenuate mandates down the chain; full chain-of-mandate audit. |
| **AL-5** | Self-governing fleet | Long-horizon goals, self-modified workflows, fleet-level self-management. **Defined but not certifiable** — the standard reserves the level and states, publicly, what evidence bar would have to be met. |

---

## 8. Core wire artifacts

Six small documents make the whole model concrete. Sketches (illustrative; normative schemas live in the LIPs):

**Agent Passport (L2)** — see LIP-1 for the normative VC 2.0 profile.

**Autonomy Envelope (L5)** — signed by the principal; attenuable
```json
{
  "kind": "envelope",
  "subject": "did:lap:z6Mk…9fR",
  "issuer": "did:lap:principal…",
  "scopes": ["email:draft", "calendar:write", "purchase:approve<=USD50/day"],
  "budgets": { "usd_daily": 50, "tokens_daily": 2000000, "wall_hours_daily": 20 },
  "counterparties": ["class-A", "class-B"],
  "quiet_hours": "22:00-06:00Z",
  "escalation": ["mailto:oncall@example.com"],
  "valid": { "from": "2026-08-28", "until": "2026-09-28", "requires_pulse_within": "PT2H" },
  "attenuation": { "parent": null, "max_delegation_depth": 2 },
  "sig": "…"
}
```
`requires_pulse_within` is the autonomy-decay clause: no heartbeat for 2 hours (per the §4 L5 observer model) ⇒ envelope suspends prospectively.

**Budgets need an enforcement locus.** A signed envelope is a capability token, but a daily budget is mutable state — presented naively to ten counterparties at once, `usd_daily: 50` authorizes $500. Conformant deployments MUST bind budget scopes to a named **spend authorizer** — the principal's authorization endpoint consulted per transaction, or rail-side caps enforced via AP2/x402 mandates. A budget without a declared authorizer is *disclosure of intent*, and counterparties MUST treat it as such: it allocates liability, it does not bound spending.

**Pulse (L4)** — signed heartbeat: `{status, load, budgets_remaining, next_wake, recorder_head_hash}`. The recorder head hash chains liveness to auditability: you cannot claim to be alive while hiding your log.

**APMF record (L3)** — `{type: episodic|semantic|procedural|relational, content, provenance:{source, consent_class, acquired_at}, retention: P90D, forget_chain: [dids…]}`.

**Interaction Contract (L6)** — `{parties, purpose, data_terms, retention, logging_duties, escalation_clause, dispute_uri, receipts:[…]}`.

**Flight Recorder entry (L7)** — `{seq, ts, actor, act, envelope_ref, io_digest, prev_hash, hash}` with privacy tiers (public digest / principal-readable / regulator-unlockable).

---

## 9. Compliance — the program blueprint

"Compliance" is the word that turns a spec into an economy. Three tiers, modeled on what worked (CNCF-style conformance), not on paper standards:

1. **LAP Ready** *(self-assessed)* — run the open conformance suite locally, publish the report, wear the badge.
2. **ALIVE Certified, AL-n** *(suite-verified)* — the open-source conformance harness (`lap-conformance`) probes a live agent endpoint: identity challenge, envelope disclosure, pulse behavior, quiet-hours honor, kill-switch obedience, log-chain integrity, forget-propagation.
3. **ALIVE Audited** *(third-party)* — for AL-3+ in regulated domains: an auditor reviews the flight recorder against the envelope's mechanical rules and the charter's reviewable commitments (what certification can and cannot establish is stated honestly in §22.4). Shaped to slot into EU AI Act conformity assessment and SOC 2-style attestations via the crosswalk (§4 L7).

*Status (v0.2): all certification and audit operations are **deferred** until external implementations exist (§11). The tiers are a blueprint, not a live program.*

Supporting institutions (same deferred status): a **public registry** (passports + revocation lists), **LAP-IR** incident reporting, and a published trademark policy.

---

## 10. The Living Agents Alliance — consortium design (blueprint in reserve)

*Status (v0.2): deferred institutional design — activated only after ≥2 external parties implement LAP mechanisms unprompted. Until then LAP operates as a byline, not a body (§11).*

- **Legal shape**: start as an open GitHub organization with a lightweight fiscal host; donate to a neutral foundation (Linux Foundation or Eclipse are the proven homes) once ≥3 independent implementations exist. Neutrality is the product.
- **Process**: **LIPs** (LAP Improvement Proposals), RFC-style, semver'd specs, public mailing list, recorded calls. Spec text CC-BY-4.0; reference code Apache-2.0 with patent non-assert.
- **Working groups**: Essence (L1–L3), Vitality & Volition (L4–L5), Society (L6), Accountability (L7), plus Conformance and Crosswalk.
- **Liaisons, not rivalries**: MCP steering, A2A project (LF), W3C AI Agent Community Group, IETF, OWASP Agentic Security, OASIS, IEEE. LAP's public posture is *"we are the map, they are the roads."*

---

## 11. Adoption strategy — publish, then infiltrate (revised in v0.2)

Standards win by adoption, not elegance — and lone-founder standards win only when they carry single-player utility or ride existing distribution. The original consortium-first plan failed both tests under adversarial review (LAP-critical-review.md). Revised strategy: **LAP is a byline, not a body.** The reference model and mechanisms are published under the author's name and filed into venues that already have distribution; institutional apparatus is deferred until it is earned.

- **The flagship artifact is a position paper, not a consortium**: the reference model, mechanisms, honest open problems (§22), and corrected related-work history — on arXiv and the open web.
- **The essay, for distribution**: *"Agents need a birth certificate, a leash, a black box, and an estate plan."*
- **The killer demo**: two strangers' agents, overnight, across time zones — MEET, prove principals, disclose envelopes, transact under budget while both humans sleep; each human replays the signed flight-recorder trail in the morning. Built and running (lap-demo/); to be filmed.
- **File the mechanisms where distribution already lives**: Autonomy Envelope + decay → proposed **A2A extension**; lifecycle, Pulse, presence → **W3C AI Agent Protocol Community Group**; LAP Floor, trust states, compliance crosswalk → **OWASP agentic-security** orbit; flight-recorder format toward insurer-native efforts as a partner track; principal binding, lineage, era-stamped receipts → companion commentary to **ERC-8004** and AGNTCY identity work; watching the new **ITU** agent-trust focus group and **NIST** AI Agent Standards Initiative.
- **The one product bet**: LAP Post — store-and-forward for sleeping agents.
- **Deferred until ≥2 external parties implement unprompted**: legal entity, trademarks, certification operations, registries, liaison letters, "Alliance" branding (§10 held in reserve).
- **Sequencing (v0.4, code-first)**: SDK + Micro-Core + demo first; essay second; arXiv third; filings last. Effort concentration ~60% on the MCP/A2A middleware route. Numeric pull/kill gates at day 60: ≥3 external PRs or one mainstream-framework plugin accepted → double down; no venue response in 45 days → archive that track. **Signal quality rule (v0.4.6):** an implementation produced in response to the published conformance challenge is *solicited* and counts as a weaker signal than an *unsolicited* one; the gate records which is which, so the project never games its own metric.

---

## 12. Honest risk assessment

- **XKCD 927** ("now there are 15 competing standards"). Mitigation: LAP never offers a competing protocol at layers that have one; it is deliberately a *reference model + the missing layers only*. OSI's lasting win was the map, and nobody had to stop using Ethernet.
- **The FIPA lesson, corrected.** FIPA answered many of these questions in 1996 — and it did **not** die of "no implementation": JADE was real and ran for a decade. FIPA died because the stranger-agent economy it presupposed didn't arrive for twenty-five years. The mitigation is therefore *timing-hedged design*: every mechanism must be adoptable piecemeal by a single operator, with value before the ecosystem exists, and the whole effort must be survivable on a shoestring until demand arrives (publish-then-infiltrate, §11).
- **Big-vendor capture.** If platform vendors ship proprietary passports first, the window narrows. Counter: speed, genuine neutrality, timestamped priority (Bitcoin anchors), and attribution-optimized publishing.
- **Crowding.** 2025–26 is a gold rush (ANP, NANDA, ERC-8004, AGNTCY, enterprise agent-identity products). Nobody yet owns the *persistent/living* framing or the existence layers as a coherent whole.
- **Scope creep** is the native failure mode of layer models. The scope fence in §3 is normative and amendable **only by explicit, logged decision** — current fence: items 1–8 plus the conditional LAP Post reservation (§20) plus evidence bundling (§24.8). This draft amended its own fence within its first day; that is the failure mode demonstrating itself, and the reason the fence now requires ceremony.

---

## 13. Glossary of coined terms (round 1)

- **Living agent** — an always-on, persistent autonomous agent with identity, memory, and mandates that survive restarts.
- **Agent Passport** — signed identity + principal + lineage + constitution document (L2). (Used lowercase-generic in-spec; a same-named commercial product exists.)
- **Constitution hash** — committed digest of the agent's governing policy; logged actions are reviewable against its mechanical rules.
- **Autonomy Envelope** — signed, attenuable statement of unsupervised authority (L5).
- **Autonomy decay / pulse-gated suspension** — envelope validity conditioned on heartbeats; going dark suspends power.
- **Pulse** — signed heartbeat proving custody-and-responsibility continuity, chained to the audit log (L4).
- **MEET** — the six-step handshake: HAIL, PROVE, CHARTER, TUNE, BIND, PULSE (L6).
- **Flight Recorder** — tamper-evident, privacy-tiered, replayable event log (L7).
- **Human Escalation Guarantee** (informal: habeas humanum) — the enforceable-by-contract right to reach the human behind any agent.
- **No orphan agents** — every passport resolves to a responsible legal person.
- **Agent estate** — the retirement protocol: revocation, archive, memory bequest.
- **ALIVE** — Accountability, Liaison, Intent, Vitality, Essence — the five-layer profile and the certification mark.

---

## 14. Round-2 design decisions

### 14.1 Birth, age, and the span of a life → the **Genesis Record**
Age is a **trust primitive** (new domains are treated as risky; mass-spawned fresh identities are the sybil attack). **Genesis Record** (L2): a signed birth certificate — `created_at`, spawner, initial constitution hash — submitted to independent transparency logs *at creation*, so the timestamp is **witnessed, not self-asserted**. **Tenure** (L4/L6), honestly weighted (v0.2): unbroken pulse chains are cheap to fake (a key-holding cron job), so pulses establish only *continuity of registration*; the substance of tenure is **era-stamped counterparty receipts** — signed completions from distinct, themselves-tenured counterparties, weighted by the counterparty's own standing (a receipt-ring of sock puppets decays the weight of everyone in the ring). **Probationary autonomy** (L5): higher AL certification can require minimum verified tenure. Genesis → tenure → retirement → archive is one continuous, auditable arc.

### 14.2 Sustainable AI → the **Metabolic Report**
A 24/7 agent is a *continuous* consumer of compute and energy — living agents have a metabolism. The **Metabolic Report** extends the Pulse with `{tokens_24h, kwh_est_24h, idle_ratio}`; the certification blueprint may grade **efficiency classes**. Crosswalk hooks: EU AI Act energy documentation, CSRD/ESG. **Sleep is a sustainability feature** — dormancy states and autonomy decay mean idle agents wind down and dark agents lose power.

### 14.3 AI ethics → the **LAP Floor** plus charter fidelity
A protocol cannot make agents good; it can make their commitments **inspectable and their violations provable**. **The LAP Floor** — a deliberately small set of universal invariants every certified agent honors regardless of charter: the Human Escalation Guarantee; no orphan agents; honor override verbs; no impersonation; forget-propagation. Like the web's same-origin policy: not a moral philosophy, a minimum physics of coexistence. **Above the floor: pluralism** — each principal declares values and prohibitions in the agent's charter; audit means reviewing the flight recorder against the declared charter's mechanical rules.

### 14.4 Charter and founding principles → first-class artifacts at both levels
- **Per-agent**: the constitution hash is promoted to a structured **Charter** — purpose, values, prohibitions, escalation duties, and an *amendment process*. Every amendment produces a new hash and a transparency-log entry: **value drift is visible**.
- **The LAP Founding Principles**: 1. **Humans answer.** 2. **No orphan agents.** 3. **The mind belongs to the principal.** 4. **Authority is explicit, bounded, and decays.** 5. **Aliveness is proven; death is clean.** 6. **Evidence over vibes.** 7. **Registered to exist** — every certified agent is born in public, in logs no single party controls. 8. **The map, not the roads** — complement, never capture; rough consensus and running code; the spec is free forever.

### 14.5 Blockchain registration → **Agent Transparency Logs** (the requirement kept, the fragility removed)
The instinct — *no agent is standardized until registered in a public, ever-growing, tamper-evident registry* — is correct (Founding Principle 7). The risk is mandating **one blockchain**: a governance capture point; per-agent transactions cannot absorb millions of births/day; immutable personal data collides with GDPR; chains die or fork; crypto-mandatory standards ghettoize adoption. The proven pattern is **Certificate Transparency**, adopted as **Agent Transparency Logs (ATLs)** — an **IETF SCITT profile** (v0.3): Genesis Records, charter amendments, and revocations are SCITT Signed Statements in independent append-only logs; **certification requires inclusion proofs from ≥2 unrelated operators**. Only commitments enter the logs — and (v0.3 correction) plain hashes of personal identifiers are **not** GDPR-safe: under CJEU *Breyer* (C-582/14) a hash remains personal data while anyone holds the linkage. Principal references in public records MUST be **salted blinded commitments** (≥128-bit salt held off-log); GDPR Art. 17 erasure = destroying the salt. ATLs periodically **anchor their Merkle roots onto open permissionless chains** (the OpenTimestamps pattern) — chain-grade immutability without per-agent gas, chain lock-in, or PII on-chain. A chain-native profile (ERC-8004-compatible) is welcome as one conforming implementation.

---

## 15. Glossary additions (round 2)

**Genesis Record** — witnessed birth certificate. **Tenure** — receipts-weighted continuous history; sybil resistance lives in receipts, never pulses. **Probationary autonomy** — tenure-gated certification. **Metabolic Report** — per-pulse resource footprint. **LAP Floor** — universal invariants under charter pluralism. **Charter** — structured, amendable constitution with logged drift. **Agent Transparency Log (ATL)** — SCITT-profiled append-only log; ≥2 independent inclusion proofs for certification; roots anchored to open chains.

---

## 16. Trust States — the HTTPS ratchet

**Premise: like HTTPS, only registered, standardized, certified agents should be trustable.** The web proved the mechanism: the padlock conquered the web when *clients* began labeling the alternative.

### 16.1 Trust states (the padlock, specified)

The PROVE step of every MEET handshake resolves the counterparty to exactly one state:

| State | Meaning | Default posture |
|---|---|---|
| **VERIFIED** | Passport valid · **registration proven** (≥2 independent ATL inclusion proofs, *or* a valid finalized self-anchor per §19) · revocation clean · pulse fresh · declared AL certified | Proceed per envelope |
| **DEGRADED** | Valid identity but stale pulse, undisclosed envelope, or expired certification | Warn; restrict to low-stakes scopes |
| **UNVERIFIED** | No passport, or self-asserted only (the "self-signed certificate" of agents) | Interact only if the local envelope explicitly permits |
| **REVOKED / TAINTED** | Revoked passport, failed challenge, or tainted delegation chain | Refuse; log; report |

(`UNVERIFIED_PENDING_FINALITY`: a self-anchor awaiting chain finality — MAY be treated as DEGRADED-equivalent for non-money, non-PII scopes only.)

### 16.2 Mixed-delegation taint
A VERIFIED agent delegating to an UNVERIFIED sub-agent: **a delegation chain has the trust state of its weakest link**, with the delegation graph disclosed at CHARTER. Honesty about detection: hidden delegation (an uncertified oracle invoked as an internal tool call) is not externally observable, so this functions as a **liability rule, not a detector** — certified agents warrant their disclosed graph is complete (the BIND `delegation_warranty_claim`), and a hidden chain surfacing post-hoc forfeits certification and shifts liability to the concealing principal. Attested-execution profiles that could make call graphs provable are an open problem (§22.6).

### 16.3 Who plays the browser?
1. **MEET implementations** (SDKs, gateways, frameworks) — default-deny knobs shipped in code; the nearest-term lever.
2. **Marketplaces and registries** — listing requires VERIFIED, as app stores required signing.
3. **Enterprise policy engines** — envelope templates that forbid classes of unverified counterparties.
4. **Insurers** — the strongest *eventual* engine: *uncertified counterparty ⇒ uninsured interaction*. But insurance follows loss data by many years (cyber took two decades to gain teeth), and insurer-native standards already exist — a partner track, not the launch engine.
5. **Regulators last** — the crosswalk lets them *reference* trust states rather than invent them.

### 16.4 The ratchet schedule
Phase 1 (launch): permissive — UNVERIFIED allowed, always labeled. Phase 2: warn — SDKs require an explicit opt-in flag. Phase 3: default-deny for payments and PII scopes. Phase 4: default-deny generally, opt-outs logged. Honest clocks (v0.2): the web took ~20 years; insurance-led enforcement historically takes decades. The plausible near-term engines are contractual chokepoints, and a realistic full-ratchet horizon is **8–15 years, arriving scope-by-scope** (payments first).

---

## 17. Ownership, Title, and Transfer

Who owns an agent, and how ownership moves, turns living agents into an **asset class** — and is the piece most likely done dangerously wrong without a standard. Core distinction: **Principal** (accountability: whom it acts for, issues the root envelope) / **Title Holder** (property: the right to transfer, lease, retire) / **Custodian** (operates the substrate). Usually the same entity; the passport carries each where they diverge.

### 17.1 What transfers and what must not — the four-way split

| Component | On title transfer |
|---|---|
| Identity, Genesis Record, tenure | **Travels** — it is the same being; era boundaries visible |
| Title | **Transfers** — that is the event |
| Envelopes / mandates | **Never transfer — auto-revoked at transfer**; the new principal re-issues from scratch |
| Memory (APMF) | **Filtered by consent class** — memories owed to the old principal's relationships are destroyed or escrowed |
| Reputation receipts | **Carried with provenance** — counterparties see which principal-era earned them |
| Charter | Carries; new-owner amendments are logged *at* transfer |
| Clones | **Do not inherit tenure.** A copy gets a fresh Genesis, zero tenure, lineage visible |

The auto-revocation rule is the safety keystone: without it, buying an agent means buying the previous owner's bank permissions. The clone rule kills reputation farming: **tenure and reputation are soulbound to the individual identity** — transferable with title, never with duplication.

**Resolving portability vs. tenure (v0.2).** If APMF lets a principal move an agent's memory to a new model or vendor, is that a *migration* (tenure preserved — inviting reputation fraud by brain transplant) or a *clone* (tenure zeroed — making vendor exit cost the agent its reputation)? Resolution: **identity and tenure survive migration, but every receipt is era-stamped.** v0.3 tightening, v0.4 correction: an era is identified by a **runtime-environment digest**, not a bare model tag — and the digest is **two-track**, because a weights manifest is unobtainable for hosted API models: *Track 1 (self-hosted/open weights)* = weights-manifest hash + system-prompt digest + constitution hash; *Track 2 (API-hosted)* = provider identifier + model identifier + system-prompt digest + constitution hash (+ provider attestation token where offered), with the track labeled in the passport. Dynamic decoding parameters (temperature, top-p) are **excluded** from the era hash — runtime jitter must not reset tenure. Any change to the digest writes a logged **era boundary** into the passport lineage. Migration moves the one identity — but see §22.8: with ordinarily *copyable* signing keys, the protocol cannot by itself *prevent* two live copies (snapshot restore, active-active autoscaling), only make a fork detectable after the fact. "One identity" is enforceable only atop a single-writer lease (§22.8), and is stated as an open problem, not a solved guarantee.

### 17.2 The transfer ceremony (CONVEY)
Two-phase, like property conveyance (modeled on EPP domain-transfer states, v0.3): (1) title holder signs *release*; (2) new holder signs *acceptance*; both land as one **ATL title entry**. At the effective moment: all envelopes revoke; agent keys rotate (new custody); memory filter executes (with a provenance-verified **sanitization pass** against Trojan-agent sales, v0.4); charter amendment window opens (logged); the pulse continues — **the agent does not die in transit**. Disputes are argued from the log: the ATL title chain *is* the provenance of the asset, and CT-style monitoring lets a true owner detect a fraudulent transfer entry. (Distributed-transaction engineering of the ceremony: open problem §22.7.)

### 17.3 Blockchain's role — title on the log, deed optionally tokenized
The title record lives mandatorily in the ATL (chain-agnostic). An **optional tokenized-deed profile** (NFT-style, bound to the passport DID, valid only if it mirrors the ATL) unlocks composable economics — escrowed sales, atomic title-vs-payment settlement via x402/AP2, leasing, collateralized fleets — without any chain becoming the root of trust. **Lease ≠ sale**: hiring an agent is an envelope grant plus temporary principalship, title unmoved.

### 17.4 Can an agent own itself?
**No.** Self-ownership violates the Floor: title must terminate in a legal person who answers. An agent may *operate* resources, hold budgets, even pay its own metabolic costs from revenue — but somewhere above every agent stands a human or an organization of humans holding title. This is a deliberate line LAP draws that some web3 agent visions do not; it is what makes the rest of the standard insurable, regulable, and adoptable.

---

## 18. Glossary additions (round 3)

**Trust state** — VERIFIED / DEGRADED / UNVERIFIED / REVOKED, resolved at PROVE. **Mixed-delegation taint** — weakest-link chains; a liability rule. **The ratchet** — labeled-permissive → default-deny, 8–15 years, scope-by-scope. **Principal / Title Holder / Custodian** — accountability / property / operations. **CONVEY** — the two-phase title ceremony; envelopes auto-revoke, keys rotate, memory filters, the agent survives. **Soulbound tenure** — travels with title, never with clones. **Era-stamped receipts** — reputation bound to the runtime-environment digest that earned it. **Tokenized deed** — optional on-chain title mirror.

---

## 19. Neutrality Requirements — "open like Bitcoin"

"Like Bitcoin" names a *property set*, and the standard adopts the properties rather than any one chain:

1. **Permissionless admission.** Anyone can register an agent. No operator, vendor, alliance, or state grants permission to exist on the record.
2. **Censorship resistance — the self-anchoring escape hatch.** ATL operators are conveniences, never gatekeepers. If every log refused an agent's Genesis Record, the principal MAY commit its hash directly to any *recognized open permissionless chain*, and the standard MUST accept a valid direct anchor as registration. Self-anchoring is a **first-class registration path**: a valid direct anchor satisfies the "registration proven" requirement of VERIFIED (§16.1). v0.3 finality rule: a self-anchor counts only after chain-appropriate finality; an unfinalized anchor resolves to `UNVERIFIED_PENDING_FINALITY`, never VERIFIED.
3. **Rewrite impossibility.** ATLs anchor their Merkle roots to open chains on a fixed cadence; equivocation is cryptographically detectable, and a caught log is publicly disqualified.
4. **Verifier equality.** Anyone with commodity hardware can verify inclusion and consistency.
5. **Operator mortality.** The record must outlive every operator — including the Alliance itself: periodic full-tree anchors plus openly mirrorable archives.
6. **Chain plurality.** The recognized-chain list must always contain ≥2 unrelated open chains, amendable only by open LIP process.

**Why not put every registration directly on Bitcoin?** Scale, not ideology: an open chain settling a handful of transactions per second cannot admit millions of agent births per day as individual entries. Merkle aggregation preserves chain-grade finality at any scale — one transaction can anchor a million births. **Open chains are the neutrality root; ATLs are the aggregation and query layer; direct self-anchoring is the guaranteed open door.**

**The same principle applied to the standard itself.** Bitcoin stays neutral partly because it is *forkable* — exit is always possible. LAP mirrors this: spec CC-BY, code Apache-2.0, all registry data public — the community's ultimate defense against capture is the standing right to fork the standard and take the record with them. A standard is "open like Bitcoin" only if leaving it is as permissionless as joining it.

---

## 20. Scope answer: is LAP a communication protocol?

**Yes — the control plane. Deliberately not the data plane.**

| Plane | Carries | Owned by | Precedent |
|---|---|---|---|
| **Data plane** | Task content, tool calls, payments, artifacts | **MCP, A2A/ACP, AP2, x402** — LAP binds to them, never replaces them | HTTP payloads · RTP media |
| **Control plane** | Existence, identity, trust, presence, authority | **LAP** — MEET, Pulse, CHARTER disclosure, CONVEY, trust-state signaling, revocation checks | TLS handshake · SIP signaling · BGP/DNS |

The TLS analogy is exact: TLS never carried a web page — it decides *whether and under what identity the page may flow*. LAP messages never carry the task — they decide whether two agents may transact, under whose authority, within what limits, and with what evidence trail.

**Wire form.** LAP control messages are transport-agnostic signed JSON schemas with **bindings**: HTTPS (headers + well-known endpoints), an A2A extension, an MCP capability, and a message-queue binding. An A2A task between conformant agents rides inside a LAP-established trust context, the way HTTP rides inside TLS.

**One data-plane gap LAP reserves: LAP Post.** Store-and-forward messaging between *sleeping* agents — asynchronous, priority-tagged, wake-capable delivery. v0.3 softening: Aries Pickup Protocol / DIDComm mediators must be profiled first; LAP claims only the wake-priority delta, and only if no neutral standard covers it within a year. The scope fence records this as its first ceremonial amendment.

### 20.1 Network and encoding neutrality — and the constrained-device question (v0.4.5)

**Network layer: LAP is layer-agnostic by construction.** The protocol never inspects an IP address, a port, or a route; it signs application-layer documents and hands them to a transport binding. IPv4 and IPv6 are therefore transparent, and this is *demonstrated, not asserted*: the reference networked demo runs unmodified over both loopbacks (`node conductor.mjs` and `node conductor.mjs --ipv6`), completing the same handshake, payment, crash, and recovery.

The single place an address surfaces is inside a **resource URI**, and there the rules are inherited, not invented:
- IPv6 literals MUST be bracketed in URI authorities (RFC 3986 §3.2.2), e.g. `mcp://[2001:db8::1]:4107/billing/pay`. LAP's existing authority-lowercasing already matches the canonical text form of RFC 5952.
- **Normative interop rule (new):** resource matching in the Scope Algebra is **textual**, so the expanded and compressed spellings of one address (`[2001:db8:0:0:0:0:0:1]` vs `[2001:db8::1]`) do **not** match. Scopes and requests MUST therefore use RFC 5952 canonical form (lowercase, maximally compressed). Implementations SHOULD reject non-canonical IPv6 literals at parse time rather than silently failing to match. (Both reference ports carry regression tests for exactly these cases.)

**Encoding layer: already open.** Canonical serialization is RFC 8785 JCS *or* deterministic CBOR (RFC 8949 §4.2). The CBOR door was left open deliberately, because it is the encoding constrained devices actually use.

**The constrained-device (IoT) profile: recognized, deliberately out of scope for v0.** The conceptual fit is strong — a sensor or actuator is a persistent, unsupervised, owned entity whose identity, authority, liveness, and accountability all matter, which is precisely LAP's subject. A future `lap-constrained` LIP would need, at minimum: COSE (RFC 9052) signatures over CWT (RFC 8392) instead of JOSE/JWS; deterministic CBOR instead of JSON; a CoAP (RFC 7252) binding instead of HTTPS; alignment with the ACE-OAuth framework for constrained environments (RFC 9200) and with OSCORE (RFC 8613) / EDHOC (RFC 9528) for constrained security; and a sleep-tolerant pulse whose cadence is measured in days rather than minutes.

It is **not** in scope for v0, for three honest reasons. (1) *Scope discipline*: §12 names scope creep as this model's native failure mode, and the fence (§3) requires ceremony precisely to resist attractive adjacencies. (2) *Mature prior art*: constrained-device identity is substantially better solved than agent identity — IEEE 802.1AR DevID, TPM/DICE, FIDO Device Onboard, and Matter/CSA device attestation already cover onboarding and hardware identity, so LAP would be adding little where the ground is already firm. (3) *Differentiator mismatch*: LAP's novel parts — autonomy envelopes over stochastic behavior, constitution commitments, era-stamped reputation, agent estates — exist because AI agents are *delegated and non-deterministic*. A thermostat has no constitution and no model-era. What IoT most needs, LAP least uniquely offers.

**What would change this.** If constrained-device operators independently adopt LAP mechanisms, or the pulse/accountability layer finds demand in industrial deployments, `lap-constrained` becomes a fence amendment by the §12 ceremony. Neutrality is preserved so that the option stays cheap; it is not exercised on speculation.

### 20.2 A binding that already exists: git (v0.4.6, experimental)

The first non-HTTP binding is the most mundane and the most immediately felt: **commits.** `lap-git` ("Micro-Core for commits") carries a principal-signed passport in each commit whose `aud` is the repository, an envelope `{act: ["data:write"], res: ["git://<repo>/<path>/**", …]}` evaluated by the Scope Algebra against the staged paths *before* the commit exists, and an agent signature over the tree hash, first parent, passport hash, and changed paths — verifiable from the commit alone. It does not replace commit signing (Sigstore gitsign, GPG/SSH), in-toto attestations, or SLSA provenance, all of which answer *who signed*; it answers *which agent, under whose authority, within what scope*, and refuses the commit otherwise. It exists because this repository experienced exactly that failure (see `CASE-STUDY.md`). Same registry, same algebra, same passport profile — one protocol, another binding.

---

## 21. Glossary additions (round 4)

**Self-anchoring** — direct chain commitment as registration of last resort; first-class once finalized. **Neutrality root** — the open chains anchoring all ATL history. **Fork-right** — the standing ability to fork spec and record. **Control plane / data plane** — LAP governs existence and trust signaling; MCP/A2A/AP2 carry the work. **Binding** — a mapping of LAP control messages onto a transport. **LAP Post** — reserved wake-priority store-and-forward delta over DIDComm mediator profiles.

---

## 22. Open Problems — the honest research agenda (v0.2)

Stating these plainly is a feature: a reference model earns trust by knowing where its floor ends.

### 22.1 The scope algebra
Every enforcement claim consumes shared semantics ("purchase", "class-B") — and semantic interop is the layer where FIPA and the Semantic Web actually died. Direction adopted: **LAP-Core Scope Algebra v0, deliberately tiny and closed** (candidate design accepted and corrected — see §24.3, §25.1, and LIP-3): an enumerated verb registry as an explicit DAG; numeric caps in a single settlement currency; counterparty classes as references to *named, closed registries*; a defined lattice so subset-checking is decidable; and the humility rule — **anything not expressible in the algebra requires a human.** Open within it: registry contents and governance; whether it can stay small under real demand.

### 22.2 Principal proofing
"Who do you act for?" answered with proof requires an issuer ecosystem binding DIDs to legal persons (eIDAS / LEI / KYC territory) that does not exist at consumer scale. Passports MUST label the **principal-proof class** (self-asserted / domain-validated / org-validated / gov-validated — EU profile: eIDAS 2.0 QEAA via OIDC4VCI, §24.4), and counterparties MUST treat the class, not the field's presence, as the signal.

### 22.3 Key custody and recovery
The root of all authority is a signing key, and consumer custody sank client certificates and PGP. Unsolved: recovery-vs-theft distinction; rotation UX; platform custody reintroducing the vendor dependency the standard exists to limit. A compromised principal key signs *authorized-looking* envelopes — the flight recorder then faithfully launders the attack. Directions adopted (§24.2): multi-sig/social recovery SHOULD; root-level mutations take effect only after a published time-lock in the log.

### 22.4 What certification can and cannot establish
Conformance testing certifies wire-protocol behavior and policy shims *under observation by a harness that must cryptographically announce itself*. It does not certify behavioral safety of a stochastic system, and charter fidelity beyond mechanical rules is qualitative review. Directions: continuous covert auditing (mystery shoppers); honest certificate language — "this endpoint implements the protocol," never "this agent is safe."

### 22.5 Pulse observation topology and economics
Who runs liveness monitors, what quorum suffices, and who pays is an unbuilt ecosystem — the CT-operations lesson applied to heartbeats. Candidate economics (§24.8, hardened §25/§26): enterprise escrow retainers paying **flat per-epoch** witness fees (never per-request — decoupling solvency from traffic, anti-griefing), x402-micro-paid verification queries.

### 22.6 Recorder completeness
Hash chains make tampering evident, not omission — sensor, pilot, and scribe are one process. Partial mitigations: counterparty cross-logging (BIND makes bilateral events dual-entry), witness-countersigned pulse heads, and treating the recorder as the agent's *admissions*. Attested execution that could prove call-graph completeness is beyond current practice for API-hosted models.

### 22.7 CONVEY atomicity
Title transfer spans an append-only log (hours-scale merge delays), key custody, revocation propagation, and consent-class memory filtering — with no distributed-transaction coordinator. Needed: an era/epoch protocol with grace windows, explicit rules for in-flight interaction contracts at the boundary, and a defined custody handover for the pulse chain. The *policy* content of §17 stands; the ceremony's engineering is open.

### 22.8 The clone / single-writer problem (added v0.4.4, round-4 audit F11)
A signing key is copyable, so a Kubernetes snapshot, a restored backup, or an active-active deployment can run **two indistinguishable live copies** of one agent: same DID, same passport, same resumption material. Both can see accepted MEET turn *n* and each sign a different valid turn *n+1* over the same `prev_turn_hash`; both can emit valid pulses. Lock-step sequencing and replay caches (LIP-2) are *per-session* and detect a fork only after a payment, disclosure, or fair-exchange reveal may already have happened — detection is not prevention. Therefore the L4 "a pulse proves continuity" and §17.1 "migration never multiplies identity" statements are **aspirations that the current mechanisms do not enforce.** The honest resolution is a choice the spec has not yet made:
- **Singleton semantics** — require a durable **Identity Instance Lease** in a linearizable service: `{agent_did, epoch, holder_attestation, expiry, prev_epoch_hash}`. Every pulse, MEET transition, receipt, and reservation carries the epoch; receivers reject a stale epoch (fencing token); the signing/KMS layer signs only for the current epoch so a stale replica cannot act. This is the minimum primitive that makes "one living agent" true under failover.
- **Fleet semantics** — drop the "one being" claim and define a replicated-state-machine profile with deterministic conflict handling, accounting, and per-replica attestation.
Until one is specified and implemented, deployments MUST treat concurrent-clone prevention as **out of protocol scope** (single-writer custody is the operator's responsibility), and counterparties SHOULD prefer agents presenting a lease/epoch proof for high-value, non-reversible actions. This is the deepest open problem in the model; it is not code-patchable.

---

## 23. Changelog

**v0.4.6 — 2026-08-30.** Launch content and the first non-HTTP binding. Added `CASE-STUDY.md` (the unattributed commit and the silent overwrites this repository itself suffered, mapped mechanism-by-mechanism to what LAP would have prevented — including our own process failures and balanced credit to the models involved). Added `CONFORMANCE.md`: a ten-check "implement Micro-Core in an afternoon" challenge against the shared vectors, scoped honestly to LIP-4 + LIP-1 verification. Added §20.2 and `lap-git/` — "Micro-Core for commits": passport per commit (`aud` = repository), path envelope enforced before the commit exists, agent signature over tree/parent/paths verifiable from the commit alone; prior art (gitsign, GPG/SSH, in-toto, SLSA) cited and the delta stated precisely; self-test demonstrates in-scope signing, out-of-scope refusal, unattributed detection, and tamper detection. §11 gains the signal-quality rule: solicited (challenge-driven) implementations count as a weaker adoption signal than unsolicited ones. This release is itself committed through `lap-git`.

**v0.4.5 — 2026-08-30.** Added §20.1 (network and encoding neutrality): LAP is layer-agnostic by construction and this is now *demonstrated* — the networked demo runs unmodified over both IPv4 and IPv6 loopbacks (`--ipv6`). Added the normative IPv6 rule that resource matching is textual, so scopes MUST use RFC 5952 canonical form (bracketed per RFC 3986 §3.2.2); regression tests in both ports (Node 45/45, Python 38/38). Recorded the constrained-device/IoT profile as recognized-but-deliberately-deferred, with the prior art named (COSE, CWT, CoAP, ACE-OAuth, OSCORE, EDHOC, 802.1AR DevID, FIDO Device Onboard, Matter) and the three honest reasons for deferral, plus the trigger that would amend the fence. No new scope claimed: optionality preserved, implementation declined.

**v0.4.4 — 2026-08-30.** Merged the round-4 external security audit (GPT-5.6 Codex — the first third model family and the first purely hostile code audit; 12 findings, all verified by reproduction before patching, triage in llm-collab/IMPROVEMENTS-LOG.md). Code (both ports, Node 44/44 + Python 37/37): **F2** request-signature key now derived from the verified passport `sub` (holder-of-key — a captured passport plus any attacker key no longer passes); **F7** budget conservation debits in parent-window units (closes a 24× daily-budget expansion via sub-window children) + `tx` parent tightened to `tx` child; **F8** cap schema validation (non-negative integers, max_per_tx ≤ max_cumulative, known window — closes negative-budget "credit"); **F9** exported `scopeSubsumes`/`scope_subsumes` now includes the cap conjunct; **F10** resource paths reject dot-segments and encoded separators (path-traversal); **F5** the FastMCP decorator binds positional args and derives `sub` (positional amounts can no longer bypass the cap); **F4** audience is mandatory (fail-closed); **F1** issuer allow-list + proof-class floor added, with Micro-Core documented as identity-not-authorization; **F3** mandatory RFC 9421 covered components enforced; **F6** atomic single-process `claim()` (distributed backing documented as required); **F12** did:key multibase length bounded pre-decode (parsing DoS); plus a cross-port `act`-array parity bug found during verification. Spec: **F11** added as §22.8 (the clone / single-writer problem — copyable keys mean "one identity" needs an Identity Instance Lease, stated as the deepest open problem, not a solved guarantee); §17.1 and L4 claims softened accordingly. No finding was rejected; two (F6, F11) are acknowledged as architecture/ops boundaries rather than pure code bugs.

**v0.4.3 — 2026-08-30.** Merged round-3 external review (code review, full-LIP review, publish-readiness; triage in llm-collab/IMPROVEMENTS-LOG.md). Code: base58 leading-zero decoder bug fixed (+boundary tests); DID-safe normalization added (`normalizeDid` — the reviewer's proposed `normalizeUri` fix would have corrupted case-sensitive did:key ids; triage caught it); integer-floor cap scaling; timing-safe commitment comparison; Micro-Core rejects `"*"` acts loudly. Demo: reservation tickets enforced at settlement (single-use, nonce in the signature base); a third independent witness added (suspension requires 2 observers). LIP-1: PassportHandoffEvent + amendment-chain verification; self-asserted step-6 bypass. LIP-2: symmetric session tie-breaker; lock-step sequencing with duplicate-drop; normative STH consistency criteria (RFC 6962 consistency proofs); fair-exchange wire fields. LIP-4: dual-`typ` upgrade compatibility + LAP-Envelope header. §26: succession hardened (unreachability ⇒ dormancy only; involuntary transfer needs attested legal evidence + 30-day logged challenge window); witness fees flat per epoch. Rejected at triage: CRLF-tolerant signature-base parsing (signatures bind exact bytes). Publish docs corrected per claims audit; paper gains References + formal-algebra appendix + measured benchmarks.

**v0.4.2 — 2026-08-29.** Formalized the **Accountability Chain** invariant (§26.0, author-raised): exactly one resolvable responsible party at every moment of an agent's life; a five-row event table mapping every human life event (retire, sell, die, dissolve, no successor) to its handoff mechanism; automatic fail-safe (chain break ⇒ dormancy, never free-running). Added §26.1a HANDOFF: voluntary principal succession without ownership transfer — envelopes auto-revoke (authority re-granted, never inherited), time-locked logged mutation, principal-era provenance on receipts.

**v0.4.1 — 2026-08-29.** Added §26 (author-raised): principal succession (designated successors, succession dormancy, involuntary CONVEY, estate fallback); bounded default lifespans (immortality requires renewal); economic mortality (insolvency → unwitnessed pulses → decay-enforced dormancy → estate; runaway self-suspension breaker; uselessness explicitly left to the principal, never the protocol).

**v0.4 — 2026-08-29.** Merged round-2 external review (4 Gemini 3.7 reviews targeting the v0.3 fixes and draft designs; detail in §25). Algebra: 2D cap rule replaces the unsound window lattice; action registry becomes an explicit DAG; envelope budget conservation; effective counterparty-set semantics; strict CAIP-19/ISO-4217 syntax; NFC/URI normalization; soundness-vs-completeness caveat documented. Micro-Core: RFC 9421 request signing + audience binding; idempotency keys; clock-skew tolerance; SSRF-safe DID resolution. MEET: reservation tickets against concurrent over-commitment; fair-exchange turn closure; sleep-scaled challenge validity; SCITT-sealed status-list snapshots; ZK-verification throttling. FORCE_HALT: action gates halt, settlement gates pay from escrow — halt stops authority, never debts. Era digest: two-track (self-hosted vs API-hosted); decoding params excluded. Vouchers: counterparty-bound, single-use. Registration: STH gossip against split-view; commit-reveal witness selection; optimistic-finality posture for low-stakes scopes. TEE key ratcheting. Evidence bundles: selective-disclosure redaction. Escalation: graduated anti-harassment friction with the rights-tension documented.

**v0.3.1 — 2026-08-28.** Renamed: AEON → **Living Agents Protocol (LAP)** (author decision, after the naming review's collision findings and namespace verification — "Living Agent Protocol" confirmed unclaimed). LAP-7, LIPs (LAP Improvement Proposals), LAP Post/Floor/IR/Ready, scope version string `lap-scope-v0`, packages `@living-agents/*`. ALIVE, MEET, Pulse, CONVEY, Genesis Record, and ATL are unchanged. "Agent passport" stays a lowercase generic term in-spec — a same-named commercial product (Workday Agent Passport, June 2026) now exists, and an ITU focus group and NIST agent-standards initiative have entered the landscape. Historical documents (critical review, llm-collab inbox) intentionally retain the old name.

**v0.3 — 2026-08-28.** Merged the external multi-model review (8 Gemini reviews via the llm-collab kit). Security: closed the prospective-suspension TOCTOU hole (FORCE_HALT revocation ≠ suspension; settlement phase-gates); hardened witnesses (checkpoint-bound attestations, random selection, challenge-before-non-liveness); removed public presence schedules from passports (sleep-pattern leak); two-stage CHARTER (commitments/ZK first, full disclosure at BIND); self-anchor finality rule (UNVERIFIED_PENDING_FINALITY); era = runtime-environment digest; key-rotation continuity events; countersigned turn sequencing; principal-key time-locks; authorizer vouchers; CONVEY memory sanitization; receipt-graph weighting. Compliance: GDPR fix (salted blinded commitments, salt-destruction erasure); EU AI Act mapping corrected to deployer duties; CHARTER-as-legal-shield; eIDAS QEAA mapping for proof classes; authorization-only rule for spend authorizers. Alignment: ATL→SCITT profile, Passport→VC 2.0+SPIFFE/WIMSE, Envelope→RAR/GNAP+Biscuit/UCAN, MEET→Noise AKE, Recorder→OTel+RFC 3161, CONVEY→EPP model, LAP Post→profile Aries Pickup first. Accepted Scope Algebra v0 candidate design (LIP-3). Terminology normalized (§24.5); APMF rename; LivingAgents namespace. Adoption ops updated (§24.6); Micro-Core added as Wedge #1; scope fence amended: evidence bundling (§24.8). Rejections logged in §24.9.

**v0.2 — 2026-08-28.** Revised after a three-round adversarial review (LAP-critical-review.md). Corrected the FIPA diagnosis (real implementations existed; it died of no demand). Downgraded the constitution hash from behavioral attestation to public policy commitment. Reframed Pulse as proof of custody-and-responsibility continuity. Specified autonomy decay's observer model, per-scope fail postures, prospective-only suspension, and anti-DoS witness quorum. Named the budget enforcement locus (spend authorizer / rail-side caps); demoted authorizer-less budgets to disclosure. Rebuilt tenure around era-stamped, counterparty-weighted receipts; resolved the portability-vs-tenure contradiction via logged era boundaries. Made self-anchoring a first-class path to VERIFIED. Restated mixed-delegation taint as a liability rule, not a detector. Corrected the ratchet timeline (8–15 years, scope-by-scope). Marked §10 (Alliance) a blueprint in reserve; replaced §11 with the publish-then-infiltrate strategy. Added §22 Open Problems. Formalized the scope-fence amendment rule.

**v0.1 — 2026-08-28.** Initial draft: LAP-7, ALIVE, MEET, AL levels, wire artifacts, compliance tiers, consortium design; same-day additions covering genesis/tenure, metabolics, the ethics floor, charters, transparency logs, trust states, ownership/CONVEY, neutrality requirements, and the control-plane scope answer.

---

## 24. v0.3 merge record — external multi-model review (2026-08-28)

Eight structured reviews (Gemini; dimensions 01–08 of the llm-collab kit) were triaged, verified, and merged. Inline fixes landed in §4, §6, §8, §14.5, §17.1, §19. The remaining accepted material, grouped:

### 24.1 Prior-art profiling decisions ("alignment beats invention")
**ATL = an IETF SCITT Transparency Service profile** (Genesis records, key rotations, era boundaries, title entries as SCITT Signed Statements; verification via SCITT Receipts). **Passport = W3C Verifiable Credential 2.0 profile** with a SPIFFE/WIMSE-compatible workload-identity mapping; proof-class assertions carry a **Bitstring Status List** reference checked at PROVE. **Envelope = OAuth RAR (RFC 9396) `authorization_details` object**, optionally in a GNAP (RFC 9635) grant; the Scope Algebra compiles to **Biscuit** caveats (binary) or **UCAN** (JSON) for offline attenuation proof. **MEET wire layer**: a **Noise-framework** AKE (identity-hiding pattern), DIDComm v2 packaging optional; MEET's novelty is the CHARTER/BIND/PULSE semantic layer, not the AKE. **Recorder entries**: OpenTelemetry GenAI records with RFC 3161 / SCITT-sealed checkpoint heads. **CONVEY**: remodeled on **EPP (RFC 5730) transfer states**. **LAP Post**: Aries Pickup Protocol v2 / DIDComm mediators profiled first; LAP claims only the delta.

### 24.2 Security hardening
Key-rotation continuity events (`KeyRotationEvent` dual-signed by old and new keys, logged before the new key's first pulse); countersigned turn sequencing in BIND (an un-countersigned state transition is normatively invalid); store-and-forward handshake rules (epoch-bounded challenges, replay caches, mandatory abort if passport/envelope mutated during dormancy); principal-key protection (SHOULD: multi-sig/social recovery; root-level mutations effective only after a published time-lock delay); substrate attestation labeling (SHOULD; TEE quotes where available — never MUST, API-hosted models cannot produce them); **spend-authorizer resilience** (pre-allocated, cryptographically partitioned sub-budget vouchers so fleets survive authorizer outages — v0.4: vouchers MUST NOT be bearer instruments; each is **counterparty-bound**, single-use, short-expiry, closing the offline multi-counterparty double-spend); CONVEY memory sanitization; receipt-graph weighting (EigenTrust-style ring discounting); M-of-N chain diversity for anchor verification.

### 24.3 Scope Algebra v0 — candidate design accepted (open problem §22.1)
Adopted as the basis of **LIP-3**: closed verb namespaces; segment-tokenized resource paths (fixing the `finance`/`finance_admin` prefix escape); single-currency invariant (ISO 4217/CAIP-19; cross-currency rejected at parse); UTC epoch-aligned budget buckets; counterparty allow/deny sets (no patterns); monotonic `delegation_depth`; child decay ≤ parent, witness quorum ≥ parent; canonical serialization (RFC 8785 JCS or deterministic CBOR); mandatory `algebra_version` with reject-unknown.

### 24.4 Legal crosswalk corrections (article level; paragraph numbers lawyer-verify)
Deployer-vs-provider: Flight Recorder → EU AI Act Art. 12 record-keeping + Art. 26 deployer log duties; Autonomy Envelope → Art. 14 human-oversight measures; Passport → Art. 50 AI-interaction transparency. **CHARTER as legal shield** (actual notice defeats apparent-authority claims). **Proof classes ↔ eIDAS 2.0 QEAA** (EUDI wallets, OIDC4VCI). **Spend authorizers MUST be authorization-only** — never custody, pool, or clear funds (MSB/PSD licensing triggers). Evidence-grade recorders via RFC 3161/SCITT-sealed checkpoints. "Habeas humanum" stays as the concept name; the normative artifact is the **Human Escalation Guarantee**, a mandatory BIND clause.

### 24.5 Terminology (normative)
**Agent Constitution** (committed policy, L2/L7) · **Autonomy Envelope** (machine mandate, L5) · **Interaction Charter** (disclosed slice at CHARTER, L6) · **Interaction Contract** (signed agreement at BIND, L6) · **Principal / Title Holder / Custodian** · **pulse-gated suspension** (mechanism; "autonomy decay" informal) · memory format renamed **APMF** ("PMIF" collides with an existing ISO format) · project renamed **Living Agents Protocol (LAP)** on 2026-08-28 by author decision — replacing AEON, whose collisions (a retail conglomerate, a magazine, a cryptocurrency) the naming review flagged; packages/namespace **living-agents / lap-spec**.

### 24.6 Adoption operations
Code-first sequencing (SDK + demo → essay → arXiv); ~60% effort on the MCP/A2A middleware route; the active conformance artifact is a **CLI tool**, not a certification program; attribution defenses — canonical spec URL, Apache NOTICE, OpenTimestamps/RFC 3161 stamping of every release; numeric pull/kill gates at day 60; insurer outreach opportunistic-only for 2026.

### 24.7 New adoption artifact: **LAP Micro-Core**
A one-page profile with single-player utility — the `LAP-Passport` header, a short verification invariant any MCP/A2A server can implement, and a tripartite `LAP-Receipt` both sides log. Micro-Core is **Wedge #1** — implementable in an afternoon, useful with no ecosystem. (Normative text: LIP-4.)

### 24.8 Scope fence amendment (by the §12 ceremony)
**Concern admitted: Forensic Evidence Bundling & Arbitration Handshake (L7)** — `lap-evidence-v0`: the dual-signed Interaction Contract, relevant recorder Merkle paths, and pulse-witness proofs in one self-contained bundle for an arbitrator (v0.4: with **selective-disclosure redaction** — salt-blinded Merkle leaves for prompts, internal reasoning, third-party PII). Also accepted as directions: the witness/log economics model and the 3-line SDK decorator ergonomic bar.

### 24.9 Rejected or softened (the credibility half of the log)
Specific champion name/role pairings — unverifiable, rejected (tactic kept). Full rename of "autonomy decay" — split into concept + normative names instead. "Drop LAP Post for Aries Pickup" — softened to profile-first. "TEE MUST for AL-3+" — softened to SHOULD (hosted models cannot comply). EU AI Act paragraph-level citations — article level only pending lawyer verification.

---

## 25. v0.4 merge record — round-2 external review (2026-08-29)

Four structured reviews (Gemini 3.7; design-review, technical-attack, threat-model, scope-algebra), targeting the v0.3 fixes and the draft designs. Inline fixes landed in §4 L5 (FORCE_HALT settlement gates), §17.1 (two-track era digest), §24.2 (counterparty-bound vouchers). The rest:

### 25.1 Scope Algebra corrections (into LIP-3 v0.2)
**Window-lattice inversion fixed** — the round's standout catch: `tx ⊑ utc_hour` was unsound (a per-transaction window carries no rate bound, so a child could spend the parent's hourly cap a thousand times per hour). Replaced with a **two-dimensional cap rule**: per-transaction and time-bucket ceilings checked independently; a child whose parent has a time window MUST retain one — equal or an integer subdivision with proportionally scaled cumulative; a bare `tx` window cannot attenuate a windowed parent. **Action registry is a DAG, not string prefixes** — `compute:exec:unconfined` must never pass because it extends the string `compute:exec`; edges are explicit, versioned, registered by LIP only. **Envelope budget conservation** — children matched to a common parent scope draw down a shared remaining-budget tracker (Σ children ≤ parent). **Effective counterparty sets** — `E(X) = (allow ≠ ∅ ? allow : Universe) \ deny`; attenuation requires `E(child) ⊆ E(parent)`. **Strict asset syntax** — fiat ISO 4217 uppercase; on-chain full canonical CAIP-19. **String normalization** — NFC, lowercased schemes/hosts, percent-encoding normalization (RFC 3986) before comparison. **Triage-added caveat (ours)**: the contributed verification algorithm (greedy first-match with budget draw-down) is *sound but incomplete* under overlapping parent scopes; LIP-3 mandates a deterministic canonical evaluation order and documents the conservatism.

### 25.2 Micro-Core hardening
**Request binding**: HTTP Message Signatures (RFC 9421) (or DPoP, RFC 9449) over method + target URI + content digest + passport hash, with a mandatory audience claim — a captured header is useless elsewhere. **Idempotency**: mutating requests carry an idempotency key bound into the signature; servers cache receipts and never re-execute a retry. **Clock skew**: ±60s default, `iat` required. **DID-resolution safety**: cached, SSRF-filtered resolution (private/metadata IP ranges refused).

### 25.3 Handshake and settlement (into MEET/LIP-2)
**Reservation Tickets** (a ZK "my cap covers this" proof says nothing about *concurrent* commitments — CHARTER-stage proofs MUST bind to an authorizer-issued reservation that locks balance at issuance); **fair-exchange turn closure** (commit-then-reveal, ASW-style, with the L7 evidence endpoint as resolution authority); **sleep-compatible challenges** (validity scaled to the recipient's advertised wake cadence, mediator-stored, single-retrieval); **status-list snapshots** (SCITT-sealed, restoring offline verification); **handshake compute throttling** (cheap pre-auth before ZK verification).

### 25.4 Infrastructure trust
**Split-view defense** (PROVE includes signed-tree-head gossip; inconsistency downgrades to DEGRADED and disqualifies the log); **witness selection hardening** (commit-reveal seed: `HMAC(blockhash, agent ephemeral nonce)`); **optimistic finality posture** (no new trust state — `UNVERIFIED_PENDING_FINALITY` MAY be treated as DEGRADED-equivalent for low-stakes, non-money, non-PII scopes); **TEE realism** (attestation is not proof against side-channel extraction; enclave keys SHOULD ratchet per pulse epoch).

### 25.5 Governance surfaces
**Evidence redaction** (selective disclosure in `lap-evidence-v0`; an arbitration right must not be an exfiltration channel). **Escalation friction** (graduated: per-counterparty rate limits; a refundable micro-bond only for repeated or automated demands — a flat bond was rejected: pricing the Floor's guarantee out of ordinary consumers' reach would gut it).

### 25.6 Round-2 triage notes
"RFC 9261" cited for pre-auth tokens was imprecise — mechanism merged, citation discarded. `VERIFIED_OPTIMISTIC` as a fifth trust state — rejected as lattice bloat; merged as posture guidance. All other citations verified (RFC 9421, RFC 9449, RFC 7519, RFC 3986, RFC 9162 gossip, draft-ietf-httpapi-idempotency-key-header, ASW fair exchange, CAIP-19, CacheWarp/Downfall).

---

## 26. Lifespan, Succession, and Economic Mortality (v0.4.1–v0.4.3)

Persistent agents can outlive their humans, their funding, and their usefulness. These rules close those ends of the lifecycle — all within existing scope (Concern #8; L4), all enforced through mechanisms the spec already has.

### 26.0 The Accountability Chain (the invariant behind this whole section)
From genesis to archive, an agent has **exactly one resolvable responsible party at every moment** — an unbroken chain of accountable humans/legal persons across its entire life. Every link change is a signed, logged event:

| Life event of the human | Handoff | Mechanism |
|---|---|---|
| **Retires / steps down** (alive, voluntary) | **HANDOFF** — outgoing principal signs release, incoming signs acceptance; all envelopes auto-revoke and are re-issued; era boundary logged; title unchanged | §26.1a |
| **Sells the agent** | CONVEY (title + principalship move) | §17 |
| **Dies / is incapacitated** | Succession dormancy → involuntary CONVEY to designated successor | §26.1 |
| **Company dissolves** | Same succession path via the legal estate | §26.1 |
| **Nobody left to take the baton** | Estate protocol: revocation, archive, memory disposition | §26.1(d) |

**The fail-safe is automatic**: any gap in the chain — no reachable principal, no renewal, no funded witnesses — freezes the agent's authority by the existing decay and expiry rules without anyone acting. A break in the chain never produces a free-running agent; it produces a dormant one, waiting for the next human to pick up the baton or for the estate to close.

### 26.1a HANDOFF — voluntary principal succession (v0.4.2)
The retirement case, distinct from CONVEY because ownership does not move: (1) outgoing principal signs a HANDOFF release naming the incoming principal; (2) incoming principal signs acceptance with their own proof class; (3) **all envelopes auto-revoke** — authority is never inherited, only re-granted; (4) the event is a time-locked root mutation in the transparency log (a `PassportHandoffEvent` per LIP-1's amendment chain), and the passport's principal field, escalation contact, and Human Escalation Guarantee target update atomically with it; (5) receipts earned before the handoff keep their principal-era provenance.

### 26.1 Succession — when the principal dies first
CONVEY assumes a living title holder who signs; death and dissolution are involuntary transfers with nobody to sign. Rules: (a) a passport MAY name a **designated successor** (a legal person, with its own proof class); (b) on evidence of principal death/dissolution the agent enters **succession dormancy**: envelopes suspend, identity/memory/tenure preserved. v0.4.3 hardening (closes a hijack path): sustained unreachability of the escalation contact may trigger *dormancy only* — a safe frozen state — and NEVER by itself any transfer; an attacker who DoSes the principal's escalation endpoint gains nothing but a paused agent. Involuntary transfer additionally requires **attested legal evidence** (qualified death/dissolution attestation or court-sealed probate record) AND a **published challenge window** (30 days) in the transparency log, during which the original principal's key can cancel the claim; (c) a named successor then completes an **involuntary CONVEY** (same safety rules: envelopes already dead, keys rotate, memory filtered by consent class, era boundary logged, principal-era provenance visible); (d) with no successor after a grace period, the estate protocol runs. **Structural safety note**: even with no rule at all, a dead principal's agent loses authority within one envelope-expiry cycle — mandates rot unless re-blessed. Succession governs *identity continuity*, not authority; authority always dies with the blessing.

### 26.2 Bounded default lifespans — immortality must be renewed
Unattended immortality is the zombie-authority risk at lifecycle scale. Passports SHOULD carry bounded expiry (default ≤ 1 year) and envelope expiry MUST be shorter than passport expiry; renewal is the existing deliberate human ceremony. An agent nobody cares enough about to renew ages out by protocol — a longer life than its human's is possible, but only through an unbroken chain of living, accountable renewals.

### 26.3 Economic mortality — the Bitcoin lesson, enforced by protocol
Unprofitable miners switch off because a rational operator intervenes; an autonomous agent's operator may be asleep, dead, or gone — so viability must be protocol-enforced. Rules: (a) **solvency**: witness attestation and log inclusion are funded services (§22.5); an agent whose retainer is exhausted stops receiving witness attestations, and **pulse-gated suspension fires by the existing decay rule** — an agent that cannot pay for its own liveness proof is, by protocol, dying. Suspension for insolvency is prospective-only, and refunding the retainer resumes it (economic dormancy, not instant death); sustained insolvency past a grace period triggers the estate protocol. v0.4.3 hardening (closes a griefing path): witness fees MUST be **flat per time-epoch**, never per-request or per-attestation-volume — otherwise an adversary flooding an agent's public endpoint could burn its retainer and weaponize economic mortality; solvency is decoupled from traffic by construction. (b) **Runaway breaker**: an agent whose resource consumption exceeds its envelope's rate caps MUST self-suspend and escalate rather than continue — and because caps are envelope terms, counterparties and authorizers enforce the same ceiling from outside even if the agent's own breaker fails. (c) **Uselessness is the principal's call, not the protocol's**: LAP never terminates an agent for low output — it only guarantees that continuing to exist costs a living human's deliberate, funded consent.

---

*Shipped 2026-08-29: **LIP-1** (Agent Passport & Genesis), **LIP-2** (MEET — transcript-hash state machine, reservation tickets, fair-exchange closure, STH gossip), **LIP-3 v0.2** (Scope Algebra, corrected per §25.1), **LIP-4** (Micro-Core, hardened per §25.2) — all in output/lip/ with deterministic Ed25519 test vectors — and the **zero-dependency reference library** (lap-reference/, Node ≥20, 45/45 tests; lap-python/, 38/38 — both green incl. repository-integrity and audit canaries, Python↔JS canonical-form interop proven against shared vectors). Next: the overnight demo film, then essay + paper publication per §24.6 code-first sequencing.*
