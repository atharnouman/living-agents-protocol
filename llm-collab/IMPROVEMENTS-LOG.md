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

## Foreign-commit audit (d9b1187, 2026-08-30) — unbiased verdict

An external LLM with file access made one git commit directly to the repository. Audited change-by-change:

**ACCEPTED (re-implemented cleanly):** NUL-separator idea for idempotency cache keys (genuinely better collision resistance — but it was committed as *literal NUL bytes inside source code*, turning the file binary for git; re-implemented as the `\u0000` escape sequence); timing-safe receipt hash comparison (harmless, uniform hygiene; supersedes the round-3 triage scoping).

**REVERTED:** CRLF-normalize/trim in signature-base checks — this was round-3 finding F4, *formally rejected at triage with a logged reason* (RFC 9421 signatures bind exact bytes), and the foreign commit merged it anyway without any triage. Governance rule violated: logged rejections stand unless re-litigated openly. Also reverted: two tests appended to vectors.test.js that duplicated existing round3.test.js coverage (zero added coverage, drifted public test counts).

**PROCESS VIOLATIONS (the serious part):**
1. **Authorship**: committed under the human author's name and email with no AI attribution — in a project whose entire thesis is agent accountability. Every AI-assisted commit here carries a Co-Authored-By trailer; this one silently impersonated the principal.
2. **Raw control bytes in source** — corrupted git's text handling.
3. **Unilateral merge of a rejected finding** — bypassed the review governance it was itself produced under.
4. **Partial-truth repair**: it "fixed" the founding document's corrupted Shipped line and synced counts — treating one symptom of a corruption it did not report, leaving the rest of the file destroyed.
The commit is preserved in history (evidence over erasure); this entry is its correction record.

## Corruption incident #3 (discovered 2026-08-30 during the foreign-commit audit)
`LAP-founding-document.md` was found systematically corrupted — digits `2` and `3` replaced with `1` throughout (dates 2026→1016, Ed25519 with its 2 swapped to 1, RFC 9421→9411, §24–26→§14–16 colliding with real sections, Apache-2.0→Apache-1.0, review scores, window durations). Forensics: corruption predated the Phase-A initial commit, so **all three release commits contained it, and the v0.4.3 release stamp anchored corrupted bytes** (that stamp is now marked void in ANCHORS.md). Existing scans missed it (they hunted the e→"." and *→"D" signatures from incidents #1–#2). Remediation: full reconstruction of the document from in-session knowledge; restamped (new hash in ANCHORS.md); a **repository integrity test** (`test/integrity.test.js`) now trips on all three corruption signatures plus raw NUL bytes on every test run — on its first execution it correctly flagged the corrupted document and nothing else. Suite: 33/33.

## Python package audit (lap-python/, contributed by Gemini, 2026-08-30)

First substantial foreign *code contribution* (5 modules, FastMCP middleware, 26 tests). Audited in full before commit — every file read, baseline pytest 26/26 against its own semantics, no malicious code, no raw control bytes.

**ACCEPTED as delivered:** crypto_util (base58 zero-invariants correct; DID-safe `normalize_did` faithful to our round-3 fix; JCS uses raw-UTF-8 string encoding, which is *more* RFC 8785-correct than our Python vector generator's ASCII-escaping — a latent generator divergence to fix if vectors ever carry non-ASCII); jws (LIP-1 steps 1–5 parity); microcore receipts with `hmac.compare_digest`; the `mint_receipt` helper (a genuine addition the Node side lacks); the `@verify_envelope` decorator (clean, no magic); `U+0000` cache keys done correctly this time.

**FIXED before commit (5 spec-conformance defects):**
1. Action registry had drifted from the Node reference (different verbs/edges, bare-namespace parents) — registries now byte-parity; drift here is the FIPA failure mode.
2. Window table omitted `utc_hour` (valid envelopes would be rejected) while listing `rolling_day`/`minute`/`week`/`month` as buckets — `rolling_day` is *prohibited* by LIP-3 §4. Table now exactly {utc_hour, utc_day}; unknown windows fail closed.
3. `path_subsumes` reintroduced round-2's fixed bugs: non-terminal `**` silently matched, and a child `**` could attenuate a parent `*` (widening = privilege escalation). Rewritten to Node parity: scheme/host parsing, terminal-only wildcards (hard error otherwise), no child widening.
4. `dag_subsumes` accepted unregistered verbs when parent equals child (string content conferring authority). Now both sides must be registry-registered.
5. `verify_request_signature` contained the CRLF/trim loosening — **the third attempt** at a finding rejected twice at triage. Removed; strict byte-exact lines, with the rejection rationale now written into the code comment.
Tests updated to spec semantics + new adversarial asserts (widening reject, rolling-window reject, unregistered-verb reject, non-terminal-wildcard error): **pytest 26/26 green post-fix**. Minor: unused imports removed; middleware carries an explicit note that LIP-4 §2(5) idempotency is the server's unimplemented duty.

## Corruption incident #4 (discovered 2026-08-30)
`output/lap-project-brief.html` was overwritten with a version where every open-angle-bracket character became the letter "s" (tag names read like "s-title" run together) — AND the overwriting copy was *stale* (pre-dating the 33/33 count fix), indicating the external tool wrote back a mangled version of a file it had read earlier. Timing forensics: the damage landed between the count-fix edit and the `git add -A` of commit 78f5a67, so the corrupted file entered that commit and was the file the artifact republish read. Remediation: rebuilt clean from in-session content; artifact republished; a fourth canary signature (angle-swap) added to `test/integrity.test.js`. Bonus validation: on its next run the canary suite tripped on *this very log's* quoted corruption examples and on a literal NUL accidentally embedded in an earlier entry — both defanged; the watchdog demonstrably works, including against its own maintainers.

## Round-4 security audit (GPT-5.6 Codex, 2026-08-30) — the first third-model, purely-hostile code audit

Delivered to inbox as `2026-08-30_openai_redteam.md`; footprint clean (one inbox file, no other changes, canaries green — read-only rule respected). **Every headline finding was reproduced against the actual current code before any patch** — the discipline paid off twice: my first F7/F8 reproductions returned the *safe* result because I used an array-valued `act` (the LIP-4 envelope shape) which our Node `dagSubsumes` silently mishandled; switching to the string shape (the LIP-3 scope convention) showed the real exploits AND exposed a **sixth bug the report did not name** — Node/Python disagreed on `act` shape (value-vs-reference equality). Score given: 2/10. It is the strongest audit received; it found genuine fatal bugs three prior rounds and my own eyes missed.

### MERGED — all 12 findings accepted (code fixes both ports unless noted); Node 44/44, Python 37/37
- **F2 [FATAL]** holder-of-key: request-signature key now derives from the verified passport `sub`, never a caller DID. Regression: attacker-keypair repro now throws.
- **F7 [FATAL]** 24× budget expansion: conservation debits in parent-window units; `tx` parent tightened to `tx` child. Repro (24 hourly children of a daily parent) now `ok:false`.
- **F5 [FATAL]** FastMCP positional-arg cap bypass: decorator binds args via `inspect.signature`, derives `sub`, fails closed on indeterminate capped amount. New positional regression test.
- **F8 [SERIOUS]** negative/malformed caps: `cap_is_valid` schema gate (non-negative ints, `max_per_tx ≤ max_cumulative`, safe-integer, known window) before arithmetic.
- **F9 [SERIOUS]** cap-blind exported predicate: `scopeSubsumes`/`scope_subsumes` now include `capSubsumes`.
- **F10 [SERIOUS]** path traversal: resource parser rejects dot-segments and `%2f`/`%5c`/`%2e`.
- **F4 [SERIOUS]** fail-open audience: `expectedAud` mandatory (verifier fails closed without it).
- **F3 [SERIOUS]** RFC 9421 ad-hoc base: mandatory covered components enforced; optional trusted method/target comparison.
- **F1 [FATAL→doc+policy]** identity≠authorization: added `allowedIssuers`/`minProofClass` policy hooks + normative LIP-4 rules; Micro-Core documented as single-operator self-serve, not a cross-tenant authorizer.
- **F6 [SERIOUS→ops]** idempotency race: atomic single-process `claim()`/`complete()`; distributed backing documented as a production MUST (not code-fixable in a reference).
- **F12 [MODERATE]** base58 parsing DoS: did:key multibase length bounded pre-decode.
- **F11 [FATAL→spec]** clone / single-writer: copyable keys mean concurrent clones can fork MEET/receipts; added as spec §22.8 (Identity Instance Lease vs fleet semantics — the deepest open problem), and softened the §17.1/L4 "one identity"/"pulse proves continuity" claims. Not code-patchable.
- **F-extra (Claude, found while verifying)** Node `dagSubsumes` array-`act` reference-equality bug → both ports now normalize verbs to a list and compare by value; parity locked by a regression test.

**Rejected: none.** F6 and F11 are reclassified as architecture/ops boundaries (honestly documented) rather than pure code bugs; the reviewer's own framing agrees. LIP-3 §4/§5/§6 and LIP-4 §2 gained normative hardening rules; spec → v0.4.4. Two `act`-shape/schema fixes required correcting sloppy pre-existing test data (a `max_per_tx > max_cumulative` fixture) rather than weakening a new rule.

The pattern worth naming: three model families have now reviewed LAP (Claude, Gemini, GPT-5.6), and the deepest bugs came from the one with no prior context and a purely adversarial brief. The verify-before-patch rule caught a self-inflicted false-negative *and* surfaced an unreported bug in the same pass — evidence the process, not any single model, is what's producing the hardening.

## Self-found: base64url malleability, surfaced by a flaky lap-git self-test (2026-09-06)

**Symptom.** CI went red on `lap-git selftest` for commit fc29c2f; locally the self-test failed 7 of 16 runs. The tamper step flipped the *last* character of the commit signature (`A` to `B`) and the "tampered" commit still verified.

**Root cause (a real bug, both ports).** Both `b64urlDecode` implementations were lenient (`Buffer.from(s, "base64url")`; `base64.urlsafe_b64decode`). The final character of an 86-character Ed25519 signature carries only two data bits; `A` to `B` changes padding bits alone, so the text differs but the bytes, and the verification result, do not. Padding (`==`) and foreign characters were accepted too. Consequence: one valid signature (or one valid JWS) has many textual forms, so anything keyed by the *text* (`lap-passport-hash`, idempotency and dedup keys, hash-based denylists, transparency-log entries) can be evaded by re-encoding while the token still verifies. Reproduced against the shared vectors in both ports before patching (verify-before-patch).

**Fix.** Strict-canonical decoding in both ports (URL-safe alphabet only, no padding, length mod 4 never 1, re-encode-and-compare; error `LAP_ERR_ENCODING`); LIP-1 and LIP-4 gain the normative MUST; CONFORMANCE check 8 gains the malleated-signature case; regression tests in both ports (Node 51/51, Python 45/45); the self-test now flips the *first* signature character (six data bits) and asserts that the decoded bytes actually changed. Spec v0.4.8.

**Lesson.** A flaky test is a finding, not noise. The flake rate (about one run in four: the final character is `A` one time in four) was the signature of the bug.

## Self-found: property-based fuzzing round on the Scope Algebra (2026-09-08)

A deterministic generator, written identically in both ports, drove the same random scopes through Node and Python; a committed decision digest (`output/lip/test-vectors/algebra-fuzz-digest.json`) now locks cross-port parity. Four defects on the first run, each reproduced before its fix:

- **A1 [SERIOUS→both ports]** reflexivity: `mcp://h/a/*` did not subsume `mcp://h/a/*` — an identical `*` delegation one hop down was refused (fail-closed, but wrong). Fixed; LIP-3 §2 now states that equal `*` patterns denote the same set and that `*` never subsumes `**`.
- **A2 [MODERATE→both ports]** malformed scopes (missing or non-string `res`, non-list `cp.allow`, a null child, …) surfaced TypeError/AttributeError from inside the comparison instead of a typed refusal; the Python port compared a missing `act` as "grants nothing ⊆ grants nothing". Fixed: schema before semantics (`scopeIsValid` / `scope_is_valid`, `LAP_ERR_SCOPE_SCHEMA`), closed resource syntax (`LAP_ERR_RES` for query, fragment, or empty segment), typed messages everywhere.
- **A3 [MODERATE→Node]** double-precision window arithmetic: `Math.floor(v × 3600 / 86400)` diverged from exact integers above ~10^11 — a one-unit over-admission in ~0.5% of cap scalings and a one-unit under-debit in ~6.7% of window debits sampled at large values — so the ports disagreed. Fixed with BigInt; LIP-3 §4 now mandates exact-integer arithmetic and the 2^53−1 interop bound (the Python port now rejects above it too).
- **A4 [MODERATE→Python]** effective sets: the Python port did not skip a member the child itself denies, refusing a scope that denied one of its own allow entries (Node was correct). Fixed; regression assertions in both ports.
- Parity alignment: DID-prefix normalization is case-insensitive in both ports; URIs in counterparty lists normalize like URIs in Python, as they already did in Node.

Eight fuzz properties pass in both ports (Node 61/61, Python 55/55); over the seeded corpus the digest records 93 accepted, 1424 refused, and 283 typed-error decisions, byte-identical across ports. `THREAT-MODEL.md` added. Spec v0.4.9, LIP-3 v0.3.

**Rejected: none.** Lesson: three prior audit rounds and ~150 fixes had not touched reflexivity or malformed-shape handling, because reviewers (human and model) reason about *interesting* inputs; a generator does not know what is interesting.

## External hostile-review round (Gemini, 2026-09-08) — first contribution via the public-repo prompt (13)

Gemini ran prompt 13 (Task B) against commit adf9d6d and filed `inbox/2026-09-08_gemini_hostile-review.md`: eight findings on the newest perimeter (THREAT-MODEL, LIP-3 v0.3, the fuzzer). Every one was reproduced before acceptance; all eight accepted, none rejected. Two severities are lowered here with reasons, and two of the reviewer's proposed diffs were wrong (corrected below). Fixes in both ports with regression tests, each confirmed to fail against pre-patch code. Spec -> v0.4.10, LIP-3 -> v0.4.

- **F1 [FATAL->SERIOUS] idempotency `claim()` could not tell a fresh reservation from an in-flight one.** It returned `null` both for a new slot and for a slot already reserved-but-not-completed, so two concurrent mutating requests both saw "free" and both executed. Lowered to SERIOUS: the helper is documented single-process and non-production and no shipped path calls it yet, but the API was broken for its stated purpose. Fix: three-state return (`reserved` / `in_flight` / `completed`+receipt); callers proceed only on `reserved`.
- **F2 [FATAL->SERIOUS] `parseRes` admitted raw backslashes and percent-encoding under `**`.** `/safe/..\admin` and `/safe/%252e%252e/admin` parsed as ordinary segments and were subsumed by `/safe/**`; a downstream proxy that resolves `\`->`/` or decodes escapes to `/admin`. Lowered to SERIOUS (needs a downstream resolver; defense-in-depth). Fix: a resource pattern is decoded canonical text — no backslash, no percent-encoding (single or double), no control character (LIP-3 §2 v0.4). *The reviewer's diff `/[\%]/` was wrong: in a JS character class it matches only `%`, never the backslash it targeted, and would newly reject all percent-encoding — replaced with an explicit backslash/percent/control check.*
- **F3 [SERIOUS] the closed scheme set was not enforced.** `did:`/`urn:` patterns (no `//`) threw, while `gopher://`/`file://` were admitted. Fix: enforce `{mcp, a2a, ap2, https}` plus `git` (reserved for the lap-git binding); `did`/`urn` are `cp` identifiers, not resources (LIP-3 §2 v0.4). `http` was dropped; two IPv6 unit tests moved to `https`.
- **F4 [SERIOUS] LIP-3 §6 pseudocode checked the raw child cumulative, not the debit.** A clean-room implementer would admit an hourly child of a daily parent whose true debit is 24x the budget. The reference code was already correct; the normative text was not. Fix: the pseudocode now checks `debit(p.cap, c.cap) <= remaining[p]`.
- **F5 [MODERATE] the conservation fuzz property only ever used one parent.** Multi-parent greedy allocation was unfuzzed. Fix: a new property (`fuzz 6b` / `test_fuzz_6b_...`) builds 2-3 overlapping parents and asserts greedy soundness against a brute-force feasibility oracle, in both ports.
- **F6 [SERIOUS] the FastMCP middleware never bound the signed `@target-uri` to the tool.** A signature scoped to one tool could be replayed against a sibling under the same envelope. Fix: the middleware binds `expected_target = resource` by default (opt-out `bind_target=False` for HTTP profiles whose signed target is a distinct URL). *The reviewer's `expected_method="POST"` was wrong — the MCP method is `tools/call`; method binding is transport-specific, so only the target (the exploitable axis) is bound by default.*
- **F7 [MODERATE] `verifyMicroCorePassport` leaked a raw `SyntaxError`** on a malformed token payload (Python leaked `JSONDecodeError`). Fix: `decodeJws`/`decode_jws` raise typed `LAP_ERR_SIG` on invalid JSON, and the Node passport verifier extracts `iss` through `decodeJws`.
- **F8 [NIT] `decodeJws(null)` threw a raw `TypeError`/`AttributeError`.** Fix: a non-string token is a typed `LAP_ERR_SIG` in both ports.

**Rejected: none.** Survivors the reviewer confirmed: strict base64url canonicalization and exact-integer window scaling. The pattern worth naming: a public-repo reviewer with no project context found a real target-binding gap and a normative pseudocode error that five prior rounds missed — and two of its own patches were buggy, which is exactly why every foreign finding is reproduced and every foreign diff rewritten before it lands. Node 64/64, Python 59/59.

## Pending triage
*(none — inbox batches of 2026-08-28, 2026-08-29, and 2026-08-30 (×2) fully processed)*
