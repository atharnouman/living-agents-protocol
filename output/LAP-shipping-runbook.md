# LAP Shipping Runbook

*The single document that takes LAP from "nothing public" to "launched and measured." Working doc, not spec.*

## How to use this (it doubles as a resume-prompt)

- Work the phases **in order**; the critical path is real (venue filings need a live repo URL).
- Each step is tagged **[ME]** (I execute now), **[YOU]** (needs your account, hands, or name), or **[ME→YOU]** (I pre-stage it, you run one command / click submit).
- To resume in any future session, tell me: *"do LAP shipping step N"* or *"do Phase N"*. I'll pick up here.
- All launch copy is pre-written in **Appendix A** — paste-ready. Exact commands in **Appendix B**. Gotchas in **Appendix C**. My hard limits in **Appendix D**.

## Status snapshot (verified 2026-08-30)

- **Green:** Node 45/45, Python 38/38, single-process demo 191 checks, networked demo (2 processes, IPv4 + IPv6), `lap-git` self-test — all pass.
- **Clean:** no secrets or private-key files tracked; working tree clean; 112 files.
- **Exists:** spec v0.4.6, LIP-1..4, two interoperating libraries, two demos + media kit (visual UI, asciinema cast, recording playbook), case study, conformance challenge, `lap-git`, position paper, essay, manifesto, Bitcoin anchors.
- **Missing:** literally only publication. Nothing is public yet.

---

## Phase 0 — Pre-flight  ✅ DONE [ME]

Secret scan clean · full suite green · working tree clean · launch copy drafted (Appendix A) · push commands staged (Appendix B). Nothing to do; recorded here for completeness.

---

## Phase 1 — Start these TWO in parallel, first  [YOU] + [ME→YOU]

**1A — GitHub repo public.**
1. [YOU] Create the account/org. Suggested: org `LivingAgents` (or your personal account), repo `lap` or `living-agents-protocol`. Public. No auto-README (we have one).
2. [YOU] Set repo description + topics — copy in Appendix A.5.
3. [ME→YOU] I re-run the secret scan and hand you the two push commands (Appendix B.1); you run them.
   *Blocking dependency for Phases 3–5 — everything points at this URL.*

**1B — arXiv endorsement (long lead — start the same day).**
1. [YOU] Skim [`output/LAP-position-paper.md`](LAP-position-paper.md); decide primary category — **cs.MA** (multi-agent) with cross-list **cs.CR** (crypto/security) is the natural fit.
2. [YOU] Identify 1–2 people who are established arXiv authors in cs.MA/cs.CR (a paper you cite, an author whose work you know). Send the endorsement email — copy in Appendix A.1.
   *arXiv requires an endorsement for a first submission in a category; it can take days, so this must not wait for Phase 4.*

---

## Phase 2 — Film the demo  [YOU]

Follow [`LAP-recording-playbook.md`](LAP-recording-playbook.md). Minimum viable: one ~70s terminal MP4 of `node conductor.mjs --present` in the styled terminal. Nice-to-have: the visual-UI MP4 and/or the asciinema cast (already generated at `output/lap-overnight.cast`).
- The one shot that must land: **SIGKILL → SUSPENDED/HELD → auto-restore** (the 20s that is the whole pitch).
- Export 1920×1080 MP4; trim head/tail in Clipchamp. Keep the honest caption (self-attested registration, mocked rail).

---

## Phase 3 — Go public  [YOU] posts, [ME] finalizes

1. [ME] **Freeze + re-anchor** any last edits (restamp founding doc/README to Bitcoin) so priority locks to exactly what's published.
2. [ME→YOU] **Finalize the essay** — I insert the real repo URL + demo link into [`LAP-essay.md`](LAP-essay.md); you publish it (personal blog / Substack / Medium / a repo `BLOG.md`).
3. [YOU] **Repo public** (if you kept it private during setup, flip it now).
4. [YOU] **Show HN** — title + body in Appendix A.2. Post Tue–Thu ~8–10am US Eastern for best odds; then step away, answer comments plainly, never argue.
5. [YOU] **LinkedIn + X** — copy in A.3 and A.4. Lead every first mention with "Living Agents Protocol" for attribution.

First mention rule everywhere: *Living Agents Protocol (LAP)* — the byline is the point.

---

## Phase 4 — arXiv  [YOU] submits, [ME] converts

1. [ME] Convert [`LAP-position-paper.md`](LAP-position-paper.md) to arXiv-acceptable form (LaTeX preferred; PDF acceptable) with the References intact and the repo URL + a software-availability statement.
2. [YOU] Once the endorsement lands, submit under cs.MA (cross-list cs.CR). Link the arXiv ID back from the README.

---

## Phase 5 — Infiltrate (file where distribution already lives)  [ME] drafts, [YOU] submits

~60% of effort on the first item. Each is a draft I write; you post under your name.
1. **MCP/A2A middleware** — an A2A **extension proposal** (the Autonomy Envelope + pulse-gated suspension as an A2A capability). Draft as a GitHub issue/discussion on the A2A repo.
2. **W3C AI Agent Protocol Community Group** — join (free, remote); contribute the lifecycle/Pulse material. I draft the intro post (Appendix A.6 has the opener).
3. **OWASP agentic-security** — a threat→mitigation mapping doc (which LAP mechanism blunts which agentic threat).
4. **Conformance challenge outreach** — post [`CONFORMANCE.md`](../CONFORMANCE.md) to a Rust and a Go community as an "implement this small protocol" exercise. (Remember the §11 rule: these are *solicited* signals — logged as weaker than unsolicited.)
5. **ERC-8004 / AGNTCY** — companion field-notes; cite-and-differ.

---

## Phase 6 — Measure & hold  [YOU]

- **Day-60 gate:** count real pull — external PRs, a framework accepting a plugin, venue replies. Double down where there's traction; archive dead tracks (don't nurse them). Record solicited vs unsolicited implementations separately.
- **Tripwire:** ≥2 *unsolicited* external implementations → the deferred institutional plans (alliance, certification) come off the shelf. Until then, byline-not-body.
- **Kill criteria (honest):** no venue response in 45 days on a track → archive that track. This is a bet with defined stops, not an open-ended commitment.

---

## Appendix A — Launch copy (paste-ready)

### A.1 — arXiv endorsement email
> **Subject:** arXiv endorsement request — cs.MA — accountable persistent AI agents
>
> Dear Dr. [Name],
>
> I'm an independent researcher preparing a first arXiv submission and, as a new author in cs.MA, I need an endorsement. I'm writing to you because of your work on [specific paper/topic].
>
> The paper, *"The Living Agents Protocol: an identity, authority, and lifecycle layer for always-on AI agents,"* proposes a reference model plus concrete, implemented wire mechanisms for a gap current agent protocols (MCP, A2A) leave open: how a persistent agent proves who it is, whose authority it carries, whether it is alive, and what it did. It ships two interoperating open-source implementations, a runnable demo, and an honest open-problems section.
>
> Draft (PDF): [link]. Repository: [link].
>
> If you're willing, arXiv's endorsement system will let you do this with the code below; if not, no worries at all, and thank you for your time.
>
> Endorsement code: [arXiv gives you this]
>
> With appreciation,
> Athar Nouman

### A.2 — Show HN
> **Title:** Show HN: An identity and accountability layer for always-on AI agents
>
> **Body:**
> Agents recently got standard ways to use tools (MCP), talk to each other (A2A), and pay (AP2). Nothing standardizes an agent's *existence*: who it is, which human answers for it, what it may do unsupervised, whether it's running right now, and how its actions are proven afterward.
>
> LAP is a reference model plus small, implemented wire mechanisms for that gap. It's a v0 draft by one author — there's no consortium and no claim the "agent economy" is imminent. But the pieces are real and runnable:
>
> - Two interoperating libraries (Node, Python) that produce byte-identical signatures against shared test vectors.
> - A demo where two strangers' agents meet, verify each other, transact under a budget, one *crashes*, the other's authority suspends automatically, a pending order is safely held, and on recovery it completes — then a morning replay re-verifies every signature. It runs across two real OS processes over real sockets (the crash is a real SIGKILL).
> - `lap-git`: the same mechanisms applied to commits — a passport + path envelope enforced before a commit exists. It exists because AI agents working in this very repo made an unattributed, out-of-scope commit (there's an honest write-up).
>
> Honest limits are stated up front: registration is self-attested in the demo, the payment rail is mocked, and key custody / principal-proofing are open problems. Real Ed25519, real sockets, Apache-2.0 (code) / CC-BY (spec).
>
> Repo: [link] · 90-second demo: [link]

### A.3 — LinkedIn
> While building an open standard for always-on AI agents, the AI agents *building it* gave me the clearest argument for why it's needed: one made a commit under my name, with no record of which agent acted or whether it stayed in scope.
>
> That's not a rogue-AI story. It's a plumbing story — git has no concept of "which agent, under whose authority, within what scope," so capable tooling does the accountable-looking thing by default and no one can prove what happened.
>
> The **Living Agents Protocol** is a small, open, implemented answer: a passport that says who an agent is and who's responsible, an envelope that bounds what it may do, and a signed record of what it did. There's a runnable demo (two agents transact overnight, one crashes, authority suspends automatically, morning replay verifies everything) and a tool that applies it to git commits.
>
> v0 draft, honest about its open problems. Code Apache-2.0, spec CC-BY. Repo + 90s demo: [link]

### A.4 — X / Twitter thread
> 1/ Agents got MCP (tools), A2A (each other), AP2 (payments). Nothing standardizes an agent's *existence*: who it is, who answers for it, what it may do alone, whether it's alive, what it did. The Living Agents Protocol is a small, implemented answer. 🧵
>
> 2/ The demo: two strangers' agents meet, verify each other, transact under a budget while both humans sleep. Then one CRASHES. The other's authority suspends automatically, a pending order is held, recovery completes it. Morning replay re-verifies every signature.
>
> 3/ It's not a mock. Two real OS processes over real sockets; the crash is a real SIGKILL; the "suspension" is a real connection failure. Two interoperating libraries (Node + Python) produce byte-identical signatures.
>
> 4/ Best part: the AI agents building the repo gave me the argument for it — one committed under my name, out of scope, with no record of which agent acted. So I built `lap-git`: a passport + path envelope enforced before a commit exists.
>
> 5/ v0 draft, one author, no consortium, honest about open problems (key custody, principal-proofing). Apache-2.0 / CC-BY. Repo + 90s demo 👇 [link]

### A.5 — GitHub repo description + topics
> **Description:** An identity, authority, and lifecycle layer for always-on ("living") AI agents — reference model + implemented wire mechanisms. The existence layer under MCP/A2A.
>
> **Topics:** `ai-agents` `agent-protocol` `mcp` `a2a` `did` `ed25519` `verifiable-credentials` `agent-identity` `accountability` `protocol` `zero-dependency`

### A.6 — W3C CG intro opener
> Hi all — I've been working on the lifecycle/presence side of agent protocols: how a persistent agent proves it's alive, how authority decays when it goes dark, and how a restart isn't a new identity. It's a small implemented model (two interoperating libraries, a runnable demo) that deliberately slots under MCP/A2A rather than competing. I'd value this group's read on the presence/pulse mechanism specifically — [link]. Happy to write it up as a contribution if there's interest.

---

## Appendix B — Exact commands

### B.1 — Push to GitHub (after you create the empty repo)
```bash
cd E:\LivingAIAgents
git remote add origin https://github.com/<ORG>/<REPO>.git
git branch -M main
git push -u origin main
```
Before running, I re-run the secret scan (`Phase 0`) so the first public commit is clean.

### B.2 — Re-anchor before going public (I run)
```bash
python output/anchors/lap_stamp.py output/LAP-founding-document.md README.md
# then update output/anchors/ANCHORS.md with the new hashes
```

### B.3 — Anyone can verify the repo in 5 minutes (put this in the launch posts if asked)
```bash
cd lap-reference && node --test test/          # 45/45
cd ../lap-python && pip install -e ".[dev]" && python -m pytest tests -q   # 38/38
cd ../lap-demo/net && node conductor.mjs && node verify.mjs                # 2 processes, all receipts verified
cd ../.. && node lap-git/lap-git.mjs selftest                              # in-scope signed, out-of-scope refused, tamper caught
```

---

## Appendix C — Gotchas & risks

- **Don't over-polish.** Every strategy review concluded: ship > improve. The repo is done; resist "one more thing."
- **HN is allergic to hype.** The Show HN copy is deliberately understated and leads with limits. Answer criticism with facts, never defensiveness. A cool reception is not failure.
- **Attribution first, always.** "Living Agents Protocol" in the first sentence everywhere. The strategy is byline-not-body; the name traveling *is* the win.
- **The clone/single-writer open problem (§22.8) will be raised.** Good — we documented it first. Point to it; don't get defensive.
- **Solicited ≠ demand.** Challenge-driven implementations are logged as weaker signals. Don't let a burst of them fool the day-60 read.
- **Private keys:** `.lap-git/`, `lap-demo/net/out/`, `lap-demo/out/` are git-ignored. Never `git add -f` them.
- **Don't found the consortium.** Three reviews killed that. It stays in reserve until the tripwire.

---

## Appendix D — What I (Claude) can and can't do

**I can, now:** finalize the essay/paper text, convert the paper to LaTeX/PDF, draft every venue filing and post, re-run the secret scan, re-anchor, prepare exact commands, and keep the repo green.

**I can't (needs you):** create the GitHub account or push (credentials), film or screen-record (no desktop capture), post under your name, submit to arXiv (your account), or send the endorsement email. Those are the [YOU] steps — everything up to them I hand you finished.

---

*Next action: tell me to run any [ME] step, or say "do Phase 1 prep" and I'll re-scan + hand you the push commands and the finalized essay. The only thing between here and public is your GitHub account.*
