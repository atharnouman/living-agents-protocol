# Prompt 12 — Publish-Readiness Red Team (round-3 priority #3)

*(For a reviewer with file access. The project is about to go public; this is the pre-flight editorial attack.)*

---

You are three hostile readers in sequence. Read:

1. `E:\LivingAIAgents\output\LAP-essay.md`
2. `E:\LivingAIAgents\output\LAP-position-paper.md`
3. `E:\LivingAIAgents\output\LAP-project-brief.md`
4. For fact-checking claims against reality: `E:\LivingAIAgents\lap-reference\` and `E:\LivingAIAgents\lap-demo\` (the actual code), `E:\LivingAIAgents\output\anchors\ANCHORS.md`

**Reader 1 — the Hacker News skeptic.** You've seen a hundred "protocol for AI agents" posts. Find every sentence that would draw a brutal top comment: overclaims relative to what the code actually does, buzzword density, the "yet another standard" reflex (does the text pre-empt XKCD 927 fast enough?), anything that smells like consortium-vaporware. Quote the exact sentence, write the top comment it would attract, then rewrite the sentence to survive.

**Reader 2 — the arXiv reviewer.** Assess the position paper as a cs.MA submission: are contributions crisply separable from prior work; is the FIPA/UDDI/SSI history accurate and fairly cited; does any claim need a citation it lacks; are the open problems honest or strategic; would you accept, revise, or reject — and what are the three mandatory revisions?

**Reader 3 — the claims auditor.** Every number and factual claim across all three documents, checked against the artifacts: "21/21 tests" (count them), "185/191 checks" (which is current?), "~115 fixes" (plausible from the improvements log?), "four review rounds" (count), "zero dependencies" (true for all packages?), "Bitcoin-anchored" (what exactly is the honest tense — anchored, or pending attestation?), version numbers consistent everywhere (v0.4.2 vs older references). Every stale or inflated number is a finding — the project's whole brand is verified honesty, so one wrong number costs more than a real bug.

Also: the three documents will be read in sequence by one person (brief → essay → paper). Flag contradictions between them and redundancies that would bore that reader.

Deliver as a NEW file `E:\LivingAIAgents\llm-collab\inbox\YYYY-MM-DD_<model>_publish-readiness.md` (never modify existing files): findings with document+quote+severity+rewritten text; the arXiv verdict with mandatory revisions; a corrected-numbers table; survivors (the strongest passages — do not touch these in edits); a ship/hold recommendation per document.
