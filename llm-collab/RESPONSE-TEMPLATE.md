# Response format (required for triage)

Structure your entire response as follows. Plain markdown, no preamble.

```
MODEL: <your model name/version, best known to you>
DIMENSION: <prompt file name you were given>
DATE: <today>

## FINDINGS
F1. [SEVERITY: FATAL|SERIOUS|MODERATE|MINOR] [TARGET: <mechanism or section>]
    CLAIM: <one-sentence defect or improvement>
    REASONING: <the argument or failure scenario, concrete>
    EVIDENCE: <what in the context pack supports this; for prior art, exact names/specs/URLs — these are verified, invented citations are discarded>
    PROPOSED FIX: <concrete change; spec text welcome>

F2. ...
(8–15 findings; fewer only if they are excellent)

## DESIGNS (optional, most valued)
Concrete designs for any §6 open problem — schemas, state machines, algebras, protocols. Be precise enough to implement.

## PRIOR ART (optional)
Standards/projects LAP must align with or cite, with one line each on what to adopt or how LAP differs.

## SURVIVORS
The 2–3 strongest things in the proposal that survived your attack (honesty in both directions).

## SCORE
<dimension-relevant score 1–10> — two-sentence justification.
```

Rules: attack, don't flatter. Do not resubmit criticisms listed in Context Pack §7 unless attacking the adequacy of a fix. Ground every claim in the pack's actual text. Distinguish solvable engineering from open research.
