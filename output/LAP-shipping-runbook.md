# LAP Shipping Runbook (v2 — post-review)

*The single document that takes LAP from "nothing public" to "launched and measured." Working doc, not spec. Revised after a gap review; everything marked ✅ was verified, not assumed.*

## How to use this (it doubles as a resume-prompt)

- Work the phases **in order**; the critical path is real (venue filings need a live repo URL; the endorser needs a readable PDF).
- Tags: **[ME]** I execute now · **[YOU]** needs your account, hands, or name · **[ME→YOU]** I pre-stage, you run one command / click submit.
- To resume in any future session: *"do LAP shipping step N"* or *"do Phase N."*
- Launch copy is paste-ready in **Appendix A**; exact commands in **B**; gotchas in **C**; my limits in **D**; the objections FAQ in **E**; the weekly metrics sheet in **F**.

## ⚠️ Hard rule: personal account, never the company account

Everything public uses **your personal identity only**: GitHub (personal account or a personal org), arXiv, asciinema, YouTube, and every email. Your machine's *global* git identity is the company one; this repository pins the personal identity **locally**, and every commit in history is already under it (verified). Before any commit from a new clone or machine, run `git config user.email` inside the repo and confirm it prints your personal address. The `SECURITY.md` contact and `CITATION.cff` author are already the personal address.

## Status snapshot (verified)

- **Green:** Node 61/61 · Python 55/55 · single-process demo 191 checks (+ tamper caught, exit 1) · networked demo (2 processes, IPv4 + IPv6) · `lap-git` self-test.
- **Clean:** no secrets or private-key files tracked; company domain appears nowhere; working tree committed via `lap-git`; local backup zip taken (`backups/`, git-ignored).
- **Consistent:** every public number swept — README, brief (md + html), founding document header and "Shipped" line, paper, essay all say v0.4.9 / 51 / 45 / five rounds / ~150.
- **Ready:** CI workflow, `SECURITY.md`, `CITATION.cff`, a `docs/` folder for GitHub Pages (visual demo, terminal playback, asciinema cast), the paper refreshed to v1.1-draft (clone problem as open problem #7, two implementations, lap-git, three-model acknowledgments) and rendered to print-ready HTML, the essay refreshed with the case-study hook.
- **Placeholders that remain, on purpose:** `https://github.com/atharnouman/living-agents-protocol` in the essay and paper; `repository-code` absent from `CITATION.cff`; no CI badge in the README yet. All three resolve in **Phase 1A step 4** the moment the real URL exists — no guessed URLs anywhere in public files.

---

## Phase 0 — Pre-flight ✅ [ME] done
Secret scan · full green check · local backup · identity check.

## Phase 0.5 — Publication-readiness sweep ✅ [ME] done (hard gate — re-run before any *future* release)
Numbers/version sweep · unpublished-package fix (`pip install -e .`, no PyPI claim) · placeholder-URL removal · CI · SECURITY · CITATION · Pages folder · essay + paper refresh · paper HTML. **Re-run rule:** before any public release, grep every public doc for the current version and test counts; drift has bitten this project four times.

---

## Phase 1 — Start these TWO in parallel, day one

**1A — GitHub, personal account** [YOU] + [ME→YOU]
1. [YOU] Create the repo under your **personal** account (or a personal org). Suggested name: `living-agents-protocol`. Public; no auto-README.
2. [YOU] Description + topics: Appendix A.5.
3. [ME→YOU] I re-run the secret scan; you run the two push commands (B.1).
4. [ME] **URL sweep** once the URL exists: replace `https://github.com/atharnouman/living-agents-protocol` in essay + paper, add `repository-code` to `CITATION.cff`, add the CI badge to the README (B.2), re-render the paper HTML, restamp, commit via `lap-git`, push.
5. [YOU] **Enable GitHub Pages** → Settings → Pages → Source: *Deploy from branch* → `main` / `/docs`. Within minutes `https://<user>.github.io/<repo>/` serves the demos. That URL becomes the "90-second demo" link.
6. [YOU] Confirm CI went green on the first push (Actions tab). If a job is red, tell me before posting anything.

**1B — arXiv endorsement, personal email** [YOU] — corrected order
1. [YOU] Print the paper to PDF: open `output/LAP-position-paper.html` → Ctrl+P → Save as PDF (after step 1A.4 so the URL is real).
2. [YOU] Create an arXiv account with your **personal** email. **Start a new submission** (cs.MA primary; cross-list cs.CR). arXiv will tell you an endorsement is required and give you an **endorsement code / link** — you cannot request endorsement before this step.
3. [YOU] Identify 1–2 established arXiv authors in cs.MA or cs.CR (someone you cite, or whose work is close). Send the email in A.1 **with the PDF attached**.
4. Expect days. It runs in the background while everything else proceeds.

---

## Phase 2 — Film the demo [YOU]
Follow `LAP-recording-playbook.md`. Minimum: one ~70s terminal MP4 of `node conductor.mjs --present` in the styled terminal; the must-capture beat is **SIGKILL → SUSPENDED/HELD → auto-restore**. Nice-to-have: the visual-UI MP4 (record the Pages `demo.html`). Hosting: upload the MP4 to **YouTube (unlisted is fine)** or attach it to the GitHub Release (Phase 3.3); the cast goes to **asciinema.org** (`asciinema upload docs/lap-overnight.cast`). Never link the private claude.ai artifact URLs.

---

## Phase 3 — Go public

1. [ME] **Freeze + re-anchor** after the URL sweep (B.3) so priority locks to exactly the published bytes.
2. [ME→YOU] **Essay** — I finalize `LAP-essay.md` with the real links; you publish it (personal blog / Substack / Medium — never the company blog).
3. [ME→YOU] **Release tag** — I create the annotated tag `v0.4.9`; you push it (B.4) and create the GitHub Release from A.7 (attach the MP4 later, when the film exists). Stable links for every post.
4. [YOU] **Show HN** — A.2. Post Tue–Thu, ~8–10am US Eastern, when you can babysit comments for ~4 hours. Answer with facts; never argue; a cool reception is not failure.
5. [YOU] **LinkedIn + X** — A.3, A.4. First mention everywhere: *Living Agents Protocol (LAP)*.

---

## Phase 4 — arXiv [YOU] submits
When the endorsement lands: submit the PDF (cs.MA; cross-list cs.CR) with the repo URL in the abstract's last line. Then [ME] add the arXiv ID to the README and paper header, restamp, commit.

---

## Phase 5 — Infiltrate (where distribution already lives) [ME] drafts · [YOU] submits
1. **A2A extension proposal** — Autonomy Envelope + pulse-gated suspension as an A2A capability (issue/discussion on the A2A repo). ~60% of effort here.
2. **W3C AI Agent Protocol CG** — join (free, remote); post the opener (A.6); offer the lifecycle/Pulse material as a contribution.
3. **OWASP agentic-security** — a threat→mitigation mapping (which LAP mechanism blunts which listed threat).
4. **Champion outreach (3 tailored notes)** — *after* the push, I pull real maintainer names from the A2A and MCP repos' `CODEOWNERS` / `MAINTAINERS` / recent-merger lists (never from memory — the earlier review rejected unverified names), and draft three short, specific notes each pointing at the one mechanism that helps *their* roadmap. You send them.
5. **Conformance challenge outreach** — post `CONFORMANCE.md` to one Rust and one Go community as an "implement this small protocol" exercise. Logged as *solicited* signals.
6. **ERC-8004 / AGNTCY** — companion field-notes; cite-and-differ.

---

## Phase 6 — Measure & hold [YOU]
- Log **Appendix F** weekly. The day-60 read needs numbers, not impressions.
- **Day-60 gate:** ≥3 external PRs or one mainstream-framework plugin accepted → double down; no venue response in 45 days on a track → archive it. Record solicited vs unsolicited separately.
- **Tripwire:** ≥2 *unsolicited* external implementations → the deferred institutional plans come off the shelf. Until then, byline-not-body.
- **After ~1 week:** upgrade the OpenTimestamps proofs so "Bitcoin-timestamped" is *confirmed*, not pending (B.5). [ME]

## Calendar (rough)
| When | What |
|---|---|
| Day 0 | 1A push + Pages + CI green · 1B arXiv account, start submission, send endorsement email |
| Day 1–2 | Film; upload MP4 + cast; URL sweep, re-anchor, release tag |
| Day 3 (Tue–Thu) | Essay live → Show HN → LinkedIn/X |
| Week 2 | arXiv submission (when endorsed) · A2A proposal · W3C opener |
| Weeks 2–4 | OWASP mapping · champion notes · conformance outreach |
| Week 8–9 | Day-60 gate |

---

## Appendix A — Launch copy (paste-ready)

### A.0 — Launch-day order (2026-09-08 refresh; everything below is [YOU] unless marked)
1. **GitHub Release** for `v0.4.9` — repo → Releases → *Draft a new release* → choose existing tag `v0.4.9` → title + body from A.7 → *Publish release*.
2. **Social preview** — Settings → General → *Social preview* → upload `docs/social-preview.png` (1280×640). Without it, links on X/LinkedIn/HN render blank.
3. **Essay** — publish `output/LAP-essay.md` on your personal blog / Substack / Medium (never the company blog). Send me the URL: [ME] adds it to the README "Read" line and restamps.
4. **Show HN** — A.2. Tue–Thu, 8–10 am US Eastern, when you can babysit comments for ~4 hours. Facts, no arguing; a cool reception is not failure.
5. **LinkedIn + X** — A.3, A.4, the same day, after HN is up (link the HN thread + repo).
6. **Champion notes** — `outreach/champion-outreach.md` (local, never committed): A2A issue first, then the MCP Discussion, then the W3C CG intro. Re-verify every maintainer name at the cited URL first.
7. **arXiv track, in parallel** — print `output/LAP-position-paper.html` to PDF; create the account; start the submission (cs.MA, cross-list cs.CR) to get the endorsement code; send A.1.
8. **Appendix F** every Monday. Solicited vs unsolicited, always separated.

### A.1 — arXiv endorsement email (send from your personal email, PDF attached)
> **Subject:** arXiv endorsement request — cs.MA — accountable persistent AI agents
>
> Dear Dr. [Name],
>
> I'm an independent researcher preparing a first arXiv submission and, as a new author in cs.MA, I need an endorsement. I'm writing to you because of your work on [specific paper/topic].
>
> The paper, *"The Living Agents Protocol: A Reference Model and Research Agenda for Persistent Autonomous Agents"* (attached), proposes a reference model plus implemented wire mechanisms for a gap current agent protocols (MCP, A2A) leave open: how a persistent agent proves who it is, whose authority it carries, whether it is alive, and what it did. It ships two interoperating open-source implementations (cross-checked by a shared fuzzing corpus), a runnable two-process demo, registration in a public transparency log, a written threat model, and an explicit open-problems section — including the ones we cannot yet solve.
>
> Repository: https://github.com/atharnouman/living-agents-protocol
>
> If you're willing, arXiv's endorsement link is below; if not, no worries at all, and thank you for your time.
>
> [arXiv endorsement link / code]
>
> With appreciation,
> Athar Nouman

### A.2 — Show HN
> **Title:** Show HN: An identity and accountability layer for always-on AI agents
>
> Agents recently got standard ways to use tools (MCP), talk to each other (A2A), and pay (AP2). Nothing standardizes an agent's *existence*: who it is, which human answers for it, what it may do unsupervised, whether it's running right now, and how its actions are proven afterward.
>
> The Living Agents Protocol (LAP) is a reference model plus small, implemented wire mechanisms for that gap. It's a v0 draft by one author — no consortium, and no claim that the "agent economy" is imminent. But the pieces are real and runnable:
>
> - Two interoperating libraries (Node with zero dependencies; Python) that produce byte-identical results against shared test vectors, plus a property-based fuzzer whose decision digest fails the build if the two ports ever disagree.
> - A demo where two strangers' agents meet, verify each other, transact under a budget, one *crashes* (a real SIGKILL; two real processes over real sockets), the other's authority suspends automatically, a pending order is held, and on recovery it completes. A morning replay re-verifies every signature.
> - A 15-minute tutorial that puts it on a real MCP server: a payment tool that refuses anything outside the caller's signed envelope and returns a signed receipt.
> - Registration that isn't self-asserted: one command puts an agent's genesis record in Sigstore's public Rekor log and verifies the inclusion proof with the library's own Merkle code.
> - `lap-git`: the same mechanisms applied to commits, built because AI agents working in this very repo made an unattributed, out-of-scope commit. Write-up, my own mistakes included: https://github.com/atharnouman/living-agents-protocol/blob/main/CASE-STUDY.md
>
> Honest limits up front: the payment rail is mocked; key custody, principal-proofing, and the clone problem are documented open problems; THREAT-MODEL.md says what is *not* defended. Five adversarial review rounds so far across three model families, ~150 verified fixes, all logged with the rejections. Apache-2.0 code, CC-BY spec.
>
> Repo: https://github.com/atharnouman/living-agents-protocol · Demo: https://atharnouman.github.io/living-agents-protocol · Zero-install: the Codespaces badge in the README.

### A.3 — LinkedIn
> While building an open standard for always-on AI agents, the AI agents *building it* handed me the clearest argument for why it's needed: one made a commit under my name, with no record of which agent acted or whether it stayed in scope.
>
> That's not a rogue-AI story. It's a plumbing story — git has no concept of "which agent, under whose authority, within what scope," so capable tooling does the accountable-looking thing by default and nobody can prove what happened.
>
> The **Living Agents Protocol** is a small, open, implemented answer: a passport that says who an agent is and who's responsible, an envelope that bounds what it may do, and a signed record of what it did. There's a runnable demo (two agents transact overnight, one crashes, authority suspends automatically, the morning replay verifies everything), a 15-minute tutorial that puts it on a real MCP server, and a tool that applies it to git commits.
>
> v0 draft, honest about its open problems. Code Apache-2.0, spec CC-BY. Repo + demo: https://github.com/atharnouman/living-agents-protocol

### A.4 — X / Twitter thread
> 1/ Agents got MCP (tools), A2A (each other), AP2 (payments). Nothing standardizes an agent's *existence*: who it is, who answers for it, what it may do alone, whether it's alive, what it did. The Living Agents Protocol is a small, implemented answer. 🧵
>
> 2/ The demo: two strangers' agents meet, verify each other, transact under a budget while both humans sleep. Then one CRASHES. The other's authority suspends automatically, a pending order is held, recovery completes it. Morning replay re-verifies every signature.
>
> 3/ Not a mock: two real OS processes over real sockets; the crash is a real SIGKILL; the "suspension" is a real connection failure. Two interoperating libraries (Node + Python) produce byte-identical signatures.
>
> 4/ Best part: the AI agents building the repo gave me the argument for it — one committed under my name, out of scope, with no record of which agent acted. So I built `lap-git`: a passport + path envelope enforced before a commit exists.
>
> 5/ Want it on your own MCP server? There's a 15-minute tutorial: a payment tool that refuses anything outside the caller's signed envelope and returns a signed receipt. Verified in CI on the official SDK.
>
> 6/ v0 draft, one author, no consortium, honest about open problems (key custody, principal-proofing, the clone problem) — and a written threat model that says what is NOT defended. Apache-2.0 / CC-BY. Repo + demo 👇 https://github.com/atharnouman/living-agents-protocol

### A.5 — GitHub description + topics
> **Description:** An identity, authority, and lifecycle layer for always-on ("living") AI agents — reference model + implemented wire mechanisms. The existence layer under MCP/A2A.
>
> **Topics:** `ai-agents` `agent-protocol` `mcp` `a2a` `did` `ed25519` `verifiable-credentials` `agent-identity` `accountability` `protocol` `zero-dependency`

### A.6 — W3C CG opener
> Hi all — I've been working on the lifecycle/presence side of agent protocols: how a persistent agent proves it's alive, how authority decays when it goes dark, and how a restart isn't a new identity. It's a small implemented model (two interoperating libraries, a runnable two-process demo) that deliberately slots under MCP/A2A rather than competing. I'd value this group's read on the presence/pulse mechanism specifically — https://github.com/atharnouman/living-agents-protocol. Happy to write it up as a contribution if there's interest.

### A.7 — GitHub Release notes for v0.4.9 (paste as the release body)
> **Title:** v0.4.9 — fuzzed Scope Algebra, threat model, real registration, MCP tutorial
>
> Everything since the first public tag (v0.4.6), newest first:
>
> - **Property-based fuzzing of the Scope Algebra (v0.4.9, LIP-3 v0.3).** A generator written identically in both ports drives the same random scopes through Node and Python; a committed decision digest fails the build if they ever disagree. The first run found four defects — an identical `*` delegation refused, language-level errors on malformed scopes, a one-unit floating-point divergence between the ports, and a missing effective-set rule in Python — all fixed with regression tests.
> - **THREAT-MODEL.md.** Assets, actors, sixteen defended threats each tied to the code that enforces the defence and the test that proves it, and the residual risks stated plainly.
> - **Canonical encoding made normative (v0.4.8).** Both decoders now reject non-canonical base64url; a lenient decoder gave one signature many textual forms, which text-keyed state could not distinguish.
> - **Add LAP to your MCP server in 15 minutes.** `examples/mcp-server/`: a FastMCP server whose payment tool refuses anything outside the caller's signed envelope and returns a signed receipt; the stdio round-trip runs in CI.
> - **Registration made real (v0.4.7).** One command registers a Genesis Record in Sigstore's public Rekor log and verifies the inclusion proof and signed timestamp with the library's own RFC 6962 code.
> - **Zero-install Codespaces**, an animated README hero built from the live demo, IPv4 + IPv6 networked demo.
>
> Tests: Node 61/61, Python 55/55, demo replay 191 checks with tamper detection, lap-git self-test. Every commit since v0.4.6 is signed by a `lap-git` agent passport (`node lap-git/lap-git.mjs verify`); documents are Bitcoin-timestamped (`output/anchors/ANCHORS.md`). Full history: founding document §23 and `llm-collab/IMPROVEMENTS-LOG.md`.
>
> Spec CC-BY-4.0 · code Apache-2.0 · demo: https://atharnouman.github.io/living-agents-protocol/

---

## Appendix B — Exact commands

**B.1 Push (after creating the empty repo under your personal account)**
```bash
cd E:\LivingAIAgents
git config user.email            # MUST print your personal address
git remote add origin https://github.com/atharnouman/living-agents-protocol.git
git branch -M main
git push -u origin main
```

**B.2 CI badge line for the README (I add it in the URL sweep)**
```
[![ci](https://github.com/atharnouman/living-agents-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/atharnouman/living-agents-protocol/actions)
```

**B.3 Re-anchor (I run)**
```bash
python output/anchors/lap_stamp.py output/LAP-founding-document.md README.md
# then update output/anchors/ANCHORS.md
```

**B.4 Release tag (I create; you push)**
```bash
git push origin v0.4.9
# then GitHub → Releases → Draft from tag v0.4.6 → attach the MP4 and docs/lap-overnight.cast
```

**B.5 Upgrade the Bitcoin proofs (~a week after stamping; I run — needs the upgrade path added to lap_stamp.py or an ots CLI on a non-Windows box)**
```bash
ots upgrade output/LAP-founding-document.md.ots && ots verify output/LAP-founding-document.md.ots
```

**B.6 Anyone can verify the repo in 5 minutes (drop into a reply when a skeptic asks)**
```bash
cd lap-reference && node --test test/                                      # 61/61
cd ../lap-python && pip install -e . pytest && python -m pytest tests -q   # 55/55
cd ../lap-demo/net && node conductor.mjs && node verify.mjs                # 2 processes, receipts verified
cd ../.. && node lap-git/lap-git.mjs selftest                              # scope refused, tamper caught
```

---

## Appendix C — Gotchas & risks
- **Personal account only.** Re-check `git config user.email` in any fresh clone. Never post from the company blog/handles.
- **Don't over-polish.** Every strategy review concluded ship > improve. Phase 0.5 is done; stop touching the spec until the gate.
- **HN is allergic to hype.** The copy leads with limits on purpose. Answer criticism with facts; a cool reception is not failure.
- **Attribution first, always** — "Living Agents Protocol" in the first sentence.
- **The clone/single-writer problem will be raised.** Good: it's open problem #7 in the paper and §22.8 in the spec. Point to it.
- **Solicited ≠ demand.** Challenge-driven implementations are logged as weaker signals.
- **Private state:** `.lap-git/`, `lap-demo/net/out/`, `lap-demo/out/`, `backups/` are git-ignored. Never `git add -f` them.
- **No guessed URLs in public files.** `https://github.com/atharnouman/living-agents-protocol` placeholders resolve only in 1A.4.
- **Don't found the consortium.** Held in reserve until the tripwire.

## Appendix D — What I can and can't do
**Can, now:** everything in [ME]: text finalization, URL sweep, re-anchor, tagging, drafting every filing and note, keeping CI green, the paper HTML.
**Can't:** create accounts, push, film, post under your name, submit to arXiv, send email. Those are the [YOU] steps; everything up to them is handed over finished.

---

## Appendix E — Likely objections, and the honest answers

- **"FIPA tried this in 1996 and died."** It did — and not for lack of implementation (JADE ran for a decade). It died waiting for a stranger-agent economy that took decades, and its semantic layer demanded agreement nobody had an incentive to give. LAP is designed against exactly that: every mechanism is single-operator-adoptable today, and the permission vocabulary is deliberately tiny and closed. Section 2 of the paper is this argument in full.
- **"This is just JWT/OAuth with new names."** The wire formats *are* deliberately standard (JWS, RFC 9421, JCS, Merkle logs) — inventing crypto would be the mistake. What's new is the semantics layered on them: authority that decays when the agent goes dark, era-stamped reputation, a decidable attenuation algebra with budget conservation, and a handshake that discloses limits before transacting.
- **"Copy the key and you have two agents — your 'one identity' is fiction."** Correct, and we said so first: open problem #7 / spec §22.8. The current mechanisms make a fork *detectable*, not *impossible*; making it impossible needs a single-writer lease with fencing epochs, which we've specified as the next step, not claimed as done.
- **"Where's the demand?"** Honest answer: the stranger-agent economy isn't here yet, and the paper says so. The demand that *is* here is narrower: AI agents already write code, and they already make unattributed, out-of-scope commits — it happened in this repo. That's why the first binding is git.
- **"XKCD 927 — now there are 15 standards."** LAP proposes no competing task, tool, or payment protocol. It binds to MCP/A2A/AP2 and is filed as *extensions* to them. Map, not roads.
- **"One person, AI-written — why trust it?"** Don't trust it; verify it. Two independent implementations pass the same vectors, every review finding (including the rejected ones) is public with reasons, a hostile third-party audit found real bugs that were fixed, and every claim in the README has a command next to it (B.6).
- **"Self-attested registration is worthless."** In the demo, yes — it's labeled as such. The spec's proof classes exist precisely so a verifier treats the *class* as the signal; production requires ≥2 independent transparency-log inclusion proofs.
- **"Why not just gitsign / GPG?"** Use them — lap-git complements, not replaces. They prove *who signed*; lap-git proves *which agent, under whose authority, within what scope*, and refuses the commit otherwise.

## Appendix F — Weekly metrics sheet (fill in every Monday)
| Week | Stars | Unique clones | Top referrer | Issues opened | PRs (unsolicited / solicited) | Venue replies | asciinema/Pages views | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| … | | | | | | | | |
| 8 (gate) | | | | | | | | decision: |

*Next action: create the personal-account repo (1A.1), tell me the URL, and I run the URL sweep, re-anchor, tag, and hand you the push commands — the entire remaining path is then yours to click through.*
