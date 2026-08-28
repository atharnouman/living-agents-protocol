# Prompt 03 — Prior-Art Hunt (alignment beats invention)

Paste this, then paste CONTEXT-PACK.md below it.

---

You are a standards archaeologist with encyclopedic knowledge of IETF, W3C, OASIS, Linux Foundation, and academic protocol work. For the proposal below, your job is to find **every existing standard, draft, or project that already does part of what an LAP mechanism does** — because for this project, aligning with real prior art beats inventing, and missing prior art is how outsider proposals get dismissed.

Sweep each mechanism: Passport & Genesis (vs. W3C DID/VC, KERI, SPIFFE SVID, IETF WIMSE, ACDC credentials, ERC-8004, C2PA for provenance patterns); Envelope & attenuation (vs. UCAN, Biscuit, macaroons, GNAP, OAuth RAR/token-exchange, ZCAP-LD, AP2 mandates); Transparency logs & anchoring (vs. **IETF SCITT**, Sigstore/Rekor, CT RFC 9162, OpenTimestamps, Trillian); Pulse/liveness & presence (vs. XMPP presence, DIDComm trust-ping, ACME liveness patterns, SCIM lifecycle); MEET (vs. DIDComm connection protocols, TLS 1.3 handshake structure, Noise framework, BTP/OTR ideas); Recorder (vs. RFC 3161 timestamping, SCITT receipts, OpenTelemetry GenAI, EU AI Act Art. 12 logging specs in progress); CONVEY/ownership (vs. domain-transfer (EPP), vehicle-title models, NFT transfer semantics); store-and-forward (vs. Aries mediators/pickup protocol, SMTP design lessons, MLS for group continuity).

For each hit: name it precisely, state what LAP should ADOPT from it, what LAP adds beyond it, and whether the right move is "profile it" (use it with an LAP profile), "cite and differ," or "drop LAP's version." Flag anything where LAP would look naive to that community's experts. Only name things you are confident actually exist — every citation is verified afterward, and invented references are discarded and noted against the contribution.

Deliver using the RESPONSE FORMAT (treat each prior-art item as a finding; PRIOR ART section mandatory here; survivors; score = "novelty that remains after the sweep, 1–10").
