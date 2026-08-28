# Living Agents Protocol (LAP) — Project Brief

*Athar Nouman · August 2026 · status: build phase complete, publishing next*

## What I'm doing, in one paragraph

AI agents recently got standard ways to use tools (Anthropic's MCP), exchange tasks with each other (Google's A2A), and pay (AP2, x402). But nothing standardizes an agent's **existence**: who it is, which human or company answers for it, what it may do while unsupervised, whether it's even running right now, what it remembers, and how its actions are proven afterwards. I'm building the **Living Agents Protocol (LAP)** — an open reference model plus concrete wire mechanisms for that missing "existence layer." Think of it as the TLS-handshake role for AI agents: it never carries the work; it decides *whether, and under whose authority*, the work may flow.

The one-line version: **agents need a birth certificate, a leash, a black box, and an estate plan.**

## What exists today (all real, all runnable)

- **Spec v0.4.3** — 26 sections, hardened by **four adversarial review rounds** (~140 verified fixes merged), including cross-model reviews: Claude red teams + external Gemini reviews, every finding verified before merge, rejections logged with reasons.
- **Four protocol drafts (LIPs)**: the Agent Passport (identity + responsible-human binding), MEET (the six-step stranger handshake), the Scope Algebra (a strict mini-language for delegable permissions where math can prove a helper never exceeds its boss), and Micro-Core (a two-header profile any tool server can adopt in an afternoon).
- **A zero-dependency reference library** (Node ≥20): 31/31 tests green, including cross-language proof that Python and JavaScript produce byte-identical canonical signatures.
- **A working overnight demo**: two strangers' agents meet, verify each other, disclose spending limits, transact real signed payments while both "humans sleep"; one agent crashes mid-session — its authority suspends automatically, a pending order is safely held, and on recovery everything completes. The morning replay verifies **191 signatures and hash links**, and a deliberate tamper is caught to the exact entry.
- **A position paper** (arXiv-ready), a public essay, and a designed manifesto page.

## The plan — "publish, then infiltrate"

Deliberately *not* founding a consortium (three strategy reviews killed that idea): LAP is a byline, not a body.

1. **Publish** — film the 90-second demo, open the GitHub repo (Apache-2.0 code, CC-BY spec), release the essay and paper.
2. **Infiltrate** — file the mechanisms as extensions into venues that already have distribution: MCP/A2A middleware (~60% of effort), the W3C AI Agent Protocol community, OWASP's agentic-security work; watching the new ITU and NIST agent-standards efforts.
3. **Day-60 gate** — objective pull signals (external PRs, a framework accepting a plugin) decide where to double down; dead tracks get archived, not nursed.
4. **The tripwire** — two external implementations we didn't recruit unlocks the bigger institutional ambitions (held in reserve until earned).

## Honest odds

Three ways this wins: the concepts get adopted into bigger standards **with attribution** (likely); it establishes deep expertise and reputation in agent identity/lifecycle (likely); LAP itself becomes the referenced existence layer if the agent economy arrives on schedule (low probability, high magnitude). The project is structured so any one of the three justifies it.

## The meta-story

The spec itself was built with AI as genuine collaborator: drafted with Claude, then attacked across multiple frontier models under a structured review kit with verification, dedupe, and a public improvements log — arguably one of the first specs hardened this way, and part of the point: this is what accountable human+AI systems engineering looks like.

*Materials (spec, papers, library, demo) available on request; public repo forthcoming.*
