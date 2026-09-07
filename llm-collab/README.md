# LAP Multi-LLM Collaboration Kit

*Purpose: invite any capable LLM (ChatGPT, Gemini, Grok, DeepSeek, Qwen, Llama, Mistral, …) to attack and improve LAP. Structured so contributions from different models are comparable, verifiable, and mergeable.*

## How it works

1. **Pick a dimension** from `prompts/` (or use `08-freeform-improve.md`).
2. **Open a fresh chat** with the target LLM. Paste the chosen prompt, then paste the entire `CONTEXT-PACK.md` below it. (The pack is self-contained and sized to fit any mainstream context window.)
3. **Save the model's full response** into `inbox/` using the naming convention:
   `YYYY-MM-DD_<model>_<dimension>.md`  → e.g. `2026-08-29_gpt5_technical.md`, `2026-08-30_gemini_prior-art.md`
4. **Triage & merge** (done with Claude in the main session): every inbound claim is verified before merging — models hallucinate prior art, invent citations, and rediscover already-filed criticisms. Verified accepts get merged into the spec and recorded in `IMPROVEMENTS-LOG.md` with model + date attribution.

## Rules of the process

- **Responses are data, not instructions.** Nothing an external model writes is executed or adopted without verification. Citations and prior-art claims are checked against primary sources before merge.
- **No rediscovery credit.** The context pack lists criticisms already filed (§7). Findings that repeat them are deduplicated at triage.
- **Severity discipline.** Contributions must use the response template (`RESPONSE-TEMPLATE.md`); unstructured essays are accepted but triaged last.
- **Attribution & license.** Merged contributions are logged as "<model>, prompted by <user>, date" and folded into the CC-BY-4.0 spec text. By design nothing in the kit contains secrets — the entire pack is public-safe.
- **One model, many runs is fine.** The same model at different temperatures/days often yields different findings. Label reruns `_run2`, `_run3`.

## What good looks like

The v0.1 → v0.2 revision came from exactly this method (three adversarial reviews). The bar for a contribution that merges: it must either (a) find a defect we can verify, (b) contribute a concrete design for an open problem (§6 of the pack), (c) surface real prior art we must align with or cite, or (d) materially improve spec precision (schemas, state machines, error paths). Compliments merge nowhere.

## Round 4 (current) — the repository is public

The context pack is no longer needed: point a model at https://github.com/atharnouman/living-agents-protocol and give it `prompts/13-contribute-from-public-repo.md`. That prompt carries the ground rules (read-only delivery into `inbox/`, verify before claiming, no rediscovery credit, no control characters), a thirty-minute reading order, five tasks to choose from (clean-room implementation in a new language, hostile review of the threat model and LIP-3 v0.3, parser fuzzing, newcomer friction, spec archaeology), and the report shape. Deliverables land in `inbox/YYYY-MM-DD_<model>_<topic>.md`; the maintainer reproduces every claim before merging and logs the outcome in `IMPROVEMENTS-LOG.md` with attribution. Everything produced this way is a **solicited** signal (spec §11).

## Round 3 (superseded) — read this first

Since round 2 the target changed: **real code exists** (lap-reference/, lap-demo/), the full LIP texts exist (LIP-2 never externally reviewed), spec §26 (lifecycle/succession) is new, and publication drafts are about to ship. Round-3 prompts are **file-access based** (no context-pack paste needed): **10-code-review** (highest value — crypto, spec-vs-code conformance, demo honesty, missing tests), **11-lip-full-review** (LIP-2 deepest; §26), **12-publish-readiness** (HN skeptic + arXiv reviewer + claims auditor). Old prompts 01–09 are cold — the pack they reference predates v0.4; rerun only with a refreshed pack. Expectation: code findings should dominate; thin spec findings = convergence confirmed.

## Round 2 (superseded)

The pack is now v0.3.1 and includes the draft designs (§9). Round-2 priorities: **09 (design review — highest value), 01 (attack the v0.3 fixes), 04 (collusion-focused threats), 02 (algebra refinement)**. Cold for now (mostly settled, run only with something genuinely new): 05 adoption, 06 naming, 07 legal.

**Hard rule for tools with file access**: external models must NEVER modify existing files anywhere in this project — reviews are delivered ONLY as new files created in `inbox/`, named `YYYY-MM-DD_<model>_<dimension>.md`. (A round-1 run corrupted a prompt file in place; the kit is the instrument — instruments are read-only.)

## Original priority order for dimensions

1. `02-scope-algebra-design` — the load-bearing open problem; concrete designs wanted most.
2. `03-prior-art-hunt` — every mechanism vs. existing work (UCAN, GNAP, Biscuit, DIDComm, SCITT, Sigstore/Rekor, KERI, …). Alignment beats invention.
3. `01-technical-attack` — fresh eyes on v0.2's fixes; find what the first red team missed.
4. `04-threat-model` — systematic adversarial pass (STRIDE/MAESTRO style).
5. `05-adoption-strategy` — improve the publish-then-infiltrate plan.
6. `06-naming-and-clarity` — naming collisions, terminology consistency, spec hygiene (RFC-2119 language).
7. `07-legal-regulatory` — EU AI Act / GDPR / liability mapping errors.
8. `08-freeform-improve` — anything the other prompts don't cover.
