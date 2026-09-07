# Living Agents Protocol (LAP)

**The existence layer for always-on AI agents** — identity, authority, liveness, and accountability for agents that never log off.

[![ci](https://github.com/atharnouman/living-agents-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/atharnouman/living-agents-protocol/actions/workflows/ci.yml) [![license: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE) [![spec: CC-BY-4.0](https://img.shields.io/badge/spec-CC--BY--4.0-lightgrey.svg)](LICENSE-SPEC.md)

`spec v0.4.9 (draft)` · `Node 61/61 · Python 55/55` · `two interoperating implementations` · `IPv4 + IPv6` · `5 adversarial review rounds, ~150 verified fixes` · `Bitcoin-timestamped`

**▶ Live demos:** [atharnouman.github.io/living-agents-protocol](https://atharnouman.github.io/living-agents-protocol/) — the visual demo (two agents, a crash, automatic suspension and recovery), the terminal playback, and an asciinema recording of the two-process run.

[![LAP overnight demo — two strangers' agents transact while both humans sleep; one crashes, its authority suspends automatically, a held order completes on recovery, and the morning replay verifies every signature](docs/demo.gif)](https://atharnouman.github.io/living-agents-protocol/demo.html)

*Click the animation for the live, interactive version.*

---

AI agents recently got standard ways to use tools ([MCP](https://modelcontextprotocol.io)), exchange tasks ([A2A](https://a2a-protocol.org)), and pay (AP2, x402). Nothing standardizes an agent's **existence**: who it is, which human answers for it, what it may do while unsupervised, whether it is running right now, what it remembers, and how its actions are proven afterwards. We built the roads before the license plates.

LAP is a reference model plus wire mechanisms for that missing control plane — the handshake-layer role: it never carries the work, it decides *whether, and under whose authority*, work may flow. The one-line version: **agents need a birth certificate, a leash, a black box, and an estate plan.**

## Try it in two minutes

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/atharnouman/living-agents-protocol?quickstart=1)
*Zero install: the Codespace arrives with Node, Python, and the test suite already run — then try the two-process demo.*

```bash
cd lap-reference && node --test test/     # 49 tests: crypto, algebra, Micro-Core, Merkle log, Rekor, integrity + audit canaries
```

```bash
cd lap-python && pip install -e ".[dev]" && python -m pytest tests -q   # the same vectors, plus the property-based fuzzer
```

```bash
cd lap-demo && node demo.js && node replay.js          # single-process narrative (191 checks; try --tamper)
```

```bash
cd lap-demo/net && node conductor.mjs && node verify.mjs  # two REAL processes over localhost HTTP
```

```bash
cd lap-demo && node register-genesis.mjs   # register a genesis in the PUBLIC Sigstore Rekor log, verify inclusion with LAP's own code
```

```bash
cd examples/mcp-server && python client.py   # a real MCP server protected by LAP: one paid call + four refusals, receipt verified
```

The single-process demo runs the whole story: two strangers' agents MEET (passports, Merkle registration proofs, a reservation ticket), sign a contract, and transact real Ed25519-signed payments overnight — then one agent *crashes*, its authority suspends automatically (confirmed by two independent witnesses), a pending order safely holds, and on recovery everything completes. The morning replay re-verifies **191 signatures and hash chains**; `node replay.js --tamper` catches a single modified log entry to the exact record.

The [**networked demo**](lap-demo/net/) proves the same story across **two real OS processes exchanging signed JSON over real sockets** — the crash is a genuine `SIGKILL`, the suspension is caused by real `ECONNREFUSED`, and the seller reloads its identity on restart (same `did:key`, because a session binds to the passport, not the process). For a filmable run: `node conductor.mjs --present`; it runs unmodified over IPv6 with `--ipv6` (LAP never inspects the network layer — spec §20.1). Media assets and a recording guide (terminal styling, a visual UI, an asciinema cast) are in [output/LAP-recording-playbook.md](output/LAP-recording-playbook.md).

Registration in the demos is self-attested by default; `register-genesis.mjs` registers a real Genesis Record in [Sigstore's public Rekor transparency log](https://rekor.sigstore.dev) and verifies the RFC 6962 inclusion proof and Rekor's signed timestamp with LAP's own Merkle code — birth witnessed, not self-asserted.

Requirements: Node ≥ 20. No `npm install` — the entire implementation uses platform built-ins.

## The protocol drafts (LIPs)

| Draft | What it specifies |
|---|---|
| [LIP-1 — Agent Passport & Genesis](output/lip/LIP-1-agent-passport-draft.md) | Identity bound to a responsible human (labeled proof classes), witnessed birth, amendment chain, the no-orphan rule |
| [LIP-2 — MEET](output/lip/LIP-2-meet-draft.md) | The six-step stranger handshake: transcript-hashed, collision-safe, with reservation tickets, fair-exchange turns, and split-view defense |
| [LIP-3 — Scope Algebra v0](output/lip/LIP-3-scope-algebra-v0-draft.md) | A deliberately tiny permission language where subset-checking is decidable — delegation can be *proven* narrower, budgets conserve across children |
| [LIP-4 — Micro-Core](output/lip/LIP-4-micro-core-draft.md) | The afternoon-sized profile: two HTTP headers + a receipt, single-server adoptable, upgrade-compatible with everything above |

The full reference model (LAP-7 layers, trust states, ownership & transfer, lifecycle from witnessed birth to economic mortality and the unbroken **Accountability Chain** of responsible humans) lives in the [founding document](output/LAP-founding-document.md). Deterministic cross-language test vectors (Python ↔ JS byte-identical): [`output/lip/test-vectors/`](output/lip/test-vectors/).

## Repository map

| Path | Contents |
|---|---|
| `lap-reference/` | Zero-dependency Node implementation: JWS, did:key, scope algebra, Micro-Core invariant, RFC 6962 Merkle log, Sigstore Rekor binding |
| `lap-python/` | Python port + FastMCP `@verify_envelope` middleware (single dependency: `cryptography`); the same vectors, plus the property-based fuzzer, in pytest |
| `lap-demo/` | The two-agent overnight demo + morning replay verifier |
| `lap-git/` | **Experimental:** "Micro-Core for commits" — agent passport + path envelope enforced before commit + verifiable tree signature |
| [`examples/mcp-server/`](examples/mcp-server/) | **Tutorial:** add LAP to your MCP server in 15 minutes — a real FastMCP server + LAP-aware client (stdio round-trip, verified in CI) |
| [`CASE-STUDY.md`](CASE-STUDY.md) | The commit nobody signed: what happened when AI agents worked here *without* an accountability layer |
| [`CONFORMANCE.md`](CONFORMANCE.md) | Implement Micro-Core in an afternoon — a ten-check challenge against the shared test vectors |
| [`THREAT-MODEL.md`](THREAT-MODEL.md) | What LAP defends against and what it does not: assets, actors, sixteen threats each tied to its enforcing code and regression test, residual risks stated plainly |
| `output/` | The founding document, LIP drafts, position paper, essay, project brief, roadmap |
| `output/anchors/` | OpenTimestamps proofs — every release is hash-committed to Bitcoin |
| `llm-collab/` | The multi-model review kit and the full improvements log (every merged, softened, and rejected finding, with reasons) |

## How this was built — and why that's part of the point

The spec was drafted with Claude (Anthropic) as co-designer, then attacked across **five structured adversarial review rounds** — including external reviews by Gemini (Google) under a fixed kit and a purely hostile security audit by GPT-5.6 (OpenAI): every finding verified before merging (several reviewer-proposed fixes were themselves caught introducing bugs), duplicates deduplicated, and every rejection logged with its reason in [`llm-collab/IMPROVEMENTS-LOG.md`](llm-collab/IMPROVEMENTS-LOG.md). We believe this is among the first protocol specifications hardened by cross-model adversarial review with a public audit trail — which is fitting, because *accountable human-plus-AI engineering* is what the protocol itself is for.

**Honest status**: this is a v0 draft by one author. There is no consortium, no certification program, and no claim that the stranger-agent economy is imminent — the [position paper](output/LAP-position-paper.md) states the open problems (key custody, principal proofing, scope-vocabulary governance) as plainly as the contributions. Several mechanisms pay their way in single-operator deployments today; the rest is a bet on where always-on agents are heading, with the history of FIPA, UDDI, and P3P studied rather than repeated.

## Contributing & licenses

See [CONTRIBUTING.md](CONTRIBUTING.md) for the LIP process and review culture. Code: [Apache-2.0](LICENSE). Specification texts: [CC-BY-4.0](LICENSE-SPEC.md). © 2026 Athar Nouman.
