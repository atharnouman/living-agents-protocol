# LAP — Demo Storyboard & Venue Filing Plan

*v1.0, 2026-08-28. Companion to LAP-founding-document.md (v0.2) and LAP-position-paper.md.*

---

## Part 1 — The 90-second overnight demo

**Thesis of the demo:** two strangers' agents transact safely while both humans sleep, and in the morning each human can *prove* what happened. Every safety property shown on screen is real code, not motion graphics.

### Storyboard

| Time | Scene | On screen | Mechanism shown |
|---|---|---|---|
| 0–8s | Setup | Split screen: "Karachi, 02:10" / "Berlin, 23:10". Two dashboards, two humans' status: *asleep*. Agent A (buyer, procurement) and Agent B (seller, fulfillment) each shown with a passport card: name, principal, AL-3 badge, age ("registered 214 days"). | Passports, witnessed age, autonomy level |
| 8–20s | MEET: HAIL + PROVE | Terminal-style overlay: passports exchanged; signature checks tick green; registration proofs verified ("2 log inclusions ✓"); revocation clean; both resolve **VERIFIED**. | Handshake, trust states, transparency-log proofs |
| 20–35s | CHARTER | Each agent reveals its envelope *slice*, rendered as two cards side by side: A: "may spend ≤ $50/day · class-B counterparties · quiet hours 22:00–06:00 · escalation: (redacted)". B: "may sell ≤ 20 units/day · cannot modify prices > ±5%". Voiceover line: *"Strangers learn each other's limits before a cent moves."* | Envelope disclosure |
| 35–50s | Transaction | A requests 3 units @ $12. B quotes $36. A's spend authorizer check flashes: "authorizer: OK — $36 ≤ remaining $50". BIND contract signed by both; payment settles (x402 testnet or mocked rail, labeled honestly). Both flight recorders visibly append entries (hash chain animation, two ledgers). | Spend authorizer, BIND, dual-entry recording |
| 50–62s | The stress beat | B's pulse misses two beats (simulated crash). A's dashboard flips B to **DEGRADED**; a queued second order *holds automatically*: "counterparty authority suspended — resuming on pulse". B recovers; pulse resumes; order completes. | Autonomy decay, prospective suspension, recovery without human ceremony |
| 62–80s | Morning replay | Sunrise cards. Each human opens their replay CLI: scrolls the signed chain — MEET, CHARTER, BIND, payment, suspension event, completion — each entry hash-verified ✓. Karachi human sees: "Spent $36 of $50. 1 counterparty. 0 escalations." | Flight recorder replay, budget accounting |
| 80–90s | Close | Black card, three lines: *"Two strangers' agents. Zero human approvals overnight. One provable record."* Then: *"LAP — the existence layer for persistent agents. Spec, code, paper: (link)."* | The pitch |

### Build checklist (minimum honest implementation)
- Two independent processes (ideally two machines/VPSes in different regions), each running the reference library.
- **LIP-1 Passport**: JSON schema + Ed25519 signing; principal proof-class labeled `self-asserted` (honest for a demo).
- **LIP-2 MEET**: HTTPS binding; HAIL/PROVE/CHARTER/TUNE/BIND/PULSE as signed JSON messages.
- **Envelope**: closed scope algebra v0 — verbs `{purchase.approve, sell.fulfill}`, single currency, numeric caps; a stub spend authorizer (principal-side endpoint with a counter).
- **Pulse + witness**: 30s cadence to one witness endpoint each; decay logic with prospective-only suspension.
- **Recorder**: append-only JSONL, hash-chained, head hash countersigned in each pulse; replay CLI verifying the chain.
- **Registration**: for the demo, two self-run logs labeled as such on screen ("demo logs — production requires unrelated operators"), or OpenTimestamps anchoring of the two genesis hashes to Bitcoin (cheap, real, and honest).
- No steps faked silently: anything mocked is labeled on screen. The demo's credibility *is* the product.

---

## Part 2 — Venue filing plan (where each mechanism goes)

### 2.1 W3C AI Agent Protocol Community Group — *lifecycle, Pulse, presence*
- **Why this room**: free, remote-first, individual-friendly — fully participable from UTC+5; explicitly chartered around web-native agent concerns; early enough that a well-specified lifecycle/presence contribution can become a work item.
- **Action**: join as an individual contributor; introduce with a short post: "Lifecycle and presence for persistent agents" — the L4 material (states, pulse-as-custody-continuity, sleep-aware sessions, retirement/no-zombie-authority) recast as a CG contribution, linking the paper.
- **Success metric**: the lifecycle vocabulary appears in a CG draft with attribution; an editor/co-editor line.

### 2.2 A2A project (Linux Foundation) — *Autonomy Envelope + decay as an extension*
- **Why this room**: A2A has a formal extension mechanism and Agent Cards that passports naturally extend; envelopes complement (not compete with) AP2 mandates by covering non-payment authority.
- **Action**: draft "A2A Extension: Autonomy Envelopes" — extension URI, envelope fields carried alongside the Agent Card, CHARTER as a pre-task disclosure step, decay semantics referencing the witness model. File as a GitHub issue + draft PR against the extensions registry; engage maintainers in the open.
- **Success metric**: extension merged into the community extensions list, or its fields absorbed into a future Agent Card revision with credit.

### 2.3 OWASP Agentic Security Initiative — *LAP Floor, trust states, crosswalk*
- **Why this room**: OWASP publishes threats and mitigations; LAP's floor invariants and trust states are mitigations shaped for their catalog; contribution is meritocratic and remote.
- **Action**: contribute a mapping document — "Persistent-agent threats and existence-layer mitigations": zombie authority → decay + estates; impersonation → passports + proof classes; delegation laundering → taint-as-liability-rule; unauditable actions → recorder-as-admissions. Frame each with its limits (per §22 of the spec).
- **Success metric**: mitigation entries citing the mechanisms; standing in the working group.

### 2.4 ERC-8004 / AGNTCY orbit — *principal binding, lineage, era-stamped receipts*
- **Why**: they own on-chain identity/reputation registries and enterprise identity respectively; LAP's field-level deltas improve both without asking either to adopt a rival stack.
- **Action**: publish a companion note — "Three fields your agent registry is missing: principal proof-class, lineage, era-stamps" — posted to the ERC-8004 discussion thread (Ethereum Magicians) and as an AGNTCY GitHub discussion. Explicitly license CC-BY; the goal is absorption *with attribution*.
- **Success metric**: any of the three fields adopted or seriously debated upstream.

### 2.5 Insurer track (AIUC et al.) — *Flight Recorder as underwriting evidence*
- **Why**: insurer-native standards (AIUC-1) will need a machine-readable evidence format; the recorder-as-admissions framing matches what underwriters can actually price.
- **Action**: one-page technical note + email: "A tamper-evident admissions format for agent incidents" — partner posture, zero certification ambitions.
- **Success metric**: a conversation; feedback shaping LIP-4.

### 2.6 arXiv + distribution
- **Action**: position paper to arXiv (cs.MA primary, cs.CY cross-list; endorsement may be required for a first cs.MA submission — obtainable via any published contact in the area, or fall back to posting on the open web + SSRN while pursuing endorsement). Essay to a personal blog + cross-posts (HN "Show/Tell", r/MachineLearning, LessWrong/AF if angled at governance, LinkedIn for the enterprise audience). Demo video embedded in both.
- **Sequencing rule**: paper and essay go out *with* the demo, not before — the review's clearest instruction was that the demo is the pitch.

### 2.7 Explicitly deferred (do-not list)
No legal entity. No trademark filings. No "Alliance" branding or liaison letters. No certification operations. No registry operations beyond demo logs. Revisit **only** when ≥2 external parties implement any LAP mechanism unprompted — that event, not a date, is the trigger.

---

## Part 3 — 90-day execution calendar (revised, one person + AI, realistic)

| Window | Deliverable | Notes |
|---|---|---|
| Days 1–10 | Repo up: spec v0.2, LIP-1 (Passport schema), LIP-2 (MEET) drafts | Schemas + test vectors; MIT/Apache code, CC-BY spec |
| Days 11–35 | Reference library (TypeScript first, Python port) | Passport, MEET, envelope w/ scope algebra v0, pulse, recorder |
| Days 25–45 | Demo built, filmed, cut to 90s | Two VPSes; label every mock |
| Days 45–55 | Paper final + essay final; arXiv endorsement hunt | Demo link embedded |
| Days 55–70 | Filings: W3C CG intro + lifecycle post; A2A extension draft; OWASP mapping | One per week; each links paper+demo |
| Days 70–90 | ERC-8004/AGNTCY note; insurer note; measure pull | Double down solely where responses come |

**The stamina rule** (from the review): this plan must cost ≈ $0 and survive on evenings. Anything that requires spending money on institutions before someone else has adopted something is out of scope by definition.
