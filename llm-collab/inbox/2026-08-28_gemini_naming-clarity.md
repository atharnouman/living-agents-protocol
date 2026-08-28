MODEL: Gemini (Advanced Coding & Reasoning)
DIMENSION: 06-naming-and-clarity.md
DATE: 2026-08-28

## FINDINGS

F1. [SEVERITY: SERIOUS] [TARGET: §1 Naming / AEON Trademark & Search Collision]
    CLAIM: The name "AEON" suffers from severe SEO pollution and trademark collisions across global retail, media, and tech sectors.
    REASONING: "Aeon" is registered globally by Aeon Co., Ltd. (Japan's largest retail conglomerate with $60B+ revenue), Aeon Magazine (prominent digital essay publisher), and Aeon cryptocurrency. Searching "AEON protocol" or "AEON agent" will produce heavy search dilution and trademark vulnerability if incorporated or commercialized.
    EVIDENCE: Context Pack §1 coins "AEON (Agent Existence & Operation Norms)."
    PROPOSED FIX: Retain "AEON" as the acronym/foundational concept name, but brand the formal standard, npm packages, and protocol specification explicitly as **"AEON-Spec"** or **"OpenAEON"** (`open-aeon.org` / `@openaeon/core`).

F2. [SEVERITY: SERIOUS] [TARGET: §4 Naming / "Autonomy Decay" Semantic Mismatch]
    CLAIM: The term "Autonomy Decay" misleads protocol implementers by implying gradual mathematical attenuation over time, whereas the spec actually implements binary state suspension.
    REASONING: In physical and biological systems, "decay" implies a continuous, analog exponential reduction ($e^{-\lambda t}$). In AEON v0.2, missing $\ge 2$ pulse witnesses does not halve the spending limit; it executes an abrupt binary shift from `ACTIVE` to `SUSPENDED` (prospective-only). Calling this "decay" causes developers to expect gradual capability degradation algorithms.
    EVIDENCE: Context Pack §4 defines "Autonomy decay: validity conditioned on heartbeat continuity... suspension is prospective only."
    PROPOSED FIX: Rename "Autonomy Decay" to **"Liveness-Conditioned Suspension"** or **"Pulse-Gated Autonomy"**.

F3. [SEVERITY: MODERATE] [TARGET: §4 Naming / "Habeas Humanum" Pretentiousness & Legal Confusion]
    CLAIM: "Habeas Humanum" reads as pretentious Latin jargon and creates false impressions of a legally enforceable constitutional writ.
    REASONING: *Habeas corpus* is a strict judicial remedy against unlawful state imprisonment. In an engineering protocol, using pseudo-legal Latin ("produce the human") alienates pragmatic software engineers and provokes corporate legal teams who reject signing terms that mimic judicial writs.
    EVIDENCE: Context Pack §4 and §7 introduce "habeas humanum (any counterparty can demand and reach the responsible human in bounded time)."
    PROPOSED FIX: Rename "Habeas Humanum" to **"Human Escalation Guarantee"** or **"Responsible Principal Reachability (RPR)"** in normative text, reserving "habeas humanum" strictly for marketing essays and motivational introductions.

F4. [SEVERITY: MODERATE] [TARGET: §4 Naming / PMIF Collision]
    CLAIM: The acronym "PMIF" collides with established graphics, typography, and mathematical standard formats.
    REASONING: PMIF is widely known in systems engineering as "Platform Management Interface Framework" and "Performance Model Interchange Format" (ISO standard).
    EVIDENCE: Context Pack §3 and §4 define "PMIF portable memory."
    PROPOSED FIX: Rename to **"APMF" (Agent Portable Memory Format)** or **"PAM" (Portable Agent Memory)**.

F5. [SEVERITY: MODERATE] [TARGET: §4 Terminology / "Charter" vs "Constitution"]
    CLAIM: Ambiguous interchangeable usage of "Charter" and "Constitution" creates confusion across L2 Passport, L6 MEET, and L7 Ethics.
    REASONING: The pack uses "Constitution hash" in L2 Passport, "CHARTER" as Step 3 in the MEET handshake, and "declared charter" in L7 Ethics. A developer cannot tell if an agent's "charter" is its ethical constitution, its autonomy envelope slice, or its bilateral interaction agreement.
    EVIDENCE: Context Pack §4 uses "constitution hash" (L2), "CHARTER" (L6 step), and "declared charter" (L7).
    PROPOSED FIX: Standardize normative terminology:
    - **"Agent Constitution"**: The root public ethical policy commitment (L2/L7).
    - **"Autonomy Envelope"**: The machine-readable capability/budget mandate (L5).
    - **"Interaction Charter"**: The exchanged scope slice during MEET Step 3 (L6).
    - **"Interaction Contract"**: The mutually signed bilateral agreement in MEET Step 5 (L6).

F6. [SEVERITY: MODERATE] [TARGET: §4 Terminology / "Owner" vs "Principal"]
    CLAIM: Boundary confusion between "Owner" (title/property) and "Principal" (legal liability and authority delegation).
    REASONING: In common software discourse, "owner" and "principal" are conflated. If an agent is sold via CONVEY, does the principal change, the owner change, or both?
    EVIDENCE: Context Pack §4 states: "*Owner* (title) $\neq$ *principal* (accountability); passport carries both."
    PROPOSED FIX: Define strict normative RFC 2119 distinctions in §3/§4:
    - **"Principal"**: The legal person (natural or corporate) holding civil/regulatory accountability and issuing the root Autonomy Envelope.
    - **"Custodian / Operator"**: The legal entity executing the substrate infrastructure.
    - **"Title Holder"**: The entity holding economic rights to convey the agent identity.

F7. [SEVERITY: MINOR] [TARGET: §4 Spec Hygiene / Hidden Normative Requirements in "Honest Framing"]
    CLAIM: Critical security requirements (e.g. "no orphan agents", "dual-entry logging") are buried in descriptive paragraphs without RFC 2119 keywords.
    REASONING: Conformance test suites and clean-room implementations cannot generate definitive assertions when normative rules are phrased as narrative commentary.
    EVIDENCE: Context Pack §4 writes: "Rule: no orphan agents — every passport resolves to a legal person. Agents cannot own themselves."
    PROPOSED FIX: Reformat every mechanism into two distinct blocks: **Normative Requirements (RFC 2119)** using MUST, SHOULD, and MAY, followed by an **Informative Rationale / Design Notes** section.

---

## 5 SECTIONS MOST REQUIRING FORMAL STATE TABLES & SCHEMAS

1. **MEET Handshake State Machine**: Complete transition matrix defining inputs, state changes, timeouts, and explicit error codes for all 6 steps.
2. **Autonomy Envelope Liveness Lifecycle**: State chart mapping `ACTIVE` $\to$ `DEGRADED` $\to$ `SUSPENDED` $\to$ `EXPIRED` $\to$ `REVOKED` against witness pulse inputs.
3. **CONVEY Two-Phase Transfer Ceremony**: Sequence diagram and state table detailing seller revocation, buyer key generation, ATL era checkpointing, and memory filtering.
4. **Agent Passport Schema (JSON-LD / W3C VC 2.0)**: Exact structural definition with required fields, cryptographic proof format, and proof-class enumeration.
5. **Flight Recorder Head-Chaining & Pulse Witness Format**: Exact byte-level schema for the hash chain linking audit entries, OTel spans, and Pulse countersignatures.

---

## SURVIVORS
1. **The "MEET" Handshake Acronym**: Memorable, friendly, intuitive, and semantically fits agent-to-agent discovery and binding.
2. **"Flight Recorder" (L7)**: Highly evocative, universally understood aviation metaphor that accurately conveys the expectation of tamper-evident, post-incident forensic investigation.
3. **"Genesis Record" (L2)**: Clean, unambiguous term that grounds agent lineage and immutably establishes verifiable tenure.

---

## SCORE
7/10 — The conceptual naming is strong and culturally resonant, but technical hygiene requires stripping pseudo-legal jargon ("habeas humanum"), fixing misleading metaphors ("autonomy decay"), and enforcing strict RFC 2119 normative boundaries.
