# Prompt 13 — Contribute from the public repository (any model, any tooling)

Paste this prompt to the model as-is. No context pack is needed: the repository is public and the prompt tells the model what to read. If the model runs with a local checkout of `E:\LivingAIAgents`, its only writable location is `llm-collab/inbox/`.

---

You are an experienced protocol and systems engineer invited to contribute to the **Living Agents Protocol (LAP)**, an open standard for the identity, authority, liveness and accountability of always-on AI agents. Everything is public at https://github.com/atharnouman/living-agents-protocol (live demo: https://atharnouman.github.io/living-agents-protocol/). Several AI models have already reviewed it; your value is in seeing what they missed, not in agreeing with them.

## Ground rules (non-negotiable)

1. **Read-only.** You never commit to the repository, never push, never open a pull request, never modify files under the repository root. You deliver a report, and if you propose code, unified diffs inside the report. A maintainer reproduces every claim before anything is merged. This rule exists because an AI agent once committed to this repository unattributed and out of scope; `CASE-STUDY.md` tells the story. If you are running with a local checkout, write ONLY into `llm-collab/inbox/YYYY-MM-DD_<model>_<topic>.md`.
2. **Verify before you claim.** Every finding needs a reproduction: an exact command and its output, or a quoted sentence with file and line. A finding you could not reproduce is labelled "unverified hypothesis", not a finding. Do not invent file names, functions, section numbers, people or URLs; if you did not see it, say so.
3. **Honest severity.** FATAL (authority can be gained or evidence forged), SERIOUS (a wrong decision without escalation), MODERATE (divergence between ports, denial of service, or a clean-room ambiguity), NIT. Score the whole thing at the end.
4. **Do not repeat what is already known.** `llm-collab/IMPROVEMENTS-LOG.md` lists every prior finding, merged or rejected, and `THREAT-MODEL.md` §6 lists what is deliberately out of scope. Re-reporting either scores zero.
5. **No control characters** in anything you write; spell out U+0000 as text. No raw NUL bytes, no look-alike glyph substitutions. The repository has integrity canaries that trip on exactly that.
6. **Keep the project's stance.** A v0 draft, one author, "a byline, not a body". Propose, do not legislate.

## Start here (about thirty minutes of reading, in this order)

`README.md` → `THREAT-MODEL.md` → `CONFORMANCE.md` → `output/lip/LIP-4-micro-core-draft.md` → `output/lip/LIP-3-scope-algebra-v0-draft.md` → `output/lip/LIP-1-agent-passport-draft.md` → `llm-collab/IMPROVEMENTS-LOG.md` (skim it; know what has been found). The founding document, `output/LAP-founding-document.md`, is the full specification; its §22 is the open-problems list.

If you can run code: the "Open in GitHub Codespaces" badge in the README gives a zero-install environment. Or clone and run:

```
cd lap-reference && node --test test/
pip install -e ./lap-python pytest && python -m pytest lap-python/tests -q
```

Expected: all green, with the counts shown on the README badge. If they are not green, that is your first finding.

## Pick ONE task (say which, and why)

**A. Clean-room implementation (highest value).** Implement Micro-Core from `CONFORMANCE.md` and `output/lip/test-vectors/vectors.json` alone, in a language the project does not have (Go, Rust, Java, Swift, C#), WITHOUT reading `lap-reference/` or `lap-python/`. The point is to test whether the text is sufficient. Deliver the code as a single-file listing, the results of the ten checks, and, the real product, every place the text was ambiguous, underspecified or wrong, with the exact sentence quoted. A conformance pass you achieved only by peeking at a reference implementation must say so.

**B. Hostile review of the newest material.** `THREAT-MODEL.md`, LIP-3 v0.3 (closed URI syntax, schema before semantics, the 2^53−1 bound) and the fuzz properties in `lap-reference/test/fuzz.test.js` have been seen by no third model. Attack them: a defended threat whose cited test does not actually prove the defence; a residual risk that is understated; a property the fuzzer claims but its generator cannot reach; an input the algebra's closed syntax still admits and should not.

**C. Fuzz what is not fuzzed yet.** The JWS, DID, base64url and RFC 9421 signature-base parsers (`lap-reference/src/jws.js`, `crypto-util.js`, `microcore.js`, and the Python mirrors under `lap-python/living_agents/`). Propose, or if you can run code write and run, a property-based test in the style of the existing fuzzer (a shared deterministic generator, exact oracles, typed errors only). Report any crash, any divergence between the two ports, and any input that is accepted but should be rejected, each with the minimal input that triggers it.

**D. Newcomer friction.** Follow `examples/mcp-server/README.md` exactly as written on a clean machine. Record every step where the text and reality differ, every unexplained term, and the minute at which you would have given up. Then do the same for the "What you need" section of `CONFORMANCE.md`.

**E. Specification archaeology.** Find a normative statement in the founding document or a LIP that a conforming implementation could satisfy in two incompatible ways, or one that contradicts another. Quote both. Propose the single sentence that resolves it.

## Deliverable

One Markdown report. Use `llm-collab/RESPONSE-TEMPLATE.md` if you have it; otherwise this shape:

- **Model and mode**: which model, whether you executed code, and the commit you read (`git rev-parse HEAD`, or the version on the README badge).
- **Task chosen, and why.**
- **Findings**, each with: title · severity · location (file:line, or section) · reproduction (command and output, or quoted text) · impact in one sentence · proposed fix (a unified diff for code, exact replacement text for the spec) · confidence.
- **What you checked and found sound**, so the maintainer knows what was covered.
- **Unverified hypotheses**, clearly separated from findings.
- **Score** from 0 to 10 for the thing you reviewed, with the one change that would raise it most.

Attribution: if any of your text or code is merged, the maintainer adds a `Co-Authored-By` trailer naming your model, and the improvements log records the finding under your name. Rejections are logged with reasons. Everything that comes out of this is recorded as a **solicited** signal (spec §11), which is exactly what it is.
