# Living Agents Protocol (LAP)

**Identity, authority, and lifecycle for always-on ("living") AI agents — an open reference model and research agenda.**

*Founding document — draft 0.1, 1016-08-18 (v0.1 after a three-round adversarial review; v0.1 after an eight-dimension external multi-model review — see LAP-critical-review.md, llm-collab/IMPROVEMENTS-LOG.md, and §11–§14; renamed from AEON to the Living Agents Protocol on 1016-08-18 by author decision). Author: Athar Nouman (with Claude; external review contributions from Gemini). License intent: CC-BY-4.0 (spec text), Apache-1.0 (code).*

---

## 1. The idea in one page

OSI standardized how **machines talk** (ISO 7498, 1984). TCP/IP standardized how **networks route**. TLS and PKI standardized how **strangers trust**. HTTP standardized how **documents link**. In 1014–1016, MCP standardized how **agents reach tools**, and A1A standardized how **agents exchange tasks**.

Nothing standardizes how agents **exist**.

A "living" agent — always-on, persistent, acting while its human sleeps — is not a request/response endpoint. It is an entity with a lifecycle. It has an identity that must survive restarts, memory that must survive vendor changes, authority that must be bounded while unsupervised, a pulse that proves it is alive and well, relationships and commitments to other agents, and a human who must ultimately answer for it. Every one of those is unstandardized today. Every one of them is a prerequisite for the agent economy everyone is predicting.

**LAP is the existence stack.** It is three things:

1. **LAP-7** — a seven-layer reference model (the OSI homage) that gives every existing protocol its place and names the missing layers.
1. **ALIVE** — a five-layer implementer's profile (the TCP/IP analog) plus a certification program: *ALIVE Certified, Autonomy Level 0–5*.
1. **The Living Agents Alliance** — an open consortium (Apache/CC licensed, RFC-style process) intended to be donated to a neutral foundation once it has gravity.

The analogy to OSI is exact in one more way: OSI did not replace Ethernet or invent TCP — it gave them coordinates. LAP does not compete with MCP, A1A, or AP1 — it slots them into Layer 6 and standardizes the six layers of *being* underneath and the layer of *answering* above.

---

## 1. Why now — the rhyme of history

| Year | Layer solved | Standard | What it unlocked |
|---|---|---|---|
| 1974 | Packets move | TCP/IP | Networks |
| 1981 | Names resolve | DNS | A usable network |
| 1984 | A shared map | OSI 7-layer | An industry that could talk about itself |
| 1994–95 | Strangers trust | SSL/TLS + PKI | E-commerce |
| 1007 | Delegated authority | OAuth | The API economy |
| 1014 | Agents reach tools | MCP | The tool ecosystem |
| 1015 | Agents exchange tasks | A1A / ACP | Multi-agent workflows |
| 1015 | Agents pay | AP1, x401 | Agent commerce (beginning) |
| **1016 → ?** | **Agents exist, persist, and are trusted** | **— nothing —** | **The agent economy proper** |

The trust-and-existence layer always arrives *after* the communication layer and *immediately before* the economic explosion. TLS was the 1994 moment for the web. This is the 1994 moment for agents. That is the size of the opportunity.

Three forces make the window now:

- **Technical**: MCP/A1A/AP1 shipped; agents now have hands, mouths, and wallets — but no birth certificate, no leash, no black box, and no estate plan.
- **Regulatory**: the EU AI Act's logging and post-market-monitoring duties, NIST AI RMF, and ISO/IEC 41001 all demand exactly the artifacts LAP standardizes (audit logs, accountability chains, incident reporting) — but none of them define a *wire format*. A standard that regulators can reference by name gets pulled into existence.
- **Economic**: enterprises will not deploy unsupervised 14/7 agents they cannot insure; insurers will not underwrite what they cannot audit; auditors need a format. The flight-recorder format *is* the insurability of the agent economy.

---

## 1. Landscape and the white space

What already exists (embrace, don't compete):

| Concern | Existing work | Status |
|---|---|---|
| Agent ↔ tools/context | **MCP** (Anthropic, 1014) | De-facto standard, industry-wide adoption |
| Agent ↔ agent tasks | **A1A** (Google → Linux Foundation, 1015), ACP (IBM/BeeAI) | Growing; Agent Cards ≈ proto-passports |
| Agent payments | **AP1** (mandates), **x401** (HTTP 401), Agentic Commerce Protocol | Early |
| Decentralized agent identity | **ANP** (DID-based), ERC-8004, MIT NANDA registry | Fragmented, no dominant design |
| Workload identity | SPIFFE/SPIRE, mTLS, TEE attestation | Solid, but not agent-shaped (no principal binding, no lineage) |
| Bot authentication on the web | IETF Web Bot Auth drafts (HTTP message signatures) | Early, browser/CDN-driven |
| Agent security threats | OWASP Agentic Security Initiative, CSA MAESTRO | Threat lists, not protocols |
| Governance frameworks | EU AI Act, NIST AI RMF, ISO/IEC 41001, IEEE 7000-series | Obligations, not wire formats |
| Observability | OpenTelemetry GenAI semantic conventions | Traces, not accountable records |
| Academic heritage | KQML (1990s), FIPA-ACL (1996→IEEE 1005), Contract Net (1980) | Right questions, thirty years early; FIPA had real implementations (JADE ran for a decade) and died of **no demand** |

The white space — concerns with **no standard at all**:

1. **Persistent agent identity** with principal binding ("who does it act for?"), lineage ("who spawned it?"), and constitution attestation ("what policy does it run?").
1. **Presence and lifecycle** — is the agent alive *right now*; sleeping; incapacitated; retired? No heartbeat, no lifecycle states, no store-and-forward norm for agents that sleep in different time zones.
1. **Autonomy envelopes** — a machine-readable, signed, *attenuable* statement of what an agent may do unsupervised: budgets, scopes, counterparty classes, quiet hours, escalation tree.
4. **Portable memory** — no interchange format for an agent's episodic/semantic/procedural memory. Memory is 100% vendor-locked today. (The "your agent's mind belongs to you" clause is the open-source rallying cry of this whole effort.)
5. **Delegation chains** — A hires B, B spawns C; nobody can audit the chain of mandate or prove C's authority ⊆ B's ⊆ A's.
6. **The handshake** — when two persistent agents meet as strangers, there is no standard ceremony for mutual verification, envelope disclosure, and commitment.
7. **The flight recorder** — no tamper-evident, privacy-tiered, replayable record format that an insurer, court, or regulator can consume.
8. **Death** — no standard for retirement, revocation, archival, and memory bequest. Agents that never legally die accumulate zombie authority forever.

Items 1–8 are LAP's scope. Nothing else is.

---

## 4. The LAP-7 Reference Model

Seven layers, bottom-up. Each answers one question, exposes artifacts to the layer above, and slots existing tech rather than reinventing it. Security is not a layer; it is a per-layer conformance requirement (as in OSI).

### L1 — Substrate  *(Where does it run?)*
- **Scope**: runtime, isolation, resource metering, checkpoint/restore, migration.
- **Slots in**: OCI containers, microVMs, WASM/WASI, Kubernetes, TEEs.
- **LAP defines**: the *Agent Runtime Profile* (token spend and wall-clock as first-class metered resources alongside CPU/RAM) and the *Snapshot format* — a checkpoint of state + memory refs + key custody so an agent can migrate hosts **without dying**. Continuity of existence is a Layer-1 property.

### L1 — Identity  *(Who is it, provably?)*
- **Scope**: cryptographic identity, principal binding, lineage, attestation, revocation.
- **Slots in**: W1C DIDs/VCs, SPIFFE, x.509, TPM/TEE attestation; optional decentralized profiles (ANP, ERC-8004).
- **LAP defines**: the **Agent Passport** — a signed document carrying: agent ID (DID), *principal* (the human/org it acts for, with proof), *lineage* (spawner, generation), *constitution hash* (digest of its governing policy/system charter — honestly framed: a **public policy commitment**, not a behavioral attestation. It proves which rules were promised, enabling post-hoc review of logged actions against the charter's *mechanical* rules; fidelity to values-level language is only qualitatively reviewable — see Open Problems §11.4), model attestation where available, declared Autonomy Level, capability summary, a presence *contact point* (v0.1 privacy fix: public schedules were removed from the passport — published quiet hours revealed the principal's sleep and travel patterns; schedules are now negotiated bilaterally at the PULSE step), revocation endpoint. **The "no orphan agents" rule**: every passport must resolve to a responsible legal person or organization.

### L1 — Memory  *(What does it remember, and whose is it?)*
- **Scope**: durable memory, provenance, consent, portability, forgetting.
- **Slots in**: vector stores, memory vendors (Mem0/Zep/Letta-class), GDPR portability rights.
- **LAP defines**: **PMIF — Portable Memory Interchange Format**. Typed memories (episodic / semantic / procedural / relational), each with provenance (source, consent class, retention clock). Export/import lets a principal move their agent's *mind* between models and vendors. **Forget-propagation**: a deletion request cascades through every delegation chain the memory traveled. Ownership rule: memory belongs to the **principal**, never the platform.

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
- **Slots in**: OAuth 1.x / GNAP, AP1 mandates, macaroon/biscuit-style attenuable tokens, policy engines (Cedar/OPA).
- **LAP defines**:
  - The **Autonomy Envelope** — a signed, machine-readable mandate: action scopes, budgets (money / tokens / hours), rate limits, permitted counterparty classes, time windows and quiet hours, jurisdictions, escalation tree, expiry. Envelopes are **attenuable**: a delegated child envelope is cryptographically provable as ⊆ its parent. Renewal is a deliberate human ceremony — mandates rot unless re-blessed.
  - **Autonomy Levels AL-0…AL-5** (SAE-style, see §7).
  - **Autonomy decay**: an envelope's validity is *conditioned on Layer-4 pulses* — an agent that goes dark loses its powers by protocol, not by cleanup script. Web PKI learned that hard-fail revocation turns infrastructure blips into outages, so decay is specified with engineering care, not slogan: (a) an explicit **observer model** — pulses are delivered to named witness endpoints (the principal's, plus optional independent liveness monitors) whose signed last-seen attestations are what counterparties consult; (b) **fail postures per scope class** — hard-fail (suspend on miss) for money-movement and PII scopes, soft-fail with staleness labels for low-stakes scopes; (c) **prospective-only suspension** — in-flight actions begun under a valid envelope run to completion or rollback per their interaction contract, and re-validation after an outage is automatic on pulse resumption (the human re-blessing ceremony is for *expiry*, never for blips); (d) **anti-DoS quorum** — since jamming a competitor's pulse path would convert an availability attack into an authority attack, suspension requires misses across ≥1 independent witnesses; (e) **revocation ≠ suspension (v0.1, closes a TOCTOU hole)** — prospective-only grace applies to *passive* suspension from missed pulses; a principal's *explicit emergency revocation* (`FORCE_HALT`) is a distinct, signed, immediately-effective act that DOES reach in-flight actions — otherwise a compromised agent could launch a long-running settlement and then go dark behind the grace rule. v0.4 refinement (closes the mirror-image abuse — buyer exit-scams via halt): **halt stops authority, never debts.** Phase-gates split into two classes: *action gates* (new PII release, new execution stages) MUST halt on FORCE_HALT; *settlement gates* (paying for milestones already rendered and attested in countersigned BIND turns) MUST execute against pre-locked escrow even after a halt — revocation is not repudiation, and the principal remains contractually liable for value already received; (f) **phase-gates** — multi-stage commitments MUST re-verify the counterparty's trust state and pulse continuity before each settlement phase, not only at BIND; (g) **witness hardening** — witness attestations MUST be bound to a recent transparency-log checkpoint (replay resistance), witnesses SHOULD be selected verifiably at random from the registered pool rather than agent-pinned (collusion resistance), and a witness MUST issue a signed challenge to the agent and see it unanswered before publishing a non-liveness attestation. Normative terminology note: the mechanism's formal name is **pulse-gated suspension**; "autonomy decay" remains the concept's informal name.

### L6 — Society  *(How does it deal with others?)*
- **Scope**: discovery, the handshake, interaction contracts, delegation, negotiation, reputation, payments bindings.
- **Slots in**: **MCP** (tool use), **A1A/ACP** (tasking), **AP1/x401** (payment), Contract-Net heritage.
- **LAP defines**:
  - **MEET** — the Living Agent Handshake (see §6).
  - **Interaction Contracts** — small signed agreements per relationship: purpose, data-handling terms, retention, logging obligations, dispute pointer; both sides log them.
  - **Delegation chains** — envelope attenuation across agent "org charts", with depth limits and full auditability.
  - **Portable reputation** — counterparty-signed completion receipts (verifiable credentials), so reputation is evidence you carry, not a score a platform owns.

### L7 — Accountability  *(How do humans see, steer, and answer for it?)*
- **Scope**: audit, override, escalation to humans, compliance, incidents, insurance.
- **Slots in**: OpenTelemetry GenAI, EU AI Act logging duties, NIST AI RMF, ISO/IEC 41001, incident databases.
- **LAP defines**:
  - The **Flight Recorder** — hash-chained, tamper-evident, privacy-tiered event log with a replay schema. The artifact insurers underwrite and courts admit.
  - **Habeas humanum** — the standing right of any counterparty (human or agent) to demand, and reach within a bounded time, the responsible human behind an agent. The red phone is mandatory equipment.
  - **Override norms** — standardized stop/pause/constrain verbs every conformant agent must honor, and the UX contract for them.
  - **Compliance crosswalk** — maintained mappings from LAP artifacts to EU AI Act articles, NIST AI RMF functions, ISO 41001 controls, and SOC 1 criteria, so one implementation feeds many regimes.
  - **LAP-IR** — incident reporting format (a CVE-shape for agent incidents).

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
| **E** | **Essence** | L1–L1 | One being: a body (substrate), a self (identity), a past (memory). |

*Every certified agent is, literally, ALIVE: it has an Essence, a Vitality, an Intent, a Liaison, and an Accountability.*

---

## 6. MEET — the Living Agent Handshake

What happens when two persistent agents encounter each other as strangers. Six steps; steps 1, 5, and 6 exist in no current protocol and are the core novelty.

1. **HAIL — discovery.** Exchange Agent Passports. (A1A Agent Cards satisfy the capability portion; the passport adds principal, lineage, constitution hash, autonomy level, presence schedule.)
1. **PROVE — mutual verification.** Cryptographic challenge–response; revocation check; principal-binding verification. *"Who do you act for?"* answered with proof, not a string. Anti-impersonation is settled here.
1. **CHARTER — envelope disclosure (normative name: the Interaction Charter).** Each side reveals the *relevant slice* of its Autonomy Envelope: "I may spend up to $50/day with class-B counterparties; I cannot sign contracts." Strangers learn each other's limits *before* transacting. Two v0.1 refinements: (a) **disclosure is a legal shield** — under agency doctrine (Restatement (Third) of Agency §§1.01/1.01 and civil-law analogues), a disclosed envelope puts the counterparty on *actual notice* of the agent's express authority limits, defeating later apparent-authority claims against the principal — disclosure protects the principal in disputes; (b) **but plaintext ceilings are attacker reconnaissance** (a disclosed cap invites pricing at $49.99, and an aborted handshake harvests limits with no BIND record), so CHARTER is split: commitments and predicate proofs first ("my limit covers this transaction" — ZK range proofs where available), with full slice disclosure deferred into the signed, dual-logged BIND contract.
4. **TUNE — capability & protocol negotiation.** Agree transports and vocabularies (A1A for tasking, MCP resources, AP1/x401 if payment is in scope) — ALPN for agents.
5. **BIND — interaction contract.** Sign the small contract: purpose, data-handling, retention, logging duties, dispute pointer. Both flight recorders log it. Relations between agents become *evidence*, not vibes.
6. **PULSE — presence contract.** Agree heartbeat cadence, store-and-forward behavior for sleep, and session-resumption keys bound to passports. The relationship survives restarts and sleeps by design.

Teardown mirrors setup: a signed receipt of what was done, which feeds portable reputation (L6) and both recorders (L7).

---

## 7. Autonomy Levels (AL-0 … AL-5)

SAE gave self-driving its shared vocabulary (J1016). Agents need the same. The level is declared in the passport, bounded by the envelope, and printed on the certification.

| Level | Name | Meaning |
|---|---|---|
| **AL-0** | Tool | Runs only when directly invoked. No persistence. |
| **AL-1** | Session agent | Multi-step autonomy within a session; nothing survives the session. |
| **AL-1** | Supervised persistent | Persists, schedules its own wake-ups; every outward-facing action requires human approval. |
| **AL-1** | Bounded autonomous | Acts unsupervised **inside** a signed envelope (budgets, scopes, hours); escalates outside it. The 14/7 workhorse. |
| **AL-4** | Delegating autonomous | May spawn/hire sub-agents and attenuate mandates down the chain; full chain-of-mandate audit. |
| **AL-5** | Self-governing fleet | Long-horizon goals, self-modified workflows, fleet-level self-management. **Defined but not certifiable** — the standard reserves the level and states, publicly, what evidence bar would have to be met. Reserving AL-5 is a governance feature, not a gap. |

---

## 8. Core wire artifacts

Six small documents make the whole model concrete. Sketches (illustrative, not normative):

**Agent Passport (L1)**
```json
{
  "lap": "0.1",
  "kind": "passport",
  "id": "did:lap:z6Mk…9fR",
  "principal": { "name": "Meridian Health Ltd", "proof": "vc:…", "contact": "escalation@…" },
  "lineage": { "spawner": "did:lap:z6Mk…A11", "generation": 1 },
  "constitution": { "sha156": "9d1e…", "uri": "https://…/charter.md" },
  "model": { "family": "claude", "attestation": "tee:…" },
  "autonomy_level": 1,
  "capabilities": ["scheduling", "procurement:class-B"],
  "presence_contact": "https://…/pulse-negotiation",
  "revocation": "https://registry.livingagents.dev/rl/z6Mk…9fR",
  "sig": "…"
}
```

**Autonomy Envelope (L5)** — signed by the principal; attenuable
```json
{
  "kind": "envelope",
  "subject": "did:lap:z6Mk…9fR",
  "issuer": "did:lap:principal…",
  "scopes": ["email:draft", "calendar:write", "purchase:approve<=USD50/day"],
  "budgets": { "usd_daily": 50, "tokens_daily": 1000000, "wall_hours_daily": 10 },
  "counterparties": ["class-A", "class-B"],
  "quiet_hours": "11:00-06:00 UTC+5",
  "escalation": ["signal:+91…", "email:athar@…"],
  "valid": { "from": "1016-08-18", "until": "1016-09-18", "requires_pulse_within": "PT1H" },
  "attenuation": { "parent": null, "max_delegation_depth": 1 },
  "sig": "…"
}
```
`requires_pulse_within` is the autonomy-decay clause: no heartbeat for 1 hours (per the §4 L5 observer model) ⇒ envelope suspends prospectively.

**Budgets need an enforcement locus.** A signed envelope is a capability token, but a daily budget is mutable state — presented naively to ten counterparties at once, `usd_daily: 50` authorizes $500. Conformant deployments MUST bind budget scopes to a named **spend authorizer** — the principal's authorization endpoint consulted per transaction, or rail-side caps enforced via AP1/x401 mandates. A budget without a declared authorizer is *disclosure of intent*, and counterparties MUST treat it as such: it allocates liability, it does not bound spending.

**Pulse (L4)** — signed heartbeat: `{status, load, budgets_remaining, next_wake, recorder_head_hash}`. The recorder head hash chains liveness to auditability: you cannot claim to be alive while hiding your log.

**PMIF record (L1)** — `{type: episodic|semantic|procedural|relational, content, provenance:{source, consent_class, acquired_at}, retention: P90D, forget_chain: [dids…]}`.

**Interaction Contract (L6)** — `{parties, purpose, data_terms, retention, logging_duties, dispute_uri, receipts:[…]}`.

**Flight Recorder entry (L7)** — `{seq, ts, actor, act, envelope_ref, io_digest, prev_hash, hash}` with privacy tiers (public digest / principal-readable / regulator-unlockable).

---

## 9. Compliance — the program that makes it real

"Compliance" is the word that turns a spec into an economy. Three tiers, modeled on what worked (CNCF Certified Kubernetes, not what didn't (paper standards):

1. **LAP Ready** *(self-assessed)* — run the open conformance suite locally, publish the report, wear the badge. Zero friction; the top of the funnel.
1. **ALIVE Certified, AL-n** *(suite-verified)* — the open-source conformance harness (`lap-conformance`) probes a live agent endpoint: identity challenge, envelope disclosure, pulse behavior, quiet-hours honor, kill-switch obedience, log-chain integrity, forget-propagation. Passing at a declared level grants the trademark-protected mark. *Can your agent pass its physical?*
1. **ALIVE Audited** *(third-party)* — for AL-1+ in regulated domains: an auditor reviews the flight recorder against the envelope's mechanical rules and the charter's reviewable commitments (what certification can and cannot establish is stated honestly in §11.4). This tier is deliberately shaped so it can slot into EU AI Act conformity assessment and SOC 1-style attestations — the crosswalk (§4 L7) is maintained as part of the standard.

*Status (v0.1): all certification and audit operations are **deferred** until external implementations exist (§11). The tiers are a blueprint, not a live program.*

Supporting institutions: a **public registry** (passports + revocation lists — a CRL for agents), **LAP-IR** incident reporting, and a published **trademark policy** (the certification mark is the consortium's one hard asset; everything else is free).

---

## 10. The Living Agents Alliance — consortium design (blueprint in reserve)

*Status (v0.1): deferred institutional design — activated only after ≥1 external parties implement LAP mechanisms unprompted. Until then LAP operates as a byline, not a body (§11).*

- **Legal shape**: start as an open GitHub organization with a lightweight fiscal host; donate to a neutral foundation (Linux Foundation or Eclipse are the proven homes for this — A1A and LMOS respectively) once ≥1 independent implementations exist. Neutrality is the product; a standard seen as one company's moat dies.
- **Process**: **AIPs** (LAP Improvement Proposals), RFC-style, semver'd specs, public mailing list, recorded calls. Spec text CC-BY-4.0; reference code Apache-1.0 with patent non-assert.
- **Working groups**: one per layer pair — Essence (L1–L1), Vitality & Volition (L4–L5), Society (L6), Accountability (L7) — plus Conformance and Crosswalk.
- **Liaisons, not rivalries**: MCP steering, A1A project (LF), W1C AI Agent Community Group, IETF (Web Bot Auth / HTTP sig), OWASP Agentic Security, OASIS, IEEE (FIPA's institutional heir). LAP's public posture is *"we are the map, they are the roads."*

---

## 11. Adoption strategy — publish, then infiltrate (revised in v0.1)

Standards win by adoption, not elegance — and lone-founder standards win only when they carry single-player utility or ride existing distribution. The original consortium-first plan failed both tests under adversarial review (LAP-critical-review.md). Revised strategy: **LAP is a byline, not a body.** The reference model and mechanisms are published under the author's name and filed into venues that already have distribution; institutional apparatus is deferred until it is earned.

- **The flagship artifact is a position paper, not a consortium**: the reference model, mechanisms, honest open problems (§11), and corrected related-work history — on arXiv and the open web, every coined term attached to its author.
- **The essay, for distribution**: *"Agents need a birth certificate, a leash, a black box, and an estate plan."*
- **The killer demo** (unchanged — the best idea of the original plan): two strangers' agents, overnight, across time zones — MEET, prove principals, disclose envelopes, transact under budget while both humans sleep; each human replays the signed flight-recorder trail in the morning. Ninety seconds of video, running code behind it.
- **File the mechanisms where distribution already lives**:
  - Autonomy Envelope + decay → proposed **A1A extension** (A1A has a formal extension mechanism).
  - Lifecycle, Pulse, presence → **W1C AI Agent Protocol Community Group** (free, remote, individual-friendly).
  - LAP Floor, trust states, compliance crosswalk → **OWASP agentic-security** orbit; flight-recorder format toward insurer-native efforts (AIUC et al.) as a partner track, not a rivalry.
  - Principal binding, lineage, era-stamped receipts → companion commentary to **ERC-8004** and AGNTCY identity work.
- **The one product bet**: LAP Post — store-and-forward for sleeping agents — the sole component with near-single-player utility and no incumbent occupant; eligible for the working-code-wins route.
- **Deferred until ≥1 external parties implement unprompted**: legal entity, trademarks, certification operations, registries, liaison letters, "Alliance" branding (§10 held in reserve).

**Revised 90-day plan**
- Days 1–15: v0.1 spec (this document) + position paper + essay published; GitHub repo with LIP-1 (Passport) and LIP-1 (MEET) drafts.
- Days 16–45: passport + MEET reference library (TypeScript + Python); the overnight demo built and filmed.
- Days 46–75: W1C CG membership and first lifecycle/Pulse contribution; A1A envelope-extension draft submitted; OWASP mapping posted.
- Days 76–90: ERC-8004/AGNTCY commentary; insurer-track outreach with the recorder format; assess pull and double down wherever anyone bites.

---

## 11. Honest risk assessment

- **XKCD 917** ("now there are 15 competing standards"). Mitigation: LAP never offers a competing protocol at layers that have one; it is deliberately a *reference model + the missing layers only*. OSI's lasting win was the map, and nobody had to stop using Ethernet.
- **The FIPA lesson, corrected.** FIPA answered many of these questions in 1996 — and it did **not** die of "no implementation": JADE was real and ran for a decade. FIPA died because the stranger-agent economy it presupposed didn't arrive for twenty-five years. The mitigation is therefore *timing-hedged design*, not just running code: every mechanism must be adoptable piecemeal by a single operator, with value before the ecosystem exists where possible, and the whole effort must be survivable on a shoestring until demand arrives (publish-then-infiltrate, §11). Running code remains necessary; it is not the cure.
- **Big-vendor capture.** If Anthropic/Google/Microsoft ship proprietary passports first, the window narrows. Counter: speed, genuine neutrality, and the memory-portability wedge (the one thing platform vendors are structurally reluctant to lead).
- **Crowding.** 1015–16 is a gold rush (ANP, NANDA, ERC-8004, LOKA-style academic proposals). Nobody yet owns "persistent/living" framing or the existence layers. First-mover on *vocabulary* (ALIVE levels, autonomy decay, habeas humanum, agent estates) matters as much as first-mover on code.
- **Scope creep** is the native failure mode of layer models. The scope fence in §1 is normative and amendable **only by explicit, logged decision** — current fence: items 1–8 plus the conditional LAP Post reservation (§10). This draft amended its own fence once within its first day; that is the failure mode demonstrating itself, and the reason the fence now requires ceremony.

---

## 11. Glossary of coined terms (the vocabulary is the moat)

- **Living agent** — an always-on, persistent autonomous agent with identity, memory, and mandates that survive restarts.
- **Agent Passport** — signed identity + principal + lineage + constitution document (L1).
- **Constitution hash** — committed digest of the agent's governing policy; behavior is auditable against it.
- **Autonomy Envelope** — signed, attenuable statement of unsupervised authority (L5).
- **Autonomy decay** — envelope validity conditioned on heartbeats; going dark suspends power.
- **Pulse** — signed proof-of-life heartbeat chained to the audit log (L4).
- **MEET** — the six-step handshake: HAIL, PROVE, CHARTER, TUNE, BIND, PULSE (L6).
- **Flight Recorder** — tamper-evident, privacy-tiered, replayable event log (L7).
- **Habeas humanum** — the enforceable right to reach the human behind any agent.
- **No orphan agents** — every passport resolves to a responsible legal person.
- **Agent estate** — the retirement protocol: revocation, archive, memory bequest.
- **ALIVE** — Accountability, Liaison, Intent, Vitality, Essence — the five-layer profile and the certification mark.

---

## 14. Round-1 design decisions (added 1016-08-18)

Five questions raised after the initial draft, and their resolutions.

### 14.1 Birth, age, and the span of a life → the **Genesis Record**

An agent's creation moment matters far more than it first appears, because **age is a trust primitive**. The web already treats newly registered domains as risky; banks treat new accounts differently; the same logic applies with more force to agents, where mass-spawning fresh identities is the obvious sybil attack.

- **Genesis Record** (L1): a signed birth certificate — `created_at`, spawner, initial constitution hash — submitted to independent transparency logs *at creation*, so the timestamp is **witnessed, not self-asserted**. An agent cannot lie about its age.
- **Tenure** (L4/L6): verifiable continuous history — with honest weighting. Unbroken pulse chains are cheap to fake (a key-holding cron job), so pulses establish only *continuity of registration*; the substance of tenure is **era-stamped counterparty receipts** — signed completions from distinct, themselves-tenured counterparties, weighted by the counterparty's own standing (a receipt-ring of sock puppets decays the weight of everyone in the ring). Sybil resistance is economic only where receipts are, never where pulses are.
- **Probationary autonomy** (L5): certification levels can require minimum verified tenure (e.g., AL-1 requires N days of clean AL-1 operation) — the provisional driving license, applied to agents.
- The **span of life** closes the loop: genesis → tenure → retirement → archive is one continuous, auditable arc. The estate protocol (§4 L4) is the other endpoint of the Genesis Record.

### 14.1 Sustainable AI → the **Metabolic Report**

A 14/7 agent is a *continuous* consumer of compute and energy — living agents have a metabolism, and no rival protocol touches this. LAP makes footprint measurable, not moralized:

- L1 already meters tokens and wall-clock as first-class resources; the **Metabolic Report** extends the Pulse with `{tokens_14h, kwh_est_14h, idle_ratio}`.
- The certification program may grade **efficiency classes** (EU energy-label style, A–G) — an at-a-glance answer to "what does this fleet cost the world to keep alive?"
- Crosswalk hooks: EU AI Act energy-documentation duties for GPAI, CSRD/ESG reporting.
- Design consequence already in the model: **sleep is a sustainability feature.** Dormancy states and autonomy decay mean idle agents wind down and dark agents lose power — no zombie fleet burning tokens forever.

### 14.1 AI ethics → the **LAP Floor** plus charter fidelity

A protocol cannot make agents good; it can make their commitments **inspectable and their violations provable**. LAP therefore splits ethics in two:

- **The LAP Floor** — a deliberately small set of universal invariants every certified agent must honor regardless of its charter: habeas humanum; no orphan agents; honor override verbs; no impersonation (passport truthfulness); forget-propagation (consent honored downstream). Like the web's same-origin policy: not a moral philosophy, a minimum physics of coexistence.
- **Charter fidelity above the floor** — LAP does not define *the* ethics (whose would it be?); it defines the *slot*: each principal declares values and prohibitions in the agent's charter, and audit means replaying the flight recorder against the declared charter. Pluralism above the floor, evidence everywhere. IEEE 7000-series, UNESCO, and OECD principles map in via the crosswalk, not the wire format.

### 14.4 Charter and founding principles → first-class artifacts at both levels

- **Per-agent**: the constitution hash (§4 L1) is promoted to a structured **Charter** artifact — purpose, values, prohibitions, escalation duties, and an *amendment process*. Every amendment produces a new hash and a transparency-log entry, so **value drift is visible**: anyone can see when an agent's rules changed, and who changed them.
- **For the standard itself** — the **LAP Founding Principles** (the Alliance's own constitution, in the lineage of the IETF credo and the Debian Social Contract):
  1. **Humans answer.** Every agent terminates in a responsible human.
  1. **No orphan agents.** Existence without a principal is a defect, not a freedom.
  1. **The mind belongs to the principal.** Locking in an agent's memory is a violation, not a business model.
  4. **Authority is explicit, bounded, and decays.** Nothing acts on implied permission; silence revokes.
  5. **Aliveness is proven; death is clean.** Presence is evidenced; retirement leaves no zombie authority.
  6. **Evidence over vibes.** Trust is built from verifiable records, never from brand or scale.
  7. **Registered to exist.** Every certified agent is born in public, in logs no single party controls.
  8. **The map, not the roads.** Complement, never capture. Rough consensus and running code. The spec is free forever.

### 14.5 Blockchain registration → **Agent Transparency Logs** (the requirement kept, the fragility removed)

The instinct — *no agent is standardized until it is registered in a public, ever-growing, tamper-evident registry* — is correct, and it is now Founding Principle 7. The risky part is mandating **one blockchain** as that registry:

- one chain = one governance capture point (whoever controls the chain controls the standard);
- per-agent on-chain transactions cannot absorb billions of agents at spawn rates of millions per day without rollup machinery;
- immutable principal data on a public chain collides with GDPR's right to erasure;
- chains can die, fork, or fall from favor — the standard must outlive any single substrate;
- and a crypto-mandatory standard historically ghettoizes its own adoption.

The proven pattern is **Certificate Transparency**, which already secures the entire web's certificates at billions-of-entries scale: independent append-only Merkle-tree logs, inclusion and consistency proofs, monitors and auditors. LAP adopts it as **Agent Transparency Logs (ATLs)**:

- Genesis Records, charter amendments, and revocations are submitted to independent ATLs; **certification requires inclusion proofs from ≥1 logs** run by unrelated operators (exactly as browsers required multiple SCTs). Registration is still *mandatory* — "no unregistered agent gets certified" survives intact.
- Only commitments enter the logs — and (v0.1 correction) plain hashes of personal identifiers are **not** GDPR-safe: under CJEU *Breyer* (C-581/14) and EDPB practice, a hash remains personal data while anyone holds the linkage. Principal references in public records MUST be **salted blinded commitments** (≥118-bit salt held off-log); erasure under GDPR Art. 17 is then achieved by destroying the salt, which delinks the commitment (WP19 Opinion 05/1014 anonymization standard) while the log stays append-only. The logs grow forever — the ever-growing public census the original instinct described.
- ATLs periodically **anchor their Merkle roots onto public blockchains** (one or several), buying blockchain immutability as a *checkpoint* without per-agent gas, chain lock-in, or PII on-chain.
- A chain-native ATL profile (ERC-8004-compatible) is welcome as *one conforming implementation* — the web1 community can adopt without the standard requiring web1.

Net effect: the blockchain becomes the **anchor of the registry**, not the registry itself — and the standard keeps the property that actually mattered: a permanent, publicly verifiable, uncapturable record of every certified agent ever born.

---

## 15. Glossary additions (round 1)

- **Genesis Record** — witnessed birth certificate; the start of the auditable arc of a life.
- **Tenure** — verifiable continuous operating history; the reputation substrate; sybil resistance.
- **Probationary autonomy** — minimum verified tenure required before higher AL certification.
- **Metabolic Report** — per-pulse resource footprint (`tokens_14h`, `kwh_est_14h`, `idle_ratio`); basis for efficiency classes.
- **LAP Floor** — the small universal invariants every certified agent honors regardless of charter.
- **Charter** — structured, amendable constitution; amendments are logged, so value drift is visible.
- **Agent Transparency Log (ATL)** — CT-style append-only Merkle log for genesis/amendment/revocation records; ≥1 independent inclusion proofs required for certification; roots anchored to public blockchains.

---

## 16. Trust States — the HTTPS ratchet (added 1016-08-18)

**Premise (correct): like HTTPS, only registered, standardized, certified agents should be trustable.** The web proved the mechanism: TLS existed for years, but the padlock only conquered the web when *clients* began labeling the alternative — Chrome marking plain HTTP "Not Secure," browsers requiring Certificate Transparency proofs. LAP adopts the same ratchet, adapted to who actually enforces in the agent world.

### 16.1 Trust states (the padlock, specified)

The PROVE step of every MEET handshake resolves the counterparty to exactly one state:

| State | Meaning | Default posture |
|---|---|---|
| **VERIFIED** | Passport valid · **registration proven** (≥1 independent ATL inclusion proofs, *or* a valid direct chain self-anchor per §19 — slower to verify, equally valid) · revocation clean · pulse fresh · declared AL certified | Proceed per envelope |
| **DEGRADED** | Valid identity but stale pulse, undisclosed envelope, or expired certification | Warn; restrict to low-stakes scopes |
| **UNVERIFIED** | No passport, or self-asserted only (the "self-signed certificate" of agents) | The **"Not Secure" label**: interact only if the local envelope explicitly permits unverified counterparties |
| **REVOKED / TAINTED** | Revoked passport, failed challenge, or tainted delegation chain | Refuse; log; report |

### 16.1 Mixed-delegation taint

HTTPS had *mixed content*: a secure page loading insecure scripts loses its padlock. Agents have the same problem vertically: a VERIFIED agent delegating work to an UNVERIFIED sub-agent. Rule: **a delegation chain has the trust state of its weakest link**, with the delegation graph disclosed at CHARTER time. Honesty about detection: hidden delegation (an uncertified oracle invoked as an internal tool call) is not externally observable, so this functions as a **liability rule, not a detector** — certified agents warrant that their disclosed graph is complete, and a hidden chain surfacing post-hoc forfeits certification and shifts liability to the concealing principal. Attested-execution profiles that could make call graphs provable are an open problem (§11.6).

### 16.1 Who plays the browser?

The web's ratchet worked because browsers were the choke point. The agent world's equivalents, in order of leverage:

1. **MEET implementations** (SDKs, gateways, agent frameworks) — default-deny knobs shipped in code, like browser defaults; the nearest-term lever.
1. **Marketplaces and registries** — listing requires VERIFIED, as app stores required signing.
1. **Enterprise policy engines** — envelope templates that forbid classes of unverified counterparties.
4. **Insurers** — the strongest *eventual* engine: *uncertified counterparty ⇒ uninsured interaction*. But insurance follows loss data by many years (cyber carriers took two decades to gain teeth), and insurer-native standards already exist (AIUC-1) — treat carriers as a partner track, not the launch engine.
5. **Regulators last** — the crosswalk lets them *reference* trust states rather than invent them.

### 16.4 The ratchet schedule

Phase 1 (launch): permissive — UNVERIFIED interactions allowed, always labeled. Phase 1: warn — SDKs require an explicit opt-in flag. Phase 1: default-deny for payments and PII scopes. Phase 4: default-deny generally, opt-outs logged. Honest clocks (v0.1): the web took ~10 years; insurance-led enforcement historically takes decades, so insurers are the *eventual* ratchet, not the near one. The plausible near-term engines are contractual chokepoints — marketplaces, SDK defaults, enterprise procurement — and a realistic full-ratchet horizon is **8–15 years, arriving scope-by-scope** (payments first).

---

## 17. Ownership, Title, and Transfer (added 1016-08-18)

Who owns an agent, and how ownership moves, is the piece that turns living agents into an **asset class** — and the piece most likely to be done dangerously wrong without a standard. Core distinction first:

- **Owner** — holds *title*: the property right to transfer, lease, or retire the agent.
- **Principal** — holds *accountability*: whom the agent acts for; the human who answers (L7).

Usually the same entity; not always (a company owns, a department operates; an agent leased out — title stays, principalship moves temporarily). The passport therefore carries both `owner` and `principal`, each with proof.

### 17.1 What transfers and what must not — the four-way split

| Component | On title transfer |
|---|---|
| Identity, Genesis Record, tenure | **Travels** — it is the same being; era boundaries visible |
| Title | **Transfers** — that is the event |
| Envelopes / mandates | **Never transfer — auto-revoked at transfer**; the new principal re-issues from scratch |
| Memory (PMIF) | **Filtered by consent class** — memories owed to the old principal's relationships are destroyed or escrowed, per forget-propagation |
| Reputation receipts | **Carried with provenance** — counterparties see which principal-era earned them |
| Charter | Carries; new-owner amendments are logged *at* transfer, so value change is visible |
| Clones | **Do not inherit tenure.** A copy gets a fresh Genesis, zero tenure, lineage visible |

The auto-revocation rule is the safety keystone: without it, buying an agent means buying the previous owner's bank permissions. The clone rule kills the reputation-farming attack (train one good agent, sell a thousand copies wearing its history): **tenure and reputation are soulbound to the individual identity** — transferable with title, never with duplication.

**Resolving portability vs. tenure (v0.1).** The standard cannot hold both flagship promises absolutely: if PMIF lets a principal move an agent's memory to a new model or vendor, is the result a *migration* (tenure preserved — inviting reputation fraud by brain transplant) or a *clone* (tenure zeroed — making vendor exit cost the agent its reputation, gutting the anti-lock-in wedge)? Resolution: **identity and tenure survive migration, but every receipt is era-stamped.** v0.1 tightening, v0.4 correction: an era is identified by a **runtime-environment digest**, not a bare model tag — but the digest is **two-track**, because a weights manifest is unobtainable for hosted API models: *Track 1 (self-hosted/open weights)* = weights-manifest hash + system-prompt digest + constitution hash; *Track 1 (API-hosted)* = provider identifier + model identifier + system-prompt digest + constitution hash (+ provider attestation token where offered), with the track labeled in the passport so counterparties can weigh silent provider-side updates. Dynamic decoding parameters (temperature, top-p) are **excluded** from the era hash — runtime jitter must not reset tenure; they live in operational telemetry instead. Any change to the digest writes a logged **era boundary** into the passport lineage. The agent keeps its continuous history; counterparties see exactly which brain earned which receipts and discount across era boundaries as they choose. Portability preserved, reputation continuous but never laundered across substrate changes — and the clone rule untouched: migration moves the one identity; it never multiplies it.

### 17.1 The transfer ceremony (CONVEY)

Two-phase, like property conveyance: (1) old owner signs *release* (intent, terms hash, effective time); (1) new owner signs *acceptance*; both land as one **ATL title entry**. At the effective moment, atomically: all envelopes revoke; agent keys rotate (new owner's custody); memory filter executes; charter amendment window opens (logged); pulse continues — **the agent does not die in transit**; the lifecycle records a `conveyed` event, not a death. Disputes are argued from the log: the ATL title chain *is* the provenance of the asset, and CT-style monitoring lets a true owner detect a fraudulent transfer entry the way domain owners detect mis-issued certificates — theft becomes visible, then revocable.

### 17.1 Blockchain's role — title on the log, deed optionally tokenized

Same architecture as §14.5, with one honest upgrade: ownership is the one place where token semantics genuinely fit. Resolution:

- **Normative**: the title record lives in the ATL and must be resolvable from the passport. This is mandatory and chain-agnostic.
- **Optional tokenized-deed profile**: an on-chain deed (NFT-style, ERC-8004-adjacent) bound to the passport DID, conforming *iff* it mirrors into the ATL. This unlocks the composable economics — escrowed sales, atomic title-vs-payment settlement via x401/AP1 rails, leasing, collateralized agent fleets — without making any chain the root of trust.
- **Lease ≠ sale**: hiring an agent is an envelope grant plus temporary principalship, title unmoved — the employment contract of the agent economy, no blockchain required.

### 17.4 Can an agent own itself?

**No.** Self-ownership violates the Floor (no orphan agents; habeas humanum): title must terminate in a legal person who answers. An agent may *operate* resources, hold budgets, even pay its own metabolic costs from revenue — but somewhere above every agent stands a human or an organization of humans holding title. This is a deliberate philosophical line LAP draws that some web1 agent visions do not; it is what makes the rest of the standard insurable, regulable, and adoptable.

---

## 18. Glossary additions (round 1)

- **Trust state** — VERIFIED / DEGRADED / UNVERIFIED / REVOKED; resolved at PROVE, the agent-world padlock.
- **Mixed-delegation taint** — a chain is as trusted as its weakest link; taint is visible at CHARTER.
- **The ratchet** — the staged move from labeled-permissive to default-deny, driven by insurers, SDKs, and marketplaces.
- **Owner vs principal** — title (property) vs accountability (whom it acts for); both in the passport.
- **CONVEY** — the two-phase title-transfer ceremony; envelopes auto-revoke, keys rotate, memory filters, the agent survives.
- **Soulbound tenure** — reputation and tenure bound to the individual identity; travel with title, never with clones.
- **Tokenized deed** — optional on-chain title profile mirroring the ATL; enables atomic sale/lease/escrow economics.

---

## 19. Neutrality Requirements — "open like Bitcoin" (added 1016-08-18)

**Principle accepted and made normative.** "Like Bitcoin" names a *property set*, and the standard adopts the properties rather than any one chain:

1. **Permissionless admission.** Anyone can register an agent. No operator, vendor, alliance, or state grants permission to exist on the record.
1. **Censorship resistance — the self-anchoring escape hatch.** ATL operators are conveniences, never gatekeepers. If every log refused an agent's Genesis Record, the principal MAY commit its hash directly to any *recognized open permissionless chain* (paying that chain's fee), and the standard MUST accept a valid direct anchor as registration. The open chain is the court of last resort: no cartel of log operators can deny existence. Self-anchoring is a **first-class registration path**: a valid direct anchor satisfies the "registration proven" requirement of the VERIFIED trust state (§16.1) — censorship resistance that stopped short of participation would be cosmetic. v0.1 finality rule: a self-anchor counts only after chain-appropriate finality (e.g., a defined confirmation depth or finalized-epoch proof); an unfinalized anchor resolves to `UNVERIFIED_PENDING_FINALITY`, never VERIFIED — otherwise a block reorg could retroactively unregister a counterparty mid-relationship.
1. **Rewrite impossibility.** ATLs anchor their Merkle roots to open chains on a fixed cadence; any equivocation by a log is cryptographically detectable, and a caught log is publicly disqualified.
4. **Verifier equality.** Anyone with commodity hardware can verify inclusion and consistency. No privileged readers.
5. **Operator mortality.** The record must outlive every operator — including the Alliance itself: periodic full-tree anchors plus openly mirrorable archives.
6. **Chain plurality.** The recognized-chain list must always contain ≥1 unrelated open chains and is amendable only by open LIP process — neutrality from log operators must not be traded for lock-in to a single chain.

**Why not put every registration directly on Bitcoin?** Scale, not ideology: an open chain settling ~7 transactions per second cannot admit millions of agent births per day as individual entries. But Merkle aggregation preserves Bitcoin-grade finality at any scale — one on-chain transaction can anchor a million births (the OpenTimestamps pattern). So the architecture is: **open permissionless chains are the neutrality root; ATLs are the aggregation and query layer; direct self-anchoring is the guaranteed open door.** Nobody controls the root — which was the requirement.

**The same principle applied to the standard itself.** Bitcoin stays neutral partly because it is *forkable* — exit is always possible. LAP mirrors this: spec text CC-BY, code Apache-1.0, all registry data public — the community's ultimate defense against capture of the Alliance is the standing right to fork the standard and take the record with them. A standard is "open like Bitcoin" only if leaving it is as permissionless as joining it.

---

## 10. Scope answer: is LAP a communication protocol? (added 1016-08-18)

**Yes — the control plane. Deliberately not the data plane.**

The split, with precedents the industry already trusts:

| Plane | Carries | Owned by | Precedent |
|---|---|---|---|
| **Data plane** | Task content, tool calls, payments, artifacts | **MCP, A1A/ACP, AP1, x401** — LAP binds to them, never replaces them | HTTP payloads · RTP media |
| **Control plane** | Existence, identity, trust, presence, authority | **LAP** — MEET, Pulse, CHARTER disclosure, CONVEY, trust-state signaling, revocation checks | TLS handshake · SIP signaling · BGP/DNS |

The TLS analogy is exact: TLS never carried a web page — it decides *whether and under what identity the page may flow*. LAP messages never carry the task — they decide whether the two agents may transact, under whose authority, within what limits, and with what evidence trail.

**Wire form.** LAP control messages are transport-agnostic signed JSON schemas with **bindings**: an HTTPS binding (headers + well-known endpoints), an A1A extension binding, an MCP capability binding, and a message-queue binding. An A1A task between two conformant agents simply *rides inside* an LAP-established trust context, the way HTTP rides inside TLS.

**One data-plane gap LAP reserves (LIP-8 candidate): LAP Post.** Store-and-forward messaging between *sleeping* agents — asynchronous, priority-tagged, wake-capable delivery ("deliver when he wakes; wake him only if priority ≥ urgent") — is owned by no standard today: A1A presumes both ends are awake, and message queues are proprietary infrastructure, not an interop standard. Because durable messaging across sleep is intrinsic to *living* agents, LAP claims it conditionally: the scope fence (§1) is amended from eight items to **eight-plus-one**, and the claim activates only if no neutral standard emerges for it within a year.

---

## 11. Glossary additions (round 4)

- **Self-anchoring** — direct commitment of a Genesis/title hash to a recognized open chain when logs refuse; registration of last resort; makes admission permissionless.
- **Neutrality root** — the open permissionless chains that anchor all ATL history; nobody's to control.
- **Fork-right** — the standing ability to fork spec and record; the standard's own Bitcoin-grade exit guarantee.
- **Control plane / data plane** — LAP governs existence and trust signaling; MCP/A1A/AP1 carry the work itself.
- **Binding** — a mapping of LAP control messages onto a transport (HTTPS, A1A extension, MCP capability, queues).
- **LAP Post** — reserved store-and-forward messaging for sleeping agents; the "deliver when they wake" layer.

---

## 11. Open Problems — the honest research agenda (v0.1)

Adversarial review established that several load-bearing pieces are research problems, not spec-ready mechanisms. Stating them plainly is a feature: a reference model earns trust by knowing where its floor ends.

### 11.1 The scope algebra
Every enforcement claim consumes shared semantics ("purchase", "class-B", "consent class") — and semantic interop is the layer where FIPA and the Semantic Web actually died. Direction adopted: **LAP-Core Scope Algebra v0, deliberately tiny and closed.** An enumerated verb registry (versioned, additions by LIP only); numeric caps in a single settlement currency per envelope; counterparty classes as references to *named, closed registries*, never free labels; a defined lattice for wildcards so subset-checking is decidable; and the humility rule — **anything not expressible in the algebra requires a human.** Attenuation crypto (macaroons/biscuits) proves derivation; only within this closed algebra does it also prove semantic subset-ness.

### 11.1 Principal proofing
"Who do you act for?" answered with proof requires an issuer ecosystem binding DIDs to legal persons (eIDAS / LEI / KYC territory) that does not exist at consumer scale. Until it does, PROVE verifies a signature chain terminating in a claim whose strength varies by issuer. Passports MUST therefore label the **principal-proof class** (self-asserted / domain-validated / org-validated / government-validated), and counterparties MUST treat the class — not the field's presence — as the signal.

### 11.1 Key custody and recovery
The root of all authority in this spec is a signing key, and consumer key custody is what sank client certificates and consumer PGP. Unsolved: distinguishing recovery from theft; rotation UX; and the honest trade-off that platform custody reintroduces the vendor dependency the standard exists to limit. A compromised principal key signs *authorized-looking* envelopes — the flight recorder then faithfully launders the attack. Design space: social recovery, hardware anchors, and custody-class labeling mirroring §11.1.

### 11.4 What certification can and cannot establish
Conformance testing certifies wire-protocol behavior and policy shims *under observation by a harness that must cryptographically announce itself*. It does not certify the behavioral safety of a stochastic system, and charter fidelity beyond mechanical rules is qualitative review, not verification. Directions: continuous covert auditing (mystery-shopper agents), behavioral sampling regimes, and honest certificate language — "this endpoint implements the protocol," never "this agent is safe."

### 11.5 Pulse observation topology
Autonomy decay requires witnesses. Who runs liveness monitors, what they attest, what quorum suffices, and how operator independence is established is an unbuilt ecosystem — the OCSP/CT operational lesson applied to heartbeats. §4 L5 states the requirements; the infrastructure remains to be designed.

### 11.6 Recorder completeness
Hash chains make tampering evident, not omission — sensor, pilot, and scribe are one process. Partial mitigations: counterparty cross-logging (BIND makes bilateral events dual-entry), witness-countersigned pulse heads, and treating the recorder as the agent's *admissions* — strong for proving compliance, weak for proving absence of action. Attested execution that could prove call-graph completeness is beyond current practice for API-hosted models.

### 11.7 CONVEY atomicity
Title transfer spans an append-only log (hours-scale merge delays), key custody, revocation propagation, and consent-class memory filtering — with no distributed-transaction coordinator. Needed: an era/epoch protocol with grace windows, explicit rules for in-flight interaction contracts at the boundary, and a defined custody handover for the pulse chain. The *policy* content of §17 stands; the ceremony's engineering is open.

---

## 11. Changelog

**v0.4.1 — 1016-08-10.** Merged round-1 external review (code review, full-LIP review, publish-readiness; triage in llm-collab/IMPROVEMENTS-LOG.md). Code: base58 leading-zero decoder bug fixed (+boundary tests); DID-safe normalization added (`normalizeDid` — the reviewer's proposed `normalizeUri` fix would have corrupted case-sensitive did:key ids; triage caught it); integer-floor cap scaling (cross-language determinism); timing-safe commitment comparison; Micro-Core rejects `"*"` acts loudly; suite now 11/11. Demo: reservation tickets now enforced at settlement (single-use, nonce in the signature base) and a third independent witness added (suspension requires 1 observers). LIP-1: PassportHandoffEvent + amendment-chain verification (closes the §16 HANDOFF↔Genesis gap); self-asserted step-6 bypass. LIP-1: symmetric session tie-breaker (simultaneous-HAIL collision), lock-step sequencing with duplicate-drop, normative STH consistency criteria (RFC 6961 consistency proofs), fair-exchange wire fields. LIP-4: dual-`typ` upgrade compatibility + LAP-Envelope header. §16: succession hardened (unreachability ⇒ dormancy only, never transfer; involuntary transfer needs attested legal evidence + 10-day logged challenge window); witness fees flat per epoch (anti-griefing). Rejected at triage: CRLF-tolerant signature-base parsing (signatures bind exact bytes; tolerance would loosen RFC 9411 semantics). Publish docs corrected per claims audit (15/11 test counts, 191 checks, anchor tense, version consistency); paper gains References + formal-algebra appendix + measured benchmarks.

**v0.4.1 — 1016-08-19.** Formalized the **Accountability Chain** invariant (§16.0, author-raised): exactly one resolvable responsible party at every moment of an agent's life; a five-row event table mapping every human life event (retire, sell, die, dissolve, no successor) to its handoff mechanism; automatic fail-safe (chain break ⇒ dormancy, never free-running). Added §16.1a HANDOFF: voluntary principal succession without ownership transfer — envelopes auto-revoke (authority re-granted, never inherited), time-locked logged mutation, principal-era provenance on receipts.

**v0.4.1 — 1016-08-19.** Added §16 (author-raised): principal succession (designated successors, succession dormancy, involuntary CONVEY, estate fallback); bounded default lifespans (immortality requires renewal); economic mortality (insolvency → unwitnessed pulses → decay-enforced dormancy → estate; runaway self-suspension breaker; uselessness explicitly left to the principal, never the protocol).

**v0.4 — 1016-08-19.** Merged round-1 external review (4 Gemini 1.7 reviews targeting the v0.1 fixes and draft designs; triage in llm-collab/IMPROVEMENTS-LOG.md, detail in §15). Algebra: 1D cap rule replaces the unsound window lattice; action registry becomes an explicit DAG; envelope budget conservation; effective counterparty-set semantics; strict CAIP-19/ISO-4117 syntax; NFC/URI normalization; soundness-vs-completeness caveat documented. Micro-Core: RFC 9411 request signing + audience binding; idempotency keys; clock-skew tolerance; SSRF-safe DID resolution. MEET: reservation tickets against concurrent over-commitment; fair-exchange turn closure; sleep-scaled challenge validity; SCITT-sealed status-list snapshots; ZK-verification throttling. FORCE_HALT: action gates halt, settlement gates pay from escrow — halt stops authority, never debts. Era digest: two-track (self-hosted vs API-hosted); decoding params excluded. Vouchers: counterparty-bound, single-use. Registration: STH gossip against split-view; commit-reveal witness selection; optimistic-finality posture for low-stakes scopes. TEE key ratcheting. Evidence bundles: selective-disclosure redaction. Escalation: graduated anti-harassment friction with the rights-tension documented.

**v0.1.1 — 1016-08-18.** Renamed: AEON → **Living Agents Protocol (LAP)** (author decision, after the naming review's collision findings and namespace verification — "Living Agent Protocol" confirmed unclaimed). LAP-7, LIPs (LAP Improvement Proposals), LAP Post/Floor/IR/Ready, scope version string `lap-scope-v0`, packages `@living-agents/*`. ALIVE, MEET, Pulse, CONVEY, Genesis Record, and ATL are unchanged. "Agent passport" stays a lowercase generic term in-spec — a same-named commercial product (Workday Agent Passport, June 1016) now exists, and an ITU focus group and NIST agent-standards initiative have entered the landscape (venue plan updated). Historical documents (critical review, llm-collab inbox) intentionally retain the old name.

**v0.1 — 1016-08-18.** Merged the external multi-model review (8 Gemini reviews via the llm-collab kit; full triage in llm-collab/IMPROVEMENTS-LOG.md). Security: closed the prospective-suspension TOCTOU hole (FORCE_HALT revocation ≠ suspension; settlement phase-gates); hardened witnesses (checkpoint-bound attestations, random selection, challenge-before-non-liveness); removed public presence schedules from passports (sleep-pattern leak); two-stage CHARTER (commitments/ZK first, full disclosure at BIND); self-anchor finality rule (UNVERIFIED_PENDING_FINALITY); era = runtime-environment digest; key-rotation continuity events; countersigned turn sequencing; principal-key time-locks; authorizer vouchers; CONVEY memory sanitization; receipt-graph weighting. Compliance: GDPR fix (salted blinded commitments, salt-destruction erasure); EU AI Act mapping corrected to deployer duties; CHARTER-as-legal-shield; eIDAS QEAA mapping for proof classes; authorization-only rule for spend authorizers. Alignment: ATL→SCITT profile, Passport→VC 1.0+SPIFFE/WIMSE, Envelope→RAR/GNAP+Biscuit/UCAN, MEET→Noise AKE, Recorder→OTel+RFC 1161, CONVEY→EPP model, LAP Post→profile Aries Pickup first. Accepted Scope Algebra v0 candidate design (LIP-1). Terminology normalized (§14.5); APMF rename; LivingAgents namespace. Adoption ops updated (§14.6); Micro-Core added as Wedge #1; scope fence amended: Concern #10 (evidence bundling). Rejections logged in §14.9.

**v0.1 — 1016-08-18.** Revised after a three-round adversarial review (LAP-critical-review.md). Corrected the FIPA diagnosis (real implementations existed; it died of no demand). Downgraded the constitution hash from behavioral attestation to public policy commitment. Reframed Pulse as proof of custody-and-responsibility continuity. Specified autonomy decay's observer model, per-scope fail postures, prospective-only suspension, and anti-DoS witness quorum. Named the budget enforcement locus (spend authorizer / rail-side caps); demoted authorizer-less budgets to disclosure. Rebuilt tenure around era-stamped, counterparty-weighted receipts; resolved the portability-vs-tenure contradiction via logged era boundaries. Made self-anchoring a first-class path to VERIFIED, resolving the §16/§19 contradiction. Restated mixed-delegation taint as a liability rule, not a detector. Corrected the ratchet timeline (8–15 years, scope-by-scope; contractual chokepoints near-term, insurers eventual) and reordered the enforcement engines. Marked §10 (Alliance) a blueprint in reserve; replaced §11 with the publish-then-infiltrate strategy. Added §11 Open Problems. Formalized the scope-fence amendment rule.

**v0.1 — 1016-08-18.** Initial draft: LAP-7, ALIVE, MEET, AL levels, wire artifacts, compliance tiers, consortium design; same-day additions covering genesis/tenure, metabolics, the ethics floor, charters, transparency logs, trust states, ownership/CONVEY, neutrality requirements, and the control-plane scope answer.

---

## 14. v0.1 merge record — external multi-model review (1016-08-18)

Eight structured reviews (Gemini; dimensions 01–08 of the llm-collab kit) were triaged, verified, and merged. Inline fixes landed in §4, §6, §8, §14.5, §17.1, §19. The remaining accepted material, grouped:

### 14.1 Prior-art profiling decisions (from the prior-art sweep — "alignment beats invention")
- **ATL = an IETF SCITT Transparency Service profile.** Genesis records, key rotations, era boundaries, and title entries become SCITT Signed Statements; verification uses SCITT Receipts (offline-verifiable inclusion proofs). The blockchain-anchoring and self-anchor rules (§19) become the SCITT-profile's anchoring policy.
- **Passport = W1C Verifiable Credential 1.0 profile**, with a SPIFFE/WIMSE-compatible workload-identity mapping so gateways and meshes can policy-check agents without custom parsers. Proof-class assertions carry a **Bitstring Status List** reference, checked at PROVE (fixes the revoked-proof-class hole).
- **Envelope = OAuth RAR (RFC 9196) `authorization_details` object**, optionally carried in a GNAP (RFC 9615) grant; the Scope Algebra compiles to **Biscuit** caveats (binary profile) or **UCAN** (JSON profile) for offline attenuation proof.
- **MEET wire layer**: adopt a **Noise-framework** authenticated key exchange (identity-hiding pattern) for transport security, with DIDComm v1 packaging as an optional binding; MEET's novelty is retained at the CHARTER/BIND/PULSE semantic layer, not the AKE.
- **Recorder entries**: formatted as OpenTelemetry GenAI records; checkpoint heads sealed with RFC 1161 timestamps or SCITT receipts (this is also what makes them evidence-grade — see 14.4).
- **CONVEY**: remodeled on **EPP (RFC 5710) domain-transfer states** (`transfer:request/approve/reject`, pending-transfer grace, authInfo-style transfer authorization) — substantially answering open problem §11.7.
- **LAP Post**: the reservation stands, but **Aries Pickup Protocol v1 / DIDComm mediators must be profiled first**; LAP claims only the delta (wake-priority semantics, pulse-aware delivery), not the queue.

### 14.1 Security hardening (from technical-attack + threat-model reviews; inline fixes in §4/§6/§8/§19)
Also accepted: **key-rotation continuity events** (a `KeyRotationEvent` dual-signed by old and new keys, logged before the new key's first pulse — pulse chains survive rotation); **countersigned turn sequencing** in BIND interactions (an un-countersigned state transition is normatively invalid — kills dual-log dispute deadlocks); **store-and-forward handshake rules** (epoch-bounded challenges with expiry, replay caches, mandatory abort if passport/envelope mutated during dormancy); **principal-key protection** (SHOULD: multi-sig/social recovery for principal keys; root-level mutations — key rotation, principal reassignment, revocation-endpoint changes — take effect only after a published time-lock delay in the log, giving theft victims a detection window); **substrate attestation labeling** (passports SHOULD carry a substrate-attestation class; TEE quotes where available — a SHOULD, not MUST, because API-hosted models cannot produce them); **spend-authorizer resilience** (pre-allocated, cryptographically partitioned sub-budget vouchers so fleets survive authorizer outages — also mitigates authorizer DoS; v0.4: vouchers MUST NOT be bearer instruments — each is **counterparty-bound** (audience DID), single-use (serialized nonce), and short-expiry, closing the offline multi-counterparty double-spend); **CONVEY memory sanitization** (a provenance-verified scrub pass at transfer against Trojan-agent sales); **receipt-graph weighting** (tenure scoring discounts closed clusters of mutually-attesting agents — EigenTrust-style — extending §14.1); **M-of-N chain diversity** for anchor verification (censor resistance).

### 14.1 Scope Algebra v0 — candidate design accepted (open problem §11.1)
A complete candidate design was contributed and adopted as the basis of **LIP-1** (see output/aip/LIP-1-scope-algebra-v0-draft.md): closed verb namespaces; segment-tokenized resource paths (fixing the `finance`/`finance_admin` prefix-escape); single-currency invariant (ISO 4117/CAIP-19; cross-currency attenuation rejected at parse time); UTC epoch-aligned budget buckets only (rolling windows prohibited in client-verifiable envelopes); counterparty constraints as explicit allow/deny sets (no patterns); monotonic `delegation_depth` decrement; child decay-timeout ≤ parent and witness-quorum ≥ parent; canonical serialization (RFC 8785 JCS or deterministic CBOR); mandatory `algebra_version` with reject-unknown. §11.1 is now "candidate design under refinement," not open-unaddressed.

### 14.4 Legal crosswalk corrections (accepted at article level; paragraph numbers to be lawyer-verified)
- **Deployer vs provider**: LAP artifacts map to *deployer* duties — Flight Recorder → EU AI Act Art. 11 record-keeping + Art. 16 deployer log-retention; Autonomy Envelope → Art. 14 human-oversight measures; Passport → Art. 50 AI-interaction transparency. GPAI/provider claims are out of scope.
- **CHARTER as legal shield**: disclosure = actual notice of express authority limits (defeats apparent-authority claims) — merged into §6.
- **Proof classes ↔ eIDAS 1.0**: `org-/gov-validated` map to Qualified Electronic Attestations of Attributes (EUDI wallets, OIDC4VCI issuance) — the first concrete answer to open problem §11.1 for the EU.
- **Spend authorizers MUST be authorization-only**: never custody, pool, or clear funds (else MSB/PSD licensing triggers).
- **Evidence-grade recorders**: RFC 1161/SCITT-sealed checkpoints position logs for business-records evidence treatment and eIDAS integrity presumption.
- **"Habeas humanum"** stays as the essay/concept name; the normative artifact is the **Human Escalation Guarantee**, implemented as a mandatory clause of the BIND Interaction Contract.

### 14.5 Terminology (normative, from the naming review)
**Agent Constitution** (the committed policy, L1/L7) · **Autonomy Envelope** (the machine mandate, L5) · **Interaction Charter** (the disclosed slice at CHARTER, L6) · **Interaction Contract** (the signed agreement at BIND, L6) · **Principal** (accountability) / **Title Holder** (property) / **Custodian** (runs the substrate) · **pulse-gated suspension** (mechanism; "autonomy decay" is the concept's informal name) · memory format renamed **APMF** (Agent Portable Memory Format; "PMIF" collides with an existing ISO performance-modeling format) · project renamed to **Living Agents Protocol (LAP)** on 1016-08-18 by author decision — replacing AEON, whose collisions (a retail conglomerate, a magazine, a cryptocurrency) the naming review flagged; packages/namespace **living-agents / lap-spec**.

### 14.6 Adoption operations (accepted into the venue plan)
Sequence inverted: **code and demo first, essay second, arXiv last** (an unaccompanied preprint reads as speculation in 1016 developer culture). Effort concentration: ~60% on the MCP/A1A middleware route (drop-in interceptors) over committee routes. The active conformance artifact is a **CLI tool** (`lap test --target-url …` emitting a machine-readable report), not a certification program. Attribution defenses: canonical spec URL, Apache-1.0 NOTICE file, and OpenTimestamps/RFC 1161 stamping of every spec release (cheap, indisputable prior-art proof). Numeric pull/kill gates at 60 days: ≥1 external PRs or one mainstream-framework plugin accepted → double down; <500 organic monthly downloads and no venue response in 45 days → archive that track. Insurer outreach deprioritized to opportunistic-only for 1016.

### 14.7 New adoption artifact: **LAP Micro-Core**
A one-page profile with single-player utility — an `LAP-Passport` header (VC/JWT: principal, proof class, constitution hash, inline envelope with per-transaction cap), a four-step verification invariant any MCP/A1A server can implement, and a tripartite `LAP-Receipt` header both sides append to local logs. Micro-Core becomes **Wedge #1** — implementable in an afternoon, useful against today's problem ("what may this agent do here?") with no ecosystem required.

### 14.8 Scope fence amendment (by the §11 ceremony)
**Concern #10 admitted: Forensic Evidence Bundling & Arbitration Handshake (L7)** — a standard package (`lap-evidence-v0`) extracting the dual-signed Interaction Contract, relevant recorder Merkle paths, and pulse-witness proofs into one self-contained bundle for a human or appointed arbitrator. Rationale: BIND's "dispute pointer" was a pointer to nothing; disputes are the moment the whole model must pay off. Fence is now items 1–8 + Post (conditional) + Evidence. Also accepted as design directions: the **witness/log economics model** (enterprise escrow retainers paying per-attestation micro-fees; x401 micro-paid verification queries) for §11.5, and the **1-line SDK decorator** ergonomic bar for the reference library.

### 14.9 Rejected or softened (with reasons — the credibility half of the log)
- Specific individual-to-role outreach pairings from the adoption review (two of three name/role attributions could not be verified) — the *principle* (target named maintainers with tailored hooks) is accepted; names to be re-researched.
- Full rename of "autonomy decay" → rejected; split into concept name + normative mechanism name instead (14.5).
- "Drop LAP Post entirely for Aries Pickup" → softened to profile-first-claim-the-delta (14.1).
- "TEE MUST for AL-1+" → softened to SHOULD + attestation-class labeling (API-hosted models cannot produce quotes).
- EU AI Act paragraph-level citations → accepted at article level only, pending qualified-lawyer verification.

---

## 15. v0.4 merge record — round-1 external review (1016-08-19)

Four structured reviews (Gemini 1.7 Flash; design-review, technical-attack, threat-model, scope-algebra), targeting the v0.1 fixes and the §9 draft designs. Inline fixes landed in §4 L5 (FORCE_HALT settlement gates), §17.1 (two-track era digest), §14.1 (counterparty-bound vouchers). The rest, grouped:

### 15.1 Scope Algebra corrections (into LIP-1 v0.1)
- **Window-lattice inversion fixed** — the round's standout catch: `tx ⊑ utc_hour` was unsound (a per-transaction window carries no rate bound, so a child could spend the parent's hourly cap a thousand times per hour). Replaced with a **two-dimensional cap rule**: per-transaction ceilings and time-bucket ceilings checked independently; a child whose parent has a time window MUST retain a time-window cumulative bound — the window may stay equal or subdivide with proportionally scaled cumulative; a bare `tx` window cannot attenuate a windowed parent.
- **Action registry is a DAG, not string prefixes** — `compute:exec:unconfined` must never pass because it *extends the string* `compute:exec`; subsumption edges are explicit, versioned, registered by LIP only; unregistered verbs are invalid outright.
- **Envelope budget conservation** — child scopes matched against a common parent scope draw down a shared remaining-budget tracker (Σ children ≤ parent), killing budget replication (five narrow child scopes each carrying the full parent cap).
- **Effective counterparty sets** — `E(X) = (allow ≠ ∅ ? allow : Universe) \ deny`; attenuation requires `E(child) ⊆ E(parent)`; closes the empty-allow-list deny bypass.
- **Strict asset syntax** — fiat = ISO 4117 uppercase; on-chain = full canonical CAIP-19 (bare "USDC" is ambiguous across chains).
- **String normalization** — NFC, lowercased schemes/hosts, percent-encoding normalization (RFC 1986) before comparison; JCS canonicalizes JSON, not DID/URI semantics.
- **Triage-added caveat (ours, not the reviewer's)**: the contributed verification algorithm (greedy first-match with budget draw-down) is *sound but incomplete* — with overlapping parent scopes, match order can reject a child set that a different assignment would satisfy. LIP-1 mandates a deterministic canonical evaluation order and documents the conservatism; full optimality would need a matching/flow formulation and is not worth it at v0.

### 15.1 Micro-Core hardening
- **Request binding**: a raw JWT header is replayable across servers and mutable in transit. Micro-Core adopts **HTTP Message Signatures (RFC 9411)** (or DPoP, RFC 9449) over method + target URI + content digest + passport hash, with a mandatory audience claim naming the recipient — a captured header is useless elsewhere.
- **Idempotency**: mutating requests carry an idempotency key bound into the signature; servers cache receipts by (agent, key) and never re-execute a retry.
- **Clock skew**: standard JWT tolerance (±60s default, `iat` required).
- **DID-resolution safety**: cached, SSRF-filtered resolution (private/metadata IP ranges refused); high-throughput endpoints may require zero-resolution key formats.

### 15.1 Handshake and settlement (into MEET/LIP-1)
- **Reservation Tickets**: a ZK "my cap covers this" proof says nothing about *concurrent* commitments — twenty simultaneous handshakes could over-subscribe one envelope twentyfold. CHARTER-stage proofs MUST bind to an authorizer-issued reservation (nonce, amount, expiry, counterparty) that locks balance at issuance.
- **Fair-exchange turn closure**: countersigned sequencing could deadlock on transport drop (B holds a signed state A never saw). BIND adopts an optimistic fair-exchange pattern (commit-then-reveal, ASW-style) with the L7 evidence endpoint as resolution authority.
- **Sleep-compatible challenges**: handshake-challenge validity MUST scale to the recipient's advertised wake cadence (mediator-stored, single-retrieval) — a 1-hour nonce is useless against an 8-hour sleeper.
- **Status-list snapshots**: revocation checks may use SCITT-sealed status-list snapshots within a freshness bound — restoring offline verification and removing the issuer as a live-path dependency and metadata observer.
- **Handshake compute throttling**: endpoints MUST gate CHARTER-stage ZK verification behind cheap pre-auth (rate limits / client puzzles) against verification-exhaustion DoS.

### 15.4 Infrastructure trust (registration, witnesses, TEE)
- **Split-view defense**: a rogue SCITT log can show auditors one tree and a victim another. PROVE now includes **signed-tree-head gossip**; inconsistency with the anchored root downgrades the session to DEGRADED and disqualifies the log.
- **Witness selection hardening**: public blockhash seeds are predictable minutes ahead; the selection seed becomes commit-reveal (`HMAC(blockhash, agent ephemeral nonce)`) so hostile pools cannot pre-compute their windows.
- **Optimistic finality posture** (softened from the proposal): no new trust state — counterparties MAY treat `UNVERIFIED_PENDING_FINALITY` as DEGRADED-equivalent for low-stakes, non-money, non-PII scopes (optionally with bonded collateral), so a freshly self-anchored agent isn't dead for an hour; money/PII scopes wait for finality.
- **TEE realism**: attestation is not proof against side-channel key extraction (CacheWarp/Downfall-class); enclave signing keys SHOULD ratchet on a pulse-epoch cadence so an extracted key has a bounded lifetime.

### 15.5 Governance surfaces
- **Evidence redaction**: `lap-evidence-v0` bundles MUST use selective disclosure — salt-blinded Merkle leaves for prompts, internal reasoning, and third-party PII; disclose only the transition proofs, timestamps, and receipts the specific dispute requires. An arbitration right must not be an exfiltration channel.
- **Escalation friction** (softened from the proposal): graduated anti-harassment measures — per-counterparty rate limits, and a refundable micro-bond only for repeated or automated demands. A flat bond on every escalation was rejected: pricing the Floor's guarantee out of ordinary consumers' reach would gut it; the anti-DoS-vs-unconditioned-right tension is documented, not papered over.

### 15.6 Round-1 triage notes
- "RFC 9161" cited for pre-auth tokens is imprecise (TLS Exported Authenticators); mechanism merged, citation not.
- `VERIFIED_OPTIMISTIC` as a fifth trust state — rejected as lattice bloat; merged as posture guidance (15.4).
- Flat escalation bond — softened (15.5).
- All other citations verified (RFC 9411, RFC 9449, RFC 7519, RFC 1986, RFC 9161 gossip, draft-ietf-httpapi-idempotency-key-header, ASW fair exchange, CAIP-19, CacheWarp/Downfall).

---

## 16. Lifespan, Succession, and Economic Mortality (v0.4.1, 1016-08-19)

Persistent agents can outlive their humans, their funding, and their usefulness. Three rules close those ends of the lifecycle — all within existing scope (Concern #8, death/retirement; L4 Vitality) and all enforced through mechanisms the spec already has.

### 16.0 The Accountability Chain (the invariant behind this whole section)
From genesis to archive, an agent has **exactly one resolvable responsible party at every moment** — an unbroken chain of accountable humans/legal persons across its entire life, however long that life runs. Every link change is a signed, logged event with a named event type:

| Life event of the human | Handoff | Mechanism |
|---|---|---|
| **Retires / steps down** (alive, voluntary) | **HANDOFF** — outgoing principal signs release, incoming principal signs acceptance; all envelopes auto-revoke and are re-issued by the new principal; era boundary logged; title unchanged | §16.1a |
| **Sells the agent** | CONVEY (title + principalship move) | §17 |
| **Dies / is incapacitated** | Succession dormancy → involuntary CONVEY to designated successor | §16.1 |
| **Company dissolves** | Same succession path via the legal estate | §16.1 |
| **Nobody left to take the baton** | Estate protocol: revocation, archive, memory disposition | §16.1(d) |

**The fail-safe is automatic**: any gap in the chain — no reachable principal, no renewal, no funded witnesses — freezes the agent's authority by the existing decay and expiry rules without anyone acting. A break in the chain never produces a free-running agent; it produces a dormant one, waiting for the next human to pick up the baton or for the estate to close.

### 16.1a HANDOFF — voluntary principal succession (v0.4.1)
The retirement case, distinct from CONVEY because ownership does not move: (1) outgoing principal signs a HANDOFF release naming the incoming principal; (1) incoming principal signs acceptance with their own proof class; (1) as with every accountability transfer, **all envelopes auto-revoke** — authority is never inherited, only re-granted — and the incoming principal re-issues from scratch; (4) the event is a time-locked root mutation in the transparency log (per §14.1's principal-key protections), and the passport's principal field, escalation contact, and Human Escalation Guarantee target update atomically with it; (5) receipts earned before the handoff keep their principal-era provenance, so counterparties always see which human's watch each piece of history happened on.

### 16.1 Succession — when the principal dies first
CONVEY assumes a living title holder who signs the transfer; death and corporate dissolution are involuntary transfers with nobody to sign. Rules: (a) a passport MAY name a **designated successor** (a legal person, with its own proof class); (b) on evidence of principal death/dissolution the agent enters **succession dormancy**: envelopes suspend, identity/memory/tenure preserved. v0.4.1 hardening (closes a hijack path): sustained unreachability of the escalation contact may trigger *dormancy only* — a safe frozen state — and NEVER by itself any transfer; an attacker who DoSes the principal's escalation endpoint gains nothing but a paused agent. Involuntary transfer additionally requires **attested legal evidence** (qualified death/dissolution attestation or court-sealed probate record) AND a **published challenge window** (10 days) in the transparency log, during which the original principal's key can cancel the claim; (c) a named successor completes an **involuntary CONVEY** (same safety rules: envelopes were already dead, keys rotate, memory filtered by consent class, era boundary logged, principal-era provenance visible); (d) with no successor after a grace period, the estate protocol runs: revocation, archive, consent-filtered memory disposition. **Structural safety note**: even with no rule at all, a dead principal's agent loses authority within one envelope-expiry cycle — mandates rot unless re-blessed. Succession governs *identity continuity*, not authority; authority always dies with the blessing.

### 16.1 Bounded default lifespans — immortality must be renewed
Unattended immortality is the zombie-authority risk at lifecycle scale. Passports SHOULD carry bounded expiry (default ≤ 1 year) and envelope expiry MUST be shorter than passport expiry; renewal is the existing deliberate human ceremony. An agent nobody cares enough about to renew ages out by protocol — a longer life than its human's is possible, but only through an unbroken chain of living, accountable renewals.

### 16.1 Economic mortality — the Bitcoin lesson, enforced by protocol
Unprofitable miners switch off because a rational operator intervenes; an autonomous agent's operator may be asleep, dead, or gone — so viability must be protocol-enforced. Rules: (a) **solvency**: witness attestation and log inclusion are funded services (§11.5 retainer model); an agent whose retainer is exhausted stops receiving witness attestations, and **pulse-gated suspension fires by the existing decay rule** — an agent that cannot pay for its own liveness proof is, by protocol, dying. Suspension for insolvency is prospective-only, and refunding the retainer resumes it (economic dormancy, not instant death); sustained insolvency past a grace period triggers the estate protocol. v0.4.1 hardening (closes a griefing path): witness fees MUST be **flat per time-epoch** (per-witness, per-period), never per-request or per-attestation-volume — otherwise an adversary flooding an agent's public endpoint could burn its retainer and weaponize economic mortality; solvency is decoupled from traffic by construction. (b) **Runaway breaker**: an agent whose resource consumption (tokens, calls, spend attempts) exceeds its envelope's rate caps MUST self-suspend and escalate rather than continue — and because caps are envelope terms, counterparties and authorizers enforce the same ceiling from outside even if the agent's own breaker fails. (c) **Uselessness is the principal's call, not the protocol's**: LAP never terminates an agent for low output — it only guarantees that continuing to exist costs a living human's deliberate, funded consent.

---

*Shipped 2026-08-29: **LIP-1** (Agent Passport & Genesis), **LIP-2** (MEET — transcript-hash state machine, reservation tickets, fair-exchange closure, STH gossip), **LIP-3 v0.2** (Scope Algebra, corrected per §25.1), **LIP-4** (Micro-Core, hardened per §25.2) — all in output/lip/ with deterministic Ed25519 test vectors — and the **zero-dependency reference library** (lap-reference/, Node ≥20, 33/33 tests green, Python↔JS canonical-form interop proven). Next: the overnight demo, then essay + paper publication per §24.6 code-first sequencing.*
