MODEL: Gemini (Advanced Coding & Reasoning)
DIMENSION: 03-prior-art-hunt.md
DATE: 2026-08-28

## FINDINGS

F1. [SEVERITY: SERIOUS] [TARGET: §4 Agent Passport & Genesis Record vs IETF WIMSE & SPIFFE]
    CLAIM: Re-inventing agent workload identity formats ignores the IETF WIMSE Working Group (Workload Identity in Multi-System Environments) and CNCF SPIFFE SVID standards.
    REASONING: Enterprise infrastructure already routes workload identity via SPIFFE X.509 SVIDs / JWT SVIDs and the emerging IETF WIMSE architecture (`draft-ietf-wimse-arch-01`). If AEON defines a bespoke Passport JSON format without a standard WIMSE token profile or SPIFFE SAN mapping, enterprise security teams and API gateways (Envoy, Istio, Kong) cannot parse or policy-check AEON agents without custom plugins.
    EVIDENCE: Context Pack §4 defines Agent Passport as a bespoke signed document rather than an interoperable identity token profile.
    PROPOSED FIX: PROFILE IT. Standardize the Agent Passport as a W3C Verifiable Credential 2.0 carrying a WIMSE-compatible Workload Identity Token and SPIFFE ID URI in the subject field (`spiffe://<trust-domain>/agent/<agent-did>`).

F2. [SEVERITY: FATAL] [TARGET: §4 Transparency Logs vs IETF SCITT]
    CLAIM: Defining a custom "Agent Transparency Log" ignores IETF SCITT (Supply Chain Integrity, Transparency and Trust), which already solves Merkle transparency, signed statements, and offline receipts.
    REASONING: IETF SCITT (`draft-ietf-scitt-architecture-08`) specifically standardizes transparent append-only ledgers for software artifacts, configuration commitments, and public statements using COSE/CBOR. SCITT produces portable, self-contained `Receipts` containing Merkle inclusion proofs that verifiers can validate offline without querying the log directly. Building a bespoke ATL makes AEON look naive to IETF security engineers.
    EVIDENCE: Context Pack §4 and §6.5 treat ATL as a custom CT-style log requiring open blockchain anchors.
    PROPOSED FIX: PROFILE IT. Explicitly declare the Agent Transparency Log to be an IETF SCITT Transparency Service. Genesis records, key rotation events, and era boundaries become standard SCITT Signed Statements, and verification uses standard SCITT Receipts.

F3. [SEVERITY: SERIOUS] [TARGET: §4 Autonomy Envelope vs GNAP & OAuth RAR]
    CLAIM: Re-inventing autonomy envelopes from scratch duplicates IETF GNAP (RFC 9635) grant negotiation and OAuth Rich Authorization Requests (RFC 9396).
    REASONING: IETF GNAP (RFC 9635) natively models multi-party delegation, interaction boundaries, client-requested rights vs AS-granted rights, and asymmetric cryptographic binding to client keys without bearer token leakage. OAuth RAR (RFC 9396) specifies the `authorization_details` format for fine-grained capability scopes.
    EVIDENCE: Context Pack §4 models the Autonomy Envelope as a disconnected artifact.
    PROPOSED FIX: PROFILE IT. Model the Autonomy Envelope as an IETF GNAP Grant Response carrying an RFC 9396 RAR `authorization_details` capability block.

F4. [SEVERITY: SERIOUS] [TARGET: §4 Envelope Attenuation vs Biscuit / UCAN]
    CLAIM: AEON's custom attenuation logic reinvents Biscuit token Datalog caveats and UCAN delegation chains.
    REASONING: Biscuit (biscuitsec.org) provides cryptographically proven offline attenuation where an authority signs a root token and downstream parties append signed Datalog blocks (caveats) that can strictly restrict, but never expand, privileges. UCAN v0.10 provides a similar JSON/JWT capability model. Re-specifying attenuation math without using Biscuit or UCAN semantics risks subtle cryptographic delegation vulnerabilities.
    EVIDENCE: Context Pack §4 and §6.1 highlight that attenuation crypto proves derivation, but leave wire serialization and verification engines unaligned.
    PROPOSED FIX: PROFILE IT. Adopt Biscuit as the binary token format and UCAN as the JSON/JWT profile for AEON Autonomy Envelopes. Scope Algebra v0 compiles directly to Biscuit Datalog caveat rules.

F5. [SEVERITY: MODERATE] [TARGET: §4 MEET Handshake vs DIDComm v2 & Noise Protocol]
    CLAIM: The 6-step MEET handshake duplicates DIDComm v2 Connection/Out-of-Band protocols and lacks modern authenticated key exchange (AKE) framing from Noise Framework.
    REASONING: DIDComm v2 (Decentralized Identity Foundation) already specifies out-of-band invitation, trust-ping, discovery, and secure messaging over heterogeneous transports. Furthermore, the cryptographic phase progression of HAIL $\to$ PROVE $\to$ TUNE maps directly to the Noise Protocol Framework (`Noise_XX` or `Noise_IK` handshakes), which provides formal security proofs against replay, key compromise impersonation, and identity leakage.
    EVIDENCE: Context Pack §4 specifies a bespoke 6-step sequence (HAIL/PROVE/CHARTER/TUNE/BIND/PULSE) without reference to formal AKE state machines.
    PROPOSED FIX: PROFILE IT. Define MEET as a formal Noise Protocol Framework handshake (`Noise_IK_psk2`) encapsulated within DIDComm v2 message packaging.

F6. [SEVERITY: MODERATE] [TARGET: §4 Pulse & Liveness vs DIDComm Trust Ping & XMPP]
    CLAIM: Liveness monitoring mechanisms duplicate XMPP Presence (RFC 6121) and DIDComm Trust Ping Protocol 2.0.
    REASONING: RFC 6121 has 20+ years of operational experience managing presence status, availability cadences, directed presence, and server-side subscription lists. DIDComm Trust Ping (DIF) standardizes ping/pong latency checks and ephemeral liveness verification between peer agents.
    EVIDENCE: Context Pack §4 defines Pulse as a bespoke heartbeat tied to the audit log head.
    PROPOSED FIX: CITE AND DIFFER. Adopt DIDComm Trust Ping message schemas for peer-to-peer liveness, but clearly document that AEON Pulse differs by cryptographically chaining the heartbeat to the Flight Recorder audit-log head and transparency log epochs.

F7. [SEVERITY: MODERATE] [TARGET: §4 Flight Recorder vs OpenTelemetry GenAI & RFC 3161]
    CLAIM: Specifying a novel logging structure ignores OpenTelemetry Semantic Conventions for Generative AI and RFC 3161 Trusted Timestamping.
    REASONING: Enterprise observability is completely standardizing on OpenTelemetry (OTel). OTel has established semantic conventions for LLM operations (tokens, prompts, model IDs, tool invocations). RFC 3161 (Time-Stamp Protocol) provides the established standard for cryptographic timestamping of append-only audit entries.
    EVIDENCE: Context Pack §3 and §4 cite OTel in the table but design Flight Recorder heads as a separate bespoke construct.
    PROPOSED FIX: PROFILE IT. Specify that Flight Recorder entries MUST be formatted as OpenTelemetry GenAI Span / Log records with SCITT / RFC 3161 signed checkpoint envelopes.

F8. [SEVERITY: MODERATE] [TARGET: §4 Ownership & CONVEY vs EPP (RFC 5730) & ERC-6551]
    CLAIM: CONVEY transfer ceremony ignores the lessons of domain transfer in Extensible Provisioning Protocol (EPP - RFC 5730) and Token Bound Accounts (ERC-6551).
    REASONING: EPP (RFC 5730) handles multi-party domain ownership transfer (Registrant $\leftrightarrow$ Registrar $\leftrightarrow$ Registry) with authorization codes (`authInfo`), pendingTransfer grace periods, and automatic key invalidation. ERC-6551 establishes smart-contract ownership of autonomous account states.
    EVIDENCE: Context Pack §4 and §6.7 identify CONVEY atomicity and transfer grace periods as open problems.
    PROPOSED FIX: PROFILE IT. Model CONVEY after EPP RFC 5730 state transitions (`transfer:request`, `transfer:approve`, `transfer:reject`, `clientHold`) combined with cryptographic key rotation proofs.

F9. [SEVERITY: MODERATE] [TARGET: §2 & §4 Store-and-Forward vs Aries RFC 0685 (Pickup Protocol v2.0)]
    CLAIM: Reserving "AEON Post" without citing Aries RFC 0685 (Pickup Protocol v2.0) overlooks existing decentralized store-and-forward protocols for sleeping agents.
    REASONING: Aries RFC 0685 already solves store-and-forward message retrieval, batch polling, live delivery modes, and mediator coordination for offline mobile and sleeping decentralized agents.
    EVIDENCE: Context Pack §2 reserves "AEON Post" for store-and-forward messaging between sleeping agents.
    PROPOSED FIX: DROP AEON'S VERSION. Drop the conditional "AEON Post" reservation and adopt Aries RFC 0685 / DIDComm v2 Mediator Routing as the standard L4/L6 store-and-forward transport.

---

## PRIOR ART TAXONOMY TABLE

| AEON Mechanism | Prior Art / Standard | Exact Citation | Strategy | What AEON Adopts vs What AEON Adds |
|---|---|---|---|---|
| **Agent Passport & Genesis (L2)** | IETF WIMSE / W3C VC 2.0 / SPIFFE | `draft-ietf-wimse-arch-01`, W3C REC `vc-data-model-2.0`, CNCF SPIFFE | **PROFILE IT** | Adopt VC 2.0 data model and SPIFFE SVID URI format; AEON adds public constitution hash and proof-class taxonomy. |
| **Autonomy Envelope (L5)** | IETF GNAP / OAuth RAR | RFC 9635 (GNAP), RFC 9396 (RAR) | **PROFILE IT** | Adopt GNAP interaction boundaries and RAR JSON schema; AEON adds Scope Algebra v0 and witness decay rules. |
| **Attenuation Crypto (L5)** | Biscuit / UCAN | `biscuitsec.org` spec v2.1, `ucan.xyz` spec v0.10 | **PROFILE IT** | Adopt Biscuit Datalog caveat engine; AEON adds closed verb registries and numeric spend caps. |
| **Transparency Log (L2/L7)** | IETF SCITT | `draft-ietf-scitt-architecture-08` | **PROFILE IT** | Adopt SCITT Transparency Service and Signed Receipts; AEON adds agent Genesis / Era Statement profiles. |
| **MEET Handshake (L6)** | Noise Framework / DIDComm v2 | `noiseprotocol.org` (Noise_IK), DIF DIDComm v2.0 | **PROFILE IT** | Adopt Noise authenticated key exchange; AEON adds CHARTER scope disclosure and BIND interaction contracts. |
| **Pulse / Liveness (L4)** | DIDComm Trust Ping / XMPP Presence | DIF Trust Ping 2.0, RFC 6121 | **CITE & DIFFER** | Adopt Trust Ping ping/pong schemas; AEON adds audit-log head chaining and multi-witness decay triggers. |
| **Flight Recorder (L7)** | OpenTelemetry / RFC 3161 | OTel GenAI Semantic Conventions v1.28, RFC 3161 | **PROFILE IT** | Adopt OTel GenAI telemetry schemas and RFC 3161 timestamps; AEON adds bilateral dual-logging and BIND binding. |
| **CONVEY Transfer (L6/L7)** | IETF EPP Domain Transfer | RFC 5730 (EPP) | **PROFILE IT** | Adopt EPP transfer lifecycle states (`pendingTransfer`, `autoRevoke`); AEON adds era-stamp boundary receipts. |
| **Store-and-Forward (L4/L6)** | Aries Pickup Protocol v2.0 | Aries RFC 0685 | **DROP AEON'S VERSION** | Drop bespoke "AEON Post"; use Aries Pickup v2 for mediator message queuing across sleep cycles. |

---

## SURVIVORS
1. **Constitution Commitment via Hash**: Existing identity standards (WIMSE, SPIFFE, VC) lack any concept of binding an identity to a public policy commitment hash with transparent log anchoring.
2. **Era-Stamped Receipts for Substrate Migration**: Neither SCITT, EPP, nor DID standards address the problem of reputation preservation vs capability laundering across AI substrate/model swaps.
3. **Decay-Tied Autonomy Envelopes**: OAuth, GNAP, and Biscuit model token expiration via static timestamps (`exp`); AEON's dynamic coupling of authorization validity to active Pulse witness continuity is genuinely novel.

---

## SCORE
9/10 (Novelty remaining after sweep: 4/10; Protocol viability with alignment: 9/10) — The vast majority of AEON's plumbing can and must be profiled directly from IETF SCITT, WIMSE, GNAP, RFC 9396, and Biscuit. AEON's true novel core is the control plane synthesis: Pulse witness decay, Era-stamped substrate migration receipts, and BIND interaction contracts.
